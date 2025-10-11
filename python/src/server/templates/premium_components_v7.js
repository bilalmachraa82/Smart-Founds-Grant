/**
 * ═══════════════════════════════════════════════════════════════
 * ARCHON PREMIUM WEB COMPONENTS v7.0
 * ═══════════════════════════════════════════════════════════════
 *
 * McKinsey-Level Interactive Components
 * Uses: Web Components API, Intersection Observer, CSS Custom Properties
 * Performance: Lazy loading, progressive enhancement
 *
 * @author Claude Code (Anthropic)
 * @version 7.0.0
 * @license MIT
 */

// ═══════════════════════════════════════════════════════════════
// BASE COMPONENT CLASS
// ═══════════════════════════════════════════════════════════════

class ArchonComponent extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._isIntersecting = false;
  }

  connectedCallback() {
    this.render();
    this._setupIntersectionObserver();
    this._setupAnimations();
  }

  _setupIntersectionObserver() {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !this._isIntersecting) {
            this._isIntersecting = true;
            this.onVisible();
          }
        });
      },
      { threshold: 0.1 }
    );
    observer.observe(this);
  }

  _setupAnimations() {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      return;
    }
    this.animate();
  }

  // Override in subclasses
  render() {}
  onVisible() {}
  animate() {}
}

// ═══════════════════════════════════════════════════════════════
// COVER PAGE COMPONENT
// ═══════════════════════════════════════════════════════════════

class ArchonCoverPage extends ArchonComponent {
  static get observedAttributes() {
    return ['logo', 'title', 'subtitle', 'date', 'classification'];
  }

