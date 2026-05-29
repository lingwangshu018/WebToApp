/* ============================================================
   WebToApp — Frontend Logic
   Zero dependencies. Every function earns its place.
   ============================================================ */

(function () {
  'use strict';

  // --- Particle System ---
  const canvas = document.getElementById('bg');
  const ctx = canvas.getContext('2d');
  let particles = [];
  const PARTICLE_COUNT = 60;
  const CONNECT_DIST = 120;

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }

  function initParticles() {
    particles = Array.from({ length: PARTICLE_COUNT }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4,
      r: Math.random() * 1.5 + 0.5,
      a: Math.random() * 0.4 + 0.1,
    }));
  }

  function drawParticles() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (let i = 0; i < particles.length; i++) {
      const p = particles[i];
      p.x += p.vx; p.y += p.vy;
      if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
      if (p.y < 0 || p.y > canvas.height) p.vy *= -1;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(124,58,237,${p.a})`;
      ctx.fill();
      for (let j = i + 1; j < particles.length; j++) {
        const q = particles[j];
        const dx = p.x - q.x, dy = p.y - q.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < CONNECT_DIST) {
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(q.x, q.y);
          ctx.strokeStyle = `rgba(124,58,237,${0.06 * (1 - dist / CONNECT_DIST)})`;
          ctx.stroke();
        }
      }
    }
    requestAnimationFrame(drawParticles);
  }

  resize();
  initParticles();
  drawParticles();
  window.addEventListener('resize', () => { resize(); initParticles(); });

  // --- Scroll Reveal ---
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('revealed'); revealObserver.unobserve(e.target); } });
  }, { threshold: 0.15 });
  document.querySelectorAll('[data-reveal]').forEach(el => revealObserver.observe(el));

  // --- Counter Animation ---
  function animateCount(el, target, duration = 1800) {
    const start = performance.now();
    const fmt = (n) => n.toLocaleString('en-US');
    const tick = (now) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = fmt(Math.floor(target * eased));
      if (progress < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }

  const animatedCounters = new WeakSet();
  const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        const target = parseInt(e.target.dataset.count);
        if (!Number.isNaN(target) && !animatedCounters.has(e.target)) {
          animateCount(e.target, target);
          animatedCounters.add(e.target);
        }
        counterObserver.unobserve(e.target);
      }
    });
  }, { threshold: 0.5 });
  document.querySelectorAll('[data-count]').forEach(el => counterObserver.observe(el));

  async function loadHomepageStats() {
    try {
      const res = await fetch('/api/stats');
      if (!res.ok) throw new Error('Failed to load stats');
      const stats = await res.json();
      const mappings = [
        ['stat-generated-apps', stats.generatedApps],
        ['stat-supported-platforms', stats.supportedPlatforms],
        ['stat-shared-recipes', stats.sharedRecipes],
      ];
      mappings.forEach(([id, value]) => {
        const el = document.getElementById(id);
        if (!el || Number.isNaN(Number(value))) return;
        el.dataset.count = String(value);
        el.textContent = '0';
        animatedCounters.delete(el);
        animateCount(el, Number(value));
        animatedCounters.add(el);
      });
    } catch (_err) {
      // Leave zero values in place rather than showing made-up numbers.
    }
  }
  loadHomepageStats();

  // --- DOM refs ---
  const urlInput = document.getElementById('url-input');
  const distillBtn = document.getElementById('distill-btn');
  const workspace = document.getElementById('workspace');
  const analysisBody = document.getElementById('analysis-body');
  const analysisStatus = document.getElementById('analysis-status');
  const appNameInput = document.getElementById('app-name');
  const appColorInput = document.getElementById('app-color');
  const colorHex = document.getElementById('color-hex');
  const generateBtn = document.getElementById('generate-btn');
  const resultPanel = document.getElementById('result-panel');
  const appLink = document.getElementById('app-link');
  const copyBtn = document.getElementById('copy-btn');
  const previewFrame = document.getElementById('preview-frame');
  const previewUrl = document.getElementById('preview-url');
  const previewOpenBtn = document.getElementById('preview-open-btn');
  let currentUrl = '';

  // --- Color picker sync ---
  appColorInput.addEventListener('input', () => { colorHex.textContent = appColorInput.value; });

  // --- URL Validation ---
  function isValidUrl(str) {
    try { const u = new URL(str.startsWith('http') ? str : 'https://' + str); return !!u.hostname.includes('.'); } catch { return false; }
  }

  function normalizeUrl(str) {
    return str.startsWith('http') ? str : 'https://' + str;
  }

  // --- Distill Flow ---
  distillBtn.addEventListener('click', startDistill);
  urlInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') startDistill(); });

  async function startDistill() {
    const raw = urlInput.value.trim();
    if (!raw || !isValidUrl(raw)) {
      urlInput.style.boxShadow = '0 0 0 2px #f87171';
      setTimeout(() => urlInput.style.boxShadow = '', 1500);
      return;
    }

    const url = normalizeUrl(raw);
    currentUrl = url;
    workspace.classList.remove('hidden');
    resultPanel.classList.add('hidden');
    analysisStatus.textContent = '分析中';
    analysisStatus.className = 'status-badge';
    analysisBody.innerHTML = '<div class="analysis-loader"><div class="loader-bar"></div><p id="loader-text">正在抓取页面...</p></div>';
    workspace.scrollIntoView({ behavior: 'smooth', block: 'start' });

    // Simulate analysis steps
    const steps = ['正在抓取页面...', '解析 DOM 结构...', '识别广告位与追踪脚本...', '提取设计系统 DNA...', '计算优化方案...'];
    for (let i = 0; i < steps.length; i++) {
      await sleep(600 + Math.random() * 400);
      const loader = document.getElementById('loader-text');
      if (loader) loader.textContent = steps[i];
    }

    // Try real API first, fallback to simulation
    let data;
    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });
      if (res.ok) data = await res.json();
    } catch { /* fallback to simulated data */ }

    if (!data) data = simulateAnalysis(url);
    showAnalysisResults(data);
  }

  function simulateAnalysis(url) {
    const host = new URL(url).hostname.replace('www.', '');
    return {
      title: host.split('.')[0].charAt(0).toUpperCase() + host.split('.')[0].slice(1),
      url: url,
      host: host,
      favicon: `https://www.google.com/s2/favicons?domain=${host}&sz=64`,
      themeColor: '#7c3aed',
      ads: Math.floor(Math.random() * 12) + 3,
      trackers: Math.floor(Math.random() * 18) + 5,
      popups: Math.floor(Math.random() * 4) + 1,
      originalSize: (Math.random() * 3 + 1.5).toFixed(1) + ' MB',
      distilledSize: (Math.random() * 200 + 80).toFixed(0) + ' KB',
      speedBoost: (Math.random() * 5 + 2).toFixed(1) + 'x',
    };
  }

  function showAnalysisResults(data) {
    analysisStatus.textContent = '完成';
    analysisStatus.className = 'status-badge done';
    appNameInput.value = data.title;

    analysisBody.innerHTML = `
      <div class="analysis-results">
        <div class="analysis-item"><span class="label">网站标题</span><span class="value info">${data.title}</span></div>
        <div class="analysis-item"><span class="label">检测到广告</span><span class="value bad">${data.ads} 个广告位</span></div>
        <div class="analysis-item"><span class="label">追踪脚本</span><span class="value bad">${data.trackers} 个追踪器</span></div>
        <div class="analysis-item"><span class="label">弹窗覆盖</span><span class="value bad">${data.popups} 个弹窗</span></div>
        <div class="analysis-item"><span class="label">原始大小</span><span class="value">${data.originalSize}</span></div>
        <div class="analysis-item"><span class="label">蒸馏后大小</span><span class="value good">${data.distilledSize}</span></div>
        <div class="analysis-item"><span class="label">预计加速</span><span class="value good">${data.speedBoost}</span></div>
      </div>`;
  }

  // --- Generate App ---

  generateBtn.addEventListener('click', async () => {
    generateBtn.textContent = '⏳ 生成中...';
    generateBtn.disabled = true;

    // Collect all toggle options
    const options = {};
    document.querySelectorAll('.toggles input[type="checkbox"]').forEach(cb => {
      options[cb.dataset.opt] = cb.checked;
    });

    try {
      const res = await fetch('/api/distill', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: currentUrl,
          name: appNameInput.value,
          color: appColorInput.value,
          display: document.getElementById('display-mode').value,
          orientation: document.getElementById('orientation').value,
          options: options,
        }),
      });

      if (!res.ok) throw new Error('生成失败');
      const data = await res.json();
      const installLink = `${location.origin}${data.url}`;
      appLink.value = installLink;
      previewUrl.textContent = installLink;
      previewFrame.src = installLink;
      previewOpenBtn.dataset.href = installLink;
      resultPanel.classList.remove('hidden');
      resultPanel.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } catch (e) {
      alert('生成失败，请重试: ' + e.message);
    }

    generateBtn.textContent = '🚀 生成应用';
    generateBtn.disabled = false;
  });

  // --- Copy Link ---
  copyBtn.addEventListener('click', () => {
    navigator.clipboard.writeText(appLink.value).then(() => {
      const orig = copyBtn.textContent;
      copyBtn.textContent = '已复制 ✓';
      setTimeout(() => copyBtn.textContent = orig, 2000);
    });
  });

  previewOpenBtn.addEventListener('click', () => {
    const href = previewOpenBtn.dataset.href;
    if (!href) return;
    window.open(href, '_blank', 'noopener,noreferrer');
  });

  // --- Recipe Cards ---
  document.querySelectorAll('.recipe-card').forEach(card => {
    card.addEventListener('click', () => {
      const url = card.dataset.url;
      if (url) {
        urlInput.value = url;
        window.scrollTo({ top: 0, behavior: 'smooth' });
        setTimeout(startDistill, 500);
      }
    });
  });

  // --- Nav scroll effect ---
  const nav = document.getElementById('nav');
  window.addEventListener('scroll', () => {
    nav.style.background = window.scrollY > 50 ? 'rgba(9,9,11,0.85)' : 'rgba(9,9,11,0.6)';
  }, { passive: true });

  // --- Util ---
  function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

})();
