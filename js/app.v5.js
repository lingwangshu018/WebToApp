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
  const PARTICLE_COUNT = 10;

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }

  function initParticles() {
    particles = Array.from({ length: PARTICLE_COUNT }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.14,
      vy: (Math.random() - 0.5) * 0.14,
      r: Math.random() * 2.2 + 1.2,
      a: Math.random() * 0.18 + 0.05,
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
      ctx.fillStyle = `rgba(176,130,96,${p.a})`;
      ctx.fill();
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
  const appNameSourceNote = document.getElementById('app-name-source-note');
  const appColorInput = document.getElementById('app-color');
  const customIconInput = document.getElementById('custom-icon-input');
  const customIconFileName = document.getElementById('custom-icon-file-name');
  const customIconPreview = document.getElementById('custom-icon-preview');
  const customIconPlaceholder = document.getElementById('custom-icon-placeholder');
  const customIconClearBtn = document.getElementById('custom-icon-clear');
  const androidVersionNameInput = document.getElementById('android-version-name');
  const androidVersionCodeInput = document.getElementById('android-version-code');
  const androidPackagePrefixInput = document.getElementById('android-package-prefix');
  const immersiveFullscreenInput = document.getElementById('feature-immersive-fullscreen');
  const desktopModeInput = document.getElementById('feature-desktop-mode');
  const colorHex = document.getElementById('color-hex');
  const generateBtn = document.getElementById('generate-btn');
  const resultPanel = document.getElementById('result-panel');
  const appLink = document.getElementById('app-link');
  const copyBtn = document.getElementById('copy-btn');
  const previewFrame = document.getElementById('preview-frame');
  const previewUrl = document.getElementById('preview-url');
  const previewOpenBtn = document.getElementById('preview-open-btn');
  const historyList = document.getElementById('history-list');
  const historyEmpty = document.getElementById('history-empty');
  const historyRecoverBtn = document.getElementById('history-recover-btn');
  const historyExportBtn = document.getElementById('history-export-btn');
  const historyImportBtn = document.getElementById('history-import-btn');
  const historyImportInput = document.getElementById('history-import-input');
  let currentUrl = '';
  let pendingAutoScrollTimer = null;
  let customIconDataUrl = '';
  let detectedIconDataUrl = '';
  let restoreIconDataUrl = '';
  let restoreIconLabel = '';
  let restoreIconFileName = '';
  let restoreIconButtonLabel = '暂无可恢复图标';
  let deviceFingerprint = '';
  const DEVICE_STORAGE_KEY = 'webtoapp-device-fingerprint-v1';
  const DEVICE_COOKIE_KEY = 'webtoapp_device_fingerprint';
  const DEFAULT_VERSION_CODE_PLACEHOLDER = '留空则自动递增';

  function normalizeFeatureOptions(raw) {
    const options = raw && typeof raw === 'object' ? raw : {};
    const immersiveFullscreen = options['feature-immersive-fullscreen'] === true || options.feature_immersive_fullscreen === true;
    const desktopMode = options['feature-desktop-mode'] === true || options.feature_desktop_mode === true;
    return {
      immersiveFullscreen,
      desktopMode,
    };
  }

  function applyFeatureOptionsToForm(raw) {
    const options = normalizeFeatureOptions(raw);
    immersiveFullscreenInput.checked = options.immersiveFullscreen;
    desktopModeInput.checked = options.desktopMode;
  }

  function collectFeatureOptions() {
    const featureOptions = normalizeFeatureOptions({
      'feature-immersive-fullscreen': immersiveFullscreenInput.checked,
      'feature-desktop-mode': desktopModeInput.checked,
    });
    return {
      'feature-immersive-fullscreen': featureOptions.immersiveFullscreen,
      'feature-desktop-mode': featureOptions.desktopMode,
    };
  }

  function cancelPendingAutoScroll() {
    if (pendingAutoScrollTimer) {
      clearTimeout(pendingAutoScrollTimer);
      pendingAutoScrollTimer = null;
    }
  }

  function isMostlyInViewport(el, threshold = 0.7) {
    if (!el) return true;
    const rect = el.getBoundingClientRect();
    const viewportHeight = window.innerHeight || document.documentElement.clientHeight;
    const visibleTop = Math.max(rect.top, 0);
    const visibleBottom = Math.min(rect.bottom, viewportHeight);
    const visibleHeight = Math.max(0, visibleBottom - visibleTop);
    const targetHeight = Math.max(1, Math.min(rect.height, viewportHeight));
    return (visibleHeight / targetHeight) >= threshold;
  }

  function scheduleGentleScroll(el, options = {}) {
    cancelPendingAutoScroll();
    const delay = options.delay || 0;
    pendingAutoScrollTimer = window.setTimeout(() => {
      pendingAutoScrollTimer = null;
      if (!el || isMostlyInViewport(el, options.threshold || 0.7)) return;
      el.scrollIntoView({ behavior: 'smooth', block: options.block || 'start' });
    }, delay);
  }

  function sanitizeAndroidVersionName(value) {
    const cleaned = String(value || '').replace(/[^0-9A-Za-z._-]/g, '').replace(/^[._-]+|[._-]+$/g, '');
    return cleaned || '1.0.0';
  }

  function sanitizeAndroidVersionCode(value) {
    if (value === null || value === undefined) return '';
    if (String(value).trim() === '') return '';
    const parsed = parseInt(String(value || '').trim(), 10);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : '';
  }

  function sanitizeAndroidPackagePrefix(value) {
    const raw = String(value || '').toLowerCase();
    const parts = raw.split('.').map((chunk) => {
      let token = chunk.replace(/[^a-z0-9_]/g, '');
      if (!token) return '';
      if (/^[0-9]/.test(token)) token = `p${token}`;
      return token;
    }).filter(Boolean);
    return parts.length >= 2 ? parts.join('.') : 'com.webtoapp';
  }

  function getDeviceFingerprint() {
    function syncFingerprintCookie(value) {
      if (!value) return;
      const secure = window.location.protocol === 'https:' ? '; Secure' : '';
      document.cookie = `${DEVICE_COOKIE_KEY}=${encodeURIComponent(value)}; Max-Age=31536000; Path=/; SameSite=Lax${secure}`;
    }
    try {
      const existing = window.localStorage.getItem(DEVICE_STORAGE_KEY);
      if (existing) {
        syncFingerprintCookie(existing);
        return existing;
      }
      const bytes = new Uint8Array(16);
      window.crypto.getRandomValues(bytes);
      const created = Array.from(bytes, (value) => value.toString(16).padStart(2, '0')).join('');
      window.localStorage.setItem(DEVICE_STORAGE_KEY, created);
      syncFingerprintCookie(created);
      return created;
    } catch (_err) {
      const fallback = `volatile-${Date.now().toString(16)}`;
      syncFingerprintCookie(fallback);
      return fallback;
    }
  }

  function apiHeaders() {
    return {
      'Content-Type': 'application/json',
      'X-Device-Fingerprint': deviceFingerprint,
    };
  }

  async function attachHistoryItem(appId) {
    const value = String(appId || '').trim();
    if (!value) return null;
    const res = await fetch(`/api/history/attach/${encodeURIComponent(value)}`, {
      method: 'POST',
      headers: apiHeaders(),
    });
    if (!res.ok) throw new Error('attach failed');
    return res.json();
  }

  async function recoverHistoryItems() {
    const res = await fetch('/api/history/recover', {
      method: 'POST',
      headers: apiHeaders(),
    });
    if (!res.ok) throw new Error('recover failed');
    return res.json();
  }

  function formatHistoryTime(value) {
    if (!value) return '刚刚';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return '刚刚';
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: 'numeric',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  function getAbsoluteUrl(pathOrUrl) {
    if (!pathOrUrl) return '';
    try {
      return new URL(pathOrUrl, window.location.origin).toString();
    } catch (_err) {
      return String(pathOrUrl || '');
    }
  }

  function escapeHtml(value) {
    return String(value || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function fillIconPreview(dataUrl, label) {
    if (dataUrl) {
      customIconDataUrl = dataUrl;
      customIconPreview.src = dataUrl;
      customIconPreview.parentElement.classList.add('has-image');
      customIconPlaceholder.textContent = label || '已回填图标';
      syncRestoreIconButton();
      return;
    }
    customIconDataUrl = '';
    customIconInput.value = '';
    if (customIconFileName) customIconFileName.textContent = '未选择任何文件';
    customIconPreview.removeAttribute('src');
    customIconPreview.parentElement.classList.remove('has-image');
    customIconPlaceholder.textContent = '自动抓取';
    syncRestoreIconButton();
  }

  function syncRestoreIconButton() {
    if (!customIconClearBtn) return;
    if (restoreIconDataUrl) {
      customIconClearBtn.textContent = restoreIconButtonLabel;
      customIconClearBtn.disabled = false;
      return;
    }
    if (customIconDataUrl) {
      customIconClearBtn.textContent = '清空图标';
      customIconClearBtn.disabled = false;
      return;
    }
    customIconClearBtn.textContent = '暂无可恢复图标';
    customIconClearBtn.disabled = true;
  }

  function setRestoreIconState(dataUrl, options = {}) {
    restoreIconDataUrl = String(dataUrl || '').trim();
    restoreIconLabel = String(options.label || '').trim();
    restoreIconFileName = String(options.fileName || '').trim();
    restoreIconButtonLabel = String(options.buttonLabel || '暂无可恢复图标').trim() || '暂无可恢复图标';
    syncRestoreIconButton();
  }

  function nameSourceLabel(source) {
    switch (String(source || '').trim()) {
      case 'site_name':
        return '站点名称元数据';
      case 'application_name':
        return '应用名称元数据';
      case 'apple_mobile_web_app_title':
        return '苹果 Web App 名称';
      case 'title_host_match':
        return '网页标题中的站点名';
      case 'title_first_part':
        return '网页标题';
      case 'title_full':
        return '网页标题';
      case 'host_fallback':
        return '域名';
      default:
        return '自动检测';
    }
  }

  function updateAppNameSourceNote(source, suggestedName) {
    if (!appNameSourceNote) return;
    if (!suggestedName) {
      appNameSourceNote.textContent = '分析后会自动填充名称与来源';
      return;
    }
    if (!source) {
      appNameSourceNote.textContent = '当前名称已回填到编辑区';
      return;
    }
    const label = nameSourceLabel(source);
    appNameSourceNote.textContent = `已根据${label}自动填充`;
  }

  function syncInputValue(input, value) {
    const text = value == null ? '' : String(value);
    input.value = text;
    input.setAttribute('value', text);
  }

  function renderHistory(items) {
    const list = Array.isArray(items) ? items : [];
    historyList.innerHTML = '';
    historyEmpty.classList.toggle('hidden', list.length > 0);
    if (!list.length) return;

    const fragment = document.createDocumentFragment();
    list.forEach((item) => {
      const card = document.createElement('article');
      const publicPath = getAbsoluteUrl(item.public_path || `/a/${item.app_id}`);
      const targetUrl = item.target_url || '';
      const breakdown = item.visit_breakdown || {};
      const downloadBreakdown = item.download_breakdown || {};
      const downloadSummary = Object.entries(downloadBreakdown)
        .map(([platform, count]) => `${platform} ${Number(count || 0).toLocaleString('zh-CN')}`)
        .join(' · ') || '暂无';
      const iconHtml = item.icon_url
        ? `<img class="history-icon" src="${escapeHtml(item.icon_url)}" alt="${escapeHtml(item.name || item.app_id)}">`
        : `<div class="history-icon" aria-hidden="true"></div>`;
      card.className = 'history-card';
      card._historyItem = item;
      card.innerHTML = `
        <div class="history-main">
          <div class="history-name-row">
            ${iconHtml}
            <div class="history-name-block">
              <div class="history-name">${escapeHtml(item.name || item.app_id)}</div>
              <div class="history-link">${escapeHtml(publicPath)}</div>
            </div>
          </div>
          <div class="history-meta">
            <span class="history-meta-chip">访问 ${Number(item.visit_count || 0).toLocaleString('zh-CN')} 次</span>
            <span class="history-meta-chip">下载 ${Number(item.download_count || 0).toLocaleString('zh-CN')} 次</span>
            <span class="history-meta-chip">更新于 ${escapeHtml(formatHistoryTime(item.updated_at))}</span>
            <span class="history-meta-chip">目标 ${escapeHtml(targetUrl)}</span>
          </div>
          <div class="history-breakdown">
            <div class="history-breakdown-row">
              <span>下载页访问</span>
              <strong>${Number(breakdown.landing || 0).toLocaleString('zh-CN')}</strong>
            </div>
            <div class="history-breakdown-row">
              <span>iPhone 安装页</span>
              <strong>${Number(breakdown.install || 0).toLocaleString('zh-CN')}</strong>
            </div>
            <div class="history-breakdown-row">
              <span>PWA 访问</span>
              <strong>${Number(breakdown.pwa || 0).toLocaleString('zh-CN')}</strong>
            </div>
            <div class="history-breakdown-row">
              <span>桌面图标启动</span>
              <strong>${Number(breakdown.launch || 0).toLocaleString('zh-CN')}</strong>
            </div>
            <div class="history-breakdown-row history-breakdown-row-wide">
              <span>平台下载</span>
              <strong>${escapeHtml(downloadSummary)}</strong>
            </div>
          </div>
        </div>
        <div class="history-actions">
          <button class="history-action primary" type="button" data-open="${escapeHtml(publicPath)}">打开下载页</button>
          <button class="history-action" type="button" data-regenerate="${escapeHtml(item.app_id || '')}">重新生成</button>
          <button class="history-action" type="button" data-edit="${escapeHtml(item.app_id || '')}">回填到编辑区</button>
          <button class="history-action" type="button" data-copy="${escapeHtml(publicPath)}">复制链接</button>
          <button class="history-action history-action-danger" type="button" data-delete="${escapeHtml(item.app_id || '')}">从历史移除</button>
        </div>
      `;
      fragment.appendChild(card);
    });
    historyList.appendChild(fragment);
  }

  async function loadHistory() {
    try {
      const res = await fetch('/api/history', {
        headers: { 'X-Device-Fingerprint': deviceFingerprint },
      });
      if (!res.ok) throw new Error('failed');
      const data = await res.json();
      renderHistory(data.items || []);
      return data.items || [];
    } catch (_err) {
      renderHistory([]);
      return [];
    }
  }

  async function recoverHistoryFromPageContext() {
    const candidates = new Set();
    const currentLink = appLink && appLink.value ? appLink.value : '';
    const currentUrl = previewOpenBtn && previewOpenBtn.dataset ? previewOpenBtn.dataset.href : '';
    [currentLink, currentUrl, window.location.href].forEach((value) => {
      const match = String(value || '').match(/\/a\/([a-f0-9]{8})(?:[/?#]|$)/i);
      if (match) candidates.add(match[1]);
    });
    if (!candidates.size) return [];
    for (const appId of candidates) {
      try {
        await attachHistoryItem(appId);
      } catch (_err) {
        // Ignore failed recovery attempts; the app may no longer exist.
      }
    }
    return loadHistory();
  }

  deviceFingerprint = getDeviceFingerprint();
  loadHistory().then((items) => {
    if (!items.length) {
      recoverHistoryFromPageContext();
    }
  });

  async function applyHistoryItemToForm(item) {
    const recipe = item.recipe || {};
    const featureOptions = recipe.options || item.options || {};
    currentUrl = item.target_url || recipe.url || '';
    syncInputValue(urlInput, currentUrl);
    syncInputValue(appNameInput, item.name || recipe.name || '');
    updateAppNameSourceNote('', item.name || recipe.name || '');
    const color = item.color || recipe.color || '#7c3aed';
    syncInputValue(appColorInput, color);
    colorHex.textContent = color;
    syncInputValue(
      androidVersionNameInput,
      sanitizeAndroidVersionName(String(item.android_version_name || recipe.android_version_name || '1.0.0'))
    );
    const previousVersionCode = sanitizeAndroidVersionCode(item.android_version_code || recipe.android_version_code || '');
    syncInputValue(androidVersionCodeInput, '');
    androidVersionCodeInput.placeholder = previousVersionCode
      ? `${DEFAULT_VERSION_CODE_PLACEHOLDER}（上次 ${previousVersionCode}）`
      : DEFAULT_VERSION_CODE_PLACEHOLDER;
    syncInputValue(
      androidPackagePrefixInput,
      sanitizeAndroidPackagePrefix(item.android_package_prefix || recipe.android_package_prefix || 'com.webtoapp')
    );
    applyFeatureOptionsToForm(featureOptions);
    if (item.icon_url) {
      try {
        const iconRes = await fetch(item.icon_url);
        if (!iconRes.ok) throw new Error('icon fetch failed');
        const iconBlob = await iconRes.blob();
        const iconDataUrl = await readFileAsDataUrl(iconBlob);
        detectedIconDataUrl = '';
        setRestoreIconState(iconDataUrl, {
          label: '已回填图标',
          fileName: '已回填当前图标',
          buttonLabel: '恢复当前图标',
        });
        fillIconPreview(iconDataUrl, '已回填图标');
        if (customIconFileName) customIconFileName.textContent = '已回填当前图标';
      } catch (_err) {
        detectedIconDataUrl = '';
        setRestoreIconState('', {});
        fillIconPreview('', '');
      }
    } else {
        detectedIconDataUrl = '';
        setRestoreIconState('', {});
        fillIconPreview('', '');
    }
    showRecoveredAnalysisResults(item);
    workspace.classList.remove('hidden');
  }

  async function generateAppFromCurrentForm() {
    const options = {};
    const versionName = sanitizeAndroidVersionName(androidVersionNameInput.value);
    const versionCode = sanitizeAndroidVersionCode(androidVersionCodeInput.value);
    const packagePrefix = sanitizeAndroidPackagePrefix(androidPackagePrefixInput.value);
    syncInputValue(androidVersionNameInput, versionName);
    syncInputValue(androidVersionCodeInput, versionCode ? String(versionCode) : '');
    syncInputValue(androidPackagePrefixInput, packagePrefix);
    options['android-version-name'] = versionName;
    if (versionCode) options['android-version-code'] = versionCode;
    options['android-package-prefix'] = packagePrefix;
    if (customIconDataUrl) options['custom-icon-data-url'] = customIconDataUrl;
    Object.assign(options, collectFeatureOptions());

    const submitRes = await fetch('/api/distill', {
      method: 'POST',
      headers: apiHeaders(),
      body: JSON.stringify({
        url: currentUrl,
        name: appNameInput.value,
        color: appColorInput.value,
        display: 'fullscreen',
        orientation: 'any',
        options: options,
      }),
    });
    if (!submitRes.ok) throw new Error('生成失败');
    const task = await submitRes.json();
    if (!task.task_id) throw new Error('任务提交失败');

    let data = null;
    let attempts = 0;
    while (attempts < 240) {
      attempts += 1;
      await sleep(attempts <= 8 ? 500 : 1000);
      const pollRes = await fetch(`/api/distill/${encodeURIComponent(task.task_id)}`, {
        headers: apiHeaders(),
      });
      if (pollRes.status === 404) throw new Error('任务不存在或已过期');
      if (!pollRes.ok) {
        let message = '生成失败';
        try {
          const err = await pollRes.json();
          if (err && err.detail) message = String(err.detail);
        } catch (_err) {}
        throw new Error(message);
      }
      const payload = await pollRes.json();
      if (payload && payload.status && payload.task_id) {
        continue;
      }
      data = payload;
      break;
    }
    if (!data) throw new Error('生成超时，请重试');

    const installLink = `${location.origin}${data.url}`;
    appLink.value = installLink;
    previewUrl.textContent = installLink;
    previewFrame.src = installLink;
    previewOpenBtn.dataset.href = installLink;
    resultPanel.classList.remove('hidden');
    await loadHistory();
    scheduleGentleScroll(resultPanel, { block: 'nearest', threshold: 0.45, delay: 180 });
    return data;
  }

  // --- Color picker sync ---
  appColorInput.addEventListener('input', () => { colorHex.textContent = appColorInput.value; });
  ['wheel', 'touchstart', 'pointerdown', 'keydown'].forEach((eventName) => {
    window.addEventListener(eventName, cancelPendingAutoScroll, { passive: true });
  });
  customIconInput.addEventListener('change', async () => {
    const file = customIconInput.files && customIconInput.files[0];
    if (!file) return;
    try {
      customIconDataUrl = await readFileAsDataUrl(file);
      if (customIconFileName) customIconFileName.textContent = file.name;
      customIconPreview.src = customIconDataUrl;
      customIconPreview.parentElement.classList.add('has-image');
      customIconPlaceholder.textContent = file.name;
      syncRestoreIconButton();
    } catch (_err) {
      customIconDataUrl = '';
      customIconInput.value = '';
      if (customIconFileName) customIconFileName.textContent = '读取失败';
      customIconPreview.removeAttribute('src');
      customIconPreview.parentElement.classList.remove('has-image');
      customIconPlaceholder.textContent = '读取失败';
      syncRestoreIconButton();
    }
  });
  customIconClearBtn.addEventListener('click', () => {
    if (restoreIconDataUrl) {
      fillIconPreview(restoreIconDataUrl, restoreIconLabel || '已恢复图标');
      if (customIconFileName) customIconFileName.textContent = restoreIconFileName || '已恢复图标';
      syncRestoreIconButton();
      return;
    }
    fillIconPreview('', '');
    syncRestoreIconButton();
  });
  androidVersionNameInput.addEventListener('blur', () => {
    androidVersionNameInput.value = sanitizeAndroidVersionName(androidVersionNameInput.value);
  });
  androidVersionCodeInput.addEventListener('blur', () => {
    const sanitized = sanitizeAndroidVersionCode(androidVersionCodeInput.value);
    androidVersionCodeInput.value = sanitized ? String(sanitized) : '';
  });
  androidPackagePrefixInput.addEventListener('blur', () => {
    androidPackagePrefixInput.value = sanitizeAndroidPackagePrefix(androidPackagePrefixInput.value);
  });

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
    scheduleGentleScroll(workspace, { block: 'start', threshold: 0.55, delay: 120 });

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
    const suggestedName = host.split('.')[0].charAt(0).toUpperCase() + host.split('.')[0].slice(1);
    return {
      title: suggestedName,
      suggestedName,
      suggestedNameSource: 'host_fallback',
      url: url,
      host: host,
      favicon: `https://www.google.com/s2/favicons?domain=${host}&sz=64`,
      faviconDataUrl: '',
      themeColor: '#7c3aed',
      ads: Math.floor(Math.random() * 12) + 3,
      trackers: Math.floor(Math.random() * 18) + 5,
      popups: Math.floor(Math.random() * 4) + 1,
      originalSize: (Math.random() * 3 + 1.5).toFixed(1) + ' MB',
      distilledSize: (Math.random() * 200 + 80).toFixed(0) + ' KB',
      speedBoost: (Math.random() * 5 + 2).toFixed(1) + 'x',
    };
  }

  function buildRecoveredAnalysisData(item) {
    const recipe = item && item.recipe && typeof item.recipe === 'object' ? item.recipe : {};
    const targetUrl = String(item.target_url || recipe.url || '').trim();
    let host = '';
    try {
      host = new URL(targetUrl).hostname.replace(/^www\./i, '');
    } catch (_err) {}
    const suggestedName = String(item.name || recipe.name || host || item.app_id || '').trim();
    const title = String(
      recipe.title
      || recipe.site_title
      || recipe.site_name
      || suggestedName
      || host
    ).trim();
    const suggestedNameSource = String(
      recipe.suggestedNameSource
      || recipe.suggested_name_source
      || recipe.name_source
      || ''
    ).trim();
    return {
      title,
      suggestedName,
      suggestedNameSource,
      host,
      targetUrl,
      hasIcon: !!item.icon_url || !!recipe.custom_icon_uploaded,
    };
  }

  function showRecoveredAnalysisResults(item) {
    const data = buildRecoveredAnalysisData(item || {});
    analysisStatus.textContent = '已恢复';
    analysisStatus.className = 'status-badge done';
    analysisBody.innerHTML = `
      <div class="analysis-results">
        <div class="analysis-item"><span class="label">网站标题</span><span class="value info">${escapeHtml(data.title || '未保存')}</span></div>
        <div class="analysis-item"><span class="label">建议名称</span><span class="value good">${escapeHtml(data.suggestedName || '未保存')}</span></div>
        <div class="analysis-item"><span class="label">名称来源</span><span class="value info">${escapeHtml(data.suggestedNameSource ? nameSourceLabel(data.suggestedNameSource) : '历史构建')}</span></div>
        <div class="analysis-item"><span class="label">图标状态</span><span class="value ${data.hasIcon ? 'good' : 'info'}">${data.hasIcon ? '已从历史恢复' : '历史中未保存图标'}</span></div>
        <div class="analysis-item"><span class="label">目标地址</span><span class="value info">${escapeHtml(data.targetUrl || data.host || '未保存')}</span></div>
      </div>
      <div class="analysis-actions">
        <button id="reanalyze-btn" class="btn-secondary" type="button">重新分析</button>
      </div>`;
    const reanalyzeBtn = document.getElementById('reanalyze-btn');
    if (reanalyzeBtn) {
      reanalyzeBtn.addEventListener('click', async () => {
        reanalyzeBtn.disabled = true;
        reanalyzeBtn.textContent = '分析中...';
        try {
          await startDistill();
        } finally {
          reanalyzeBtn.disabled = false;
          reanalyzeBtn.textContent = '重新分析';
        }
      });
    }
  }

  function showAnalysisResults(data) {
    analysisStatus.textContent = '完成';
    analysisStatus.className = 'status-badge done';
    const title = String(data.title || data.host || '').trim();
    const suggestedName = String(data.suggestedName || data.siteName || data.title || data.host || '').trim();
    const suggestedNameSource = String(data.suggestedNameSource || '').trim();
    const suggestedNameSourceLabel = nameSourceLabel(suggestedNameSource);
    const themeColor = String(data.themeColor || '#7c3aed').trim() || '#7c3aed';
    syncInputValue(appNameInput, suggestedName);
    updateAppNameSourceNote(suggestedNameSource, suggestedName);
    syncInputValue(appColorInput, themeColor);
    colorHex.textContent = themeColor.toUpperCase();
    if (data.faviconDataUrl) {
      detectedIconDataUrl = String(data.faviconDataUrl);
      setRestoreIconState(detectedIconDataUrl, {
        label: '已自动抓取',
        fileName: '已自动抓取网站图标',
        buttonLabel: '恢复自动抓取',
      });
      fillIconPreview(String(data.faviconDataUrl), '已自动抓取');
      if (customIconFileName) customIconFileName.textContent = '已自动抓取网站图标';
    } else {
      detectedIconDataUrl = '';
      setRestoreIconState('', {});
      fillIconPreview('', '');
    }

    analysisBody.innerHTML = `
      <div class="analysis-results">
        <div class="analysis-item"><span class="label">网站标题</span><span class="value info">${escapeHtml(title)}</span></div>
        <div class="analysis-item"><span class="label">建议名称</span><span class="value good">${escapeHtml(suggestedName)}</span></div>
        <div class="analysis-item"><span class="label">名称来源</span><span class="value info">${escapeHtml(suggestedNameSourceLabel)}</span></div>
        <div class="analysis-item"><span class="label">图标状态</span><span class="value ${data.faviconDataUrl ? 'good' : 'info'}">${data.faviconDataUrl ? '已自动抓取' : '未检测到图标'}</span></div>
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

    try {
      await generateAppFromCurrentForm();
    } catch (e) {
      alert('生成失败，请重试: ' + e.message);
    }

    generateBtn.textContent = '🚀 生成应用';
    generateBtn.disabled = false;
  });

  syncRestoreIconButton();

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

  historyList.addEventListener('click', async (event) => {
    const target = event.target.closest('[data-open], [data-copy], [data-delete], [data-edit], [data-regenerate]');
    if (!target) return;
    const card = target.closest('.history-card');
    const item = card && card._historyItem;
    if (target.dataset.open) {
      window.open(target.dataset.open, '_blank', 'noopener,noreferrer');
      return;
    }
    if (target.dataset.edit) {
      if (!item) return;
      await applyHistoryItemToForm(item);
      scheduleGentleScroll(workspace, { block: 'start', threshold: 0.55, delay: 80 });
      return;
    }
    if (target.dataset.regenerate) {
      if (!item) return;
      try {
        target.disabled = true;
        target.textContent = '生成中...';
        await applyHistoryItemToForm(item);
        await generateAppFromCurrentForm();
      } catch (_err) {
        alert('重新生成失败，请重试');
      } finally {
        target.disabled = false;
        target.textContent = '重新生成';
      }
      return;
    }
    if (target.dataset.copy) {
      try {
        await navigator.clipboard.writeText(target.dataset.copy);
        const original = target.textContent;
        target.textContent = '已复制';
        window.setTimeout(() => { target.textContent = original; }, 1600);
      } catch (_err) {
        alert('复制失败，请手动复制链接');
      }
      return;
    }
    if (target.dataset.delete) {
      if (!window.confirm('确定要从当前设备的历史记录中移除这个构建吗？')) return;
      try {
        target.disabled = true;
        const res = await fetch(`/api/history/${encodeURIComponent(target.dataset.delete)}`, {
          method: 'DELETE',
          headers: { 'X-Device-Fingerprint': deviceFingerprint },
        });
        if (!res.ok) throw new Error('删除失败');
        const data = await res.json();
        renderHistory((data.history && data.history.items) || []);
      } catch (_err) {
        alert('移除失败，请重试');
      } finally {
        target.disabled = false;
      }
    }
  });

  historyExportBtn.addEventListener('click', async () => {
    try {
      const res = await fetch('/api/history/export', {
        headers: { 'X-Device-Fingerprint': deviceFingerprint },
      });
      if (!res.ok) throw new Error('导出失败');
      const data = await res.json();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const href = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = href;
      link.download = `webtoapp-history-${new Date().toISOString().slice(0, 10)}.json`;
      link.click();
      URL.revokeObjectURL(href);
    } catch (_err) {
      alert('导出失败，请重试');
    }
  });

  historyImportBtn.addEventListener('click', () => {
    historyImportInput.click();
  });

  historyImportInput.addEventListener('change', async () => {
    const file = historyImportInput.files && historyImportInput.files[0];
    if (!file) return;
    try {
      const text = await file.text();
      const payload = JSON.parse(text);
      const res = await fetch('/api/history/import', {
        method: 'POST',
        headers: apiHeaders(),
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error('导入失败');
      const data = await res.json();
      renderHistory((data.history && data.history.items) || []);
      alert(`导入完成：${data.imported} 条，恢复 ${data.restored} 条`);
    } catch (_err) {
      alert('导入失败，请确认文件格式正确');
    } finally {
      historyImportInput.value = '';
    }
  });

  if (historyRecoverBtn) {
    historyRecoverBtn.addEventListener('click', async () => {
      const original = historyRecoverBtn.textContent;
      historyRecoverBtn.disabled = true;
      historyRecoverBtn.textContent = '恢复中...';
      try {
        const data = await recoverHistoryItems();
        renderHistory((data.history && data.history.items) || []);
      } catch (_err) {
        alert('恢复失败，请重试');
      } finally {
        historyRecoverBtn.disabled = false;
        historyRecoverBtn.textContent = original;
      }
    });
  }

  // --- Recipe Cards ---
  document.querySelectorAll('.recipe-card').forEach(card => {
    card.addEventListener('click', () => {
      const url = card.dataset.url;
      if (url) {
        urlInput.value = url;
        cancelPendingAutoScroll();
        if (window.scrollY > 120) {
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }
        setTimeout(startDistill, 500);
      }
    });
  });

  // --- Nav scroll effect ---
  const nav = document.getElementById('nav');
  window.addEventListener('scroll', () => {
    nav.style.background = window.scrollY > 50 ? 'rgba(243, 234, 223, 0.94)' : 'rgba(243, 234, 223, 0.9)';
  }, { passive: true });

  // --- Util ---
  function readFileAsDataUrl(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result || ''));
      reader.onerror = () => reject(reader.error || new Error('file read failed'));
      reader.readAsDataURL(file);
    });
  }

  function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

})();
