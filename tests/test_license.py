import json

from cloudsaver import license as license_module


def reset_license_state(monkeypatch, tmp_path):
    monkeypatch.setattr(license_module, "LICENSE_FILE", tmp_path / "license.json")
    monkeypatch.setattr(license_module, "_license_state", None)


def test_generate_validate_and_activate_license(monkeypatch, tmp_path):
    reset_license_state(monkeypatch, tmp_path)

    key = license_module.generate_license_key("PRO", "202612")
    valid, tier, expiry = license_module.validate_key(key)

    assert valid is True
    assert tier == "PRO"
    assert expiry == "202612"

    state = license_module.activate_license(key, "buyer@example.com")

    assert state.tier == "PRO"
    assert state.valid is True
    assert state.expired is False
    assert state.expires_at == "2026-12"
    assert state.email == "buyer@example.com"
    assert license_module.is_pro(state) is True
    assert license_module.LICENSE_FILE.exists()


def test_expired_license_does_not_grant_pro(monkeypatch, tmp_path):
    reset_license_state(monkeypatch, tmp_path)

    key = license_module.generate_license_key("PRO", "200001")
    state = license_module.activate_license(key)

    assert state.expired is True
    assert state.valid is False
    assert license_module.is_pro(state) is False


def test_tampered_license_checksum_fails(monkeypatch, tmp_path):
    reset_license_state(monkeypatch, tmp_path)

    key = license_module.generate_license_key("BIZ", "202612")
    tampered = key[:-1] + ("A" if key[-1] != "A" else "B")

    valid, tier, expiry = license_module.validate_key(tampered)

    assert valid is False
    assert tier == "BIZ"
    assert expiry == "202612"


def test_load_license_returns_free_for_invalid_file(monkeypatch, tmp_path):
    reset_license_state(monkeypatch, tmp_path)
    license_module.LICENSE_FILE.write_text(json.dumps({"raw_key": "CS-PRO-202612-INVALID-BAD"}))

    state = license_module.load_license()

    assert state.tier == "FREE"
    assert state.valid is False
    assert license_module.is_pro(state) is False
