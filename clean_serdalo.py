import os
import re
from pypdf import PdfReader

PDF_FILE = "dataset/serdalo/serdalo_test_1.pdf"
OUTPUT_FILE = "dataset/serdalo/serdalo_test_1_clean.txt"


def clean_line(line):
    line = line.strip()

    if not line:
        return ""

    # Ссылки
    line = re.sub(r"https?://\S+", " ", line)
    line = re.sub(r"www\.\S+", " ", line)
    line = re.sub(r"vk\.com/\S+", " ", line)
    line = re.sub(r"@\w+", " ", line)

    # Markdown-ссылки
    line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)

    # Номера страниц
    if re.fullmatch(r"\d+", line):
        return ""

    # Ненужные элементы газеты
    if line in {
        "12+",
        "ЛЕРХIАМ",
        "WWW.SERDALO.RU",
    }:
        return ""

    # Лишние пробелы
    line = re.sub(r"[ \t]+", " ", line)

    return line.strip()


def fix_hyphenation(text):
    """
    Соединяет слова, которые были разбиты переносом строки.

    Например:

    Келамата-
    наькъан

    превращается в:

    Келаматанаькъан
    """

    # Слово + перенос + продолжение слова
    text = re.sub(
        r"([А-Яа-яIӀi0-9]+)-\n([А-Яа-яIӀi0-9]+)",
        r"\1\2",
        text
    )

    return text


def process_page(page_number, page):

    print(f"📄 Обрабатываем страницу {page_number}...")

    try:
        text = page.extract_text(
            extraction_mode="layout"
        )

    except Exception as e:
        print(f"⚠️ Ошибка страницы {page_number}: {e}")
        return ""

    if not text:
        return ""

    lines = []

    for line in text.splitlines():

        line = clean_line(line)

        if line:
            lines.append(line)

    text = "\n".join(lines)

    # Исправляем переносы слов
    text = fix_hyphenation(text)

    return text


def main():

    print("=" * 60)
    print("🇮🇳 ОЧИСТКА ГАЗЕТЫ «СЕРДАЛО»")
    print("=" * 60)

    if not os.path.exists(PDF_FILE):

        print(f"❌ PDF не найден:\n{PDF_FILE}")
        return

    print(f"\n📚 Открываем:\n{PDF_FILE}")

    reader = PdfReader(PDF_FILE)

    print(f"📄 Страниц: {len(reader.pages)}")

    pages = []

    for number, page in enumerate(reader.pages, start=1):

        text = process_page(number, page)

        if text:
            pages.append(text)

    # Объединяем страницы
    text = "\n\n".join(pages)

    # Убираем слишком много пустых строк
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Убираем пробелы в конце строк
    text = re.sub(r"[ \t]+\n", "\n", text)

    # Убираем повторяющиеся пробелы
    text = re.sub(r"[ \t]{2,}", " ", text)

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(text)

    print("\n" + "=" * 60)
    print("✅ ГОТОВО!")
    print("=" * 60)

    print(f"💾 Файл:\n{OUTPUT_FILE}")
    print(f"📊 Символов: {len(text):,}")
    print(f"📝 Строк: {len(text.splitlines()):,}")

    print("=" * 60)


if __name__ == "__main__":
    main()