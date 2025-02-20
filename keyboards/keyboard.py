from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import sqlite3


def get_user_language(user_id):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT language FROM user_languages WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return row[0]
    return "en"


def is_user_admin(user_id):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


main_earn_button = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="bonus 🚀"),
            KeyboardButton(text="mystery box 🎁"),
        ],
        [
            KeyboardButton(text="❄️ referral"),
            KeyboardButton(text="🤩 tournaments"),
        ],
        [
            KeyboardButton(text="Join channels 💎"),
            KeyboardButton(text="Dual Boost ⚡️"),
        ],
        [
            KeyboardButton(text="back to main menu 🔙"),
        ],
    ],
    resize_keyboard=True,
)

main_earn_button_ru = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="бонус 🚀"),
            KeyboardButton(text="Тайнбокс 🎁"),
        ],
        [
            KeyboardButton(text="❄️ реферал"),
            KeyboardButton(text="🤩 турниры"),
        ],
        [
            KeyboardButton(text="Подписаться 💎"),
            KeyboardButton(text="Буст x2 ⚡️"),
        ],
        [
            KeyboardButton(text="вернуться в главное меню 🔙"),
        ],
    ],
    resize_keyboard=True,
)

main_earn_button_uz = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="bonus 🚀"),
            KeyboardButton(text="sirli quti 🎁"),
        ],
        [
            KeyboardButton(text="❄️ referal"),
            KeyboardButton(text="🤩 turnirlar"),
        ],
        [
            KeyboardButton(text="obuna bo'lish 💎"),
            KeyboardButton(text="bust x2 ⚡️"),
        ],
        [
            KeyboardButton(text="bosh menuga qaytish 🔙"),
        ],
    ],
    resize_keyboard=True,
)


def get_main_menu(user_id: int):
    is_admin = is_user_admin(user_id)
    ln = get_user_language(user_id)
    if ln == "uz":
        st = "o'yinni boshlash 🎮"
        lb = "🏅 Liderbord"
        bb = "pul ishlash 💸"
        kb = "📱 kabinet"
        pz = "Sovg'alar 🎁"
        # rf = "❄️ referal"
        # tu = "🤩 turnirlar"
        gr = "o'yin qoidalari 📜"
        io = "ma'lumot 📚"
        ss = "sozlamalar ⚙️"
    elif ln == "ru":
        st = "новая игра 🎮"
        lb = "🏅 Лидербоард"
        bb = "зарабатывать 💸"
        kb = "📱 кабинет"
        pz = "Призы 🎁"
        # rf = "❄️ реферал"
        # tu = "🤩 турниры"
        gr = "правила игры 📜"
        io = "информация 📚"
        ss = "настройки ⚙️"
    else:
        st = "start game 🎮"
        lb = "🏅 Leaderboard"
        bb = "earn 💸"
        kb = "📱 cabinet"
        pz = "Prizes 🎁"
        # rf = "❄️ referral"
        # tu = "🤩 tournaments"
        gr = "game rules 📜"
        io = "information 📚"
        ss = "settings ⚙️"
    keyboard = [
        [
            KeyboardButton(text=st),
            KeyboardButton(text=lb),
        ],
        [
            KeyboardButton(text=bb),
            KeyboardButton(text=pz),
        ],
        [
            KeyboardButton(text=kb),
            KeyboardButton(text=gr),
        ],
        [
            KeyboardButton(text=io),
            KeyboardButton(text=ss),
        ],
    ]
    if is_admin:
        keyboard.append([KeyboardButton(text="🧑‍💻 admin panel")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


change_name = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="change username 🖌"),
            KeyboardButton(text="change Language 🇺🇸"),
        ],
        [
            KeyboardButton(text="❓ help"),
            KeyboardButton(text="back to main menu 🔙"),
        ],
    ],
    resize_keyboard=True,
)

change_name_ru = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="изменить имя пользователя 🖌"),
            KeyboardButton(text="изменить язык 🇷🇺"),
        ],
        [
            KeyboardButton(text="❓ помощь"),
            KeyboardButton(text="вернуться в главное меню 🔙"),
        ],
    ],
    resize_keyboard=True,
)

change_name_uz = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="usernameni o'zgartirish  🖌"),
            KeyboardButton(text="Tilni o'zgartirish 🇺🇿"),
        ],
        [
            KeyboardButton(text="❓ yordam"),
            KeyboardButton(text="bosh menuga qaytish 🔙"),
        ],
    ],
    resize_keyboard=True,
)

count_players = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="2️⃣"),
            KeyboardButton(text="3️⃣"),
            KeyboardButton(text="4️⃣"),
        ],
        [KeyboardButton(text="back to main menu 🔙")],
    ],
    resize_keyboard=True,
)

