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

start_stop_game_uz = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="O'yinni boshlash ✅", callback_data="start_game"
            ),
        ],
        [
            InlineKeyboardButton(
                text="O'yinni o'chirib tashlash 🚫", callback_data="stop_game"
            ),
        ],
    ]
)

start_stop_game_ru = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Начать игру ✅", callback_data="start_game"),
        ],
        [
            InlineKeyboardButton(text="Удалить игру 🚫", callback_data="stop_game"),
        ],
    ]
)


# cancel_g = InlineKeyboardMarkup(
#     inline_keyboard=[
#         [
#             InlineKeyboardButton(text="quit game 🚀", callback_data="cancel_game"),
#         ]
#     ]
# )


@dp.callback_query(lambda c: c.data == "start_game")
async def inline_star_game_inline(callback_query: types.CallbackQuery):
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
    ln = get_user_language(callback_query.from_user.id)
    if gn == gp:
        players = get_all_players_in_game(game_id)
        if ln == "uz":
            ms1 = "O'yin boshlanmoqda: "
        elif ln == "ru":
            ms1 = "Игра начинается: "
        else:
            ms1 = "Game starts in: "
        ms2 = "3️⃣"
        tasks = []
        cr_id = get_game_creator_id(game_id)
        players.remove(cr_id)
        for player in players:
            if player is None:
                continue
            reset_exclusion_count(game_id, player)
            create_game_record_if_not_exists(game_id, player)
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
        if ln == "uz":
            ms1 = f"O'yinni boshlash uchun yana {dif} ta o'yinchilar kerak !!!"
        elif ln == "ru":
            ms1 = f"Нам нужно {dif} больше игроков, чтобы начать игру!!!"
        else:
            ms1 = f"{dif} players are needed to start the game!!!"
        await bot.send_message(callback_query.from_user.id, ms1)
        return


async def send_game_start_messages(player_id, ms1, ms2, lent):
    sec = await bot.send_message(player_id, ms1)
    msg = await bot.send_message(player_id, ms2)
    await periodically_edit_message(
        player_id, msg.message_id, sec.message_id, lent + 1, cur_table, interval=1
    )


# def generate_exclude_keyboard(game_id):
#     with sqlite3.connect("users_database.db") as conn:
#         cursor = conn.cursor()
#         cursor.execute(
#             """
#             SELECT invitee_id, (SELECT nfgame FROM users_database WHERE user_id = invitee_id) AS player_name
#             FROM invitations
#             WHERE game_id = ? AND invitee_id IS NOT NULL
#             """,
#             (game_id,),
#         )
#         players = cursor.fetchall()

#     if not players:
#         return InlineKeyboardMarkup(
#             inline_keyboard=[
#                 [
#                     InlineKeyboardButton(
#                         text="Delete the game 🚫", callback_data="stop_game"
#                     )
#                 ]
#             ],
#         )

#     keyboard = InlineKeyboardMarkup(
#         inline_keyboard=[
#             [
#                 InlineKeyboardButton(
#                     text=f"Exclude {player_name} 🚀",
#                     callback_data=f"exclude_player:{invitee_id}",
#                 )
#             ]
#             for invitee_id, player_name in players
#         ]
#         + [
#             [InlineKeyboardButton(text="Delete the game 🚫", callback_data="stop_game")]
#         ],
#     )

#     return keyboard


