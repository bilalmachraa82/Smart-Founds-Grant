/**
 * ═══════════════════════════════════════════════════════════════
 * ARCHON LOADER v3.0 - Progressive Enhancement Orchestrator
 * ═══════════════════════════════════════════════════════════════
 *
 * Responsabilidades:
 * 1. Lazy loading de assets pesados (Three.js, ApexCharts, Prism.js)
 * 2. IntersectionObserver para carregar só quando visível
 * 3. Inicialização de charts com dados do JSON embebido
 * 4. Parse de markdown com callouts custom
 * 5. Gestão de checkboxes de ações com progresso
 *
 * @author Claude Code (Anthropic)
 * @version 3.0.0
 * @license MIT
 */

// ═══════════════════════════════════════════════════════════════
// CONFIGURATION
// ═══════════════════════════════════════════════════════════════

const ARCHON_CONFIG = {
  // CDN URLs
  cdn: {
    threejs: 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js',
    apexcharts: 'https://cdn.jsdelivr.net/npm/apexcharts@3.45.0/dist/apexcharts.min.js',
    prismCore: 'https://cdn.jsdelivr.net/npm/prismjs@1.29.0/prism.min.js',
    prismCSS: 'https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism-tomorrow.min.css',
    prismMarkdown: 'https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-markdown.min.js',
    prismPython: 'https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-python.min.js'
  },

  // IntersectionObserver thresholds
  observerOptions: {
    root: null,
    rootMargin: '100px', // Start loading 100px before visible
    threshold: 0.1
  },

  // Loaded state tracking
  loaded: {
    threejs: false,
    apexcharts: false,
    prism: false
  }
};

// ═══════════════════════════════════════════════════════════════
// UTILITY FUNCTIONS
// ═══════════════════════════════════════════════════════════════

/**
 * Load external script dynamically
 * @param {string} url - Script URL
 * @param {boolean} isModule - Load as ES module
 * @returns {Promise<void>}
 */
function loadScript(url, isModule = false) {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = url;
    if (isModule) script.type = 'module';
    script.onload = () => resolve();
    script.onerror = () => reject(new Error(`Failed to load script: ${url}`));
    document.head.appendChild(script);
  });
}

/**
 * Load external CSS stylesheet
 * @param {string} url - CSS URL
 * @returns {Promise<void>}
 */
function loadCSS(url) {
  return new Promise((resolve, reject) => {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = url;
    link.onload = () => resolve();
    link.onerror = () => reject(new Error(`Failed to load CSS: ${url}`));
    document.head.appendChild(link);
  });
}

/**
 * Get embedded chart data from JSON script tag
 * @returns {Object} Chart data
 */
function getChartData() {
  const scriptTag = document.getElementById('chart-data');
  if (!scriptTag) {
    console.error('Chart data not found in HTML');
    return null;
  }
  try {
    return JSON.parse(scriptTag.textContent);
  } catch (error) {
    console.error('Failed to parse chart data:', error);
    return null;
  }
}

// ═══════════════════════════════════════════════════════════════
// THREE.JS BACKGROUND LOADER
// ═══════════════════════════════════════════════════════════════

/**
 * Initialize Three.js animated mesh gradient background
 */
async function initThreeJSBackground() {
  if (ARCHON_CONFIG.loaded.threejs) return;

  const canvas = document.getElementById('three-canvas');
  if (!canvas) return;

  try {
    console.log('[Archon] Loading Three.js...');

    // Dynamically import Three.js as ES module
    const THREE = await import(ARCHON_CONFIG.cdn.threejs);

    // Scene setup
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({
      canvas: canvas,
      alpha: true,
      antialias: true
    });

    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    canvas.style.display = 'block';

    camera.position.z = 5;

    // Create gradient mesh geometry
    const geometry = new THREE.SphereGeometry(15, 32, 32);

    // Custom shader material for smooth gradients
    const material = new THREE.ShaderMaterial({
      uniforms: {
        time: { value: 0 },
        color1: { value: new THREE.Color('#0066CC') }, // Archon Blue
        color2: { value: new THREE.Color('#10B981') }, // PRR Green
        color3: { value: new THREE.Color('#0A2540') }  // Deep Ocean
      },
      vertexShader: `
        varying vec3 vPosition;
        varying vec3 vNormal;
        uniform float time;

        void main() {
          vPosition = position;
          vNormal = normal;

          // Animate vertices with sine wave
          vec3 pos = position;
          pos.x += sin(position.y * 0.5 + time * 0.3) * 0.3;
          pos.y += cos(position.x * 0.5 + time * 0.2) * 0.3;
          pos.z += sin(position.z * 0.5 + time * 0.4) * 0.3;

          gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
        }
      `,
      fragmentShader: `
        uniform vec3 color1;
        uniform vec3 color2;
        uniform vec3 color3;
        uniform float time;
        varying vec3 vPosition;
        varying vec3 vNormal;

        void main() {
          // Smooth gradient blending
          float mixValue1 = (vPosition.y + 5.0) / 10.0;
          float mixValue2 = (vPosition.x + 5.0) / 10.0;

          vec3 color = mix(color1, color2, mixValue1);
          color = mix(color, color3, mixValue2 * 0.5);

          // Subtle pulse effect
          color *= 0.8 + 0.2 * sin(time * 0.5);

          gl_FragColor = vec4(color, 0.15); // Low opacity for subtlety
        }
      `,
      transparent: true,
      side: THREE.DoubleSide
    });

    const mesh = new THREE.Mesh(geometry, material);
    scene.add(mesh);

    // Animation loop
    function animate() {
      requestAnimationFrame(animate);

      material.uniforms.time.value += 0.01;
      mesh.rotation.x += 0.001;
      mesh.rotation.y += 0.002;

      renderer.render(scene, camera);
    }

    animate();

    // Handle window resize
    window.addEventListener('resize', () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    });

    ARCHON_CONFIG.loaded.threejs = true;
    console.log('[Archon] Three.js background initialized ✓');

  } catch (error) {
    console.error('[Archon] Three.js initialization failed:', error);
    // Fallback: hide canvas, CSS gradient shows instead
    canvas.style.display = 'none';
  }
}

