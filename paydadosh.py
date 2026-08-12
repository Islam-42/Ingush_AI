import urllib.request
import urllib.parse
import re
from bs4 import BeautifulSoup


BASE_URL = "https://paydadosh.ru"


def normalize_word(word):
    """Приводим ингушское слово к единому виду."""
    word = word.lower().strip()

    # Разные варианты ингушского Ӏ
    word = word.replace("ӏ", "Ӏ")
    word = word.replace("i", "Ӏ")

    # Убираем лишние пробелы
    word = re.sub(r"\s+", " ", word)

    return word


def get_page(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 Chrome/138 Safari/537.36"
            ),
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        },
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read()


def get_search_results(word):
    """Получаем все ссылки /word/ со страницы поиска."""

    encoded = urllib.parse.quote(word)

    url = f"{BASE_URL}/?q={encoded}"

    print(f"🌐 URL поиска:")
    print(url)

    html = get_page(url)
    soup = BeautifulSoup(html, "html.parser")

    results = []

    for a in soup.find_all("a", href=True):

        href = a["href"]

        if not href.startswith("/word/"):
            continue

        text = " ".join(a.stripped_strings)

        if not text:
            continue

        full_url = urllib.parse.urljoin(BASE_URL, href)

        results.append({
            "text": text,
            "url": full_url,
        })

    # Убираем дубликаты
    unique = []

    seen = set()

    for item in results:
        if item["url"] not in seen:
            seen.add(item["url"])
            unique.append(item)

    return unique


def extract_word_from_url(url):
    """
    Извлекает слово из URL.

    Например:
    /word/105034-доттагӀа
    """

    match = re.search(r"/word/\d+-(.+)$", url)

    if not match:
        return ""

    slug = match.group(1)

    # Иногда в URL могут быть дополнительные слова
    slug = urllib.parse.unquote(slug)

    return slug


def find_card(word):
    """Ищем карточку слова на PaydaDosh."""

    normalized_target = normalize_word(word)

    results = get_search_results(word)

    print()
    print(f"🔎 Найдено ссылок: {len(results)}")

    # Показываем найденные ссылки для отладки
    for i, item in enumerate(results):
        print(f"[{i}] {item['text']}")
        print(f"    {item['url']}")

    # -------------------------------------------------
    # 1. Проверяем каждую ссылку
    # -------------------------------------------------

    for item in results:

        url_word = extract_word_from_url(item["url"])

        if not url_word:
            continue

        normalized_url = normalize_word(url_word)

        # В URL может быть:
        #
        # доттагӀа-доттагӀачо-доттагӀий
        #
        # поэтому берём первую часть slug
        first_part = normalized_url.split("-")[0]

        if first_part == normalized_target:
            return item["url"]

    # -------------------------------------------------
    # 2. Ищем слово непосредственно в slug
    # -------------------------------------------------

    for item in results:

        url_word = extract_word_from_url(item["url"])

        if not url_word:
            continue

        normalized_url = normalize_word(url_word)

        if normalized_url.startswith(normalized_target + "-"):
            return item["url"]

    # -------------------------------------------------
    # 3. Ищем слово в тексте ссылки
    # -------------------------------------------------

    for item in results:

        text = normalize_word(item["text"])

        if text == normalized_target:
            return item["url"]

    # -------------------------------------------------
    # 4. Частичное совпадение
    # -------------------------------------------------

    for item in results:

        url_word = normalize_word(
            extract_word_from_url(item["url"])
        )

        if normalized_target in url_word:
            return item["url"]

    return None


def parse_card(url, requested_word):
    """Открываем карточку и достаём перевод."""

    print()
    print("📖 Открываем карточку:")
    print(url)

    html = get_page(url)

    soup = BeautifulSoup(html, "html.parser")

    # TITLE
    title = soup.title.get_text(" ", strip=True) if soup.title else ""

    print()
    print("TITLE:")
    print(title)

    # Ищем наиболее вероятный заголовок страницы
    headings = []

    for tag in soup.find_all(["h1", "h2", "h3"]):

        text = " ".join(tag.stripped_strings)

        if text:
            headings.append(text)

    print()
    print("ЗАГОЛОВКИ:")

    for h in headings[:20]:
        print("-", h)

    # Главный способ:
    # TITLE обычно выглядит:
    # ДоттагӀа — друг, побратим, товарищ...
    translation = None

    if title:
        parts = title.split("—", 1)

        if len(parts) == 2:

            title_word = normalize_word(parts[0])

            if (
                title_word == normalize_word(requested_word)
                or normalize_word(requested_word) in title_word
            ):
                translation = parts[1].strip()

    # Если TITLE не подошёл — ищем h1
    if not translation:

        for heading in headings:

            if "—" not in heading:
                continue

            left, right = heading.split("—", 1)

            if normalize_word(left) == normalize_word(requested_word):

                translation = right.strip()
                break

    return {
        "word": requested_word,
        "translation": translation,
        "url": url,
        "title": title,
    }


def main():

    word = input("🔎 Введите ингушское слово: ").strip()

    if not word:
        print("❌ Слово не введено")
        return

    print()
    print(f"🔎 Ищем: {word}")
    print("🌐 Ищем карточку на PaydaDosh...")

    try:
        card_url = find_card(word)

    except Exception as e:

        print()
        print("❌ Ошибка поиска:")
        print(e)

        return

    if not card_url:

        print()
        print("❌ Точная карточка не найдена.")

        return

    print()
    print("✅ Карточка найдена:")
    print(card_url)

    try:
        result = parse_card(card_url, word)

    except Exception as e:

        print()
        print("❌ Ошибка загрузки карточки:")
        print(e)

        return

    print()
    print("==============================")
    print("        РЕЗУЛЬТАТ")
    print("==============================")

    print(f"Слово: {result['word']}")

    if result["translation"]:
        print(f"Перевод: {result['translation']}")
    else:
        print("Перевод: ❌ не найден")

    print(f"URL: {result['url']}")


if __name__ == "__main__":
    main()