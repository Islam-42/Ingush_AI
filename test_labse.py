import json
from sentence_transformers import SentenceTransformer


MODEL_NAME = "lingtrain/labse-ingush"
DATASET_FILE = "rag/ingush_russian.jsonl"


print("=" * 60)
print("🇮🇳 INGUSH AI — LABSE TEST")
print("=" * 60)

print()
print("🧠 Загружаем модель...")

model = SentenceTransformer(
    MODEL_NAME
)

print("✅ Модель загружена")

print()
print("📚 Загружаем корпус...")

sentences = []

with open(
    DATASET_FILE,
    "r",
    encoding="utf-8"
) as f:

    for line in f:

        if not line.strip():
            continue

        item = json.loads(line)

        sentences.append(item)


print(
    f"✅ Загружено предложений: "
    f"{len(sentences)}"
)


print()
print("🔢 Создаём embeddings...")

texts = [
    item["ingush"]
    for item in sentences
]

embeddings = model.encode(
    texts,
    normalize_embeddings=True,
    show_progress_bar=True
)

print()
print(
    "✅ Embeddings созданы"
)

print(
    "Размер:",
    embeddings.shape
)


# ============================================================
# ПРОСТОЙ ТЕСТ
# ============================================================

query = input(
    "\n🇮🇳 Введи ингушское предложение: "
).strip()


if not query:

    print("Пустой запрос.")

    exit()


print()
print("🔎 Ищем похожие предложения...")


query_embedding = model.encode(
    [query],
    normalize_embeddings=True
)[0]


# cosine similarity
scores = embeddings @ query_embedding


# Индексы лучших результатов
top_indices = scores.argsort()[-5:][::-1]


print()
print("=" * 60)
print("🔎 НАИБОЛЕЕ ПОХОЖИЕ:")
print("=" * 60)


for position, index in enumerate(
    top_indices,
    1
):

    item = sentences[index]

    score = scores[index]

    print()

    print(
        f"#{position} "
        f"similarity={score:.4f}"
    )

    print(
        "🇮🇳",
        item["ingush"]
    )

    print(
        "🇷🇺",
        item["russian"]
    )

    print("-" * 60)