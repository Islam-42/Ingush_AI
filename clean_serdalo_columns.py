import os
import re
import pdfplumber

PDF_FILE = "dataset/serdalo/serdalo_test_1.pdf"
OUTPUT_FILE = "dataset/serdalo/serdalo_test_1_final.txt"


# ============================================================
# НАСТРОЙКИ
# ============================================================

# Для страницы A3 шириной ~842 pt.
# Эти границы соответствуют колонкам текста Сердало.
COLUMN_RANGES = [
    (40, 330),
    (330, 500),
    (500, 650),
    (650, 805),
]


# ============================================================
# ОЧИСТКА ТЕКСТА
# ============================================================

def clean_line(line):
    line = line.strip()

    if not line:
        return ""

    # URL
    line = re.sub(
        r"https?://\S+",
        "",
        line,
        flags=re.IGNORECASE
    )

    # WWW
    line = re.sub(
        r"WWW\.SERDALO\.RU",
        "",
        line,
        flags=re.IGNORECASE
    )

    # Лишние пробелы
    line = re.sub(r"\s+", " ", line)

    return line.strip()


# ============================================================
# СЛОВО В КОЛОНКУ
# ============================================================

def get_column(x0, x1):
    center = (x0 + x1) / 2

    for index, (left, right) in enumerate(COLUMN_RANGES):
        if left <= center < right:
            return index

    return None


# ============================================================
# ИЗВЛЕЧЕНИЕ КОЛОНОК
# ============================================================

def extract_page_columns(page):

    words = page.extract_words(
        x_tolerance=2,
        y_tolerance=3,
        keep_blank_chars=False
    )

    columns = {
        0: [],
        1: [],
        2: [],
        3: [],
    }

    for word in words:

        text = word["text"]

        if not text.strip():
            continue

        column = get_column(
            word["x0"],
            word["x1"]
        )

        if column is None:
            continue

        columns[column].append(word)

    result = []

    for column_number in range(4):

        words_column = columns[column_number]

        if not words_column:
            continue

        # Сортировка:
        # сначала сверху вниз,
        # потом слева направо

        words_column.sort(
            key=lambda x: (
                round(x["top"], 1),
                x["x0"]
            )
        )

        lines = []

        current_line = []
        current_top = None

        for word in words_column:

            top = word["top"]

            # Если новая строка
            if (
                current_top is None
                or abs(top - current_top) > 5
            ):

                if current_line:
                    lines.append(
                        " ".join(current_line)
                    )

                current_line = [
                    word["text"]
                ]

                current_top = top

            else:

                current_line.append(
                    word["text"]
                )

        if current_line:
            lines.append(
                " ".join(current_line)
            )

        result.extend(lines)

        result.append("")

    return result


# ============================================================
# СКЛЕИВАЕМ ПЕРЕНОСЫ
# ============================================================

def fix_hyphenation(lines):

    result = []

    i = 0

    while i < len(lines):

        line = lines[i].strip()

        if not line:
            result.append("")
            i += 1
            continue

        # Если строка заканчивается дефисом
        if (
            line.endswith("-")
            and i + 1 < len(lines)
        ):

            next_line = lines[i + 1].strip()

            if next_line:

                line = (
                    line[:-1]
                    + next_line
                )

                i += 2

                result.append(line)

                continue

        result.append(line)

        i += 1

    return result


# ============================================================
# УДАЛЕНИЕ МУСОРА
# ============================================================

def remove_noise(lines):

    result = []

    for line in lines:

        line = clean_line(line)

        if not line:
            continue

        # Номер страницы
        if re.fullmatch(
            r"\d{1,3}",
            line
        ):
            continue

        # Номер выпуска
        if re.fullmatch(
            r"№\s*\d+\s*\(\d+\)",
            line
        ):
            continue

        # Возраст
        if line in ["12+", "16+", "18+"]:
            continue

        # Соцсети
        if (
            "vk.com" in line.lower()
            or "@gserdalo" in line.lower()
            or "дзен сердало" in line.lower()
        ):
            continue

        # Заголовок сайта
        if "WWW.SERDALO.RU" in line.upper():
            continue

        result.append(line)

    return result


# ============================================================
# УДАЛЯЕМ ДУБЛИ
# ============================================================

def remove_duplicates(lines):

    result = []

    previous = None

    for line in lines:

        normalized = re.sub(
            r"\s+",
            " ",
            line.lower()
        )

        if normalized == previous:
            continue

        result.append(line)

        previous = normalized

    return result


# ============================================================
# ФОРМИРУЕМ АБЗАЦЫ
# ============================================================

def make_paragraphs(lines):

    paragraphs = []

    current = []

    for line in lines:

        line = line.strip()

        if not line:
            if current:

                paragraphs.append(
                    " ".join(current)
                )

                current = []

            continue

        current.append(line)

    if current:

        paragraphs.append(
            " ".join(current)
        )

    return paragraphs


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("🇮🇳 СОЗДАНИЕ КАЧЕСТВЕННОГО КОРПУСА «СЕРДАЛО»")
    print("=" * 70)

    print(f"\n📚 PDF: {PDF_FILE}")

    all_pages = []

    with pdfplumber.open(PDF_FILE) as pdf:

        print(
            f"📄 Страниц: {len(pdf.pages)}"
        )

        for page_number, page in enumerate(
            pdf.pages,
            start=1
        ):

            print(
                f"📖 Страница {page_number}..."
            )

            lines = extract_page_columns(page)

            lines = fix_hyphenation(lines)

            lines = remove_noise(lines)

            lines = remove_duplicates(lines)

            paragraphs = make_paragraphs(lines)

            if paragraphs:

                all_pages.append(
                    f"\n===== СТРАНИЦА {page_number} =====\n"
                )

                all_pages.extend(
                    paragraphs
                )

    # ========================================================
    # СОХРАНЕНИЕ
    # ========================================================

    text = "\n\n".join(all_pages)

    os.makedirs(
        os.path.dirname(OUTPUT_FILE),
        exist_ok=True
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(text)

    print("\n" + "=" * 70)
    print("✅ ГОТОВО")
    print("=" * 70)

    print(
        f"\n💾 Сохранено:\n{OUTPUT_FILE}"
    )

    print(
        f"\n📊 Символов: {len(text):,}"
    )

    print(
        f"📝 Слов: "
        f"{len(text.split()):,}"
    )


if __name__ == "__main__":
    main()