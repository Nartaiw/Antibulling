import logging
import asyncio
import logging
import random
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.methods import DeleteWebhook
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from openai import OpenAI
from keep_alive import keep_alive

# ========== НАСТРОЙКИ (ВСТАВЬ СВОИ ДАННЫЕ) ==========
TOKEN = '8653619802:AAHVlY7GBl89CRrD8vsBXlfs6SMLHcBDZns'
API_KEY = 'sk-hedKmL95WT36pOWlDxlYtIK-hldUtBKSMqoOT1PKzcbY9Sh0Uin53TMISsaAukOe_GC4rIdAGdfTZ6wuy6nxcg'

# ========== ЛОГИРОВАНИЕ И ИНИЦИАЛИЗАЦИЯ ==========
logging.basicConfig(level=logging.INFO)
bot = Bot(TOKEN)
dp = Dispatcher()

# Хранилище данных пользователей
user_data = {}  # {user_id: {"language": "kk"/"ru"/"en", "problem_type": "bullying"/"cyberbullying", "mood": None, "test_step": 0, "answers": [], "diary": []}}

# ========== ТЕКСТЫ НА ТРЁХ ЯЗЫКАХ ==========
TEXTS = {
    "choose_language": {
        "kk": "🇰🇿 Тілді таңдаңыз:",
        "ru": "🇷🇺 Выберите язык:",
        "en": "🇬🇧 Choose language:"
    },
    "choose_problem_type": {
        "kk": "Қандай мәселе бойынша көмек керек?",
        "ru": "По какой проблеме нужна помощь?",
        "en": "What kind of problem do you need help with?"
    },
    "bullying_btn": {
        "kk": "🏫 Буллинг (мектепте)",
        "ru": "🏫 Буллинг (в школе)",
        "en": "🏫 Bullying (at school)"
    },
    "cyberbullying_btn": {
        "kk": "💻 Кибербуллинг (интернетте)",
        "ru": "💻 Кибербуллинг (в интернете)",
        "en": "💻 Cyberbullying (online)"
    },
    "welcome": {
        "kk": "🌟 Сәлем! Мен – психолог-бот, кибербуллинг пен буллингке қарсы көмектесемін.\n\nМенің мүмкіндіктерім:\n• Тыңдап, қолдау көрсету\n• Зорлық-зомбылыққа қарсы кеңестер\n• Мазасыздық деңгейіне тест\n• Тыныс алу жаттығулары\n• Көңіл-күй күнделігі\n\nТөмендегі батырмаларды пайдалан 👇",
        "ru": "🌟 Привет! Я – бот-психолог, помогаю справиться с буллингом и кибербуллингом.\n\nЯ умею:\n• Выслушать и поддержать\n• Дать советы по противодействию травле\n• Провести тест на тревожность\n• Научить дыхательным упражнениям\n• Вести дневник настроения\n\nИспользуй кнопки ниже 👇",
        "en": "🌟 Hello! I'm a psychologist bot that helps with bullying and cyberbullying.\n\nI can:\n• Listen and support\n• Give anti-bullying advice\n• Conduct an anxiety test\n• Teach breathing exercises\n• Keep a mood diary\n\nUse the buttons below 👇"
    },
    "bullying_quick_advice": {
        "kk": "⚠️ Бұл – буллинг. Сен кінәлі емессің.\n\nҚазір не істеуге болады:\n1️⃣ Агрессиямен жауап берме – бұл жағдайды нашарлатады.\n2️⃣ Қатты және қысқа айт: «Тоқта», «Маған ұнамайды».\n3️⃣ Жағдайдан кет (сыныптан шық, алыстап кет).\n4️⃣ **Ересек адамға айт** – ата-анаңа, мұғалімге, психологқа.\n\nТолығырақ кеңес керек пе?",
        "ru": "⚠️ Это буллинг. Ты не виноват(а).\n\nЧто можно сделать прямо сейчас:\n1️⃣ Не отвечай агрессией – это усугубит ситуацию.\n2️⃣ Скажи твёрдо и коротко: «Прекрати», «Мне это не нравится».\n3️⃣ Уйди из ситуации (выйди из класса, отойди).\n4️⃣ **Обязательно расскажи взрослому** – родителям, учителю, психологу.\n\nНужен более подробный совет?",
        "en": "⚠️ This is bullying. You are not guilty.\n\nWhat you can do right now:\n1️⃣ Don't respond with aggression – it makes it worse.\n2️⃣ Say firmly and shortly: 'Stop', 'I don't like it'.\n3️⃣ Leave the situation (leave the classroom, walk away).\n4️⃣ **Tell an adult** – your parents, teacher, school psychologist.\n\nNeed more detailed advice?"
    },
    "cyberbullying_quick_advice": {
        "kk": "⚠️ Бұл – кибербуллинг. Интернеттегі зорлық-зомбылыққа қарсы әрекет ету жоспары:\n\n1️⃣ **Жауап берме** – тролльдер назармен қоректенеді.\n2️⃣ **Скриншот жаса** – дәлелдерді сақта (күні мен уақытымен).\n3️⃣ **Бұғаттау және шағымдану** – әлеуметтік желілерде бұғаттап, шағым жібер.\n4️⃣ **Ересек адамға айт** – ата-анаңа немесе сенімді адамға.\n5️⃣ **Көмек сызықтары** – төмендегі батырмада ресурстар бар.\n\nҚосымша кеңес керек пе?",
        "ru": "⚠️ Это кибербуллинг. План действий против травли в интернете:\n\n1️⃣ **Не отвечай** – тролли питаются вниманием.\n2️⃣ **Сделай скриншот** – сохрани доказательства (с датой и временем).\n3️⃣ **Заблокируй и пожалуйся** – в соцсетях заблокируй обидчика и отправь жалобу.\n4️⃣ **Расскажи взрослому** – родителям или другому доверенному лицу.\n5️⃣ **Линии помощи** – в кнопке «Ресурсы» есть контакты.\n\nНужен более развёрнутый совет?",
        "en": "⚠️ This is cyberbullying. Action plan against online harassment:\n\n1️⃣ **Don't respond** – trolls feed on attention.\n2️⃣ **Take a screenshot** – save evidence (with date and time).\n3️⃣ **Block and report** – block the bully on social media and send a complaint.\n4️⃣ **Tell an adult** – parents or another trusted person.\n5️⃣ **Helplines** – the 'Resources' button has contacts.\n\nNeed more detailed advice?"
    },
    "resources": {
        "kk": "📞 **Көмек ресурстары:**\n\n• **Балалар сенім телефоны**: 8-800-2000-122 (тәулік бойы, анонимды)\n• **Төтенше жағдайлар қызметі**: 112\n• **Психологиялық қолдау чаты**: https://psi.mos.ru\n• **Мектеп психологы** – сынып жетекшісінен сұра\n\nЕсіңде болсын: көмек сұрау – бұл қалыпты және батылдық.",
        "ru": "📞 **Ресурсы помощи:**\n\n• **Детский телефон доверия**: 8-800-2000-122 (круглосуточно, анонимно)\n• **Единый номер экстренных служб**: 112\n• **Чат психологической поддержки**: https://psi.mos.ru\n• **Школьный психолог** – спроси у классного руководителя\n\nПомни: просить помощи – это нормально и смело.",
        "en": "📞 **Help resources:**\n\n• **Child helpline**: 8-800-2000-122 (24/7, anonymous)\n• **Emergency number**: 112\n• **Psychological support chat**: https://psi.mos.ru\n• **School psychologist** – ask your class teacher\n\nRemember: asking for help is normal and brave."
    },
    "breathing": {
        "kk": "🌬️ **«Шаршы» тыныс алу жаттығуы**\n\n1. Мұрынмен дем алу – 4 секунд\n2. Тынысты ұстау – 4 секунд\n3. Ауызбен дем шығару – 4 секунд\n4. Тынысты ұстау – 4 секунд\n\n5 рет қайтала. Өзіңе қамқор болғаның үшін кереметсің! 💚",
        "ru": "🌬️ **Дыхательное упражнение «Квадрат»**\n\n1. Вдох носом – 4 секунды\n2. Задержка дыхания – 4 секунды\n3. Выдох ртом – 4 секунды\n4. Задержка – 4 секунды\n\nПовтори 5 раз. Ты молодец, что заботишься о себе! 💚",
        "en": "🌬️ **'Square' breathing exercise**\n\n1. Inhale through nose – 4 seconds\n2. Hold breath – 4 seconds\n3. Exhale through mouth – 4 seconds\n4. Hold breath – 4 seconds\n\nRepeat 5 times. You're great for taking care of yourself! 💚"
    },
    "mood_question": {
        "kk": "📝 Қазір көңіл-күйің қалай? Таңда:",
        "ru": "📝 Как твоё настроение сейчас? Выбери:",
        "en": "📝 How is your mood right now? Choose:"
    },
    "mood_saved": {
        "kk": "Жазылды: сенің көңіл-күйің – {mood}. Өзіңе қамқор бол 💙",
        "ru": "Записано: твоё настроение – {mood}. Береги себя 💙",
        "en": "Saved: your mood is {mood}. Take care 💙"
    },
    "random_advice": {
        "kk": "💡 *Кездейсоқ кеңес:*\n{advice}",
        "ru": "💡 *Случайный совет:*\n{advice}",
        "en": "💡 *Random advice:*\n{advice}"
    },
    "stress_result": {
        "kk": "📊 Тест аяқталды!\n\n{result}\n\nӨзіңе уақыт бөлгеніңе рахмет 💙",
        "ru": "📊 Тест завершён!\n\n{result}\n\nСпасибо, что уделил время себе 💙",
        "en": "📊 Test completed!\n\n{result}\n\nThank you for taking time for yourself 💙"
    },
    "help_text": {
        "kk": "📖 **Менің мүмкіндіктерім:**\n\n• **Сөйлесу** – жағдайыңды жаз.\n• **Тыныс алу** – стреске қарсы жаттығу.\n• **Стресс-тест** – жағдайды тексеру.\n• **Ресурстар** – сенім телефондары.\n• **Көңіл-күй күнделігі** – сезіміңді жаз.\n• **Кездейсоқ кеңес** – қолдау.\n\nӨте ауыр болса, дереу **112** немесе **8-800-2000-122** нөмірлеріне қоңырау шал.",
        "ru": "📖 **Что я умею:**\n\n• **Просто поговорить** – напиши о своей ситуации.\n• **Дыхание** – антистресс-упражнение.\n• **Тест на стресс** – оценка состояния.\n• **Ресурсы** – телефоны доверия.\n• **Дневник настроения** – запиши чувства.\n• **Случайный совет** – поддержка.\n\nЕсли очень плохо, звони **112** или **8-800-2000-122**.",
        "en": "📖 **What I can do:**\n\n• **Just talk** – write about your situation.\n• **Breathing** – anti-stress exercise.\n• **Stress test** – assess your condition.\n• **Resources** – helplines.\n• **Mood diary** – write down your feelings.\n• **Random advice** – support.\n\nIf you're feeling very bad, call **112** or **8-800-2000-122**."
    }
}

