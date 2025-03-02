import sqlite3
from config import dp, F, bot
from aiogram import types
from aiogram.fsm.context import FSMContext
from keyboards.keyboard import *
from keyboards.inline import *
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    PreCheckoutQuery,
    LabeledPrice,
)

from states.state import NewGameState, MessagetoAdmin, awaiting_game_number
from db import *


@dp.message(F.text.in_(["settings ⚙️", "sozlamalar ⚙️", "настройки ⚙️"]))
async def settingxcyvus(message: types.Message):
    ln = get_user_language(message.from_user.id)
    if ln == "uz":
        ms = "Quidagilardan birini tanlang: ⬇️"
        kb = change_name_uz
    elif ln == "ru":
        ms = "Выберите один из этих вариантов: ⬇️"
        kb = change_name_ru
    else:
        ms = "Choose one of these options: ⬇️"
        kb = change_name
    await message.answer(ms, reply_markup=kb)


@dp.message(F.text.in_(["❓ help", "❓ yordam", "❓ помощь"]))
async def help_butn(message: types.Message, state: FSMContext):
    ln = get_user_language(message.from_user.id)
    if ln == "uz":
        ms = "Agar sizda biron bir savol yoki taklif bo'lsa, bu yerga yozing. Admin imkon qadar tezroq javob beradi. ⬇️"
        kb = cancel_button_uz
    elif ln == "ru":
        ms = "Если у вас есть вопросы или предложения, смело пишите здесь. Администратор ответит как можно скорее. ⬇️"
        kb = cancel_button_ru
    else:
        ms = "If you have any questions or suggestions, feel free to write here. An admin will respond as soon as possible. ⬇️"
        kb = cancel_button
    await message.answer(ms, reply_markup=kb)

    await state.set_state(MessagetoAdmin.msgt)


@dp.message(MessagetoAdmin.msgt)
async def help_button_state(message: types.Message, state: FSMContext):
    ln = get_user_language(message.from_user.id)
    if not message.text in [
        "back to main menu 🔙",
        "вернуться в главное меню 🔙",
        "bosh menuga qaytish 🔙",
    ]:
        await bot.send_message(
            chat_id=6807731973,
            text=f"User — {message.from_user.first_name} (<a href='tg://openmessage?user_id={message.from_user.id}'>{message.from_user.id}</a>) sent you message: \n{message.text}",
            parse_mode="HTML",
        )

        if ln == "uz":
            ms = "Xabaringiz muvaffaqiyatli yuborildi ✅"
        elif ln == "ru":
            ms = "Ваше сообщение успешно отправлено ✅"
        else:
            ms = "Your message has been sent successfully ✅"
        await message.answer(ms, reply_markup=get_main_menu(message.from_user.id))
        await state.clear()
    else:
        await state.clear()
        if ln == "uz":
            ms = "Siz asosiy menudasiz 👇"
        elif ln == "ru":
            ms = "Вы находитесь в главном меню 👇"
        else:
            ms = "You are in main menu 👇"
        await message.answer(ms, reply_markup=get_main_menu(message.from_user.id))


@dp.message(
    F.text.in_(
        [
            "изменить имя пользователя 🖌",
            "change username 🖌",
            "usernameni o'zgartirish  🖌",
        ]
    )
)
async def changeee(message: types.Message, state: FSMContext):
    await state.clear()
    ln = get_user_language(message.from_user.id)
    if ln == "ru":
        ms = f"Ваше текущее имя пользователя 👉 {get_user_nfgame(message.from_user.id)}\n"
        ms1 = "Если вы хотите изменить его, введите новое имя пользователя:"
        kb = cancel_button_ru
    elif ln == "uz":
        ms = f"Sizning hozirgi foydalanuvchi nomingiz 👉 {get_user_nfgame(message.from_user.id)}\n"
        ms1 = "Agar uni o'zgartirishni hohlasangiz, shu yerga yangi usaname kiriting:"
        kb = cancel_button_uz
    else:
        ms = f"Your current username is 👉 {get_user_nfgame(message.from_user.id)}\n"
        ms1 = "If you'd like to change it, please type your new username:\n"
        kb = cancel_button
    await message.answer(ms, reply_markup=kb)
    await message.answer(ms1, reply_markup=get_username_button(ln))
    await state.set_state(NewGameState.waiting_for_nfgame)


@dp.message(NewGameState.waiting_for_nfgame)
async def set_new_nfgame(message: types.Message, state: FSMContext):
    ln = get_user_language(message.from_user.id)
    new_nfgame = message.text
    if is_game_started(get_game_id_by_user(message.from_user.id)):
        if ln == "uz":
            ms = "Siz hozirda oʻyinda ishtirok etyapsiz va oʻyin tugaguncha foydalanuvchi nomingizni oʻzgartira olmaysiz ❌"
        elif ln == "ru":
            ms = "В данный момент вы участвуете в игре и не можете изменить свое имя пользователя до окончания игры ❌"
        else:
            ms = f"You are currently participating in a game and cannot change your username until the game ends ❌"
        await message.answer(ms, reply_markup=get_main_menu(message.from_user.id))
        await state.clear()
        return
    if new_nfgame in [
        "back to main menu 🔙",
        "вернуться в главное меню 🔙",
        "bosh menuga qaytish 🔙",
    ]:
        await state.clear()
        if ln == "uz":
            ms = "Siz asosiy menudasiz 👇"
        elif ln == "ru":
            ms = "Вы находитесь в главном меню 👇"
        else:
            ms = "You are in main menu 👇"
        await message.answer(ms, reply_markup=get_main_menu(message.from_user.id))
        return
    h = is_name_valid(new_nfgame)
    if not h:
        if ln == "uz":
            ms = "Siz kiritgan ma'lumot noto'g'ri! Iltimos, foydalanuvchi nomingizni berilgan formatda kiriting"
            kb = cancel_button_uz
        elif ln == "ru":
            ms = "Ваши данные неверны! Введите имя пользователя в указанном формате"
            kb = cancel_button_ru
        else:
            ms = "Your data is incorrect! Please enter your username in a given format"
            kb = cancel_button
        await message.answer(ms, reply_markup=kb)
    elif h == 2:
        if ln == "uz":
            ms = "Botda bu foydalanuvchi nomi allaqachon mavjud. Iltimos, boshqa foydalanuvchi nomini kiriting."
            kb = cancel_button_uz
        elif ln == "ru":
            ms = "Пользователь с таким именем уже есть в боте. Введите другое имя пользователя."
            kb = cancel_button_ru
        else:
            ms = "There is already user with this username in the bot. Please enter another username."
            kb = cancel_button
        await message.answer(ms, reply_markup=kb)
    else:
        user_id = message.from_user.id
        with sqlite3.connect("users_database.db") as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users_database SET nfgame = ? WHERE user_id = ?",
                (new_nfgame, user_id),
            )
            conn.commit()

        if ln == "uz":
            ms = f"Ismingiz {new_nfgame}ga muvaffaqiyatli o'zgartirildi ✅"
        elif ln == "ru":
            ms = f"Ваше имя успешно изменено на {new_nfgame} ✅"
        else:
            ms = f"Your name has been successfully changed to: {new_nfgame} ✅"
        await message.answer(ms, reply_markup=get_main_menu(message.from_user.id))
        await state.clear()