@dp.callback_query(lambda c: c.data == "stop_game")
async def can_game(callback_query: types.CallbackQuery):
    user = callback_query.from_user
    with sqlite3.connect("users_database.db") as conn:
        ln = get_user_language(user.id)
        if ln == "uz":
            ms1 = "Hozirda siz hech qanday o'yinnig yaratuvchisi emassiz"
            ms2 = "O'yin yaratuvchisi tomonidan to'xtatildi."
            ms3 = "Siz o'yinni yakunladingiz. Barcha o'yinchilarga xabar berildi. ✔️"
        elif ln == "ru":
            ms1 = "В настоящее время вы не являетесь создателем ни одной игры."
            ms2 = "Игра остановлена ​​или завершена создателем"
            ms3 = "Вы отменили игру. Все игроки уведомлены. ✔️"
        else:
            ms1 = "You are not currently the creator of any game."
            ms2 = "The game has been stopped or finished by the creator."
            ms3 = "You have canceled the game. All players have been notified. ✔️"
        cursor = conn.cursor()
        game_id = get_game_id_by_user(user.id)
        increase_exclusion_count(game_id, user.id)
        if not game_id:
            await callback_query.answer(ms1)
            return
        cursor.execute(
            "SELECT invitee_id FROM invitations WHERE game_id = ?", (game_id,)
        )
        players = cursor.fetchall()
        for player in players:
            player_id = player[0]
            if player_id is not None:
                update_game_details(game_id, player, None)
                delete_user_from_all_games(player_id)
                try:
                    await bot.send_message(
                        player_id, ms2, reply_markup=get_main_menu(player_id)
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
        update_game_details(game_id, callback_query.from_user.id, None)
        await callback_query.message.answer(
            ms3, reply_markup=get_main_menu(callback_query.from_user.id)
        )
        await delete_all_game_messages(game_id)


# async def player_quit_game(user_id, game_id, inviter_id):
#     with sqlite3.connect("users_database.db") as conn:
#         cursor = conn.cursor()
#         update_game_details(game_id, user_id, None)
#         cursor.execute(
#             "DELETE FROM invitations WHERE invitee_id = ? AND game_id = ?",
#             (user_id, game_id),
#         )
#         conn.commit()
#         cursor.execute(
#             "SELECT nfgame FROM users_database WHERE user_id = ?", (user_id,)
#         )

#         player_name = cursor.fetchone()
#         if player_name:
#             player_name = get_user_nfgame(user_id)
#             try:
#                 await bot.send_message(
#                     inviter_id,
#                     f"Player {player_name} has quit the game.\nPlayers left in the game: {get_player_count(game_id)}",
#                 )
#             except Exception as e:
#                 print(f"Error sending message to creator {inviter_id}: {e}")


stop_incomplete_games = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Stop/leave current game 🛑", callback_data="stop_incomplete_games"
            )
        ]
    ]
)
stop_incomplete_games_uz = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Davom etayotgan o'yinni tark etish/to'xtatish 🛑",
                callback_data="stop_incomplete_games",
            )
        ]
    ]
)
stop_incomplete_games_ru = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Остановить/покинуть текущую игру 🛑",
                callback_data="stop_incomplete_games",
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
    ln = get_user_language(user_id)
    if ln == "uz":
        ms1 = "Sizda tugatilmagan o'yinlar mavjud emas"
        ms4 = "Sizning barcha o'yinlaringiz to'xtatildi."
    elif ln == "ru":
        ms1 = "У вас нет незавершённых игр."
        ms4 = "Все ваши игры приостановлены."
    else:
        ms1 = "You have no incomplete games to stop."
        ms4 = "Your incomplete games have been stopped."
    if not games:
        await callback_query.message.answer(ms1, reply_markup=get_main_menu(user_id))
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
                ln = get_user_language(player_id)
                if ln == "uz":
                    ms2 = "O'yin yaratuvchisi tomonidan to'xtatildi."
                elif ln == "ru":
                    ms2 = "Игра остановлена ​​создателем."
                else:
                    ms2 = "The game has been stopped by the creator."
                try:
                    await bot.send_message(
                        player_id,
                        ms2,
                        reply_markup=get_main_menu(player_id),
                    )
                except Exception as e:
                    print(f"Failed to send message to player {player_id}: {e}")
        else:
            update_game_details(game["game_id"], user_id, None)
            delete_user_from_all_games(user_id)
            try:
                ln = get_user_language(creator_id)
                if ln == "uz":
                    ms3 = f"{get_user_nfgame(callback_query.from_user.id)} o'yinni tark etdi.\nQolgan o'yinchilar soni: {get_player_count(get_game_id_by_user(creator_id))}"
                elif ln == "ru":
                    ms3 = f"Игрок {get_user_nfgame(callback_query.from_user.id)} покинул игру.\nИгроков осталось в игре: {get_player_count(get_game_id_by_user(creator_id))}"
                else:
                    ms3 = f"A player {get_user_nfgame(callback_query.from_user.id)} has left the game.\nPlayers left in game: {get_player_count(get_game_id_by_user(creator_id))}"
                await bot.send_message(
                    creator_id, ms3, reply_markup=get_main_menu(creator_id)
                )
            except Exception as e:
                print(f"Failed to send message to creator {creator_id}: {e}")
    await callback_query.message.answer(
        ms4,
        reply_markup=get_main_menu(callback_query.from_user.id),
    )
    await delete_user_messages(game["game_id"], callback_query.from_user.id)
    await callback_query.answer()