# Списки советов для random_advice на трёх языках
RANDOM_ADVICE_LISTS = {
    "kk": [
        "🌟 Егер ренжіп тұрсаң – бүгін алғысың келетін үш нәрсені жаз.",
        "🧘 Терең тыныс алу мазасыздықты азайтады.",
        "📖 Күнделік жүргіз: эмоцияларыңды қағазға төк – бұл жеңілдетеді.",
        "👥 Сен жалғыз емессің. Көптеген балалар буллингке кездескен. Басқаруға болады, бастысы – үндемеу.",
        "🎨 Шығармашылықпен айналыс: сурет салу, музыка, мүсіндеу сөзбен айту қиын нәрсені білдіруге көмектеседі.",
        "🚶‍♀️ Таза ауада қысқа серуендеу миды ауыстырып, стрессті төмендетеді.",
        "💬 Өзіңе айт: «Мен күресе аламын. Менің күшім бар». Бұл аффирмация жұмыс істейді."
    ],
    "ru": [
        "🌟 Если тебе грустно – попробуй написать три вещи, за которые ты благодарен сегодня.",
        "🧘 Глубокий вдох и медленный выдох снижают тревогу прямо сейчас.",
        "📖 Веди дневник: выплёскивай эмоции на бумагу – это освобождает.",
        "👥 Ты не один. Миллионы детей сталкивались с буллингом. Справляться можно, главное – не молчать.",
        "🎨 Займись творчеством: рисунок, музыка, лепка помогают выразить то, что сложно сказать словами.",
        "🚶‍♀️ Короткая прогулка на свежем воздухе переключает мозг и снижает стресс.",
        "💬 Скажи себе: «Я справлюсь. У меня есть силы». Это аффирмация, она работает."
    ],
    "en": [
        "🌟 If you're sad – try writing three things you're grateful for today.",
        "🧘 A deep breath and slow exhale reduce anxiety right now.",
        "📖 Keep a diary: pour your emotions onto paper – it's freeing.",
        "👥 You are not alone. Millions of children have faced bullying. You can cope, the main thing is not to stay silent.",
        "🎨 Do something creative: drawing, music, sculpting helps express what's hard to say in words.",
        "🚶‍♀️ A short walk in fresh air resets your mind and reduces stress.",
        "💬 Tell yourself: 'I can handle this. I have strength.' This affirmation works."
    ]
}

