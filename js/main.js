/* CalcNest — shared site JS (V1.4)
   Handles: mobile nav, cookie banner (GDPR), FAQ accordions,
   chart canvas HiDPI scaling, current-year in footer.
   No external dependencies. */
(function () {
  'use strict';

  /* ---- Mobile nav toggle ---- */
  function initNav() {
    var toggle = document.getElementById('nav-toggle');
    var nav = document.getElementById('site-nav');
    if (!toggle || !nav) return;
    toggle.addEventListener('click', function () {
      nav.classList.toggle('open');
    });
    // Close nav after clicking a link (mobile)
    nav.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () { nav.classList.remove('open'); });
    });
  }

  /* ---- Cookie banner (GDPR) ---- */
  function initCookieBanner() {
    var banner = document.getElementById('cookie-banner');
    var acceptBtn = document.getElementById('cookie-accept');
    if (!banner || !acceptBtn) return;
    try {
      if (localStorage.getItem('calcnest_cookie_ok')) return;
    } catch (e) { return; }
    banner.classList.add('show');
    acceptBtn.addEventListener('click', function () {
      try { localStorage.setItem('calcnest_cookie_ok', '1'); } catch (e) {}
      banner.classList.remove('show');
    });
  }

  /* ---- FAQ accordions ---- */
  function initFaq() {
    var items = document.querySelectorAll('.faq-item');
    items.forEach(function (item) {
      var q = item.querySelector('.faq-q');
      if (!q) return;
      q.addEventListener('click', function () {
        item.classList.toggle('open');
      });
    });
  }

  /* ---- Money formatter ---- */
  function fmtMoney(v, currency) {
    var sym = currency || '$';
    var abs = Math.abs(v);
    var s;
    if (abs >= 1e6) s = (v / 1e6).toFixed(2) + 'M';
    else if (abs >= 1e4) s = (v / 1e3).toFixed(1) + 'K';
    else s = v.toFixed(2);
    return sym + s;
  }

  /* ---- HiDPI chart scaling ---- */
  function setupCanvas(canvas, cssW) {
    var dpr = window.devicePixelRatio || 1;
    var w = cssW || canvas.clientWidth || 300;
    var h = Math.round(w * 0.55); // fixed aspect
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    canvas.style.width = w + 'px';
    canvas.style.height = h + 'px';
    var ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);
    return { ctx: ctx, w: w, h: h };
  }

  window.CalcNest = {
    fmtMoney: fmtMoney,
    setupCanvas: setupCanvas
  };

  document.addEventListener('DOMContentLoaded', function () {
    initNav();
    initCookieBanner();
    initFaq();

    // Footer year
    var yearEl = document.getElementById('year');
    if (yearEl) yearEl.textContent = String(new Date().getFullYear());
  });
})();
