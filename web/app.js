const state = {
  rootPath: "",
  files: [],
  filteredFiles: [],
  selected: new Set(),
  audit: null,
  treemapFolder: "",
  reviewBatches: [],
  duplicateGroups: [],
  perceptualGroups: [],
  license: null,
  capabilities: {},
  lastScanJobId: "",
  lastHistoryId: null,
  scanCancelling: false,
  fileTablePage: 0,
  fileTablePageSize: 50,
};

const elements = {
  form: document.querySelector("#scan-form"),
  pathInput: document.querySelector("#path-input"),
  locationOptions: document.querySelector("#location-options"),
  quickLocations: document.querySelector("#quick-locations"),
  sidebarRecentScans: document.querySelector("#sidebar-recent-scans"),
  teamSection: document.querySelector("#team-section"),
  teamName: document.querySelector("#team-name"),
  teamMemberCount: document.querySelector("#team-member-count"),
  teamShareButton: document.querySelector("#team-share-btn"),
  teamMembersList: document.querySelector("#team-members-list"),
  teamAuditsList: document.querySelector("#team-audits-list"),
  teamSchedulesList: document.querySelector("#team-schedules-list"),
  teamCreateForm: document.querySelector("#team-create-form"),
  teamNameInput: document.querySelector("#team-name-input"),
  qualityInput: document.querySelector("#quality-input"),
  qualityOutput: document.querySelector("#quality-output"),
  resolutionInput: document.querySelector("#resolution-input"),
  status: document.querySelector("#scan-status"),
  scanStateLabel: document.querySelector("#scan-state-label"),
  scanStateTitle: document.querySelector("#scan-state-title"),
  scanStateCard: document.querySelector(".scan-state-card"),
  scanStage: document.querySelector("#scan-stage"),
  metricTotal: document.querySelector("#metric-total"),
  metricTotalDetail: document.querySelector("#metric-total-detail"),
  metricFiles: document.querySelector("#metric-files"),
  metricFilesDetail: document.querySelector("#metric-files-detail"),
  metricReducible: document.querySelector("#metric-reducible"),
  metricDuplicates: document.querySelector("#metric-duplicates"),
  metricCost: document.querySelector("#metric-cost"),
  currentRoot: document.querySelector("#current-root"),
  overviewEmpty: document.querySelector("#overview-empty"),
  scanMeta: document.querySelector("#scan-meta"),
  selectionSummary: document.querySelector("#selection-summary"),
  filterInput: document.querySelector("#filter-input"),
  categoryFilter: document.querySelector("#category-filter"),
  reduceButton: document.querySelector("#reduce-button"),
  quarantineButton: document.querySelector("#quarantine-button"),
  exportJsonButton: document.querySelector("#export-json-button"),
  exportCsvButton: document.querySelector("#export-csv-button"),
  safeNextSteps: document.querySelector("#safe-next-steps"),
  planConfidence: document.querySelector("#plan-confidence"),
  planDuplicates: document.querySelector("#plan-duplicates"),
  planDuplicatesDetail: document.querySelector("#plan-duplicates-detail"),
  planImages: document.querySelector("#plan-images"),
  planImagesDetail: document.querySelector("#plan-images-detail"),
  planLargeFiles: document.querySelector("#plan-large-files"),
  planLargeFilesDetail: document.querySelector("#plan-large-files-detail"),
  planVideo: document.querySelector("#plan-video"),
  planVideoDetail: document.querySelector("#plan-video-detail"),
  planAudio: document.querySelector("#plan-audio"),
  planAudioDetail: document.querySelector("#plan-audio-detail"),
  recommendedPlan: document.querySelector("#recommended-plan"),
  advisorPanel: document.querySelector("#advisor-panel"),
  advisorStatusText: document.querySelector("#advisor-status-text"),
  advisorRefresh: document.querySelector("#advisor-refresh"),
  advisorContent: document.querySelector("#advisor-content"),
  categoryCount: document.querySelector("#category-count"),
  categoryBars: document.querySelector("#category-bars"),
  folderList: document.querySelector("#folder-list"),
  treemapBreadcrumbs: document.querySelector("#treemap-breadcrumbs"),
  treemap: document.querySelector("#treemap"),
  mapDetail: document.querySelector("#map-detail"),
  historyList: document.querySelector("#history-list"),
  duplicateCount: document.querySelector("#duplicate-count"),
  duplicateList: document.querySelector("#duplicate-list"),
  perceptualCount: document.querySelector("#perceptual-count"),
  perceptualList: document.querySelector("#perceptual-list"),
  perceptualScanButton: document.querySelector("#perceptual-scan-button"),
  restoreManifestInput: document.querySelector("#restore-manifest-input"),
  restoreButton: document.querySelector("#restore-button"),
  reviewQueue: document.querySelector("#review-queue"),
  reviewBatches: document.querySelector("#review-batches"),
  restoreTestPrompt: document.querySelector("#restore-test-prompt"),
  fileCount: document.querySelector("#file-count"),
  fileTableBody: document.querySelector("#file-table-body"),
  selectAll: document.querySelector("#select-all"),
  workspaceTabs: document.querySelector(".workspace-tabs"),
  workspaceViews: document.querySelectorAll(".workspace-view"),
  sidebar: document.querySelector("#sidebar"),
  sidebarToggle: document.querySelector("#sidebar-toggle"),
  sidebarBackdrop: document.querySelector("#sidebar-backdrop"),
  modalTriggers: document.querySelectorAll("[data-modal-target]"),
  themeButtons: document.querySelectorAll("[data-theme-option]"),
  toastRegion: document.querySelector("#toast-region"),
  workspaceSubtitle: document.querySelector("#workspace-subtitle"),
  reviewQueueBadge: document.querySelector("#review-queue-badge"),
  licenseBadge: document.querySelector("#license-badge"),
  licenseForm: document.querySelector("#license-form"),
  licenseKeyInput: document.querySelector("#license-key-input"),
  licenseEmailInput: document.querySelector("#license-email-input"),
  licenseActivationStatus: document.querySelector("#license-activation-status"),
  paymentOptions: document.querySelector(".payment-options"),
  updateNotice: document.querySelector("#update-notice"),
  updateLink: document.querySelector("#update-link"),
  upgradeNudge: document.querySelector("#upgrade-nudge"),
  upgradeNudgeMessage: document.querySelector("#upgrade-nudge-message"),
  upgradeNudgeDismiss: document.querySelector(".upgrade-nudge-dismiss"),
  onboardingModal: document.querySelector("#onboarding-modal"),
  stopScanBtn: document.querySelector("#stop-scan-btn"),
};

const THEME_STORAGE_KEY = "cloudsaver-theme";
const UPGRADE_COOLDOWN_MS = 7 * 24 * 60 * 60 * 1000;
const systemThemeQuery = window.matchMedia("(prefers-color-scheme: dark)");
let fileTableObserver = null;

const UPGRADE_TRIGGERS = {
  large_scan_opportunity: {
    condition: (audit) => audit.opportunities.estimated_recoverable_bytes > 5 * 1024 ** 3,
    message: (audit) => `CloudSaver found ${audit.opportunities.estimated_recoverable_human} of review opportunity. Pro preview adds advanced cleanup analysis and professional reports.`,
    shown: false,
  },
  cloud_mount_detected: {
    condition: () => state.cloudMountsDetected?.length > 0,
    message: () => "CloudSaver detected cloud-synced folders. Use the local report to review storage before upgrading a cloud plan.",
    shown: false,
  },
  duplicate_high_count: {
    condition: (audit) => audit.opportunities.duplicate_count > 50,
    message: (audit) => `${audit.opportunities.duplicate_count} duplicate groups found. Pro preview adds perceptual matching for visually similar images.`,
    shown: false,
  },
  video_detected: {
    condition: (audit) => (audit.by_category.video?.bytes || 0) > 2 * 1024 ** 3,
    message: (audit) => `${formatBytes(audit.by_category.video.bytes)} of video files detected. Pro can re-encode to H.265 - typically 45% smaller.`,
    shown: false,
  },
};

function formatBytes(bytes) {
  const units = ["B", "KB", "MB", "GB", "TB"];
  let value = Number(bytes || 0);
  let index = 0;
  while (value >= 1024 && index < units.length - 1) {
    value /= 1024;
    index += 1;
  }
  return `${value.toFixed(2)} ${units[index]}`;
}

