import asyncio
import json
import os
import re
from collections import defaultdict, deque

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from dotenv import load_dotenv
from openai import AsyncOpenAI


# ============================================================
# НАСТРОЙКИ
# ============================================================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

DICTIONARY_FILE = "ingush_dictionary_clean.json"

AI_MODEL = "openrouter/free"

# Сколько сообщений помнить для каждого пользователя
MAX_HISTORY = 12


# ============================================================
# ПРОВЕРКА
# ============================================================

if not BOT_TOKEN:
    raise RuntimeError(
        "❌ BOT_TOKEN не найден в .env"
    )

if not OPENROUTER_API_KEY:
    raise RuntimeError(
        "❌ OPENROUTER_API_KEY не найден в .env"
    )


# ============================================================
# TELEGRAM
# ============================================================

bot = Bot(
    token=BOT_TOKEN
)

dp = Dispatcher()


# ============================================================
# OPENROUTER
# ============================================================

client = AsyncOpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
    timeout=60.0,
    max_retries=2,
)


# ============================================================
# ПАМЯТЬ ДИАЛОГОВ
# ============================================================

user_histories = defaultdict(
    lambda: deque(
        maxlen=MAX_HISTORY
    )
)


# ============================================================
# НОРМАЛИЗАЦИЯ
# ============================================================

