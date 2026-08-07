import re
from pathlib import Path

out_dir = Path(r"C:\Users\asus\Desktop\MSALGCM Paper\RRL Papers\_extracted")
report = Path(r"C:\Users\asus\Desktop\MSALGCM Paper\RRL Papers\_results_scan.txt")
keywords = [
    "Table", "accuracy", "makespan", "gap", "runtime", "iteration",
    "best", "mean", "fitness", "cost", "distance", "seed", "run",
    "percent", "SA", "TS", "PSO", "result", "comparison", "experiment",
]

lines = []
for f in sorted(out_dir.glob("*.txt")):
    text = f.read_text(encoding="utf-8", errors="replace")
    lines.append("=" * 80)
    lines.append(f.name)
    pages = text.split("--- PAGE")
    hot = []
    for i, p in enumerate(pages[1:], 1):
        nums = len(re.findall(r"\d+\.?\d*", p))
        kw = sum(1 for k in keywords if k.lower() in p.lower())
        score = nums + kw * 2
        if score > 35:
            hot.append((score, i))
    hot.sort(reverse=True)
    lines.append(f"Hot pages: {hot[:10]}")
    for score, pg in hot[:5]:
        chunk = pages[pg]
        lines.append(f"\n--- {f.stem} PAGE {pg} (score={score}) ---")
        lines.append(re.sub(r"\s+", " ", chunk)[:3500])

report.write_text("\n".join(lines), encoding="utf-8")
print(f"Wrote {report}")
