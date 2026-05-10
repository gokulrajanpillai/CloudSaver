const state = {
  rootPath: "",
  files: [],
  filteredFiles: [],
  selected: new Set(),
  audit: null,
  treemapFolder: "",
  reviewBatches: [],
  duplicateGroups: [],
};

const elements = {
  form: document.querySelector("#scan-form"),
  pathInput: document.querySelector("#path-input"),
  locationOptions: document.querySelector("#location-options"),
  quickLocations: document.querySelector("#quick-locations"),
  scanStarters: document.querySelector("#scan-starters"),
  qualityInput: document.querySelector("#quality-input"),
  qualityOutput: document.querySelector("#quality-output"),
  resolutionInput: document.querySelector("#resolution-input"),
  status: document.querySelector("#scan-status"),
  scanStateLabel: document.querySelector("#scan-state-label"),
  scanStateTitle: document.querySelector("#scan-state-title"),
  metricTotal: document.querySelector("#metric-total"),
  metricFiles: document.querySelector("#metric-files"),
  metricReducible: document.querySelector("#metric-reducible"),
  metricDuplicates: document.querySelector("#metric-duplicates"),
  metricCost: document.querySelector("#metric-cost"),
  currentRoot: document.querySelector("#current-root"),
  selectionSummary: document.querySelector("#selection-summary"),
  filterInput: document.querySelector("#filter-input"),
  reduceButton: document.querySelector("#reduce-button"),
  quarantineButton: document.querySelector("#quarantine-button"),
  exportJsonButton: document.querySelector("#export-json-button"),
  exportCsvButton: document.querySelector("#export-csv-button"),
  planConfidence: document.querySelector("#plan-confidence"),
  planDuplicates: document.querySelector("#plan-duplicates"),
  planDuplicatesDetail: document.querySelector("#plan-duplicates-detail"),
  planImages: document.querySelector("#plan-images"),
  planImagesDetail: document.querySelector("#plan-images-detail"),
  planLargeFiles: document.querySelector("#plan-large-files"),
  planLargeFilesDetail: document.querySelector("#plan-large-files-detail"),
  recommendedPlan: document.querySelector("#recommended-plan"),
  categoryCount: document.querySelector("#category-count"),
  categoryBars: document.querySelector("#category-bars"),
  folderList: document.querySelector("#folder-list"),
  treemapBreadcrumbs: document.querySelector("#treemap-breadcrumbs"),
  treemap: document.querySelector("#treemap"),
  mapDetail: document.querySelector("#map-detail"),
  historyList: document.querySelector("#history-list"),
  duplicateCount: document.querySelector("#duplicate-count"),
  duplicateList: document.querySelector("#duplicate-list"),
  restoreManifestInput: document.querySelector("#restore-manifest-input"),
  restoreButton: document.querySelector("#restore-button"),
  reviewBatches: document.querySelector("#review-batches"),
  supportHeadline: document.querySelector("#support-headline"),
  supportDetail: document.querySelector("#support-detail"),
  fileCount: document.querySelector("#file-count"),
  fileTableBody: document.querySelector("#file-table-body"),
  selectAll: document.querySelector("#select-all"),
  workspaceTabs: document.querySelector(".workspace-tabs"),
  workspaceViews: document.querySelectorAll(".workspace-view"),
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
    neutral: ["Ready", "Choose a folder"],
    ready: ["Ready", "Ready to scan"],
    scanning: ["Scanning", "Scan in progress"],
    complete: ["Complete", "Scan complete"],
    error: ["Needs attention", "Check scan input"],
  };
  return states[tone] || states.neutral;
}

function setStatus(message, tone = "neutral") {
  elements.status.textContent = message;
  elements.status.dataset.tone = tone;
  const [label, title] = scanStateForTone(tone);
  elements.scanStateLabel.textContent = label;
  elements.scanStateTitle.textContent = title;
}

function setWorkspaceView(view) {
  elements.workspaceViews.forEach((section) => {
    section.classList.toggle("active", section.dataset.view === view);
  });
  elements.workspaceTabs.querySelectorAll("[data-view-target]").forEach((button) => {
    button.classList.toggle("active", button.dataset.viewTarget === view);
  });
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Request failed.");
  }
  return data;
}

