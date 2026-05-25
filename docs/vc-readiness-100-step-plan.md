# CloudSaver VC Readiness Review And 100-Step Product Plan

Date reviewed: 2026-05-29

## CEO Verdict

CloudSaver has a credible wedge: local-first storage intelligence for people and small
teams who do not trust hosted cleanup products with file names, paths, or content. The
repo already contains a meaningful Python scanning backend, a React/Tauri desktop shell,
demo data, duplicate review, reversible cleanup concepts, pricing/support docs, and a
privacy narrative.

The product is not yet VC-presentable as a working venture-scale product. It is closer to
a strong preview prototype with good raw material. The main investor risks are provider
integration gaps, mismatch between docs and shipped behavior, incomplete desktop
packaging assets, test suite health, and an unclear growth/commercial motion.

## Current Integration Check

- Google Drive: Remote API scanning exists in `src-python/api/gdrive.py`, OAuth exists in
  `src-python/api/auth.py`, and the UI can add a Google Drive account. However,
  `Sources.scanSource` currently requires `source.path` and always posts to
  `/scan/local/start`, so a Google Drive account source cannot be scanned from the React
  UI. Refresh-token storage also uses a state-derived key instead of a stable account key.
- iCloud Drive: Detection and local synced-folder scanning exist. iCloud-only file state
  annotation exists for macOS, but iCloud is not a true remote provider integration.
- Dropbox: Only the local `~/Dropbox` folder is detected. There is no Dropbox OAuth,
  metadata API scan, quota sync, Smart Sync state handling, or remote cleanup support.
- OneCloud or OneDrive: "OneCloud" is not the common consumer provider name; this plan
  treats the request as OneDrive. Only `~/OneDrive` local folder detection exists. There is
  no Microsoft Graph OAuth, quota sync, Files On-Demand state handling, or remote cleanup.
- Other popular providers: There is no S3, Box, Proton Drive, pCloud, Backblaze B2, SMB,
  WebDAV, Synology, or Google Photos integration.
- Provider parity: The data model has `local`, `gdrive_local`, `icloud`, and
  `google_drive`. It needs a provider abstraction before adding more serious connectors.

## Current UI, UX, Brand, And Packaging Check

- UI direction: The React app is utilitarian and fairly coherent: nav rail, source cards,
  overview metrics, duplicate review, cleanup, settings, command palette, and demo mode.
- UX gaps: First-run flow does not yet prove end-to-end trust for cloud accounts,
  provider limitations are not visible enough in-app, and failed scans/auth errors need
  clearer recovery steps.
- Icons: The React UI uses `lucide-react`, which is appropriate. The Tauri config points
  at `src-tauri/icons/*`, but that directory only contains `.gitkeep`, so desktop bundling
  is not ready.
- Splash screens: No app splash/loading screen was found for Tauri startup, sidecar boot,
  or long first scan setup.
- Fonts: The React app ships Inter via `@fontsource/inter`; the legacy web UI references
  Google-hosted DM Sans. For a privacy-first desktop product, remote font loading should
  be removed or made explicit.
- Visual identity: There is an SVG brand mark in the legacy web UI, but no complete
  production icon family, installer artwork, screenshots, or pitch-ready media kit.
- Test health: `python3 -m pytest` fails in this environment because `httpx` is missing.
  `npm run typecheck` fails in test files. `npm test` collects Playwright specs under
  Vitest and hits sandboxed localhost failures. This must be fixed before investor demos.

## 100-Step VC Readiness Plan

### Foundation And Trust

1. Add a public "what CloudSaver does and does not do" product contract in-app, matching
   README, privacy docs, and release notes so users and investors see one consistent
   promise.
2. Build a first-run onboarding flow that asks the user to choose local scan, synced cloud
   folder, or direct provider account and explains the privacy boundary for each path.
3. Add a trust center screen covering local processing, optional network paths, licenses,
   AI advisor data boundaries, update checks, and provider OAuth scopes.
4. Add a source capability matrix in the app showing scan, quota, duplicates, safe move,
   restore, and direct remote cleanup support per provider.
5. Add explicit "preview", "beta", and "production-ready" badges for incomplete features
   such as AI Advisor, Business workspace, and direct cloud connectors.
6. Add structured known-limitations copy to the UI for direct Google Drive, iCloud,
   Dropbox, OneDrive, and S3 behavior until each connector is production-grade.
7. Add privacy-safe telemetry settings that map directly to backend behavior and persist
   opt-out state rather than keeping local-only toggle state in React.
8. Add a diagnostics export bundle that redacts paths, emails, and filenames while keeping
   environment, provider, scan-stage, and error details for support.
9. Add consent prompts before any outbound request, including OAuth, update checks,
   payments, AI advisor, and team workspace actions.
10. Add a local encrypted credential inventory screen showing connected accounts, token
    status, last refresh, and disconnect/revoke actions.

### Provider Platform

11. Create a provider adapter interface for list, quota, file identity, duplicate identity,
    trash, restore, refresh token, and capability reporting.
12. Refactor local, iCloud, Google Drive local-sync, and Google Drive remote scan into
    adapter implementations behind one source scan API.