  render() {
    const logo = this.getAttribute('logo') || '';
    const title = this.getAttribute('title') || 'AI Transformation Strategy';
    const subtitle = this.getAttribute('subtitle') || 'Vale Inovação - Aviso 03/C05-i02';
    const date = this.getAttribute('date') || new Date().getFullYear();
    const classification = this.getAttribute('classification') || 'CONFIDENTIAL';

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          position: relative;
          min-height: 100vh;
          overflow: hidden;
          background: linear-gradient(135deg, #0A1929 0%, #0F2544 100%);
          color: #F8FAFC;
        }

        .mesh-gradient {
          position: absolute;
          inset: 0;
          z-index: 0;
        }

        .content {
          position: relative;
          z-index: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          min-height: 100vh;
          padding: 2rem;
        }

        .logo {
          width: 180px;
          height: 180px;
          margin-bottom: 3rem;
          opacity: 0;
          transform: scale(0.8) translateY(-30px);
          filter: drop-shadow(0 10px 30px rgba(0, 0, 0, 0.3));
        }

        .logo.visible {
          animation: logo-entrance 800ms cubic-bezier(0, 0, 0.2, 1) forwards;
        }

        @keyframes logo-entrance {
          to {
            opacity: 1;
            transform: scale(1) translateY(0);
          }
        }

        .title {
          font-family: var(--font-display, 'SF Display', sans-serif);
          font-size: clamp(2.5rem, 8vw, 4.5rem);
          font-weight: 100;
          letter-spacing: -0.02em;
          text-align: center;
          margin-bottom: 1.5rem;
          max-width: 900px;
          opacity: 0;
          transform: translateY(30px);
        }

        .title.visible {
          animation: title-entrance 1200ms cubic-bezier(0, 0, 0.2, 1) 200ms forwards;
        }

        @keyframes title-entrance {
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .subtitle {
          font-size: clamp(1.25rem, 3vw, 1.5rem);
          font-weight: 300;
          opacity: 0.9;
          margin-bottom: 4rem;
          text-align: center;
          opacity: 0;
          transform: translateY(30px);
        }

        .subtitle.visible {
          animation: title-entrance 1200ms cubic-bezier(0, 0, 0.2, 1) 400ms forwards;
        }

        .meta {
          display: flex;
          gap: 2rem;
          font-size: 0.875rem;
          opacity: 0.7;
          opacity: 0;
          transform: translateY(30px);
        }

        .meta.visible {
          animation: title-entrance 1200ms cubic-bezier(0, 0, 0.2, 1) 600ms forwards;
        }

        .classification-stamp {
          position: absolute;
          top: 2rem;
          right: 2rem;
          padding: 0.5rem 1.5rem;
          border: 2px solid rgba(211, 47, 47, 0.5);
          color: #EF4444;
          font-weight: 700;
          letter-spacing: 0.1em;
          text-transform: uppercase;
          transform: rotate(3deg);
          opacity: 0;
          transform: rotate(3deg) scale(1.5);
        }

        .classification-stamp.visible {
          animation: stamp 500ms cubic-bezier(0.34, 1.56, 0.64, 1) 1000ms forwards;
        }

        @keyframes stamp {
          to {
            opacity: 1;
            transform: rotate(3deg) scale(1);
          }
        }

        @media (max-width: 640px) {
          .logo {
            width: 120px;
            height: 120px;
          }
          .classification-stamp {
            top: 1rem;
            right: 1rem;
            font-size: 0.75rem;
            padding: 0.375rem 1rem;
          }
          .meta {
            flex-direction: column;
            gap: 0.5rem;
            text-align: center;
          }
        }
      </style>

      <canvas class="mesh-gradient" id="meshCanvas"></canvas>

      <div class="content">
        ${logo ? `<img src="${logo}" alt="Company Logo" class="logo" />` : '<div class="logo"></div>'}
        <h1 class="title">${title}</h1>
        <p class="subtitle">${subtitle}</p>
        <div class="meta">
          <time>${date}</time>
          <span>•</span>
          <span>Prepared by Archon AI</span>
        </div>
      </div>

      <div class="classification-stamp">${classification}</div>
    `;
  }

  connectedCallback() {
    super.connectedCallback();
    this._initMeshGradient();
    setTimeout(() => this._triggerAnimations(), 100);
  }

  _triggerAnimations() {
    const elements = this.shadowRoot.querySelectorAll('.logo, .title, .subtitle, .meta, .classification-stamp');
    elements.forEach(el => el.classList.add('visible'));
  }

  _initMeshGradient() {
    const canvas = this.shadowRoot.getElementById('meshCanvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    // Simple animated gradient mesh
    let frame = 0;
    const animate = () => {
      frame++;
      const gradient1 = ctx.createRadialGradient(
        canvas.width * 0.2 + Math.sin(frame * 0.002) * 100,
        canvas.height * 0.5 + Math.cos(frame * 0.003) * 100,
        0,
        canvas.width * 0.2,
        canvas.height * 0.5,
        canvas.width * 0.5
      );
      gradient1.addColorStop(0, 'rgba(0, 102, 204, 0.1)');
      gradient1.addColorStop(1, 'rgba(0, 102, 204, 0)');

      const gradient2 = ctx.createRadialGradient(
        canvas.width * 0.8 + Math.cos(frame * 0.002) * 100,
        canvas.height * 0.8 + Math.sin(frame * 0.003) * 100,
        0,
        canvas.width * 0.8,
        canvas.height * 0.8,
        canvas.width * 0.4
      );
      gradient2.addColorStop(0, 'rgba(212, 175, 55, 0.1)');
      gradient2.addColorStop(1, 'rgba(212, 175, 55, 0)');

      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = gradient1;
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = gradient2;
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      requestAnimationFrame(animate);
    };
    animate();

    window.addEventListener('resize', () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    });
  }
}

// ═══════════════════════════════════════════════════════════════
// SCQA FRAMEWORK COMPONENT
// ═══════════════════════════════════════════════════════════════

class ArchonSCQA extends ArchonComponent {
  static get observedAttributes() {
    return ['situation', 'complication', 'question', 'answer'];
  }

  render() {
    const situation = this.getAttribute('situation') || '';
    const complication = this.getAttribute('complication') || '';
    const question = this.getAttribute('question') || '';
    const answer = this.getAttribute('answer') || '';

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 2rem;
          margin: 3rem 0;
        }

        .scqa-block {
          padding: 2rem;
          border-radius: 8px;
          position: relative;
          overflow: hidden;
          opacity: 0;
          transform: translateY(30px);
          transition: all 300ms cubic-bezier(0, 0, 0.2, 1);
        }

        .scqa-block.visible {
          opacity: 1;
          transform: translateY(0);
        }

        .scqa-block::before {
          content: attr(data-letter);
          position: absolute;
          top: 1rem;
          right: 1rem;
          font-size: 4rem;
          font-weight: 900;
          opacity: 0.05;
          line-height: 1;
        }

        .situation {
          background: linear-gradient(135deg, rgba(0, 128, 255, 0.05) 0%, rgba(0, 128, 255, 0.02) 100%);
          border: 1px solid rgba(0, 128, 255, 0.2);
        }

        .complication {
          background: linear-gradient(135deg, rgba(239, 68, 68, 0.05) 0%, rgba(239, 68, 68, 0.02) 100%);
          border: 1px solid rgba(239, 68, 68, 0.2);
        }

        .question {
          background: linear-gradient(135deg, rgba(245, 158, 11, 0.05) 0%, rgba(245, 158, 11, 0.02) 100%);
          border: 1px solid rgba(245, 158, 11, 0.2);
        }

        .answer {
          background: linear-gradient(135deg, rgba(16, 185, 129, 0.05) 0%, rgba(16, 185, 129, 0.02) 100%);
          border: 1px solid rgba(16, 185, 129, 0.2);
        }

        h3 {
          font-size: 1.125rem;
          margin: 0 0 1rem 0;
          text-transform: uppercase;
          letter-spacing: 0.025em;
          font-weight: 600;
        }

        .situation h3 { color: #0080FF; }
        .complication h3 { color: #EF4444; }
        .question h3 { color: #F59E0B; }
        .answer h3 { color: #10B981; }

        p {
          font-size: 1rem;
          line-height: 1.8;
          color: #0F172A;
          margin: 0;
        }

        @media (max-width: 1024px) {
          :host {
            grid-template-columns: 1fr;
          }
        }
      </style>

      <div class="scqa-block situation" data-letter="S">
        <h3>Situation</h3>
        <p>${situation}</p>
      </div>

      <div class="scqa-block complication" data-letter="C">
        <h3>Complication</h3>
        <p>${complication}</p>
      </div>

      <div class="scqa-block question" data-letter="Q">
        <h3>Question</h3>
        <p>${question}</p>
      </div>

      <div class="scqa-block answer" data-letter="A">
        <h3>Answer</h3>
        <p>${answer}</p>
      </div>
    `;
  }

  onVisible() {
    const blocks = this.shadowRoot.querySelectorAll('.scqa-block');
    blocks.forEach((block, index) => {
      setTimeout(() => {
        block.classList.add('visible');
      }, index * 150);
    });
  }
}

// ═══════════════════════════════════════════════════════════════
// SCENARIO CARDS COMPONENT
// ═══════════════════════════════════════════════════════════════

class ArchonScenarioCards extends ArchonComponent {
  static get observedAttributes() {
    return ['scenarios-data'];
  }

