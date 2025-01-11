import asyncio
import logging
import sqlite3
import uuid
import hendlers
import register
from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.deep_linking import create_start_link
from config import *
from keyboards.keyboard import main_menu, count_players, change_name
from states.state import registration, registration_game, new_game
from keyboards.inline import *
from db import *
from aiogram.types import Update


conn = sqlite3.connect("users_database.db")
cursor = conn.cursor()
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS users_database (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    registration_date TEXT, 
    nfgame TEXT
)
"""
)
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS users_game_states (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    game_id_user TEXT,
    messages_ingame TEXT,
)
"""
)
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS invitations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        inviter_id INTEGER,
        invitee_id INTEGER,
        game_id TEXT,
        players_cnt INTEGER,
        needed_players INTEGER,
        is_started INTEGER,
        current_turn_user_id INTEGER,  
        number_of_cards INTEGER,
        FOREIGN KEY(inviter_id) REFERENCES users_database(user_id),
        FOREIGN KEY(invitee_id) REFERENCES users_database(user_id)
    )
    """
)

cursor.execute(
    """
        CREATE TABLE IF NOT EXISTS game_state (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id TEXT,
            player_id TEXT,
            cards TEXT,
            last_cards TEXT,
            current_table TEXT, 
            real_bullet TEXT,
            blanks_count INTEGER,
            life_status INTEGER,
            UNIQUE(game_id, player_id)
        )
    """
)

conn.commit()
conn.close()


@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    payload = message.text.split(" ", 1)[-1] if " " in message.text else ""
    await state.update_data(payload=payload)
    if "game_" in payload:
        if not is_user_registered(message.from_user.id):
            await message.answer("Welcome to the bot! Please enter your name:")
            await state.set_state(registration_game.pref1_name)
            return
        game_id = payload.split("game_")[1]
        if get_player_count(game_id) == 0:
            await message.answer(
                f"Game has already finished or been stopped. ☹️", reply_markup=main_menu
            )
            return
        if game_id == get_game_id_by_user(message.from_user.id):
            if message.from_user.id == get_game_inviter_id(game_id):
                await message.answer(
                    "You are already in this game as a creator", reply_markup=main_menu
                )
            else:
                await message.answer(
                    "You are already in this game! 😇", reply_markup=cancel_g
                )
            return
        if get_needed_players(game_id) <= get_player_count(game_id):
            await message.answer(
                f"There is no available space for another player or the game has already finished 😞",
                reply_markup=main_menu,
            )

            await state.clear()
            return
        user = message.from_user
        inviter_id = get_game_inviter_id(game_id)
        if not inviter_id:
            await message.answer(
                f"This game has finished or been stopped by the creator.",
                reply_markup=main_menu,
            )
            await state.clear()
            return
        if inviter_id and inviter_id == user.id:
            await message.answer("You are already in this game as the creator!")
            return
        if is_user_in_game(game_id, user.id):
            await message.answer("You are already in this game!", reply_markup=cancel_g)
            return
        if not inviter_id:
            await message.answer(
                f"This game has finished or been stopped by the creator.",
                reply_markup=main_menu,
            )

            await state.clear()
            return
        if has_incomplete_games(message.from_user.id):
            await message.answer(
                f"You have incomplete games! \nPlease stop them first and try again.",
                reply_markup=stop_incomplete_games,
            )

            await state.clear()
            return
        insert_invitation(inviter_id, user.id, game_id)
        player_count = get_player_count(game_id)
        if player_count < 2:
            await message.answer(
                f"This game has finished or been stopped by the creator.",
                reply_markup=main_menu,
            )
            await state.clear()
            return

        await message.answer(
            f"You have successfully joined the game! 🤩\nCurrent number of players: {player_count}\nWaiting for everyone to be ready...",
            reply_markup=cancel_g,
        )

        name = get_user_nfgame(user.id)
        await bot.send_message(
            inviter_id,
            f"User {name} has joined the game!\nPlayers in the game: {player_count}",
        )
        if get_needed_players(game_id) == get_player_count(game_id):
            await bot.send_message(
                inviter_id,
                f"All players ready. You can start the game right now.",
                reply_markup=start_stop_game,
            )
        await state.clear()
    else:
        user = message.from_user
        if is_user_registered(user.id):
            await message.answer(
                "Welcome back! You are in the main menu.", reply_markup=main_menu
            )
        else:
            await message.answer("Welcome to the bot! Please enter your name:")
            await state.clear()
            await state.set_state(registration.pref_name)


@dp.message(F.text == "start game 🎮")
async def start_game_handler(message: types.Message, state: FSMContext):
    if message.chat.type == "private":
        if has_incomplete_games(message.from_user.id):
            await message.answer(
                "You have incomplete games. Please finish or stop them before creating a new one.",
                reply_markup=stop_incomplete_games,
            )

            return
        await message.answer(
            "Choose the number of players: ⬇️", reply_markup=count_players
        )
        await state.set_state(new_game.number_of_players)
    else:
        await message.answer("Please use this option in a private chat.")


@dp.message(F.text == "back to main menu 🔙")
async def start_game_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"You are in main manu.",
        reply_markup=main_menu,
    )


@dp.message(new_game.number_of_players)
async def get_name(message: types.Message, state: FSMContext):
    cnt = 0
    if message.text == "2️⃣":
        cnt = 2
    elif message.text == "3️⃣":
        cnt = 3
    elif message.text == "4️⃣":
        cnt = 4
    else:
        await message.answer(
            "You have entered wrong information! Please choose one of these numbers: ⬇️",
            reply_markup=count_players,
        )
        await state.set_state(new_game.number_of_players)
        return

    user = message.from_user
    game_id = str(uuid.uuid4())
    invite_link = await create_start_link(bot, payload=f"game_{game_id}")
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO invitations (inviter_id, game_id, needed_players)
        VALUES (?, ?, ?)
        """,
        (user.id, game_id, cnt),
    )
    conn.commit()
    conn.close()
    await message.answer(
        f"Here is your invitation link. Share this link with your friends to play the game together👇. Game starts as soon as {cnt} players gathered.",
        reply_markup=main_menu,
    )

    sharable_message = (
        "🎮 **Join the Game!** 🎮\n\n"
        "I just created a game, and I'd love for you to join!\n\n"
        "Click the link below to join the game:\n"
        f"\n{invite_link}\n\n"
    )

    await message.answer(
        sharable_message,
    )
    await state.clear()


@dp.message(F.text == "game status 🌟")
async def start_game_handler(message: types.Message, state: FSMContext):
    game_id = get_game_id_by_user(message.from_user.id)
    if not has_incomplete_games(message.from_user.id):
        await message.answer(
            f"You are not participating in any game currently.", reply_markup=main_menu
        )
    else:
        msg = f"Current game status: active ✅\n"
        if message.from_user.id == get_game_inviter_id(game_id):
            msg += f"You are creator of this game 👨‍💻\nNumber of participants: {get_player_count(game_id)}"
            await message.answer(msg, reply_markup=generate_exclude_keyboard(game_id))
        else:
            msg += f"You are participant in this game 👤\nNumber of participants: {get_player_count(game_id)}"
            await message.answer(msg, reply_markup=cancel_g)


@dp.message()
async def any_word(msg: types.Message, state: FSMContext):
    await msg.answer(f"You entered unfamiliar information.")


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