13. Add a provider job router so React can start scans without hardcoding local or Google
    Drive endpoint paths.
14. Add normalized provider file IDs that distinguish local paths, inode-like IDs, Drive
    IDs, Graph IDs, Dropbox IDs, and object-storage keys.
15. Add normalized provider state fields for cloud-only, available offline, downloading,
    pinned, shared, owner, modified, checksum, and remote trash status.
16. Add provider-level rate-limit handling with retries, backoff, progress messages, and
    user-visible retry-after guidance.
17. Add resumable provider scans with cursor/page-token persistence and a safe resume UI.
18. Add provider scan cancellation that stops local walking and remote pagination cleanly.
19. Add provider smoke tests using mocked APIs and golden fixtures for each provider.
20. Add integration test fixtures for cross-provider duplicate matching across local,
    iCloud, Google Drive, Dropbox, and OneDrive.

### Google Drive

21. Fix the React scan flow so `google_drive` sources call `/gdrive/scan/start` with a
    token and use the `/gdrive/scan/{job_id}/ws` websocket.
22. Store Google refresh tokens under a stable account key such as email or provider
    account ID, not transient OAuth state.
23. Add access-token refresh before scan, trash, and web-link actions.
24. Add Drive account reauthentication and graceful expired-token recovery.
25. Add Drive shared-drive support including `supportsAllDrives`,
    `includeItemsFromAllDrives`, corpora selection, and drive picker UX.
26. Add Drive folder-path reconstruction so results show readable paths instead of only
    file names.
27. Add Drive quota details, including usage by Drive, trash, shared drive, and account
    limit where available.
28. Add Drive duplicate confidence using `md5Checksum`, file size, MIME type, and modified
    time with clear handling for Google Docs files that lack binary checksums.
29. Add Drive remote trash preview and undo guidance before moving duplicates to trash.
30. Add a Google OAuth production checklist for verified app status, scopes, branding,
    consent screen, redirect URI, and restricted-scope review.

### iCloud

31. Add a dedicated iCloud source adapter that scans through local sync paths but reports
    iCloud-specific capabilities and limitations.
32. Improve iCloud state detection with documented macOS APIs or robust filesystem
    metadata checks instead of relying primarily on fragile `brctl` output.
33. Add clear handling for evicted iCloud-only files so users know whether a scan would
    trigger downloads or only inspect placeholders.
34. Add "download before scan" and "skip cloud-only files" choices for iCloud sources.
35. Add iCloud restore guidance for review-folder moves, including what happens when files
    are moved out of iCloud Drive.
36. Add Windows iCloud Drive detection beyond `~/iCloudDrive`, including common Apple
    Windows client locations.
37. Add iCloud Photos limitation messaging because iCloud Drive and iCloud Photos are
    different products.
38. Add iCloud source tests that simulate local, evicted, downloading, and permission
    denied states.
39. Add user-facing warnings for Photos Library bundles and package directories before
    duplicate review or cleanup.
40. Add a documented iCloud QA matrix for macOS versions, optimized storage settings, and
    Windows iCloud client versions.

### Dropbox

41. Add Dropbox local-sync detection for macOS, Windows, Linux, team folders, and custom
    Dropbox locations.
42. Add Dropbox OAuth and account connection with minimal metadata and file modification
    scopes.
43. Add Dropbox remote metadata scan with pagination, content hash support, and team space
    awareness.
44. Add Dropbox quota and plan data so cost/recoverable storage estimates reflect the
    connected account.
45. Add Dropbox Smart Sync or online-only state detection for local synced folders.
46. Add Dropbox safe trash workflow using the Dropbox API, with preview and recovery
    instructions.
47. Add Dropbox shared-folder ownership warnings so users do not remove files that belong
    to teammates unexpectedly.
48. Add Dropbox tests with mocked list-folder, continue, delete, and restore flows.
49. Add Dropbox capability labels distinguishing local synced scan and direct API scan.
50. Add Dropbox app-review and production OAuth checklist.

### OneDrive And Microsoft 365

51. Add Microsoft Graph OAuth for personal OneDrive, work OneDrive, and SharePoint-backed
    document libraries.
52. Add OneDrive local-sync detection for Windows, macOS, enterprise tenant folders, and
    custom sync roots.
53. Add Microsoft Graph metadata scanning with delta tokens for incremental scans.
54. Add OneDrive quota, storage used, deleted items, and plan metadata.
55. Add Files On-Demand state detection for local synced OneDrive folders.
56. Add OneDrive recycle-bin workflow with preview, restore guidance, and retention-window
    messaging.
57. Add tenant and shared-library labels so users know whether files are personal, team,
    or SharePoint-owned.
58. Add conflict and version-history awareness so duplicates and cleanup do not break
    collaborative documents.
59. Add OneDrive mocked API tests for personal, business, shared, and throttled accounts.
60. Add Microsoft app-registration, publisher verification, and Graph scope review
    checklist.

### Additional Providers And Enterprise Reach