# @dp.callback_query(lambda c: c.data.startswith("exclude_player:"))
# async def exclude_player_querriy(callback_query: types.CallbackQuery):
#     # await bot.delete_message(
#     #     callback_query.from_user.id, callback_query.message.message_id
#     # )
#     user = callback_query.from_user
#     data = callback_query.data.split(":")
#     if len(data) != 2:
#         await callback_query.answer("Invalid data.")
#         return
#     player_to_remove = int(data[1])

#     game_id = get_game_id_by_user(user.id)
#     increase_exclusion_count(game_id, user.id)

#     with sqlite3.connect("users_database.db") as conn:
#         cursor = conn.cursor()
#         cursor.execute(
#             "SELECT inviter_id FROM invitations WHERE game_id = ? AND invitee_id IS NULL",
#             (game_id,),
#         )
#         inviter_id = cursor.fetchone()
#         if not inviter_id or inviter_id[0] != user.id:
#             await callback_query.answer("Only the game creator can exclude players.")
#             return
#         if is_game_started(game_id) and is_user_turn(player_to_remove, game_id):
#             await bot.send_message(
#                 chat_id=user.id,
#                 text=f"Now it's {get_user_nfgame(player_to_remove)}'s turn❗️\nYou can not exclude this player when it is his turn.",
#             )
#             return
#         cursor.execute(
#             "DELETE FROM invitations WHERE invitee_id = ? AND game_id = ?",
#             (player_to_remove, game_id),
#         )
#         conn.commit()
#         update_game_details(game_id, player_to_remove, None)
#         winner = get_alive_number(game_id)
#         if winner != 0 and is_game_started(game_id):
#             await bot.send_message(
#                 chat_id=winner,
#                 text=f"Game has finished. \nYou are winner. 🥳🥳🥳🥳🥳\nConguratulation on winning in the game. \n🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉",
#                 reply_markup=get_main_menu(winner),
#             )
#             update_game_details(
#                 game_id, winner, get_user_nfgame(winner) + " - " + str(winner)
#             )
#             conn = sqlite3.connect("users_database.db")
#             cursor = conn.cursor()
#             cursor.execute(
#                 """
#                 SELECT user_id
#                 FROM user_game_messages
#                 WHERE game_id = ?
#                 """,
#                 (game_id,),
#             )
#             user_ids = cursor.fetchall()
#             user_ids = list(set([user for user in user_ids]))
#             for users in user_ids:
#                 users = users[0]
#                 if users and is_player_dead(game_id, users):
#                     update_game_details(
#                         game_id, users, get_user_nfgame(winner) + " - " + str(winner)
#                     )
#                     await bot.send_message(
#                         chat_id=users,
#                         text=f"The game in which you died has ended ⭐️\nWinner: {get_user_nfgame(winner)} — {winner} 🏆",
#                     )
#             delete_game(game_id)
#             await delete_all_game_messages(game_id)
#     try:
#         await bot.send_message(
#             player_to_remove,
#             "Game has finished or been stopped by the creator.",
#             reply_markup=get_main_menu(player_to_remove),
#         )
#         await delete_user_messages(game_id, player_to_remove)
#     except Exception as e:
#         print(f"Failed to send message to player {player_to_remove}: {e}")

