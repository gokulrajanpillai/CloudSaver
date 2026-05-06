const state = {
  rootPath: "",
  files: [],
  filteredFiles: [],
  selected: new Set(),
  audit: null,
};

const elements = {
  form: document.querySelector("#scan-form"),
  pathInput: document.querySelector("#path-input"),
  locationOptions: document.querySelector("#location-options"),
  qualityInput: document.querySelector("#quality-input"),
  qualityOutput: document.querySelector("#quality-output"),
  resolutionInput: document.querySelector("#resolution-input"),
  status: document.querySelector("#scan-status"),
  metricTotal: document.querySelector("#metric-total"),
  metricFiles: document.querySelector("#metric-files"),
  metricReducible: document.querySelector("#metric-reducible"),
  metricDuplicates: document.querySelector("#metric-duplicates"),
  currentRoot: document.querySelector("#current-root"),
  selectionSummary: document.querySelector("#selection-summary"),
  filterInput: document.querySelector("#filter-input"),
  reduceButton: document.querySelector("#reduce-button"),
  categoryCount: document.querySelector("#category-count"),
  categoryBars: document.querySelector("#category-bars"),
  folderList: document.querySelector("#folder-list"),
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
}

function renderSummary(data) {
  const audit = data.audit;
  elements.metricTotal.textContent = audit.summary.total_human;
  elements.metricFiles.textContent = String(audit.summary.file_count);
  elements.metricReducible.textContent = data.estimated_reducible_human;
  elements.metricDuplicates.textContent = audit.opportunities.duplicate_human;
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
      const disabled = supported ? "" : "disabled";
      const statusClass = supported ? "status-pill" : "status-pill unsupported";
      const statusText = supported ? "Reducible" : "Not supported";
      const expected = supported
        ? `${file.reduction.estimated_saved_human} (${file.reduction.estimated_reduction_percent}%)`
        : "-";
      return `
        <tr>
          <td class="select-cell">
            <input type="checkbox" data-file-id="${escapeHtml(file.id)}" ${checked} ${disabled} aria-label="Select ${escapeHtml(file.name)}">
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
  elements.selectionSummary.textContent = selectedFiles.length
    ? `${selectedFiles.length} selected, approximately ${formatBytes(estimatedBytes)} reducible`
    : "Select reducible files after scanning.";
  elements.reduceButton.disabled = selectedFiles.length === 0;
}

async function scan(event) {
  event.preventDefault();
  const path = elements.pathInput.value.trim();
  if (!path) {
    setStatus("Enter a folder path to scan.", "error");
    return;
  }

  setStatus("Scanning files and estimating reductions...");
  elements.form.querySelector("button").disabled = true;
  try {
    const data = await postJson("/api/scan", {
      path,
      quality: Number(elements.qualityInput.value),
      ...resolution(),
    });
    state.rootPath = data.root_path;
    state.files = data.files;
    state.filteredFiles = [...data.files];
    state.selected.clear();
    state.audit = data.audit;
    renderSummary(data);
    renderCategories(data.audit);
    renderFolders(data.audit);
    renderFiles();
    setStatus(`Scan complete. ${data.files.length} files analyzed.`);
  } catch (error) {
    setStatus(error.message, "error");
  } finally {
    elements.form.querySelector("button").disabled = false;
  }
}

async function reduceSelected() {
  const fileIds = [...state.selected];
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

elements.form.addEventListener("submit", scan);
elements.qualityInput.addEventListener("input", () => {
  elements.qualityOutput.value = elements.qualityInput.value;
  elements.qualityOutput.textContent = elements.qualityInput.value;
});
elements.filterInput.addEventListener("input", filterFiles);
elements.reduceButton.addEventListener("click", reduceSelected);
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
