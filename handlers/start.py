import logging
import os
import asyncio
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
)
import json
import os

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
USERS_FILE = "users.json"
CHOOSING_ROLE = 1
user_data = {}
def load_user_data_from_file():
    global user_data
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
        logger.info("Данные пользователей загружены")
    except:
        user_data = {}
        logger.warning("Созданы новые данные пользователей")

def save_user_data_to_file():
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(user_data, f, ensure_ascii=False, indent=4)


def set_user_role(user_id, role):
    user_data[str(user_id)] = {"role": role}  # Перезаписываем полностью
    save_user_data_to_file()  # Не забываем сохранить!



def get_user_role(user_id):
    return user_data.get(str(user_id), {}).get('role', 'abit')
def get_schedule_by_department(dept_name):
    # Заглушка расписания
    schedules = {
        "Деканат": "🏛 Деканат на БМ (каб. 52-36):\n "
                "Пн-Пт с 09:00 до 16:00.\n\n"
                "🏛 Деканат на Гастелло (каб. 13-06):\n"
                " Пн-Пт с 09:00 до 16:00.\n\n"
                "Перерыв на обед с 13:00 до 14:00\n",
        "Медпункт": "🏥 Мед пункт на Гастелло (каб. 11-02): \n"
                    "Пн-Пт с 09:00 до 16:00.\n\n"
                    "🏥 Мед пункт на Ленсовета (каб. 21-07):\n"
                    " Пн-Пт с 09:00 до 16:00.\n\n"
                    "🏥 Мед пункт на БМ (каб. 32-01): \n"
                    "Пн,Вт,Чт,Пт с 09:00 до 17:00.\n"
                    "Среда не приемный день. Обед с 12:00 до 13:00.\n\n"
                    "График спортивного врача БМ (каб. 32-01):\n"
                    "Пн,Вт,Чт,Пт с 12:00 по 15:00\n",
        "Профком": "👥Профком на Гастелло (каб.13-13) \n"
                    "\n"
                    "👥Профком на Ленсовета (каб.21-19)\n"
                    "\n"
                    "👥Профком Профкома на БМ (каб.51-02а)\n\n"
                  
                    "Расписание профкома меняется в зависимости от нагруженности."
                     '\nПодробнее https://vk.com/ppos_guap \n'
                    "\n",
        "ОтделКадров": "📜Отдел кадров (БМ каб.23-03):\n"
                    "Пн,Вт,Чт,Пт: 9:00-10:00, 14:00-16:30 \n"
                    "Ср: 14:00-15:00\n",
        "ВторойОтдел":"🏢 Второй отдел БМ (каб.12-33): \n"
                    "Пн,Вт,Чт, Пт: 14:00-16:00 \n"
                    "В среду приема нет.\n" ,
    }
    return schedules.get(dept_name, "Расписание не найдено.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Принудительно загружаем свежие данные
    load_user_data_from_file()

    user_id = update.effective_user.id
    # Сбрасываем состояние для этого пользователя
    context.user_data.clear()

    # Загружаем актуальную роль из файла
    role = get_user_role(user_id)
    context.user_data['current_role'] = role

    await start_show_role_menu(update, context)
    return CHOOSING_ROLE

async def start_show_role_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # здесь весь код показа меню выбора роли без return
    context.user_data['nav_stack'] = []

    keyboard = [
        [InlineKeyboardButton("📚 Абитуриент", callback_data="role_abit"),
         InlineKeyboardButton("🎓 Студент", callback_data="role_student")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        chat_id = update.message.chat_id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat_id
    else:
        return

    msg = await context.bot.send_message(
        chat_id=chat_id,
        text="🔌 Подключаемся к ГУАП IT4.0...",
        reply_markup=reply_markup
    )
    context.user_data['start_msg_id'] = msg.message_id

    progress_steps = [
        "\n📡 Ищем актуальные данные... [█░░░░░░░] 12%\n",
        "\n💾 Загружаем модули... [███░░░░░] 37%\n",
        "\n🔍 Анализируем ваш профиль... [█████░░░] 62%\n",
        "\n⚙️ Оптимизируем интерфейс... [███████░] 88%\n",
        "\n \n     ❌ Ошибка 404. Скучные лекции не найдены! ❌  \n\n                    Активирован ГУАП IT4.0!   \n\n           [██████████████████████] 100%     \n\n                   👇 Выбери свою роль\n"
    ]

    for step in progress_steps:
        await msg.edit_text(step, reply_markup=reply_markup)
        await asyncio.sleep(0.7)


async def choose_role_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    role = query.data.replace("role_", "")  # "role_abit" → "abit"

    # Сохраняем роль (важно!)
    set_user_role(user_id, role)


    # Удаляем старое меню
    try:
        await query.delete_message()
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение: {e}")

    # Показываем главное меню для новой роли
    if role == "student":
        await show_student_menu(update, context, user_id)
    else:
        await show_abit_menu(update, context, user_id)




async def handle_inline_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if str(user_id) not in user_data:
        load_user_data_from_file()  # Перезагружаем данные

    # Проверяем роль при каждом действии
    current_role = get_user_role(user_id)
    context.user_data['current_role'] = current_role  # Сохраняем в сессии
    query = update.callback_query
    await query.answer()
    data = query.data

    try:
        await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение: {e}")

    nav_stack = context.user_data.get('nav_stack', [])

    if data == "back":
        current_role = context.user_data.get('current_role', get_user_role(update.effective_user.id))
        if not context.user_data.get('nav_stack'):
            # Если стек пуст, возвращаем в меню по роли
            if current_role == "student":
                await show_student_menu(update, context, update.effective_user.id)
            else:
                await show_abit_menu(update, context, update.effective_user.id)
            return

        if len(nav_stack) > 1:
            nav_stack.pop()
            prev_screen = nav_stack[-1]
        else:
            prev_screen = 'role_menu'
            nav_stack = ['role_menu']

        context.user_data['nav_stack'] = nav_stack
        await show_screen(update, context, prev_screen)
        return

    # Обработка кнопки смены роли
    # Если нажата кнопка "Сменить роль" — передаем управление в `choose_role_callback`
    if query.data == "change_role":
        # Принудительная перезагрузка данных
        load_user_data_from_file()

        # Удаляем старое сообщение
        try:
            await query.delete_message()
        except:
            pass

        # Показываем меню выбора роли
        keyboard = [
            [InlineKeyboardButton("📚 Абитуриент ", callback_data="role_abit"),
             InlineKeyboardButton("🎓 Студент", callback_data="role_student")]
        ]
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="\n   Выберите новую роль:  \n",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return CHOOSING_ROLE  # Важно вернуть состояние!

    # 4. Возвращаем состояни

    # Пример перехода в подменю расписания студента
    if data == "student_schedule":
        nav_stack.append('student_schedule')
        context.user_data['nav_stack'] = nav_stack

        keyboard = [
            [InlineKeyboardButton("🏛 Деканат", callback_data="dept_Деканат")],
            [InlineKeyboardButton("🏥 Мед пункт", callback_data="dept_Медпункт"),
            InlineKeyboardButton("👥 Профком", callback_data="dept_Профком")],
            [InlineKeyboardButton("📜 Отдел кадров", callback_data="dept_ОтделКадров"),
            InlineKeyboardButton("🏢 Второй отдел", callback_data="dept_ВторойОтдел")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back")]
        ]
        await query.message.reply_text("Выберите отдел:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data.startswith("dept_"):
        dept_name = data.replace("dept_", "")
        schedule = get_schedule_by_department(dept_name)

        nav_stack.append(f"dept_{dept_name}")
        context.user_data['nav_stack'] = nav_stack

        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="back")]]
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=schedule,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    # Остальные пункты — текстовые ответы с кнопкой назад
    response_map = {
        "student_science": """
    🔬 Наука в Институте 4 — это не скучно. Это старт твоей карьеры.
    
    У нас ты можешь заниматься реальными научными проектами, публиковать статьи, выступать на конференциях и внедрять свои идеи в жизнь. 
    Всё это — уже с первого курса.
    
    🔍 В институте активно развиваются направления: 
    — искусственный интеллект
    — телекоммуникации
    — информационная безопасность
    — инженерия и программирование
    
    Ты можешь выбрать то, что ближе именно тебе, и начать свой путь в науке вместе с сильным научным руководителем.
    
    Конференции:
    🎓 <a href="https://guap.ru/c/msnk">«Международная студенческая научная конференция ГУАП»</a>
    🌍 <a href="https://guap.ru/m/ptpi">«Обработка, передача и защита информации»</a>
    🧠 <a href="https://guap.ru/n/aai">«Прикладной искусственный интеллект: перспективы и риски»</a>
    
Подробнее про Науку у нас  <a href="https://guap.ru/i04/science">на странице</a>
Наука здесь — это про движение. 
Присоединяйся ✨
    """,
    "student_thesis": "<b>📝 Порядок сдачи ВКР и ВКРМ:</b>\n"
"1️⃣ <b>Написание работы и согласование с научным руководителем </b>\n"
"2️⃣ <b>Проверка на оригинальность (антиплагиат)</b>\n"
"3️⃣ <b> Прохождение экспертизы </b>\n"
"4️⃣ <b>Прошивка работы в ауд. 11-20 (Б. Морская 67)</b>\n"
"Часы работы: с 09:00 до 16:00 ежедневно, перерыв с 12:00 до 12:30\n"
"5️⃣ <b>Получение отзыва руководителя</b>\n"
"6️⃣ <b>Получение рецензии (для магистров)</b>\n"                 
"7️⃣ <b>Сдача работы на кафедру</b>\n"
"<b>📌 Важно</b>\n"
"Сроки и требования к оригинальности уточняйте на своей кафедре\n\n"

"<b>🔍 Дополнительная информация по кафедрам:</b>\n"
"📊Кафедра 41: подробная инструкция в курсе ЛМС\nПо вопросам обращаться:\n"
"Телефон: (812) 494-70-41"
" Эл. почта: dept41@guap.ru\n\n"

"🌐Кафедра 42: по вопросам обращаться\n"
"Телефон: (812) 494-70-53"
" Эл. почта: kaf42@guap.ru\n\n"

"👨‍💻Кафедра 43: инструкция в группе ВК - vk.com/k43guap\nПо вопросам обращаться:\n"
"Телефон: (812) 494-70-43 "
" Эл. почта: k43@guap.ru\n\n"

"🤖Кафедра 44 : по вопросам обращаться\n"
"Телефон: (812) 494-70-44"
" Эл. почта: kaf44@guap.ru\n\n"

'<b>🎓 Примеры работ студентов можно найти на <a href="https://guap.ru/vitrina4">Витрине Проектов</a></b>',
    "student_grants":
        "<b>🎓 Финансовая поддержка студентов ГУАП</b>\n\n"
        "<b>1. Государственная академическая стипендия</b>\n"
        "📌 <b>Кому положена:</b> Бюджетники-очники, сдавшие сессию без долгов\n"
        "💰 <b>Размер (с 01.02.2025):</b> 4500 ₽ — \"отлично\" ; 3500 ₽ — \"хорошо\"/\"хорошо+отлично\"\n"
        "🎭 <b>Также стипендию могут получать Льготные категории:</b> Сироты/инвалиды/ветераны; Студенты 1-2 курса с родителем-инвалидом I гр.; Иностранцы по квоте.\n\n"

        "<b>2. Повышенная стипендия </b>\n"
        "🎯 <b>Направления:</b>\n"
        "• Учёба/наука - 15 000 ₽\n"
        "• Общественная деятельность - 12 000 ₽\n"
        "• Спорт/творчество - 12 000 ₽\n"
        "📅 <b>На стипендию могут подавать:</b>\n"
        "Бакалавры: с 3 курса (учёба), с 2 курса (другое)\n"
        "Магистры: с 2 семестра\n"
        "ℹ️ Заявления принимают в начале каждого семестра. Следите за анонсами в группе <a href=\"https://vk.com/suaidept4\">ВК</a>\n\n"

        "<b>3. Гранты</b>\n"
        "Гранты — это финансовая поддержка для реализации научных, образовательных или социальных проектов.\n"
        "🔍 <b>Где искать:</b> <a href=\"https://guap.ru/m/science/grants\">Гранты ГУАП</a>, РНФ, Минобрнауки, Правительство СПб\n\n"

        "<b>4. Материальная помощь</b>\n"
        "❗ <b>Поддержка для:</b> Бюджетников — до 10 000 ₽ ; Контрактников — до 4 000 ₽\n"
        "📌 Подробности, как подать заявление на мат помощь, можно прочитать <a href=\"https://vk.com/@ppos_guap-stipendii-i-materialnaya-pomosch\">ТУТ</a>\n\n"

        "<b>🎓 Все виды стипендий можно найти на <a href=\"https://guap.ru/m/sveden/grants\">официальном сайте</a></b>",

    "student_job":
    """💼 Лучше искать стажировки у нас!
    
Мы понимаем, как трудно сегодня найти работу без опыта. Именно поэтому в нашем институте действует HR-Клуб — пространство, где студенты начинают путь к успешной карьере с первых курсов.

📌 HR-клуб предлагает:
- Обеспечение стажировок для студентов.  
- Повышение конкурентоспособности студентов на рынке труда.  
- Создание и поддержка связей между студентами и компаниями-партнерами.  
        
🔍Наши партнеры включают ведущие компании и организации в различных отраслях:

🏢 Научно-технический центр ПРОТЕЙ
🏥 НМИЦ имени В.А. Алмазова 
⛽ Газпром нефть
⚓АО «Концерн «Гранит-Электрон»
🔌 Компания «Гринатом» 
🏦 Промсвязьбанк
🌐 SkyNet 
🛠️ АО «Элкус» 
🚢 НЕОТЕК МАРИН
🔧 НОРБИТ
🖥️ Neoflex
        
Не упустите шанс! Присоединяйтесь к HR-клубу и начните строить свою карьеру уже сегодня!✨

<b>🔗Подробнее на <a href=\"https://guap.ru/hrclub\">официальном сайте</a></b>""",

        "student_competitions":
    """🚀 Воплоти свои IT-мечты с SUAI TECH!  
    
Присоединяйся к сообществу студентов, увлеченных технологиями, и развивай свои навыки!  

🔍 Что мы предлагаем?
- Развитие практических навыков через участие в реальных проектах.  
- Подготовка к карьерным вызовам с помощью хакатонов, олимпиад и обучения.  
- Нетворкинг с единомышленниками и менторами, участие в стартапах и инновационных проектах.  
- Участие в соревнованиях, таких как олимпиады и хакатоны, что отлично дополнит ваше резюме!  
    
Наши клубы по интересам:
🏆 Олимпиадное программирование
💡 Хакатон-движение
📊 Data Science 
🔍 Алгоритмы и структуры данных

🏢 А также экскурсии в IT-компании 
Узнай о новых технологиях и подходах к разработке, а также советы по прохождению собеседований.
 
👨‍💻 Не бойся начать!
В нашем клубе каждый может развиваться, независимо от уровня знаний✨ 
 
<b>🔗Подробнее на <a href=\"https://guap.ru/n/suaitech\">официальном сайте</a></b>""",
        "student_question":
        "📊 Кафедра 41\n📞 Телефон: (812) 494-70-41\n📧 Email:  dept41@guap.ru\nКабинет: 52-13 (Б. Морская 67)\n"  "Группа ВКонтакте: https://vk.com/suaidept41\n\n"
        "🌐 Кафедра 42\n📞 Телефон: (812) 494-70-53\n📧 Email: kaf42@guap.ru\n" "Группа ВКонтакте: https://vk.com/guapk42\n\n"
        "👨‍💻 Кафедра 43\n📞 Телефон: (812) 494-70-43\n📧 Email:  k43@guap.ru\nКабинет: 23-12 (Б. Морская 67)\n" "Группа ВКонтакте: https://vk.com/k43guap\n\n"
        "🖥️ Кафедра 44\n📞 Телефон: (812) 494-70-44\n📧 Email: kaf44@guap.ru\nКабинет: 22-12 (Б. Морская 67)\n\n"
        "⭐️ Деканат ⭐️\n📞 Телефон: (812) 494-70-40; (812) 312-24-14\n📧 Email: dek4@guap.ru\n" "📞 Телефон деканата младших курсов: (812) 708-39-43\n📧 Email деканата младших курсов: dek4gast@guap.ru \n" 
        "Группа ВКонтакте: https://vk.com/suaidept4\n\n",
        "abit_programs":
"""Привет, абитуриент! 🚀
Если ты хочешь связать свою жизнь с IT, программированием и современными технологиями, у нас есть отличные варианты для тебя! 💻✨
    
09.03.03 — Прикладная информатика. 
📌Направленность: «Информационная сфера»
🏛 Реализует Кафедра Прикладной Информатики 
🎥 Подробнее о направлении в <a href=\"https://rutube.ru/video/27c11ad17064fc129bcb41ad106a2886/\">видео</a>
        
09.03.02 — Информационные системы и технологии. 
📌Направленности:
• Информационные системы в бизнесе 💼
• Информационные технологии в дизайне 🎨
• Информационные технологии в медиаиндустрии 🎬
🏛 Реализует Кафедра информационных систем и технологий 
🎥 Подробнее о направлениях в <a href=\"https://rutube.ru/video/395606c05f20953137aa40dfeef1c91b/\">видео</a>
        
09.03.04 — Программная инженерия
📌 Направленность: Проектирование программных систем 
🏛 Реализует Кафедра компьютерных технологий и программной инженерии 
🎥 Подробнее о направлении в <a href=\"https://rutube.ru/video/96d5c759f81e398b7518ef11e0bc47f7/\">видео</a>

09.03.01 — Информатика и вычислительная техника
📌 Направленность: Компьютерные технологии, системы и сети 
🏛 Реализует Кафедра вычислительных систем и сетей 
🎥 Подробнее о направлении в <a href=\"https://rutube.ru/video/c734430a9329f1de44348ce7d563c0eb/\">видео</a>
        
🔍 Почитать о каждом направлении можно на сайте <a href=\"https://priem.guap.ru/bach/calc?filter=dep_4#bach\">Приемной комиссии</a>""",
"abit_exams":
"""📢 Вступительные испытания в ГУАП: сроки, правила, запись

Если вы поступаете на бакалавриат 4 Института и вам нужно сдать вступительные испытания, вот важные даты и условия:
📅 Документы нужно подать до 15 июля, 18:00. Сдать ВИ — до 25 июля

👨‍🎓 Кто сдает Вступительные испытания?
✓Иностранцы
✓Абитуриенты с инвалидностью
✓Выпускники колледжей и вузов
✓Граждане РФ с иностранным аттестатом
✓Поступающие по отдельной квоте
✓Выпускники школ Белгородской, Брянской, Курской областей

📝 Для записи на ВИ:  Подайте документы, Дождитесь статуса «Подтверждено» в Личном кабинете, Выберите дату и формат (очно/дистанционно)

ℹ️ Важно
Результаты появятся в личном кабинете через 3 дня после экзамена.
Программы испытаний и перечень предметов — <a href=\"https://priem.guap.ru/bach/exams\">здесь</a>.
❓ Есть вопросы? Подробнее можете посмотреть в <a href=\"https://rutube.ru/video/ef69e63cbff5d7ab6a6b5377cf5c8e3e/\">видео </a>""",

        "abit_dorms":"""
🏠 Твой новый дом в ГУАП: всё об общежитиях 

Привет, будущий студент! Если ты иногородний и поступаешь в ГУАП, эта информация точно для тебя. Давай разберёмся, как устроена жизнь в наших общежитиях — просто и без лишних сложностей.

📍 Где будем жить?
В ГУАП есть несколько комфортабельных общежитий в шаговой доступности от учебных корпусов:
<a href=\"https://guap.ru/m/dom/1\">Общежитие №1 </a> — современный корпус на проспекте Маршала Жукова с уютными комнатами и своей столовой.
<a href=\"https://guap.ru/m/dom/2\">Общежитие №2 </a> — уютное здание на улице Передовиков с зонами для отдыха.
<a href=\"https://guap.ru/m/dom/3\">Общежитие №3 </a> — новое здание на Варшавской улице с хорошим ремонтом.
<a href=\"https://guap.ru/m/dom/4\">Межвузовский городок «УМСГ»</a> — здесь живут студенты разных вузов, всегда весело и много мероприятий.

📌 Как получить место?
1️⃣ Подал документы и отметил «Нуждаюсь в общежитии»? Отлично, ты уже в списке!
2️⃣ Проверь статус: зайди в личный кабинет → «Редактировать» → посмотри графу «Требуется общежитие».
3️⃣ Жди списки: они появятся 26 августа — чем выше твой балл ЕГЭ, тем выше шанс заселиться в первую волну.

💡 Совет: даже если не попал в первые списки — не переживай! Места освобождаются, и ты обязательно получишь комнату.

📅 Когда заселяемся?
Старт заселения: 27 августа.
Если приезжаешь позже: напиши Мирошниченко Никите Игоревичу (miroshnichenko.nikita.97@yandex.ru) — чтобы сохранить место.

🚪 В день заселения тебя встретят, помогут с документами и покажут твою комнату.
        """
,
"abit_contacts": """
📱 Контакты для абитуриентов ГУАП: к кому обращаться?

Поступление — это волнительно, и мы понимаем, что у тебя может быть много вопросов. Вот все контакты, которые помогут тебе на этом пути!

🌟 По вопросам поступления :
Семененко Татьяна Вячеславовна
✉ Почта: stv12-02@yandex.ru
📞 Телефон: +7 (812) 312-21-07 (доб. 043)

🏠 По вопросам общежитий:
Мирошниченко Никита Игоревич
✉ Почта: miroshnichenko.nikita.97@yandex.ru
📞 Телефон: +7 (995) 713-14-84

🏛 Приёмная комиссия :
📞 Телефон: +7 (812) 312-21-07
✉ Почта: priem@guap.ru
🌐 Сайт: priem.guap.ru/bach

💬 Чат для абитуриентов в Telegram
Ты можешь задать любой вопрос и пообщаться с другими поступающими Института 4 здесь:
👉 t.me/+R7cxpnN_YB4yZDQ6
"""

    }

    if data in response_map:
        nav_stack.append(data)
        context.user_data['nav_stack'] = nav_stack
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="back")]]
        await context.bot.send_message(chat_id=query.message.chat_id, text=response_map[data],  reply_markup=InlineKeyboardMarkup(keyboard),
                                       parse_mode='HTML', disable_web_page_preview=True)
    else:
        # Неизвестная команда — возвращаем на главное меню роли
        nav_stack = ['role_menu']
        context.user_data['nav_stack'] = nav_stack
        await show_screen(update, context, 'role_menu')

