# Signing And Notarization

CloudSaver release artifacts are unsigned until project credentials are configured.

## macOS

Required:

- Apple Developer account
- Developer ID Application certificate
- Notarization credentials

Recommended release steps:

1. Build the macOS artifact in GitHub Actions.
2. Sign the application with `codesign`.
3. Notarize with `xcrun notarytool`.
4. Staple the notarization ticket.
5. Publish the signed artifact and checksum.

## Windows

Required:

- Code signing certificate
- Signing key storage, preferably hardware-backed or cloud KMS

Recommended release steps:

1. Build the Windows artifact in GitHub Actions.
2. Sign with `signtool`.
3. Verify signature.
4. Publish the signed artifact and checksum.

## Linux

Recommended:

- Publish SHA-256 checksums for AppImage/deb/rpm artifacts.
- Use Flatpak when possible for sandboxed distribution.
- Publish package manifests from release checksums.

## Secrets

Never commit signing keys, certificates, passwords, or notarization credentials. Store them
as GitHub Actions secrets or use a dedicated signing service.
