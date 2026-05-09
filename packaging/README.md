# Packaging

This directory contains package-manager templates for CloudSaver releases.

The templates are intentionally not submitted automatically. Publishing requires:

- A tagged GitHub Release
- Final release artifact URLs
- SHA-256 checksums from release artifacts
- Maintainer accounts for the target package registry
- Signing credentials where required

## Targets

- Homebrew: `packaging/homebrew/cloudsaver.rb.template`
- Winget: `packaging/winget/cloudsaver.yaml.template`
- Scoop: `packaging/scoop/cloudsaver.json.template`
- Flatpak: `packaging/flatpak/io.github.gokulrajanpillai.CloudSaver.yml.template`

Replace `VERSION`, `URL`, and `SHA256` placeholders during each release.

Paid convenience build policy is documented in `docs/paid-builds.md`.