// ═══════════════════════════════════════════════════════════════
// APEXCHARTS LOADER
// ═══════════════════════════════════════════════════════════════

/**
 * Load and initialize ApexCharts with brand theme
 */
async function initApexCharts() {
  if (ARCHON_CONFIG.loaded.apexcharts) return;

  try {
    console.log('[Archon] Loading ApexCharts...');

    // Load ApexCharts library
    await loadScript(ARCHON_CONFIG.cdn.apexcharts);

    // Wait for global ApexCharts object
    if (typeof ApexCharts === 'undefined') {
      throw new Error('ApexCharts not loaded');
    }

    // Get chart data from embedded JSON
    const data = getChartData();
    if (!data) return;

    // Brand color palette
    const colors = {
      archonBlue: '#0066CC',
      prrGreen: '#10B981',
      gold: '#F59E0B',
      red: '#EF4444',
      purple: '#8B5CF6',
      slate: '#64748B'
    };

    // Global theme configuration
    const globalTheme = {
      chart: {
        fontFamily: 'Inter, -apple-system, system-ui, sans-serif',
        toolbar: { show: false },
        animations: {
          enabled: true,
          easing: 'easeinout',
          speed: 800
        }
      },
      theme: {
        mode: 'light',
        palette: 'palette1'
      },
      dataLabels: {
        enabled: true,
        style: {
          fontSize: '14px',
          fontWeight: 600
        }
      },
      stroke: {
        width: 2,
        curve: 'smooth'
      },
      grid: {
        borderColor: '#E2E8F0',
        strokeDashArray: 4
      },
      tooltip: {
        theme: 'light',
        style: {
          fontSize: '14px'
        }
      }
    };

    // ──────────────────────────────────────────────────────────
    // Chart 1: Score Gauge (Radial Bar)
    // ──────────────────────────────────────────────────────────
    const scoreGaugeOptions = {
      ...globalTheme,
      series: [data.score.normalized],
      chart: {
        ...globalTheme.chart,
        type: 'radialBar',
        height: 350
      },
      plotOptions: {
        radialBar: {
          startAngle: -135,
          endAngle: 135,
          hollow: {
            size: '65%',
            background: 'transparent'
          },
          track: {
            background: '#E2E8F0',
            strokeWidth: '100%'
          },
          dataLabels: {
            name: {
              fontSize: '16px',
              color: '#64748B',
              offsetY: -10
            },
            value: {
              fontSize: '48px',
              fontWeight: 900,
              color: '#0F172A',
              offsetY: 10,
              formatter: function (val) {
                return (val / 10).toFixed(1);
              }
            }
          }
        }
      },
      fill: {
        type: 'gradient',
        gradient: {
          shade: 'dark',
          type: 'horizontal',
          shadeIntensity: 0.5,
          gradientToColors: [colors.prrGreen],
          inverseColors: false,
          opacityFrom: 1,
          opacityTo: 1,
          stops: [0, 100]
        }
      },
      colors: [colors.archonBlue],
      labels: [`Classe ${data.score.class}`]
    };

    const scoreGaugeChart = new ApexCharts(
      document.querySelector('#score-gauge-chart'),
      scoreGaugeOptions
    );
    scoreGaugeChart.render();

    // ──────────────────────────────────────────────────────────
    // Chart 2: Budget Donut
    // ──────────────────────────────────────────────────────────
    const budgetDonutOptions = {
      ...globalTheme,
      series: [
        data.budget.saas,
        data.budget.consulting,
        data.budget.training,
        data.budget.hr,
        data.budget.roc
      ],
      chart: {
        ...globalTheme.chart,
        type: 'donut',
        height: 350
      },
      labels: ['SaaS', 'Consultoria', 'Formação', 'RH', 'ROC'],
      colors: [
        colors.archonBlue,
        colors.prrGreen,
        colors.gold,
        colors.purple,
        colors.slate
      ],
      plotOptions: {
        pie: {
          donut: {
            size: '70%',
            labels: {
              show: true,
              name: {
                fontSize: '16px',
                fontWeight: 600
              },
              value: {
                fontSize: '24px',
                fontWeight: 900,
                formatter: function (val) {
                  return `${parseFloat(val).toLocaleString('pt-PT')}€`;
                }
              },
              total: {
                show: true,
                label: 'Total',
                fontSize: '18px',
                fontWeight: 600,
                color: '#64748B',
                formatter: function (w) {
                  const total = w.globals.seriesTotals.reduce((a, b) => a + b, 0);
                  return `${total.toLocaleString('pt-PT')}€`;
                }
              }
            }
          }
        }
      },
      legend: {
        position: 'bottom',
        fontSize: '14px',
        fontWeight: 500
      }
    };

    const budgetDonutChart = new ApexCharts(
      document.querySelector('#budget-donut-chart'),
      budgetDonutOptions
    );
    budgetDonutChart.render();

    // ──────────────────────────────────────────────────────────
    // Chart 3: Eligibility Heatmap
    // ──────────────────────────────────────────────────────────
    const eligibilityHeatmapOptions = {
      ...globalTheme,
      series: [
        {
          name: 'Elegibilidade',
          data: [
            { x: 'PME', y: data.eligibility.pme === 'yes' ? 100 : 0 },
            { x: 'Investimento', y: data.eligibility.investment === 'yes' ? 100 : 0 },
            { x: 'CAE', y: data.eligibility.cae === 'yes' ? 100 : 0 },
            { x: 'Localização', y: data.eligibility.location === 'yes' ? 100 : 0 },
            { x: 'Inovação', y: data.eligibility.innovation === 'yes' ? 100 : 50 }
          ]
        }
      ],
      chart: {
        ...globalTheme.chart,
        type: 'heatmap',
        height: 300
      },
      plotOptions: {
        heatmap: {
          colorScale: {
            ranges: [
              { from: 0, to: 0, color: colors.red, name: 'Não Cumpre' },
              { from: 1, to: 50, color: colors.gold, name: 'Parcial' },
              { from: 51, to: 100, color: colors.prrGreen, name: 'Cumpre' }
            ]
          }
        }
      },
      dataLabels: {
        enabled: true,
        formatter: function (val) {
          return val === 100 ? '✓' : val === 0 ? '✗' : '~';
        },
        style: {
          fontSize: '24px',
          fontWeight: 900
        }
      }
    };

    const eligibilityHeatmapChart = new ApexCharts(
      document.querySelector('#eligibility-heatmap-chart'),
      eligibilityHeatmapOptions
    );
    eligibilityHeatmapChart.render();

    ARCHON_CONFIG.loaded.apexcharts = true;
    console.log('[Archon] ApexCharts initialized ✓');

  } catch (error) {
    console.error('[Archon] ApexCharts initialization failed:', error);
  }
}

