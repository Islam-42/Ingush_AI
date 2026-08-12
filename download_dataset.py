from datasets import load_dataset
import json
from pathlib import Path


DATASET = "lingtrain/ingush-russian"

OUTPUT = Path("rag/ingush_russian.jsonl")


print("=" * 60)
print("🇮🇳 INGUSH AI DATASET")
print("=" * 60)

print()
print("📥 Загружаем русско-ингушский корпус...")

dataset = load_dataset(
    DATASET,
    split="train"
)

print(
    f"✅ Загружено строк: {len(dataset)}"
)

print()
print("🔎 Поля датасета:")
print(dataset.column_names)

OUTPUT.parent.mkdir(
    exist_ok=True
)

count = 0

with open(
    OUTPUT,
    "w",
    encoding="utf-8"
) as f:

    for row in dataset:

        ingush = str(
            row.get(
                "ing",
                ""
            )
        ).strip()

        russian = str(
            row.get(
                "ru",
                ""
            )
        ).strip()

        if not ingush:
            continue

        if not russian:
            continue

        item = {
            "ingush": ingush,
            "russian": russian
        }

        f.write(
            json.dumps(
                item,
                ensure_ascii=False
            )
            + "\n"
        )

        count += 1


print()
print(
    f"✅ Сохранено пар: {count}"
)

print(
    f"📁 Файл: {OUTPUT}"
)

print()
print("=" * 60)

# Показываем первые 5

print()
print("📖 ПЕРВЫЕ ПРИМЕРЫ:")
print()

with open(
    OUTPUT,
    "r",
    encoding="utf-8"
) as f:

    for i in range(5):

        line = f.readline()

        if not line:
            break

        item = json.loads(line)

        print(
            f"🇮🇳 {item['ingush']}"
        )

        print(
            f"🇷🇺 {item['russian']}"
        )

        print("-" * 60)