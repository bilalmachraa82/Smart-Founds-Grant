"""
Reports API v7 - Premium Report Generation Endpoints

Handles complete premium report generation with RAG + Multi-Agent + IFIC Services.

Endpoints:
    POST /api/v7/reports/generate - Generate complete premium report
    GET /api/v7/reports/{report_id} - Get report by ID
    GET /api/v7/reports/{report_id}/download - Download Excel/PDF
    DELETE /api/v7/reports/{report_id} - Delete report
    GET /api/v7/reports/list - List all reports for user
    WebSocket /api/v7/reports/progress/{report_id} - Real-time progress updates

@author Claude Code (Anthropic)
@version 7.0.0
@license MIT
"""

from typing import Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks, Depends, Response
from fastapi.responses import StreamingResponse, HTMLResponse
from pydantic import BaseModel

from ..models.questionnaire import DiagnosticQuestionnaire
from ..services.smart_orchestrator_v7 import SmartOrchestratorV7, ProgressUpdate
from ..services.credential_service import credential_service
from ..config.logfire_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v7/reports", tags=["reports_v7"])


# ═══════════════════════════════════════════════════════════════
# REQUEST/RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════

class GenerateReportRequest(BaseModel):
    """Request model for report generation."""
    questionnaire_id: Optional[UUID] = None
    questionnaire_data: Optional[DiagnosticQuestionnaire] = None
    project_start_date: Optional[str] = None
    include_excel: bool = True
    include_pdf: bool = False


class ReportResponse(BaseModel):
    """Response model for generated report."""
    report_id: UUID
    status: str  # "processing", "completed", "failed"
    html_url: Optional[str] = None
    excel_url: Optional[str] = None
    pdf_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
# IN-MEMORY STORAGE (Temporary - Move to Redis/DB)
# ═══════════════════════════════════════════════════════════════

# WebSocket connections for progress updates
active_connections: Dict[str, WebSocket] = {}

# Report storage (temporary - should be in database)
reports_storage: Dict[UUID, Dict] = {}


# ═══════════════════════════════════════════════════════════════
# DEPENDENCY INJECTION
# ═══════════════════════════════════════════════════════════════

async def get_orchestrator() -> SmartOrchestratorV7:
    """Get smart orchestrator instance with all services."""
    # TODO: Inject RAG, Agent, LLM, DB services
    orchestrator = SmartOrchestratorV7(
        rag_service=None,  # await get_rag_service()
        agent_service=None,  # await get_agent_service()
        llm_service=None,  # await get_llm_service()
        db_service=None,  # await get_db_service()
    )
    return orchestrator


# ═══════════════════════════════════════════════════════════════
# WEBSOCKET PROGRESS HANDLER
# ═══════════════════════════════════════════════════════════════

@router.websocket("/progress/{report_id}")
async def websocket_progress(websocket: WebSocket, report_id: str):
    """
    WebSocket endpoint for real-time progress updates.

    Client connects and receives progress updates as report generates.

    Example:
        const ws = new WebSocket('ws://localhost:8000/api/v7/reports/progress/123');
        ws.onmessage = (event) => {
            const progress = JSON.parse(event.data);
            console.log(`${progress.percent}%: ${progress.message}`);
        };
    """
    await websocket.accept()
    active_connections[report_id] = websocket

    logger.info(f"WebSocket connected for report {report_id}")

    try:
        # Keep connection alive
        while True:
            data = await websocket.receive_text()

            # Handle ping/pong
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for report {report_id}")
        if report_id in active_connections:
            del active_connections[report_id]


async def send_progress_update(report_id: str, progress: ProgressUpdate):
    """Send progress update to connected WebSocket clients."""
    if report_id in active_connections:
        try:
            await active_connections[report_id].send_json({
                "percent": progress.percent,
                "message": progress.message,
                "step": progress.step,
                "data": progress.data,
                "timestamp": progress.timestamp
            })
        except Exception as e:
            logger.error(f"Failed to send progress update: {e}")


