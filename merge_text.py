from pathlib import Path

folder = Path("ocr_book")
output = Path("textbook.txt")

files = sorted(folder.glob("page_*.txt"))

with output.open("w", encoding="utf-8") as f:
    for file in files:
        text = file.read_text(encoding="utf-8", errors="ignore").strip()

        f.write(f"\n\n===== СТРАНИЦА {file.stem.replace('page_', '')} =====\n\n")
        f.write(text)

print(f"Готово!")
print(f"Обработано страниц: {len(files)}")
print(f"Файл: {output}")