async function loadLocations() {
  const response = await fetch("/api/locations");
  const data = await response.json();
  elements.locationOptions.innerHTML = data.locations
    .map((location) => `<option value="${escapeHtml(location.path)}">${escapeHtml(location.label)}</option>`)
    .join("");
  elements.quickLocations.innerHTML = data.locations
    .slice(0, 6)
    .map((location) => `<button type="button" data-path="${escapeHtml(location.path)}">${escapeHtml(location.label)}</button>`)
    .join("");
  renderScanStarters(data.locations || []);
}

function renderScanStarters(locations) {
  const priority = ["Downloads", "Pictures", "Desktop", "CloudStorage", "Documents"];
  const starters = priority
    .map((label) => locations.find((location) => location.label === label || location.path.endsWith(`/${label}`)))
    .filter(Boolean);
  const uniqueStarters = starters.filter(
    (location, index, all) => all.findIndex((item) => item.path === location.path) === index
  );
  elements.scanStarters.innerHTML = uniqueStarters
    .slice(0, 4)
    .map(
      (location) => `
        <button type="button" data-path="${escapeHtml(location.path)}">
          <strong>${escapeHtml(starterLabel(location.label))}</strong>
          <span>${escapeHtml(location.path)}</span>
        </button>
      `
    )
    .join("") || "<span class='starter-empty'>Common folders were not found.</span>";
}

function starterLabel(label) {
  const labels = {
    Downloads: "Downloads",
    Pictures: "Photos",
    Desktop: "Desktop",
    CloudStorage: "Cloud folders",
    Documents: "Documents",
  };
  return labels[label] || label;
}