  render() {
    const scenariosData = this.getAttribute('scenarios-data');
    let scenarios = [];

    try {
      scenarios = JSON.parse(scenariosData || '[]');
    } catch (e) {
      console.error('Invalid scenarios data:', e);
    }

    const scenariosHTML = scenarios.map((scenario, index) => {
      const typeClass = scenario.type || 'moderate';
      const isRecommended = scenario.recommended || typeClass === 'moderate';

      return `
        <div class="scenario-card ${typeClass}" data-index="${index}">
          ${isRecommended ? '<div class="recommended-badge">RECOMMENDED</div>' : ''}
          <h4>${scenario.label || 'Scenario'}</h4>

          <div class="scenario-metrics">
            <div class="metric-item">
              <span class="metric-label">Investment</span>
              <span class="metric-value">€${this._formatNumber(scenario.investment)}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">NPV (3y)</span>
              <span class="metric-value">€${this._formatNumber(scenario.npv)}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">ROI</span>
              <span class="metric-value">${scenario.roi}%</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">Payback</span>
              <span class="metric-value">${scenario.payback} mo</span>
            </div>
          </div>

          <div class="probability-bar">
            <div class="probability-label">Success Probability</div>
            <div class="probability-track">
              <div class="probability-fill" style="width: ${scenario.probability || 70}%"></div>
            </div>
            <div class="probability-value">${scenario.probability || 70}%</div>
          </div>
        </div>
      `;
    }).join('');

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
          gap: 1.5rem;
          margin: 2rem 0;
        }