# ═══════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    request: GenerateReportRequest,
    background_tasks: BackgroundTasks,
    orchestrator: SmartOrchestratorV7 = Depends(get_orchestrator)
):
    """
    Generate complete premium McKinsey-level report.

    This endpoint:
    1. Validates questionnaire
    2. Starts background report generation
    3. Returns report_id immediately
    4. Sends progress updates via WebSocket

    Args:
        request: Generation request with questionnaire data

    Returns:
        ReportResponse with report_id and status

    Example:
        POST /api/v7/reports/generate
        {
            "questionnaire_data": {...},
            "project_start_date": "2025-01-15",
            "include_excel": true
        }

        Response:
        {
            "report_id": "550e8400-e29b-41d4-a716-446655440000",
            "status": "processing",
            "created_at": "2025-01-11T10:30:00Z"
        }
    """

    # Validate request
    if not request.questionnaire_data and not request.questionnaire_id:
        raise HTTPException(
            status_code=400,
            detail="Either questionnaire_data or questionnaire_id must be provided"
        )

    # Generate report ID
    report_id = uuid4()

    # Initialize report storage
    reports_storage[report_id] = {
        "report_id": report_id,
        "status": "processing",
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
        "html": None,
        "excel": None,
        "pdf": None,
        "metadata": None,
        "error": None
    }

    logger.info(f"Starting report generation: {report_id}")

    # Get questionnaire
    if request.questionnaire_data:
        questionnaire = request.questionnaire_data
    else:
        # Load from database using questionnaire_id
        try:
            supabase = credential_service._get_supabase_client()
            result = supabase.table("archon_questionnaires") \
                .select("data") \
                .eq("id", request.questionnaire_id) \
                .execute()

            if not result.data or len(result.data) == 0:
                raise HTTPException(
                    status_code=404,
                    detail=f"Questionnaire not found: {request.questionnaire_id}"
                )

            # Parse JSONB data into DiagnosticQuestionnaire object
            questionnaire_data = result.data[0]["data"]
            questionnaire = DiagnosticQuestionnaire(**questionnaire_data)

            logger.info(f"Loaded questionnaire {request.questionnaire_id} from database")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error loading questionnaire from database: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error loading questionnaire: {str(e)}"
            )

    # Progress callback
    async def progress_callback(progress: ProgressUpdate):
        await send_progress_update(str(report_id), progress)

    # Background generation task
    async def generate_in_background():
        try:
            result = await orchestrator.generate_complete_report(
                questionnaire=questionnaire,
                project_start_date=request.project_start_date,
                progress_callback=progress_callback
            )

            # Update storage
            reports_storage[report_id].update({
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "html": result["html"],
                "excel": result["excel"],
                "pdf": result.get("pdf"),
                "metadata": result["metadata"]
            })

            logger.info(f"Report generation completed: {report_id}")

        except Exception as e:
            logger.error(f"Report generation failed: {e}", exc_info=True)
            reports_storage[report_id].update({
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.now().isoformat()
            })

    # Add to background tasks
    background_tasks.add_task(generate_in_background)

    return ReportResponse(
        report_id=report_id,
        status="processing",
        created_at=reports_storage[report_id]["created_at"]
    )


@router.get("/{report_id}", response_class=HTMLResponse)
async def get_report_html(report_id: UUID):
    """
    Get generated report HTML.

    Returns the premium HTML report for viewing in browser.

    Args:
        report_id: UUID of the report

    Returns:
        HTML content

    Example:
        GET /api/v7/reports/550e8400-e29b-41d4-a716-446655440000
    """

    if report_id not in reports_storage:
        raise HTTPException(status_code=404, detail="Report not found")

    report = reports_storage[report_id]

    if report["status"] == "processing":
        return HTMLResponse(
            content="""
            <html>
                <head><title>Report Generating...</title></head>
                <body>
                    <h1>Report is being generated...</h1>
                    <p>Please wait. This page will auto-refresh.</p>
                    <script>setTimeout(() => location.reload(), 2000);</script>
                </body>
            </html>
            """,
            status_code=202
        )

    if report["status"] == "failed":
        raise HTTPException(status_code=500, detail=f"Report generation failed: {report['error']}")

    if not report["html"]:
        raise HTTPException(status_code=404, detail="Report HTML not available")

    return HTMLResponse(content=report["html"])


