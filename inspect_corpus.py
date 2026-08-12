import urllib.request
from urllib.parse import quote
from bs4 import BeautifulSoup


WORD = "мукъане"
URL = "https://paydadosh.ru/corpus?q=" + quote(WORD)

request = urllib.request.Request(
    URL,
    headers={
        "User-Agent": "Mozilla/5.0"
    }
)

with urllib.request.urlopen(request, timeout=30) as response:
    html = response.read()

soup = BeautifulSoup(html, "html.parser")

# Ищем все элементы, содержащие точные предложения
sentences = [
    "Из малув-мукъане хой хьона?!",
    "ХӀанз мукъане салаӀа воаллий-те ше а, нахага а салоӀийтий-те?",
    "ГӀаьхь мукъане волий?"
]

print("=" * 70)
print("ПОИСК HTML ЭЛЕМЕНТОВ")
print("=" * 70)

for sentence in sentences:
    print("\n" + "-" * 70)
    print("Ищем:", sentence)

    element = soup.find(
        string=lambda text: text and sentence in text
    )

    if not element:
        print("❌ Не найдено")
        continue

    print("✅ Найдено")
    print("TAG:", element.parent.name)

    print("\nРодитель:")
    print(element.parent.prettify()[:5000])

    # Несколько родителей выше
    parent = element.parent

    for level in range(1, 6):
        if parent.parent:
            parent = parent.parent

        print("\n" + "=" * 40)
        print("УРОВЕНЬ", level)
        print("TAG:", parent.name)
        print("CLASS:", parent.get("class"))
        print("=" * 40)

        print(parent.prettify()[:5000])