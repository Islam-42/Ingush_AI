from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# Загружаем страницы учебника
folder = Path("ocr_book")
files = sorted(folder.glob("page_*.txt"))

documents = []

for file in files:
    text = file.read_text(encoding="utf-8", errors="ignore").strip()

    if text:
        documents.append({
            "page": file.stem,
            "text": text
        })

print(f"Загружено страниц: {len(documents)}")


# Создаём TF-IDF индекс
texts = [doc["text"] for doc in documents]

vectorizer = TfidfVectorizer(
    lowercase=True,
    ngram_range=(1, 2)
)

matrix = vectorizer.fit_transform(texts)

print("Индекс создан!")
print("Можно задавать вопросы.")
print("Для выхода напиши: exit\n")


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

    # Получаем 3 наиболее похожие страницы
    best_indexes = similarities.argsort()[-3:][::-1]

    print("\n📚 Найдено:\n")

    for index in best_indexes:
        score = similarities[index]

        print(
            f"--- {documents[index]['page']} "
            f"(сходство: {score:.3f}) ---"
        )

        print(documents[index]["text"][:1000])
        print()