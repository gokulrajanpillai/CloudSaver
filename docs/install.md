# Install CloudSaver

CloudSaver can be used from source today. Signed convenience builds are planned after
release signing credentials are configured.

## From Source

```bash
python3 -m pip install -r requirements.txt
python3 -m cloudsaver.web_server
```

Open `http://127.0.0.1:8765`.

## Package Entry Points

After installing CloudSaver as a package:

```bash
cloudsaver-web
cloudsaver-desktop
cloudsaver
```

## GitHub Releases

Release artifacts should include:

- Source distribution
- Wheel distribution
- Desktop build artifacts when available
- SHA-256 checksums
- Release notes

## Platform Notes

### macOS

Use the GitHub release artifact or package-manager template. Signed and notarized builds are
planned but require Apple Developer credentials.

### Windows

Use the GitHub release artifact or package-manager template. Signed builds are planned but
require a code-signing certificate.

### Linux

Use source installation, AppImage-style artifacts when available, or the Flatpak template.
