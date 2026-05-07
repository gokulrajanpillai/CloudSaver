# Contributing

Thanks for helping improve CloudSaver.

## Project Scope

CloudSaver is a local-first, open-source storage audit and safe optimization tool. Good
contributions usually fit one of these areas:

- Local or mounted-folder scanning
- Storage audit accuracy
- Duplicate candidate review and verification
- Safe image optimization that preserves originals by default
- Exportable local reports
- Packaging, documentation, tests, and accessibility

Out of scope for now:

- Hosted accounts or SaaS dashboards
- Silent deletion or destructive cleanup
- Required telemetry
- Direct cloud-provider API integrations
- Features that upload file names, paths, or contents by default

## Development

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Run tests:

```bash
pytest
```

Run the local web UI:

```bash
python3 -m src.cloudsaver_web
```

Then open `http://127.0.0.1:8765`.

## Pull Requests

- Keep changes focused.
- Add or update tests for behavior changes.
- Avoid committing generated `output/` files, credentials, tokens, or private scan data.
- Document user-visible behavior in `README.md` when needed.
- Preserve the local-first privacy model.