async def show_screen(update: Update, context: ContextTypes.DEFAULT_TYPE, screen_name: str):
    query = update.callback_query
    user_id = update.effective_user.id
    role = get_user_role(user_id)  # фикс: приведение к строке
    logger.info(f"Показываем экран {screen_name} для пользователя {user_id} с ролью {role}")

    if screen_name == "role_menu":
        if role == "abit":
            await show_abit_menu(update, context, user_id)
        elif role == "student":
            await show_student_menu(update, context, user_id)
        return
    try:
        await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение: {e}")

    if screen_name == 'role_menu':
        if role == "student":
            keyboard = [
                [InlineKeyboardButton("🕔 Расписание", callback_data="student_schedule"),
                InlineKeyboardButton("🔬 Наука", callback_data="student_science")],
                [ InlineKeyboardButton("🎓 ВКР", callback_data="student_thesis"),
                  InlineKeyboardButton("💼 Стажировки", callback_data="student_job")],
                [InlineKeyboardButton("💵 Стипендии", callback_data="student_grants"),
                 InlineKeyboardButton("🏆Чемпионаты ", callback_data="student_competitions")],
                [InlineKeyboardButton("❓Контакты для связи", callback_data="student_question")],
                [InlineKeyboardButton("🔄 Сменить роль", callback_data="change_role")]
            ]

            image_path = "st2.png"
        else:
            keyboard = [
                [InlineKeyboardButton("📚 Направления подготовки ", callback_data="abit_programs")],
                [InlineKeyboardButton("📅 Вступительные испытания ", callback_data="abit_exams")],
                 [InlineKeyboardButton("📝Общежития", callback_data="abit_dorms"),
                 InlineKeyboardButton("☎️Контакты", callback_data="abit_contacts")],
                [InlineKeyboardButton("🔄 Сменить роль", callback_data="change_role")]
            ]

            image_path = "ab.png"

        reply_markup = InlineKeyboardMarkup(keyboard)

        if not os.path.exists(image_path):
            await context.bot.send_message(chat_id=user_id, reply_markup=reply_markup)
        else:
            with open(image_path, "rb") as photo:
                await context.bot.send_photo(chat_id=user_id, photo=photo, reply_markup=reply_markup)

    elif screen_name == 'student_schedule':
        keyboard = [
            [InlineKeyboardButton("🏛 Деканат", callback_data="dept_Деканат")],
            [InlineKeyboardButton("🏥 Мед пункт", callback_data="dept_Медпункт"),
             InlineKeyboardButton("👥 Профком", callback_data="dept_Профком")],
            [InlineKeyboardButton("📜 Отдел кадров", callback_data="dept_ОтделКадров"),
             InlineKeyboardButton("🏢 Второй отдел", callback_data="dept_ВторойОтдел")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back")]
        ]

        await context.bot.send_message(chat_id=user_id, text="Выберите отдел:", reply_markup=InlineKeyboardMarkup(keyboard))
async def show_abit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE,  user_id):
    keyboard = [
        [InlineKeyboardButton("📚 Направления подготовки ", callback_data="abit_programs")],
        [InlineKeyboardButton("📅 Вступительные испытания ", callback_data="abit_exams")],
        [InlineKeyboardButton("📝Общежития", callback_data="abit_dorms"),
         InlineKeyboardButton("☎️Контакты", callback_data="abit_contacts")],
        [InlineKeyboardButton("🔄 Сменить роль", callback_data="change_role")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    image_path = "ab.png"
    if not os.path.exists(image_path):
        await context.bot.send_message(chat_id=user_id, reply_markup=reply_markup)
    else:
        with open(image_path, "rb") as photo:
            await context.bot.send_photo(chat_id=user_id, photo=photo, reply_markup=reply_markup)




async def show_student_menu(update: Update, context: ContextTypes.DEFAULT_TYPE,  user_id):
    keyboard = [
        [InlineKeyboardButton("🕔 Расписание", callback_data="student_schedule"),
         InlineKeyboardButton("🔬 Наука", callback_data="student_science")],
        [InlineKeyboardButton("🎓 ВКР", callback_data="student_thesis"),
         InlineKeyboardButton("💼 Стажировки", callback_data="student_job")],
        [InlineKeyboardButton("💵 Стипендии", callback_data="student_grants"),
         InlineKeyboardButton("🏆Чемпионаты ", callback_data="student_competitions")],
        [InlineKeyboardButton("❓Контакты для связи", callback_data="student_question")],
        [InlineKeyboardButton("🔄 Сменить роль", callback_data="change_role")]
    ]
    image_path = "st2.png"
    reply_markup = InlineKeyboardMarkup(keyboard)
    if not os.path.exists(image_path):
        await context.bot.send_message(chat_id=user_id, reply_markup=reply_markup)
    else:
        with open(image_path, "rb") as photo:
            await context.bot.send_photo(chat_id=user_id, photo=photo, reply_markup=reply_markup)


async def change_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Показываем меню выбора ролей (как в start)
    await start(update, context)
    # НЕ возвращаем CHOOSING_ROLE, иначе ConversationHandler сбросится
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Выход из диалога.")
    return ConversationHandler.END