"""Insert full narrative literature (from groupmate paper.pdf) into comparative evaluation v2.md."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT / "Paper Setup" / "comparative evaluation v2.md"
LIT = ROOT / "Paper Setup" / "_section2_full_literature.md"

START = "## 2. REVIEW OF RELATED LITERATURE"
END = "## 3. METHODOLOGY"


def main() -> None:
    if not LIT.is_file():
        raise SystemExit(f"Missing literature insert: {LIT}")

    text = V2.read_text(encoding="utf-8")
    lit = LIT.read_text(encoding="utf-8").strip()

    i0 = text.index(START)
    i1 = text.index(END)
    merged = text[:i0] + lit + "\n\n---\n\n" + text[i1:]

    # Bump version marker if still v2.1
    merged = merged.replace("**Version:** v2.1", "**Version:** v2.2", 1)
    merged = merged.replace(
        "7. Literature §2.1–2.11 full narrative retained in companion drafts "
        "(`paper.pdf`, `Comparative-Evaluation-SA-TS-PSO-FULL-PAPER (1).pdf`); "
        "this document condenses for results integration.",
        "7. Convergence figures exist under `results/` but are not embedded in this PDF export.",
    )

    V2.write_text(merged, encoding="utf-8")
    print(f"Updated {V2} ({len(merged):,} chars)")


if __name__ == "__main__":
    main()
