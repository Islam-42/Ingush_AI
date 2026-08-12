import pymupdf

PDF = "dataset/serdalo/serdalo_test_1.pdf"

doc = pymupdf.open(PDF)
page = doc[1]  # страница 2

blocks = page.get_text("blocks")

print("=" * 80)
print("ТЕКСТОВЫЕ БЛОКИ СТРАНИЦЫ 2")
print("=" * 80)

for i, block in enumerate(blocks):
    x0, y0, x1, y1, text = block[:5]

    text = text.strip().replace("\n", " ")

    if not text:
        continue

    print()
    print(f"БЛОК #{i}")
    print(f"x={x0:.1f}..{x1:.1f}")
    print(f"y={y0:.1f}..{y1:.1f}")
    print(f"ШИРИНА={x1-x0:.1f}")
    print(f"ТЕКСТ: {text[:250]}")