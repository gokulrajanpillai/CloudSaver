# Business Storage Audit Report Template

Use this structure for small-business or professional storage reviews.

CloudSaver can generate this style of redacted Markdown report with
`cloudsaver.core.generate_business_report`. Paths are redacted by default so reports can be
shared with managers or clients without exposing full local folder names.

## Executive Summary

- Scan root:
- Scan date:
- Total storage scanned:
- Estimated recoverable storage:
- Estimated monthly storage cost avoided:
- High-confidence duplicate storage:
- Media optimization opportunity:

## Storage Distribution

- Largest folders:
- Largest file categories:
- Largest individual files:

## Cleanup Plan

| Priority | Opportunity | Confidence | Action |
| --- | --- | --- | --- |
| Low risk | Verified duplicates | High | Move extra copies to review |
| Medium risk | Large stale files | Medium | Confirm owner before moving |
| Optional | Image optimization | Medium | Create reduced copies |

## Risks And Notes

- Skipped or unreadable paths:
- Protected folders:
- Files requiring human review:

## Recommended Follow-Up

- Review quarantine manifest.
- Restore any false positives.
- Re-run scan after cleanup.
- Archive or delete reviewed files only after approval.
