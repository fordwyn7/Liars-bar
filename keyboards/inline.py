import sqlite3
import asyncio
import random
from config import bot, dp, F
from keyboards.keyboard import main_menu
from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.handlers import CallbackQueryHandler
from db import *
from game.game_state import send_random_cards_to_players, get_current_turn_user_id,get_next_player_id

start_stop_game = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Start the game ✅", callback_data="start_game"),
        ],
        [
            InlineKeyboardButton(text="Delete the game 🚫", callback_data="stop_game"),
        ],
    ]
)

ban_user = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Exclude the player 🚫", callback_data="exclude_player"
            ),
        ]
    ]
)

cancel_g = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="quit game 🚀", callback_data="cancel_game"),
        ]
    ]
)


@dp.callback_query(lambda c: c.data == "start_game")
async def start_game(callback_query: types.CallbackQuery):
    await bot.delete_message(
        callback_query.from_user.id, callback_query.message.message_id
    )
    game_id = get_game_id_by_user(callback_query.from_user.id)
    gn = get_needed_players(game_id)
    gp = get_player_count(game_id)
    suits = ["heart ❤️", "diamond ♦️", "spade ♠️", "club ♣️"]
    current_table = random.choice(suits)
    global cur_table
    cur_table = set_current_table(game_id, current_table)
    if gn == gp:
        players = get_all_players_in_game(game_id)
        ms1 = "Game starts in: "
        ms2 = "3️⃣"
        tasks = []
        cr_id = get_game_creator_id(game_id)
        players.remove(cr_id)
        for player in players:
            if player is None:
                print(f"Invalid player ID detected: {player}")
                continue
            tasks.append(send_game_start_messages(player, ms1, ms2, len(players)))
        if callback_query.from_user.id is None:
            await callback_query.answer("Invalid creator ID.", show_alert=True)
            return
        creator_sec = await bot.send_message(callback_query.from_user.id, ms1)
        creator_msg = await bot.send_message(callback_query.from_user.id, ms2)
        await asyncio.gather(
            periodically_edit_message(
                callback_query.from_user.id,
                creator_msg.message_id,
                creator_sec.message_id,
                len(players) + 1,
                cur_table,
                interval=1,
            ),
            *tasks,
        )
        arr = get_all_players_in_game(game_id)
        for i in arr:
            if not i:
                arr.remove(i)
        for play in arr:
            set_real_bullet_for_player(game_id, play)
        set_current_turn(game_id, random.choice(arr))
        save_player_cards(game_id)
        await send_random_cards_to_players(game_id)
        await callback_query.answer()
    else:
        dif = gn - gp
        if dif == 1:
            await bot.send_message(
                callback_query.from_user.id, f"1 player is needed to start the game!!!"
            )
        else:
            await bot.send_message(
                callback_query.from_user.id,
                f"{dif} players are needed to start the game!!!",
            )
        return


async def send_game_start_messages(player_id, ms1, ms2, lent):
    sec = await bot.send_message(player_id, ms1)
    msg = await bot.send_message(player_id, ms2)
    await periodically_edit_message(
        player_id, msg.message_id, sec.message_id, lent + 1, cur_table, interval=1
    )


