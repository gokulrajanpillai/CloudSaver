from pathlib import Path


MARKETING_ROOT = Path(__file__).resolve().parent.parent / "marketing"


def test_landing_page_contains_required_sections():
    html = (MARKETING_ROOT / "index.html").read_text()

    assert "Clean up storage without uploading private files." in html
    assert 'id="how"' in html
    assert 'id="features"' in html
    assert 'id="pricing"' in html
    assert "application/ld+json" in html
    assert "Storage pressure estimator" in html
    assert "Source Preview" in html
    assert "cloud accounts" not in html
    assert "cloud scanning" not in html


def test_capture_page_uses_formspree_endpoint():
    html = (MARKETING_ROOT / "capture.html").read_text()

    assert 'method="POST"' in html
    assert "formspree.io" in html
    assert 'name="source"' in html


def test_calculator_has_non_zero_formula():
    js = (MARKETING_ROOT / "script.js").read_text()

    assert "function calculateOverspend" in js
    assert "Math.max(monthly * serviceMultiplier * recoverableRate, 0.01)" in js
    assert "CloudSaver Pro pays for itself" not in js
