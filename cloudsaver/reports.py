from cloudsaver import _core_impl as _impl
from cloudsaver._core_impl import (
    APP_DATA_DIR,
    OUTPUT_DIR,
    render_storage_audit_html,
    export_storage_audit_dashboard,
    generate_business_report,
    export_to_json_file,
    export_large_files,
    _render_metric,
    _render_file_rows,
    redacted_path_label,
)


def _sync_globals() -> None:
    _impl.OUTPUT_DIR = OUTPUT_DIR


def export_to_json_file(data, filename):
    _sync_globals()
    return _impl.export_to_json_file(data, filename)


def export_storage_audit_dashboard(files):
    _sync_globals()
    return _impl.export_storage_audit_dashboard(files)

__all__ = [
    'APP_DATA_DIR',
    'OUTPUT_DIR',
    'render_storage_audit_html',
    'export_storage_audit_dashboard',
    'generate_business_report',
    'export_to_json_file',
    'export_large_files',
    'redacted_path_label',
]
