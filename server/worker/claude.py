from __future__ import annotations
"""Task 13: Claude API client for video frame analysis and report generation."""
import base64
import json
import re
from typing import Any, Optional

import anthropic

from server.config import settings

_client: Optional[anthropic.Anthropic] = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.claude_api_key)
    return _client


def _encode_image(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


CONTENT_DETECTION_PROMPT = """You are an experienced tennis coach. Examine these video keyframes and determine which technical modules are covered.

For each module:
- forehand: frames showing forehand stroke posture
- backhand: frames showing backhand stroke posture
- serve: frames showing serve motion
- volley: frames showing net volley posture
- footwork: observable player movement and positioning (almost always present)
- return: frames showing return of serve posture

Output ONLY a JSON object:
{
  "covered_modules": ["forehand", "serve", "footwork"],
  "module_confidence": {"forehand": 0.9, "backhand": 0.0, "serve": 0.8, "volley": 0.0, "footwork": 0.7, "return": 0.0},
  "summary": "This video mainly contains serve and forehand practice."
}"""

ANALYSIS_SYSTEM_PROMPT = """You are an experienced NTRP-certified tennis coach with 20 years of teaching experience.
Analyze these tennis video keyframes and assess the player's technical performance.

Evaluate:
1. Shot type identification (forehand/backhand/serve/volley)
2. Stroke quality (rotation/backswing/follow-through/contact point)
3. Footwork and positioning (open/closed stance, recovery)
4. Common technical issues (e.g. running around backhand, late contact)
5. Comparison to NTRP standards

Be honest — if a frame is unclear, say so. Output in JSON format."""


def detect_video_modules(frame_paths: list[str]) -> dict[str, Any]:
    client = get_client()
    sample_size = min(12, len(frame_paths))
    step = max(1, len(frame_paths) // sample_size)
    sampled = frame_paths[::step][:sample_size]

    content: list[dict[str, Any]] = [{"type": "text", "text": f"Sampled {len(sampled)} keyframes. Determine which technical modules are covered."}]
    for path in sampled:
        content.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": _encode_image(path)}})

    response = client.messages.create(model=settings.claude_model, max_tokens=512, system=CONTENT_DETECTION_PROMPT, messages=[{"role": "user", "content": content}])
    text = response.content[0].text
    json_match = re.search(r'\{[\s\S]*\}', text)
    return json.loads(json_match.group(0)) if json_match else {"covered_modules": [], "module_confidence": {}, "summary": ""}


def analyze_frames_batch(frame_paths: list[str], batch_index: int, total_batches: int) -> dict[str, Any]:
    client = get_client()
    content: list[dict[str, Any]] = [{"type": "text", "text": f"Batch {batch_index + 1}/{total_batches}, {len(frame_paths)} keyframes. Analyze the player's technical performance."}]
    for path in frame_paths:
        content.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": _encode_image(path)}})
    response = client.messages.create(model=settings.claude_model, max_tokens=4096, system=ANALYSIS_SYSTEM_PROMPT, messages=[{"role": "user", "content": content}])
    return {"batch": batch_index, "raw_response": response.content[0].text}


def generate_watch_section(oppo_stats: dict[str, Any], fitness_data: dict[str, Any]) -> str:
    if not oppo_stats:
        return """NOTE: No watch data uploaded. The following are unavailable:
- Shot statistics (from OPPO tennis mode): unavailable — estimate from video frames
- Swing speed: unavailable
- Heart rate / distance / calories: unavailable
- **Fitness scores: mark as "no watch data, unable to assess", set scores to null**"""

    return "\n".join([
        f"- Total shots: {oppo_stats.get('total_shots', 'N/A')}",
        f"- Serves: {oppo_stats.get('serve_count', 'N/A')}",
        f"- FH topspin: {oppo_stats.get('forehand_topspin', 'N/A')} | FH slice: {oppo_stats.get('forehand_slice', 'N/A')}",
        f"- BH topspin: {oppo_stats.get('backhand_topspin', 'N/A')} | BH slice: {oppo_stats.get('backhand_slice', 'N/A')}",
        f"- Avg swing speed: {oppo_stats.get('avg_swing_speed', 'N/A')}",
        "",
        "## Fitness Data (from watch)",
        f"- Avg HR: {fitness_data.get('cardiovascular_endurance', {}).get('avg_hr', 'N/A')} bpm",
        f"- Total distance: {fitness_data.get('movement', {}).get('total_distance_m', 'N/A')} m",
        f"- Distance/min: {fitness_data.get('movement', {}).get('distance_per_min', 'N/A')} m/min",
        f"- Total calories: {fitness_data.get('training_load', {}).get('total_calories', 'N/A')} kcal",
    ])


def generate_final_report(
    frame_analyses: list[dict[str, Any]],
    oppo_stats: dict[str, Any],
    fitness_data: dict[str, Any],
    rag_context: str,
    user_profile: dict[str, Any],
    covered_modules: list[str],
) -> dict[str, Any]:
    all_modules = ["forehand", "backhand", "serve", "volley", "footwork", "return"]
    uncovered = [m for m in all_modules if m not in covered_modules]
    covered_str = ", ".join(covered_modules)
    uncovered_str = ", ".join(uncovered) if uncovered else "none"

    client = get_client()
    prompt = f"""Generate a complete NTRP tennis assessment report.

## Video Content Coverage
- Detected modules: {covered_str}
- Undetected modules: {uncovered_str}
- **IMPORTANT**: Only score detected modules. Mark undetected modules as "insufficient_data" with null scores.

## Player Info
- Birth year: {user_profile.get('birth_year', 'unknown')}
- Years playing: {user_profile.get('playing_years', 'unknown')}
- Self-rated: NTRP {user_profile.get('self_rated_ntrp', 'unknown')}
- Target: NTRP {user_profile.get('target_ntrp', 'unknown')}

## OPPO Watch Data
{generate_watch_section(oppo_stats, fitness_data)}

## Frame Analysis Summary
{chr(10).join([f'- Batch {a["batch"] + 1}: {a["raw_response"][:300]}...' for a in frame_analyses])}

## NTRP Teaching Reference
{rag_context}

## Output Format
Output two parts separated by `---JSON---`:

Part 1: Complete Markdown report with:
1. Overall NTRP rating (with confidence; if >=3 modules missing, skip composite NTRP)
2. Technique scores (only for detected modules, 0-100 + rationale)
3. Fitness scores (only if watch data available)
4. Strengths & weaknesses (only from available modules)
5. 4-week training plan (2 sessions/week, focused on detected weaknesses)

Part 2 (after `---JSON---`): JSON object:
```json
{{
  "overall_ntrp": 3.0,
  "ntrp_confidence": 0.7,
  "technique_breakdown": {{
    "forehand": {{"score": 72, "status": "ok", "depth_control": 70}},
    "backhand": {{"score": null, "status": "insufficient_data", "note": "not detected"}},
    "serve": {{"score": 65, "status": "ok"}},
    "volley": {{"score": null, "status": "insufficient_data"}},
    "footwork": {{"score": 60, "status": "ok"}},
    "return": {{"score": null, "status": "insufficient_data"}}
  }},
  "strengths": ["Forehand consistency"],
  "weaknesses": ["Serve placement"],
  "uncovered_modules": ["backhand", "volley", "return"],
  "key_frames": []
}}
```

Base all recommendations on NTRP teaching guidelines. Use quantitative benchmarks where available."""

    response = client.messages.create(model=settings.claude_model, max_tokens=8192, messages=[{"role": "user", "content": prompt}])
    full_text = response.content[0].text

    if "---JSON---" in full_text:
        parts = full_text.split("---JSON---", 1)
        report_md = parts[0].strip()
        json_str = parts[1].strip()
        json_match = re.search(r'\{[\s\S]*\}', json_str)
        structured = json.loads(json_match.group(0)) if json_match else {}
    else:
        report_md = full_text
        structured = {}

    return {"report_markdown": report_md, "structured": structured}


SCREENSHOT_PROMPT = """You are a data extraction assistant. This is a screenshot from an OPPO Watch tennis mode summary.
Extract ALL numeric values you can find. Look for Chinese labels like:
总击球数 (total shots), 发球 (serves), 正手上旋 (forehand topspin), 正手削球 (forehand slice),
反手上旋 (backhand topspin), 反手削球 (backhand slice), 挥拍速度 (swing speed),
心率 (heart rate), 跑动距离 (distance), 卡路里 (calories).

Output ONLY a JSON object with these fields (use null for any you cannot find):
{
  "total_shots": 300,
  "serve_count": 60,
  "forehand_topspin": 120,
  "forehand_slice": 30,
  "backhand_topspin": 60,
  "backhand_slice": 30,
  "avg_swing_speed": 45.5,
  "avg_heart_rate": 135,
  "max_heart_rate": 172,
  "total_distance": 1500,
  "total_calories": 480
}

Do not include any text outside the JSON."""


def extract_screenshot_stats(screenshot_path: str) -> dict[str, Any]:
    """Extract tennis statistics from an OPPO Watch screenshot."""
    client = get_client()
    content: list[dict[str, Any]] = [
        {"type": "text", "text": "Extract all tennis statistics from this OPPO Watch screenshot."},
        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": _encode_image(screenshot_path)}},
    ]
    response = client.messages.create(
        model=settings.claude_model, max_tokens=512,
        system=SCREENSHOT_PROMPT, messages=[{"role": "user", "content": content}],
    )
    text = response.content[0].text
    json_match = re.search(r'\{[\s\S]*\}', text)
    return json.loads(json_match.group(0)) if json_match else {}