@dp.message(F.text.in_(["cancel 🚫", "отмена 🚫", "bekor qilish 🚫"]))
async def cancel(message: types.Message, state: FSMContext):
    await state.clear()
    ln = get_user_language(message.from_user.id)
    if ln == "uz":
        ms = "Siz harakatni bekor qildingiz."
    elif ln == "ru":
        ms = "Вы отменили операцию."
    else:
        ms = f"You have canceled the operation."
    await message.answer(ms, reply_markup=get_main_menu(message.from_user.id))


@dp.message(F.text.in_(["information 📚", "информация 📚", "ma'lumot 📚"]))
async def statistics_a(message: types.Message, state: FSMContext):
    await state.clear()
    ln = get_user_language(message.from_user.id)
    if ln == "uz":
        chk = "📢 Bot kanali"
        kr = "👨‍💻 yaratuvchi"
        st = f"Bot statistikasi 📈:\n\nFoydalanuvchilar soni 👥: {get_total_users()}\nIshga tushirilgan sana: 01.03.2025 📅\nVaqt mintaqasi ⏳: UTC +5\n\n❕Barcha ma'lumotlar shu mintaqa bo'yicha ko'rsatiladi."
    elif ln == "ru":
        chk = "📢 Канал бота"
        kr = "👨‍💻 Создатель"
        st = f"Cтатистика ботов 📈:\n\nПользователи в боте 👥: {get_total_users()}\nБот активен с 01.03.2025 📅\nЧасовой пояс бота ⏳: UTC +5\n\n❕ Все данные представлены в часовом поясе бота"
    else:
        chk = "📢 Bot's Channel"
        kr = "👨‍💻 Creator"
        st = f"Here are the bot's statistics 📈:\n\nTotal users in the bot 👥: {get_total_users()}\nBot has been active since 01.03.2025 📅\nBot's timezone ⏳: UTC +5\n\n❕ All data are presented in a bot's timezone"
    inline_buttons = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=chk, url="https://t.me/liars_fortune_channel"
                ),
            ],
            [
                InlineKeyboardButton(text=kr, url="https://t.me/TechBotsy"),
            ],
        ]
    )
    await message.answer(
        st,
        reply_markup=inline_buttons,
    )