        .scenario-card {
          background: white;
          border-radius: 8px;
          padding: 2rem;
          position: relative;
          box-shadow: 0 4px 8px -1px rgba(0, 0, 0, 0.08);
          opacity: 0;
          transform: translateY(20px);
          transition: all 300ms cubic-bezier(0, 0, 0.2, 1);
        }

        .scenario-card.visible {
          opacity: 1;
          transform: translateY(0);
        }

        .scenario-card:hover {
          transform: translateY(-4px);
          box-shadow: 0 20px 40px -8px rgba(0, 0, 0, 0.15);
        }

        .scenario-card.conservative {
          border-top: 4px solid #64748B;
        }

        .scenario-card.moderate {
          border-top: 4px solid #10B981;
        }

        .scenario-card.aggressive {
          border-top: 4px solid #0080FF;
        }

        .recommended-badge {
          position: absolute;
          top: 1rem;
          right: 1rem;
          background: #10B981;
          color: white;
          padding: 0.25rem 0.5rem;
          border-radius: 4px;
          font-size: 0.625rem;
          font-weight: 700;
          letter-spacing: 0.05em;
        }

        h4 {
          margin: 0 0 1.5rem 0;
          font-size: 1.25rem;
          font-weight: 600;
          color: #0A1929;
        }

        .scenario-metrics {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 1rem;
          margin-bottom: 1.5rem;
        }

        .metric-item {
          display: flex;
          flex-direction: column;
        }

        .metric-label {
          font-size: 0.75rem;
          color: #64748B;
          text-transform: uppercase;
          letter-spacing: 0.025em;
          margin-bottom: 0.25rem;
        }

        .metric-value {
          font-size: 1.125rem;
          font-weight: 600;
          color: #0A1929;
        }

        .probability-bar {
          margin-top: 1rem;
          padding-top: 1rem;
          border-top: 1px solid #E2E8F0;
        }

        .probability-label {
          font-size: 0.75rem;
          color: #64748B;
          text-transform: uppercase;
          letter-spacing: 0.025em;
          margin-bottom: 0.5rem;
        }

        .probability-track {
          height: 6px;
          background: #E2E8F0;
          border-radius: 9999px;
          overflow: hidden;
          margin-bottom: 0.5rem;
        }

