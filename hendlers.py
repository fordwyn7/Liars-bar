import sqlite3
from config import dp, F, bot
from aiogram import types
from aiogram.fsm.context import FSMContext
from keyboards.keyboard import change_name, main_menu, cancel_button
from states.state import NewGameState, MessagetoAdmin, messagetouser
from db import (
    get_user_nfgame,
    is_name_valid,
    is_game_started,
    get_game_id_by_user,
    get_total_users,
)


@dp.message(F.text == "/send")
async def send_message_to(message: types.Message, state:FSMContext):
    if message.from_user.id == 6807731973:
        await message.answer(f"Write the ID of user and then the message in SEPARATE line. ")
        await state.set_state(messagetouser.messag)
    else:
        await message.answer(f"You entered unfamiliar information.")
@dp.message(messagetouser.messag)
async def state_send_msg(message: types.Message, state: FSMContext):
    user_id_va = message.text.split("\n")[0]
    await bot.send_message(chat_id=int(user_id_va), text=message.text.split("\n")[1])
    await message.answer("Your message has been sent successfully ✅")

@dp.message(F.text == "settings ⚙️")
async def settings(message: types.Message):
    await message.answer(f"Choose one of these options: ⬇️", reply_markup=change_name)


@dp.message(F.text == "❓ help")
async def help_butn(message: types.Message, state: FSMContext):
    await message.answer(
        "If you have any questions or suggestions, feel free to write here. An admin will respond as soon as possible. ⬇️",
        reply_markup=cancel_button,
    )

    await state.set_state(MessagetoAdmin.msgt)


@dp.message(MessagetoAdmin.msgt)
async def help_button_state(message: types.Message, state: FSMContext):
    if message.text != "back to main menu 🔙":
        await bot.send_message(
            chat_id=6807731973,
            text=f"User — {message.from_user.first_name} (<a href='tg://openmessage?user_id={message.from_user.id}'>{message.from_user.id}</a>) sent you message: \n{message.text}",
            parse_mode="HTML",
        )
        await message.answer(
            "Your message has been sent successfully ✅",
            reply_markup=main_menu,
        )

        await state.clear()
    else:
        await state.clear()
        await message.answer(
            f"You are in main menu 👇",
            reply_markup=main_menu,
        )


@dp.message(F.text == "change name 🖌")
async def changeee(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"Your current name is: {get_user_nfgame(message.from_user.id)}\nIf you'd like to change it, please type your new name:",
        reply_markup=cancel_button,
    )
    await state.set_state(NewGameState.waiting_for_nfgame)


@dp.message(NewGameState.waiting_for_nfgame)
async def set_new_nfgame(message: types.Message, state: FSMContext):
    new_nfgame = message.text
    if is_game_started(get_game_id_by_user(message.from_user.id)):
        await message.answer(
            f"You are currently participating in a game and cannot change your name until the game ends.",
            reply_markup=main_menu,
        )
        await state.clear()
        return
    if new_nfgame == "back to main menu 🔙":
        await state.clear()
        await message.answer(f"You are in main menu ⬇️", reply_markup=main_menu)
        return
    h = is_name_valid(new_nfgame)
    if h == 1:
        await message.answer(
            f"The length of the name must not exceed 30 characters."
        )
    else:
        user_id = message.from_user.id
        with sqlite3.connect("users_database.db") as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users_database SET nfgame = ? WHERE user_id = ?",
                (new_nfgame, user_id),
            )
            conn.commit()
        await message.answer(
            f"Your name has been successfully changed to: {new_nfgame} ✅",
            reply_markup=main_menu,
        )

        await state.clear()


@dp.message(F.text == "cancel 🚫")
async def cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"You have canceled changing the name.", reply_markup=main_menu
    )


@dp.message(F.text == "statistics 📊")
async def cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"Here are the bot's statistics 📈:\n\nTotal users in the bot 👥: {get_total_users()}\nBot has been active since 01.03.2024 📅",
        reply_markup=main_menu,
    )


@dp.message(F.text == "how to play 📝")
async def cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "📔 Game Rules 📔\n\n"
        "🔴 Each game requires at least 2️⃣ players (up to 4️⃣).\n"
        "🔴 Each player receives 5️⃣ cards randomly at the start of the game.\n"
        "🔴 At the beginning of the game, there will be information about the total cards and the table card.\n"
        "  ⚫️ Table card: This is the card that all players must match.\n\n"
        "🔴 The first turn will be chosen randomly by the bot. After that, the remaining players take turns in order.\n\n"
        "Card Details:\n"
        "⚪️ Each game includes 2️⃣ universal cards 🎴 and a Joker card 🃏.\n"
        "⚪️ A universal card can be used in place of the current table card.\n\n"
        "Gameplay:\n"
        "1. On your turn, you can send up to 3️⃣ cards at once.\n"
        "2. The next player will receive a message indicating how many cards you sent.\n"
        "3. They can choose to press the Liar button.\n\n"
        "   ⚫️ If the Liar button is pressed, the cards you sent will be revealed.\n"
        "     ⚫️ If there is at least one card that doesn't match either the universal card or the table card, you will be declared a liar and must shoot yourself.\n"
        "     ⚫️ However, if all your cards are correct, the player who pressed the Liar button will shoot themselves instead.\n\n"
        "Special Case:\n"
        "🔵 Joker Card 🃏:\n"
        "  ⚫️ If the Joker card is sent alone and the next player opens it, all players will shoot themselves except for the player who sent the Joker.\n\n"
        "Additional Rules:\n"
        "🔵 If you have no cards left, you will skip your turn until you receive new cards.\n"
        "🔵 Each time the Liar button is pressed, all cards will be redistributed.\n"
        "🔵 There are 6 bullets in your gun, but only 1 is real—the others are blanks, and no one knows which bullet is real.\n\n"
        "The game continues until only one player remains."
    )