# ========== КЛАВИАТУРЫ ==========
def get_language_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇰🇿 Қазақша", callback_data="lang_kk"),
         InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
         InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]
    ])
    return kb

def get_problem_type_keyboard(lang):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=TEXTS["bullying_btn"][lang], callback_data="type_bullying")],
        [InlineKeyboardButton(text=TEXTS["cyberbullying_btn"][lang], callback_data="type_cyberbullying")]
    ])
    return kb

def get_main_keyboard(lang, problem_type):
    # problem_type может быть "bullying" или "cyberbullying" – но кнопки одинаковые, просто текст общий
    # Тексты для кнопок берём из TEXTS, но они одинаковы для всех типов (кроме выбора типа)
    btn_help = TEXTS["help_text"][lang]  # используем как ярлык? Лучше создать отдельные тексты для кнопок
    # Создадим простые названия кнопок на трёх языках
    btn_texts = {
        "kk": ["🆘 Көмек", "🧘 Тыныс алу", "📊 Стресс-тест", "📚 Ресурстар", "📝 Көңіл-күй", "💡 Кеңес"],
        "ru": ["🆘 Помощь", "🧘 Дыхание", "📊 Тест на стресс", "📚 Ресурсы", "📝 Настроение", "💡 Совет"],
        "en": ["🆘 Help", "🧘 Breathing", "📊 Stress test", "📚 Resources", "📝 Mood", "💡 Advice"]
    }
    btns = btn_texts[lang]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=btns[0], callback_data="help"),
         InlineKeyboardButton(text=btns[1], callback_data="breathing")],
        [InlineKeyboardButton(text=btns[2], callback_data="stress_test"),
         InlineKeyboardButton(text=btns[3], callback_data="resources")],
        [InlineKeyboardButton(text=btns[4], callback_data="mood_diary"),
         InlineKeyboardButton(text=btns[5], callback_data="random_advice")]
    ])
    return kb

