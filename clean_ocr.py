from pathlib import Path
import re

SOURCE = Path("ocr_book")
OUTPUT = Path("clean_book")

OUTPUT.mkdir(exist_ok=True)

# Очевидные технические ошибки OCR.
# Сначала используем только безопасные замены.
REPLACEMENTS = {
    "ГГАЛГТАЙ": "ГIАЛГIАЙ",
    "ГГАЛГ1АЙ": "ГIАЛГIАЙ",
    "ГГАЛГIАЙ": "ГIАЛГIАЙ",
    "ГГАЛГТАЙ": "ГIАЛГIАЙ",
}

files = sorted(SOURCE.glob("page_*.txt"))

print(f"Найдено страниц: {len(files)}")
print("Начинаю очистку...\n")

total_changes = 0

for file in files:
    text = file.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    original = text

    # Исправляем известные ошибки
    for old, new in REPLACEMENTS.items():
        text = text.replace(old, new)

    # Убираем очевидные артефакты PDF/OCR
    text = text.replace("\x00", "")

    # Убираем слишком много пустых строк
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Убираем пробелы в конце строк
    text = "\n".join(
        line.rstrip()
        for line in text.splitlines()
    )

    if text != original:
        total_changes += 1

    output_file = OUTPUT / file.name
    output_file.write_text(
        text,
        encoding="utf-8"
    )

print("\n✅ Очистка завершена!")
print(f"Обработано страниц: {len(files)}")
print(f"Изменено страниц: {total_changes}")
print(f"Результат находится в: {OUTPUT}")