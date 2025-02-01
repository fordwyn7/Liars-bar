from config import bot, dp
from aiogram import types
from aiogram.fsm.context import FSMContext
from states.state import registration, registration_game
from keyboards.keyboard import get_main_menu
from keyboards.inline import (
    cancel_g,
    ban_user,
    generate_exclude_keyboard,
    start_stop_game,
)
from db import (
    register_user,
    is_user_registered,
    insert_invitation,
    get_game_inviter_id,
    get_player_count,
    get_needed_players,
    get_game_id_by_user,
    get_game_inviter_id,
    is_name_valid,
)
import sqlite3


@dp.message(registration.pref_name)
async def get_name(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    payload = user_data.get("payload", "")
    await bot.send_message(chat_id=1155076760, text=f"{payload}.")
    preferred_name = message.text.strip()
    if "/start" in message.text:
        await message.answer("Please enter your username first.")
        return
    h = is_name_valid(preferred_name)
    if not h:
        await message.answer(
            "Your data is incorrect! Please enter your username in a given format")
    elif h == 2:
        await message.answer("There is already user with this username in the bot. Please enter another username.")
    else:
        user = message.from_user
        
        register_user(
            user.id, user.username, user.first_name, user.last_name, preferred_name
        )
        await message.answer(
            f"🎉\nCongratulations on successfully registering, {preferred_name}!\nChoose one of these options 👇",
            reply_markup=get_main_menu(message.from_user.id),
        )

        await state.clear()


@dp.message(registration_game.pref1_name)
async def get_name(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    payload = user_data.get("payload", "")
    if "/start" in message.text:
        await message.answer("Please enter your username first.")
    if payload.startswith("game_"):
        game_id = payload.split("game_")[1]
        inviter_id = get_game_inviter_id(game_id)
        user = message.from_user
        preferred_name = message.text
        h = is_name_valid(preferred_name)
        if not h:
            await message.answer(
                f"Your data is incorrect! Please enter your username in a given format"
            )
        elif h == 2:
            await message.answer(
                "There is already user with this username in the bot. Please enter another username."
            )
        else:
            register_user(
                user.id, user.username, user.first_name, user.last_name, preferred_name
            )
            if not inviter_id:
                await message.answer(
                    "No game found with that ID or it has already finished.",
                    reply_markup=get_main_menu(message.from_user.id),
                )
                return
            if game_id == get_game_id_by_user(message.from_user.id):
                if message.from_user.id == get_game_inviter_id(game_id):
                    await message.answer(
                        "You are already in this game as a creator 😇",
                        reply_markup=get_main_menu(message.from_user.id),
                    )
                else:
                    await message.answer(
                        "You are already in this game! 😇", reply_markup=cancel_g
                    )
                return
            if get_player_count(game_id) == 0:
                await message.answer(
                    f"Game has already finished or been stopped. ☹️",
                    reply_markup=get_main_menu(message.from_user.id),
                )
                return

            if get_needed_players(game_id) <= get_player_count(game_id):
                await message.answer(
                    f"There is no available space for another player or the game has already finished 😞",
                    reply_markup=get_main_menu(message.from_user.id),
                )

                await state.clear()
                return
            insert_invitation(inviter_id, user.id, game_id)
            player_count = get_player_count(game_id)
            await message.answer(
                f"🎉\nCongratulations on successfully registering, {preferred_name}!",
                reply_markup=get_main_menu(message.from_user.id),
            )
            await message.answer(
                f"You have successfully joined the game! 🤩\nCurrent number of players: {player_count}\nWaiting for everyone to be ready...",
                reply_markup=cancel_g,
            )

            await bot.send_message(
                inviter_id,
                f"User {preferred_name} has joined the game! 🎉\nPlayers in the game: {player_count}",
            )

            if get_needed_players(game_id) == get_player_count(game_id):
                await bot.send_message(
                    inviter_id,
                    f"All players ready. You can start the game right now. ",
                    reply_markup=start_stop_game,
                )

            await state.clear()
    else:
        await message.answer("Invalid game ID format. Please try again.")