@router.get("/{report_id}/metadata")
async def get_report_metadata(report_id: UUID) -> Dict[str, Any]:
    """
    Get report metadata without full HTML.

    Useful for listing reports and showing quick info.

    Args:
        report_id: UUID of the report

    Returns:
        Metadata dict

    Example:
        GET /api/v7/reports/550e8400-e29b-41d4-a716-446655440000/metadata

        Response:
        {
            "report_id": "...",
            "status": "completed",
            "company_name": "CodeLab Portugal",
            "merit_score": 7.5,
            "compliance_status": "ELEGÍVEL",
            "created_at": "2025-01-11T10:30:00Z",
            "completed_at": "2025-01-11T10:31:23Z"
        }
    """

    if report_id not in reports_storage:
        raise HTTPException(status_code=404, detail="Report not found")

    report = reports_storage[report_id]

    return {
        "report_id": str(report_id),
        "status": report["status"],
        "created_at": report["created_at"],
        "completed_at": report["completed_at"],
        "metadata": report["metadata"],
        "has_excel": report["excel"] is not None,
        "has_pdf": report["pdf"] is not None,
        "error": report["error"]
    }


@router.get("/{report_id}/download/excel")
async def download_excel(report_id: UUID):
    """
    Download Excel export of report.

    Args:
        report_id: UUID of the report

    Returns:
        Excel file as StreamingResponse

    Example:
        GET /api/v7/reports/550e8400-e29b-41d4-a716-446655440000/download/excel
    """

    if report_id not in reports_storage:
        raise HTTPException(status_code=404, detail="Report not found")

    report = reports_storage[report_id]

    if not report["excel"]:
        raise HTTPException(status_code=404, detail="Excel export not available")

    # Reset BytesIO position
    report["excel"].seek(0)

    # Get company name for filename
    company_name = report["metadata"].get("company_name", "Report") if report["metadata"] else "Report"
    filename = f"{company_name}_Vale_Inovacao_{datetime.now().strftime('%Y%m%d')}.xlsx"

    return StreamingResponse(
        report["excel"],
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.delete("/{report_id}")
async def delete_report(report_id: UUID):
    """
    Delete a report.

    Args:
        report_id: UUID of the report

    Returns:
        Success message

    Example:
        DELETE /api/v7/reports/550e8400-e29b-41d4-a716-446655440000
    """

    if report_id not in reports_storage:
        raise HTTPException(status_code=404, detail="Report not found")

    del reports_storage[report_id]

    logger.info(f"Report deleted: {report_id}")

    return {"message": "Report deleted successfully", "report_id": str(report_id)}


@router.get("/list")
async def list_reports(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None
) -> Dict[str, Any]:
    """
    List all reports.

    Args:
        skip: Number of reports to skip
        limit: Maximum number of reports to return
        status: Filter by status (processing/completed/failed)

    Returns:
        List of reports with metadata

    Example:
        GET /api/v7/reports/list?limit=10&status=completed

        Response:
        {
            "reports": [...],
            "total": 42,
            "skip": 0,
            "limit": 10
        }
    """

    # Filter reports
    filtered_reports = [
        {
            "report_id": str(rid),
            "status": r["status"],
            "created_at": r["created_at"],
            "completed_at": r["completed_at"],
            "company_name": r["metadata"].get("company_name") if r["metadata"] else None,
            "merit_score": r["metadata"].get("merit_score") if r["metadata"] else None
        }
        for rid, r in reports_storage.items()
        if status is None or r["status"] == status
    ]

    # Sort by created_at descending
    filtered_reports.sort(key=lambda x: x["created_at"], reverse=True)

    # Pagination
    total = len(filtered_reports)
    paginated = filtered_reports[skip:skip+limit]

    return {
        "reports": paginated,
        "total": total,
        "skip": skip,
        "limit": limit
    }


# ═══════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════════

@router.get("/health")
async def health_check():
    """Health check endpoint for v7 reports API."""
    return {
        "status": "healthy",
        "version": "7.0.0",
        "active_reports": len([r for r in reports_storage.values() if r["status"] == "processing"]),
        "completed_reports": len([r for r in reports_storage.values() if r["status"] == "completed"]),
        "active_websockets": len(active_connections)
    }
