from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def retrieve_relevant_chunks(
    db: AsyncSession,
    ntrp_level: float,
    weaknesses: list[str],
    target_ntrp: float | None = None,
    top_k: int = 10,
) -> list[dict[str, Any]]:
    """检索与用户水平和弱项最相关的知识库 chunk。"""
    # 将弱项关键词映射到技术模块
    module_keywords = []
    for w in weaknesses:
        w_lower = w.lower()
        if any(k in w_lower for k in ["正手", "forehand"]):
            module_keywords.append("forehand")
        if any(k in w_lower for k in ["反手", "backhand"]):
            module_keywords.append("backhand")
        if any(k in w_lower for k in ["发球", "serve"]):
            module_keywords.append("serve")
        if any(k in w_lower for k in ["接发", "return"]):
            module_keywords.append("return")
        if any(k in w_lower for k in ["截击", "网前", "volley"]):
            module_keywords.append("volley")
        if any(k in w_lower for k in ["脚步", "移动", "到位", "footwork"]):
            module_keywords.append("footwork")
        if any(k in w_lower for k in ["体能", "心率", "耐力", "fitness"]):
            module_keywords.append("fitness")

    if not module_keywords:
        module_keywords = ["forehand", "backhand", "serve", "footwork"]

    module_filter = "', '".join(module_keywords)
    query = text(f"""
        SELECT id, ntrp_level, module, category, content
        FROM ntrp_chunks
        WHERE ntrp_level BETWEEN :min_level AND :max_level
          AND module IN ('{module_filter}')
        ORDER BY
          CASE category
            WHEN 'correction' THEN 1
            WHEN 'teaching_points' THEN 2
            WHEN 'training_plan' THEN 3
            ELSE 4
          END,
          ABS(ntrp_level - :level)
        LIMIT :limit
    """)

    result = await db.execute(
        query,
        {
            "min_level": max(1.0, ntrp_level - 0.5),
            "max_level": min(7.0, (target_ntrp or ntrp_level) + 0.5),
            "level": ntrp_level,
            "limit": top_k,
        },
    )

    rows = result.fetchall()
    return [
        {
            "id": row[0],
            "ntrp_level": row[1],
            "module": row[2],
            "category": row[3],
            "content": row[4],
        }
        for row in rows
    ]


def format_chunks_for_prompt(chunks: list[dict[str, Any]]) -> str:
    """将检索到的 chunk 格式化为 Prompt 可用的文本。"""
    lines = []
    for i, c in enumerate(chunks, 1):
        lines.append(f"[{i}] (NTRP {c['ntrp_level']} | {c['module']} | {c['category']})")
        lines.append(c["content"])
        lines.append("---")
    return "\n".join(lines)
