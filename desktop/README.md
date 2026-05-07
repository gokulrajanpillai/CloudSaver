# Desktop Shell

CloudSaver currently ships a lightweight desktop launcher:

```bash
cloudsaver-desktop
```

The launcher starts the local CloudSaver web app on an available localhost port and opens
the user's default browser. This keeps the app local-first while giving non-technical users
a one-command entry point.

## Future Native Shell

A full native shell can be added after the dashboard stabilizes. The recommended path is:

1. Keep the Python scanner and web server as the local backend.
2. Add a Tauri or Electron wrapper for native menus, folder picker, app icon, and updates.
3. Reuse the existing `web/` app as the renderer.
4. Package signed installers from GitHub Actions once signing credentials exist.