        .probability-fill {
          height: 100%;
          background: linear-gradient(90deg, #10B981 0%, #0EA5E9 100%);
          border-radius: 9999px;
          transition: width 1s cubic-bezier(0, 0, 0.2, 1);
        }

        .probability-value {
          text-align: right;
          font-size: 0.875rem;
          font-weight: 600;
          color: #0A1929;
        }

        @media (max-width: 640px) {
          :host {
            grid-template-columns: 1fr;
          }
        }
      </style>

      ${scenariosHTML}
    `;
  }

  _formatNumber(num) {
    if (!num) return '0';
    return new Intl.NumberFormat('pt-PT').format(num);
  }

  onVisible() {
    const cards = this.shadowRoot.querySelectorAll('.scenario-card');
    cards.forEach((card, index) => {
      setTimeout(() => {
        card.classList.add('visible');
      }, index * 100);
    });
  }
}

// ═══════════════════════════════════════════════════════════════
// KPI DASHBOARD COMPONENT
// ═══════════════════════════════════════════════════════════════

class ArchonKPIDashboard extends ArchonComponent {
  static get observedAttributes() {
    return ['metrics-data'];
  }

  render() {
    const metricsData = this.getAttribute('metrics-data');
    let metrics = [];

    try {
      metrics = JSON.parse(metricsData || '[]');
    } catch (e) {
      console.error('Invalid metrics data:', e);
    }

    const metricsHTML = metrics.map((metric, index) => {
      const statusClass = metric.status || 'green';
      const statusEmoji = { green: '🟢', yellow: '🟡', red: '🔴', gray: '⚪' }[statusClass];

      return `
        <div class="kpi-card" data-index="${index}">
          <div class="traffic-light ${statusClass}">${statusEmoji}</div>
          <h5>${metric.name}</h5>
          <div class="kpi-value">${metric.current}${metric.unit}</div>
          <div class="kpi-target">Target: ${metric.target}${metric.unit}</div>
          <div class="kpi-progress">
            <div class="kpi-progress-bar ${statusClass}" style="width: ${metric.progress}%"></div>
          </div>
          <div class="kpi-meta">
            <span>${metric.progress}% complete</span>
            ${metric.trend ? `<span class="trend">${metric.trend}</span>` : ''}
          </div>
        </div>
      `;
    }).join('');

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
          gap: 1.5rem;
          margin: 2rem 0;
        }

        .kpi-card {
          background: white;
          border-radius: 8px;
          padding: 1.5rem;
          position: relative;
          border: 1px solid #E2E8F0;
          opacity: 0;
          transform: scale(0.95);
          transition: all 300ms cubic-bezier(0, 0, 0.2, 1);
        }

        .kpi-card.visible {
          opacity: 1;
          transform: scale(1);
        }

        .kpi-card:hover {
          border-color: #CBD5E1;
          box-shadow: 0 4px 8px -1px rgba(0, 0, 0, 0.08);
        }

        .traffic-light {
          position: absolute;
          top: 1rem;
          right: 1rem;
          font-size: 1.5rem;
        }

        .traffic-light.red {
          animation: pulse-urgent 1s infinite;
        }

        @keyframes pulse-urgent {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.1); }
        }

        h5 {
          margin: 0 0 0.5rem 0;
          font-size: 1rem;
          font-weight: 500;
          color: #334155;
        }

        .kpi-value {
          font-size: 2rem;
          font-weight: 700;
          color: #0A1929;
          margin-bottom: 0.5rem;
          line-height: 1;
        }

        .kpi-target {
          font-size: 0.875rem;
          color: #64748B;
          margin-bottom: 1rem;
        }

        .kpi-progress {
          width: 100%;
          height: 4px;
          background: #E2E8F0;
          border-radius: 9999px;
          overflow: hidden;
          margin-bottom: 0.5rem;
        }

        .kpi-progress-bar {
          height: 100%;
          border-radius: 9999px;
          transition: width 1s cubic-bezier(0, 0, 0.2, 1);
        }

        .kpi-progress-bar.green { background: #10B981; }
        .kpi-progress-bar.yellow { background: #F59E0B; }
        .kpi-progress-bar.red { background: #EF4444; }
        .kpi-progress-bar.gray { background: #94A3B8; }

        .kpi-meta {
          display: flex;
          justify-content: space-between;
          font-size: 0.75rem;
          color: #64748B;
        }

        .trend {
          font-weight: 600;
        }

        @media (max-width: 640px) {
          :host {
            grid-template-columns: 1fr;
          }
        }
      </style>

      ${metricsHTML}
    `;
  }

  onVisible() {
    const cards = this.shadowRoot.querySelectorAll('.kpi-card');
    cards.forEach((card, index) => {
      setTimeout(() => {
        card.classList.add('visible');
      }, index * 50);
    });
  }
}

// ═══════════════════════════════════════════════════════════════
// CALLOUT COMPONENT
// ═══════════════════════════════════════════════════════════════

class ArchonCallout extends ArchonComponent {
  static get observedAttributes() {
    return ['type', 'title'];
  }

  render() {
    const type = this.getAttribute('type') || 'info';
    const title = this.getAttribute('title') || '';
    const content = this.innerHTML;

    const icons = {
      info: 'ℹ️',
      success: '✅',
      warning: '⚠️',
      danger: '❌',
      insight: '💡'
    };

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          padding: 1.5rem;
          border-radius: 8px;
          margin: 2rem 0;
          position: relative;
          padding-left: calc(1.5rem + 40px);
          opacity: 0;
          transform: translateX(-20px);
          transition: all 300ms cubic-bezier(0, 0, 0.2, 1);
        }

