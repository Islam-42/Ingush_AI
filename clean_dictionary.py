import json
import re
from collections import defaultdict, Counter

INPUT = "ingush_dictionary.json"

OUTPUT_CLEAN = "ingush_dictionary_clean.json"
OUTPUT_TRAIN = "ingush_dictionary.jsonl"
OUTPUT_STATS = "dictionary_stats.json"


def normalize(text):
    """Минимальная нормализация текста."""
    if not isinstance(text, str):
        return ""

    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ============================================================
# ЗАГРУЗКА
# ============================================================

print("📚 Загружаем словарь...")

with open(INPUT, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Исходных записей: {len(data)}")


# ============================================================
# УДАЛЯЕМ ЗАПИСИ БЕЗ ПЕРЕВОДА
# ============================================================

data_with_translation = []

for item in data:
    word = normalize(item.get("word", ""))
    translation = normalize(item.get("translation", ""))

    if not word or not translation:
        continue

    item["word"] = word
    item["translation"] = translation

    if item.get("description"):
        item["description"] = normalize(item["description"])

    if item.get("part_of_speech"):
        item["part_of_speech"] = normalize(item["part_of_speech"])

    data_with_translation.append(item)


print(
    f"После удаления записей без перевода: "
    f"{len(data_with_translation)}"
)


# ============================================================
# ГРУППИРУЕМ ОДИНАКОВЫЕ СЛОВА
# ============================================================

groups = defaultdict(list)

for item in data_with_translation:
    key = item["word"].casefold()
    groups[key].append(item)


clean_data = []

for key, items in groups.items():

    first = items[0]

    translations = []
    descriptions = []
    parts_of_speech = []
    urls = []

    for item in items:

        translation = item["translation"]

        if translation not in translations:
            translations.append(translation)

        description = item.get("description", "")

        if description and description not in descriptions:
            descriptions.append(description)

        pos = item.get("part_of_speech", "")

        if pos and pos not in parts_of_speech:
            parts_of_speech.append(pos)

        url = item.get("url", "")

        if url and url not in urls:
            urls.append(url)

    clean_item = {
        "word": first["word"],
        "translations": translations,
        "part_of_speech": parts_of_speech,
        "descriptions": descriptions,
        "urls": urls,
        "source_entries": len(items),
    }

    clean_data.append(clean_item)


# ============================================================
# СОХРАНЯЕМ ОЧИЩЕННЫЙ СЛОВАРЬ
# ============================================================

with open(OUTPUT_CLEAN, "w", encoding="utf-8") as f:
    json.dump(
        clean_data,
        f,
        ensure_ascii=False,
        indent=2
    )


# ============================================================
# СОЗДАЁМ JSONL ДЛЯ БУДУЩЕГО ДАТАСЕТА
# ============================================================

with open(OUTPUT_TRAIN, "w", encoding="utf-8") as f:

    for item in clean_data:

        for translation in item["translations"]:

            record = {
                "word": item["word"],
                "translation": translation
            }

            f.write(
                json.dumps(
                    record,
                    ensure_ascii=False
                ) + "\n"
            )


# ============================================================
# СТАТИСТИКА
# ============================================================

duplicate_groups = [
    items
    for items in groups.values()
    if len(items) > 1
]

multi_translation = [
    item
    for item in clean_data
    if len(item["translations"]) > 1
]

stats = {
    "original_records": len(data),

    "records_with_translation": len(data_with_translation),

    "unique_words": len(clean_data),

    "duplicate_groups": len(duplicate_groups),

    "words_with_multiple_translations": len(multi_translation),

    "empty_translation_removed":
        len(data) - len(data_with_translation),

    "training_pairs":
        sum(len(item["translations"]) for item in clean_data),
}


with open(OUTPUT_STATS, "w", encoding="utf-8") as f:
    json.dump(
        stats,
        f,
        ensure_ascii=False,
        indent=2
    )


# ============================================================
# ВЫВОД
# ============================================================

print()
print("=" * 60)
print("🎉 ОЧИСТКА ЗАВЕРШЕНА")
print("=" * 60)

print(f"Исходных записей:              {stats['original_records']}")
print(f"С переводом:                   {stats['records_with_translation']}")
print(f"Уникальных слов:               {stats['unique_words']}")
print(f"Групп дубликатов:              {stats['duplicate_groups']}")
print(
    f"Многозначных слов:             "
    f"{stats['words_with_multiple_translations']}"
)
print(
    f"Удалено без перевода:          "
    f"{stats['empty_translation_removed']}"
)
print(
    f"Обучающих пар:                 "
    f"{stats['training_pairs']}"
)

print()
print("📄 Создано:")
print(f"  {OUTPUT_CLEAN}")
print(f"  {OUTPUT_TRAIN}")
print(f"  {OUTPUT_STATS}")