function resolution() {
  const [maxWidth, maxHeight] = elements.resolutionInput.value.split("x").map(Number);
  return { max_width: maxWidth, max_height: maxHeight };
}

function scanStateForTone(tone) {
  const states = {
    neutral: ["Idle", "No scan yet"],
    ready: ["Ready", "Ready to scan"],
    scanning: ["Scanning", "Scan in progress"],
    complete: ["Complete", "Scan complete"],
    error: ["Needs attention", "Check scan input"],
  };
  return states[tone] || states.neutral;
}

function effectiveTheme(preference) {
  if (preference === "light" || preference === "dark") {
    return preference;
  }
  return systemThemeQuery.matches ? "dark" : "light";
}

function storedThemePreference() {
  const stored = localStorage.getItem(THEME_STORAGE_KEY);
  return ["system", "light", "dark"].includes(stored) ? stored : "system";
}

function applyTheme(preference = storedThemePreference()) {
  const theme = effectiveTheme(preference);
  document.documentElement.dataset.theme = theme;
  document.documentElement.dataset.themePreference = preference;
  elements.themeButtons.forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.themeOption === preference));
  });
}

function setThemePreference(preference) {
  localStorage.setItem(THEME_STORAGE_KEY, preference);
  applyTheme(preference);
}

function completeOnboarding() {
  localStorage.setItem("cs-onboarded", "true");
  elements.onboardingModal?.close();
}

function showOnboardingIfNeeded() {
  if (!localStorage.getItem("cs-onboarded")) {
    elements.onboardingModal?.showModal();
  }
}

function setStatus(message, tone = "neutral", stage = "") {
  elements.status.textContent = message;
  elements.status.dataset.tone = tone;
  elements.scanStateCard.dataset.tone = tone;
  const [label, title] = scanStateForTone(tone);
  elements.scanStateLabel.textContent = label;
  elements.scanStateTitle.textContent = title;
  elements.scanStage.textContent = stage || {
    neutral: "Choose a folder",
    ready: "Ready",
    scanning: "Working",
    complete: "Complete",
    error: "Needs attention",
  }[tone] || "Ready";
}

function setMetricText(element, nextText) {
  if (!element) {
    return;
  }
  const value = String(nextText ?? "-");
  const previous = element.dataset.metricValue || element.textContent || "";
  element.dataset.metricValue = value;

  const reducedMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;
  let from = parseAnimatedMetric(previous);
  const to = parseAnimatedMetric(value);
  if (!from && to) {
    from = { ...to, number: 0 };
  }
  if (reducedMotion || !from || !to || from.suffix !== to.suffix || from.prefix !== to.prefix) {
    element.textContent = value;
    return;
  }

  const start = performance.now();
  const duration = 600;
  const ease = (t) => 1 - Math.pow(1 - t, 3);

  function frame(now) {
    const progress = Math.min(1, (now - start) / duration);
    const current = from.number + (to.number - from.number) * ease(progress);
    element.textContent = formatAnimatedMetric(current, to);
    if (progress < 1 && element.dataset.metricValue === value) {
      requestAnimationFrame(frame);
    } else {
      element.textContent = value;
    }
  }

  requestAnimationFrame(frame);
}

function parseAnimatedMetric(text) {
  const match = String(text).trim().match(/^([^0-9-]*)(-?\d+(?:\.\d+)?)(.*)$/);
  if (!match) {
    return null;
  }
  return {
    prefix: match[1],
    number: Number(match[2]),
    suffix: match[3],
    decimals: match[2].includes(".") ? match[2].split(".")[1].length : 0,
  };
}

function formatAnimatedMetric(number, template) {
  const formatted = template.decimals > 0 ? number.toFixed(template.decimals) : String(Math.round(number));
  return `${template.prefix}${formatted}${template.suffix}`;
}

function showToast(message, tone = "success") {
  const toast = document.createElement("div");
  toast.className = `toast ${tone}`;
  toast.setAttribute("role", tone === "error" ? "alert" : "status");
  toast.textContent = `${tone === "error" ? "Error" : "Done"}: ${message}`;
  elements.toastRegion.append(toast);
  window.setTimeout(() => {
    toast.classList.add("leaving");
    window.setTimeout(() => toast.remove(), 240);
  }, 4000);
}

function showUpgradeToast(message) {
  const toast = document.createElement("button");
  toast.type = "button";
  toast.className = "toast upgrade";
  toast.setAttribute("role", "status");
  toast.textContent = `${message} Learn more`;
  toast.addEventListener("click", () => document.querySelector("#upgrade-modal")?.showModal());
  elements.toastRegion.append(toast);
  window.setTimeout(() => {
    toast.classList.add("leaving");
    window.setTimeout(() => toast.remove(), 240);
  }, 5000);
}

function upgradeDismissedRecently(key) {
  const dismissedAt = Number(localStorage.getItem(`cloudsaver-upgrade-dismissed-${key}`) || 0);
  return dismissedAt && Date.now() - dismissedAt < UPGRADE_COOLDOWN_MS;
}

function showUpgradeNudge(message, key) {
  if (upgradeDismissedRecently(key)) {
    return;
  }
  elements.upgradeNudge.dataset.triggerKey = key;
  elements.upgradeNudgeMessage.textContent = message;
  elements.upgradeNudge.hidden = false;
}

function checkUpgradeTriggers(audit) {
  if (state.license?.is_pro) {
    return;
  }
  for (const [key, trigger] of Object.entries(UPGRADE_TRIGGERS)) {
    if (!trigger.shown && trigger.condition(audit) && !upgradeDismissedRecently(key)) {
      trigger.shown = true;
      showUpgradeNudge(trigger.message(audit), key);
      break;
    }
  }
}

function updateReviewQueueBadge() {
  if (!elements.reviewQueueBadge) {
    return;
  }
  const count = state.reviewBatches.length;
  elements.reviewQueueBadge.hidden = count === 0;
  elements.reviewQueueBadge.textContent = count > 9 ? "9+" : String(count);
}

function setWorkspaceView(view) {
  elements.workspaceViews.forEach((section) => {
    section.classList.toggle("active", section.dataset.view === view);
  });
  elements.workspaceTabs.querySelectorAll("[data-view-target]").forEach((button) => {
    button.classList.toggle("active", button.dataset.viewTarget === view);
  });
}

function setSidebarOpen(open) {
  elements.sidebar.classList.toggle("open", open);
  elements.sidebarBackdrop.hidden = false;
  elements.sidebarBackdrop.classList.toggle("open", open);
  if (!open) {
    window.setTimeout(() => {
      if (!elements.sidebarBackdrop.classList.contains("open")) {
        elements.sidebarBackdrop.hidden = true;
      }
    }, 300);
  }
  elements.sidebarToggle.setAttribute("aria-expanded", String(open));
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function emptyState(kind, title, detail = "") {
  const detailMarkup = detail ? `<p>${escapeHtml(detail)}</p>` : "";
  const icons = {
    overview: '<svg class="empty-icon" viewBox="0 0 64 64" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M8 26 C8 22 11 20 14 20 L26 20 L30 24 L50 24 C53 24 56 27 56 30 L56 48 C56 51 53 54 50 54 L14 54 C11 54 8 51 8 48 Z"/><line x1="8" y1="32" x2="56" y2="32"/></svg>',
    map: '<svg class="empty-icon" viewBox="0 0 64 64" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="6" width="22" height="22" rx="3"/><rect x="32" y="6" width="26" height="10" rx="3"/><rect x="32" y="20" width="26" height="22" rx="3"/><rect x="6" y="32" width="22" height="26" rx="3"/><rect x="32" y="46" width="26" height="12" rx="3"/></svg>',
    duplicate: '<svg class="empty-icon" viewBox="0 0 64 64" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="18" y="8" width="30" height="36" rx="4"/><rect x="10" y="18" width="30" height="36" rx="4"/><line x1="16" y1="30" x2="34" y2="30"/><line x1="16" y1="37" x2="28" y2="37"/></svg>',
    table: '<svg class="empty-icon" viewBox="0 0 64 64" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="10" width="52" height="44" rx="4"/><line x1="6" y1="22" x2="58" y2="22"/><line x1="24" y1="22" x2="24" y2="54"/><line x1="6" y1="34" x2="58" y2="34"/><line x1="6" y1="44" x2="58" y2="44"/></svg>',
  };
  return `<div class="empty-state ${kind}-empty">${icons[kind] || ""}<strong>${escapeHtml(title)}</strong>${detailMarkup}</div>`;
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    if (response.status === 402 && data.error === "pro_required") {
      handleProGate(data.message || "This feature");
    }
    throw new Error(data.error || "Request failed.");
  }
  return data;
}