        :host(.visible) {
          opacity: 1;
          transform: translateX(0);
        }

        :host([type="info"]) {
          background: rgba(0, 128, 255, 0.05);
          border: 1px solid rgba(0, 128, 255, 0.2);
        }

        :host([type="success"]) {
          background: rgba(16, 185, 129, 0.05);
          border: 1px solid rgba(16, 185, 129, 0.2);
        }

        :host([type="warning"]) {
          background: rgba(245, 158, 11, 0.05);
          border: 1px solid rgba(245, 158, 11, 0.2);
        }

        :host([type="danger"]) {
          background: rgba(239, 68, 68, 0.05);
          border: 1px solid rgba(239, 68, 68, 0.2);
        }

        :host([type="insight"]) {
          background: rgba(212, 175, 55, 0.05);
          border: 1px solid rgba(212, 175, 55, 0.2);
        }

        .icon {
          position: absolute;
          left: 1.5rem;
          top: 1.5rem;
          font-size: 1.5rem;
        }

        h4 {
          margin: 0 0 0.5rem 0;
          font-size: 1.125rem;
          font-weight: 600;
          color: #0A1929;
        }

        .content {
          color: #334155;
          line-height: 1.6;
        }
      </style>

      <div class="icon">${icons[type]}</div>
      ${title ? `<h4>${title}</h4>` : ''}
      <div class="content">
        <slot></slot>
      </div>
    `;
  }

  onVisible() {
    this.classList.add('visible');
  }
}

// ═══════════════════════════════════════════════════════════════
// PAGE BREAK COMPONENT (for print)
// ═══════════════════════════════════════════════════════════════

class ArchonPageBreak extends HTMLElement {
  connectedCallback() {
    this.style.display = 'block';
    this.style.pageBreakAfter = 'always';
    this.style.height = '0';
    this.style.margin = '0';
    this.setAttribute('aria-hidden', 'true');
  }
}

// ═══════════════════════════════════════════════════════════════
// FLOATING TOC COMPONENT
// ═══════════════════════════════════════════════════════════════

class ArchonFloatingTOC extends ArchonComponent {
  connectedCallback() {
    super.connectedCallback();
    this._buildTOC();
    this._setupScrollTracking();
  }

  render() {
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          position: fixed;
          right: 2rem;
          top: 50%;
          transform: translateY(-50%);
          width: 240px;
          background: white;
          border-radius: 8px;
          padding: 1.5rem;
          box-shadow: 0 20px 40px -8px rgba(0, 0, 0, 0.15);
          z-index: 20;
          max-height: 80vh;
          overflow-y: auto;
          opacity: 0;
          transform: translateY(-50%) translateX(20px);
          transition: all 300ms cubic-bezier(0, 0, 0.2, 1);
        }

        :host(.visible) {
          opacity: 1;
          transform: translateY(-50%) translateX(0);
        }

        @media (max-width: 1440px) {
          :host {
            display: none;
          }
        }

        .progress-bar {
          width: 100%;
          height: 4px;
          background: #E2E8F0;
          border-radius: 9999px;
          margin-bottom: 1.5rem;
          overflow: hidden;
        }

        .progress-fill {
          height: 100%;
          background: #D4AF37;
          border-radius: 9999px;
          transition: width 200ms ease-out;
          width: 0%;
        }

        .toc-title {
          font-size: 0.75rem;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: #64748B;
          margin-bottom: 1rem;
        }

        .toc-list {
          list-style: none;
          padding: 0;
          margin: 0;
        }

        .toc-item {
          margin: 0;
          border-left: 2px solid transparent;
          transition: all 200ms ease-out;
        }

        .toc-item.active {
          border-left-color: #D4AF37;
          background: rgba(212, 175, 55, 0.1);
        }

        .toc-link {
          display: flex;
          align-items: center;
          padding: 0.5rem 1rem;
          color: #475569;
          text-decoration: none;
          font-size: 0.875rem;
          transition: all 200ms ease-out;
        }

        .toc-link:hover {
          color: #0A1929;
          background: #F1F5F9;
        }

        .toc-number {
          font-weight: 700;
          margin-right: 0.5rem;
          color: #D4AF37;
          min-width: 1.5rem;
        }

        .toc-text {
          flex: 1;
        }

        .toc-time {
          font-size: 0.75rem;
          color: #94A3B8;
        }
      </style>

      <div class="progress-bar">
        <div class="progress-fill"></div>
      </div>

      <div class="toc-title">Contents</div>
      <ul class="toc-list"></ul>
    `;
  }