#     await callback_query.message.edit_text(
#         f"Player excluded successfully. Remaining players: {get_player_count(game_id)}",
#         reply_markup=generate_exclude_keyboard(game_id),
#     )


def get_join_tournament_button(tournament_id: str):
    inline_keyboard = InlineKeyboardMarkup()
    inline_keyboard.add(
        InlineKeyboardButton(
            text="🎮 Join the Tournament",
            callback_data=f"join_tournament:{tournament_id}",
        )
    )
    return inline_keyboard


# user_tournaments_keyboard = InlineKeyboardMarkup(
#     inline_keyboard=[
#         [
#             InlineKeyboardButton(
#                 text="⚡️ Ongoing Tournaments", callback_data="view_ongoing"
#             )
#         ],
#         [
#             InlineKeyboardButton(
#                 text="🌟 Upcoming Tournaments", callback_data="view_upcoming"
#             )
#         ],
#         [
#             InlineKeyboardButton(
#                 text="📑 Tournament Archive", callback_data="view_archive"
#             )
#         ],
#     ]
# )

archive_tournamnets = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📑 Tournaments Archive", callback_data="view_archive"
            )
        ],
    ]
)
archive_tournamnets_ru = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📑 Архив турниров", callback_data="view_archive")],
    ]
)
archive_tournamnets_uz = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📑 Turnirlar arxivi", callback_data="view_archive"
            )
        ],
    ]
)


@dp.callback_query(lambda c: c.data.startswith("view_"))
async def handle_tournament_action(callback_query: types.CallbackQuery):
    action = callback_query.data.split("_")[1]
    if action == "archive":
        await show_archive_tournaments(callback_query)


# async def show_ongoing_tournaments(callback_query: types.CallbackQuery):
#     tournaments = get_ongoing_tournaments()
#     if not tournaments:
#         await callback_query.answer(
#             "No ongoing tournaments right now 🤷‍♂️",
#             show_alert=True,
#             reply_markup=get_main_menu(callback_query.from_user.id),
#         )
#         return
#     response = "⚡️ *Ongoing Tournaments:*\n\n"
#     for tournament in tournaments:
#         response += f"🏆 {tournament['id']} (Ends: {tournament['end_time']})\n"
#     await callback_query.message.answer(response, parse_mode="Markdown")


async def show_archive_tournaments(callback_query: types.CallbackQuery):
    tournaments = get_tournament_archive()
    ln = get_user_language(callback_query.from_user.id)
    if ln == "uz":
        ms = "Arxivda hech qanday turnirlar yoq 🤷‍♂️"
        response = "📑 *Turinrlar arxivi:*\n\n"
    elif ln == "ru":
        ms = "Турниров в архиве нет 🤷‍♂️"
        response = "📑 *Архив турнира:*\n\n"
    else:
        ms = "No tournaments in the archive 🤷‍♂️"
        response = "📑 *Tournament Archive:*\n\n"
    if not tournaments:
        await callback_query.answer(
            ms, show_alert=True, reply_markup=get_main_menu(callback_query.from_user.id)
        )
        return

    for tournament in tournaments:
        if ln == "uz":
            response += f"🏆 ID: {tournament['id']}\n🌟 Boshlangan: {tournament["start_time"]}\n📅 Tugagan: {tournament["end_time"]}\n🥇 G'olib: {get_user_nfgame(tournament['winner'])} (ID: {tournament['winner']})\n\n"
        elif ln == "ru":
            response += f"🏆 ID: {tournament['id']}\n🌟 Hачал: {tournament["start_time"]}\n📅 Закончено: {tournament["end_time"]}\n🥇 Победитель: {get_user_nfgame(tournament['winner'])} (ID: {tournament['winner']})\n\n"
        else:
            response += f"🏆 ID: {tournament['id']}\n🌟 Started: {tournament["start_time"]}\n📅 Ended: {tournament["end_time"]}\n🥇 Winner: {get_user_nfgame(tournament['winner'])} (ID: {tournament['winner']})\n\n"
    await callback_query.message.answer(response, parse_mode="Markdown")


