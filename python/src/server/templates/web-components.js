/**
 * ═══════════════════════════════════════════════════════════════
 * ARCHON WEB COMPONENTS v3.0
 * ═══════════════════════════════════════════════════════════════
 *
 * Modern, reusable, framework-agnostic components
 * Using native Web Components API (Custom Elements v1)
 *
 * Browser support: Chrome 54+, Safari 10.1+, Firefox 63+
 * Polyfill not needed for 2025 targets
 */

/* ═══════════════════════════════════════════════════════════════
   BASE COMPONENT CLASS - Shared functionality
   ═══════════════════════════════════════════════════════════════ */

class ArchonComponent extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  /**
   * Utility: Create element with attributes
   */
  createElement(tag, attrs = {}, content = '') {
    const el = document.createElement(tag);
    Object.entries(attrs).forEach(([key, value]) => {
      if (key.startsWith('on')) {
        el.addEventListener(key.substring(2).toLowerCase(), value);
      } else if (key === 'class') {
        el.className = value;
      } else {
        el.setAttribute(key, value);
      }
    });
    if (content) el.innerHTML = content;
    return el;
  }

  /**
   * Utility: Load design system styles into shadow DOM
   */
  loadDesignSystem() {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = '/templates/design-system.css';
    this.shadowRoot.appendChild(link);
  }
}

/* ═══════════════════════════════════════════════════════════════
   <archon-badge> - Status/category badges
   ═══════════════════════════════════════════════════════════════

   Usage:
   <archon-badge variant="success">Elegível</archon-badge>
   <archon-badge variant="warning" size="lg">Condicional</archon-badge>
   <archon-badge variant="danger" glow>Não Elegível</archon-badge>
   ═══════════════════════════════════════════════════════════════ */

class ArchonBadge extends ArchonComponent {
  static get observedAttributes() {
    return ['variant', 'size', 'glow', 'pulse'];
  }

  connectedCallback() {
    this.render();
  }

  attributeChangedCallback() {
    this.render();
  }

  render() {
    const variant = this.getAttribute('variant') || 'default';
    const size = this.getAttribute('size') || 'md';
    const glow = this.hasAttribute('glow');
    const pulse = this.hasAttribute('pulse');

    const variantClasses = {
      success: 'badge-success',
      warning: 'badge-warning',
      danger: 'badge-danger',
      info: 'badge-info',
      default: 'badge-default'
    };

    const sizeClasses = {
      sm: 'badge-sm',
      md: 'badge-md',
      lg: 'badge-lg',
      xl: 'badge-xl'
    };

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: inline-flex;
          align-items: center;
        }

        .badge {
          display: inline-flex;
          align-items: center;
          gap: var(--space-2);
          font-family: var(--font-body);
          font-weight: var(--font-weight-medium);
          border-radius: var(--radius-full);
          transition: all var(--duration-base) var(--ease-smooth);
          white-space: nowrap;
        }

        /* Sizes */
        .badge-sm {
          padding: var(--space-1) var(--space-3);
          font-size: var(--font-size-xs);
        }

        .badge-md {
          padding: var(--space-1-5) var(--space-4);
          font-size: var(--font-size-sm);
        }

        .badge-lg {
          padding: var(--space-2) var(--space-6);
          font-size: var(--font-size-base);
        }

        .badge-xl {
          padding: var(--space-3) var(--space-8);
          font-size: var(--font-size-lg);
        }

        /* Variants */
        .badge-success {
          background: hsl(var(--color-prr-green-100));
          color: hsl(var(--color-prr-green-700));
          border: 1px solid hsl(var(--color-prr-green-300));
        }

        .badge-warning {
          background: hsl(var(--color-gold-100));
          color: hsl(158 100% 25%); /* Darker for contrast */
          border: 1px solid hsl(var(--color-gold-400));
        }

        .badge-danger {
          background: hsl(var(--color-danger-100));
          color: hsl(var(--color-danger-700));
          border: 1px solid hsl(0 84% 80%);
        }

        .badge-info {
          background: hsl(var(--color-archon-blue-100));
          color: hsl(var(--color-archon-blue-700));
          border: 1px solid hsl(var(--color-archon-blue-300));
        }