def generate_exclude_keyboard(game_id):
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT invitee_id, (SELECT nfgame FROM users WHERE user_id = invitee_id) AS player_name
            FROM invitations
            WHERE game_id = ? AND invitee_id IS NOT NULL
            """,
            (game_id,),
        )
        players = cursor.fetchall()

    if not players:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Delete the game 🚫", callback_data="stop_game"
                    )
                ]
            ],
        )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"Exclude {player_name} 🚀",
                    callback_data=f"exclude_player:{invitee_id}",
                )
            ]
            for invitee_id, player_name in players
        ]
        + [
            [InlineKeyboardButton(text="Delete the game 🚫", callback_data="stop_game")]
        ],
    )

    return keyboard


@dp.callback_query(lambda c: c.data == "stop_game")
async def can_game(callback_query: types.CallbackQuery):
    user = callback_query.from_user
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        game_id = get_game_id_by_user(user.id)
        if not game_id:
            await callback_query.answer(
                "You are not currently the creator of any game."
            )
            return
        cursor.execute(
            "SELECT invitee_id FROM invitations WHERE game_id = ?", (game_id,)
        )
        players = cursor.fetchall()
        for player in players:
            player_id = player[0]
            if player_id is not None:
                delete_user_from_all_games(player_id)
                try:
                    await bot.send_message(
                        player_id,
                        "The game has been stopped or finished by the creator.",
                        reply_markup=main_menu,
                    )
                except Exception as e:
                    print(f"Error sending message to player {player_id}: {e}")

        cursor.execute(
            """
            DELETE FROM invitations 
            WHERE game_id = (
                SELECT game_id FROM invitations WHERE inviter_id = ? AND invitee_id IS NULL
            )
            """,
            (user.id,),
        )
        conn.commit()

        await callback_query.message.answer(
            "You have canceled the game. All players have been notified.",
            reply_markup=main_menu,
        )


async def player_quit_game(user_id, game_id, inviter_id):
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM invitations WHERE invitee_id = ? AND game_id = ?",
            (user_id, game_id),
        )
        conn.commit()
        cursor.execute("SELECT nfgame FROM users WHERE user_id = ?", (user_id,))
        player_name = cursor.fetchone()

        if player_name:
            player_name = get_user_nfgame(user_id)
            try:
                await bot.send_message(
                    inviter_id,
                    f"Player {player_name} has quit the game.\nPlayers left in the game: {get_player_count(game_id)}",
                )
                
            except Exception as e:
                print(f"Error sending message to creator {inviter_id}: {e}")


@dp.callback_query(lambda c: c.data == "cancel_game")
async def handle_quit_game(callback_query: types.CallbackQuery):
    await bot.delete_message(
        callback_query.from_user.id, callback_query.message.message_id
    )
    user = callback_query.from_user
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        game_id = get_game_id_by_user(user.id)
        if not game_id:
            await callback_query.answer("You are not currently in any game.")
            return
        if has_incomplete_games(user.id):
            if is_user_in_game(game_id, user.id) and get_current_turn_user_id(game_id) == user.id:
                await  callback_query.message.answer(
                f"Now it is your turn! You can't leave the game at that time🙅‍♂️"
            )
                return
            cursor.execute(
                "DELETE FROM invitations WHERE invitee_id = ? AND game_id = ?",
                (user.id, game_id),
            )
            conn.commit()
            inviter_id = get_game_inviter_id(game_id)
            await player_quit_game(user.id, game_id, inviter_id)
            await callback_query.message.answer(
                f"You have quit the current game.", reply_markup=main_menu
            )
            delete_user_from_all_games(user.id)
        else:
            await callback_query.message.answer("You have already quit the game.")


stop_incomplete_games = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Stop/leave current game 🛑", callback_data="stop_incomplete_games"
            )
        ]
    ]
)


@dp.callback_query(lambda c: c.data == "stop_incomplete_games")
async def handle_stop_incomplete_games(callback_query: types.CallbackQuery):
    await bot.delete_message(
        callback_query.from_user.id, callback_query.message.message_id
    )
    user_id = callback_query.from_user.id
    games = get_games_by_user(user_id)

    if not games:
        await callback_query.message.answer(
            "You have no incomplete games to stop.",
            reply_markup=main_menu,
        )
        await callback_query.answer()
        return

    for game in games:
        creator_id = get_game_inviter_id(game["game_id"])
        if user_id == creator_id:
            players = get_all_players_in_game(game["game_id"])
            for i in players:
                if not i:
                    players.remove(i)
            delete_game(game["game_id"])
            for player_id in players:
                delete_user_from_all_games(player_id)
                try:
                    await bot.send_message(
                        player_id,
                        "The game has been stopped by the creator.",
                        reply_markup=main_menu,
                    )
                except Exception as e:
                    print(f"Failed to send message to player {player_id}: {e}")
        else:
            delete_user_from_all_games(user_id)
            try:
                await bot.send_message(
                    creator_id,
                    f"A player {get_user_nfgame(callback_query.from_user.id)} has left the game.\nPlayers left in game: {get_player_count(get_game_id_by_user(creator_id))}",
                    reply_markup=main_menu,
                )
            except Exception as e:
                print(f"Failed to send message to creator {creator_id}: {e}")
    await callback_query.message.answer(
        "Your incomplete games have been stopped.",
        reply_markup=main_menu,
    )
    await callback_query.answer()


@dp.callback_query(lambda c: c.data.startswith("exclude_player:"))
async def exclude_player(callback_query: types.CallbackQuery):
    await bot.delete_message(
        callback_query.from_user.id, callback_query.message.message_id
    )
    user = callback_query.from_user
    data = callback_query.data.split(":")
    if len(data) != 2:
        await callback_query.answer("Invalid data.")
        return
    player_to_remove = int(data[1])

    game_id = get_game_id_by_user(user.id)
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT inviter_id FROM invitations WHERE game_id = ? AND invitee_id IS NULL",
            (game_id,),
        )
        inviter_id = cursor.fetchone()
        if not inviter_id or inviter_id[0] != user.id:
            await callback_query.answer("Only the game creator can exclude players.")
            return

        cursor.execute(
            "DELETE FROM invitations WHERE invitee_id = ? AND game_id = ?",
            (player_to_remove, game_id),
        )
        conn.commit()

    try:
        await bot.send_message(
            player_to_remove,
            "Game has finished or been stopped by the creator.",
            reply_markup=main_menu,
        )
    except Exception as e:
        print(f"Failed to send message to player {player_to_remove}: {e}")

    await callback_query.message.edit_text(
        f"Player excluded successfully. Remaining players: {get_player_count(game_id)}",
        reply_markup=generate_exclude_keyboard(game_id),
    )