@dp.callback_query(lambda c: c.data.startswith("join_tournament:"))
async def join_tournament(callback_query: types.CallbackQuery):
    tournament_id = callback_query.data.split(":")[1]
    user_id = callback_query.from_user.id
    tournament = get_ongoing_tournaments()
    ln = get_user_language(user_id)
    if ln == "uz":
        ms = "Turnir topilmadi yoki allaqachon tugagan/boshlangan 😕"
        ms2 = "❕ Siz allaqachon ushbu turnirga ro'yhatdan o'tgansiz"
        ms3 = "✅ Siz muvaffaqiyatli ro'yhatdan o'tdingiz"
        response = (
            "✅ *Siz turnirga qo'shildingiz* 🎉\n\n"
            "🏆 Musobaqalashish uchun tayyor turing!\n"
            "⏳ Turnir bir necha daqiqada boshlanadi. Online bo'ling va tayyor turing!"
        )
    elif ln == "ru":
        ms = "Турнир не найден или уже начался/завершён 😕"
        ms2 = "❕ Вы уже зарегистрированы на этот турнир."
        ms3 = "✅ Вы успешно присоединились к турниру!"
        response = (
            "✅ *Вы успешно присоединились к турниру!* 🎉\n\n"
            "🏆 Будьте готовы к соревнованиям!\n"
            "⏳ Турнир начнется через несколько минут. Будьте онлайн и готовы к турниру!"
        )
    else:
        ms = "Tournament not found or already started/finished 😕"
        ms2 = "❕ You are already registered for this tournament."
        ms3 = "✅ You have successfully joined the tournament!"
        response = (
            "✅ *You have successfully joined the tournament!* 🎉\n\n"
            "🏆 Get ready to compete!\n"
            "⏳ The tournament will start in a few minutes. Be online and ready for the tournament!"
        )
    if not tournament:
        await callback_query.answer(ms, show_alert=True)
        return
    tournament = tournament[0]
    if is_user_in_tournament(tournament_id, user_id):
        await callback_query.answer(ms2, show_alert=True)
        return
    try:
        add_user_to_tournament(tournament_id, user_id)
        await callback_query.answer(ms3)
        message_id = callback_query.message.message_id
        chat_id = callback_query.message.chat.id

        await bot.edit_message_text(
            chat_id=chat_id, message_id=message_id, text=response, parse_mode="Markdown"
        )
    except Exception as e:
        print(f"❌ Error adding user to tournament: {e}")
        await callback_query.answer(
            "❌ Failed to join the tournament. Please try again later.", show_alert=True
        )


@dp.callback_query(lambda c: c.data.startswith("remove_"))
async def confirm_remove_player(callback: types.CallbackQuery):
    player_id = callback.data.split("_")[1]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Yes", callback_data=f"confirm_remove_{player_id}"
                ),
                InlineKeyboardButton(text="❌ No", callback_data="cancel_remove"),
            ],
        ]
    )

    await callback.message.edit_text(
        f"Do you want to remove {get_user_nfgame(int(player_id))} from the tournament?",
        reply_markup=keyboard,
    )