async function loadLicense() {
  const response = await fetch("/api/license");
  const data = await response.json();
  state.license = data;
  renderLicenseBadge(data);
  loadTeamStatus().catch(() => {});
  return data;
}

async function loadCapabilities() {
  const response = await fetch("/api/capabilities");
  const data = await response.json();
  state.capabilities = data;
  elements.paymentOptions.hidden = !data.payments_configured;
  return data;
}

async function loadUpdateStatus() {
  const response = await fetch("/api/update/status");
  const data = await response.json();
  if (data.update_available && data.release_url) {
    elements.updateNotice.hidden = false;
    elements.updateLink.href = data.release_url;
  } else {
    elements.updateNotice.hidden = true;
  }
}

function renderLicenseBadge(license) {
  const badge = elements.licenseBadge;
  if (license.is_pro) {
    badge.classList.add("license-badge--pro");
    badge.innerHTML = `<span>CloudSaver ${escapeHtml(license.tier)}</span><small>Active until ${escapeHtml(license.expires_at)}</small>`;
  } else {
    badge.classList.remove("license-badge--pro");
    badge.innerHTML = '<span>Free</span><button type="button" id="upgrade-button" data-modal-target="upgrade-modal">Pro preview</button>';
  }
}

function handleProGate(featureName) {
  showToast(`${featureName} requires CloudSaver Pro`, "error");
  document.querySelector("#upgrade-modal")?.showModal();
}

async function loadTeamStatus() {
  if (!state.license?.is_biz) {
    elements.teamSection.hidden = true;
    return null;
  }
  const response = await fetch("/api/team/status");
  const data = await response.json();
  if (!response.ok) {
    elements.teamSection.hidden = true;
    return null;
  }
  state.teamStatus = data;
  renderTeamStatus(data);
  return data;
}

function renderTeamStatus(data) {
  if (!state.license?.is_biz) {
    elements.teamSection.hidden = true;
    return;
  }
  elements.teamSection.hidden = false;
  const workspace = data?.workspace;
  const members = data?.members || [];
  elements.teamName.textContent = workspace ? workspace.name : "No workspace";
  elements.teamMemberCount.textContent = `${members.length} members`;
  elements.teamShareButton.disabled = !workspace || !state.lastHistoryId;
  elements.teamMembersList.textContent = members.length
    ? members.map((member) => member.display_name || "Unnamed device").join(", ")
    : "No members loaded.";
}

async function createTeamWorkspace(event) {
  event.preventDefault();
  const name = elements.teamNameInput.value.trim();
  if (!name) {
    return;
  }
  await postJson("/api/team/create", { name });
  showToast("Team workspace created.");
  await loadTeamStatus();
}

async function shareCurrentAudit() {
  if (!state.lastHistoryId) {
    return;
  }
  const result = await postJson("/api/team/share-audit", { scan_id: state.lastHistoryId });
  showToast("Scan summary shared with team.");
  elements.teamAuditsList.textContent = `Shared audit ${result.shared_audit_id}`;
}

async function activateLicense(event) {
  event.preventDefault();
  const key = elements.licenseKeyInput.value.trim();
  if (!key) {
    elements.licenseActivationStatus.dataset.tone = "error";
    elements.licenseActivationStatus.textContent = "Enter a CloudSaver license key.";
    return;
  }
  elements.licenseActivationStatus.dataset.tone = "";
  elements.licenseActivationStatus.textContent = "Activating license...";
  try {
    const data = await postJson("/api/license/activate", {
      key,
      email: elements.licenseEmailInput.value.trim() || null,
    });
    state.license = data;
    renderLicenseBadge(data);
    elements.licenseActivationStatus.dataset.tone = "success";
    elements.licenseActivationStatus.textContent = data.is_pro
      ? "CloudSaver Pro activated. Thank you!"
      : "License activated, but it is expired.";
    showToast("CloudSaver license activated.");
    window.setTimeout(() => {
      document.querySelector("#upgrade-modal")?.close();
    }, 3000);
  } catch (error) {
    elements.licenseActivationStatus.dataset.tone = "error";
    elements.licenseActivationStatus.textContent = error.message;
  }
}

async function startCheckout(plan) {
  if (!state.capabilities?.payments_configured) {
    elements.licenseActivationStatus.dataset.tone = "error";
    elements.licenseActivationStatus.textContent = "Direct checkout is not configured in this preview build.";
    return;
  }
  elements.licenseActivationStatus.dataset.tone = "";
  elements.licenseActivationStatus.textContent = "Opening secure checkout...";
  try {
    const data = await postJson("/api/payments/checkout", {
      plan,
      email: elements.licenseEmailInput.value.trim() || null,
    });
    window.open(data.checkout_url, "_blank", "noopener");
    elements.licenseActivationStatus.textContent = "Complete checkout in the browser, then return to CloudSaver.";
  } catch (error) {
    elements.licenseActivationStatus.dataset.tone = "error";
    elements.licenseActivationStatus.textContent = error.message;
  }
}

async function loadLocations() {
  const response = await fetch("/api/locations");
  const data = await response.json();
  elements.locationOptions.innerHTML = data.locations
    .map((location) => `<option value="${escapeHtml(location.path)}">${escapeHtml(location.label)}</option>`)
    .join("");
  elements.quickLocations.innerHTML = data.locations
    .slice(0, 4)
    .map((location) => `<button type="button" data-path="${escapeHtml(location.path)}">${escapeHtml(location.label)}</button>`)
    .join("");
}

async function loadHistory() {
  const response = await fetch("/api/history");
  const data = await response.json();
  if (!response.ok) {
    return;
  }
  renderHistory(data.scans || []);
  renderSidebarRecentScans(data.scans || []);
}

function renderHistory(scans) {
  elements.historyList.innerHTML = scans
    .map((scan) => {
      const date = new Date(scan.scanned_at * 1000).toLocaleString();
      return `
        <div class="history-item">
          <div>
            <strong title="${escapeHtml(scan.root_path)}">${escapeHtml(scan.root_path)}</strong>
            <span>${escapeHtml(date)} - ${scan.file_count} files</span>
          </div>
          <span>${formatBytes(scan.recoverable_bytes)} recoverable</span>
        </div>
      `;
    })
    .join("") || "<div class='empty-state'>No scan history yet.</div>";
}

function renderSidebarRecentScans(scans) {
  elements.sidebarRecentScans.innerHTML = scans
    .slice(0, 3)
    .map((scan) => {
      const date = new Date(scan.scanned_at * 1000).toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
      });
      return `
        <button type="button" data-path="${escapeHtml(scan.root_path)}">
          <strong title="${escapeHtml(scan.root_path)}">${escapeHtml(scan.root_path)}</strong>
          <span>Rescan folder - ${escapeHtml(date)}</span>
        </button>
      `;
    })
    .join("") || "<span class='starter-empty'>No recent folders.</span>";
}

function renderSummary(data) {
  const audit = data.audit;
  setMetricText(elements.metricTotal, audit.summary.total_human);
  elements.metricTotalDetail.textContent = `${audit.summary.file_count} files`;
  setMetricText(elements.metricFiles, String(audit.summary.file_count));
  elements.metricFilesDetail.textContent = "Local scan complete";
  setMetricText(elements.metricReducible, data.estimated_reducible_human);
  setMetricText(elements.metricDuplicates, audit.opportunities.duplicate_human);
  setMetricText(elements.metricCost, audit.opportunities.estimated_monthly_cost_avoided_human);
  elements.currentRoot.textContent = data.root_path;
  elements.overviewEmpty.hidden = true;
  elements.scanMeta.textContent = `${audit.summary.file_count} files - scanned ${new Date().toLocaleString()}`;
  if (elements.workspaceSubtitle) {
    elements.workspaceSubtitle.textContent = data.root_path;
  }
  renderCleanupPlan(audit, data.estimated_reducible_human);
  if (state.license?.is_pro) {
    refreshAdvisor();
  } else {
    elements.advisorPanel.hidden = true;
    checkUpgradeTriggers(audit);
  }
}