async function loadHistory() {
  const response = await fetch("/api/history");
  const data = await response.json();
  if (!response.ok) {
    return;
  }
  renderHistory(data.scans || []);
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

function renderSummary(data) {
  const audit = data.audit;
  elements.metricTotal.textContent = audit.summary.total_human;
  elements.metricFiles.textContent = String(audit.summary.file_count);
  elements.metricReducible.textContent = data.estimated_reducible_human;
  elements.metricDuplicates.textContent = audit.opportunities.duplicate_human;
  elements.metricCost.textContent = audit.opportunities.estimated_monthly_cost_avoided_human;
  elements.currentRoot.textContent = data.root_path;
  elements.supportHeadline.textContent = `${data.estimated_reducible_human} of image savings estimated`;
  elements.supportDetail.textContent = `CloudSaver scanned ${audit.summary.file_count} files locally and found ${audit.opportunities.estimated_recoverable_human} in review opportunities. Sponsorship funds safer cleanup, signed builds, and platform support.`;
  renderCleanupPlan(audit, data.estimated_reducible_human);
}

function renderCleanupPlan(audit, estimatedReducibleHuman) {
  const opportunities = audit.opportunities;
  elements.planConfidence.textContent = `${opportunities.estimated_recoverable_human} review opportunity`;
  elements.planDuplicates.textContent = opportunities.duplicate_count
    ? `${opportunities.duplicate_human} duplicate review`
    : "No duplicates found";
  elements.planDuplicatesDetail.textContent = opportunities.duplicate_count
    ? `${opportunities.duplicate_count} extra copies found. Verified matches are the safest place to start.`
    : "CloudSaver did not find duplicate candidates in this scan.";
  elements.planImages.textContent = `${estimatedReducibleHuman} image reduction`;
  elements.planImagesDetail.textContent = opportunities.image_optimization_count
    ? `${opportunities.image_optimization_count} images can be copied at smaller size without changing originals.`
    : "No large reducible images were found in this scan.";
  elements.planLargeFiles.textContent = `${opportunities.large_file_count} large files`;
  elements.planLargeFilesDetail.textContent = opportunities.large_file_count
    ? `${opportunities.large_file_human} in large files needs manual review before moving.`
    : "No files over the large-file threshold were found.";
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
    .join("") || "<div class='empty-state'>No categories found.</div>";
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
    .join("") || "<div class='empty-state'>No folders found.</div>";
}

function categoryColor(category) {
  const colors = {
    image: "#16806a",
    video: "#8f5fe8",
    audio: "#b7791f",
    document: "#1f6fb2",
    archive: "#596579",
    other: "#7a8794",
  };
  return colors[category] || colors.other;
}

function renderTreemap(files, audit = state.audit) {
  if (!audit) {
    elements.treemap.innerHTML = "<div class='empty-state'>Run a scan to visualize storage usage.</div>";
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
    elements.treemap.innerHTML = "<div class='empty-state'>No files to visualize.</div>";
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
        <button type="button" class="table-action" data-map-reveal="${escapeHtml(item.file.path)}">Reveal</button>
        <button type="button" class="table-action" data-map-select="${escapeHtml(item.file.id)}">Select</button>
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
      const files = (group.files || [])
        .slice(0, 4)
        .map((file) => `<li title="${escapeHtml(file.path)}">${escapeHtml(file.path)}</li>`)
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
          <ul>${files}</ul>
          <div class="duplicate-actions">
            <button class="duplicate-action" type="button" data-duplicate-index="${index}">Select extra copies</button>
            <button class="duplicate-action primary" type="button" data-move-duplicate-index="${index}">Move extra copies to review</button>
          </div>
        </div>
      `;
    })
    .join("") || "<div class='empty-state'>No duplicate candidates found.</div>";
}

function selectDuplicateExtras(index) {
  const group = state.duplicateGroups[index];
  if (!group || !Array.isArray(group.files)) {
    return [];
  }
  const extraFiles = group.files.slice(1);
  extraFiles.forEach((file) => state.selected.add(file.id));
  renderFiles();
  setStatus(`${extraFiles.length} duplicate extra copies selected for review.`, "ready");
  return extraFiles;
}

async function moveDuplicateExtras(index) {
  const extraFiles = selectDuplicateExtras(index);
  if (!extraFiles.length) {
    return;
  }
  await quarantineSelected();
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
  state.filteredFiles = query
    ? state.files.filter((file) => `${file.name} ${file.path} ${file.category}`.toLowerCase().includes(query))
    : [...state.files];
  renderFiles();
}

function renderFiles() {
  elements.fileCount.textContent = `${state.filteredFiles.length} files`;
  if (!state.filteredFiles.length) {
    elements.fileTableBody.innerHTML = "<tr><td colspan='7' class='empty-state'>No files match the current filter.</td></tr>";
    updateSelectionSummary();
    return;
  }

  elements.fileTableBody.innerHTML = state.filteredFiles
    .map((file) => {
      const supported = file.reduction.supported;
      const checked = state.selected.has(file.id) ? "checked" : "";
      const statusClass = supported ? "status-pill" : "status-pill unsupported";
      const statusText = supported ? "Reducible" : "Review only";
      const expected = supported
        ? `${file.reduction.estimated_saved_human} (${file.reduction.estimated_reduction_percent}%)`
        : "-";
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
          <td><span class="${statusClass}">${statusText}</span></td>
          <td><button class="table-action" type="button" data-reveal-path="${escapeHtml(file.path)}">Reveal</button></td>
        </tr>
      `;
    })
    .join("");
  updateSelectionSummary();
}

function updateSelectionSummary() {
  const selectedFiles = state.files.filter((file) => state.selected.has(file.id));
  const estimatedBytes = selectedFiles.reduce(
    (total, file) => total + file.reduction.estimated_saved_bytes,
    0
  );
  const selectedReducible = selectedFiles.filter((file) => file.reduction.supported);
  elements.selectionSummary.textContent = selectedFiles.length
    ? `${selectedFiles.length} selected, approximately ${formatBytes(estimatedBytes)} image-copy savings`
    : "Select image files to create smaller copies after scanning.";
  elements.reduceButton.disabled = selectedReducible.length === 0;
  elements.quarantineButton.disabled = selectedFiles.length === 0;
  elements.exportJsonButton.disabled = !state.audit;
  elements.exportCsvButton.disabled = !state.audit;
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
  setStatus(startingMessage, "scanning");
  elements.form.querySelector("button").disabled = true;
  try {
    const start = await postJson("/api/scan/start", {
      path,
      quality: Number(elements.qualityInput.value),
      ...resolution(),
    });
    const data = await waitForScan(start.job_id);
    state.rootPath = data.root_path;
    state.files = data.files;
    state.filteredFiles = [...data.files];
    state.selected.clear();
    state.audit = data.audit;
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
    return data;
  } catch (error) {
    setStatus(error.message, "error");
    throw error;
  } finally {
    elements.form.querySelector("button").disabled = false;
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
    const response = await fetch(`/api/scan/status?job_id=${encodeURIComponent(jobId)}`);
    const job = await response.json();
    if (!response.ok) {
      throw new Error(job.error || "Scan status request failed.");
    }
    if (job.status === "failed") {
      throw new Error(job.error || "Scan failed.");
    }
    if (job.status === "complete") {
      return job.result;
    }
    const current = job.current_folder || job.current_path || "Preparing scan...";
    setStatus(`Scanning ${job.files_scanned || 0} files... ${current}`, "scanning");
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
  } catch (error) {
    setStatus(error.message, "error");
  } finally {
    updateSelectionSummary();
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
  } finally {
    updateSelectionSummary();
  }
}