@dp.callback_query(F.data == "cancel_remove")
async def cancel_remove(callback: types.CallbackQuery):
    await callback.message.edit_text("Player removal canceled ❌")
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("bonus_cb_"))
async def claim_bonus(callback: types.CallbackQuery):
    user_id = callback.data.split("bonus_cb_")[1]
    ln = get_user_language(user_id)
    if ln == "uz":
        ms1 = "❌ Siz bugungi bonusni olib bo'lgansiz. Ertaga urinib ko'ring"
    elif ln == "ru":
        ms1 = "❌ Вы уже забрали свой бонус сегодня. Возвращайтесь завтра!"
    else:
        ms1 = "❌ You've already claimed your bonus today. Come back tomorrow!"
    if not can_claim_bonus(user_id):
        await callback.answer(ms1, show_alert=True)
        return
    coins = random.randint(1, 20)
    update_claim_time(user_id)
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users_database SET unity_coin = unity_coin + ? WHERE user_id = ?",
        (coins, callback.from_user.id),
    )
    conn.commit()
    conn.close()
    ln = get_user_language(user_id)
    if ln == "uz":
        ms1 = f"🎉 Siz {coins} Unity Coinga ega bo'ldingiz. Ko'proq bonus uchun ertaga qaytib keling."
    elif ln == "ru":
        ms1 = f"🎉 Вы получили {coins} Unity Coin! Возвращайтесь завтра за еще!"
    else:
        ms1 = f"🎉 You received {coins} coins! Come back tomorrow for more!"
    await callback.answer(ms1, show_alert=True)


select_language_button = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="English 🇺🇸", callback_data="lan_en"),
        ],
        [
            InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lan_ru"),
        ],
        [
            InlineKeyboardButton(text="O'zbek 🇺🇿", callback_data="lan_uz"),
        ],
    ]
)

select_language_button_2 = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="English 🇺🇸", callback_data="changelan_en"),
        ],
        [
            InlineKeyboardButton(text="Русский 🇷🇺", callback_data="changelan_ru"),
        ],
        [
            InlineKeyboardButton(text="O'zbek 🇺🇿", callback_data="changelan_uz"),
        ],
    ]
)


def get_username_button(lang: str):
    if lang == "ru":
        text = "руководство📜"
    elif lang == "uz":
        text = "qo'llanma 📜"
    else:
        text = "instruction 📜"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=text, callback_data="username_rules"),
            ],
        ]
    )


@dp.callback_query(F.data == "username_rules")
async def cancel_remove(callback: types.CallbackQuery):
    ln = get_user_language(callback.from_user.id)

    if ln == "ru":
        ms = (
            "Ваше имя пользователя должно быть УНИКАЛЬНЫМ и может содержать только:\n"
            "- Латинские буквы (a-z, A-Z)\n"
            "- Цифры (0-9)\n"
            "- Подчеркивания (_)\n"
            "Максимальная длина - 30 символов."
        )
    elif ln == "uz":
        ms = (
            "Foydalanuvchi nomi botda YAGONA bo‘lishi kerak va faqat quyidagilarni o‘z ichiga olishi mumkin:\n"
            "- Lotin harflari (a-z, A-Z)\n"
            "- Raqamlar (0-9)\n"
            "- Pastki chiziq (_) \n"
            "Maksimal uzunlik - 30 ta belgi."
        )
    else:
        ms = (
            "Your username must be UNIQUE and can only contain:\n"
            "- Latin alphabet characters (a-z, A-Z)\n"
            "- Numbers (0-9)\n"
            "- Underscores (_)\n"
            "Maximum length - 30 characters."
        )

    await callback.answer(ms, show_alert=True)


