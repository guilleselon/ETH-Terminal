"""Full CSS for the app."""

CSS = """
* { box-sizing: border-box; }
body { margin:0; background:#0b0f17; color:#e5e7eb; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif; font-size:14px; }
.app { min-height:100vh; }
.topbar { display:flex; align-items:center; justify-content:space-between; padding:14px 24px; border-bottom:1px solid #1f2937; background:#0b0f17; position:sticky; top:0; z-index:10; }
.brand { font-weight:700; font-size:16px; letter-spacing:-0.02em; }
.brand span { color:#627eea; }
.tag { font-size:11px; color:#6b7280; margin-left:12px; }
main { padding:24px; max-width:1400px; margin:0 auto; }
h2 { font-size:20px; margin:0 0 4px; letter-spacing:-0.02em; }
.sub { color:#6b7280; font-size:13px; margin:0 0 20px; }
.grid { display:grid; gap:16px; }
.kpis { grid-template-columns:repeat(2, 1fr); margin-bottom:20px; }
.card { background:#111827; border:1px solid #1f2937; border-radius:12px; padding:16px; }
.card-title { font-size:13px; font-weight:600; color:#9ca3af; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:12px; }
.kpi-label { color:#6b7280; font-size:12px; text-transform:uppercase; letter-spacing:0.05em; }
.kpi-value { font-size:22px; font-weight:700; margin-top:6px; letter-spacing:-0.02em; }
.kpi-delta { font-size:12px; margin-top:4px; }
.pos { color:#22c55e; } .neg { color:#ef4444; } .neu { color:#9ca3af; }
table { width:100%; border-collapse:collapse; }
th { text-align:left; padding:10px 12px; color:#6b7280; font-weight:500; font-size:11px; text-transform:uppercase; letter-spacing:0.05em; border-bottom:1px solid #1f2937; }
td { padding:12px; border-bottom:1px solid #0f172a; font-size:13px; vertical-align:middle; }
tr:hover td { background:#0f172a; }
.error-banner { background:#450a0a; border:1px solid #ef4444; color:#fca5a5; padding:10px 14px; border-radius:8px; margin-bottom:16px; font-size:13px; }
.info-banner { background:#1e3a8a; border:1px solid #627eea; color:#bfdbfe; padding:10px 14px; border-radius:8px; margin-bottom:16px; font-size:13px; }
.warn-banner { background:#422006; border:1px solid #eab308; color:#fde68a; padding:10px 14px; border-radius:8px; margin-bottom:16px; font-size:13px; }
.chart-title-row { display:flex; align-items:center; justify-content:space-between; margin-bottom:12px; flex-wrap: wrap; gap: 8px; }
.chart-hint { font-size:11px; color:#4b5563; }

/* ════════════════════════════════════════════════════════════
   LOADING
   ════════════════════════════════════════════════════════════ */
.loading-banner {
    display: flex; align-items: center; gap: 12px;
    padding: 12px 16px; margin-bottom: 20px;
    background: linear-gradient(90deg, #1e3a8a 0%, #1e40af 100%);
    border: 1px solid #627eea; border-radius: 10px;
    color: #bfdbfe; font-size: 13px; font-weight: 500;
}
.loading-spinner {
    width: 18px; height: 18px;
    border: 2px solid #627eea;
    border-top-color: #bfdbfe;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    flex-shrink: 0;
}
@keyframes spin { to { transform: rotate(360deg); } }
.skeleton-card {
    background: #111827; border: 1px solid #1f2937;
    border-radius: 12px; padding: 16px; margin-bottom: 20px;
}
.skeleton-line {
    height: 14px; background: linear-gradient(90deg, #1f2937 0%, #374151 50%, #1f2937 100%);
    border-radius: 6px; margin-bottom: 10px;
    animation: shimmer 1.5s infinite;
}
.skeleton-line.w30 { width: 30%; }
.skeleton-line.w50 { width: 50%; }
.skeleton-line.w70 { width: 70%; }
.skeleton-line.h60 { height: 60px; }
.skeleton-line.h120 { height: 120px; }
@keyframes shimmer {
    0% { background-position: -200px 0; }
    100% { background-position: calc(200px + 100%) 0; }
}

/* ════════════════════════════════════════════════════════════
   LANDING
   ════════════════════════════════════════════════════════════ */
.landing {
    position: fixed;
    inset: 0;
    background: #0b0f17;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    animation: landing-fade-in 0.3s ease-out;
}
@keyframes landing-fade-in {
    from { opacity: 0; }
    to   { opacity: 1; }
}
.landing-inner {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 48px;
    padding: 40px;
    max-width: 500px;
    width: 100%;
}
.landing-header { text-align: center; }
.landing-logo {
    font-size: 48px;
    font-weight: 800;
    letter-spacing: -0.04em;
    line-height: 1;
    color: #e5e7eb;
}
.landing-logo span { color: #627eea; }
.landing-subtitle {
    margin-top: 12px;
    font-size: 14px;
    color: #6b7280;
    letter-spacing: 0.02em;
}
.landing-status {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 16px;
}
.landing-spinner {
    width: 48px;
    height: 48px;
    border: 3px solid #1f2937;
    border-top-color: #627eea;
    border-radius: 50%;
    animation: spin 0.9s linear infinite;
}
.landing-text {
    font-size: 14px;
    color: #9ca3af;
    font-weight: 500;
    letter-spacing: 0.02em;
}
.landing-hint {
    font-size: 11px;
    color: #4b5563;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-family: monospace;
}

/* ════════════════════════════════════════════════════════════
   MOMENTUM
   ════════════════════════════════════════════════════════════ */
.mom-grid { display:grid; grid-template-columns:repeat(6, 1fr); gap:8px; }
.mom-item { text-align:center; padding:12px 8px; background:#0b0f17; border-radius:8px; border:1px solid #1f2937; }
.mom-period { font-size:11px; color:#6b7280; text-transform:uppercase; letter-spacing:0.08em; font-weight:700; }
.mom-val { font-size:16px; font-weight:700; margin-top:6px; font-family:monospace; }
.mom-verdict { font-size:18px; font-weight:700; margin-bottom:6px; letter-spacing:-0.01em; }
.mom-buy-strong { color:#4ade80; }
.mom-buy-caution { color:#a3e635; }
.mom-wait { color:#facc15; }
.mom-sell { color:#f87171; }
.mom-advice { font-size:13px; color:#9ca3af; line-height:1.55; }
.mom-horizons { font-size:11px; color:#6b7280; margin-top:10px; font-family:monospace; }

/* ════════════════════════════════════════════════════════════
   VOLUME
   ════════════════════════════════════════════════════════════ */
.vol-grid { display:grid; grid-template-columns:repeat(4, 1fr); gap:12px; }
.vol-item { padding:14px; background:#0b0f17; border-radius:10px; border:1px solid #1f2937; }
.vol-item-lbl { font-size:11px; color:#6b7280; text-transform:uppercase; letter-spacing:0.05em; font-weight:600; }
.vol-item-val { font-size:20px; font-weight:700; margin-top:6px; font-family:monospace; }
.vol-item-sub { font-size:11px; color:#6b7280; margin-top:4px; }
.vol-high { color:#4ade80; }
.vol-normal { color:#9ca3af; }
.vol-low { color:#facc15; }
.vol-advice { font-size:13px; color:#9ca3af; line-height:1.55; }
.vol-contradiction {
    margin-top: 12px; padding: 10px 14px;
    background: rgba(30, 58, 138, 0.35);
    border-left: 3px solid #627eea;
    border-radius: 6px;
    font-size: 12px; color: #bfdbfe; line-height: 1.5;
}
.vol-signals { display:grid; grid-template-columns:repeat(4, 1fr); gap:12px; margin-top:16px; padding-top:16px; border-top:1px solid #1f2937; }
.vol-signal-lbl { font-size:11px; color:#6b7280; text-transform:uppercase; letter-spacing:0.05em; font-weight:600; }
.vol-signal-val { font-size:15px; font-weight:700; margin-top:4px; }
.vol-signal-note { font-size:11px; color:#6b7280; margin-top:2px; }

/* ════════════════════════════════════════════════════════════
   ZONES
   ════════════════════════════════════════════════════════════ */
.zone-card { border-radius:16px; padding:28px; margin-bottom:20px; border:2px solid #22c55e; background:linear-gradient(135deg, #052e16 0%, #064e3b 100%); }
.zone-card.tactical {
    border-color: #3b82f6;
    background: linear-gradient(135deg, #0c1e3a 0%, #122a52 100%);
    margin-bottom: 16px;
}
.zone-card.tactical .zone-label { color: #93c5fd; }
.zone-card.tactical .zone-prices { color: #cbd5e1; font-size: 32px; }
.zone-card.tactical .zone-members-lbl { color: #93c5fd; }
.zone-card.tactical .zone-member-badge {
    background: rgba(59, 130, 246, 0.15);
    border-color: #3b82f6;
    color: #93c5fd;
}
.zone-card.tactical .zone-meta-lbl { color: #93c5fd; }
.zone-card.tactical .zone-meta { border-top-color: #1e40af; }
.zone-card.tactical .zone-distance.neg { color: #93c5fd; }
.zone-card.accumulation { border-color:#22c55e; background:linear-gradient(135deg, #052e16 0%, #064e3b 100%); }
.zone-card.accumulation.distant { border-color: #16a34a; opacity: 0.9; }
.zone-card.no-zone { border-color:#eab308; background:linear-gradient(135deg, #1c1917 0%, #292524 100%); }
.zone-label { font-size:13px; color:#86efac; text-transform:uppercase; letter-spacing:0.1em; font-weight:700; margin-bottom:8px; }
.zone-card.no-zone .zone-label { color:#facc15; }
.zone-prices { font-size:38px; font-weight:800; letter-spacing:-0.03em; line-height:1.1; color:#e5e7eb; }
.zone-distance { font-size:16px; font-weight:700; margin-top:8px; }
.zone-distance.neg { color:#4ade80; }
.zone-distance.pos { color:#f87171; }
.zone-adj-note { font-size:12px; color:#86efac; margin-top:6px; font-style:italic; }
.zone-card.no-zone .zone-adj-note { color:#facc15; }
.zone-members { margin-top: 16px; display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.zone-members-lbl { font-size: 11px; color: #86efac; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; margin-right: 4px; }
.zone-member-badge {
    display: inline-block; padding: 4px 10px;
    background: rgba(34, 197, 94, 0.15);
    border: 1px solid #22c55e;
    border-radius: 999px;
    color: #86efac; font-size: 11px; font-weight: 600;
}
.zone-meta { display:grid; grid-template-columns:repeat(3, 1fr); gap:12px; border-top:1px solid #166534; padding-top:16px; margin-top:20px; }
.zone-meta-item { text-align:center; }
.zone-meta-lbl { font-size:11px; color:#86efac; text-transform:uppercase; letter-spacing:0.05em; }
.zone-card.no-zone .zone-meta-lbl { color:#facc15; }
.zone-meta-val { font-size:18px; font-weight:700; margin-top:4px; font-family:monospace; }
.zone-meta-val.sl { color:#f87171; }
.zone-meta-val.tp { color:#93b4ff; }
.zone-meta-val.rr { color:#facc15; }
.rr-tag {
    display: inline-block; margin-top: 6px; padding: 2px 8px;
    background: rgba(120, 113, 108, 0.15); border: 1px solid #78716c;
    border-radius: 999px; font-size: 10px; color: #a8a29e;
    text-transform: uppercase; letter-spacing: 0.05em; font-weight: 700;
}
.rr-context-note {
    margin-top: 16px; padding: 10px 14px;
    background: rgba(120, 113, 108, 0.15);
    border-left: 3px solid #a8a29e;
    border-radius: 6px;
    font-size: 12px; color: #cbd5e1; line-height: 1.5;
}
.zone-card.tactical .rr-context-note {
    background: rgba(59, 130, 246, 0.15);
    border-left-color: #3b82f6;
    color: #bfdbfe;
}
.distance-hint {
    margin-top: 12px; padding: 8px 12px;
    background: rgba(59, 130, 246, 0.15);
    border-radius: 6px;
    font-size: 12px; color: #93c5fd;
    text-align: center;
}
.zone-card.accumulation .distance-hint {
    background: rgba(34, 197, 94, 0.15);
    color: #86efac;
}
.zones-explainer {
    padding: 12px 16px; margin-bottom: 16px;
    background: rgba(30, 58, 138, 0.25);
    border-left: 3px solid #3b82f6;
    border-radius: 6px;
    font-size: 12px; color: #bfdbfe; line-height: 1.6;
}
.zones-explainer strong { color: #e5e7eb; }

/* ════════════════════════════════════════════════════════════
   GLOBAL MARKET CONTEXT
   ════════════════════════════════════════════════════════════ */
.global-context {
    background: linear-gradient(135deg, #0a0e1a 0%, #101828 100%);
    border: 1px solid #1f2937;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 20px;
}
.global-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 14px;
    padding-bottom: 12px;
    border-bottom: 1px solid #1f2937;
}
.global-icon { font-size: 16px; line-height: 1; }
.global-title {
    font-size: 13px; font-weight: 700; color: #9ca3af;
    text-transform: uppercase; letter-spacing: 0.08em;
}
.global-source {
    font-size: 11px; color: #4b5563; margin-left: auto;
    font-family: monospace;
}
.global-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.global-item { text-align: left; }
.global-item-lbl {
    font-size: 11px; color: #6b7280; text-transform: uppercase;
    letter-spacing: 0.05em; font-weight: 600; margin-bottom: 6px;
}
.global-item-val {
    font-size: 18px; font-weight: 700; font-family: monospace;
    color: #e5e7eb; letter-spacing: -0.02em;
}
.global-item-sub { font-size: 11px; color: #6b7280; margin-top: 4px; }

/* Fear & Greed — color based on value */
.fg-value {
    font-size: 22px; font-weight: 800; font-family: monospace;
    letter-spacing: -0.03em;
}
.fg-max { font-size: 12px; color: #4b5563; margin-left: 2px; }
.fg-extreme-fear  { color: #dc2626; }
.fg-fear          { color: #f87171; }
.fg-neutral       { color: #facc15; }
.fg-greed         { color: #a3e635; }
.fg-extreme-greed { color: #22c55e; }

/* ════════════════════════════════════════════════════════════
   CHANGES BANNER
   ════════════════════════════════════════════════════════════ */
.changes-banner {
    padding: 14px 18px; margin-bottom: 20px;
    background: linear-gradient(135deg, rgba(120, 53, 15, 0.35) 0%, rgba(154, 52, 18, 0.35) 100%);
    border: 1px solid #ea580c;
    border-radius: 10px;
}
.changes-banner-title {
    font-size: 13px; color: #fed7aa; text-transform: uppercase;
    letter-spacing: 0.08em; font-weight: 700; margin-bottom: 8px;
}
.changes-list { list-style: none; padding: 0; margin: 0; }
.changes-list li {
    padding: 6px 0; font-size: 13px; color: #fed7aa;
    border-bottom: 1px solid rgba(234, 88, 12, 0.2);
}
.changes-list li:last-child { border-bottom: none; }
.changes-list li::before {
    content: "▸ "; color: #fb923c; font-weight: 700; margin-right: 4px;
}

/* ════════════════════════════════════════════════════════════
   DECISIONS
   ════════════════════════════════════════════════════════════ */
.decision-card {
    background: linear-gradient(135deg, rgba(88, 28, 135, 0.25) 0%, rgba(107, 33, 168, 0.25) 100%);
    border: 1px solid #a855f7;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
}
.decision-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 12px;
    flex-wrap: wrap;
}
.decision-title { font-weight: 700; font-size: 14px; color: #d8b4fe; white-space: nowrap; }
.decision-header-right {
    display: flex; align-items: center; gap: 8px; flex-shrink: 0;
}
.decision-status {
    display: inline-block; padding: 3px 10px; border-radius: 999px;
    font-size: 11px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.05em; white-space: nowrap;
}
.decision-status.waiting { background: rgba(234, 179, 8, 0.2); color: #facc15; }
.decision-status.in_zone { background: rgba(34, 197, 94, 0.25); color: #4ade80; }
.decision-status.tp_hit { background: rgba(34, 197, 94, 0.4); color: #86efac; }
.decision-status.sl_hit { background: rgba(239, 68, 68, 0.3); color: #f87171; }
.decision-status.expired { background: rgba(120, 113, 108, 0.3); color: #a8a29e; }
.decision-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin-top: 10px;
}
.decision-item-lbl { font-size: 10px; color: #c084fc; text-transform: uppercase; letter-spacing: 0.05em; }
.decision-item-val { font-size: 14px; font-weight: 700; font-family: monospace; margin-top: 2px; }
.decision-pin-info {
    font-size: 11px; color: #a78bfa; margin-top: 10px;
    padding-top: 10px; border-top: 1px solid rgba(168, 85, 247, 0.25);
}
.unpin-btn {
    background: transparent; border: 1px solid #a855f7; color: #d8b4fe;
    padding: 4px 10px; border-radius: 6px; font-size: 11px;
    cursor: pointer; font-weight: 600; text-decoration: none;
    white-space: nowrap;
}
.unpin-btn:hover { background: rgba(168, 85, 247, 0.15); }
.pin-btn {
    display: inline-block; margin-top: 20px;
    background: rgba(168, 85, 247, 0.15);
    border: 1px solid #a855f7;
    color: #d8b4fe;
    padding: 8px 16px; border-radius: 8px;
    font-size: 12px; font-weight: 700;
    cursor: pointer; text-decoration: none;
    text-transform: uppercase; letter-spacing: 0.05em;
}
.pin-btn:hover { background: rgba(168, 85, 247, 0.3); }
.pinned-note {
    display: inline-block; margin-top: 20px;
    font-size: 11px; color: #a78bfa;
    font-style: italic;
}

/* ════════════════════════════════════════════════════════════
   CHANGE HISTORY
   ════════════════════════════════════════════════════════════ */
.history-row {
    display: grid; grid-template-columns: 90px 1fr;
    gap: 12px; padding: 10px 0;
    border-bottom: 1px solid #0f172a;
    font-size: 12px;
}
.history-row:last-child { border-bottom: none; }
.history-time { color: #6b7280; font-family: monospace; }
.history-changes { color: #cbd5e1; }
.history-changes .change-item { padding: 2px 0; }
.history-changes .change-item::before {
    content: "▸ "; color: #627eea; font-weight: 700;
}

/* ════════════════════════════════════════════════════════════
   CHART LEGEND
   ════════════════════════════════════════════════════════════ */
.chart-legend {
    display: flex; flex-wrap: wrap; gap: 12px;
    margin-top: 10px; padding: 8px 12px;
    background: rgba(15, 23, 42, 0.6);
    border-radius: 6px;
    font-size: 11px; color: #9ca3af;
}
.chart-legend-item { display: flex; align-items: center; gap: 6px; }
.chart-legend-swatch { width: 18px; height: 3px; border-radius: 2px; }

/* ════════════════════════════════════════════════════════════
   TOPBAR ACTIONS
   ════════════════════════════════════════════════════════════ */
.topbar-actions {
    display: flex;
    align-items: center;
    gap: 12px;
}

/* ════════════════════════════════════════════════════════════
   CMC CREDITS COUNTER
   ════════════════════════════════════════════════════════════ */
.credits-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 8px;
    font-size: 12px;
    font-family: monospace;
    cursor: help;
    transition: border-color 0.15s;
}
.credits-badge:hover { border-color: #374151; }
.credits-icon { font-size: 13px; line-height: 1; }
.credits-label {
    color: #9ca3af;
    font-weight: 600;
    font-size: 11px;
    letter-spacing: 0.03em;
}
.credits-count { font-weight: 700; }
.credits-count.credits-ok      { color: #4ade80; }
.credits-count.credits-warn    { color: #facc15; }
.credits-count.credits-danger  { color: #f87171; }
.credits-today { color: #6b7280; }

/* ════════════════════════════════════════════════════════════
   REFRESH BUTTON
   ════════════════════════════════════════════════════════════ */
.refresh-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 8px;
    color: #9ca3af;
    font-size: 12px;
    font-weight: 600;
    font-family: inherit;
    cursor: pointer;
    transition: all 0.15s;
    height: 32px;
}
.refresh-btn:hover {
    background: #1f2937;
    color: #e5e7eb;
    border-color: #374151;
}
.refresh-btn.htmx-request {
    pointer-events: none;
    opacity: 0.7;
}
.refresh-spinner {
    display: none;
    width: 12px;
    height: 12px;
    border: 2px solid #627eea;
    border-top-color: transparent;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
}
.refresh-btn.htmx-request .refresh-spinner { display: inline-block; }
.refresh-btn.htmx-request .refresh-icon { display: none; }
.refresh-text { font-size: 12px; }

/* ════════════════════════════════════════════════════════════
   RESPONSIVE
   ════════════════════════════════════════════════════════════ */
@media (max-width:900px) {
    .kpis { grid-template-columns: 1fr; }
    .zone-prices { font-size:28px; }
    .zone-card.tactical .zone-prices { font-size: 24px; }
    .zone-meta { grid-template-columns:1fr; }
    .mom-grid { grid-template-columns:repeat(3, 1fr); }
    .vol-grid { grid-template-columns:repeat(2, 1fr); }
    .vol-signals { grid-template-columns:1fr 1fr; }
    .decision-grid { grid-template-columns: repeat(2, 1fr); }
    .history-row { grid-template-columns: 1fr; }
    .global-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 600px) {
    .refresh-text { display: none; }
    .refresh-btn  { padding: 6px 10px; }
    .landing-logo { font-size: 36px; }
}
"""