function renderCleanupPlan(audit, estimatedReducibleHuman) {
  const opportunities = audit.opportunities;
  elements.planConfidence.textContent = `${opportunities.estimated_recoverable_human} review opportunity`;
  renderSafeNextSteps(audit);
  elements.planDuplicates.textContent = opportunities.duplicate_count
    ? opportunities.duplicate_human
    : "No duplicates found";
  elements.planDuplicatesDetail.textContent = opportunities.duplicate_count
    ? `${opportunities.duplicate_count} extra copies found. Verified matches are the safest place to start.`
    : "CloudSaver did not find duplicate candidates in this scan.";
  elements.planImages.textContent = estimatedReducibleHuman;
  elements.planImagesDetail.textContent = opportunities.image_optimization_count
    ? `${opportunities.image_optimization_count} images can be copied at smaller size without changing originals.`
    : "No large reducible images were found in this scan.";
  elements.planLargeFiles.textContent = opportunities.large_file_human || `${opportunities.large_file_count} files`;
  elements.planLargeFilesDetail.textContent = opportunities.large_file_count
    ? `${opportunities.large_file_human} in large files needs manual review before moving.`
    : "No files over the large-file threshold were found.";
  elements.planVideo.textContent = opportunities.video_optimization_human || "0.00 B";
  elements.planVideoDetail.textContent = opportunities.video_optimization_count
    ? `${opportunities.video_optimization_count} video files could benefit from H.265/HEVC re-encoding.`
    : "Install FFprobe to estimate video savings, or scan a folder with video files.";
  elements.planAudio.textContent = opportunities.audio_optimization_human || "0.00 B";
  elements.planAudioDetail.textContent = opportunities.audio_optimization_count
    ? `${opportunities.audio_optimization_count} audio files could benefit from OPUS conversion.`
    : "Install FFprobe to estimate audio savings, or scan a folder with audio files.";
}

function renderSafeNextSteps(audit) {
  const opportunities = audit.opportunities;
  const duplicateStep = opportunities.duplicate_count
    ? {
        tone: "low",
        risk: "Low risk",
        title: "Review verified duplicates",
        body: `${opportunities.duplicate_count} extra copies found. Start with high-confidence duplicate groups and keep the recommended copy.`,
        action: "Review duplicates",
        target: "duplicates",
      }
    : {
        tone: "manual",
        risk: "Manual review",
        title: "Inspect largest folders",
        body: "No duplicate groups were found. Use the storage map to find folders worth reviewing manually.",
        action: "View storage map",
        target: "map",
      };
  const largeFileStep = opportunities.large_file_count
    ? {
        tone: "manual",
        risk: "Manual review",
        title: "Check large files",
        body: `${opportunities.large_file_human} in large files needs owner/context review before moving.`,
        action: "View files",
        target: "files",
      }
    : {
        tone: "optional",
        risk: "Optional",
        title: "Export a report",
        body: "Save a local report before making cleanup decisions or sharing a summary.",
        action: "Open files",
        target: "files",
      };
  const imageStep = opportunities.image_optimization_count
    ? {
        tone: "optional",
        risk: "Optional",
        title: "Create image copies",
        body: `${opportunities.image_optimization_count} images can be copied at a smaller size without changing originals.`,
        action: "Select images",
        planAction: "select-images",
      }
    : {
        tone: "optional",
        risk: "Optional",
        title: "Keep the report",
        body: "No large reducible images were found. Keep the scan history for comparison after cleanup.",
        action: "View history",
        target: "history",
      };
  elements.safeNextSteps.innerHTML = [duplicateStep, largeFileStep, imageStep]
    .map((step) => `
      <div class="safe-step ${step.tone}">
        <span>${escapeHtml(step.risk)}</span>
        <strong>${escapeHtml(step.title)}</strong>
        <p>${escapeHtml(step.body)}</p>
        <button type="button" class="plan-action" ${step.target ? `data-view-target="${escapeHtml(step.target)}"` : ""} ${step.planAction ? `data-plan-action="${escapeHtml(step.planAction)}"` : ""}>${escapeHtml(step.action)}</button>
      </div>
    `)
    .join("");
}

function renderAdvisorGate() {
  elements.advisorPanel.hidden = true;
  elements.advisorRefresh.hidden = true;
  elements.advisorStatusText.textContent = "Available with CloudSaver Pro";
  elements.advisorContent.innerHTML = "";
}

function renderAdvisorLoading() {
  elements.advisorPanel.hidden = false;
  elements.advisorRefresh.hidden = false;
  elements.advisorStatusText.textContent = "Analyzing your storage...";
  elements.advisorContent.innerHTML = `
    <div class="advisor-loading">
      <div class="advisor-skeleton"></div>
      <div class="advisor-skeleton advisor-skeleton--short"></div>
      <div class="advisor-skeleton"></div>
    </div>
  `;
}

function renderAdvisorRecommendations(data) {
  const recommendations = data.recommendations || [];
  elements.advisorPanel.hidden = false;
  elements.advisorRefresh.hidden = false;
  elements.advisorStatusText.textContent = data.total_opportunity_human || "Recommendations ready";
  elements.advisorContent.innerHTML = `
    <div class="advisor-headline">${escapeHtml(data.headline || "CloudSaver found storage opportunities.")}</div>
    <div class="advisor-recs">
      ${recommendations.map((rec) => `
        <div class="advisor-rec">
          <div class="advisor-rec-meta">
            <strong>${escapeHtml(rec.impact_human || "")}</strong>
            ${rec.cost_saving_human ? `<span class="advisor-cost-save">saves ${escapeHtml(rec.cost_saving_human)}</span>` : ""}
          </div>
          <div class="advisor-rec-body">
            <strong class="advisor-rec-title">${escapeHtml(rec.title || "")}</strong>
            <p>${escapeHtml(rec.explanation || "")}</p>
            <p class="advisor-action">${escapeHtml(rec.action || "")}</p>
          </div>
        </div>
      `).join("")}
    </div>
    <p class="advisor-encouragement">${escapeHtml(data.encouragement || "")}</p>
  `;
}