@dp.callback_query(F.data.startswith("changelan_"))
async def change_language(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    language_code = callback.data.split("_")[1]

    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO user_languages (user_id, language) 
        VALUES (?, ?) 
        ON CONFLICT(user_id) DO UPDATE SET language = excluded.language
        """,
        (user_id, language_code),
    )
    conn.commit()
    conn.close()

    # Confirmation messages in selected languages
    messages = {
        "en": "✅ Language set to English!",
        "ru": "✅ Язык установлен на русский!",
        "uz": "✅ Til o'zbek tiliga o'zgartirildi!",
    }

    await callback.message.delete()
    await callback.message.answer(
        messages[language_code], reply_markup=get_main_menu(user_id)
    )


def generate_courses_keyboard():
    courses = getall_channels()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for curs in courses:
        curs = list(curs)
        channel_id, channel_link = curs[0], curs[1]
        if channel_id[0] == "-":
            channel_id = channel_id[4:]
        row = [
            InlineKeyboardButton(
                text=f"{channel_id}", callback_data=f"view_course:{channel_id}"
            ),
            InlineKeyboardButton(
                text="🚫", callback_data=f"delete_course:{channel_id}"
            ),
        ]
        keyboard.inline_keyboard.append(row)
    return keyboard


@dp.callback_query(F.data.startswith("delete_course:"))
async def delete_course_callback(call: types.CallbackQuery):
    channel_identifier = call.data.split(":")[1]
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM channel_earn WHERE channel_id = ?", (channel_identifier,)
    )
    conn.commit()
    conn.close()
    await call.answer("Channel has been successfully deleted ✅", show_alert=True)

    keyboard = generate_courses_keyboard()
    await call.message.edit_reply_markup(reply_markup=keyboard)


@dp.callback_query(F.data.startswith("view_course:"))
async def view_course_callbackfef(call: types.CallbackQuery):
    chid = call.data.split(":")[1]
    await bot.send_message(1155076760, chid)
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT channel_link FROM channel_earn WHERE channel_id = ?",
        (chid,),
    )
    chn = cursor.fetchall()
    conn.close()
    await call.message.answer(chn[0])
    await call.answer()


# @dp.callback_query(lambda c: c.data == "cancel_game")
# async def handle_quit_game(callback_query: types.CallbackQuery):
#     await bot.delete_message(
#         callback_query.from_user.id, callback_query.message.message_id
#     )
#     user = callback_query.from_user
#     with sqlite3.connect("users_database.db") as conn:
#         cursor = conn.cursor()
#         game_id = get_game_id_by_user(user.id)
#         increase_exclusion_count(game_id, user.id)
#         if not game_id:
#             await callback_query.answer("You are not currently in any game.")
#             return
#         if has_incomplete_games(user.id):
#             if (
#                 is_user_in_game(game_id, user.id)
#                 and get_current_turn_user_id(game_id) == user.id
#             ):
#                 await callback_query.message.answer(
#                     f"Now it is your turn! You can't leave the game at that time🙅‍♂️"
#                 )
#                 return
#             update_game_details(game_id, user.id, None)
#             cursor.execute(
#                 "DELETE FROM invitations WHERE invitee_id = ? AND game_id = ?",
#                 (user.id, game_id),
#             )
#             conn.commit()
#             inviter_id = get_game_inviter_id(game_id)
#             await player_quit_game(user.id, game_id, inviter_id)
#             await callback_query.message.answer(
#                 f"You have quit the current game.",
#                 reply_markup=get_main_menu(callback_query.from_user.id),
#             )
#             await delete_user_messages(game_id, user.id)
#             delete_user_from_all_games(user.id)
#             winner = get_alive_number(game_id)
#             if winner != 0 and is_game_started(game_id):
#                 await bot.send_message(
#                     chat_id=winner,
#                     text=f"Game has finished. \nYou are winner. 🥳🥳🥳🥳🥳\nConguratulation on winning in the game. \n🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉",
#                     reply_markup=get_main_menu(winner),
#                 )
#                 update_game_details(
#                     game_id, winner, get_user_nfgame(winner) + " - " + str(winner)
#                 )
#                 conn = sqlite3.connect("users_database.db")
#                 cursor = conn.cursor()
#                 cursor.execute(
#                     """
#                     SELECT user_id
#                     FROM user_game_messages
#                     WHERE game_id = ?
#                     """,
#                     (game_id,),
#                 )
#                 user_ids = cursor.fetchall()
#                 user_ids = list(set([user for user in user_ids]))
#                 for users in user_ids:
#                     users = users[0]
#                     if users and is_player_dead(game_id, users):
#                         update_game_details(
#                             game_id,
#                             users,
#                             get_user_nfgame(winner) + " - " + str(winner),
#                         )
#                         await bot.send_message(
#                             chat_id=users,
#                             text=f"The game in which you died has ended ⭐️\nWinner: {get_user_nfgame(winner)} — {winner} 🏆",
#                         )
#                 delete_game(game_id)
#                 await delete_all_game_messages(game_id)
#         else:
#             await callback_query.message.answer("You have already quit the game.")