def get_stress_keyboard(lang):
    # Кнопки с цифрами одинаковы для всех языков
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1️⃣", callback_data="stress_1"),
         InlineKeyboardButton(text="2️⃣", callback_data="stress_2"),
         InlineKeyboardButton(text="3️⃣", callback_data="stress_3"),
         InlineKeyboardButton(text="4️⃣", callback_data="stress_4")]
    ])
    return kb

def get_mood_keyboard(lang):
    mood_texts = {
        "kk": ["😢 Жаман", "😐 Қалыпты", "😊 Жақсы"],
        "ru": ["😢 Плохое", "😐 Нормальное", "😊 Хорошее"],
        "en": ["😢 Bad", "😐 Normal", "😊 Good"]
    }
    moods = mood_texts[lang]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=moods[0], callback_data="mood_bad"),
         InlineKeyboardButton(text=moods[1], callback_data="mood_normal"),
         InlineKeyboardButton(text=moods[2], callback_data="mood_good")]
    ])
    return kb

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
async def get_ai_response(user_message: str, user_id: int, lang: str, problem_type: str) -> str:
    """Запрос к OpenAI с учётом языка и типа проблемы"""
    client = OpenAI(
        base_url="https://api.langdock.com/openai/eu/v1",
        api_key=API_KEY
    )
    # Базовый системный промпт с учётом типа проблемы
    if problem_type == "cyberbullying":
        problem_description = "кибербуллинг (травля в интернете, соцсетях, мессенджерах)."
        extra_advice = "Давай советы по кибербезопасности: скриншоты, блокировка, жалоба, не вступать в перепалку, сохранять доказательства."
    else:
        problem_description = "буллинг (травля в школе, классе, среди сверстников)."
        extra_advice = "Давай советы, как реагировать на агрессию вживую, к кому обратиться в школе."
    
    system_prompt = (
        f"Ты — эмпатичный, добрый и компетентный ИИ-психолог для школьников, столкнувшихся с {problem_description} "
        f"Твоя задача — помочь ребёнку справиться. Правила: "
        f"1) Выслушай и дай эмоциональную поддержку. Покажи, что ребёнок не виноват. "
        f"2) {extra_advice} "
        f"3) Всегда мягко рекомендуй обратиться к доверенному взрослому (родителям, учителю, психологу). "
        f"4) Если сообщение содержит суицидальные мысли — обязательно приведи телефоны доверия (8-800-2000-122, 112). "
        f"5) Отвечай на языке '{lang}' (kk - казахский, ru - русский, en - английский). "
        f"6) Общайся на 'ты', используй эмодзи, будь дружелюбным."
    )
    try:
        completion = client.chat.completions.create(
            model="gpt-5.4-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        logging.error(f"Ошибка API: {e}")
        if lang == "kk":
            return "Кешіріңіз, мен қазір шамадан тыс жүктелгенім. Кейінірек жазып көріңіз 💙"
        elif lang == "en":
            return "Sorry, I'm overloaded right now. Try again later 💙"
        else:
            return "Извини, сейчас я перегружен. Попробуй написать позже 💙"

# ========== ОБРАБОТЧИКИ КОМАНД И СООБЩЕНИЙ ==========
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    # Инициализируем пользователя (пока без языка)
    user_data[user_id] = {
        "language": None,
        "problem_type": None,
        "test_step": 0,
        "answers": [],
        "diary": [],
        "last_action": None
    }
    await message.answer(TEXTS["choose_language"]["ru"], reply_markup=get_language_keyboard())  # по умолчанию русский, но предложим выбор

@dp.message(Command("language"))
async def cmd_language(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {}
    await message.answer(TEXTS["choose_language"]["ru"], reply_markup=get_language_keyboard())

@dp.message(Command("change_type"))
async def cmd_change_type(message: types.Message):
    user_id = message.from_user.id
    lang = user_data.get(user_id, {}).get("language", "ru")
    await message.answer(TEXTS["choose_problem_type"][lang], reply_markup=get_problem_type_keyboard(lang))

@dp.callback_query(F.data.startswith("lang_"))
async def set_language(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang_code = callback.data.split("_")[1]  # kk, ru, en
    user_data[user_id]["language"] = lang_code
    # После выбора языка предлагаем выбрать тип проблемы
    await callback.message.edit_text(TEXTS["choose_problem_type"][lang_code], reply_markup=get_problem_type_keyboard(lang_code))
    await callback.answer()

@dp.callback_query(F.data.startswith("type_"))
async def set_problem_type(callback: CallbackQuery):
    user_id = callback.from_user.id
    problem_type = callback.data.split("_")[1]  # bullying or cyberbullying
    user_data[user_id]["problem_type"] = problem_type
    lang = user_data[user_id]["language"]
    # Отправляем приветственное сообщение с главной клавиатурой
    await callback.message.edit_text(TEXTS["welcome"][lang], reply_markup=get_main_keyboard(lang, problem_type))
    await callback.answer()

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    user_id = message.from_user.id
    lang = user_data.get(user_id, {}).get("language", "ru")
    await message.answer(TEXTS["help_text"][lang], parse_mode="Markdown", reply_markup=get_main_keyboard(lang, user_data.get(user_id, {}).get("problem_type", "bullying")))

@dp.message(F.text)
async def handle_text(message: Message):
    user_id = message.from_user.id
    if user_id not in user_data or user_data[user_id].get("language") is None:
        await message.answer("Сначала выберите язык /start или /language")
        return
    if user_data[user_id].get("problem_type") is None:
        lang = user_data[user_id]["language"]
        await message.answer(TEXTS["choose_problem_type"][lang], reply_markup=get_problem_type_keyboard(lang))
        return

    lang = user_data[user_id]["language"]
    problem_type = user_data[user_id]["problem_type"]
    text_lower = message.text.lower()

    # Кризисная проверка на трёх языках
    crisis_words = ["суицид", "покончить с собой", "не хочу жить", "умру", "смерть", "убить себя",
                    "өз-өзіме қол жұмсау", "өлгім келеді", "өлім", "suicide", "kill myself", "don't want to live"]
    if any(word in text_lower for word in crisis_words):
        crisis_response = (
            "💔 Я рядом.\n\n"
            "❗ **Позвони прямо сейчас:**\n"
            "• Детский телефон доверия: 8-800-2000-122\n"
            "• 112\n\n"
            "Ты не один. Разговор со специалистом поможет. 💙"
        )
        await message.answer(crisis_response, parse_mode="Markdown", reply_markup=get_main_keyboard(lang, problem_type))
        return

    # Проверка ключевых слов буллинга / кибербуллинга
    bullying_keywords = ["обижают", "дразнят", "бьют", "травля", "буллинг", "издеваются", "смеются", "игнорируют",
                         "мазақтайды", "ұрып-соғады", "зорлық", "bullying", "harass", "mock", "ignore"]
    cyber_keywords = ["интернет", "соцсетей", "мессенджер", "онлайн", "чат", "кибер", "инстаграм", "тикток",
                      "whatsapp", "telegram", "желіде", "кибербуллинг", "cyberbullying", "online", "social media"]

    is_bullying = any(kw in text_lower for kw in bullying_keywords)
    is_cyber = any(kw in text_lower for kw in cyber_keywords)

    # Если явно упоминается кибербуллинг или интернет-травля, даём быстрый совет по кибербуллингу
    if is_cyber or (problem_type == "cyberbullying" and is_bullying):
        quick = TEXTS["cyberbullying_quick_advice"][lang]
        await message.answer(quick, reply_markup=get_main_keyboard(lang, problem_type))
        ai_response = await get_ai_response(message.text, user_id, lang, problem_type)
        await message.answer(ai_response, parse_mode="Markdown", reply_markup=get_main_keyboard(lang, problem_type))
        return
    elif is_bullying:
        quick = TEXTS["bullying_quick_advice"][lang]
        await message.answer(quick, reply_markup=get_main_keyboard(lang, problem_type))
        ai_response = await get_ai_response(message.text, user_id, lang, problem_type)
        await message.answer(ai_response, parse_mode="Markdown", reply_markup=get_main_keyboard(lang, problem_type))
        return

    # Обычный диалог
    await message.answer("🔍 Думаю...")
    ai_answer = await get_ai_response(message.text, user_id, lang, problem_type)
    await message.answer(ai_answer, parse_mode="Markdown", reply_markup=get_main_keyboard(lang, problem_type))

# ========== INLINE КНОПКИ ==========
@dp.callback_query(F.data == "help")
async def inline_help(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = user_data.get(user_id, {}).get("language", "ru")
    await callback.message.answer(TEXTS["help_text"][lang], parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "breathing")
async def inline_breathing(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = user_data.get(user_id, {}).get("language", "ru")
    await callback.message.answer(TEXTS["breathing"][lang], parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "resources")
async def inline_resources(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = user_data.get(user_id, {}).get("language", "ru")
    await callback.message.answer(TEXTS["resources"][lang], parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "mood_diary")
async def mood_diary(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = user_data.get(user_id, {}).get("language", "ru")
    await callback.message.answer(TEXTS["mood_question"][lang], reply_markup=get_mood_keyboard(lang))
    await callback.answer()

@dp.callback_query(F.data.startswith("mood_"))
async def save_mood(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = user_data.get(user_id, {}).get("language", "ru")
    mood_key = callback.data.split("_")[1]  # bad, normal, good
    mood_map = {
        "bad": {"kk": "жаман", "ru": "плохое", "en": "bad"},
        "normal": {"kk": "қалыпты", "ru": "нормальное", "en": "normal"},
        "good": {"kk": "жақсы", "ru": "хорошее", "en": "good"}
    }
    mood_text = mood_map[mood_key][lang]
    if "diary" not in user_data[user_id]:
        user_data[user_id]["diary"] = []
    user_data[user_id]["diary"].append({"date": datetime.now().strftime("%Y-%m-%d %H:%M"), "mood": mood_text})
    saved_msg = TEXTS["mood_saved"][lang].format(mood=mood_text)
    await callback.message.answer(saved_msg, reply_markup=get_main_keyboard(lang, user_data[user_id].get("problem_type", "bullying")))
    await callback.answer()

@dp.callback_query(F.data == "random_advice")
async def random_advice(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = user_data.get(user_id, {}).get("language", "ru")
    advice_list = RANDOM_ADVICE_LISTS.get(lang, RANDOM_ADVICE_LISTS["ru"])
    advice = random.choice(advice_list)
    await callback.message.answer(TEXTS["random_advice"][lang].format(advice=advice), parse_mode="Markdown", reply_markup=get_main_keyboard(lang, user_data[user_id].get("problem_type", "bullying")))
    await callback.answer()

@dp.callback_query(F.data == "stress_test")
async def start_stress_test(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = user_data.get(user_id, {}).get("language", "ru")
    user_data[user_id]["test_step"] = 1
    user_data[user_id]["answers"] = []
    questions = {
        "kk": [
            "Сұрақ 1/5: Қандай жиілікте себепсіз алаңдаушылық сезінесіз?\n1) Ешқашан\n2) Кейде\n3) Жиі\n4) Үнемі",
            "Сұрақ 2/5: Ұйықтау қиынға соға ма?\n1) Жоқ\n2) Сирек\n3) Жиі\n4) Әр түн сайын дерлік",
            "Сұрақ 3/5: Стрестен тәбетіңіз төмендей ме?\n1) Жоқ\n2) Кейде\n3) Жиі\n4) Өте жиі",
            "Сұрақ 4/5: Денеңізде шиеленіс сезесіз бе?\n1) Жоқ\n2) Әлсіз\n3) Күшті\n4) Үнемі шиеленіс",
            "Сұрақ 5/5: Жағдайды жеңе алмаймын деп ойлайсыз ба?\n1) Ешқашан\n2) Сирек\n3) Кейде\n4) Өте жиі"
        ],
        "ru": [
            "Вопрос 1/5: Как часто ты чувствуешь тревогу без причины?\n1) Никогда\n2) Иногда\n3) Часто\n4) Постоянно",
            "Вопрос 2/5: Трудно ли тебе засыпать из-за переживаний?\n1) Нет\n2) Редко\n3) Часто\n4) Почти каждую ночь",
            "Вопрос 3/5: Бывает ли, что ты теряешь аппетит из-за стресса?\n1) Нет\n2) Иногда\n3) Часто\n4) Очень часто",
            "Вопрос 4/5: Чувствуешь ли ты напряжение в теле (плечи, челюсть)?\n1) Нет\n2) Слегка\n3) Сильно\n4) Постоянное напряжение",
            "Вопрос 5/5: Как часто ты думаешь, что не справляешься с ситуацией?\n1) Никогда\n2) Редко\n3) Иногда\n4) Очень часто"
        ],
        "en": [
            "Question 1/5: How often do you feel anxious for no reason?\n1) Never\n2) Sometimes\n3) Often\n4) Constantly",
            "Question 2/5: Do you have trouble falling asleep due to worries?\n1) No\n2) Rarely\n3) Often\n4) Almost every night",
            "Question 3/5: Do you lose your appetite due to stress?\n1) No\n2) Sometimes\n3) Often\n4) Very often",
            "Question 4/5: Do you feel tension in your body (shoulders, jaw)?\n1) No\n2) Slightly\n3) Strongly\n4) Constant tension",
            "Question 5/5: How often do you think you can't handle the situation?\n1) Never\n2) Rarely\n3) Sometimes\n4) Very often"
        ]
    }
    q_list = questions[lang]
    await callback.message.answer(q_list[0], reply_markup=get_stress_keyboard(lang))
    await callback.answer()

@dp.callback_query(F.data.startswith("stress_"))
async def process_stress_test(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = user_data.get(user_id, {}).get("language", "ru")
    step = user_data[user_id]["test_step"]
    answer_value = int(callback.data.split("_")[1])
    user_data[user_id]["answers"].append(answer_value)

    questions = {
        "kk": [
            "Сұрақ 1/5: Қандай жиілікте себепсіз алаңдаушылық сезінесіз?",
            "Сұрақ 2/5: Ұйықтау қиынға соға ма?",
            "Сұрақ 3/5: Стрестен тәбетіңіз төмендей ме?",
            "Сұрақ 4/5: Денеңізде шиеленіс сезесіз бе?",
            "Сұрақ 5/5: Жағдайды жеңе алмаймын деп ойлайсыз ба?"
        ],
        "ru": [
            "Вопрос 1/5: Как часто ты чувствуешь тревогу без причины?",
            "Вопрос 2/5: Трудно ли тебе засыпать из-за переживаний?",
            "Вопрос 3/5: Бывает ли, что ты теряешь аппетит из-за стресса?",
            "Вопрос 4/5: Чувствуешь ли ты напряжение в теле?",
            "Вопрос 5/5: Как часто ты думаешь, что не справляешься?"
        ],
        "en": [
            "Question 1/5: How often do you feel anxious for no reason?",
            "Question 2/5: Do you have trouble falling asleep due to worries?",
            "Question 3/5: Do you lose your appetite due to stress?",
            "Question 4/5: Do you feel tension in your body?",
            "Question 5/5: How often do you think you can't handle the situation?"
        ]
    }
    q_list = questions[lang]

    if step < 5:
        user_data[user_id]["test_step"] += 1
        await callback.message.edit_text(q_list[step], reply_markup=get_stress_keyboard(lang))
    else:
        total = sum(user_data[user_id]["answers"])
        if total <= 7:
            result_texts = {
                "kk": "💚 **Стресс деңгейі төмен** – сен жақсы күресесің. Өзіңе қамқор бола бер!",
                "ru": "💚 **Низкий уровень стресса** – ты хорошо справляешься. Продолжай заботиться о себе!",
                "en": "💚 **Low stress level** – you are coping well. Keep taking care of yourself!"
            }
        elif total <= 12:
            result_texts = {
                "kk": "💛 **Стресс деңгейі орташа** – аздап шиеленіс бар. Тыныс алу жаттығуларын немесе серуендеуді қолдан.",
                "ru": "💛 **Средний уровень стресса** – небольшое напряжение есть. Попробуй дыхательные упражнения или прогулку.",
                "en": "💛 **Medium stress level** – there is some tension. Try breathing exercises or a walk."
            }
        else:
            result_texts = {
                "kk": "🧡 **Стресс деңгейі жоғары** – сенің жағдайың назар аударуды қажет етеді. Мектеп психологына немесе 8-800-2000-122 нөміріне хабарлас.",
                "ru": "🧡 **Высокий уровень стресса** – твоему состоянию нужно внимание. Обратись к психологу в школе или позвони 8-800-2000-122.",
                "en": "🧡 **High stress level** – your condition needs attention. Contact a school psychologist or call 8-800-2000-122."
            }
        result = result_texts[lang]
        await callback.message.edit_text(TEXTS["stress_result"][lang].format(result=result), reply_markup=get_main_keyboard(lang, user_data[user_id].get("problem_type", "bullying")))
        user_data[user_id]["test_step"] = 0
    await callback.answer()

# ========== ЗАПУСК БОТА ==========
async def main():
    await bot(DeleteWebhook(drop_pending_updates=True))
    await dp.start_polling(bot)

if __name__ == "__main__":
    keep_alive()  # Веб-серверді боттан бұрын іске қосамыз
    asyncio.run(main())