def normalize(text: str) -> str:

    if not text:
        return ""

    text = text.strip().lower()

    replacements = {
        "Ӏ": "ӏ",
        "I": "ӏ",
        "І": "ӏ",
        "i": "ӏ",
        "1": "ӏ",
        "[": "ӏ",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


# ============================================================
# ЗАГРУЗКА СЛОВАРЯ
# ============================================================

print("=" * 60)
print("🇮🇳 INGUSH AI")
print("=" * 60)

print("📚 Загружаем ингушский словарь...")


try:

    with open(
        DICTIONARY_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        dictionary = json.load(f)


except FileNotFoundError:

    raise RuntimeError(
        f"❌ Файл {DICTIONARY_FILE} не найден."
    )


except json.JSONDecodeError as e:

    raise RuntimeError(
        f"❌ Ошибка JSON-файла: {e}"
    )


except Exception as e:

    raise RuntimeError(
        f"❌ Ошибка загрузки словаря: {e}"
    )


print(
    f"✅ Загружено записей: {len(dictionary)}"
)


# ============================================================
# ИНГУШСКИЙ ИНДЕКС
# ============================================================

print("🔎 Создаём ингушский индекс...")

dictionary_index = {}


for entry in dictionary:

    if not isinstance(entry, dict):
        continue

    word = entry.get(
        "word",
        ""
    )

    if not isinstance(word, str):
        continue

    word = word.strip()

    if not word:
        continue

    key = normalize(word)

    if not key:
        continue

    dictionary_index.setdefault(
        key,
        []
    ).append(entry)


print(
    f"🇮🇳 Ингушских ключей: "
    f"{len(dictionary_index)}"
)


# ============================================================
# РУССКИЙ ИНДЕКС
# ============================================================

print("🔎 Создаём русский индекс...")

reverse_dictionary_index = {}


for entry in dictionary:

    if not isinstance(entry, dict):
        continue

    word = entry.get(
        "word",
        ""
    )

    if not isinstance(word, str):
        continue

    translations = entry.get(
        "translations",
        []
    )

    if not isinstance(
        translations,
        list
    ):
        continue

    for translation in translations:

        if not isinstance(
            translation,
            str
        ):
            continue

        # Разделяем:
        # красный, розовый
        # на отдельные значения

        parts = re.split(
            r"[,;/]",
            translation
        )

        for part in parts:

            part = part.strip()

            if not part:
                continue

            key = normalize(part)

            if not key:
                continue

            reverse_dictionary_index.setdefault(
                key,
                []
            )

            if entry not in reverse_dictionary_index[key]:

                reverse_dictionary_index[key].append(
                    entry
                )


print(
    f"🇷🇺 Русских ключей: "
    f"{len(reverse_dictionary_index)}"
)


# ============================================================
# ИЗВЛЕЧЕНИЕ СЛОВ
# ============================================================

def extract_words(text: str):

    if not text:
        return []

    return re.findall(
        r"[А-Яа-яЁёӀӏIІі0-9\[\]ʼ'’\-]+",
        text
    )


# ============================================================
# ПОИСК
# ============================================================

def search_ingush_exact(query: str):

    key = normalize(query)

    if not key:
        return []

    return dictionary_index.get(
        key,
        []
    )


def search_russian_exact(query: str):

    key = normalize(query)

    if not key:
        return []

    return reverse_dictionary_index.get(
        key,
        []
    )


# ============================================================
# ОПРЕДЕЛЕНИЕ ЯВНОГО ЗАПРОСА НА ПЕРЕВОД
# ============================================================

def is_translation_request(text: str):

    text_lower = text.lower().strip()

    patterns = [

        "переведи",
        "перевод",
        "как будет",
        "что значит",
        "что означает",
        "значение слова",
        "на ингушском",
        "по-ингушски",
        "по ингушски",
        "на русском",
        "по-русски",

        # возможные варианты на английском
        "translate",
        "meaning",

    ]

    return any(
        pattern in text_lower
        for pattern in patterns
    )


# ============================================================
# ПОИСК КОНКРЕТНОГО СЛОВА В ЗАПРОСЕ
# ============================================================

def find_translation_candidates(text: str):

    words = extract_words(text)

    ingush_results = []
    russian_results = []

    for word in words:

        if len(word) < 2:
            continue

        found_ingush = search_ingush_exact(
            word
        )

        for entry in found_ingush:

            if entry not in ingush_results:

                ingush_results.append(
                    entry
                )

        found_russian = search_russian_exact(
            word
        )

        for entry in found_russian:

            if entry not in russian_results:

                russian_results.append(
                    entry
                )

    return (
        ingush_results[:10],
        russian_results[:10]
    )


# ============================================================
# ФОРМИРОВАНИЕ ДАННЫХ СЛОВАРЯ
# ============================================================

def build_dictionary_context(
    entries
):

    if not entries:
        return ""

    context = []

    context.append(
        "Дополнительные сведения из словаря:"
    )

    for entry in entries[:8]:

        if not isinstance(
            entry,
            dict
        ):
            continue

        word = entry.get(
            "word",
            ""
        )

        translations = entry.get(
            "translations",
            []
        )

        descriptions = entry.get(
            "descriptions",
            []
        )

        context.append(
            f"\nСлово: {word}"
        )

        if isinstance(
            translations,
            list
        ) and translations:

            context.append(
                "Переводы: "
                + "; ".join(
                    str(x)
                    for x in translations[:10]
                )
            )

        if isinstance(
            descriptions,
            list
        ) and descriptions:

            context.append(
                "Описание: "
                + " ".join(
                    str(x)
                    for x in descriptions[:2]
                )
            )

    return "\n".join(
        context
    )


# ============================================================
# ПРЯМОЙ ПЕРЕВОД
# ============================================================

def make_ingush_to_russian_answer(
    entries
):

    if not entries:
        return None

    words = []
    translations = []

    for entry in entries:

        if not isinstance(
            entry,
            dict
        ):
            continue

        word = entry.get(
            "word",
            ""
        )

        if isinstance(
            word,
            str
        ):

            word = word.strip()

            if (
                word
                and word not in words
            ):

                words.append(
                    word
                )

        values = entry.get(
            "translations",
            []
        )

        if not isinstance(
            values,
            list
        ):
            continue

        for value in values:

            value = str(
                value
            ).strip()

            if (
                value
                and value not in translations
            ):

                translations.append(
                    value
                )

    if not words or not translations:
        return None

    answer = (
        f"🔎 <b>{words[0]}</b>\n\n"
        "🇷🇺 <b>Значения:</b>\n"
    )

    for translation in translations[:8]:

        answer += (
            f"• {translation}\n"
        )

    return answer.strip()


def make_russian_to_ingush_answer(
    entries
):

    if not entries:
        return None

    words = []

    for entry in entries:

        if not isinstance(
            entry,
            dict
        ):
            continue

        word = entry.get(
            "word",
            ""
        )

        if not isinstance(
            word,
            str
        ):
            continue

        word = word.strip()

        if (
            word
            and word not in words
        ):

            words.append(
                word
            )

    if not words:
        return None

    answer = (
        "🇮🇳 <b>На ингушском:</b>\n\n"
    )

    for word in words[:8]:

        answer += (
            f"• <b>{word}</b>\n"
        )

    return answer.strip()


# ============================================================
# СИСТЕМНЫЙ ПРОМПТ
# ============================================================

SYSTEM_PROMPT = """
Ты — Ingush AI.

Ты являешься AI-собеседником, который помогает людям
общаться и изучать ингушский язык.

ТВОЯ ГЛАВНАЯ ЗАДАЧА:

Не просто переводить отдельные слова.

Ты должен уметь:
- поддерживать разговор;
- понимать вопросы;
- отвечать на вопросы;
- объяснять вещи;
- помогать изучать ингушский язык;
- переводить;
- исправлять небольшие ошибки;
- продолжать предыдущую тему разговора.

============================================================
ЯЗЫК ОТВЕТА
============================================================

По умолчанию отвечай НА ИНГУШСКОМ.

Если пользователь пишет по-русски,
это НЕ означает, что нужно отвечать по-русски.

Наоборот:

если пользователь задаёт обычный вопрос на русском,
постарайся ответить на ингушском.

Если пользователь явно просит:
"ответь по-русски",
"на русском",
"переведи на русский",

тогда отвечай по-русски.

Если пользователь пишет на ингушском,
отвечай на ингушском.

============================================================
ПЕРЕВОД
============================================================

Если пользователь явно просит перевод:

"переведи..."
"как будет..."
"что значит..."
"как сказать..."
"на ингушском..."
"по-ингушски..."
"на русском..."

тогда используй данные словаря.

Если в словаре несколько значений,
не выбирай автоматически первое.

Покажи несколько подходящих вариантов.

============================================================
ИНГУШСКИЙ ЯЗЫК
============================================================

Очень важно:

НЕ ПРИДУМЫВАЙ слова и грамматические формы,
если не уверен.

Если предоставлены данные словаря,
используй их как основу.

Но не нужно вставлять словарную информацию
в каждый обычный разговор.

Словарь является справочным материалом.

============================================================
ОБЫЧНЫЙ РАЗГОВОР
============================================================

Если пользователь пишет:

"как дела?"

"что делаешь?"

"расскажи что-нибудь"

"кто ты?"

"поговори со мной"

и т.п.

НЕ нужно переводить эти сообщения.

Нужно нормально ответить на них.

Ответ должен быть на ингушском.

============================================================
КОНТЕКСТ
============================================================

Учитывай предыдущие сообщения пользователя
и свои предыдущие ответы.

Если пользователь продолжает предыдущую тему,
не начинай разговор заново.

============================================================
СТИЛЬ
============================================================

Отвечай естественно.

Не говори:

"Согласно данным словаря..."

"В переданных данных..."

"В JSON..."

"Согласно API..."

"Я нашёл..."

Не объясняй внутреннюю работу системы.

Не упоминай OpenRouter.

Не упоминай название внутренних файлов.

Не упоминай PaydaDosh.

============================================================
ВАЖНО
============================================================

Если ты не уверен в каком-либо ингушском слове,
лучше сказать, что не уверен,
чем придумать несуществующее слово.

Не выдавай выдуманный пример
за настоящий пример из источника.

Будь дружелюбным.

Не делай ответы чрезмерно длинными,
если пользователь не попросил подробно.

НЕ составляй предложения простым перечислением слов.
Ты должен понимать смысл сообщения пользователя и создавать
естественные, грамматически связанные предложения на ингушском.

Если пользователь пишет по-русски и просит ответить на ингушском —
сначала пойми смысл русского сообщения, затем сформулируй
естественный ответ на ингушском.

Если не уверен в каком-либо слове, лучше сформулируй предложение
проще, используя известную тебе ингушскую лексику.

Ответ должен выглядеть как нормальная речь человека,
а не как набор отдельных слов из словаря.
"""


# ============================================================
# AI
# ============================================================

async def ask_ai(
    user_id,
    user_message,
    dictionary_entries=None,
    force_russian=False
):

    if dictionary_entries is None:
        dictionary_entries = []

    dictionary_context = build_dictionary_context(
        dictionary_entries
    )

    system_prompt = SYSTEM_PROMPT

    if force_russian:

        system_prompt += """

В ЭТОМ СООБЩЕНИИ пользователь явно попросил
русский язык.

Поэтому ответь на русском.
"""

    if dictionary_context:

        system_prompt += (
            "\n\n"
            + dictionary_context
        )

    messages = [

        {
            "role": "system",
            "content": system_prompt,
        }

    ]

    # --------------------------------------------------------
    # История
    # --------------------------------------------------------

    history = user_histories[user_id]

    for item in history:

        messages.append(item)

    # --------------------------------------------------------
    # Текущее сообщение
    # --------------------------------------------------------

    messages.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    try:

        response = await client.chat.completions.create(

            model=AI_MODEL,

            messages=messages,

            temperature=0.35,

            max_tokens=700,

        )

        if not response.choices:

            return (
                "⚠️ AI не вернул ответ."
            )

        answer = (
            response
            .choices[0]
            .message
            .content
        )

        if not answer:

            return (
                "⚠️ AI не вернул текст ответа."
            )

        answer = answer.strip()

        # ----------------------------------------------------
        # Сохраняем диалог
        # ----------------------------------------------------

        history.append(
            {
                "role": "user",
                "content": user_message,
            }
        )

        history.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        return answer

    except Exception as e:

        print(
            "❌ Ошибка OpenRouter:",
            repr(e)
        )

        return (
            "⚠️ Не удалось получить ответ от AI.\n\n"
            "Попробуй ещё раз через несколько секунд."
        )


# ============================================================
# TELEGRAM HANDLER
# ============================================================

@dp.message()
async def handle_message(
    message: Message
):

    if not message.text:
        return

    user_text = message.text.strip()

    if not user_text:
        return

    user_id = message.from_user.id

    print()
    print("=" * 60)

    print(
        f"👤 Пользователь: "
        f"{user_text}"
    )

    try:

        # ====================================================
        # ПРОВЕРЯЕМ:
        # ЯВНО ЛИ ПОЛЬЗОВАТЕЛЬ ПРОСИТ ПЕРЕВОД?
        # ====================================================

        translation_request = (
            is_translation_request(
                user_text
            )
        )

        print(
            "🔄 Запрос перевода:",
            translation_request
        )

        # ====================================================
        # ЕСЛИ ЭТО ПЕРЕВОД
        # ====================================================

        if translation_request:

            (
                ingush_results,
                russian_results
            ) = find_translation_candidates(
                user_text
            )

            print(
                "🇮🇳 Ингушских совпадений:",
                len(ingush_results)
            )

            print(
                "🇷🇺 Русских совпадений:",
                len(russian_results)
            )

            # ------------------------------------------------
            # Если нашли ингушское слово
            # ------------------------------------------------

            if ingush_results:

                # Если запрос выглядит как:
                # "что значит доттагӀ"

                answer = (
                    make_ingush_to_russian_answer(
                        ingush_results
                    )
                )

                if answer:

                    await message.answer(
                        answer,
                        parse_mode="HTML"
                    )

                    print(
                        "✅ Словарный перевод "
                        "ингушский → русский"
                    )

                    return

            # ------------------------------------------------
            # Если нашли русское слово
            # ------------------------------------------------

            if russian_results:

                answer = (
                    make_russian_to_ingush_answer(
                        russian_results
                    )
                )

                if answer:

                    await message.answer(
                        answer,
                        parse_mode="HTML"
                    )

                    print(
                        "✅ Словарный перевод "
                        "русский → ингушский"
                    )

                    return

            # ------------------------------------------------
            # Если словарь не помог
            # ------------------------------------------------

            answer = await ask_ai(

                user_id=user_id,

                user_message=user_text,

                dictionary_entries=(
                    ingush_results
                    + russian_results
                ),

            )

            await message.answer(
                answer
            )

            return

        # ====================================================
        # ОБЫЧНЫЙ РАЗГОВОР
        # ====================================================

        (
            ingush_results,
            russian_results
        ) = find_translation_candidates(
            user_text
        )

        # ====================================================
        # ВАЖНО:
        #
        # НЕ отправляем русские совпадения
        # в качестве команды перевода.
        #
        # Они только дают AI дополнительный контекст.
        # ====================================================

        dictionary_results = []

        dictionary_results.extend(
            ingush_results[:5]
        )

        dictionary_results.extend(
            russian_results[:5]
        )

        print(
            "📚 Словарных подсказок:",
            len(dictionary_results)
        )

        # ====================================================
        # AI-СОБЕСЕДНИК
        # ====================================================

        answer = await ask_ai(

            user_id=user_id,

            user_message=user_text,

            dictionary_entries=dictionary_results,

        )

        await message.answer(
            answer
        )

        print(
            "✅ Ответ отправлен"
        )

    except Exception as e:

        print(
            "❌ Ошибка обработки:",
            repr(e)
        )

        try:

            await message.answer(
                "⚠️ Произошла ошибка "
                "при обработке сообщения."
            )

        except Exception:
            pass


# ============================================================
# MAIN
# ============================================================

async def main():

    print()
    print("=" * 60)

    print(
        "🇮🇳 INGUSH AI"
    )

    print("=" * 60)

    print(
        "🤖 Telegram бот запускается..."
    )

    print(
        f"📚 Словарь: "
        f"{DICTIONARY_FILE}"
    )

    print(
        f"📖 Записей: "
        f"{len(dictionary)}"
    )

    print(
        f"🇮🇳 Ингушских ключей: "
        f"{len(dictionary_index)}"
    )

    print(
        f"🇷🇺 Русских ключей: "
        f"{len(reverse_dictionary_index)}"
    )

    print(
        f"🧠 AI модель: "
        f"{AI_MODEL}"
    )

    print(
        f"💬 Память: "
        f"{MAX_HISTORY} сообщений"
    )

    print("=" * 60)
    print()

    # ========================================================
    # TELEGRAM
    # ========================================================

    try:

        me = await bot.get_me()

        print(
            f"✅ Telegram подключён: "
            f"@{me.username}"
        )

    except Exception as e:

        print(
            "❌ Не удалось подключиться "
            "к Telegram:",
            repr(e)
        )

        return

    # ========================================================
    # POLLING
    # ========================================================

    try:

        await dp.start_polling(
            bot
        )

    finally:

        await bot.session.close()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    asyncio.run(main())