@dp.message(F.text.in_(["game rules 📜", "o'yin qoidalari 📜", "правила игры 📜"]))
async def how_to_play(message: types.Message, state: FSMContext):
    await state.clear()
    ln = get_user_language(message.from_user.id)
    if ln == "ru":
        msg = (
            "📚 *Правила игры* 📚\n\n"
            "👥 *Игроки:* 2-4 человека.\n"
            "🃏 *Карты:* У каждого игрока 5 карт.\n\n"
            "🔄 *Как играть:*\n"
            "▪️ На стол кладется карта, определяющая масть (❤️ ♦️ ♣️ ♠️).\n"
            "▪️ В свой ход можно сыграть 1-3 карты той же масти.\n"
            "▪️ Если подходящих карт нет, используйте *Универсальную карту* 🎴.\n"
            "▪️ После хода следующий игрок может:\n"
            "1️⃣ *Продолжить* – Принять ход и сыграть свою карту.\n"
            "2️⃣ *Сказать «ЛЖЕЦ!»* – Оспорить сыгранные карты.\n\n"
            "❗ *Если сказали «ЛЖЕЦ!»:*\n"
            "✔️ *Правда?* Оспаривающий получает «выстрел».\n"
            "❌ *Ложь?* Вы получаете «выстрел».\n\n"
            "🌟 *Особые карты:*\n"
            "🎴 *Универсальная карта* – Заменяет любую масть.\n"
            "🃏 *Джокер* – Играется отдельно. Если кто-то оспорит, *все остальные получают выстрел!*\n\n"
            "⚙️ *Дополнительные правила:*\n"
            "▪️ Если у вас нет карт, вы пропускаете ход.\n"
            "▪️ В револьвере 6 патронов, но только 1 настоящий.\n\n"
            "🏆 *Как победить:*\n"
            "Оставайся последним выжившим – и ты победитель! 🎉"
        )

    elif ln == "uz":
        msg = (
            "📚 *O‘yin qoidalari* 📚\n\n"
            "👥 *O‘yinchilar:* 2-4 kishi.\n"
            "🃏 *Kartalar:* Har bir o‘yinchi uchun 5 ta karta.\n\n"
            "🔄 *Qanday o‘ynash kerak?*\n"
            "▪️ Stolga bitta karta qo‘yiladi va qaysi toifadagi kartalar o‘ynalishini belgilanadi (❤️ ♦️ ♣️ ♠️).\n"
            "▪️ O‘zingizning navbatingizda shu toifaga mos 1-3 ta karta tashlaysiz.\n"
            "▪️ Agar mos karta bo‘lmasa, *Universal karta* 🎴 dan foydalanasiz.\n"
            "▪️ Keyingi o‘yinchi:\n"
            "1️⃣ *Davom ettirish* – Kartani qabul qilib, o‘yinini davom ettiradi.\n"
            "2️⃣ *«Yolg‘on!»* – Tashlangan kartalarni tekshiradi.\n\n"
            "❗ *Agar «Yolg‘on!» chaqirilsa:*\n"
            "✔️ *Rost bo‘lsa* – «Yolg‘on!» tugmasini bosgan o‘yinchi «otariladi».\n"
            "❌ *Yolg‘on bo‘lsa* – Siz «otarilasiz».\n\n"
            "🌟 *Maxsus kartalar:*\n"
            "🎴 *Universal karta* – Istalgan toifaga mos keladi.\n"
            "🃏 *Joker* – Bitta o‘ynash mumkin. Agar kimdir «Yolg‘on!» desa, *qolganlarning barchasi «otariladi»!*\n\n"
            "⚙️ *Qo‘shimcha qoidalar:*\n"
            "▪️ Kartalaringiz tugasa, navbatingiz o‘tib ketadi.\n"
            "▪️ Qurol 6 ta o‘ringa ega, ammo faqat 1 tasi haqiqiy o‘q.\n\n"
            "🏆 *G‘alaba sharti:*\n"
            "Oxirgi tirik qolgan o‘yinchi g‘olib bo‘ladi! 🎉"
        )

    else:
        msg = (
            "📚 *Game Rules* 📚\n\n"
            "👥 *Players:* 2-4 people.\n"
            "🃏 *Cards:* Each player starts with 5 cards.\n\n"
            "🔄 *How to Play:*\n"
            "A card is placed on the table to set the suit (❤️ ♦️ ♣️ ♠️).\n"
            "On your turn, you can play 1-3 cards that match the suit.\n"
            "If you have no matching cards, use the *Universal Card* 🎴.\n"
            "After playing, the next player can either:\n"
            "1️⃣ *Continue* - Accept the move and play their turn.\n"
            "2️⃣ *Call LIAR!* - Challenge the played cards.\n\n"
            "❗ *If LIAR is called:*\n"
            "✔️ *Truth?* The challenger gets “shot.”\n"
            "❌ *Lie?* You get “shot.”\n\n"
            "🌟 *Special Cards:*\n"
            "🎴 *Universal Card* - Matches any suit.\n"
            "🃏 *Joker* - Play it alone. If someone challenges, *everyone else gets shot!*\n\n"
            "⚙️ *Other Rules:*\n"
            "🔹 If you run out of cards, you skip your turn.\n"
            "🔹 The gun has 6 spots, but only 1 real bullet.\n\n"
            "🏆 *Winning Condition:*\n"
            "The last player left standing wins!"
        )
    await message.answer(msg, parse_mode="Markdown")