        .badge-default {
          background: hsl(var(--color-slate-100));
          color: hsl(var(--color-slate-700));
          border: 1px solid hsl(var(--color-slate-300));
        }

        /* Glow effect */
        .badge-glow.badge-success {
          box-shadow: 0 0 20px hsla(var(--color-prr-green-500) / 0.4);
        }

        .badge-glow.badge-warning {
          box-shadow: 0 0 20px hsla(var(--color-gold-500) / 0.4);
        }

        .badge-glow.badge-danger {
          box-shadow: 0 0 20px hsla(var(--color-danger-500) / 0.4);
        }

        /* Pulse animation */
        @keyframes badge-pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.7; }
        }

        .badge-pulse {
          animation: badge-pulse 2s var(--ease-in-out) infinite;
        }

        .pulse-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: currentColor;
          animation: pulse-dot 2s var(--ease-in-out) infinite;
        }

        @keyframes pulse-dot {
          0%, 100% {
            transform: scale(1);
            opacity: 1;
          }
          50% {
            transform: scale(1.5);
            opacity: 0.5;
          }
        }
      </style>
      <span class="badge ${variantClasses[variant]} ${sizeClasses[size]} ${glow ? 'badge-glow' : ''} ${pulse ? 'badge-pulse' : ''}">
        ${pulse ? '<span class="pulse-dot"></span>' : ''}
        <slot></slot>
      </span>
    `;
  }
}

customElements.define('archon-badge', ArchonBadge);

/* ═══════════════════════════════════════════════════════════════
   <archon-card> - Flexible card container
   ═══════════════════════════════════════════════════════════════

   Usage:
   <archon-card>
     <h3 slot="header">Card Title</h3>
     <p>Card content goes here</p>
     <div slot="footer">Footer content</div>
   </archon-card>
   ═══════════════════════════════════════════════════════════════ */

class ArchonCard extends ArchonComponent {
  static get observedAttributes() {
    return ['variant', 'hover', 'glass'];
  }

  connectedCallback() {
    this.render();
  }

  attributeChangedCallback() {
    this.render();
  }

  render() {
    const variant = this.getAttribute('variant') || 'default';
    const hover = this.hasAttribute('hover');
    const glass = this.hasAttribute('glass');

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
        }

        .card {
          background: hsl(var(--color-slate-50));
          border: 1px solid hsl(var(--color-slate-200));
          border-radius: var(--radius-2xl);
          overflow: hidden;
          transition: all var(--duration-medium) var(--ease-smooth);
        }

        .card-glass {
          background: hsla(var(--color-slate-50) / 0.8);
          backdrop-filter: var(--backdrop-blur-md);
          border: 1px solid hsla(var(--color-slate-200) / 0.5);
        }

        .card-hover:hover {
          transform: translateY(-4px);
          box-shadow: var(--shadow-xl);
          border-color: hsl(var(--color-archon-blue-300));
        }

        .card-header {
          padding: var(--space-6);
          border-bottom: 1px solid hsl(var(--color-slate-200));
        }

        .card-body {
          padding: var(--space-6);
        }

        .card-footer {
          padding: var(--space-6);
          border-top: 1px solid hsl(var(--color-slate-200));
          background: hsl(var(--color-slate-100) / 0.5);
        }

        /* Variant styles */
        .card-primary {
          border-color: hsl(var(--color-archon-blue-300));
        }

        .card-primary .card-header {
          background: linear-gradient(135deg,
            hsl(var(--color-archon-blue-50)),
            hsl(var(--color-slate-50)));
        }

        .card-success {
          border-color: hsl(var(--color-prr-green-300));
        }

        .card-success .card-header {
          background: linear-gradient(135deg,
            hsl(var(--color-prr-green-50)),
            hsl(var(--color-slate-50)));
        }

        @media (prefers-color-scheme: dark) {
          .card {
            background: hsl(var(--color-slate-900));
            border-color: hsl(var(--color-slate-700));
          }

          .card-glass {
            background: hsla(var(--color-slate-900) / 0.6);
            border: 1px solid hsla(var(--color-slate-700) / 0.3);
          }

          .card-header,
          .card-footer {
            border-color: hsl(var(--color-slate-700));
          }

          .card-footer {
            background: hsl(var(--color-slate-800) / 0.5);
          }
        }
      </style>
      <div class="card card-${variant} ${hover ? 'card-hover' : ''} ${glass ? 'card-glass' : ''}">
        <div class="card-header">
          <slot name="header"></slot>
        </div>
        <div class="card-body">
          <slot></slot>
        </div>
        <div class="card-footer">
          <slot name="footer"></slot>
        </div>
      </div>
    `;
  }
}

