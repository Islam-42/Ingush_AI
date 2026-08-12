from pathlib import Path

folder = Path("ocr_book")
files = sorted(folder.glob("page_*.txt"))

empty = []
short = []

for file in files:
    text = file.read_text(encoding="utf-8", errors="ignore").strip()
    chars = len(text)

    if chars == 0:
        empty.append(file.name)
    elif chars < 100:
        short.append((file.name, chars))

print(f"Всего страниц: {len(files)}")
print(f"Пустых страниц: {len(empty)}")
print(f"Очень коротких страниц: {len(short)}")

if empty:
    print("\nПустые страницы:")
    print(", ".join(empty))

if short:
    print("\nОчень короткие страницы:")
    for name, chars in short:
        print(f"{name}: {chars} символов")