async function refreshAdvisor() {
  if (!state.audit) {
    return;
  }
  if (!state.license?.is_pro) {
    renderAdvisorGate();
    return;
  }
  if (!state.lastScanJobId) {
    return;
  }
  renderAdvisorLoading();
  try {
    const start = await postJson("/api/advisor/analyze", { job_id: state.lastScanJobId });
    const data = await waitForScan(start.job_id);
    renderAdvisorRecommendations(data);
  } catch (error) {
    elements.advisorStatusText.textContent = "Advisor unavailable";
    elements.advisorContent.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

function renderCategories(audit) {
  const categories = Object.entries(audit.by_category);
  const maxBytes = Math.max(...categories.map(([, summary]) => summary.bytes), 1);
  elements.categoryCount.textContent = `${categories.length} categories`;
  elements.categoryBars.innerHTML = categories
    .map(([category, summary]) => {
      const width = Math.max((summary.bytes / maxBytes) * 100, 2);
      return `
        <div class="category-row">
          <strong>${escapeHtml(category)}</strong>
          <div class="bar-track"><div class="bar-fill" style="width:${width}%"></div></div>
          <span>${formatBytes(summary.bytes)}</span>
        </div>
      `;
    })
    .join("") || emptyState("overview", "Choose a folder to begin your storage audit");
}

function renderFolders(audit) {
  elements.folderList.innerHTML = audit.top_folders
    .map((folder) => `
      <div class="folder-item">
        <div>
          <strong title="${escapeHtml(folder.folder_id)}">${escapeHtml(folder.folder_id)}</strong>
          <span>${folder.count} files</span>
        </div>
        <span>${formatBytes(folder.bytes)}</span>
      </div>
    `)
    .join("") || emptyState("overview", "Largest folders will appear after scanning");
}

function categoryColor(category) {
  const colors = {
    image: "#00d4b4",
    video: "#7c3aed",
    audio: "#f59e0b",
    document: "#2563eb",
    archive: "#64748b",
    other: "#94a3b8",
  };
  return colors[category] || colors.other;
}

function renderTreemap(files, audit = state.audit) {
  if (!audit) {
    elements.treemap.innerHTML = emptyState("map", "Scan to see where your storage is going");
    return;
  }

  elements.treemapBreadcrumbs.innerHTML = state.treemapFolder
    ? `<button type="button" data-folder="">Storage root</button><span>${escapeHtml(state.treemapFolder)}</span>`
    : "<span>Storage root</span>";

  const items = state.treemapFolder
    ? files
        .filter((file) => (file.parents || []).includes(state.treemapFolder))
        .filter((file) => file.size_bytes > 0)
        .slice(0, 40)
        .map((file) => ({
          kind: "file",
          id: file.id,
          label: file.name,
          detail: file.path,
          bytes: file.size_bytes,
          category: file.category,
        }))
    : (audit.top_folders || []).slice(0, 28).map((folder) => ({
        kind: "folder",
        label: folder.folder_id,
        detail: `${folder.count} files`,
        bytes: folder.bytes,
        folder: folder.folder_id,
      }));

  const totalBytes = items.reduce((total, item) => total + item.bytes, 0);
  if (!items.length || totalBytes <= 0) {
    elements.treemap.innerHTML = emptyState("map", "No files to visualize");
    return;
  }

  elements.treemap.innerHTML = items
    .map((item) => {
      const basis = Math.max((item.bytes / totalBytes) * 100, 4);
      const color = item.kind === "folder" ? "#31475c" : categoryColor(item.category);
      const folderAttribute = item.folder ? `data-folder="${escapeHtml(item.folder)}"` : "";
      const fileAttribute = item.id ? `data-file-id="${escapeHtml(item.id)}"` : "";
      return `
        <button class="treemap-tile ${item.kind}" type="button" ${folderAttribute} ${fileAttribute} style="flex-basis:${basis}%; background:${color}" title="${escapeHtml(item.detail)} - ${formatBytes(item.bytes)}">
          <strong>${escapeHtml(item.label)}</strong>
          <span>${formatBytes(item.bytes)}</span>
        </button>
      `;
    })
    .join("");
}

function setTreemapFolder(folder) {
  state.treemapFolder = folder;
  renderTreemap(state.files, state.audit);
  if (folder) {
    renderMapDetail({
      type: "Folder",
      title: folder,
      detail: "Showing files inside this folder.",
      bytes: null,
    });
  }
}

function renderMapDetail(item) {
  if (!item) {
    elements.mapDetail.innerHTML = `
      <span>Selection</span>
      <strong>No item selected</strong>
      <p>Click a folder or file in the map to inspect it.</p>
    `;
    return;
  }
  const size = item.bytes !== null && item.bytes !== undefined ? `<p>${formatBytes(item.bytes)}</p>` : "";
  const actions = item.file
    ? `
      <div class="map-detail-actions">
        <button type="button" class="table-action" data-map-select="${escapeHtml(item.file.id)}">Select in files</button>
      </div>
    `
    : "";
  elements.mapDetail.innerHTML = `
    <span>${escapeHtml(item.type)}</span>
    <strong title="${escapeHtml(item.title)}">${escapeHtml(item.title)}</strong>
    <p title="${escapeHtml(item.detail)}">${escapeHtml(item.detail)}</p>
    ${size}
    ${actions}
  `;
}

function renderDuplicates(audit) {
  const groups = audit.duplicate_candidates || [];
  state.duplicateGroups = groups;
  elements.duplicateCount.textContent = `${groups.length} groups`;
  elements.duplicateList.innerHTML = groups
    .map((group, index) => {
      const status = group.verification_status || "candidate";
      const confidence = group.confidence || "medium";
      const keepPath = group.recommended_keep_path || "";
      const keepReason = group.recommended_keep_reason || "Review the group before moving extra copies.";
      const files = (group.files || [])
        .slice(0, 4)
        .map((file) => {
          const keep = (file.id || file.path) === group.recommended_keep_id;
          return `<li class="${keep ? "recommended-keep" : ""}" title="${escapeHtml(file.path)}">${keep ? "Keep: " : ""}${escapeHtml(file.path)}</li>`;
        })
        .join("");
      return `
        <div class="duplicate-group">
          <div class="duplicate-summary">
            <div>
              <strong title="${escapeHtml(group.name)}">${escapeHtml(group.name)}</strong>
              <span>${group.copies} copies - ${formatBytes(group.recoverable_bytes)} recoverable</span>
            </div>
            <span class="status-pill ${status === "verified" ? "" : "unsupported"}">${escapeHtml(status)} / ${escapeHtml(confidence)}</span>
          </div>
          ${keepPath ? `<p class="duplicate-keep" title="${escapeHtml(keepPath)}"><strong>Recommended keep:</strong> ${escapeHtml(keepPath)}<span>${escapeHtml(keepReason)}</span></p>` : ""}
          <ul>${files}</ul>
          <div class="duplicate-actions">
            <button class="duplicate-action" type="button" data-duplicate-index="${index}">Review extra copies</button>
          </div>
        </div>
      `;
    })
    .join("") || emptyState("duplicate", "No duplicates found yet");
  renderPerceptualDuplicates();
}

function duplicateGroupMarkup(group, badge = "") {
  const keepPath = group.recommended_keep_path || "";
  const files = (group.files || [])
    .slice(0, 4)
    .map((file) => {
      const keep = (file.id || file.path) === group.recommended_keep_id;
      return `<li class="${keep ? "recommended-keep" : ""}" title="${escapeHtml(file.path)}">${keep ? "Keep: " : ""}${escapeHtml(file.path)}</li>`;
    })
    .join("");
  const status = group.verification_status || "candidate";
  const confidence = group.confidence || "medium";
  const badgeMarkup = badge
    ? `<span class="status-pill similar-pill">${escapeHtml(badge)}</span>`
    : `<span class="status-pill ${status === "verified" ? "" : "unsupported"}">${escapeHtml(status)} / ${escapeHtml(confidence)}</span>`;
  return `
    <div class="duplicate-group">
      <div class="duplicate-summary">
        <div>
          <strong title="${escapeHtml(group.name)}">${escapeHtml(group.name)}</strong>
          <span>${group.copies} copies - ${formatBytes(group.recoverable_bytes)} recoverable</span>
        </div>
        ${badgeMarkup}
      </div>
      ${keepPath ? `<p class="duplicate-keep" title="${escapeHtml(keepPath)}"><strong>Recommended keep:</strong> ${escapeHtml(keepPath)}</p>` : ""}
      <ul>${files}</ul>
    </div>
  `;
}

function renderPerceptualDuplicates() {
  const groups = state.perceptualGroups || [];
  elements.perceptualCount.textContent = state.audit ? `${groups.length} groups` : "Not scanned";
  elements.perceptualScanButton.disabled = !state.rootPath;
  elements.perceptualList.innerHTML = groups.length
    ? groups.map((group) => duplicateGroupMarkup(group, "Similar")).join("")
    : emptyState("duplicate", state.rootPath ? "No similar images found yet" : "Run a scan to find similar images");
}

function selectDuplicateExtras(index) {
  const group = state.duplicateGroups[index];
  if (!group || !Array.isArray(group.files)) {
    return [];
  }
  const keepId = group.recommended_keep_id;
  const extraFiles = group.files.filter((file, index) => {
    if (!keepId && index === 0) {
      return false;
    }
    return (file.id || file.path) !== keepId;
  });
  extraFiles.forEach((file) => state.selected.add(file.id));
  renderFiles();
  setStatus(`${extraFiles.length} duplicate extra copies selected for review.`, "ready");
  return extraFiles;
}

function selectReducibleImages() {
  const reducibleFiles = state.files.filter((file) => file.reduction.supported);
  reducibleFiles.forEach((file) => state.selected.add(file.id));
  renderFiles();
  setStatus(`${reducibleFiles.length} reducible image files selected.`, "ready");
  setWorkspaceView("files");
}

function filterFiles() {
  const query = elements.filterInput.value.trim().toLowerCase();
  const categoryQuery = elements.categoryFilter.value;
  state.filteredFiles = state.files.filter((file) => {
    const categoryMatches = categoryQuery ? file.category === categoryQuery : true;
    const textMatches = query
      ? `${file.name} ${file.path} ${file.category}`.toLowerCase().includes(query)
      : true;
    return categoryMatches && textMatches;
  });
  state.fileTablePage = 0;
  renderFiles();
}

function applyCategoryFilter(category) {
  elements.categoryFilter.value = category;
  elements.filterInput.value = "";
  filterFiles();
  setWorkspaceView("files");
}

function renderFiles() {
  const visibleLimit = (state.fileTablePage + 1) * state.fileTablePageSize;
  const visibleFiles = state.filteredFiles.slice(0, visibleLimit);
  elements.fileCount.textContent = `Showing ${visibleFiles.length} of ${state.filteredFiles.length} files`;
  if (!state.filteredFiles.length) {
    elements.fileTableBody.innerHTML = `<tr><td colspan='8'>${emptyState("table", state.audit ? "No files match the current filter" : "Files will appear here after scanning")}</td></tr>`;
    updateSelectionSummary();
    return;
  }

  const rows = visibleFiles
    .map((file) => {
      const supported = file.reduction.supported;
      const checked = state.selected.has(file.id) ? "checked" : "";
      const statusClass = supported ? "status-pill" : "status-pill unsupported";
      const statusText = supported ? "Reducible" : "Review only";
      const expected = supported
        ? `${file.reduction.estimated_saved_human} (${file.reduction.estimated_reduction_percent}%)`
        : "-";
      const codec = codecLabel(file);
      return `
        <tr>
          <td class="select-cell">
            <input type="checkbox" data-file-id="${escapeHtml(file.id)}" ${checked} aria-label="Select ${escapeHtml(file.name)}">
          </td>
          <td>
            <span class="file-name" title="${escapeHtml(file.name)}">${escapeHtml(file.name)}</span>
            <span class="file-path" title="${escapeHtml(file.path)}">${escapeHtml(file.path)}</span>
          </td>
          <td>${escapeHtml(file.category)}</td>
          <td>${formatBytes(file.size_bytes)}</td>
          <td>${expected}</td>
          <td>${codec}</td>
          <td><span class="${statusClass}">${statusText}</span></td>
          <td><button class="table-action" type="button" data-reveal-path="${escapeHtml(file.path)}">Reveal</button></td>
        </tr>
      `;
    })
    .join("");
  const sentinel = visibleFiles.length < state.filteredFiles.length
    ? "<tr id='file-table-sentinel'><td colspan='8'>Loading more files...</td></tr>"
    : "";
  elements.fileTableBody.innerHTML = rows + sentinel;
  observeFileTableSentinel();
  updateSelectionSummary();
}

function observeFileTableSentinel() {
  if (fileTableObserver) {
    fileTableObserver.disconnect();
  }
  const sentinel = document.querySelector("#file-table-sentinel");
  if (!sentinel || !("IntersectionObserver" in window)) {
    return;
  }
  fileTableObserver = new IntersectionObserver((entries) => {
    if (entries.some((entry) => entry.isIntersecting)) {
      state.fileTablePage += 1;
      renderFiles();
    }
  });
  fileTableObserver.observe(sentinel);
}

function codecLabel(file) {
  const video = file.video_estimate || {};
  if (video.codec_name) {
    const size = video.width && video.height ? `${video.width}x${video.height}` : "video";
    return `<span class="codec-pill video">${escapeHtml(video.codec_name.toUpperCase())} · ${escapeHtml(size)}</span>`;
  }
  const audio = file.audio_estimate || {};
  if (audio.codec_name) {
    const rate = audio.sample_rate ? `${audio.sample_rate}Hz` : "audio";
    return `<span class="codec-pill audio">${escapeHtml(audio.codec_name.toUpperCase())} · ${escapeHtml(rate)}</span>`;
  }
  return "-";
}

function updateSelectionSummary() {
  const selectedFiles = state.files.filter((file) => state.selected.has(file.id));
  const estimatedBytes = selectedFiles.reduce(
    (total, file) => total + file.reduction.estimated_saved_bytes,
    0
  );
  const selectedReducible = selectedFiles.filter((file) => file.reduction.supported);
  const selectedConvertible = selectedFiles.filter((file) => file.reduction.format_conversion_available);
  elements.selectionSummary.textContent = selectedFiles.length
    ? `${selectedFiles.length} selected, approximately ${formatBytes(estimatedBytes)} image-copy savings`
    : "Select image files to create smaller copies after scanning.";
  elements.reduceButton.disabled = selectedReducible.length === 0 && selectedConvertible.length === 0;
  elements.quarantineButton.disabled = selectedFiles.length === 0;
  elements.exportJsonButton.disabled = !state.audit;
  elements.exportCsvButton.disabled = !state.audit;
  const visibleReducible = state.filteredFiles.filter((file) => file.reduction.supported);
  const selectedVisibleReducible = visibleReducible.filter((file) => state.selected.has(file.id));
  if (selectedVisibleReducible.length === 0) {
    elements.selectAll.checked = false;
    elements.selectAll.indeterminate = false;
  } else if (selectedVisibleReducible.length === visibleReducible.length) {
    elements.selectAll.checked = true;
    elements.selectAll.indeterminate = false;
  } else {
    elements.selectAll.checked = false;
    elements.selectAll.indeterminate = true;
  }
}

function reportFilename(extension) {
  const timestamp = new Date().toISOString().replaceAll(":", "-").slice(0, 19);
  return `cloudsaver-report-${timestamp}.${extension}`;
}

function downloadText(filename, text, type) {
  const blob = new Blob([text], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function csvCell(value) {
  const text = String(value ?? "");
  return `"${text.replaceAll('"', '""')}"`;
}

function exportJsonReport() {
  if (!state.audit) {
    return;
  }
  downloadText(
    reportFilename("json"),
    JSON.stringify({ root_path: state.rootPath, audit: state.audit, files: state.files }, null, 2),
    "application/json"
  );
}

function exportCsvReport() {
  if (!state.audit) {
    return;
  }
  const headers = [
    "name",
    "path",
    "category",
    "size_bytes",
    "estimated_saved_bytes",
    "estimated_reduction_percent",
    "reduction_supported",
    "duplicate_verification",
  ];
  const rows = state.files.map((file) => [
    file.name,
    file.path,
    file.category,
    file.size_bytes,
    file.reduction.estimated_saved_bytes,
    file.reduction.estimated_reduction_percent,
    file.reduction.supported,
    file.duplicate_verification?.status || "",
  ]);
  const csv = [headers, ...rows].map((row) => row.map(csvCell).join(",")).join("\n");
  downloadText(reportFilename("csv"), `${csv}\n`, "text/csv");
}

async function scan(event) {
  event.preventDefault();
  const path = elements.pathInput.value.trim();
  if (!path) {
    setStatus("Enter a folder path to scan.", "error");
    return;
  }

  try {
    await runScanForPath(path, "Starting scan...");
  } catch {
    return;
  }
}

async function runScanForPath(path, startingMessage = "Refreshing scan...") {
  setStatus(startingMessage, "scanning", "Starting scan");
  state.scanCancelling = false;
  elements.form.querySelector("button[type=submit]").disabled = true;
  if (elements.stopScanBtn) {
    elements.stopScanBtn.hidden = false;
    elements.stopScanBtn.disabled = false;
    elements.stopScanBtn.querySelector("span").textContent = "Stop scan";
  }
  try {
    const start = await postJson("/api/scan/start", {
      path,
      quality: Number(elements.qualityInput.value),
      ...resolution(),
    });
    state.lastScanJobId = start.job_id;
    const data = await waitForScan(start.job_id);
    if (data === null) {
      setStatus("Scan stopped.", "idle");
      return null;
    }
    state.rootPath = data.root_path;
    state.files = data.files;
    state.filteredFiles = [...data.files];
    state.selected.clear();
    state.audit = data.audit;
    state.lastHistoryId = data.history_id;
    state.perceptualGroups = [];
    state.treemapFolder = "";
    renderMapDetail(null);
    renderSummary(data);
    renderCategories(data.audit);
    renderFolders(data.audit);
    renderTreemap(data.files, data.audit);
    renderDuplicates(data.audit);
    renderFiles();
    loadHistory();
    setStatus(`Scan complete. ${data.files.length} files analyzed.`, "complete");
    showToast(`Scan complete: ${data.files.length} files analyzed.`);
    renderTeamStatus(state.teamStatus || null);
    return data;
  } catch (error) {
    setStatus(error.message, "error");
    showToast(error.message, "error");
    throw error;
  } finally {
    elements.form.querySelector("button[type=submit]").disabled = false;
    if (elements.stopScanBtn) elements.stopScanBtn.hidden = true;
    state.scanCancelling = false;
  }
}

async function stopScan() {
  state.scanCancelling = true;
  if (elements.stopScanBtn) {
    elements.stopScanBtn.disabled = true;
    elements.stopScanBtn.querySelector("span").textContent = "Stopping…";
  }
  if (state.lastScanJobId) {
    postJson("/api/scan/cancel", { job_id: state.lastScanJobId }).catch(() => {});
  }
}

async function refreshCurrentScan(message = "Refreshing scan results...") {
  if (!state.rootPath) {
    return null;
  }
  return runScanForPath(state.rootPath, message);
}

async function waitForScan(jobId) {
  while (true) {
    if (state.scanCancelling) return null;
    const response = await fetch(`/api/scan/status?job_id=${encodeURIComponent(jobId)}`);
    const job = await response.json();
    if (!response.ok) {
      throw new Error(job.error || "Scan status request failed.");
    }
    if (job.status === "failed") {
      throw new Error(job.error || "Scan failed.");
    }
    if (job.status === "cancelled") return null;
    if (job.status === "complete") {
      return job.result;
    }
    const stage = job.stage || "Scanning files";
    const current = job.current_folder || job.current_path || "Preparing scan...";
    setStatus(`${current} - ${job.files_scanned || 0} files scanned`, "scanning", stage);
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
}

async function reduceSelected() {
  const fileIds = state.files
    .filter((file) => state.selected.has(file.id) && file.reduction.supported)
    .map((file) => file.id);
  if (!fileIds.length) {
    return;
  }
  elements.reduceButton.disabled = true;
  setStatus("Creating reduced image copies...", "scanning");
  try {
    const result = await postJson("/api/reduce", {
      root_path: state.rootPath,
      file_ids: fileIds,
      quality: Number(elements.qualityInput.value),
      ...resolution(),
    });
    const reduced = result.results.filter((item) => item.status === "reduced").length;
    setStatus(`${reduced} reduced copies created. Actual image-copy savings: ${result.total_saved_human}.`, "complete");
    showToast(`${reduced} reduced copies created.`);
  } catch (error) {
    setStatus(error.message, "error");
    showToast(error.message, "error");
  } finally {
    updateSelectionSummary();
  }
}

async function convertSelectedToWebp() {
  const fileIds = state.files
    .filter((file) => state.selected.has(file.id) && file.reduction.format_conversion_available)
    .map((file) => file.id);
  if (!fileIds.length) {
    return;
  }
  elements.reduceButton.disabled = true;
  setStatus("Converting selected images to WebP copies...", "scanning");
  try {
    const result = await postJson("/api/convert", {
      root_path: state.rootPath,
      file_ids: fileIds,
      target_format: "webp",
      quality: Number(elements.qualityInput.value),
      ...resolution(),
    });
    const converted = result.results.filter((item) => item.status === "reduced").length;
    setStatus(`${converted} WebP copies created. Estimated savings: ${result.total_saved_human}.`, "complete");
    showToast(`${converted} WebP copies created.`);
  } catch (error) {
    setStatus(error.message, "error");
    showToast(error.message, "error");
  } finally {
    updateSelectionSummary();
  }
}

async function optimizeSelectedImages() {
  const selectedFiles = state.files.filter((file) => state.selected.has(file.id));
  const convertible = selectedFiles.filter((file) => file.reduction.format_conversion_available);
  if (convertible.length && convertible.length === selectedFiles.length) {
    await convertSelectedToWebp();
    return;
  }
  await reduceSelected();
}

async function runPerceptualScan() {
  if (!state.rootPath) {
    return;
  }
  elements.perceptualScanButton.disabled = true;
  setStatus("Finding visually similar images...", "scanning");
  try {
    const start = await postJson("/api/scan/perceptual", {
      root_path: state.rootPath,
      threshold: 10,
    });
    const data = await waitForScan(start.job_id);
    state.perceptualGroups = data.perceptual_duplicate_groups || [];
    renderPerceptualDuplicates();
    setStatus(`${state.perceptualGroups.length} similar image groups found.`, "complete");
    showToast(`${state.perceptualGroups.length} similar image groups found.`);
  } catch (error) {
    setStatus(error.message, "error");
    showToast(error.message, "error");
  } finally {
    elements.perceptualScanButton.disabled = !state.rootPath;
  }
}

async function quarantineSelected() {
  const fileIds = [...state.selected];
  if (!fileIds.length) {
    return;
  }
  elements.quarantineButton.disabled = true;
  setStatus("Moving selected files to the local review folder...", "scanning");
  try {
    const result = await postJson("/api/quarantine", {
      root_path: state.rootPath,
      file_ids: fileIds,
    });
    setStatus(`${result.quarantined_count} files moved to review. Manifest: ${result.manifest_path}`, "complete");
    showToast(`${result.quarantined_count} files moved to review folder.`);
    if (!state.license?.is_pro && result.quarantined_count > 0) {
      window.setTimeout(() => {
        showUpgradeToast("Pro preview adds advanced media analysis and professional cleanup reports.");
      }, 2000);
    }
    state.reviewBatches.unshift({
      manifestPath: result.manifest_path,
      count: result.quarantined_count,
      createdAt: Date.now(),
    });
    renderReviewBatches();
    state.selected.clear();
    elements.selectAll.checked = false;
    await refreshCurrentScan("Refreshing scan after moving files to review...");
  } catch (error) {
    setStatus(error.message, "error");
    showToast(error.message, "error");
  } finally {
    updateSelectionSummary();
  }
}

function renderReviewBatches() {
  elements.reviewQueue.hidden = state.reviewBatches.length === 0;
  elements.restoreTestPrompt.hidden = state.reviewBatches.length === 0;
  elements.reviewBatches.innerHTML = state.reviewBatches
    .map((batch) => {
      const date = new Date(batch.createdAt).toLocaleString();
      return `
        <div class="review-batch">
          <div>
            <strong>${batch.count} files moved to review</strong>
            <span title="${escapeHtml(batch.manifestPath)}">${escapeHtml(date)} - ${escapeHtml(batch.manifestPath)}</span>
          </div>
          <button type="button" class="tertiary-action" data-restore-manifest="${escapeHtml(batch.manifestPath)}">Restore batch</button>
        </div>
      `;
    })
    .join("") || "<div class='empty-state'>Moved files will appear here for quick restore.</div>";
  updateReviewQueueBadge();
}

async function revealPath(path) {
  if (!path) {
    return;
  }
  try {
    await postJson("/api/reveal", { path });
    setStatus("Opened the file location.", "complete");
    showToast("Opened the file location.");
  } catch (error) {
    setStatus(error.message, "error");
    showToast(error.message, "error");
  }
}

async function restoreManifest() {
  const manifestPath = elements.restoreManifestInput.value.trim();
  if (!manifestPath) {
    setStatus("Enter a restore manifest path.", "error");
    return;
  }
  elements.restoreButton.disabled = true;
  setStatus("Restoring files from manifest...", "scanning");
  try {
    const result = await postJson("/api/restore", { manifest_path: manifestPath });
    const restored = result.results.filter((item) => item.status === "restored").length;
    setStatus(`${restored} files restored from review.`, "complete");
    showToast(`${restored} files restored from review.`);
    state.reviewBatches = state.reviewBatches.filter((batch) => batch.manifestPath !== manifestPath);
    renderReviewBatches();
    await refreshCurrentScan("Refreshing scan after restore...");
  } catch (error) {
    setStatus(error.message, "error");
    showToast(error.message, "error");
  } finally {
    elements.restoreButton.disabled = false;
  }
}

elements.form.addEventListener("submit", scan);
elements.stopScanBtn?.addEventListener("click", stopScan);
elements.qualityInput.addEventListener("input", () => {
  elements.qualityOutput.value = elements.qualityInput.value;
  elements.qualityOutput.textContent = elements.qualityInput.value;
});
elements.filterInput.addEventListener("input", filterFiles);
elements.categoryFilter.addEventListener("change", filterFiles);
elements.reduceButton.addEventListener("click", optimizeSelectedImages);
elements.quarantineButton.addEventListener("click", quarantineSelected);
elements.perceptualScanButton.addEventListener("click", runPerceptualScan);
elements.restoreButton.addEventListener("click", restoreManifest);
elements.exportJsonButton.addEventListener("click", exportJsonReport);
elements.exportCsvButton.addEventListener("click", exportCsvReport);
elements.licenseForm.addEventListener("submit", activateLicense);
elements.advisorRefresh.addEventListener("click", refreshAdvisor);
elements.paymentOptions.addEventListener("click", (event) => {
  const button = event.target.closest("[data-plan]");
  if (!button) {
    return;
  }
  startCheckout(button.dataset.plan);
});
elements.teamCreateForm.addEventListener("submit", createTeamWorkspace);
elements.teamShareButton.addEventListener("click", () => {
  shareCurrentAudit().catch((error) => showToast(error.message, "error"));
});
elements.upgradeNudgeDismiss.addEventListener("click", () => {
  const key = elements.upgradeNudge.dataset.triggerKey;
  if (key) {
    localStorage.setItem(`cloudsaver-upgrade-dismissed-${key}`, String(Date.now()));
  }
  elements.upgradeNudge.hidden = true;
});
elements.workspaceTabs.addEventListener("click", (event) => {
  const button = event.target.closest("[data-view-target]");
  if (!button) {
    return;
  }
  setWorkspaceView(button.dataset.viewTarget);
});
elements.sidebarToggle.addEventListener("click", () => {
  setSidebarOpen(!elements.sidebar.classList.contains("open"));
});
elements.sidebarBackdrop.addEventListener("click", () => setSidebarOpen(false));
elements.themeButtons.forEach((button) => {
  button.addEventListener("click", () => setThemePreference(button.dataset.themeOption));
});
systemThemeQuery.addEventListener("change", () => {
  if (storedThemePreference() === "system") {
    applyTheme("system");
  }
});
elements.modalTriggers.forEach((trigger) => {
  trigger.addEventListener("click", () => {
    const modal = document.querySelector(`#${trigger.dataset.modalTarget}`);
    if (modal?.showModal) {
      modal.showModal();
    }
  });
});
document.addEventListener("click", (event) => {
  const onboardPathButton = event.target.closest("[data-onboard-path]");
  if (onboardPathButton) {
    const value = onboardPathButton.dataset.onboardPath;
    if (value === "custom") {
      elements.pathInput.focus();
    } else if (value === "home") {
      elements.pathInput.value = "~";
    } else {
      elements.pathInput.value = `~/${value}`;
    }
    completeOnboarding();
    return;
  }
  if (event.target.closest("[data-onboarding-dismiss]")) {
    completeOnboarding();
    return;
  }
  const focusScanButton = event.target.closest("[data-focus-scan]");
  if (focusScanButton) {
    elements.pathInput.focus();
    return;
  }
  const closeButton = event.target.closest("[data-modal-close]");
  if (closeButton) {
    closeButton.closest("dialog")?.close();
  }
});
document.addEventListener("keydown", (event) => {
  const activeTag = document.activeElement?.tagName?.toLowerCase();
  const isTyping = ["input", "select", "textarea"].includes(activeTag);
  if (event.key === "?" && !isTyping) {
    document.querySelector("#shortcuts-modal")?.showModal();
    return;
  }
  if (event.key === "/" && !isTyping) {
    event.preventDefault();
    elements.filterInput.focus();
    return;
  }
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "s") {
    event.preventDefault();
    elements.form.requestSubmit();
    return;
  }
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "r") {
    event.preventDefault();
    refreshCurrentScan().catch(() => {});
    return;
  }
  if (!isTyping && /^[1-5]$/.test(event.key)) {
    const views = ["overview", "map", "duplicates", "files", "history"];
    setWorkspaceView(views[Number(event.key) - 1]);
    return;
  }
  if (event.key === "Escape" && elements.sidebar.classList.contains("open")) {
    setSidebarOpen(false);
    return;
  }
  if (event.key === "Escape" && elements.filterInput.value) {
    elements.filterInput.value = "";
    filterFiles();
  }
});
elements.form.addEventListener("submit", () => setSidebarOpen(false));
elements.recommendedPlan.addEventListener("click", (event) => {
  const categoryButton = event.target.closest("[data-category-filter]");
  if (categoryButton) {
    applyCategoryFilter(categoryButton.dataset.categoryFilter);
    return;
  }
  const viewButton = event.target.closest("[data-view-target]");
  if (viewButton) {
    setWorkspaceView(viewButton.dataset.viewTarget);
    return;
  }
  const actionButton = event.target.closest("[data-plan-action]");
  if (!actionButton) {
    return;
  }
  if (actionButton.dataset.planAction === "select-images") {
    selectReducibleImages();
  }
});
elements.quickLocations.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-path]");
  if (!button) {
    return;
  }
  elements.pathInput.value = button.dataset.path;
  setStatus(`Ready to scan ${button.textContent}.`, "ready");
  setSidebarOpen(false);
});
elements.sidebarRecentScans.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-path]");
  if (!button) {
    return;
  }
  const path = button.dataset.path;
  elements.pathInput.value = path;
  setSidebarOpen(false);
  runScanForPath(path, "Rescanning recent folder...").catch(() => {});
});
elements.treemap.addEventListener("click", (event) => {
  const tile = event.target.closest("[data-folder]");
  if (tile) {
    setTreemapFolder(tile.dataset.folder);
    return;
  }
  const fileTile = event.target.closest("[data-file-id]");
  if (fileTile) {
    const file = state.files.find((item) => item.id === fileTile.dataset.fileId);
    if (!file) {
      return;
    }
    renderMapDetail({
      type: file.category,
      title: file.name,
      detail: file.path,
      bytes: file.size_bytes,
      file,
    });
  }
});
elements.treemapBreadcrumbs.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-folder]");
  if (!button) {
    return;
  }
  setTreemapFolder(button.dataset.folder);
});
elements.mapDetail.addEventListener("click", (event) => {
  const selectButton = event.target.closest("[data-map-select]");
  if (!selectButton) {
    return;
  }
  state.selected.add(selectButton.dataset.mapSelect);
  renderFiles();
  setStatus("File selected from storage map.", "ready");
});
elements.duplicateList.addEventListener("click", (event) => {
  const selectButton = event.target.closest("button[data-duplicate-index]");
  if (!selectButton) {
    return;
  }
  selectDuplicateExtras(Number(selectButton.dataset.duplicateIndex));
  setWorkspaceView("files");
});
elements.fileTableBody.addEventListener("change", (event) => {
  const checkbox = event.target.closest("input[type='checkbox'][data-file-id]");
  if (!checkbox) {
    return;
  }
  if (checkbox.checked) {
    state.selected.add(checkbox.dataset.fileId);
  } else {
    state.selected.delete(checkbox.dataset.fileId);
  }
  updateSelectionSummary();
});
elements.fileTableBody.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-reveal-path]");
  if (!button) {
    return;
  }
  revealPath(button.dataset.revealPath);
});
elements.reviewBatches.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-restore-manifest]");
  if (!button) {
    return;
  }
  elements.restoreManifestInput.value = button.dataset.restoreManifest;
  restoreManifest();
});
elements.restoreTestPrompt.addEventListener("click", (event) => {
  if (!event.target.closest("[data-restore-latest]")) {
    return;
  }
  const latest = state.reviewBatches[0];
  if (!latest) {
    return;
  }
  elements.restoreManifestInput.value = latest.manifestPath;
  restoreManifest();
});
elements.selectAll.addEventListener("change", () => {
  const visibleReducible = state.filteredFiles.filter((file) => file.reduction.supported);
  if (elements.selectAll.checked) {
    visibleReducible.forEach((file) => state.selected.add(file.id));
  } else {
    visibleReducible.forEach((file) => state.selected.delete(file.id));
  }
  renderFiles();
});

loadLocations().catch(() => setStatus("Location suggestions are unavailable.", "error"));
loadHistory().catch(() => {});
loadCapabilities().catch(() => {
  elements.paymentOptions.hidden = true;
});
loadLicense().catch(() => {});
loadUpdateStatus().catch(() => {});
applyTheme();
showOnboardingIfNeeded();
