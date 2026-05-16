# Screenshots

CloudSaver needs product screenshots before the first public preview tag.

Required preview screenshots:

- First-run folder selection.
- Scan progress.
- Dashboard summary.
- Storage treemap.
- Duplicate review.
- Quarantine/review flow.
- Recent scan history.

Store screenshots under `docs/assets/` and reference them from `README.md`.

Suggested filenames:

- `docs/assets/first-run-scan.png`
- `docs/assets/scan-progress.png`
- `docs/assets/dashboard-summary.png`
- `docs/assets/storage-map.png`
- `docs/assets/duplicate-review.png`
- `docs/assets/review-restore.png`
- `docs/assets/history.png`

## Demo Script

Use a small throwaway folder, not a real private folder:

1. Start the web UI with `python3 -m cloudsaver.web_server`.
2. Open `http://127.0.0.1:8765`.
3. Choose the fixture folder.
4. Capture scan progress.
5. Capture the dashboard after scan completion.
6. Open duplicate review and capture the recommended keep copy.
7. Move one safe fixture file to review.
8. Restore it from the review queue.
9. Export JSON or CSV from the Files tab.

Do not capture private filenames, private paths, private email addresses, license keys, or
real customer data.
