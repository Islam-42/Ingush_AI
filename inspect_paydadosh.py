import urllib.request
from bs4 import BeautifulSoup
from urllib.parse import urljoin


URL = "https://paydadosh.ru/word/105034-%D0%B4%D0%BE%D1%82%D1%82%D0%B0%D0%B3%D3%8F"


def get_page(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
            )
        },
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read()


html = get_page(URL)

soup = BeautifulSoup(html, "html.parser")

print("Размер HTML:", len(html))
print()

print("===== ССЫЛКИ НА /word/ =====")

count = 0

for a in soup.find_all("a", href=True):

    href = a["href"]

    if "/word/" not in href:
        continue

    text = " ".join(
        a.get_text(" ", strip=True).split()
    )

    full_url = urljoin(URL, href)

    print()
    print("Текст:", repr(text))
    print("URL:", full_url)

    count += 1

    if count >= 50:
        break


print()
print("Всего найдено первых ссылок:", count)


print()
print("===== ФОРМЫ =====")

for form in soup.find_all("form"):

    print()
    print("ACTION:", form.get("action"))
    print("METHOD:", form.get("method"))

    for inp in form.find_all(["input", "button"]):

        print(
            " ",
            inp.name,
            "name=", inp.get("name"),
            "type=", inp.get("type"),
            "value=", inp.get("value"),
            "placeholder=", inp.get("placeholder"),
        )
