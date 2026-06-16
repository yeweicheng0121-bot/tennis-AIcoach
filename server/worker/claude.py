import base64
import json
import re
from typing import Any

import anthropic

from server.config import settings

_client: anthropic.Anthropic | None = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.claude_api_key)
    return _client


def _encode_image(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


ANALYSIS_SYSTEM_PROMPT = """你是一位经验丰富的 NTRP 认证网球教练，拥有 20 年一线教学经验。
你的任务是分析网球比赛视频的关键帧，评估球员的技术水平。

请从以下维度分析：
1. 击球类型识别（正手/反手/发球/截击）
2. 动作质量评估（转体/引拍/随挥/击球点位置）
3. 脚步与站位（开放式/关闭式/到位率/回位意识）
4. 常见技术问题（如侧身绕正手、击球点靠后、随挥不完整等）
5. 与 NTRP 标准对比

所有分析必须基于你看到的内容，不要臆测。如果某帧不够清晰无法判断，请标注"无法确定"。

请以 JSON 格式输出分析结果。"""


def analyze_frames_batch(
    frame_paths: list[str], batch_index: int, total_batches: int
) -> dict[str, Any]:
    """分析一批关键帧，返回结构化 JSON。"""
    client = get_client()

    content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": f"这是第 {batch_index + 1}/{total_batches} 批关键帧，共 {len(frame_paths)} 张。请分析这些帧中球员的技术表现。",
        }
    ]

    for path in frame_paths:
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": _encode_image(path),
                },
            }
        )

    response = client.messages.create(
        model=settings.claude_model,
        max_tokens=4096,
        system=ANALYSIS_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
    )

    return {"batch": batch_index, "raw_response": response.content[0].text}


def generate_final_report(
    frame_analyses: list[dict[str, Any]],
    oppo_stats: dict[str, Any],
    fitness_data: dict[str, Any],
    rag_context: str,
    user_profile: dict[str, Any],
) -> dict[str, Any]:
    """汇总所有分析结果，生成 Markdown 报告 + 结构化 JSON。"""
    client = get_client()

    prompt = f"""请基于以下信息，生成一份完整的 NTRP 网球评估报告。

## 用户信息
- 出生年份：{user_profile.get('birth_year', '未知')}
- 球龄：{user_profile.get('playing_years', '未知')} 年
- 自评等级：NTRP {user_profile.get('self_rated_ntrp', '未知')}
- 目标等级：NTRP {user_profile.get('target_ntrp', '未知')}
- 伤病史：{user_profile.get('injury_history', '无')}

## OPPO 手表数据
- 总击球数：{oppo_stats.get('total_shots', 'N/A')}
- 发球数：{oppo_stats.get('serve_count', 'N/A')}
- 正手上旋：{oppo_stats.get('forehand_topspin', 'N/A')} 次 | 正手削球：{oppo_stats.get('forehand_slice', 'N/A')} 次
- 反手上旋：{oppo_stats.get('backhand_topspin', 'N/A')} 次 | 反手削球：{oppo_stats.get('backhand_slice', 'N/A')} 次
- 平均挥拍速度：{oppo_stats.get('avg_swing_speed', 'N/A')}

## 体能数据
- 平均心率：{fitness_data.get('cardiovascular_endurance', {}).get('avg_hr', 'N/A')} bpm
- 最大心率：{fitness_data.get('cardiovascular_endurance', {}).get('max_hr', 'N/A')} bpm
- 总跑动距离：{fitness_data.get('movement', {}).get('total_distance_m', 'N/A')} m
- 每分钟跑动：{fitness_data.get('movement', {}).get('distance_per_min', 'N/A')} m/min
- 总卡路里：{fitness_data.get('training_load', {}).get('total_calories', 'N/A')} kcal

## 视频帧分析摘要
{chr(10).join([f'- 批次 {a["batch"] + 1}: {a["raw_response"][:300]}...' for a in frame_analyses])}

## NTRP 教学指南参考
{rag_context}

## 输出要求
请输出两部分，用 `---JSON---` 分隔：

第一部分：完整的 Markdown 格式评估报告，包含：
1. 综合 NTRP 等级评定（含置信度）
2. 技术评分（正手/反手/发球/截击/脚步/接发，每项 0-100 分 + 依据）
3. 体能评分（心肺/移动/负荷，每项 0-100 分 + 依据）
4. 强弱项识别（3-5 项优势 + 3-5 项短板）
5. 关键问题帧说明
6. 4 周训练计划（每周 2 次，包含具体练习名称、组数、次数）

第二部分（`---JSON---` 之后）：一个 JSON 对象，包含以下字段：
```json
{{
  "overall_ntrp": 3.0,
  "ntrp_confidence": 0.7,
  "technique_breakdown": {{
    "forehand": {{"score": 72, "depth_control": 70, "stability": 75}},
    "backhand": {{"score": 55, "depth_control": 50, "stability": 60}},
    "serve": {{"score": 65, "success_rate": 60, "motion_quality": 70}},
    "volley": {{"score": 50, "stability": 55}},
    "footwork": {{"score": 60, "in_place_rate": 65, "adjustment": 60}},
    "return": {{"score": 55, "stability": 60}}
  }},
  "strengths": ["正手稳定性"],
  "weaknesses": ["反手深度控制", "网前截击"],
  "key_frames": [{{"timestamp": 120, "issue": "击球点靠后", "suggestion": "提前引拍"}}]
}}
```

所有建议必须基于 NTRP 教学指南，所有量化指标优先使用 NTRP 标准基准值。
"""

    response = client.messages.create(
        model=settings.claude_model,
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )

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
