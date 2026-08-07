from docx import Document
from docx.oxml.ns import qn

path = r"C:\Users\asus\Desktop\MSALGCM Paper\Paper Setup\MSALGCM-Final-Paper-Draft.docx"
doc = Document(path)
for i, p in enumerate(doc.paragraphs[:50]):
    style = p.style.name if p.style else "?"
    print(f"{i:3} [{style}] {p.text[:120]!r}")
print("--- sections", len(doc.sections))
for si, s in enumerate(doc.sections):
    cols = s._sectPr.find(qn("w:cols"))
    if cols is not None:
        print(f"section {si}: num={cols.get(qn('w:num'))} space={cols.get(qn('w:space'))}")
    else:
        print(f"section {si}: single column")
