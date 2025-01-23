import sqlite3
import asyncio
import random
from config import bot, dp, F
from keyboards.keyboard import get_main_menu
from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.handlers import CallbackQueryHandler
from db import *
from game.game_state import (
    send_random_cards_to_players,
    get_current_turn_user_id,
    get_next_player_id,
)
from datetime import datetime, timezone, timedelta

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
                continue

            create_game_record_if_not_exists(game_id, player)
            # conn = sqlite3.connect("users_database.db")
            # cursor = conn.cursor()
            # cursor.execute(
            #     """
            # SELECT game_id, game_start_time
            # FROM game_archive
            # WHERE user_id = ?
            # """,
            #     (player,),
            # )
            # result = cursor.fetchone()
            # conn.close()

            # if result:
            #     game_id, start_time = result
            #     message_text = (
            #         f"🎮 Game Created Successfully!\n"
            #         f"Game ID: {game_id}\n"
            #         f"Start Time: {start_time}"
            #     )
            #     await bot.send_message(player, message_text)
            # else:
            #     await bot.send_message(
            #         player, "⚠️ No game record found for your user ID."
            #     )
            tasks.append(send_game_start_messages(player, ms1, ms2, len(players)))
        create_game_record_if_not_exists(game_id, cr_id)
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
    with sqlite3.connect("users_database.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT invitee_id, (SELECT nfgame FROM users_database WHERE user_id = invitee_id) AS player_name
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
    with sqlite3.connect("users_database.db") as conn:
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
                # await callback_query.message.answer(game_id + "       6")

                update_game_details(game_id, player, None)
                delete_user_from_all_games(player_id)
                try:
                    await bot.send_message(
                        player_id,
                        "The game has been stopped or finished by the creator.",
                        reply_markup=get_main_menu(player_id),
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
        # await callback_query.message.answer(game_id + "      5")
        update_game_details(game_id, callback_query.from_user.id, None)
        await callback_query.message.answer(
            "You have canceled the game. All players have been notified.",
            reply_markup=get_main_menu(callback_query.from_user.id),
        )
        await delete_all_game_messages(game_id)


async def player_quit_game(user_id, game_id, inviter_id):
    with sqlite3.connect("users_database.db") as conn:
        cursor = conn.cursor()
        # await bot.send_message.answer(user_id, game_id + "     4")
        update_game_details(game_id, user_id, None)
        cursor.execute(
            "DELETE FROM invitations WHERE invitee_id = ? AND game_id = ?",
            (user_id, game_id),
        )
        conn.commit()
        cursor.execute(
            "SELECT nfgame FROM users_database WHERE user_id = ?", (user_id,)
        )
        player_name = cursor.fetchone()

        if player_name:
            player_name = get_user_nfgame(user_id)
            try:
                await bot.send_message(
                    inviter_id,
                    f"Player {player_name} has quit the game.\nPlayers left in the game: {get_player_count(game_id)}",
                )
                await delete_user_messages(game_id, user_id)
            except Exception as e:
                print(f"Error sending message to creator {inviter_id}: {e}")


@dp.callback_query(lambda c: c.data == "cancel_game")
async def handle_quit_game(callback_query: types.CallbackQuery):
    await bot.delete_message(
        callback_query.from_user.id, callback_query.message.message_id
    )
    user = callback_query.from_user
    with sqlite3.connect("users_database.db") as conn:
        cursor = conn.cursor()
        game_id = get_game_id_by_user(user.id)
        if not game_id:
            await callback_query.answer("You are not currently in any game.")
            return
        if has_incomplete_games(user.id):
            if (
                is_user_in_game(game_id, user.id)
                and get_current_turn_user_id(game_id) == user.id
            ):
                await callback_query.message.answer(
                    f"Now it is your turn! You can't leave the game at that time🙅‍♂️"
                )
                return
            # await callback_query.message.answer(game_id+"    3")

            update_game_details(game_id, user.id, None)
            cursor.execute(
                "DELETE FROM invitations WHERE invitee_id = ? AND game_id = ?",
                (user.id, game_id),
            )
            conn.commit()
            inviter_id = get_game_inviter_id(game_id)
            await player_quit_game(user.id, game_id, inviter_id)
            await callback_query.message.answer(
                f"You have quit the current game.",
                reply_markup=get_main_menu(callback_query.from_user.id),
            )
            await delete_user_messages(game_id, user.id)
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
            reply_markup=get_main_menu(user_id),
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
                        reply_markup=get_main_menu(player_id),
                    )
                except Exception as e:
                    print(f"Failed to send message to player {player_id}: {e}")
        else:
            # await callback_query.message.answer(game["game_id"] + "    2")
            update_game_details(game["game_id"], user_id, None)
            delete_user_from_all_games(user_id)
            try:
                await bot.send_message(
                    creator_id,
                    f"A player {get_user_nfgame(callback_query.from_user.id)} has left the game.\nPlayers left in game: {get_player_count(get_game_id_by_user(creator_id))}",
                    reply_markup=get_main_menu(creator_id),
                )
            except Exception as e:
                print(f"Failed to send message to creator {creator_id}: {e}")
    await callback_query.message.answer(
        "Your incomplete games have been stopped.",
        reply_markup=get_main_menu(callback_query.from_user.id),
    )
    await delete_user_messages(game["game_id"], callback_query.from_user.id)
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
    with sqlite3.connect("users_database.db") as conn:
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
        # await callback_query.message.answer(game_id+"    1")
        update_game_details(game_id, player_to_remove, None)
    try:
        await bot.send_message(
            player_to_remove,
            "Game has finished or been stopped by the creator.",
            reply_markup=get_main_menu(player_to_remove),
        )
        await delete_user_messages(game_id, player_to_remove)
    except Exception as e:
        print(f"Failed to send message to player {player_to_remove}: {e}")

    await callback_query.message.edit_text(
        f"Player excluded successfully. Remaining players: {get_player_count(game_id)}",
        reply_markup=generate_exclude_keyboard(game_id),
    )


def get_join_tournament_button(tournament_id: str):
    inline_keyboard = InlineKeyboardMarkup()
    inline_keyboard.add(
        InlineKeyboardButton(
            text="🎮 Join the Tournament",
            callback_data=f"join_tournament:{tournament_id}",
        )
    )
    return inline_keyboard


user_tournaments_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⚡️ Ongoing Tournaments", callback_data="view_ongoing"
            )
        ],
        [
            InlineKeyboardButton(
                text="🌟 Upcoming Tournaments", callback_data="view_upcoming"
            )
        ],
        [
            InlineKeyboardButton(
                text="📑 Tournament Archive", callback_data="view_archive"
            )
        ],
    ]
)


