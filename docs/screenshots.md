# Screenshots

CloudSaver needs current product screenshots in `docs/assets/` before tagging a release.

## Quick Start

Run the fixture script to create a ~1 GB demo folder with images, documents, archives,
videos, and duplicate groups:

```bash
python3 scripts/create-demo-fixture.py
```

The script prints the fixture folder path and exact screenshot steps. Use a throwaway
fixture — never capture private paths, real filenames, email addresses, or license keys.

## Required Files

| Filename | What to capture |
| --- | --- |
| `docs/assets/first-run-scan.png` | Sidebar scan controls before any scan |
| `docs/assets/scan-progress.png` | Sidebar while a scan is running |
| `docs/assets/dashboard-summary.png` | Recommended tab after scan completes |
| `docs/assets/storage-map.png` | Map tab showing the storage treemap |
| `docs/assets/duplicate-review.png` | Duplicates tab with recommended keep copies |
| `docs/assets/review-restore.png` | Review tab with restore manifest visible |
| `docs/assets/history.png` | Scan history list |

## Step-by-Step

1. Run the fixture script and note the fixture folder path.
2. Start the web UI: `python3 -m cloudsaver.web_server`
3. Open `http://127.0.0.1:8765`.
4. **Capture `first-run-scan.png`** — sidebar visible, no scan started.
5. Paste the fixture folder path and click **Start scan**.
6. **Capture `scan-progress.png`** — scan is running (files counted, progress bar).
7. Wait for the scan to finish.
8. **Capture `dashboard-summary.png`** — Recommended tab with storage totals and cleanup cards.
9. Click the **Map** tab. **Capture `storage-map.png`** — treemap showing folder sizes.
10. Click the **Duplicates** tab. **Capture `duplicate-review.png`** — duplicate groups with keep recommendations.
11. Select one duplicate group and click **Move to review**.
12. Click the **Review** tab. **Capture `review-restore.png`** — restore manifest with batch visible.
13. Click **History** in the sidebar. **Capture `history.png`** — list of recent scans.

## Window Size

Use a 1280×800 or 1440×900 browser window for consistent framing across screenshots.
Browser dev tools can force a fixed viewport size.

## After Capturing

Reference the screenshots from `README.md`:

```markdown
![Dashboard](docs/assets/dashboard-summary.png)
![Duplicate review](docs/assets/duplicate-review.png)
![Storage map](docs/assets/storage-map.png)
```

Delete the fixture folder when done:

```bash
rm -rf /tmp/cloudsaver-demo
```
