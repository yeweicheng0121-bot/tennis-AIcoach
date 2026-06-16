from __future__ import annotations
"""Task 11: RAG knowledge retrieval using pgvector keyword fallback."""
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


MODULE_KEYWORD_MAP = {
    "正手": "forehand", "forehand": "forehand",
    "反手": "backhand", "backhand": "backhand",
    "发球": "serve", "serve": "serve", "双误": "serve",
    "接发": "return", "return": "return",
    "截击": "volley", "网前": "volley", "volley": "volley",
    "脚步": "footwork", "移动": "footwork", "到位": "footwork", "footwork": "footwork",
    "体能": "fitness", "心率": "fitness", "耐力": "fitness", "fitness": "fitness",
}


async def retrieve_relevant_chunks(
    db: AsyncSession,
    ntrp_level: float,
    weaknesses: list[str],
    target_ntrp: float | None = None,
    top_k: int = 10,
) -> list[dict[str, Any]]:
    module_keywords = []
    for w in weaknesses:
        for kw, mod in MODULE_KEYWORD_MAP.items():
            if kw in w.lower():
                module_keywords.append(mod)
                break
    if not module_keywords:
        module_keywords = ["forehand", "backhand", "serve", "footwork"]

    module_filter = "', '".join(set(module_keywords))
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
    result = await db.execute(query, {
        "min_level": max(1.0, ntrp_level - 0.5),
        "max_level": min(7.0, (target_ntrp or ntrp_level) + 0.5),
        "level": ntrp_level,
        "limit": top_k,
    })
    rows = result.fetchall()
    return [{"id": r[0], "ntrp_level": r[1], "module": r[2], "category": r[3], "content": r[4]} for r in rows]


def format_chunks_for_prompt(chunks: list[dict[str, Any]]) -> str:
    lines = []
    for i, c in enumerate(chunks, 1):
        lines.append(f"[{i}] (NTRP {c['ntrp_level']} | {c['module']} | {c['category']})")
        lines.append(c["content"])
        lines.append("---")
    return "\n".join(lines)