  _buildTOC() {
    const sections = document.querySelectorAll('[data-section]');
    const tocList = this.shadowRoot.querySelector('.toc-list');

    sections.forEach((section, index) => {
      const sectionName = section.getAttribute('data-section');
      const sectionTitle = section.querySelector('h2, h3')?.textContent || sectionName;
      const readTime = section.getAttribute('data-read-time') || '3 min';

      const li = document.createElement('li');
      li.className = 'toc-item';
      li.innerHTML = `
        <a href="#${sectionName}" class="toc-link">
          <span class="toc-number">${String(index + 1).padStart(2, '0')}</span>
          <span class="toc-text">${sectionTitle}</span>
          <span class="toc-time">${readTime}</span>
        </a>
      `;
      tocList.appendChild(li);
    });

    setTimeout(() => this.classList.add('visible'), 500);
  }

  _setupScrollTracking() {
    const progressFill = this.shadowRoot.querySelector('.progress-fill');
    const sections = document.querySelectorAll('[data-section]');
    const tocItems = this.shadowRoot.querySelectorAll('.toc-item');

    const updateProgress = () => {
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      const scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
      const progress = (scrollTop / scrollHeight) * 100;
      progressFill.style.width = `${progress}%`;

      // Update active section
      let currentSection = null;
      sections.forEach((section) => {
        const rect = section.getBoundingClientRect();
        if (rect.top <= 100) {
          currentSection = section;
        }
      });

      tocItems.forEach((item, index) => {
        if (currentSection && sections[index] === currentSection) {
          item.classList.add('active');
        } else {
          item.classList.remove('active');
        }
      });
    };

    window.addEventListener('scroll', updateProgress, { passive: true });
    updateProgress();
  }
}

// ═══════════════════════════════════════════════════════════════
// REGISTER ALL COMPONENTS
// ═══════════════════════════════════════════════════════════════

if ('customElements' in window) {
  customElements.define('archon-cover-page', ArchonCoverPage);
  customElements.define('archon-scqa', ArchonSCQA);
  customElements.define('archon-scenario-cards', ArchonScenarioCards);
  customElements.define('archon-kpi-dashboard', ArchonKPIDashboard);
  customElements.define('archon-callout', ArchonCallout);
  customElements.define('archon-page-break', ArchonPageBreak);
  customElements.define('archon-floating-toc', ArchonFloatingTOC);

  console.log('✅ Archon Premium Components v7.0 loaded');
} else {
  console.warn('⚠️ Web Components not supported in this browser');
}

// ═══════════════════════════════════════════════════════════════
// GLOBAL UTILITIES
// ═══════════════════════════════════════════════════════════════

window.ArchonUtils = {
  // Format currency
  formatCurrency(value) {
    return new Intl.NumberFormat('pt-PT', {
      style: 'currency',
      currency: 'EUR'
    }).format(value);
  },

  // Format number
  formatNumber(value) {
    return new Intl.NumberFormat('pt-PT').format(value);
  },

  // Format date
  formatDate(date) {
    return new Intl.DateTimeFormat('pt-PT', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    }).format(new Date(date));
  },

  // Smooth scroll to element
  scrollTo(selector) {
    const element = document.querySelector(selector);
    if (element) {
      element.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      });
    }
  },

  // Trigger all component animations
  triggerAnimations() {
    const components = document.querySelectorAll('archon-cover-page, archon-scqa, archon-scenario-cards, archon-kpi-dashboard, archon-callout');
    components.forEach(component => {
      if (component.onVisible) {
        component.onVisible();
      }
    });
  }
};
