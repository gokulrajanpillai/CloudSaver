from __future__ import annotations

import argparse
import os
import tarfile
import zipfile
from pathlib import Path


def add_to_zip(archive: zipfile.ZipFile, source: Path, archive_root: Path) -> None:
    if source.is_dir():
        for path in source.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(archive_root))
        return
    archive.write(source, source.relative_to(archive_root))


def add_to_tar(archive: tarfile.TarFile, source: Path, archive_root: Path) -> None:
    archive.add(source, arcname=source.relative_to(archive_root))


def find_desktop_payload(dist_dir: Path) -> Path:
    candidates = [
        dist_dir / "CloudSaver.app",
        dist_dir / "CloudSaver.exe",
        dist_dir / "CloudSaver",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"CloudSaver desktop payload was not found in {dist_dir}")


def package_artifact(platform: str, version: str, dist_dir: Path, release_dir: Path) -> Path:
    payload = find_desktop_payload(dist_dir)
    release_dir.mkdir(parents=True, exist_ok=True)
    archive_base = release_dir / f"CloudSaver-{version}-{platform}"

    if platform.startswith("windows"):
        archive_path = archive_base.with_suffix(".zip")
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
            add_to_zip(archive, payload, dist_dir)
        return archive_path

    archive_path = Path(f"{archive_base}.tar.gz")
    with tarfile.open(archive_path, "w:gz") as archive:
        add_to_tar(archive, payload, dist_dir)
    return archive_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Package a CloudSaver desktop build artifact.")
    parser.add_argument("--platform", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--dist-dir", default="dist")
    parser.add_argument("--release-dir", default="release")
    args = parser.parse_args()

    artifact = package_artifact(
        platform=args.platform,
        version=args.version,
        dist_dir=Path(args.dist_dir),
        release_dir=Path(args.release_dir),
    )
    print(os.fspath(artifact))


if __name__ == "__main__":
    main()
