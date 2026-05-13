from cloudsaver import payments
from cloudsaver.history import (
    get_license_delivery,
    mark_license_delivery_activated,
    save_license_delivery,
)


def test_compute_expiry_yyyymm_format():
    expiry = payments.compute_expiry_yyyymm(12)

    assert len(expiry) == 6
    assert expiry.isdigit()


def test_handle_webhook_generates_license(monkeypatch):
    class FakeWebhook:
        @staticmethod
        def construct_event(payload, signature, secret):
            assert payload == b"{}"
            assert signature == "sig"
            assert secret == "whsec_test"
            return {
                "type": "checkout.session.completed",
                "data": {
                    "object": {
                        "id": "cs_test_123",
                        "customer_email": "buyer@example.com",
                        "metadata": {"price_id": "price_pro"},
                    }
                },
            }

    class FakeStripe:
        Webhook = FakeWebhook

    monkeypatch.setattr(payments, "STRIPE_AVAILABLE", True)
    monkeypatch.setattr(payments, "WEBHOOK_SECRET", "whsec_test")
    monkeypatch.setattr(payments, "stripe", FakeStripe)

    delivery = payments.handle_webhook(b"{}", "sig")

    assert delivery["session_id"] == "cs_test_123"
    assert delivery["tier"] == "PRO"
    assert delivery["customer_email"] == "buyer@example.com"
    assert delivery["license_key"].startswith("CS-PRO-")


def test_handle_webhook_ignores_non_actionable_event(monkeypatch):
    class FakeWebhook:
        @staticmethod
        def construct_event(payload, signature, secret):
            return {"type": "customer.created", "data": {"object": {}}}

    class FakeStripe:
        Webhook = FakeWebhook

    monkeypatch.setattr(payments, "STRIPE_AVAILABLE", True)
    monkeypatch.setattr(payments, "WEBHOOK_SECRET", "whsec_test")
    monkeypatch.setattr(payments, "stripe", FakeStripe)

    assert payments.handle_webhook(b"{}", "sig") is None


def test_license_delivery_storage_round_trip(tmp_path):
    delivery = {
        "session_id": "cs_test_123",
        "license_key": "CS-PRO-202612-ABCDEFGH-ABCDE",
        "tier": "PRO",
        "expiry_yyyymm": "202612",
        "customer_email": "buyer@example.com",
    }

    save_license_delivery(delivery, tmp_path / "history.sqlite3")
    stored = get_license_delivery("cs_test_123", tmp_path / "history.sqlite3")

    assert stored["license_key"] == delivery["license_key"]
    assert stored["customer_email"] == "buyer@example.com"
    assert stored["activated_at"] is None

    mark_license_delivery_activated("cs_test_123", tmp_path / "history.sqlite3")
    assert get_license_delivery("cs_test_123", tmp_path / "history.sqlite3")["activated_at"] is not None
