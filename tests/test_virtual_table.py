from pathlib import Path


APP_JS = Path(__file__).resolve().parent.parent / "web" / "app.js"


def test_file_table_uses_incremental_rendering():
    js = APP_JS.read_text()

    assert "fileTablePageSize: 50" in js
    assert "IntersectionObserver" in js
    assert "file-table-sentinel" in js
    assert "Showing ${visibleFiles.length} of ${state.filteredFiles.length} files" in js