@dp.callback_query(lambda c: c.data.startswith("view_"))
async def handle_tournament_action(callback_query: types.CallbackQuery):
    action = callback_query.data.split("_")[1]

    if action == "ongoing":
        await show_ongoing_tournaments(callback_query)
    elif action == "upcoming":
        await show_upcoming_tournaments(callback_query)
    elif action == "archive":
        await show_archive_tournaments(callback_query)


async def show_ongoing_tournaments(callback_query: types.CallbackQuery):
    tournaments = get_ongoing_tournaments()
    if not tournaments:
        await callback_query.message.answer(
            "No ongoing tournaments right now.",
            reply_markup=get_main_menu(callback_query.from_user.id),
        )
        return
    response = "⚡️ *Ongoing Tournaments:*\n\n"
    for tournament in tournaments:
        response += f"🏆 {tournament['name']} (Ends: {tournament['end_time']})\n"
    await callback_query.message.answer(response, parse_mode="Markdown")


async def show_upcoming_tournaments(callback_query: types.CallbackQuery):
    tournaments = get_upcoming_tournaments()
    if not tournaments:
        await callback_query.message.answer(
            "No upcoming tournaments scheduled.",
            reply_markup=get_main_menu(callback_query.from_user.id),
        )
        return
    
    for tournament in tournaments:
        if "_" in tournament['name']:
            nop = get_current_players(tournament['name'].split("_")[1])
        else:
            nop = get_current_players(tournament['name'])
        response = (
            f"🌟 Tournament ID: {tournament['id']}\n"
            f"🗓 Starts: {tournament['start_time']}\n"
            f"🏁 Ends: {tournament['end_time']}\n\n"
            f"🗓 Registration starts: {tournament['register_start']}\n"
            f"🏁 Registration ends: {tournament['register_end']}\n\n"
            f"👥 Registered Players: {nop}/{tournament['maximum_players']}\n\n"
            f"🏆 Prize: \n\n{tournament['prize']}\n\n"
            f"⚠️Once you register for the tournament, you can't quit it ❗️\n"
            f"🔗 Join using the button below:"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔥 Join the Tournament 🔥",
                    callback_data=f"join_tournament:{tournament['name']}"
                )
            ]
        ])

        await callback_query.message.answer(
            response, reply_markup=keyboard, parse_mode="Markdown"
        )



async def show_archive_tournaments(callback_query: types.CallbackQuery):
    tournaments = get_tournament_archive()
    if not tournaments:
        await callback_query.message.answer(
            "No tournaments in the archive.",
            reply_markup=get_main_menu(callback_query.from_user.id),
        )
        return

    response = "📑 *Tournament Archive:*\n\n"
    for tournament in tournaments:
        response += f"🏆 ID: {tournament['id']}\n🌟 Started: {tournament["start_time"]}\n📅 Ended: {tournament["end_time"]}\n🥇 Winner: {tournament['winner']}\n\n"
    await callback_query.message.answer(response, parse_mode="Markdown")

@dp.callback_query(lambda c: c.data.startswith("join_tournament:"))
async def join_tournament(callback_query: types.CallbackQuery):
    tournament_id = callback_query.data.split(":")[1]
    user_id = callback_query.from_user.id
    current_time = datetime.now(timezone.utc) + timedelta(hours=5)
    tournament = get_upcoming_tournaments()
    register_start = datetime.strptime(tournament["register_start"], "%Y-%m-%d %H:%M:%S")
    register_end = datetime.strptime(tournament["register_end"], "%Y-%m-%d %H:%M:%S")
    if not (register_start <= current_time <= register_end):
        await callback_query.answer(
            f"❌ Registration is only open between {register_start.strftime('%Y-%m-%d %H:%M:%S')} and {register_end.strftime('%Y-%m-%d %H:%M:%S')}.",
            show_alert=True,
        )
        return
    if is_user_in_tournament(tournament_id, user_id):
        await callback_query.answer("❕ You are already registered for this tournament.", show_alert=True)
        return

    try:
        add_user_to_tournament(tournament_id, user_id)
        await callback_query.answer("✅ You have successfully joined the tournament!", show_alert=True)
    except Exception as e:
        print(f"❌ Error adding user to tournament: {e}")
        await callback_query.answer("❌ Failed to join the tournament. Please try again later.", show_alert=True)


