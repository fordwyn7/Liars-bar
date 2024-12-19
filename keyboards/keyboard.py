from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="start game 🎮"),
        ],
        [
            KeyboardButton(text="settings ⚙️"),
            KeyboardButton(text="game status 🌟"),
        ],
        [
            KeyboardButton(text="how to play 📝"),
            KeyboardButton(text="statistics 📊"),
        ],
    ],
    resize_keyboard=True,
)

change_name = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="change name 🖌"),
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
