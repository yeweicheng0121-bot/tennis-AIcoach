from __future__ import annotations
"""LLM client — Anthropic SDK (Claude via Qiniu proxy)."""
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
        _client = anthropic.Anthropic(api_key=settings.llm_api_key, base_url=settings.llm_base_url)
    return _client


def _encode_image(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _image_content(path: str) -> dict[str, Any]:
    """Anthropic image content block."""
    return {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": _encode_image(path)}}


def _chat(system: str, messages: list[dict], max_tokens: int = 512) -> str:
    """Single Anthropic message with system prompt."""
    client = get_client()
    resp = client.messages.create(
        model=settings.llm_model, max_tokens=max_tokens, system=system, messages=messages
    )
    return resp.content[0].text or ""


# ── Prompts ──────────────────────────────────────────────

CONTENT_DETECTION_PROMPT = """You are an experienced tennis coach. Examine these video keyframes and determine which technical modules are covered.

For each module:
- serve: player at baseline, self-tossing ball upward with non-dominant hand, racket raised overhead in trophy position. KEY: the player tosses the ball themselves — this is NOT a forehand. If you see a ball toss + overhead swing = SERVE.
- forehand: player reacting to incoming ball, racket prep at side/waist, body turned sideways
- backhand: same as forehand but on non-dominant side
- volley: player near net, short punch stroke, no full backswing
- footwork: player movement, split step, recovery positioning
- return: player receiving a serve, often in ready position at baseline

CRITICAL: serve vs forehand overhead — serve has a ball toss by the player. Forehand overhead has no toss. Do NOT confuse them.

Output ONLY a JSON object:
{
  "covered_modules": ["forehand", "serve", "footwork"],
  "module_confidence": {"forehand": 0.9, "backhand": 0.0, "serve": 0.8, "volley": 0.0, "footwork": 0.7, "return": 0.0},
  "summary": "This video mainly contains serve and forehand practice."
}"""

ANALYSIS_SYSTEM_PROMPT = """You are an experienced tennis coach. Your job is NOT to give scores — your job is to FIND PROBLEMS and suggest FIXES.

For each frame, identify:
1. What stroke is the player doing? (serve / forehand / backhand / volley)
2. What specific technical problems do you observe? Be precise. Examples:
   - "Toss is too low and too far left, causing contact point behind the head"
   - "No knee bend during trophy phase, losing power from legs"
   - "Follow-through stops at shoulder instead of crossing body to opposite hip"
   - "Contact point is too far back, elbow is bent instead of extended"
3. Why does this problem matter? (e.g. "low toss → rushed swing → inconsistent contact → double faults")
4. How to fix it? Give one specific drill. (e.g. "Stand at service line, practice toss WITHOUT hitting, aim for consistent height at 12 o'clock. 50 tosses per session.")

Do NOT describe what looks good. Focus on what needs improvement.
Do NOT give generic scores like "72/100". Give specific observations.
If frames are unclear, say which frames and why.

Output in JSON format with these fields for each module:
{
  "module": "serve",
  "problems": [
    {"issue": "specific observable problem", "cause": "why it happens", "fix": "specific drill or correction", "severity": "high/medium/low"}
  ],
  "overall_assessment": "one-sentence summary"
}"""

SCREENSHOT_PROMPT = """You are a data extraction assistant. This is a screenshot from an OPPO Watch tennis mode summary.
Extract ALL numeric values you can find. Look for Chinese labels like:
总击球数 (total shots), 发球 (serves), 正手上旋 (forehand topspin), 正手削球 (forehand slice),
反手上旋 (backhand topspin), 反手削球 (backhand slice), 挥拍速度 (swing speed),
心率 (heart rate), 跑动距离 (distance), 卡路里 (calories).

Output ONLY a JSON object with these fields (use null for any you cannot find):
{
  "total_shots": 300, "serve_count": 60,
  "forehand_topspin": 120, "forehand_slice": 30,
  "backhand_topspin": 60, "backhand_slice": 30,
  "avg_swing_speed": 45.5, "avg_heart_rate": 135,
  "max_heart_rate": 172, "total_distance": 1500, "total_calories": 480
}
Do not include any text outside the JSON."""


# ── Functions ────────────────────────────────────────────

def _extract_json(text: str) -> dict[str, Any]:
    """Robust JSON extraction from LLM output."""
    json_match = re.search(r'\{[\s\S]*\}', text)
    if not json_match:
        return {}
    try:
        return json.loads(json_match.group(0))
    except json.JSONDecodeError:
        return {}


def detect_video_modules(frame_paths: list[str], focus_module = None) -> dict[str, Any]:
    sample_size = min(12, len(frame_paths))
    step = max(1, len(frame_paths) // sample_size)
    sampled = frame_paths[::step][:sample_size]

    focus_text = f"\n\nIMPORTANT: The player says they are practicing **{focus_module}**. Prioritize detecting {focus_module} — look for its specific biomechanical markers." if focus_module else ""

    messages = [{"role": "user", "content": [
            {"type": "text", "text": f"Sampled {len(sampled)} keyframes. Determine which technical modules are covered.{focus_text}"},
            *[_image_content(p) for p in sampled],
        ]},
    ]
    text = _chat(CONTENT_DETECTION_PROMPT, messages, max_tokens=512)
    result = _extract_json(text)
    return result if result else {"covered_modules": [], "module_confidence": {}, "summary": ""}


def analyze_frames_batch(frame_paths: list[str], batch_index: int, total_batches: int, focus_module = None) -> dict[str, Any]:
    focus_text = f"\n\nCONTEXT: The player says this video is for practicing **{focus_module}**. Focus your analysis on {focus_module} technique — look for specific {focus_module} mechanics and problems." if focus_module else ""
    messages = [{"role": "user", "content": [
            {"type": "text", "text": f"Batch {batch_index + 1}/{total_batches}, {len(frame_paths)} keyframes. Analyze the player's technical performance.{focus_text}"},
            *[_image_content(p) for p in frame_paths],
        ]},
    ]
    text = _chat(ANALYSIS_SYSTEM_PROMPT, messages, max_tokens=4096)
    return {"batch": batch_index, "raw_response": text}


def extract_screenshot_stats(screenshot_path: str) -> dict[str, Any]:
    messages = [{"role": "user", "content": [
            {"type": "text", "text": "Extract all tennis statistics from this OPPO Watch screenshot."},
            _image_content(screenshot_path),
        ]},
    ]
    text = _chat(SCREENSHOT_PROMPT, messages, max_tokens=512)
    return _extract_json(text)


def generate_watch_section(oppo_stats: dict[str, Any], fitness_data: dict[str, Any]) -> str:
    if not oppo_stats:
        return """NOTE: No watch data uploaded. The following are unavailable:
- Shot statistics: unavailable — estimate from video frames
- Swing speed: unavailable
- Heart rate / distance / calories: unavailable
- **Fitness scores: mark as "no watch data, unable to assess", set scores to null**"""

    return "\n".join([
        f"- Total shots: {oppo_stats.get('total_shots', 'N/A')}",
        f"- Serves: {oppo_stats.get('serve_count', 'N/A')}",
        f"- FH topspin: {oppo_stats.get('forehand_topspin', 'N/A')} | FH slice: {oppo_stats.get('forehand_slice', 'N/A')}",
        f"- BH topspin: {oppo_stats.get('backhand_topspin', 'N/A')} | BH slice: {oppo_stats.get('backhand_slice', 'N/A')}",
        f"- Avg swing speed: {oppo_stats.get('avg_swing_speed', 'N/A')}",
        "", "## Fitness Data (from watch)",
        f"- Avg HR: {fitness_data.get('cardiovascular_endurance', {}).get('avg_hr', 'N/A')} bpm",
        f"- Total distance: {fitness_data.get('movement', {}).get('total_distance_m', 'N/A')} m",
        f"- Total calories: {fitness_data.get('training_load', {}).get('total_calories', 'N/A')} kcal",
    ])


def generate_final_report(
    frame_analyses: list[dict[str, Any]],
    oppo_stats: dict[str, Any],
    fitness_data: dict[str, Any],
    rag_context: str,
    user_profile: dict[str, Any],
    covered_modules: list[str],
    focus_module = None,
) -> dict[str, Any]:
    all_modules = ["forehand", "backhand", "serve", "volley", "footwork", "return"]
    uncovered = [m for m in all_modules if m not in covered_modules]
    covered_str = ", ".join(covered_modules)
    uncovered_str = ", ".join(uncovered) if uncovered else "none"
    focus_hint = f"""

## ⚠️ 重要提示
学员告知此视频主要练习的是 **{focus_module}**。即使从静态帧中看起来像其他技术动作，也请优先按照 {focus_module} 来分析。注意区分 {focus_module} 的关键特征（如发球的抛球动作、trophy position、平台站位等）。""" if focus_module else ""

    prompt = f"""你是一位资深网球教练，正在为一位学员撰写技术分析报告。请严格按以下四段式结构撰写。
{focus_hint}

## 视频检测到的模块
✅ {covered_str}
❌ {uncovered_str}（未检测到的模块跳过不评）

## 学员信息
球龄 {user_profile.get('playing_years', '?')}年 | 自评 NTRP {user_profile.get('self_rated_ntrp', '?')} | 目标 NTRP {user_profile.get('target_ntrp', '?')}

## 手表数据
{generate_watch_section(oppo_stats, fitness_data)}

## AI 帧分析结果
{chr(10).join([f'批次{a["batch"]+1}: {a["raw_response"][:400]}' for a in frame_analyses])}

## NTRP 教学参考
{rag_context}

## 报告结构（必须严格遵循）

### 一、评分
对检测到的 8 种击球类型（正手上旋 / 正手平击 / 正手切削 / 反手上旋 / 反手平击 / 反手切削 / 发球 / 截击），
给出 NTRP 等级（1.0-7.0）和简短理由。未检测到的标注"未检测到"。

### 二、评价
详细分析每个模块：
- ✅ 做得好的地方（2-3 点）
- ⚠️ 存在的问题（2-3 点，要具体。不是"抛球不稳"，而是"抛球高度在头顶上方约30cm，偏向左侧约20cm"）
- 📊 与目标等级 NTRP {user_profile.get('target_ntrp', '?')} 的差距在哪

### 三、调整方案
针对每个问题，给出具体的纠正方案：
- 问题：xxx
- 根因：xxx
- 纠正练习：xxx（具体到每天做几组、每组几次、注意什么）

### 四、训练建议
- 本周训练计划（每天练什么、多长时间、组数次数）
- 建议 2 周后复评，重点检查哪些改进点
- 长期进阶路径（从当前水平到目标水平需要经历哪几个阶段）

## 写作规则
- 全文使用中文，语气像教练对学员说话
- 每个问题必须配对应的练习，每个练习必须有组数次数
- 优先排序：告诉学员最先应该改什么，为什么这是最重要的
- 评分要诚实，但重点放在如何提高上

用 `---JSON---` 分隔两部分输出：
第一部分：Markdown 格式的完整教练报告（中文）
第二部分：JSON 对象
```json
{{
  "overall_ntrp": 3.0,
  "ntrp_confidence": 0.7,
  "technique_breakdown": {{
    "forehand_topspin": {{"score": 72, "level": "3.0", "top_issue": "..."}},
    "forehand_flat": {{"score": 68, "level": "3.0", "top_issue": "..."}},
    "forehand_slice": {{"score": null, "level": null, "top_issue": "未检测到"}},
    "backhand_topspin": {{"score": null, "level": null, "top_issue": "未检测到"}},
    "backhand_flat": {{"score": null, "level": null, "top_issue": "未检测到"}},
    "backhand_slice": {{"score": null, "level": null, "top_issue": "未检测到"}},
    "serve": {{"score": 65, "level": "2.5", "top_issue": "..."}},
    "volley": {{"score": null, "level": null, "top_issue": "未检测到"}}
  }},
  "top_3_priorities": ["最先改的技术", "其次", "再次"],
  "weekly_plan_summary": "一句话概括本周训练重点"
}}
```"""

    full_text = _chat('You are a professional tennis coach writing a coaching report in Chinese.', [{"role": "user", "content": prompt}], max_tokens=8192)

    if "---JSON---" in full_text:
        parts = full_text.split("---JSON---", 1)
        report_md = parts[0].strip()
        structured = _extract_json(parts[1].strip())
    else:
        report_md = full_text
        structured = {}

    return {"report_markdown": report_md, "structured": structured}
