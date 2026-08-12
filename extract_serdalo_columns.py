import pdfplumber
import os
import re

PDF_PATH = "dataset/serdalo/serdalo_test_1.pdf"
OUTPUT_PATH = "dataset/serdalo/page2_columns_test.txt"


def clean_word(word):
    """
    Минимальная очистка слова.
    Пока ничего агрессивного не исправляем,
    чтобы не испортить ингушский текст.
    """

    word = word.strip()

    if not word:
        return ""

    return word


def group_words_into_lines(words, y_tolerance=3):
    """
    Собираем слова в строки по координате top.
    """

    lines = []

    for word in sorted(words, key=lambda w: (w["top"], w["x0"])):

        placed = False

        for line in lines:

            if abs(line["top"] - word["top"]) <= y_tolerance:
                line["words"].append(word)
                placed = True
                break

        if not placed:
            lines.append({
                "top": word["top"],
                "words": [word]
            })

    # Сортируем слова внутри каждой строки
    for line in lines:
        line["words"].sort(key=lambda w: w["x0"])

    # Сортируем строки сверху вниз
    lines.sort(key=lambda x: x["top"])

    return lines


def extract_column(page, x0, x1):
    """
    Извлекает текст из указанной колонки.
    """

    words = page.extract_words(
        x_tolerance=2,
        y_tolerance=3,
        keep_blank_chars=False
    )

    column_words = []

    for word in words:

        center_x = (word["x0"] + word["x1"]) / 2

        if x0 <= center_x <= x1:
            column_words.append(word)

    lines = group_words_into_lines(column_words)

    result = []

    for line in lines:

        words = [
            clean_word(w["text"])
            for w in line["words"]
        ]

        words = [w for w in words if w]

        if words:
            result.append(" ".join(words))

    return result


def main():

    print("=" * 60)
    print("🇮🇳 ТЕСТ КОЛОНОК «СЕРДАЛО»")
    print("=" * 60)

    with pdfplumber.open(PDF_PATH) as pdf:

        print(f"\n📄 Страниц в PDF: {len(pdf.pages)}")

        # Страница 2 = индекс 1
        page = pdf.pages[1]

        print("\n📐 Размер страницы:")
        print(f"width:  {page.width}")
        print(f"height: {page.height}")

        # Границы колонок.
        #
        # По твоему inspect_serdalo.py:
        #
        # левая колонка:   ~52 - 327
        # средняя колонка: ~352 - 490
        # правая колонка:  ~502 - 790
        #
        columns = [
            ("ЛЕВАЯ КОЛОНКА", 45, 330),
            ("СРЕДНЯЯ КОЛОНКА", 345, 495),
            ("ПРАВАЯ КОЛОНКА", 495, 795),
        ]

        all_text = []

        for name, x0, x1 in columns:

            print("\n" + "=" * 60)
            print(name)
            print(f"x: {x0} → {x1}")
            print("=" * 60)

            lines = extract_column(
                page,
                x0,
                x1
            )

            print(f"Строк: {len(lines)}")

            for line in lines:
                print(line)

            all_text.append(
                f"\n===== {name} =====\n"
            )

            all_text.extend(lines)

    os.makedirs(
        os.path.dirname(OUTPUT_PATH),
        exist_ok=True
    )

    with open(
        OUTPUT_PATH,
        "w",
        encoding="utf-8"
    ) as f:

        f.write("\n".join(all_text))

    print("\n" + "=" * 60)
    print("✅ ГОТОВО")
    print("=" * 60)

    print(
        f"\n💾 Результат:\n{OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()