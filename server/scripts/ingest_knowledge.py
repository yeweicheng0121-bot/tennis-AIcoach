import re
from pathlib import Path

RAG_DIR = Path(__file__).parent.parent.parent / "RAG"


def split_into_chunks(text: str, chunk_size: int = 400, overlap: int = 60) -> list[str]:
    """按段落边界拆分文本为 chunk。"""
    paragraphs = text.split("\n\n")
    chunks = []
    current = ""
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(current) + len(para) < chunk_size:
            current += para + "\n\n"
        else:
            if current.strip():
                chunks.append(current.strip())
            current = para + "\n\n"
    if current.strip():
        chunks.append(current.strip())

    merged = []
    buf = ""
    for c in chunks:
        if len(buf) + len(c) < chunk_size:
            buf += c + "\n\n"
        else:
            if buf.strip():
                merged.append(buf.strip())
            buf = c + "\n\n"
    if buf.strip():
        merged.append(buf.strip())
    return merged


def extract_level_and_module(filename: str, text: str) -> list[dict]:
    """从文本中提取 NTRP 等级和模块标签。"""
    chunks = split_into_chunks(text)
    records = []

    level_match = re.search(r"NTRP\s*(\d+\.?\d*)", filename + " " + text[:500])
    level = float(level_match.group(1)) if level_match else 3.0

    for chunk in chunks:
        module = "general"
        first_part = chunk[:400]
        if "正手" in first_part or "Forehand" in first_part:
            module = "forehand"
        elif "反手" in first_part or "Backhand" in first_part:
            module = "backhand"
        elif "发球" in first_part or "Serve" in first_part:
            module = "serve"
        elif "接发" in first_part or "Return" in first_part:
            module = "return"
        elif "截击" in first_part or "网前" in first_part or "Volley" in first_part:
            module = "volley"
        elif "脚步" in first_part or "Footwork" in first_part:
            module = "footwork"
        elif "体能" in first_part or "Fitness" in first_part:
            module = "fitness"

        category = "standard"
        if (
            "错误" in first_part
            or "纠正" in first_part
            or "Mistake" in first_part
            or "Correction" in first_part
        ):
            category = "correction"
        elif (
            "训练方案" in first_part
            or "训练计划" in first_part
            or "Training Plan" in first_part
        ):
            category = "training_plan"
        elif "教学要点" in first_part or "Teaching Points" in first_part:
            category = "teaching_points"

        records.append(
            {
                "ntrp_level": level,
                "module": module,
                "category": category,
                "content": chunk,
            }
        )

    return records


def load_all_chunks() -> list[dict]:
    """加载 RAG 目录下所有 markdown 文件并拆分为 chunk。"""
    all_records = []
    for md_file in RAG_DIR.glob("*.md"):
        text = md_file.read_text(encoding="utf-8")
        records = extract_level_and_module(md_file.name, text)
        all_records.extend(records)
    return all_records


if __name__ == "__main__":
    records = load_all_chunks()
    print(f"Total chunks: {len(records)}")
    for r in records[:10]:
        print(
            f"  Level {r['ntrp_level']} | {r['module']} | {r['category']} | {len(r['content'])} chars"
        )