function renderReviewBatches() {
  elements.reviewBatches.innerHTML = state.reviewBatches
    .map((batch) => {
      const date = new Date(batch.createdAt).toLocaleString();
      return `
        <div class="review-batch">
          <div>
            <strong>${batch.count} files moved to review</strong>
            <span title="${escapeHtml(batch.manifestPath)}">${escapeHtml(date)} - ${escapeHtml(batch.manifestPath)}</span>
          </div>
          <button type="button" class="tertiary-action" data-restore-manifest="${escapeHtml(batch.manifestPath)}">Restore</button>
        </div>
      `;
    })
    .join("") || "<div class='empty-state'>Moved files will appear here for quick restore.</div>";
}

async function revealPath(path) {
  if (!path) {
    return;
  }
  try {
    await postJson("/api/reveal", { path });
    setStatus("Opened the file location.", "complete");
  } catch (error) {
    setStatus(error.message, "error");
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
    state.reviewBatches = state.reviewBatches.filter((batch) => batch.manifestPath !== manifestPath);
    renderReviewBatches();
    await refreshCurrentScan("Refreshing scan after restore...");
  } catch (error) {
    setStatus(error.message, "error");
  } finally {
    elements.restoreButton.disabled = false;
  }
}

elements.form.addEventListener("submit", scan);
elements.qualityInput.addEventListener("input", () => {
  elements.qualityOutput.value = elements.qualityInput.value;
  elements.qualityOutput.textContent = elements.qualityInput.value;
});
elements.filterInput.addEventListener("input", filterFiles);
elements.reduceButton.addEventListener("click", reduceSelected);
elements.quarantineButton.addEventListener("click", quarantineSelected);
elements.restoreButton.addEventListener("click", restoreManifest);
elements.exportJsonButton.addEventListener("click", exportJsonReport);
elements.exportCsvButton.addEventListener("click", exportCsvReport);
elements.workspaceTabs.addEventListener("click", (event) => {
  const button = event.target.closest("[data-view-target]");
  if (!button) {
    return;
  }
  setWorkspaceView(button.dataset.viewTarget);
});
elements.recommendedPlan.addEventListener("click", (event) => {
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
});
elements.scanStarters.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-path]");
  if (!button) {
    return;
  }
  elements.pathInput.value = button.dataset.path;
  setStatus(`Ready to scan ${button.querySelector("strong").textContent}.`, "ready");
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
  const revealButton = event.target.closest("[data-map-reveal]");
  if (revealButton) {
    revealPath(revealButton.dataset.mapReveal);
    return;
  }
  const selectButton = event.target.closest("[data-map-select]");
  if (!selectButton) {
    return;
  }
  state.selected.add(selectButton.dataset.mapSelect);
  renderFiles();
  setStatus("File selected from storage map.", "ready");
});
elements.duplicateList.addEventListener("click", (event) => {
  const moveButton = event.target.closest("button[data-move-duplicate-index]");
  if (moveButton) {
    moveDuplicateExtras(Number(moveButton.dataset.moveDuplicateIndex));
    return;
  }
  const selectButton = event.target.closest("button[data-duplicate-index]");
  if (!selectButton) {
    return;
  }
  selectDuplicateExtras(Number(selectButton.dataset.duplicateIndex));
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
