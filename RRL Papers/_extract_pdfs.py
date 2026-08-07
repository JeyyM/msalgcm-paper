import pypdf
from pathlib import Path

folder = Path(r"C:\Users\asus\Desktop\MSALGCM Paper\RRL Papers")
out_dir = folder / "_extracted"
out_dir.mkdir(exist_ok=True)

for pdf in sorted(folder.glob("*.pdf")):
    try:
        reader = pypdf.PdfReader(str(pdf))
        parts = []
        for i, page in enumerate(reader.pages):
            t = page.extract_text() or ""
            parts.append(f"--- PAGE {i + 1} ---\n{t}")
        full = "\n".join(parts)
        out = out_dir / (pdf.stem + ".txt")
        out.write_text(full, encoding="utf-8", errors="replace")
        print(f"{pdf.name}: {len(reader.pages)} pages, {len(full)} chars")
    except Exception as e:
        print(f"ERROR {pdf.name}: {e}")
