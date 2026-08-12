import urllib.request
import urllib.parse
import re
import json
import csv
import os
import time
from bs4 import BeautifulSoup


BASE_URL = "https://paydadosh.ru"

SITEMAP_INDEX_URL = f"{BASE_URL}/sitemap.xml"

OUTPUT_JSON = "ingush_dictionary.json"
OUTPUT_CSV = "ingush_dictionary.csv"
PROGRESS_FILE = "progress.json"

REQUEST_DELAY = 0.3
TIMEOUT = 30
MAX_RETRIES = 3


# =========================================================
# URL / HTTP
# =========================================================

def encode_url(url):
    """
    Превращает кириллицу и другие Unicode-символы
    в корректный percent-encoded URL.
    """

    parsed = urllib.parse.urlsplit(url)

    path = urllib.parse.quote(
        parsed.path,
        safe="/:@"
    )

    query = urllib.parse.quote(
        parsed.query,
        safe="=&"
    )

    return urllib.parse.urlunsplit(
        (
            parsed.scheme,
            parsed.netloc,
            path,
            query,
            parsed.fragment,
        )
    )


def get_page(url):
    """
    Загружает страницу с повторными попытками.
    """

    encoded_url = encode_url(url)

    request = urllib.request.Request(
        encoded_url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 Chrome/138 Safari/537.36"
            ),
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,*/*;q=0.8"
            ),
        },
    )

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):

        try:

            with urllib.request.urlopen(
                request,
                timeout=TIMEOUT
            ) as response:

                return response.read()

        except Exception as e:

            last_error = e

            if attempt < MAX_RETRIES:

                print(
                    f"      ⚠️ Повторная попытка "
                    f"{attempt}/{MAX_RETRIES - 1}"
                )

                time.sleep(2)

    raise last_error


# =========================================================
# SITEMAP
# =========================================================

def extract_sitemap_urls(html):
    """
    Извлекает URL из XML sitemap.
    """

    text = html.decode("utf-8", errors="ignore")

    urls = re.findall(
        r"<loc>\s*(.*?)\s*</loc>",
        text,
        re.DOTALL
    )

    return [
        urllib.parse.unquote(url.strip())
        for url in urls
    ]


def get_sitemap_parts():
    """
    Находит все sitemap, содержащие слова.
    """

    print("🌐 Загружаем главный sitemap...")

    try:

        html = get_page(SITEMAP_INDEX_URL)

    except Exception as e:

        print("❌ Не удалось загрузить sitemap.xml")
        print(e)

        return []

    urls = extract_sitemap_urls(html)

    print(f"📦 Найдено sitemap: {len(urls)}")

    word_sitemaps = []

    for url in urls:

        if "sitemap-words" in url:
            word_sitemaps.append(url)

    # Если sitemap.xml не является индексом,
    # пробуем искать sitemap-words напрямую.

    if not word_sitemaps:

        print("⚠️ В sitemap.xml sitemap слов не найден.")

        # Проверяем первые 50 возможных частей
        for i in range(1, 51):

            url = f"{BASE_URL}/sitemap-words/{i}.xml"

            try:

                html = get_page(url)

                found = extract_sitemap_urls(html)

                if found:

                    word_sitemaps.append(url)

                    print(
                        f"   + sitemap-words/{i}.xml"
                    )

            except Exception:
                pass

    # Убираем дубликаты

    unique = []

    seen = set()

    for url in word_sitemaps:

        if url not in seen:

            seen.add(url)
            unique.append(url)

    return unique


def collect_word_urls():
    """
    Собирает URL всех слов из всех sitemap.
    """

    sitemaps = get_sitemap_parts()

    if not sitemaps:

        print("❌ Sitemap слов не найден.")

        return []

    print()
    print("📚 Sitemap слов:")

    for url in sitemaps:
        print("   ", url)

    all_urls = []

    seen = set()

    print()
    print("🔎 Собираем URL слов...")

    for sitemap_url in sitemaps:

        print()
        print(f"📄 {sitemap_url}")

        try:

            html = get_page(sitemap_url)

            urls = extract_sitemap_urls(html)

            print(
                f"   Найдено: {len(urls)}"
            )

            for url in urls:

                if "/word/" not in url:
                    continue

                if url not in seen:

                    seen.add(url)
                    all_urls.append(url)

        except Exception as e:

            print(
                f"   ❌ Ошибка: {e}"
            )

    print()
    print(
        f"✅ Всего уникальных URL слов: "
        f"{len(all_urls)}"
    )

    return all_urls


# =========================================================
# NORMALIZATION
# =========================================================

def normalize_word(word):

    word = word.lower().strip()

    word = word.replace("ӏ", "Ӏ")

    word = word.replace("i", "Ӏ")

    word = re.sub(
        r"\s+",
        " ",
        word
    )

    return word


# =========================================================
# PARSING
# =========================================================

def get_text(element):

    if not element:
        return ""

    return " ".join(
        element.stripped_strings
    )


def parse_title(title):

    if not title:
        return "", ""

    if "—" not in title:
        return title.strip(), ""

    left, right = title.split(
        "—",
        1
    )

    # Убираем хвост сайта

    translation = right.split(
        "|",
        1
    )[0].strip()

    return (
        left.strip(),
        translation
    )


def parse_card(url):

    html = get_page(url)

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    # -----------------------------------------------------
    # TITLE
    # -----------------------------------------------------

    title = ""

    if soup.title:

        title = get_text(
            soup.title
        )

    word_from_title, translation = parse_title(
        title
    )

    # -----------------------------------------------------
    # H1
    # -----------------------------------------------------

    h1 = ""

    tag = soup.find("h1")

    if tag:
        h1 = get_text(tag)

    word = h1 or word_from_title

    # -----------------------------------------------------
    # BODY
    # -----------------------------------------------------

    body_text = ""

    if soup.body:

        body_text = get_text(
            soup.body
        )

    # -----------------------------------------------------
    # META DESCRIPTION
    # -----------------------------------------------------

    description = ""

    meta = soup.find(
        "meta",
        attrs={
            "name": "description"
        }
    )

    if meta:

        description = meta.get(
            "content",
            ""
        ).strip()

    # -----------------------------------------------------
    # ЧАСТЬ РЕЧИ
    # -----------------------------------------------------

    part_of_speech = ""

    # Ищем распространённые обозначения

    possible_pos = [
        "сущ.",
        "гл.",
        "прил.",
        "нареч.",
        "мест.",
        "част.",
        "числ.",
        "предл.",
        "союз",
        "частица",
        "межд.",
        "нар.",
    ]

    for pos in possible_pos:

        if re.search(
            rf"\b{re.escape(pos)}\b",
            body_text,
            re.IGNORECASE
        ):

            part_of_speech = pos
            break

    # -----------------------------------------------------
    # СОХРАНЯЕМ
    # -----------------------------------------------------

    return {

        "word": word,

        "translation": translation,

        "part_of_speech": part_of_speech,

        "description": description,

        "url": url,

        "title": title,

    }


# =========================================================
# PROGRESS
# =========================================================

def load_progress():

    if not os.path.exists(
        PROGRESS_FILE
    ):

        return {
            "last_index": 0
        }

    try:

        with open(
            PROGRESS_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception:

        return {
            "last_index": 0
        }


def save_progress(index):

    with open(
        PROGRESS_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            {
                "last_index": index
            },
            f,
            ensure_ascii=False,
            indent=2
        )


# =========================================================
# DATABASE
# =========================================================

def load_dictionary():

    if not os.path.exists(
        OUTPUT_JSON
    ):

        return []

    try:

        with open(
            OUTPUT_JSON,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception:

        return []


def save_dictionary(data):

    # JSON

    with open(
        OUTPUT_JSON,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )

    # CSV

    with open(
        OUTPUT_CSV,
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=[
                "word",
                "translation",
                "part_of_speech",
                "description",
                "url",
                "title",
            ]
        )

        writer.writeheader()

        writer.writerows(data)


# =========================================================
# MAIN
# =========================================================

def main():

    print("=" * 70)
    print("      ИНГУШСКИЙ СЛОВАРЬ — PaydaDosh")
    print("=" * 70)

    # -----------------------------------------------------
    # 1. Sitemap
    # -----------------------------------------------------

    urls = collect_word_urls()

    if not urls:

        return

    # -----------------------------------------------------
    # ВРЕМЕННО: тест
    # -----------------------------------------------------

    TEST_MODE = False
    TEST_LIMIT = 5
    
    if TEST_MODE:

        urls = urls[:5]

        print()
        print(
            "🧪 ТЕСТОВЫЙ РЕЖИМ: "
            "обрабатываем только 5 слов"
        )

    # -----------------------------------------------------
    # 2. Progress
    # -----------------------------------------------------

    progress = load_progress()

    start_index = progress.get(
        "last_index",
        0
    )

    if start_index >= len(urls):

        start_index = 0

    # -----------------------------------------------------
    # 3. Existing data
    # -----------------------------------------------------

    dictionary = load_dictionary()

    print()
    print(
        f"📚 Уже сохранено слов: "
        f"{len(dictionary)}"
    )

    print(
        f"▶ Начинаем с позиции: "
        f"{start_index + 1}"
    )

    # -----------------------------------------------------
    # 4. Collect
    # -----------------------------------------------------

    for index in range(
        start_index,
        len(urls)
    ):

        url = urls[index]

        print()
        print("=" * 70)

        print(
            f"[{index + 1}/{len(urls)}]"
        )

        print(
            f"URL: {url}"
        )

        try:

            result = parse_card(
                url
            )

            print(
                f"Слово: "
                f"{result['word']}"
            )

            print(
                f"Перевод: "
                f"{result['translation']}"
            )

            dictionary.append(
                result
            )

            save_dictionary(
                dictionary
            )

            save_progress(
                index + 1
            )

            print(
                "💾 Сохранено"
            )

        except KeyboardInterrupt:

            print()
            print(
                "🛑 Остановлено пользователем"
            )

            save_dictionary(
                dictionary
            )

            save_progress(
                index
            )

            print(
                "💾 Прогресс сохранён."
            )

            return

        except Exception as e:

            print()
            print(
                f"❌ Ошибка: {e}"
            )

            # Даже ошибочный URL пропускаем,
            # чтобы сборщик не застрял.

            save_progress(
                index + 1
            )

        time.sleep(
            REQUEST_DELAY
        )

    print()
    print("=" * 70)

    print(
        "🎉 СБОР ЗАВЕРШЁН"
    )

    print(
        f"📚 Всего слов: "
        f"{len(dictionary)}"
    )

    print(
        f"📄 JSON: "
        f"{OUTPUT_JSON}"
    )

    print(
        f"📄 CSV: "
        f"{OUTPUT_CSV}"
    )


if __name__ == "__main__":
    main()