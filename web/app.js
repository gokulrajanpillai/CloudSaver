const state = {
  rootPath: "",
  files: [],
  filteredFiles: [],
  selected: new Set(),
  audit: null,
  treemapFolder: "",
};

const elements = {
  form: document.querySelector("#scan-form"),
  pathInput: document.querySelector("#path-input"),
  locationOptions: document.querySelector("#location-options"),
  quickLocations: document.querySelector("#quick-locations"),
  qualityInput: document.querySelector("#quality-input"),
  qualityOutput: document.querySelector("#quality-output"),
  resolutionInput: document.querySelector("#resolution-input"),
  status: document.querySelector("#scan-status"),
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
  categoryCount: document.querySelector("#category-count"),
  categoryBars: document.querySelector("#category-bars"),
  folderList: document.querySelector("#folder-list"),
  treemapBreadcrumbs: document.querySelector("#treemap-breadcrumbs"),
  treemap: document.querySelector("#treemap"),
  historyList: document.querySelector("#history-list"),
  duplicateCount: document.querySelector("#duplicate-count"),
  duplicateList: document.querySelector("#duplicate-list"),
  restoreManifestInput: document.querySelector("#restore-manifest-input"),
  restoreButton: document.querySelector("#restore-button"),
  fileCount: document.querySelector("#file-count"),
  fileTableBody: document.querySelector("#file-table-body"),
  selectAll: document.querySelector("#select-all"),
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

function setStatus(message, tone = "neutral") {
  elements.status.textContent = message;
  elements.status.dataset.tone = tone;
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
      return `
        <button class="treemap-tile ${item.kind}" type="button" ${folderAttribute} style="flex-basis:${basis}%; background:${color}" title="${escapeHtml(item.detail)} - ${formatBytes(item.bytes)}">
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
}

function renderDuplicates(audit) {
  const groups = audit.duplicate_candidates || [];
  elements.duplicateCount.textContent = `${groups.length} groups`;
  elements.duplicateList.innerHTML = groups
    .map((group) => {
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
        </div>
      `;
    })
    .join("") || "<div class='empty-state'>No duplicate candidates found.</div>";
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
    elements.fileTableBody.innerHTML = "<tr><td colspan='6' class='empty-state'>No files match the current filter.</td></tr>";
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
    ? `${selectedFiles.length} selected, approximately ${formatBytes(estimatedBytes)} reducible`
    : "Select reducible files after scanning.";
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

  setStatus("Starting scan...");
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
    renderSummary(data);
    renderCategories(data.audit);
    renderFolders(data.audit);
    renderTreemap(data.files, data.audit);
    renderDuplicates(data.audit);
    renderFiles();
    loadHistory();
    setStatus(`Scan complete. ${data.files.length} files analyzed.`);
  } catch (error) {
    setStatus(error.message, "error");
  } finally {
    elements.form.querySelector("button").disabled = false;
  }
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
    setStatus(`Scanning ${job.files_scanned || 0} files... ${current}`);
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
  setStatus("Creating reduced copies in output/reduced...");
  try {
    const result = await postJson("/api/reduce", {
      root_path: state.rootPath,
      file_ids: fileIds,
      quality: Number(elements.qualityInput.value),
      ...resolution(),
    });
    const reduced = result.results.filter((item) => item.status === "reduced").length;
    setStatus(`${reduced} files reduced. Actual saved size: ${result.total_saved_human}.`);
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
  setStatus("Moving selected files to the local review folder...");
  try {
    const result = await postJson("/api/quarantine", {
      root_path: state.rootPath,
      file_ids: fileIds,
    });
    setStatus(`${result.quarantined_count} files moved to review. Manifest: ${result.manifest_path}`);
    state.selected.clear();
  } catch (error) {
    setStatus(error.message, "error");
  } finally {
    updateSelectionSummary();
  }
}

async function restoreManifest() {
  const manifestPath = elements.restoreManifestInput.value.trim();
  if (!manifestPath) {
    setStatus("Enter a restore manifest path.", "error");
    return;
  }
  elements.restoreButton.disabled = true;
  setStatus("Restoring files from manifest...");
  try {
    const result = await postJson("/api/restore", { manifest_path: manifestPath });
    const restored = result.results.filter((item) => item.status === "restored").length;
    setStatus(`${restored} files restored from review.`);
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
elements.quickLocations.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-path]");
  if (!button) {
    return;
  }
  elements.pathInput.value = button.dataset.path;
  setStatus(`Ready to scan ${button.textContent}.`);
});
elements.treemap.addEventListener("click", (event) => {
  const tile = event.target.closest("[data-folder]");
  if (!tile) {
    return;
  }
  setTreemapFolder(tile.dataset.folder);
});
elements.treemapBreadcrumbs.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-folder]");
  if (!button) {
    return;
  }
  setTreemapFolder(button.dataset.folder);
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