customElements.define('archon-card', ArchonCard);

/* ═══════════════════════════════════════════════════════════════
   <archon-metric> - Metric display card (KPI)
   ═══════════════════════════════════════════════════════════════

   Usage:
   <archon-metric
     label="Score Mérito"
     value="6.8"
     suffix="/10"
     trend="up"
     icon="📈">
   </archon-metric>
   ═══════════════════════════════════════════════════════════════ */

class ArchonMetric extends ArchonComponent {
  static get observedAttributes() {
    return ['label', 'value', 'suffix', 'trend', 'icon', 'variant'];
  }

  connectedCallback() {
    this.render();
  }

  attributeChangedCallback() {
    this.render();
  }

  render() {
    const label = this.getAttribute('label') || '';
    const value = this.getAttribute('value') || '0';
    const suffix = this.getAttribute('suffix') || '';
    const trend = this.getAttribute('trend'); // 'up' | 'down' | null
    const icon = this.getAttribute('icon') || '';
    const variant = this.getAttribute('variant') || 'default';

    const trendIcon = trend === 'up' ? '↗' : trend === 'down' ? '↘' : '';
    const trendColor = trend === 'up' ? 'var(--color-prr-green-500)' :
                       trend === 'down' ? 'var(--color-danger-500)' :
                       'var(--color-slate-500)';

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
        }

        .metric {
          background: hsl(var(--color-slate-50));
          border: 2px solid hsl(var(--color-slate-200));
          border-radius: var(--radius-xl);
          padding: var(--space-6);
          transition: all var(--duration-base) var(--ease-smooth);
        }

        .metric:hover {
          border-color: hsl(var(--color-archon-blue-300));
          box-shadow: var(--shadow-md);
        }

