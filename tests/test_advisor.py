import json

from cloudsaver import advisor


def sample_audit():
    return {
        "summary": {
            "total_bytes": 10 * 1024**3,
            "total_human": "10.00 GB",
            "file_count": 3,
        },
        "by_category": {
            "image": {"count": 2, "bytes": 2 * 1024**3},
            "video": {"count": 1, "bytes": 8 * 1024**3},
        },
        "opportunities": {
            "duplicate_count": 1,
            "duplicate_bytes": 1024,
            "image_optimization_bytes": 2048,
            "video_optimization_bytes": 4096,
            "audio_optimization_bytes": 0,
            "estimated_recoverable_bytes": 6144,
            "estimated_monthly_cost_avoided_usd": 0.25,
            "large_file_count": 1,
        },
    }


def test_build_audit_summary_for_ai_excludes_names_and_paths():
    files = [
        {
            "name": "private-photo.jpg",
            "path": "/Users/example/private-photo.jpg",
            "category": "image",
            "size_bytes": 1024,
            "media_probe": {"codec_name": "h264"},
        }
    ]

    summary = advisor.build_audit_summary_for_ai(sample_audit(), files, [])
    encoded = json.dumps(summary)

    assert "private-photo.jpg" not in encoded
    assert "/Users/example" not in encoded
    assert summary["codec_distribution"] == {"h264": 1}


def test_get_recommendations_parses_mocked_anthropic_response(monkeypatch):
    response_json = {
        "headline": "Recover video space first.",
        "total_opportunity_human": "6.0 GB recoverable",
        "recommendations": [
            {
                "rank": 1,
                "title": "Optimize videos",
                "impact_human": "4.0 GB",
                "cost_saving_human": "$0.10/month",
                "explanation": "Large videos dominate this scan.",
                "action": "Review video optimization options.",
                "confidence": "high",
            }
        ],
        "growth_warning": None,
        "encouragement": "A few focused actions will help.",
    }

    class FakeMessages:
        @staticmethod
        def create(**kwargs):
            class Message:
                content = [type("Content", (), {"text": "```json\n" + json.dumps(response_json) + "\n```"})]

            return Message()

    class FakeAnthropicClient:
        def __init__(self, api_key):
            self.messages = FakeMessages()

    class FakeAnthropicModule:
        Anthropic = FakeAnthropicClient

    monkeypatch.setattr(advisor, "ADVISOR_AVAILABLE", True)
    monkeypatch.setattr(advisor, "anthropic", FakeAnthropicModule)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    result = advisor.get_recommendations(sample_audit(), [], [])

    assert result["headline"] == "Recover video space first."
    assert result["recommendations"][0]["confidence"] == "high"
