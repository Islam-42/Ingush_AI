import pdfplumber

PDF_FILE = "dataset/serdalo/serdalo_test_1.pdf"

with pdfplumber.open(PDF_FILE) as pdf:

    page = pdf.pages[1]

    print("=" * 60)
    print("РАЗМЕР СТРАНИЦЫ")
    print("=" * 60)

    print("width:", page.width)
    print("height:", page.height)

    words = page.extract_words()

    print("\nКоличество слов:", len(words))

    print("\nПЕРВЫЕ 100 СЛОВ С КООРДИНАТАМИ:")
    print("=" * 60)

    for word in words[:100]:

        print(
            f"x0={word['x0']:.1f} "
            f"x1={word['x1']:.1f} "
            f"top={word['top']:.1f} "
            f"bottom={word['bottom']:.1f} "
            f"→ {word['text']}"
        )