// ═══════════════════════════════════════════════════════════════
// PRISM.JS MARKDOWN PARSER
// ═══════════════════════════════════════════════════════════════

/**
 * Initialize Prism.js for syntax highlighting
 */
async function initPrism() {
  if (ARCHON_CONFIG.loaded.prism) return;

  try {
    console.log('[Archon] Loading Prism.js...');

    // Load Prism CSS theme
    await loadCSS(ARCHON_CONFIG.cdn.prismCSS);

    // Load Prism core
    await loadScript(ARCHON_CONFIG.cdn.prismCore);

    // Load language plugins
    await Promise.all([
      loadScript(ARCHON_CONFIG.cdn.prismMarkdown),
      loadScript(ARCHON_CONFIG.cdn.prismPython)
    ]);

    // Wait for global Prism object
    if (typeof Prism === 'undefined') {
      throw new Error('Prism not loaded');
    }

    // Highlight all code blocks in markdown content
    Prism.highlightAllUnder(document.querySelector('.markdown-content'));

    // Parse custom callouts (convert markdown to styled divs)
    parseCallouts();

    ARCHON_CONFIG.loaded.prism = true;
    console.log('[Archon] Prism.js initialized ✓');

  } catch (error) {
    console.error('[Archon] Prism.js initialization failed:', error);
  }
}

