# Release Process

CloudSaver publishes GitHub Releases from version tags.

## Versioning

Use semantic versioning:

- Patch: bug fixes and documentation-only release improvements
- Minor: new user-facing features
- Major: breaking CLI, data format, or workflow changes

## Manual Release Checklist

1. Update `CHANGELOG.md`.
2. Update `pyproject.toml` version.
3. Run tests:

   ```bash
   python3 -m pytest
   ```

4. Build locally:

   ```bash
   python3 -m pip install --upgrade build
   python3 -m build
   ```

5. Create and push a version tag:

   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

The `Release` GitHub Actions workflow builds source and wheel distributions, creates
`SHA256SUMS`, and publishes the GitHub Release.

## Desktop Builds

The `Desktop Builds` workflow uses PyInstaller to build one-file binaries for Windows,
macOS, and Linux. These artifacts are unsigned until platform signing credentials are
configured.

Run it manually from GitHub Actions or by pushing a version tag.

## Package Manager Templates

Package templates live in `packaging/`. After a release is published, replace `VERSION`,
`URL`, and `SHA256` placeholders with final artifact metadata and submit them to the
appropriate registries.

Signing and notarization requirements are documented in `packaging/SIGNING.md`.
