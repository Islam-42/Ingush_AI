from pathlib import Path
import subprocess

PDF = Path("knowledge/ГIалгIай мотт. 3 класс (2017).pdf")
OUTPUT = Path("ocr_book")

OUTPUT.mkdir(exist_ok=True)

print(f"📖 Учебник: {PDF.name}")
print("🔍 Начинаю OCR...\n")

# Получаем количество страниц
result = subprocess.run(
    ["pdfinfo", str(PDF)],
    capture_output=True,
    text=True
)

pages = None

for line in result.stdout.splitlines():
    if line.startswith("Pages:"):
        pages = int(line.split(":")[1].strip())
        break

if pages is None:
    print("❌ Не удалось определить количество страниц.")
    exit()

print(f"📄 Всего страниц: {pages}\n")

for page in range(1, pages + 1):

    output_file = OUTPUT / f"page_{page:03d}.txt"

    # Если страница уже обработана — пропускаем
    if output_file.exists():
        print(f"⏭️ Страница {page}/{pages} уже готова")
        continue

    image_prefix = OUTPUT / f"page_{page:03d}"

    print(f"🔄 Обрабатываю страницу {page}/{pages}...")

    # PDF → PNG
    subprocess.run(
        [
            "pdftoppm",
            "-f", str(page),
            "-singlefile",
            "-png",
            "-r", "300",
            str(PDF),
            str(image_prefix)
        ],
        check=True
    )

    image_file = Path(str(image_prefix) + ".png")

    # PNG → TXT
    subprocess.run(
        [
            "tesseract",
            str(image_file),
            str(image_prefix),
            "-l", "rus"
        ],
        check=True
    )

    generated_txt = Path(str(image_prefix) + ".txt")

    if generated_txt.exists():
        generated_txt.rename(output_file)

    # Удаляем тяжёлую картинку
    if image_file.exists():
        image_file.unlink()

print("\n✅ OCR завершён!")