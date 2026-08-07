"""Generate PDF from Paper Setup/comparative evaluation v2.md."""

from __future__ import annotations

from pathlib import Path

import markdown
from xhtml2pdf import pisa

ROOT = Path(__file__).resolve().parents[1]
MD_PATH = ROOT / "Paper Setup" / "comparative evaluation v2.md"
PDF_PATH = ROOT / "Paper Setup" / "comparative evaluation v2.pdf"

CSS = """
@page {
    size: letter;
    margin: 1.8cm 2cm;
}
body {
    font-family: Times, "Times New Roman", serif;
    font-size: 10.5pt;
    line-height: 1.42;
    color: #111;
}
h1 {
    font-size: 15pt;
    text-align: center;
    margin-bottom: 0.35em;
}
h2 {
    font-size: 12.5pt;
    margin-top: 1.1em;
    border-bottom: 1px solid #ccc;
    padding-bottom: 0.12em;
}
h3 {
    font-size: 11pt;
    margin-top: 0.85em;
}
p, li {
    text-align: justify;
    margin: 0.32em 0;
}
blockquote {
    margin: 0.5em 0.8em;
    padding: 0.35em 0.7em;
    border-left: 3px solid #888;
    background: #f7f7f7;
    font-size: 9.5pt;
}
table {
    width: 100%;
    border-collapse: collapse;
    font-size: 8.5pt;
    margin: 0.5em 0 0.9em 0;
    table-layout: fixed;
    word-wrap: break-word;
}
th, td {
    border: 1px solid #444;
    padding: 3px 4px;
    vertical-align: top;
}
th {
    background: #eee;
    font-weight: bold;
}
hr {
    border: none;
    border-top: 1px solid #ccc;
    margin: 0.9em 0;
}
code {
    font-family: Consolas, monospace;
    font-size: 8.5pt;
}
.meta {
    text-align: center;
    font-size: 9.5pt;
    margin-bottom: 0.9em;
}
"""


def _preprocess(md: str) -> str:
    lines = md.splitlines()
    if lines and lines[0].startswith("# "):
        title = lines[0][2:].strip()
        rest = lines[1:]
        meta_lines: list[str] = []
        body_start = 0
        for i, line in enumerate(rest):
            if line.strip() == "---":
                body_start = i + 1
                break
            if line.strip():
                meta_lines.append(line.strip())
        meta_html = "<br/>".join(meta_lines)
        body = "\n".join(rest[body_start:])
        return f'<div class="meta"><h1>{title}</h1>{meta_html}</div>\n\n{body}'
    return md


def main() -> None:
    if not MD_PATH.is_file():
        raise SystemExit(f"Missing source markdown: {MD_PATH}")

    md_text = _preprocess(MD_PATH.read_text(encoding="utf-8"))
    html_body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "nl2br", "sane_lists"],
    )
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"/><style>{CSS}</style></head>
<body>{html_body}</body></html>"""

    PDF_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PDF_PATH.open("wb") as pdf_file:
        status = pisa.CreatePDF(html, dest=pdf_file, encoding="utf-8")

    if status.err:
        raise SystemExit(f"PDF generation failed with {status.err} errors")

    print(f"Wrote {PDF_PATH}")


if __name__ == "__main__":
    main()
