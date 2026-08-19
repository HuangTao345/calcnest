/* CalcNest — lightweight privacy-friendly analytics (V1.4)
   Design:
   - No cookies, no third-party scripts. Privacy Policy promise intact.
   - Collects ≥5 core events per page.
   - Queue in sessionStorage, flush via sendBeacon to a configurable endpoint.
   - Falls back to console.debug when endpoint not configured (local dev).
   To activate: set window.CALCNEST_ANALYTICS_ENDPOINT = "https://your-site/analytics"
   (e.g. Cloudflare Pages Function, Plausible, or GoatCounter-compatible beacon). */
(function () {
  'use strict';

  // 延迟读取端点：允许在页面任何位置（包括脚本后）设置 CALCNEST_ANALYTICS_ENDPOINT
  function getEndpoint() {
    return (typeof window.CALCNEST_ANALYTICS_ENDPOINT !== 'undefined')
      ? window.CALCNEST_ANALYTICS_ENDPOINT : '';
  }

  function nowISO() {
    try { return new Date().toISOString(); } catch (e) { return ''; }
  }

  function pageName() {
    var p = window.location.pathname || '/';
    // strip trailing slash
    if (p.length > 1 && p.slice(-1) === '/') p = p.slice(0, -1);
    return p || '/';
  }

  function queue() {
    try {
      var q = sessionStorage.getItem('cn_ev');
      return q ? JSON.parse(q) : [];
    } catch (e) { return []; }
  }

  function save(q) {
    try { sessionStorage.setItem('cn_ev', JSON.stringify(q.slice(-50))); } catch (e) {}
  }

  function push(event, payload) {
    var q = queue();
    var item = {
      ev: event,
      page: pageName(),
      t: nowISO(),
      ref: document.referrer ? document.referrer.slice(0, 200) : '',
      v: '1.4'
    };
    if (payload) { for (var k in payload) { if (Object.prototype.hasOwnProperty.call(payload, k)) item[k] = payload[k]; } }
    q.push(item);
    save(q);
    flush();
  }

  function flush() {
    var q = queue();
    if (!q.length) return;
    var ENDPOINT = getEndpoint();
    if (!ENDPOINT) {
      // 开发/本地：不静默丢数据，控制台可见
      if (window.console && console.debug) console.debug('[CalcNest analytics]', q.slice(-5));
      save([]); // 本地已"消费"
      return;
    }
    var batch = q.slice(0, 10);
    var body = JSON.stringify(batch);
    var ok = false;
    try {
      if (navigator.sendBeacon) {
        ok = navigator.sendBeacon(ENDPOINT, new Blob([body], { type: 'application/json' }));
      }
    } catch (e) { ok = false; }
    if (ok) {
      var rest = q.slice(batch.length);
      save(rest);
    }
  }

  // ---------- 核心事件（≥5） ----------
  window.CalcNestAnalytics = {
    track: push,
    pageview: function () { push('pageview'); },
    toolView: function (toolId) { push('tool_view', { tool: toolId }); },
    calcSubmit: function (toolId) { push('calc_submit', { tool: toolId }); },
    resultShown: function (toolId) { push('result_shown', { tool: toolId }); },
    navClick: function (target) { push('nav_click', { target: target }); },
    faqOpen: function (topic) { push('faq_open', { topic: topic }); },
    flushNow: flush
  };

  // 页面级自动事件：pageview + tool_view
  document.addEventListener('DOMContentLoaded', function () {
    push('pageview');
    var m = window.location.pathname.match(/tools\/([a-z0-9-]+)\.html/i);
    if (m) push('tool_view', { tool: m[1] });
  });
})();
