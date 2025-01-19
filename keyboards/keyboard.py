from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import sqlite3
def is_user_admin(user_id):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None
def get_main_menu(user_id: int):
    is_admin = is_user_admin(user_id)
    keyboard = [
        [
            KeyboardButton(text="start game 🎮"),      
            KeyboardButton(text="game status 🌟"),      
        ],
        [
            KeyboardButton(text="🎯 game archive"),
            KeyboardButton(text="how to play 📝"),
        ],
        [
            KeyboardButton(text="information 📚"),
            KeyboardButton(text="settings ⚙️"),
            
        ],
    ]
    if is_admin:
        keyboard.append([KeyboardButton(text="🧑‍💻 admin panel")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


change_name = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="change name 🖌"),
            KeyboardButton(text="❓ help"),
        ],
        [
            KeyboardButton(text="back to main menu 🔙"),
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

cancel_button = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="back to main menu 🔙")]],
    resize_keyboard=True,
)


admin_panel_button = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🎯 Game archive"),
            KeyboardButton(text="🏆 tournaments"),
        ],
        [
            KeyboardButton(text="👤 Admins"),
            KeyboardButton(text="🧑‍🎓 users"),
        ],
        [
            KeyboardButton(text="📊 statistics"),
            KeyboardButton(text="📤 send message"),
        ],
        [
            KeyboardButton(text="🔙 main menu"),
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