def get_user_game_archive(user_id: int):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT game_id, game_start_time, game_end_time, game_winner
            FROM game_archive
            WHERE user_id = ?
            """,
            (user_id,),
        )
        games = cursor.fetchall()
        return games
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return []
    finally:
        conn.close()


@dp.message(F.text.in_(["bonus 🚀", "bonus 🚀", "бонус 🚀"]))
async def get_daily_bonus_function(message: types.Message):
    user_id = message.from_user.id
    ln = get_user_language(user_id)
    if ln == "uz":
        bn = "Bonusni olish 🎁"
        msg = (
            "🎁 *Kunlik Bonus!* 🎁\n\n"
            "Bonus miqdori 1 dan 20 gacha tasodifiy Unity Coin! 💰 \nBonusni olish uchun pastdagi tugmani bosing. 🚀\n\n"
            "Har kuni bonuslarni olishni unutmang! 😌"
        )
    elif ln == "ru":
        bn = "Получите бонус 🎁"
        msg = (
            "🎁 *Ежедневный бонус!* 🎁\n\n"
            "Бонусная сумма от 1 до 20 случайных Unity Coin! 💰 \nНажмите кнопку ниже, чтобы получить бонус. 🚀\n\n"
            "Не забывайте получать бонусы каждый день! 😌"
        )
    else:
        bn = "Claim Bonus 🎁"
        msg = (
            "🎁 *Daily Bonus!* 🎁\n\n"
            "Claim your reward of *1 to 20 Unity Coins*! 💰 \nTap the button below and get your reward. 🚀\n\n"
            "Come back tomorrow for more! 🎉"
        )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=bn, callback_data=f"bonus_cb_{user_id}")]
        ]
    )

    await message.answer(
        msg,
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


def get_start_of_week():
    today = datetime.now(timezone.utc)
    start_of_week = today - timedelta(days=today.weekday())
    return start_of_week.replace(hour=0, minute=0, second=0, microsecond=0).strftime(
        "%Y-%m-%d 00:00:00"
    )


def get_weekly_leaderboard():
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()

    start_of_week = get_start_of_week()
    cursor.execute(
        """
        SELECT user_id, COUNT(*) as total_games, 
               SUM(CASE WHEN SUBSTR(game_winner, INSTR(game_winner, '-') + 2) = CAST(user_id AS TEXT) THEN 1 ELSE 0 END) as games_won
        FROM game_archive
        WHERE game_end_time >= ?
        GROUP BY user_id
        ORDER BY games_won DESC, total_games DESC
        LIMIT 10
    """,
        (start_of_week,),
    )

    leaderboard = cursor.fetchall()
    conn.close()

    return leaderboard


def format_weekly_leaderboard(user_id):
    leaderboard = get_weekly_leaderboard()
    ln = get_user_language(user_id)
    if ln == "uz":
        msg = "📅 Dushanbadan buyon hali o'yinlar o'ynalmadi!"
        leaderboard_text = "🏆 Haftalik Liderbord 🏆\n\n"
    elif ln == "ru":
        msg = "📅 С понедельника не игралось ни одной игры!"
        leaderboard_text = "🏆 Еженедельная таблица лидеров 🏆\n\n"
    else:
        msg = "📅 No games played since Monday!"
        leaderboard_text = "🏆 Weekly Leaderboard 🏆\n\n"
    if not leaderboard:
        return msg

    medals = ["🥇", "🥈", "🥉"]

    for rank, (user_id, total_games, games_won) in enumerate(leaderboard, start=1):
        username = get_user_nfgame(user_id)
        medal = f"{medals[rank - 1]}. " if rank <= 3 else f"{rank}."
        leaderboard_text += f"{medal} {username} — 🎮 {total_games} | 🏆 {games_won}\n"

    return leaderboard_text


@dp.message(F.text.in_(["🏅 Leaderboard", "🏅 Лидербоард", "🏅 Liderbord"]))
async def show_weekly_leaderboard(message: types.Message):
    leaderboard_text = format_weekly_leaderboard(message.from_user.id)
    await message.answer(leaderboard_text)


@dp.message(F.text.in_(["📱 kabinet", "📱 cabinet", "📱 кабинет"]))
async def my_cabinet(message: types.Message):
    user_id = message.from_user.id
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT registration_date, nfgame, unity_coin FROM users_database WHERE user_id = ?",
        (user_id,),
    )
    user_info = cursor.fetchone()
    if not user_info:
        await message.answer("❌ You are not registered in the database.")
        conn.close()
        return
    registration_date, nfgame, unity_coins = user_info
    cursor.execute("SELECT COUNT(*) FROM game_archive WHERE user_id = ?", (user_id,))
    games_played = cursor.fetchone()[0]
    conn.close()
    tools = fetch_user_tools(user_id)
    ln = get_user_language(message.from_user.id)
    if ln == "uz":
        user_cabinet_message = (
            f"📱 Sizning kabinetingiz\n\n"
            f"👤 Username: {nfgame}\n"
            f"🗓 Ro'yhatdan o'tgan sana: {registration_date}\n"
            f"🎮 O'ynagan o'yinlari soni: {games_played}\n"
            f"👥 Referallari soni: {get_number_of_referrals(message.from_user.id)}\n"
            f"💰 Unity Coinlari: {unity_coins}\n\n"
            f"🔗 super jihozlar:\nskip 🪓: {tools["skipper"]}\nblock ⛔️: {tools["blocker"]}\nchange 🔄: {tools["changer"]}"
        )
    elif ln == "ru":
        user_cabinet_message = (
            f"📱 Ваш кабинет\n\n"
            f"👤 Username: {nfgame}\n"
            f"🗓 Дата регистрации: {registration_date}\n"
            f"🎮 Сыграно игр: {games_played}\n"
            f"👥 рефералы: {get_number_of_referrals(message.from_user.id)}\n"
            f"💰 Unity Coins: {unity_coins}\n"
            f"🔗 супер инструменты:\nskip 🪓: {tools["skipper"]}\nblock ⛔️: {tools["blocker"]}\nchange 🔄: {tools["changer"]}"
        )
    else:
        user_cabinet_message = (
            f"📱 Your Cabinet\n\n"
            f"👤 Username: {nfgame}\n"
            f"🗓 Registration Date: {registration_date}\n"
            f"🎮 Games Played: {games_played}\n"
            f"👥 referrals: {get_number_of_referrals(message.from_user.id)}\n"
            f"💰 Unity Coins: {unity_coins}\n"
            f"🔗 super tools:\nskip 🪓: {tools["skipper"]}\nblock ⛔️: {tools["blocker"]}\nchange 🔄: {tools["changer"]}"
        )
    await message.answer(user_cabinet_message)


@dp.message(F.text.in_(["Sovg'alar 🎁", "Prizes 🎁", "Призы 🎁"]))
async def process_withdraw_user(message: types.Message):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM withdraw_options LIMIT 1")
    withdraw_options = cursor.fetchone()
    if not withdraw_options:
        await message.answer("❌ No withdrawal options found.")
        conn.close()
        return
    (
        three_month_premium,
        six_month_premium,
        twelve_month_premium,
        hundrad_stars,
        five_hundrad_stars,
        thousand_stars,
    ) = withdraw_options
    cursor.execute(
        "SELECT unity_coin FROM users_database WHERE user_id = ?",
        (message.from_user.id,),
    )
    unity_coin = cursor.fetchone()[0]
    conn.close()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"❄️ 3 Months", callback_data="get_3_month"),
                InlineKeyboardButton(
                    text=f"⭐ 100 Stars", callback_data="get_100_stars"
                ),
            ],
            [
                InlineKeyboardButton(text=f"❄️ 6 Months", callback_data="get_6_month"),
                InlineKeyboardButton(
                    text=f"⭐ 500 Stars", callback_data="get_500_stars"
                ),
            ],
            [
                InlineKeyboardButton(text=f"❄️ 12 Months", callback_data="get_12_month"),
                InlineKeyboardButton(
                    text=f"⭐ 1,000 Stars", callback_data="get_1000_stars"
                ),
            ],
        ]
    )
    ln = get_user_language(message.from_user.id)
    if ln == "uz":
        ms1 = (
            f"💳 *Sizning hozirgi hisobingiz*: {unity_coin} Unity Coin 💰\n\n"
            "💰 *Coinlarni nimalarga almashtirish mumkin: *\n"
        )
        msg2 = "Almashtirish uchun pastdagi tugmani bosing 👇"
    elif ln == "ru":
        ms1 = (
            f"💳 *Ваш текущий баланс*: {unity_coin} Unity Coin 💰\n\n"
            "💰 *На что можно обменять Unity coins: *\n"
        )
        msg2 = "Нажмите кнопку ниже, чтобы обменять 👇"
    else:
        ms1 = (
            f"💳 *Your current balance*: {unity_coin} Unity Coin 💰\n\n"
            "💰 *Withdrawal options*\n"
        )
        msg2 = "Choose a button to get 👇"
    withdraw_message = "\n".join(
        [
            ms1,
            f"🚀 *Telegram Premium*\n"
            f"❄️ *3 Months*: {three_month_premium} Unity Coins 💰\n"
            f"❄️ *6 Months*: {six_month_premium} Unity Coins 💰\n"
            f"❄️ *12 Months*: {twelve_month_premium} Unity Coins 💰\n\n"
            f"⭐️ *Telegram Stars* \n"
            f"✨ *100 Stars*: {hundrad_stars} Unity Coins 💰\n"
            f"✨ *500 Stars*: {five_hundrad_stars} Unity Coins 💰\n"
            f"✨ *1,000 Stars*: {thousand_stars} Unity Coins 💰\n\n",
            msg2,
        ]
    )

    await message.answer(withdraw_message, parse_mode="Markdown", reply_markup=keyboard)


@dp.message(F.text.in_(["🤩 tournaments", "🤩 turnirlar", "🤩 турниры"]))
async def show_tournaments_menu(message: types.Message):
    get_o = get_ongoing_tournaments()
    ln = get_user_language(message.from_user.id)
    if ln == "uz":
        ong = "⚡ Hozirda davom etayotgan turnir mavjud! 🎮\nAgar ro'yhatdan o'tish tugamagan bo'lsa siz hali ham qo'shilishingiz mumkin. 🔥"
        upc = "Hech qanday yangi turnir rejalashtirilmagan 🏆\nAmmo siz pastdagi tugmani bosish orqali o'tmishdagi turnirlar natijalarini ko'rishingiz mumkin. 📜"
    elif ln == "ru":
        ong = "⚡ В настоящее время проходит турнир! 🎮\nВы можете принять участие, если регистрация еще открыта. 🔥"
        upc = "Новые турниры не планируются 🏆\nНо вы можете изучить архив прошлых турниров. 📜"
    else:
        ong = "⚡ There is an ongoing tournament! 🎮\nYou can participate if it's still open. 🔥"
        upc = "No upcoming tournaments are scheduled. 🏆\nBut you can explore the archive of past tournaments. 📜"
    if get_o:
        await message.answer(ong, reply_markup=archive_tournamnets)
        return
    tournaments = get_upcoming_tournaments()
    if not tournaments:
        await message.answer(upc, reply_markup=archive_tournamnets)
        return
    for tournament in tournaments:
        if ln == "uz":
            response = (
                f"🌟 Turnir ID: {tournament['id']}\n\n"
                f"🗓 Boshlanish vaqti: {tournament['start_time']}\n"
                f"🏁 Tugash vaqti: {tournament['end_time']}\n\n"
                f"🏆 Sovrin: \n{tournament['prize']}\n\n"
                f"📢 Turnir boshlanishi bilan barcha qoshilish uchun link oladi, shuning uchun osha payt online bo'ling ❗️❗️❗️\n"
            )
        elif ln == "ru":
            response = (
                f"🌟 ID турнира: {tournament['id']}\n\n"
                f"🗓 Время начала: {tournament['start_time']}\n"
                f"🏁 Время окончания: {tournament['end_time']}\n\n"
                f"🏆 Приз: \n{tournament['prize']}\n\n"
                f"📢 Перед началом турнира все получат уведомление о возможности присоединиться. Так что будьте в это время онлайн. ❗️❗️❗️\n"
            )
        else:
            response = (
                f"🌟 Tournament ID: {tournament['id']}\n\n"
                f"🗓 Starts: {tournament['start_time']}\n"
                f"🏁 Ends: {tournament['end_time']}\n\n"
                f"🏆 Prize: \n{tournament['prize']}\n\n"
                f"📢 Before the tournament begins, everyone will receive a notification to join. So be online at that time ❗️❗️❗️\n"
            )
    await message.answer(
        response,
        reply_markup=archive_tournamnets,
    )


@dp.message(F.text.in_(["❄️ referal", "❄️ referral", "❄️ реферал"]))
async def tournaments_users_button(message: types.Message):
    referral_link = generate_referral_link(message.from_user.id)
    u_coins = get_unity_coin_referral()
    ln = get_user_language(message.from_user.id)
    if ln == "uz":
        ms = f"Sizning referal havolangiz 👇\nUshbu havolani do'stlaringizga yuboring va har bir ro'yhatdan o'tgan do'stingiz uchun {u_coins} Unity Coin 💰 ga ega bo'ling."
        ref = (
            f"🎮 *Salom!* Ushbu botga qo‘shib, qiziqarli o‘yinlar o‘ynang va mukofotlarga ega bo‘ling! 🚀\n\n"
            f"👉 Boshlash uchun ushbu havolani bosing 👇\n\n{referral_link}\n\n"
            "O‘ynang, yutib oling va zavqlaning! 😉"
        )
    elif ln == "ru":
        ms = f"Вот ваша реферальная ссылка 👇\nОтправьте ее своим друзьям и получите {u_coins} Unity coins 💰 за каждого нового друга."
        ref = (
            f"🎮 *Привет!* Присоединяйся к этому боту, играй в увлекательные игры и зарабатывай награды! 🚀\n\n"
            f"👉 Используй эту ссылку, чтобы начать 👇\n\n{referral_link}\n\n"
            "Играй, зарабатывай и наслаждайся! 😉"
        )
    else:
        ms = f"Here is your refferal link 👇\nSend this to your friends and get {u_coins} Unity Coins 💰 for each new friend."
        ref = (
            f"🎮 *Hey!* Join this bot to play fun games and earn rewards! 🚀\n\n"
            f"👉 Use this link to get started 👇\n\n{referral_link}\n\n"
            "Play, earn, and enjoy! 😉"
        )
    await message.answer(ms)
    await message.answer(ref)


@dp.message(
    F.text.in_(["change Language 🇺🇸", "изменить язык 🇷🇺", "Tilni o'zgartirish 🇺🇿"])
)
async def change_langguage(message: types.Message):
    ln = get_user_language(message.from_user.id)
    if ln == "uz":
        ms = "🌍 Kerakli tilni tanlang: "
    elif ln == "ru":
        ms = "🌍 Выберите нужный язык: "
    else:
        ms = "🌍 Please select your language: "
    await message.answer(ms, reply_markup=select_language_button_2)


# @dp.message(F.text == "🎯 game archive")
# async def show_game_archive(message: types.Message, state: FSMContext):
#     user_id = message.from_user.id
#     games = get_user_game_archive(user_id)

#     if not games:
#         await message.answer("No games found in your archive.")
#         return
#     response = "📜 Your Game Archive:\n\n"
#     for idx, (_, start_time, _, _) in enumerate(games, start=1):
#         response += f"{idx}. game — {start_time.split(' ')[0]} 📅\n"

#     response += "\n📋 Send the game number to view its details."
#     await message.answer(response, reply_markup=cancel_button)
#     await state.set_state(awaiting_game_number.waiting)

# @dp.message(awaiting_game_number.waiting)
# async def send_game_statistics(message: types.Message, state: FSMContext):
#     if message.text == "back to main menu 🔙":
#         await state.clear()
#         await message.answer(
#             f"You are in main menu.", reply_markup=get_main_menu(message.from_user.id)
#         )
#         return
#     user_id = message.from_user.id
#     games = get_user_game_archive(user_id)

#     if not message.text.isdigit():
#         await message.answer(
#             "❌ Please send a valid game number.", reply_markup=get_main_menu(user_id)
#         )
#         await state.clear()
#         return
#     game_number = int(message.text)
#     if game_number < 1 or game_number > len(games):
#         await message.answer(
#             "❌ Invalid game number. Please try again.",
#             reply_markup=get_main_menu(user_id),
#         )
#         await state.clear()
#         return
#     record_id, start_time, end_time, winner = games[game_number - 1]
#     game_status = (
#         f"🕹 Game Details:\n"
#         f"🆔 Game ID: {record_id}\n"
#         f"⏰ Start Time: {start_time}\n"
#         f"🏁 End Time: {end_time if end_time else 'Has not finished'}\n"
#         f"🏆 Winner: {winner if winner else 'No Winner'}"
#     )
#     await message.answer(
#         game_status,
#         reply_markup=get_main_menu(message.from_user.id),
#     )
#     await state.clear()


@dp.message(F.text.in_(["pul ishlash 💸", "зарабатывать 💸", "earn 💸"]))
async def earn_feature_for_users(message: types.Message):
    user_id = message.from_user.id
    ln = get_user_language(user_id)
    if ln == "uz":
        msg = "Bu yerda siz Unity Coinlarni ishlash bo'yicha barcha variantlarini topishingiz mumkin 💰"
        kb = main_earn_button_uz
    elif ln == "ru":
        msg = "Здесь вы найдете все варианты заработка Unity Coin 💰"
        kb = main_earn_button_ru
    else:
        msg = f"Here you can find all the options for earn Unity Coins 💰"
        kb = main_earn_button
    await message.answer(msg, reply_markup=kb)


from aiogram.utils.keyboard import InlineKeyboardBuilder


@dp.message(F.text.in_(["Join channels 💎", "Подписаться 💎", "obuna bo'lish 💎"]))
async def join_channels_to_earn(message: types.Message):
    user_id = message.from_user.id
    channels = get_unsubscribed_channels(user_id)
    if not channels:
        await message.answer("There are no channels to subscribe to yet 😓")
        return
    channel_id, channel_link = channels
    ln = get_user_language(user_id)
    if ln == "uz":
        ms1 = "✅ Kanalga qo'shilish"
        ms2 = "🔍 Tekshirish"
        ms3 = "⏭️ O'tkazib yuborish"
        ms4 = "✅ Ushbu kanalga qo'shiling va mukofot sifatida 5 ta Unity Coinga ega bo'ling! 🎉\n\n⬇️ Obuna bo'lish uchun quyidagi tugmani bosing:"
    elif ln == "ru":
        ms1 = "✅ Подписаться"
        ms2 = "🔍 Проверить"
        ms3 = "⏭️ Пропустить"
        ms4 = "✅ Присоединяйтесь к этому каналу и получите 5 монет Unity в награду! 🎉\n\n⬇️ Нажмите кнопку ниже, чтобы подписаться:"
    else:
        ms1 = "✅ Subscribe"
        ms2 = "🔍 Check"
        ms3 = "⏭️ Skip"
        ms4 = "✅ Join this channel and receive 5 Unity Coins as a reward! 🎉\n\n⬇️ Click the button below to subscribe:"
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=ms1, url=channel_link)
    keyboard.button(text=ms2, callback_data=f"check_sub:{channel_id}")
    keyboard.button(text=ms3, callback_data=f"skip_sub:{channel_id}")
    keyboard.adjust(1)

    await message.answer(ms4, reply_markup=keyboard.as_markup())


@dp.callback_query(lambda c: c.data.startswith("check_sub:"))
async def check_subscription(callback: types.CallbackQuery):
    channel_id = callback.data.split(":")[1]
    user_id = callback.from_user.id
    ln = get_user_language(user_id)
    if ln == "uz":
        ms12 = "🎉 Sizga 5 Unity Coin berildi."
        ms22 = "Obuna bo'lish uchun boshqa kanallar yo'q 😓"
    elif ln == "ru":
        ms12 = "🎉 Вы получили 5 Unity Coin"
        ms22 = "Пока нет каналов, на которые можно подписаться 😓"
    else:
        ms12 = "🎉 You have been awarded 5 Unity Coins."
        ms22 = "There are no channels to subscribe to yet 😓"
    if ln == "uz":
        ms1 = "✅ Kanalga qo'shilish"
        ms2 = "🔍 Tekshirish"
        ms3 = "⏭️ O'tkazib yuborish"
        ms4 = "✅ Ushbu kanalga qo'shiling va mukofot sifatida 5 ta Unity Coinga ega bo'ling! 🎉\n\n⬇️ Obuna bo'lish uchun quyidagi tugmani bosing:"
        ms5 = "🚨 Siz hali obuna bo'lmagansiz!"
    elif ln == "ru":
        ms1 = "✅ Подписаться"
        ms2 = "🔍 Проверить"
        ms3 = "⏭️ Пропустить"
        ms4 = "✅ Присоединяйтесь к этому каналу и получите 5 монет Unity в награду! 🎉\n\n⬇️ Нажмите кнопку ниже, чтобы подписаться:"
        ms5 = "🚨 Вы еще не подписаны!"
    else:
        ms1 = "✅ Subscribe"
        ms2 = "🔍 Check"
        ms3 = "⏭️ Skip"
        ms4 = "✅ Join this channel and receive 5 Unity Coins as a reward! 🎉\n\n⬇️ Click the button below to subscribe:"
        ms5 = "🚨 You are not subscribed yet!"
    member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)

    if member.status in ["member", "administrator", "creator"]:
        save_subscription(user_id, channel_id)
        new_channels = get_unsubscribed_channels(user_id)
        conn = sqlite3.connect("users_database.db")
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users_database SET unity_coin = unity_coin + ? WHERE user_id = ?",
            (5, user_id),
        )
        conn.commit()
        conn.close()

        await callback.message.edit_text(ms12)
        channels = get_unsubscribed_channels(user_id)
        if not channels:
            await callback.message.answer(ms22)
            return

        channel_id, channel_link = channels

        keyboard = InlineKeyboardBuilder()
        keyboard.button(text=ms1, url=channel_link)
        keyboard.button(text=ms2, callback_data=f"check_sub:{channel_id}")
        keyboard.button(text=ms3, callback_data=f"skip_sub:{channel_id}")
        keyboard.adjust(1)

        await callback.message.answer(
            ms4,
            reply_markup=keyboard.as_markup(),
        )

    else:
        await callback.answer(ms5, show_alert=True)


@dp.callback_query(lambda c: c.data.startswith("skip_sub:"))
async def skip_subscription(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    channel_id = callback.data.split(":")[1]

    save_subscription(user_id, channel_id)
    await callback.message.delete()
    ln = get_user_language(user_id)
    if ln == "uz":
        ms12 = "🎉 Sizga 5 Unity Coin berildi."
        ms22 = "Obuna bo'lish uchun boshqa kanallar yo'q 😓"
    elif ln == "ru":
        ms12 = "🎉 Вы получили 5 Unity Coin"
        ms22 = "Пока нет каналов, на которые можно подписаться 😓"
    else:
        ms12 = "🎉 You have been awarded 5 Unity Coins."
        ms22 = "There are no channels to subscribe to yet 😓"
    if ln == "uz":
        ms1 = "✅ Kanalga qo'shilish"
        ms2 = "🔍 Tekshirish"
        ms3 = "⏭️ O'tkazib yuborish"
        ms4 = "✅ Ushbu kanalga qo'shiling va mukofot sifatida 5 ta Unity Coinga ega bo'ling! 🎉\n\n⬇️ Obuna bo'lish uchun quyidagi tugmani bosing:"
        ms5 = "🚨 Siz hali obuna bo'lmagansiz!"
    elif ln == "ru":
        ms1 = "✅ Подписаться"
        ms2 = "🔍 Проверить"
        ms3 = "⏭️ Пропустить"
        ms4 = "✅ Присоединяйтесь к этому каналу и получите 5 монет Unity в награду! 🎉\n\n⬇️ Нажмите кнопку ниже, чтобы подписаться:"
        ms5 = "🚨 Вы еще не подписаны!"
    else:
        ms1 = "✅ Subscribe"
        ms2 = "🔍 Check"
        ms3 = "⏭️ Skip"
        ms4 = "✅ Join this channel and receive 5 Unity Coins as a reward! 🎉\n\n⬇️ Click the button below to subscribe:"
        ms5 = "🚨 You are not subscribed yet!"
    channels = get_unsubscribed_channels(user_id)
    if not channels:
        await callback.message.answer(ms22)
        return

    channel_id, channel_link = channels

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=ms1, url=channel_link)
    keyboard.button(text=ms2, callback_data=f"check_sub:{channel_id}")
    keyboard.button(text=ms3, callback_data=f"skip_sub:{channel_id}")
    keyboard.adjust(1)

    await callback.message.answer(
        ms4,
        reply_markup=keyboard.as_markup(),
    )


from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    LabeledPrice,
    PreCheckoutQuery,
)


@dp.message(F.text.in_(["🛍 shop", "🛍 do'kon", "🛍 магазин"]))
async def buying_(message: types.Message):
    user_id = message.from_user.id
    ln = get_user_language(user_id)

    if ln == "uz":
        ms12 = (
            "🛒 Liar's Fortune do'koni ga xush kelibsiz!\n\n"
            "🎲 O'zingizga kerakli narsalarni harid qiling va ulardan o'yinda foydalanishdan zavqlaning, yoki ko'proq pul ishlash imkoniyatingizni oshiring. 🛍😊\n\nHozirda mavjud mahsulotlar 👇"
        )

    elif ln == "ru":
        ms12 = (
            "🛒 Добро пожаловать в магазин Liar's Fortune!\n\n"
            "🎲 Купите инструменты и наслаждайтесь их использованием в игре или увеличьте свои шансы заработать больше. 🛍😊\nТекущие доступные продукты 👇"
        )

    else:
        ms12 = (
            "🛒 Добро пожаловать в магазин Liar's Fortune!\n\n"
            "🎲 Купите инструменты и наслаждайтесь их использованием в игре или увеличьте свои шансы заработать больше. 🛍😊\nТекущие доступные продукты 👇"
        )
        # ms12 = (
        #     "🛒 Welcome to the Liar's Fortune Shop!\n\n"
        #     "🎲 Buy tools and enjoy using them in a game or increase your chance to earn more. 🛍😊\nCurrently available products 👇"
        # )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="skip 🪓", callback_data="buy_skip_pass"),
                InlineKeyboardButton(text="block ⛔️", callback_data="buy_block_press"),
                InlineKeyboardButton(
                    text="change 🔄", callback_data="buy_card_changer"
                ),
            ],
        ]
    )

    await message.answer(ms12, reply_markup=keyboard)


@dp.callback_query(F.data.startswith("buy_"))
async def process_purchase(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    tool_key = callback.data.replace("buy_", "")
    price = get_tool_prices()[tool_key]
    ln = get_user_language(user_id)
    if tool_key == "skip_pass":
        toolname = "skip 🪓"
        if ln == "uz":
            vazifa = "Keyingi o'yinchining navbatini o'tkazib yuboradi ✔️"
        elif ln == "ru":
            vazifa = "Пропускает ход следующего игрока ✔️"
        else:
            vazifa = "Skips the next player's turn ✔️"
    elif tool_key == "block_press":
        toolname = "block ⛔️"
        if ln == "uz":
            vazifa = "Keyingi o'yinchi sizni yolg'onchi deb topa olmaydi ✔️"
        elif ln == "ru":
            vazifa = "Следующий игрок не сможет признать тебя лжецом ✔️"
        else:
            vazifa = "The next player can't press a liar ✔️"

    else:
        toolname = "change 🔄"
        if ln == "uz":
            vazifa = "Tashlangan barcha kartalarni bosh karta bilan bir xil ko'rinishga keltirib beradi ✔️"
        elif ln == "ru":
            vazifa = "Делает все отправленные карты такими же, как и основная карта ✔️"
        else:
            vazifa = "Changes all sent cards to a table card ✔️"
    # if ln == "uz":
    purtit = "Xarid"
    desc = (
        f"🛍 Mahsulot: {toolname}\n"
        f"💰 Narxi: {price} star ⭐️\n"
        f"🎭 Vazifasi: {vazifa}\n"
        f"🕐 Foydalanish: Kartani tashlashdan oldin aktiv (✅) holatda bo'lishi kerak.\n\n"
        f"Sotib olish uchun pastdagi tugmani bosing. 👇"
    )
    # elif ln == "en":
    #     purtit = "Purchase"
    #     desc = (
    #         f"🛍 Item: {toolname}\n"  # Added \n here
    #         f"💰 Price: {price} star ⭐️\n"
    #         f"🎭 Task: {vazifa}\n"
    #         f"🕐 Usage: It has to be activated before sending cards.\n\n"
    #         f"➤ Press the button below to purchase. 👇"
    #     )
    # else:
    #     purtit = "Покупка"
    #     desc = (
    #         f"🛍 Продукт: {toolname}\n"
    #         f"💰 Цена: {price} star ⭐️\n"
    #         f"🎭 Задача: {vazifa}\n"
    #         f"🕐 Использование: Перед отправкой карты должны быть активны (✅).\n\n"
    #         f"Для покупки нажмите на кнопку ниже. 👇"
    #     )
    await bot.send_invoice(
        chat_id=user_id,
        title=purtit,
        description=desc,
        payload=f"tool_{tool_key}",
        provider_token="TELEGRAM_STARS",
        currency="XTR",
        prices=[LabeledPrice(label=f"{tool_key.title()}", amount=price)],
        start_parameter=f"buy_tool_{tool_key}",
    )


@dp.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


ADMIN_ID = 1155076760


@dp.message(F.successful_payment)
async def payment_success(message: types.Message):
    user_id = message.from_user.id
    tool_key = message.successful_payment.invoice_payload.split("tool_")[-1]

    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    skipper = 1 if tool_key == "skip_pass" else 0
    blocker = 1 if tool_key == "block_press" else 0
    changer = 1 if tool_key == "card_changer" else 0

    cursor.execute(
        """
        INSERT INTO supper_tool (user_id, skipper, blocker, changer)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET 
            skipper = skipper + ?,
            blocker = blocker + ?,
            changer = changer + ?
        """,
        (user_id, skipper, blocker, changer, skipper, blocker, changer),
    )

    conn.commit()
    conn.close()

    await message.answer(
        f"✅ You have successfully purchased {tool_key.replace('_', ' ')}! 🎉"
    )

    payment = message.successful_payment

    # await message.answer("If you want to refund your purchase, resend this message to the bot 👇:")
    # await message.answer(f"refund {payment.telegram_payment_charge_id}")

    await bot.send_message(
        ADMIN_ID,
        f"🛍 Purchase Alert\n"
        f"👤 User: {message.from_user.id}\n"
        f"💳 Bought: {tool_key.replace('_', ' ')}\n"
        f"💰 Price: {get_tool_prices()[tool_key]} Stars\n\n"
        f"♻️ Refund key: {payment.telegram_payment_charge_id}",
    )


# CARD_PRICES = {
#     "card_1": 1,  # 🃏 Card 1 costs 100 Stars
#     "card_2": 250,  # 🎭 Card 2 costs 250 Stars
#     "card_3": 500,  # 💎 Card 3 costs 500 Stars
# }


# @dp.message(F.text == "checkkk")
# async def buy_card(callback: types.Message):
#     user_id = callback.from_user.id
#     card_key = "card_1"

#     if card_key not in CARD_PRICES:
#         return await callback.answer("❌ Invalid selection.", show_alert=True)

#     price = CARD_PRICES[card_key]

#     await bot.send_invoice(
#         chat_id=user_id,
#         title="Purchase Card",
#         description=f"Buy this card for {price} Stars!",
#         payload=f"card_{card_key}",
#         provider_token="TELEGRAM_STARS",
#         currency="XTR",
#         prices=[LabeledPrice(label=f"Card {card_key}", amount=price)],
#         start_parameter=f"buy_card_{card_key}",
#     )


# @dp.pre_checkout_query()
# async def pre_checkout(pre_checkout_query: PreCheckoutQuery):
#     await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


# @dp.message(F.successful_payment)
# async def payment_success(message: types.Message):
#     user_id = message.from_user.id
#     card_key = message.successful_payment.invoice_payload.split("_")[-1]

#     await message.answer(
#         f"✅ You have successfully purchased *Card {card_key}*! 🎉",
#         parse_mode="MarkdownV2",
#     )

#     await bot.send_message(
#         ADMIN_ID,
#         f"🛍 *Purchase Alert*\n👤 User: [{message.from_user.full_name}](tg://user?id={user_id})\n💳 Bought: *Card {card_key}*\n💰 Price: {CARD_PRICES[card_key]} Stars",
#         parse_mode="MarkdownV2",
#     )


@dp.message(F.text.startswith("refund"))
async def refund_request(message: types.Message):
    try:
        trsn = message.text.split(" ")[-1]
        user_id = int(message.from_user.id)

        await bot.refund_star_payment(
            user_id,
            telegram_payment_charge_id=trsn,
        )

        await message.answer(f"✅ Successfully refunded.")

    except Exception as e:
        await message.answer(f"❌ Error processing refund: {e}")
