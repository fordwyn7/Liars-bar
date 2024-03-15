from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


KEYBOAR_NAME = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="TEXT_OF_KEYBOARD"),KeyboardButton(text="TEXT_OF_KEYBOARD"),
        ],
        [
            KeyboardButton(text="TEXT_OF_KEYBOARD_2"),
        ],
        [
            KeyboardButton(text="TEXT_OF_KEYBOARD_3"),KeyboardButton(text="TEXT_OF_KEYBOARD_4"),KeyboardButton(text="TEXT_OF_KEYBOARD_5"),
        ],
    ],
    resize_keyboard=True,
)