61. Add S3-compatible bucket scanning for AWS S3, Cloudflare R2, Backblaze B2, Wasabi, and
    MinIO using read-only list/head permissions.
62. Add Box OAuth and metadata scanning for business storage teams.
63. Add SMB/NAS source profiles for Synology, QNAP, and generic network shares with
    permission and latency guidance.
64. Add WebDAV source support for self-hosted and privacy-conscious users.
65. Add Google Photos research and limitation documentation, then decide whether to build
    a separate connector or explicitly exclude it.
66. Add provider import/export profiles so support teams can preconfigure source types
    without storing user secrets in plaintext.
67. Add provider health checks that validate credentials, permissions, quota access, and
    cleanup capabilities before the first scan.
68. Add provider-specific cost models and plan selectors with editable assumptions.
69. Add multi-account support per provider with distinct avatars, emails, tenant names,
    and workspace labels.
70. Add a provider marketplace-style connector screen that communicates available,
    beta, planned, and unavailable connectors.

### Core Storage Intelligence

71. Add incremental scan history that detects new, changed, deleted, and moved files
    between scans.
72. Add storage growth forecasting with source-level trend lines and "days until full"
    projections.
73. Add cross-source duplicate matching that works across local, Google Drive, iCloud,
    Dropbox, and OneDrive with confidence explanations.
74. Add configurable keep rules such as newest, oldest, local copy, cloud copy, largest
    resolution, tagged favorite, or specific folder priority.
75. Add a "safe cleanup simulation" mode that shows exactly what would move, where it
    would go, and how to restore it.
76. Add bundle/package awareness for `.photoslibrary`, app bundles, project folders,
    Lightroom catalogs, Final Cut libraries, and node/vendor directories.
77. Add cold-file detection based on access time, modified time, scan history, and provider
    metadata.
78. Add large-folder drilldown with owner, category, duplicate, and growth overlays.
79. Add media-specific insights for RAW photos, videos, screenshots, screen recordings,
    exports, caches, archives, and downloaded installers.
80. Add report exports tailored for individuals, freelancers, agencies, and IT admins.

### Cleanup Safety

81. Add a universal review queue that supports local moves, provider trash, skipped files,
    failed moves, partial restore, and audit logs.
82. Add immutable cleanup manifests with checksums, provider file IDs, original metadata,
    and restore instructions.
83. Add restore testing that verifies every supported cleanup path can be reversed in an
    automated test fixture.
84. Add guarded-delete language throughout the app: the primary action should remain
    review/trash, not permanent deletion.
85. Add protected-path rules for cloud roots, system directories, app libraries, package
    directories, and team-owned folders.
86. Add permission-denied and locked-file handling that preserves scan progress and shows
    actionable next steps.
87. Add dry-run and approval gates for batch operations above a configurable file count or
    byte threshold.
88. Add cleanup batch signing or tamper detection so support can trust restore manifests.
89. Add user education for provider trash retention windows, shared files, and ownership.
90. Add post-cleanup verification that recalculates recovered space and updates provider
    quota after remote operations.

### VC Demo, UX, Brand, And Commercial Readiness

91. Add a polished desktop icon set for macOS, Windows, Linux, tray, installer, and
    marketing use, and wire it into Tauri.
92. Add a native splash/loading screen showing sidecar startup, provider health checks,
    and offline readiness.
93. Add a pitch-ready demo workspace with deterministic fixtures, seeded provider mocks,
    screenshots, and a one-command reset.
94. Add three investor demo scripts: consumer storage cleanup, freelancer media cleanup,
    and small-team shared-drive cleanup.
95. Add a visual design pass that standardizes spacing, type scale, dark mode contrast,
    empty states, provider icons, status badges, and error banners.
96. Add accessibility acceptance tests for keyboard navigation, focus order, reduced
    motion, color contrast, dialog behavior, and screen-reader labels.
97. Add packaging pipelines for signed macOS, Windows, and Linux preview builds with
    checksums and release provenance.
98. Add a quality gate where Python tests, TypeScript checks, Vitest unit tests,
    Playwright smoke tests, and release smoke all pass before demos.
99. Add pricing, pilot, and conversion instrumentation that measures activation,
    scan completion, duplicate review, cleanup, restore, report export, and repeat usage
    without exposing private file data.
100. Add a VC data room package with product screenshots, architecture diagram, privacy
     model, security model, roadmap, traction dashboard, competitive matrix, revenue
     experiments, and customer pilot evidence.

## Immediate Next Commits Recommended

1. Fix React Google Drive scan routing and websocket handling.
2. Add tests proving Google Drive account sources can start and complete mocked scans.
3. Fix TypeScript test compilation errors.
4. Exclude Playwright specs from Vitest or move them fully under Playwright config.
5. Add missing Python dev dependencies or document the supported test install command.
6. Add real Tauri app icons and verify desktop bundle config.
7. Replace remote font loading in the legacy web UI with local bundled fonts.
8. Add in-app provider capability matrix and limitation messaging.
9. Add stable credential-keying and refresh-token use for Google Drive.
10. Add provider abstraction skeleton before adding Dropbox and OneDrive.