        .metric-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: var(--space-4);
        }

        .metric-icon {
          font-size: var(--font-size-2xl);
          opacity: 0.8;
        }

        .metric-label {
          font-size: var(--font-size-sm);
          font-weight: var(--font-weight-medium);
          color: hsl(var(--color-slate-600));
          text-transform: uppercase;
          letter-spacing: var(--letter-spacing-wide);
        }

        .metric-value {
          font-size: var(--font-size-4xl);
          font-weight: var(--font-weight-bold);
          color: hsl(var(--color-slate-900));
          line-height: var(--line-height-tight);
          font-variant-numeric: tabular-nums;
        }

        .metric-suffix {
          font-size: var(--font-size-xl);
          font-weight: var(--font-weight-normal);
          color: hsl(var(--color-slate-600));
          margin-left: var(--space-1);
        }

        .metric-trend {
          display: inline-flex;
          align-items: center;
          gap: var(--space-1);
          margin-top: var(--space-2);
          font-size: var(--font-size-sm);
          font-weight: var(--font-weight-medium);
        }

        .metric-trend-icon {
          font-size: var(--font-size-base);
        }

        /* Variant colors */
        .metric-primary .metric-value {
          color: hsl(var(--color-archon-blue-600));
        }

        .metric-success .metric-value {
          color: hsl(var(--color-prr-green-600));
        }

        .metric-warning .metric-value {
          color: hsl(158 100% 30%);
        }

        @media (prefers-color-scheme: dark) {
          .metric {
            background: hsl(var(--color-slate-900));
            border-color: hsl(var(--color-slate-700));
          }

          .metric-value {
            color: hsl(var(--color-slate-50));
          }
        }
      </style>
      <div class="metric metric-${variant}">
        <div class="metric-header">
          <div class="metric-label">${label}</div>
          ${icon ? `<div class="metric-icon">${icon}</div>` : ''}
        </div>
        <div class="metric-value">
          ${value}
          ${suffix ? `<span class="metric-suffix">${suffix}</span>` : ''}
        </div>
        ${trend ? `
          <div class="metric-trend" style="color: hsl(${trendColor})">
            <span class="metric-trend-icon">${trendIcon}</span>
            <slot></slot>
          </div>
        ` : ''}
      </div>
    `;
  }
}

customElements.define('archon-metric', ArchonMetric);

/* ═══════════════════════════════════════════════════════════════
   <archon-progress> - Progress bar/ring
   ═══════════════════════════════════════════════════════════════

   Usage:
   <archon-progress value="67" max="100" variant="success"></archon-progress>
   <archon-progress value="67" type="ring" size="120"></archon-progress>
   ═══════════════════════════════════════════════════════════════ */

class ArchonProgress extends ArchonComponent {
  static get observedAttributes() {
    return ['value', 'max', 'type', 'variant', 'size', 'label'];
  }

  connectedCallback() {
    this.render();
  }

  attributeChangedCallback() {
    this.render();
  }

  render() {
    const value = parseFloat(this.getAttribute('value')) || 0;
    const max = parseFloat(this.getAttribute('max')) || 100;
    const type = this.getAttribute('type') || 'bar'; // 'bar' | 'ring'
    const variant = this.getAttribute('variant') || 'primary';
    const size = parseInt(this.getAttribute('size')) || 120;
    const label = this.getAttribute('label');

    const percentage = Math.min((value / max) * 100, 100);

    if (type === 'ring') {
      const radius = size / 2 - 8;
      const circumference = 2 * Math.PI * radius;
      const offset = circumference - (percentage / 100) * circumference;

      this.shadowRoot.innerHTML = `
        <style>
          .progress-ring {
            display: inline-block;
            position: relative;
          }

          .progress-ring-circle {
            transition: stroke-dashoffset var(--duration-slow) var(--ease-out);
          }

          .progress-ring-value {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: ${size / 5}px;
            font-weight: var(--font-weight-bold);
            color: hsl(var(--color-slate-900));
          }
        </style>
        <div class="progress-ring">
          <svg width="${size}" height="${size}">
            <circle
              cx="${size / 2}"
              cy="${size / 2}"
              r="${radius}"
              fill="none"
              stroke="hsl(var(--color-slate-200))"
              stroke-width="8"
            />
            <circle
              class="progress-ring-circle"
              cx="${size / 2}"
              cy="${size / 2}"
              r="${radius}"
              fill="none"
              stroke="hsl(var(--color-${variant === 'success' ? 'prr-green' : 'archon-blue'}-500))"
              stroke-width="8"
              stroke-linecap="round"
              stroke-dasharray="${circumference}"
              stroke-dashoffset="${offset}"
              transform="rotate(-90 ${size / 2} ${size / 2})"
            />
          </svg>
          <div class="progress-ring-value">${percentage.toFixed(0)}%</div>
        </div>
      `;
    } else {
      // Bar type
      this.shadowRoot.innerHTML = `
        <style>
          .progress-bar-container {
            width: 100%;
          }

          .progress-bar-label {
            display: flex;
            justify-content: space-between;
            margin-bottom: var(--space-2);
            font-size: var(--font-size-sm);
            font-weight: var(--font-weight-medium);
            color: hsl(var(--color-slate-700));
          }

          .progress-bar-track {
            width: 100%;
            height: 12px;
            background: hsl(var(--color-slate-200));
            border-radius: var(--radius-full);
            overflow: hidden;
          }

          .progress-bar-fill {
            height: 100%;
            background: hsl(var(--color-${variant === 'success' ? 'prr-green' : 'archon-blue'}-500));
            border-radius: var(--radius-full);
            transition: width var(--duration-slow) var(--ease-out);
          }
        </style>
        <div class="progress-bar-container">
          ${label ? `
            <div class="progress-bar-label">
              <span>${label}</span>
              <span>${percentage.toFixed(0)}%</span>
            </div>
          ` : ''}
          <div class="progress-bar-track">
            <div class="progress-bar-fill" style="width: ${percentage}%"></div>
          </div>
        </div>
      `;
    }
  }
}

customElements.define('archon-progress', ArchonProgress);

/* ═══════════════════════════════════════════════════════════════
   EXPORT for module usage
   ═══════════════════════════════════════════════════════════════ */

export {
  ArchonBadge,
  ArchonCard,
  ArchonMetric,
  ArchonProgress
};
