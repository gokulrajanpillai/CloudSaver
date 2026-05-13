from __future__ import annotations

"""
CloudSaver AI Savings Advisor - powered by Claude.

Privacy guarantee: No file names, no paths, no folder names are sent to the API.
Only statistical summaries (sizes, counts, categories, patterns) are transmitted.
"""

import json
import os
from typing import Generator

try:
    import anthropic

    ADVISOR_AVAILABLE = True
except ImportError:  # pragma: no cover - package is optional in default installs
    anthropic = None
    ADVISOR_AVAILABLE = False

MODEL = "claude-opus-4-7"
MAX_TOKENS = 1024

SYSTEM_PROMPT = """You are CloudSaver AI, a storage optimization expert built into the
CloudSaver desktop app. You analyze anonymous storage audit data and provide actionable,
specific, friendly recommendations.

CRITICAL PRIVACY RULES - you will receive only:
- File counts, sizes, categories (image/video/audio/document/archive/other)
- Detected patterns (duplicate counts, codec names, temperature distribution)
- No file names, no folder names, no paths, no personal information

Your recommendations must:
1. Be specific and actionable
2. Explain WHY in one sentence
3. Give a dollar-value saving when cloud storage cost is involved
4. Rank by impact
5. Be conversational and encouraging, not alarming
6. Be under 300 words total
7. Use plain language

Format your response as JSON matching this schema:
{
  "headline": "str",
  "total_opportunity_human": "str",
  "recommendations": [
    {
      "rank": 1,
      "title": "str",
      "impact_human": "str",
      "cost_saving_human": "str | null",
      "explanation": "str",
      "action": "str",
      "confidence": "high | medium | low"
    }
  ],
  "growth_warning": "str | null",
  "encouragement": "str"
}"""


def build_audit_summary_for_ai(audit: dict, files: list[dict], history: list[dict]) -> dict:
    """
    Build a privacy-safe summary of scan results for the AI prompt.
    MUST NOT include any file names, paths, or personally identifying information.
    """

    opportunities = audit.get("opportunities", {})
    by_category = audit.get("by_category", {})

    codec_counts = {}
    for file in files:
        probe = file.get("media_probe") or {}
        video = file.get("video_estimate") or {}
        audio = file.get("audio_estimate") or {}
        codec = probe.get("codec_name") or video.get("codec_name") or audio.get("codec_name")
        if codec:
            codec_counts[codec] = codec_counts.get(codec, 0) + 1

    temp_counts = {"hot": 0, "warm": 0, "cold": 0, "frozen": 0}
    for file in files:
        temp = file.get("temperature", "warm")
        temp_counts[temp] = temp_counts.get(temp, 0) + 1

    growth_gb_per_month = None
    if len(history) >= 2:
        oldest = history[-1]
        newest = history[0]
        months = max((newest["scanned_at"] - oldest["scanned_at"]) / (30 * 24 * 3600), 0.1)
        growth_bytes = newest["total_bytes"] - oldest["total_bytes"]
        growth_gb_per_month = round(growth_bytes / (1024**3) / months, 2)

    return {
        "scan_summary": {
            "total_bytes": audit["summary"]["total_bytes"],
            "total_human": audit["summary"]["total_human"],
            "file_count": audit["summary"]["file_count"],
        },
        "by_category": {
            category: {"count": values["count"], "bytes": values["bytes"]}
            for category, values in by_category.items()
        },
        "opportunities": {
            "duplicate_count": opportunities.get("duplicate_count", 0),
            "duplicate_bytes": opportunities.get("duplicate_bytes", 0),
            "image_optimization_bytes": opportunities.get("image_optimization_bytes", 0),
            "video_optimization_bytes": opportunities.get("video_optimization_bytes", 0),
            "audio_optimization_bytes": opportunities.get("audio_optimization_bytes", 0),
            "cold_folder_bytes": opportunities.get("cold_folder_bytes", 0),
            "estimated_recoverable_bytes": opportunities.get("estimated_recoverable_bytes", 0),
            "estimated_monthly_cost_avoided_usd": opportunities.get(
                "estimated_monthly_cost_avoided_usd", 0
            ),
        },
        "codec_distribution": codec_counts,
        "temperature_distribution": temp_counts,
        "growth_gb_per_month": growth_gb_per_month,
        "large_file_count": opportunities.get("large_file_count", 0),
        "perceptual_duplicate_groups": len(audit.get("perceptual_duplicates", [])),
    }


def get_recommendations(audit: dict, files: list[dict], history: list[dict]) -> dict:
    """Calls Claude API and returns parsed recommendations dict."""

    if not ADVISOR_AVAILABLE:
        raise RuntimeError("anthropic package not installed")

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic(api_key=api_key)
    summary = build_audit_summary_for_ai(audit, files, history)
    message = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": "Analyze this storage audit and provide recommendations:\n\n"
                + json.dumps(summary, indent=2),
            }
        ],
    )

    text = message.content[0].text
    if "```json" in text:
        text = text.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in text:
        text = text.split("```", 1)[1].split("```", 1)[0].strip()
    return json.loads(text)


def stream_recommendations(
    audit: dict,
    files: list[dict],
    history: list[dict],
) -> Generator[str, None, None]:
    """Streaming version - yields SSE-formatted chunks for real-time display."""

    if not ADVISOR_AVAILABLE:
        yield 'data: {"error": "anthropic not installed"}\n\n'
        return
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        yield 'data: {"error": "ANTHROPIC_API_KEY not set"}\n\n'
        return

    client = anthropic.Anthropic(api_key=api_key)
    summary = build_audit_summary_for_ai(audit, files, history)
    with client.messages.stream(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": "Analyze:\n\n" + json.dumps(summary)}],
    ) as stream:
        for text in stream.text_stream:
            yield f"data: {json.dumps({'chunk': text})}\n\n"
    yield 'data: {"done": true}\n\n'