/**
 * Parse custom callout syntax in markdown
 * Converts:
 * > ⚠️ **Warning:** Text
 * Into:
 * <div class="callout callout-warning">...</div>
 */
function parseCallouts() {
  const markdownContent = document.querySelector('.markdown-content');
  if (!markdownContent) return;

  const html = markdownContent.innerHTML;

  // Callout patterns
  const patterns = [
    {
      regex: />\s*✅\s*\*\*(.*?):\*\*(.*?)(?=\n|$)/g,
      type: 'success',
      icon: '✅'
    },
    {
      regex: />\s*⚠️\s*\*\*(.*?):\*\*(.*?)(?=\n|$)/g,
      type: 'warning',
      icon: '⚠️'
    },
    {
      regex: />\s*❌\s*\*\*(.*?):\*\*(.*?)(?=\n|$)/g,
      type: 'danger',
      icon: '❌'
    },
    {
      regex: />\s*ℹ️\s*\*\*(.*?):\*\*(.*?)(?=\n|$)/g,
      type: 'info',
      icon: 'ℹ️'
    }
  ];

  let newHtml = html;

  patterns.forEach(pattern => {
    newHtml = newHtml.replace(pattern.regex, (match, title, content) => {
      return `
        <div class="callout callout-${pattern.type}">
          <div class="callout-title">
            <span class="callout-icon">${pattern.icon}</span>
            ${title.trim()}
          </div>
          <div class="callout-content">${content.trim()}</div>
        </div>
      `;
    });
  });

  markdownContent.innerHTML = newHtml;
}

// ═══════════════════════════════════════════════════════════════
// ACTION PLAN PROGRESS TRACKER
// ═══════════════════════════════════════════════════════════════

/**
 * Initialize action checkboxes with progress tracking
 */
function initActionProgress() {
  const actionCheckboxes = document.querySelectorAll('.action-checkbox');
  const progressRing = document.querySelector('.action-progress archon-progress');

  if (!actionCheckboxes.length || !progressRing) return;

  // Update progress when checkboxes change
  actionCheckboxes.forEach(checkbox => {
    checkbox.addEventListener('change', () => {
      const total = actionCheckboxes.length;
      const checked = document.querySelectorAll('.action-checkbox:checked').length;

      // Update progress ring
      progressRing.setAttribute('value', checked);

      // Visual feedback
      if (checked === total) {
        progressRing.setAttribute('variant', 'success');
        showCompletionMessage();
      }
    });
  });

  console.log('[Archon] Action progress tracker initialized ✓');
}

/**
 * Show completion celebration when all actions are checked
 */
function showCompletionMessage() {
  const hint = document.querySelector('.progress-hint');
  if (hint) {
    hint.innerHTML = '🎉 <strong>Todas as ações completas!</strong> Candidatura pronta para submissão.';
    hint.style.color = 'hsl(var(--color-prr-green-700))';
  }
}

// ═══════════════════════════════════════════════════════════════
// INTERSECTION OBSERVER SETUP
// ═══════════════════════════════════════════════════════════════

/**
 * Setup lazy loading observers for each section
 */
function setupLazyLoading() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const sectionId = entry.target.id;

        switch (sectionId) {
          case 'hero-section':
            initThreeJSBackground();
            break;
          case 'charts-section':
            initApexCharts();
            break;
          case 'content-section':
            initPrism();
            break;
        }

        // Unobserve after loading (one-time trigger)
        observer.unobserve(entry.target);
      }
    });
  }, ARCHON_CONFIG.observerOptions);

  // Observe key sections
  const sections = ['hero-section', 'charts-section', 'content-section'];
  sections.forEach(id => {
    const section = document.getElementById(id);
    if (section) observer.observe(section);
  });

  console.log('[Archon] Lazy loading observers initialized ✓');
}

// ═══════════════════════════════════════════════════════════════
// INITIALIZATION
// ═══════════════════════════════════════════════════════════════

/**
 * Main initialization function
 * Runs when DOM is ready
 */
function init() {
  console.log('[Archon] Initializing Premium Report v3.0...');

  // Setup lazy loading with IntersectionObserver
  setupLazyLoading();

  // Initialize action progress tracker (always runs, lightweight)
  initActionProgress();

  console.log('[Archon] Initialization complete ✓');
}

// Run when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

// Export for debugging
window.ArchonLoader = {
  config: ARCHON_CONFIG,
  initThreeJSBackground,
  initApexCharts,
  initPrism,
  initActionProgress
};
