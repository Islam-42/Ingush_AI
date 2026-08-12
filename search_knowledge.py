from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# =========================
# Загружаем учебник
# =========================

textbook = Path("textbook.txt").read_text(
    encoding="utf-8",
    errors="ignore"
)

# =========================
# Загружаем словарь
# =========================

dictionary = Path("dictionary.txt").read_text(
    encoding="utf-8",
    errors="ignore"
)


# =========================
# Разбиваем документы
# =========================

documents = []


# Учебник разбиваем по страницам
for part in textbook.split("===== СТРАНИЦА "):

    if part.strip():
        documents.append({
            "source": "Учебник",
            "text": part
        })


# Словарь тоже разбиваем по страницам
for part in dictionary.split("===== СТРАНИЦА "):

    if part.strip():
        documents.append({
            "source": "Словарь",
            "text": part
        })


print(f"Загружено документов: {len(documents)}")


# =========================
# Создаём TF-IDF
# =========================

texts = [
    document["text"]
    for document in documents
]

vectorizer = TfidfVectorizer(
    lowercase=True,
    ngram_range=(1, 2),
    min_df=1
)

matrix = vectorizer.fit_transform(texts)

print("Индекс создан!")
print("Можно задавать вопросы.")
print("Для выхода напиши: exit\n")


# =========================
# Поиск
# =========================

while True:

    query = input("🔎 Вопрос: ").strip()

    if query.lower() == "exit":
        break

    if not query:
        continue

    query_vector = vectorizer.transform([query])

    similarities = cosine_similarity(
        query_vector,
        matrix
    )[0]

    best_indexes = similarities.argsort()[-5:][::-1]

    print("\n📚 НАЙДЕНО:\n")

    for index in best_indexes:

        score = similarities[index]

        document = documents[index]

        print(
            f"--- {document['source']} "
            f"(сходство: {score:.3f}) ---"
        )

        print(
            document["text"][:1500]
        )

        print("\n" + "=" * 60 + "\n")