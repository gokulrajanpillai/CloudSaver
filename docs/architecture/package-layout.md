# Package Layout

CloudSaver now uses a real `cloudsaver` Python package for product code.

## Runtime Modules

- `cloudsaver.core`: scan engine, audits, duplicate verification, reduction, quarantine
- `cloudsaver.history`: local SQLite scan history
- `cloudsaver.web_server`: local web app and API
- `cloudsaver.desktop`: desktop-style launcher

## Compatibility Modules

The previous `src.cloudsaver*` modules remain as thin wrappers so older commands and imports
keep working while documentation and package entry points move to `cloudsaver.*`.

## Future Split

As the app grows, `cloudsaver.core` should be split into smaller modules:

- `scan.py`
- `audit.py`
- `duplicates.py`
- `media.py`
- `quarantine.py`
- `reports.py`
