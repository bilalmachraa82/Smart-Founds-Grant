/**
 * End-to-End Test for Smart Grant Buddy App
 * Tests the complete flow with a fictional Portuguese company
 */

const https = require('https');
const http = require('http');

// Fictional Portuguese Company Data
const COMPANY_DATA = {
  name: "InnovaTech Solutions Lda",
  nif: "515789432",
  investment: 450000, // €450,000
  employees: 35,
  turnover: 2500000, // €2,500,000
  projectDescription: `Projeto de Investigação e Desenvolvimento focado na criação de uma plataforma de Inteligência Artificial para otimização de processos industriais.

O projeto visa desenvolver algoritmos avançados de machine learning e visão computacional para automatização de processos de controlo de qualidade na indústria transformadora.

Inclui componentes de:
- Desenvolvimento de modelos de IA proprietários
- Integração com sistemas IoT industriais
- Interface web para gestão e monitorização em tempo real
- Sistema de análise preditiva para manutenção preventiva

O projeto promove a transformação digital e inovação tecnológica, alinhado com os objetivos da Agenda Digital Portuguesa e do PRR.`
};

// Test Configuration
const TEST_CONFIG = {
  appUrl: 'https://smart-grant-buddy.lovable.app',
  legalVersionUrl: 'https://jgewjmhqemhxyzysnbzt.supabase.co/functions/v1/legal-version',
  runAiparatiUrl: 'https://jgewjmhqemhxyzysnbzt.supabase.co/functions/v1/run-aiparati',
  railwayUrl: 'https://eu-founds-grant-production.up.railway.app',
  maxWaitTime: 60000 // 60 seconds max wait
};

// Helper function to make HTTPS requests
function makeRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const protocol = urlObj.protocol === 'https:' ? https : http;

    const reqOptions = {
      hostname: urlObj.hostname,
      port: urlObj.port,
      path: urlObj.pathname + urlObj.search,
      method: options.method || 'GET',
      headers: options.headers || {}
    };

    const req = protocol.request(reqOptions, (res) => {
      let data = '';

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        resolve({
          statusCode: res.statusCode,
          headers: res.headers,
          body: data
        });
      });
    });

    req.on('error', (error) => {
      reject(error);
    });

    if (options.body) {
      req.write(options.body);
    }

    req.end();
  });
}

// Test Results Logger
const testResults = {
  timestamp: new Date().toISOString(),
  companyData: COMPANY_DATA,
  tests: [],
  overallStatus: 'PENDING'
};

function logTest(testName, status, details) {
  const result = {
    test: testName,
    status: status,
    details: details,
    timestamp: new Date().toISOString()
  };
  testResults.tests.push(result);
  console.log(`\n${'='.repeat(80)}`);
  console.log(`TEST: ${testName}`);
  console.log(`STATUS: ${status}`);
  console.log(`DETAILS: ${JSON.stringify(details, null, 2)}`);
  console.log('='.repeat(80));
}

