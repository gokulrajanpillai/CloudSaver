# Desktop Shell

CloudSaver ships a desktop shell that reuses the same local web UI as the browser app:

```bash
cloudsaver-desktop
```

The desktop entry point starts the local CloudSaver backend on an available localhost port
and opens the UI in an embedded desktop window when `pywebview` is installed. If the
embedded shell is unavailable, it falls back to the user's default browser.

This keeps the scanner local-first while giving Windows, macOS, and Linux users a packaged
desktop app that shares the same UI, API, scan history, duplicate review, cleanup, and
restore behavior as the web app.

## Local Development

Install desktop dependencies:

```bash
python3 -m pip install -e ".[desktop]"
```

Run the embedded desktop shell:

```bash
cloudsaver-desktop
```

Run the browser fallback explicitly:

```bash
cloudsaver-desktop --browser
```

## Release Packages

The `Desktop Builds` GitHub Actions workflow builds PyInstaller desktop artifacts for:

- `linux-x64`
- `macos`
- `windows-x64`

On version tags, the workflow uploads packaged desktop archives to the matching GitHub
Release. The artifacts are unsigned until platform signing credentials are configured.