count_players_ru = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="2️⃣"),
            KeyboardButton(text="3️⃣"),
            KeyboardButton(text="4️⃣"),
        ],
        [KeyboardButton(text="вернуться в главное меню 🔙")],
    ],
    resize_keyboard=True,
)

count_players_uz = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="2️⃣"),
            KeyboardButton(text="3️⃣"),
            KeyboardButton(text="4️⃣"),
        ],
        [KeyboardButton(text="bosh menuga qaytish 🔙")],
    ],
    resize_keyboard=True,
)

cancel_button = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="back to main menu 🔙")]],
    resize_keyboard=True,
)

cancel_button_ru = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="вернуться в главное меню 🔙")]],
    resize_keyboard=True,
)

cancel_button_uz = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="bosh menuga qaytish 🔙")]],
    resize_keyboard=True,
)

admin_panel_button = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🎯 Game archive"),
            KeyboardButton(text="🏆 tournaments"),
        ],
        [
            KeyboardButton(text="📊 statistics"),
            KeyboardButton(text="📤 send message"),
        ],
        [
            KeyboardButton(text="💳 user's balance"),
            KeyboardButton(text="✏️ change amount"),
        ],
        [
            KeyboardButton(text="👤 Admins"),
            KeyboardButton(text="🧑‍🎓 users"),
        ],
        [
            KeyboardButton(text="👨‍👩‍👦‍👦 refferals"),
            KeyboardButton(text="🔙 main menu"),
        ],
    ],
    resize_keyboard=True,
)

referrals_section_buttons = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🔝 Top referrals"),
            KeyboardButton(text="🔄 change referral amount"),
        ],
        [
            KeyboardButton(text="back to admin panel 🔙"),
        ],
    ],
    resize_keyboard=True,
)

change_amounts_buttons = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="💸 change game coins"),
            KeyboardButton(text="💰 withdraw change"),
        ],
        [
            KeyboardButton(text="back to admin panel 🔙"),
        ],
    ],
    resize_keyboard=True,
)

users_balance_button = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="➕ Add Unity Coins to All Users"),
            KeyboardButton(text="👀 View User Unity Coins"),
        ],
        [
            KeyboardButton(text="back to admin panel 🔙"),
        ],
    ],
    resize_keyboard=True,
)

change_users_balance = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="➕ Add Unity Coins"),
            KeyboardButton(text="➖ Subtract Unity Coins"),
        ],
        [
            KeyboardButton(text="back to admin panel 🔙"),
        ],
    ],
    resize_keyboard=True,
)

admins_list_button = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="➕ add admin"),
            KeyboardButton(text="🧾 list of admins"),
        ],
        [
            KeyboardButton(text="back to admin panel 🔙"),
        ],
    ],
    resize_keyboard=True,
)

back_button = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="cancel 🚫"),
        ],
    ],
    resize_keyboard=True,
)

back_button_ru = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="отмена 🚫"),
        ],
    ],
    resize_keyboard=True,
)

back_button_uz = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="bekor qilish 🚫"),
        ],
    ],
    resize_keyboard=True,
)

back_to_admin_panel = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="back to admin panel 🔙"),
        ],
    ],
    resize_keyboard=True,
)

send_messages = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📨 send message to all"),
            KeyboardButton(text="📩 send message to one"),
        ],
        [
            KeyboardButton(text="back to admin panel 🔙"),
        ],
    ],
    resize_keyboard=True,
)

users_control_button = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🪪 List of users"),
        ],
        [
            KeyboardButton(text="🗒 information of user"),
        ],
        [
            KeyboardButton(text="back to admin panel 🔙"),
        ],
    ],
    resize_keyboard=True,
)

tournaments_admin_panel_button = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="⚡️ Ongoing"),
            KeyboardButton(text="⏳ Upcoming"),
            KeyboardButton(text="🗂 Archive"),
        ],
        [
            KeyboardButton(text="➕ create a new Tournament"),
        ],
        [
            KeyboardButton(text="back to admin panel 🔙"),
        ],
    ],
    resize_keyboard=True,
)

upcoming_tournaments_button = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📝 edit starting"),
            KeyboardButton(text="🚫 delete the tournament"),
        ],
        [
            KeyboardButton(text="back to tournaments panel 🔙"),
        ],
    ],
    resize_keyboard=True,
)

ongoing_tournaments_button = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="✅ start the tournament"),
            KeyboardButton(text="👀 watch results"),
        ],
        [
            KeyboardButton(text="🚫 delete this tournament"),
            KeyboardButton(text="⛹️ players"),
        ],
        [
            KeyboardButton(text="back to tournaments panel 🔙"),
        ],
    ],
    resize_keyboard=True,
)

back_to_tournaments_button = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="back to tournaments panel 🔙"),
        ],
    ],
    resize_keyboard=True,
)