async function runTests() {
  console.log('\n' + '='.repeat(80));
  console.log('SMART GRANT BUDDY - END-TO-END TEST');
  console.log('='.repeat(80));
  console.log('\nFictional Company Data:');
  console.log(JSON.stringify(COMPANY_DATA, null, 2));
  console.log('\n' + '='.repeat(80));

  try {
    // TEST 1: Check if frontend is accessible
    console.log('\n[TEST 1] Checking frontend accessibility...');
    try {
      const frontendResponse = await makeRequest(TEST_CONFIG.appUrl);
      logTest(
        'Frontend Accessibility',
        frontendResponse.statusCode === 200 ? 'PASS' : 'FAIL',
        {
          statusCode: frontendResponse.statusCode,
          contentLength: frontendResponse.body.length,
          hasContent: frontendResponse.body.length > 0
        }
      );
    } catch (error) {
      logTest('Frontend Accessibility', 'FAIL', { error: error.message });
    }

    // TEST 2: Check legal-version endpoint
    console.log('\n[TEST 2] Testing legal-version endpoint...');
    try {
      const legalVersionResponse = await makeRequest(TEST_CONFIG.legalVersionUrl);
      const legalVersionData = JSON.parse(legalVersionResponse.body);
      logTest(
        'Legal Version Endpoint',
        legalVersionResponse.statusCode === 200 ? 'PASS' : 'FAIL',
        {
          statusCode: legalVersionResponse.statusCode,
          hasVersionHash: !!legalVersionData.version_hash,
          versionHash: legalVersionData.version_hash,
          response: legalVersionData
        }
      );
    } catch (error) {
      logTest('Legal Version Endpoint', 'FAIL', { error: error.message });
    }

    // TEST 3: Check Railway backend health
    console.log('\n[TEST 3] Testing Railway backend...');
    try {
      const railwayResponse = await makeRequest(`${TEST_CONFIG.railwayUrl}/health`);
      logTest(
        'Railway Backend Health',
        railwayResponse.statusCode === 200 ? 'PASS' : 'FAIL',
        {
          statusCode: railwayResponse.statusCode,
          response: railwayResponse.body.substring(0, 500)
        }
      );
    } catch (error) {
      logTest('Railway Backend Health', 'FAIL', { error: error.message });
    }

    // TEST 4: Test the main AI analysis endpoint
    console.log('\n[TEST 4] Testing AI analysis (run-aiparati)...');
    console.log('This may take up to 60 seconds...');

    try {
      const payload = {
        companyName: COMPANY_DATA.name,
        nif: COMPANY_DATA.nif,
        investment: COMPANY_DATA.investment,
        employees: COMPANY_DATA.employees,
        turnover: COMPANY_DATA.turnover,
        description: COMPANY_DATA.projectDescription
      };

      const startTime = Date.now();
      const analysisResponse = await makeRequest(TEST_CONFIG.runAiparatiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(payload)
      });
      const responseTime = Date.now() - startTime;

      let analysisData;
      try {
        analysisData = JSON.parse(analysisResponse.body);
      } catch (e) {
        analysisData = { raw: analysisResponse.body };
      }

      const testStatus = analysisResponse.statusCode === 200 ? 'PASS' : 'FAIL';

      logTest(
        'AI Analysis Endpoint',
        testStatus,
        {
          statusCode: analysisResponse.statusCode,
          responseTime: `${responseTime}ms`,
          responseTimeOk: responseTime < 30000,
          hasEligibility: !!(analysisData.eligibility || analysisData.analysis?.eligibility),
          hasIncentive: !!(analysisData.incentive || analysisData.analysis?.incentive),
          hasScoring: !!(analysisData.scoring || analysisData.analysis?.scoring),
          hasCitations: !!(analysisData.citations),
          citationCount: analysisData.citations ? analysisData.citations.length : 0,
          hasDocuments: !!(analysisData.generated_documents || analysisData.documents),
          responseKeys: Object.keys(analysisData)
        }
      );

      // TEST 5: Validate response structure
      console.log('\n[TEST 5] Validating response structure...');

      const validationChecks = {
        hasEligibilityAnalysis: !!(analysisData.eligibility || analysisData.analysis?.eligibility),
        hasIncentiveCalculation: !!(analysisData.incentive || analysisData.analysis?.incentive),
        hasScoringInfo: !!(analysisData.scoring || analysisData.analysis?.scoring),
        hasCitations: !!(analysisData.citations),
        citationCount: analysisData.citations ? analysisData.citations.length : 0,
        expectedCitationCount: analysisData.citations ? analysisData.citations.length >= 20 : false,
        hasGeneratedDocuments: !!(analysisData.generated_documents || analysisData.documents),
        responseTimeUnder30s: responseTime < 30000
      };

      const allChecksPassed = Object.values(validationChecks).every(v =>
        typeof v === 'boolean' ? v : true
      );

      logTest(
        'Response Structure Validation',
        allChecksPassed ? 'PASS' : 'PARTIAL',
        validationChecks
      );

      // TEST 6: Detailed analysis output
      console.log('\n[TEST 6] Analyzing detailed output...');

      const detailedAnalysis = {
        fullResponse: analysisData,
        eligibility: analysisData.eligibility || analysisData.analysis?.eligibility || 'N/A',
        incentive: analysisData.incentive || analysisData.analysis?.incentive || 'N/A',
        scoring: analysisData.scoring || analysisData.analysis?.scoring || 'N/A',
        citationsSample: analysisData.citations ? analysisData.citations.slice(0, 5) : [],
        documents: analysisData.generated_documents || analysisData.documents || 'N/A'
      };

      logTest(
        'Detailed Analysis Output',
        'INFO',
        detailedAnalysis
      );

      // Determine overall status
      const criticalTestsPassed = testResults.tests.filter(t =>
        ['Frontend Accessibility', 'AI Analysis Endpoint'].includes(t.test) &&
        t.status === 'PASS'
      ).length === 2;

      testResults.overallStatus = criticalTestsPassed ? 'WORKING' : 'FAILING';

    } catch (error) {
      logTest('AI Analysis Endpoint', 'FAIL', {
        error: error.message,
        stack: error.stack
      });
      testResults.overallStatus = 'FAILING';
    }

  } catch (error) {
    console.error('Fatal error during testing:', error);
    testResults.overallStatus = 'FAILING';
    testResults.fatalError = error.message;
  }

  // Final Report
  console.log('\n\n' + '='.repeat(80));
  console.log('FINAL TEST REPORT');
  console.log('='.repeat(80));
  console.log(`\nOverall Status: ${testResults.overallStatus === 'WORKING' ? '✅ WORKING' : '❌ FAILING'}`);
  console.log(`\nTotal Tests Run: ${testResults.tests.length}`);
  console.log(`Passed: ${testResults.tests.filter(t => t.status === 'PASS').length}`);
  console.log(`Failed: ${testResults.tests.filter(t => t.status === 'FAIL').length}`);
  console.log(`Partial: ${testResults.tests.filter(t => t.status === 'PARTIAL').length}`);

  console.log('\n' + '='.repeat(80));
  console.log('TEST SUMMARY');
  console.log('='.repeat(80));
  testResults.tests.forEach(test => {
    const icon = test.status === 'PASS' ? '✅' : test.status === 'FAIL' ? '❌' : 'ℹ️';
    console.log(`${icon} ${test.test}: ${test.status}`);
  });

  console.log('\n' + '='.repeat(80));

  // Save results to file
  const fs = require('fs');
  const resultsFile = `/Users/bilal/Programaçao/Smart Founds Grant/Archon/test-results-${Date.now()}.json`;
  fs.writeFileSync(resultsFile, JSON.stringify(testResults, null, 2));
  console.log(`\nDetailed results saved to: ${resultsFile}`);

  process.exit(testResults.overallStatus === 'WORKING' ? 0 : 1);
}

// Run the tests
runTests().catch(error => {
  console.error('Unhandled error:', error);
  process.exit(1);
});
