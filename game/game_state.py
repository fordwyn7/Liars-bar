import sqlite3
import asyncio
import random
from config import bot, dp
from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from keyboards.keyboard import *
from db import *
from collections import Counter


def get_current_turn_user_id(game_id):
    with sqlite3.connect("users_database.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT current_turn_user_id FROM invitations WHERE game_id = ?", (game_id,)
        )
        result = cursor.fetchone()
        return result[0] if result else None


def get_player_cards(game_id, player_id):
    with sqlite3.connect("users_database.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT cards
            FROM game_state
            WHERE game_id = ? AND player_id = ?
            """,
            (game_id, player_id),
        )
        result = cursor.fetchone()
        if result and result[0]:
            return result
        return []


async def send_random_cards_to_players(game_id):
    players = get_all_players_in_game(game_id)
    current_turn_user_id = None
    if is_game_started(game_id):
        current_turn_user_id = get_current_turn_user_id(game_id)
    else:
        await send_message_to_all_players(
            game_id, f"Something went wrong. Restart the game."
        )
        return
    for player_id in players:
        if not player_id or is_player_dead(game_id, player_id):
            continue
        pc = get_player_cards(game_id, player_id)
        player_cards = pc[0].split(",")
        is_turn = current_turn_user_id == player_id
        if is_turn:
            addition_keyboard = InlineKeyboardButton(
                text="Send Cards 🟣",
                callback_data="send_cards" if is_turn else "disabled",
            )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=card,
                        callback_data=(
                            f"select_card:{index}:{card}:unselected"
                            if is_turn
                            else "disabled"
                        ),
                    )
                    for index, card in enumerate(player_cards)
                ]
            ]
            + ([[addition_keyboard]] if is_turn else [])
        )
        if is_player_dead(game_id, player_id):
            message = await bot.send_message(
                chat_id=player_id,
                text="You are dead. You can quit now",
            )
            message_id = message.message_id
            await save_message(player_id, game_id, message_id)
            continue
        else:
            await asyncio.sleep(2)
            message = await bot.send_message(
                chat_id=player_id,
                text=(
                    f"Now it's your turn 🫵 \nCurrent table: {get_current_table(game_id)} \nHere are your cards: "
                    if is_turn
                    else f"Here are your cards. \nWait for your turn! Now {get_user_nfgame(get_current_turn_user_id(game_id))}'s turn."
                ),
                reply_markup=keyboard,
            )
            message_id = message.message_id
            await save_message(player_id, game_id, message_id)


selected_cards_count = {}


@dp.callback_query(lambda c: c.data.startswith("select_card"))
async def toggle_card_selection(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    game_id = get_game_id_by_user(user_id)
    if not is_user_turn(user_id, game_id):
        await callback_query.answer("It's not your turn!", show_alert=True)
        return
    data = callback_query.data.split(":")
    index = int(data[1])
    card = data[2]
    current_state = data[3]
    if user_id not in selected_cards_count:
        selected_cards_count[user_id] = 0
    if current_state == "unselected" and selected_cards_count[user_id] > 2:
        await callback_query.answer(
            "You can only select up to 3 cards.", show_alert=True
        )
        return

    new_state = "selected" if current_state == "unselected" else "unselected"
    new_text = f"{card} ✅" if new_state == "selected" else card
    if new_state == "selected":
        selected_cards_count[user_id] += 1
    elif current_state == "selected":
        selected_cards_count[user_id] -= 1

    message = callback_query.message
    keyboard = message.reply_markup.inline_keyboard
    button = keyboard[0][index]
    button.text = new_text
    button.callback_data = f"select_card:{index}:{card}:{new_state}"

    await bot.edit_message_reply_markup(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
    )
    await callback_query.answer(f"Card {card} is now {new_state}.")


def add_last_cards_column_if_not_exists():
    with sqlite3.connect("users_database.db") as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                ALTER TABLE game_state 
                ADD COLUMN last_cards TEXT
                """
            )
            conn.commit()
        except sqlite3.OperationalError:
            pass


def insert_or_update_last_cards(game_id, selected_cards):
    with sqlite3.connect("users_database.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT last_cards FROM game_state WHERE game_id = ?
            """,
            (game_id,),
        )
        result = cursor.fetchone()

        if result:
            cursor.execute(
                """
                UPDATE game_state
                SET last_cards = ?
                WHERE game_id = ?
                """,
                (",".join(selected_cards), game_id),
            )
        else:
            cursor.execute(
                """
                INSERT INTO game_state (game_id, last_cards)
                VALUES (?, ?)
                """,
                (game_id, ",".join(selected_cards)),
            )

        conn.commit()


def get_last_cards(game_id):
    with sqlite3.connect("users_database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(game_state)")
        columns = [row[1] for row in cursor.fetchall()]
        if "last_cards" not in columns:
            raise ValueError(
                "The 'last_cards' column does not exist in the game_state table."
            )
        cursor.execute(
            """
            SELECT last_cards
            FROM game_state
            WHERE game_id = ?
            """,
            (game_id,),
        )
        result = cursor.fetchone()
        return result if result else None


@dp.callback_query(lambda c: c.data == "send_cards")
async def send_cards(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    game_id = get_game_id_by_user(user_id)
    keyboard = callback_query.message.reply_markup.inline_keyboard

    if not is_user_turn(user_id, game_id):
        await callback_query.answer("It's not your turn!", show_alert=True)
        return

    selected_cards = [
        button.text.replace(" ✅", "")
        for row in keyboard
        for button in row
        if "✅" in button.text
    ]
    selected_cards_count.clear()
    if selected_cards:
        await bot.delete_message(
            callback_query.from_user.id, callback_query.message.message_id
        )
        mss = await bot.send_message(
            chat_id=callback_query.from_user.id,
            text=f"You sent the following cards: {', '.join(selected_cards)} ",
        )
        await save_message(callback_query.from_user.id, game_id, mss.message_id)
        with sqlite3.connect("users_database.db") as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT cards FROM game_state 
                WHERE game_id = ? AND player_id = ?
                """,
                (game_id, user_id),
            )
            result = cursor.fetchone()
            if result:
                current_cards = result[0].split(",")
                current_card_counts = Counter(current_cards)
                selected_card_counts = Counter(selected_cards)
                remaining_card_counts = current_card_counts - selected_card_counts
                remaining_cards = list(remaining_card_counts.elements())
                cursor.execute(
                    """
                    UPDATE game_state
                    SET cards = ?, last_cards = ?
                    WHERE game_id = ? AND player_id = ?
                    """,
                    (
                        ",".join(remaining_cards),
                        ",".join(selected_cards),
                        game_id,
                        user_id,
                    ),
                )
                conn.commit()

        insert_or_update_last_cards(game_id, selected_cards)
        update_current_turn(game_id)

    else:
        message = await bot.send_message(
            chat_id=callback_query.from_user.id,
            text="No cards selected! Please choose cards first.",
        )
        message_id = message.message_id
        await save_message(callback_query.from_user.id, game_id, message_id)
        return

    players = get_all_players_in_game(game_id)
    for p_id in players:
        if not p_id:
            continue
        if p_id != user_id:
            message = await bot.send_message(
                chat_id=p_id,
                text=(
                    f"Player {get_user_nfgame(user_id)} sent {len(selected_cards)} cards. "
                ),
            )
            message_id = message.message_id
            await save_message(p_id, game_id, message_id)
    for p_id in players:
        if not p_id:
            continue
        if p_id != get_next_player_id(game_id, user_id):
            message = await bot.send_message(
                chat_id=p_id,
                text=f"Now {get_user_nfgame(get_next_player_id(game_id, user_id))}'s turn. \nPlease wait until your turn ⏰",
            )
            message_id = message.message_id
            await save_message(p_id, game_id, message_id)
    next_player_id = get_next_player_id(game_id, user_id)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Continue 🚀", callback_data="continue_game"),
                InlineKeyboardButton(text="Liar 🙅‍♂️", callback_data="liar_game"),
            ]
        ]
    )

    message = await bot.send_message(
        chat_id=next_player_id,
        text=f"{get_user_nfgame(user_id)} made his turn 🌟",
        reply_markup=keyboard,
    )
    message_id = message.message_id
    await save_message(next_player_id, game_id, message_id)


@dp.callback_query(lambda c: c.data in ["continue_game", "liar_game"])
async def handle_continue_or_liar(callback_query: types.CallbackQuery):
    await bot.delete_message(
        callback_query.from_user.id, callback_query.message.message_id
    )
    user_id = callback_query.from_user.id
    game_id = get_game_id_by_user(user_id)
    if callback_query.data == "liar_game":
        previous_player_id = get_previous_player_id(game_id, user_id)
        previous_player_cards = get_last_cards(game_id)[0]
        table_current = get_current_table(game_id).split(" ")[-1]
        liar_bool = True
        all_shoot = False
        for i in previous_player_cards.split(","):
            if i == "🃏" and len(previous_player_cards.split(",")) == 1:
                all_shoot = True
                break
            if i != table_current and i != "🎴":
                liar_bool = False
        if all_shoot:
            players = get_all_players_in_game(game_id)
            players.remove(previous_player_id)
            message = await bot.send_message(
                chat_id=previous_player_id,
                text=f"Player {get_user_nfgame(user_id)} opened the last sent cards and it was a Joker(🃏) card, so all players will shoot themselves.",
            )
            message_id = message.message_id
            await save_message(previous_player_id, game_id, message_id)
            await asyncio.sleep(2)
            for player in players:
                message = await bot.send_message(
                    chat_id=player,
                    text=f"Player {get_user_nfgame(user_id)} opened the last sent cards and it was a Joker(🃏) card, so you all must shoot yourself.",
                )
                message_id = message.message_id
                await save_message(player, game_id, message_id)
            await asyncio.sleep(3)
            for player in players:
                bull = await shoot_self(game_id, player)
                if type(bull) == type(True):
                    await send_message_to_all_players(
                        game_id,
                        f"Player {get_user_nfgame(player)} shot himself and is dead by the real bullet 😵\nHe is now eliminated from the game.",
                    )
                    if is_user_turn(player, game_id):
                        update_current_turn(game_id)
                    messa = await bot.send_message(
                        chat_id=player,
                        text="You shot yourself and dead by real bullet 😵\nNow you are eliminated from game. We will inform the winner when the game ends",
                    )
                    delete_user_from_all_games(player)
                    await save_message(player, game_id, messa.message_id)
                else:
                    await send_message_to_all_players(
                        game_id,
                        f"Player {get_user_nfgame(player)} shot himself and has NOT died because of the blank bullet ⭕️. He can continue the game ✅\nHis next chance to die - 1/{6-bull}",
                    )
            winner = get_alive_number(game_id)
            if winner != 0:
                await bot.send_message(
                    chat_id=winner,
                    text=f"Game has finished. \nYou are winner. 🥳🥳🥳🥳🥳\nConguratulation on winning in the game. \n🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉",
                    reply_markup=get_main_menu(winner),
                )
                update_game_details(
                    game_id, winner, get_user_nfgame(winner) + " - " + str(winner)
                )
                conn = sqlite3.connect("users_database.db")
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT user_id
                    FROM user_game_messages
                    WHERE game_id = ?
                    """,
                    (game_id,),
                )
                user_ids = cursor.fetchall()
                user_ids = list(set([user for user in user_ids]))
                for users in user_ids:
                    users = users[0]
                    if users and is_player_dead(game_id, users):
                        update_game_details(
                            game_id,
                            users,
                            get_user_nfgame(winner) + " - " + str(winner),
                        )
                        await bot.send_message(
                            chat_id=users,
                            text=f"The game in which you died has ended ⭐️\nWinner: {get_user_nfgame(winner)} — {winner} 🏆",
                        )
                tournament_id = get_tournament_id_by_user(winner)
                await bot.send_message(chat_id=1155076760, text=f"{tournament_id}, {is_user_in_tournament(tournament_id, winner)} check 2")
                
                if tournament_id and is_user_in_tournament(tournament_id, winner):
                    save_round_winner(tournament_id, str(winner), str(winner))
                    cur_round = int(get_current_round_number(tournament_id))
                    plrs = get_users_in_round(tournament_id, cur_round)
                    nopir = int(get_number_of_groups_in_round(tournament_id, cur_round))
                    await bot.send_message(chat_id=1155076760, text=f"{plrs}, {cur_round}, {get_number_of_winners(tournament_id, cur_round)} check 4")
                    if int(get_number_of_winners(tournament_id, cur_round)) == nopir:
                        notify_round_results(tournament_id, cur_round)
                    if not update_tournament_winner_if_round_finished(tournament_id, cur_round) == 12:
                        start_next_round(plrs, tournament_id, cur_round)
                delete_game(game_id)
                await delete_all_game_messages(game_id)
                return
            ms = f"Game has restarted! ♻️ \nYou all receive full cards again ✅ \nNow {get_user_nfgame(get_current_turn_user_id(game_id))}'s turn."
            
            players = get_all_players_in_game(game_id)
            for play in players:
                if not is_player_dead(game_id, play):
                    msss = await bot.send_message(chat_id=play, text=ms)
                    await save_message(play, game_id, msss.message_id)
            await asyncio.sleep(2)
            await reset_game_for_all_players(game_id)
            
            return
        if not liar_bool:
            await send_message_to_all_players(
                game_id,
                f"{get_user_nfgame(user_id)} has assumed that player {get_user_nfgame(previous_player_id)} lied 🤥 \nHe was actually right 😎 \nHere are the liar's cards - {previous_player_cards}",
            )
            bullet = await shoot_self(game_id, previous_player_id)
            await asyncio.sleep(3)
            msge = (
                f"Now liar shot himself and there was a real bullet in his gun 🔰 \nEventually, he is dead and eliminated from the game 😵"
                if isinstance(bullet, bool) and bullet
                else f"Now liar shot himself and there was NO real bullet in his pistol ⭕️\nHe will stay in the game ✅ \nHis next chance to die is 1/{6 - bullet}."
            )
            await send_message_to_all_players(game_id, msge)
            if isinstance(bullet, bool) and bullet:
                mjj = await bot.send_message(
                    chat_id=previous_player_id,
                    text="Now you shot yourself and dead by real bullet😵\nYou are eliminated from the game 😕",
                )
                if is_user_turn(previous_player_id, game_id):
                    update_current_turn(game_id)
                await save_message(previous_player_id, game_id, mjj.message_id)
                delete_user_from_all_games(previous_player_id)
        else:
            await send_message_to_all_players(
                game_id,
                f"{get_user_nfgame(user_id)} has assumed that player {get_user_nfgame(previous_player_id)} lied 🤥. But he was NOT right 🫣. \nHere is his cards - {previous_player_cards}",
            )
            bullet = await shoot_self(game_id, user_id)
            await asyncio.sleep(3)
            msge = (
                f"Now player {get_user_nfgame(user_id)} shot himself because of blaming others 🔫\nIt was a real bullet in his pistol 🥶 \nEventually, he is dead and eliminated from the game 😵"
                if isinstance(bullet, bool) and bullet
                else f"Now player {get_user_nfgame(user_id)} shot himself because of blaming others 🔫\nIt was NOT a real bullet and will stay in the game ✅\nHis next chance to die is 1/{6 - bullet}."
            )
            await send_message_to_all_players(game_id, msge)
            if isinstance(bullet, bool) and bullet:
                mjj = await bot.send_message(
                    chat_id=user_id,
                    text="You shot yourselef because of blaming others 🤥\nNow you are dead by real bullet, and eliminated from the game 😵",
                )
                if is_user_turn(user_id, game_id):
                    update_current_turn(game_id)
                delete_user_from_all_games(user_id)
                await save_message(user_id, game_id, mjj.message_id)
        while is_player_dead(game_id, get_current_turn_user_id(game_id)):
            set_current_turn(
                game_id, get_next_player_id(game_id, get_current_turn_user_id(game_id))
            )
        winner = get_alive_number(game_id)
        if winner != 0:
            await bot.send_message(
                chat_id=winner,
                text=f"Game has finished. \nYou are winner. 🥳🥳🥳🥳🥳\nConguratulation on winning in the game. \n🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉",
                reply_markup=get_main_menu(winner),
            )
            update_game_details(
                game_id, winner, get_user_nfgame(winner) + " - " + str(winner)
            )
            conn = sqlite3.connect("users_database.db")
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT user_id
                FROM user_game_messages
                WHERE game_id = ?
                """,
                (game_id,),
            )
            user_ids = cursor.fetchall()
            user_ids = list(set([user for user in user_ids]))
            for users in user_ids:
                users = users[0]
                if users and is_player_dead(game_id, users):
                    update_game_details(
                        game_id, users, get_user_nfgame(winner) + " - " + str(winner)
                    )
                    await bot.send_message(
                        chat_id=users,
                        text=f"The game in which you died has ended ⭐️\nWinner: {get_user_nfgame(winner)} — {winner} 🏆",
                    )
            tournament_id = get_tournament_id_by_user(winner)
            await bot.send_message(chat_id=1155076760, text=f"{tournament_id, is_user_in_tournament(tournament_id, winner)} check 2")
            if tournament_id and is_user_in_tournament(tournament_id, winner):
                save_round_winner(tournament_id, str(winner), str(winner))
                cur_round = int(get_current_round_number(tournament_id))
                plrs = get_users_in_round(tournament_id, cur_round)
                nopir = int(get_number_of_groups_in_round(tournament_id, cur_round))
                await bot.send_message(chat_id=1155076760, text=f"{plrs}, {cur_round}, {get_number_of_winners(tournament_id, cur_round)} check 1")
                
                if int(get_number_of_winners(tournament_id, cur_round)) == nopir:
                    notify_round_results(tournament_id, cur_round)
                if not update_tournament_winner_if_round_finished(tournament_id, cur_round) == 12:
                    start_next_round(plrs, tournament_id, cur_round)
            delete_game(game_id)
            await delete_all_game_messages(game_id)
            return
        ms = f"Game has restarted! ♻️ \nYou all receive full cards again ✅ \nNow {get_user_nfgame(get_current_turn_user_id(game_id))}'s turn."
        players = get_all_players_in_game(game_id)
        for play in players:
            if not is_player_dead(game_id, play):
                mss = await bot.send_message(chat_id=play, text=ms)
                await save_message(play, game_id, mss.message_id)
        await reset_game_for_all_players(game_id)
    elif callback_query.data == "continue_game":
        rm = get_player_cards(game_id, user_id)
        cnt = 0
        array = get_all_players_in_game(game_id)
        for i in array:
            if not i:
                array.remove(i)
        while len(rm) == 0 and cnt < len(array):
            pls = get_all_players_in_game(game_id)
            for i in pls:
                if i and i != user_id:
                    mss = await bot.send_message(
                        chat_id=i,
                        text=f"Player {get_user_nfgame(user_id)} has no other cards so he skips his turn.",
                    )
                    await save_message(i, game_id, mss.message_id)
                    mss2 = await bot.send_message(
                        chat_id=user_id,
                        text=f"You have no other cards. You skipped your turn. ",
                    )
                    await save_message(user_id, game_id, mss2.message_id)
                    update_current_turn(game_id)
            rm = get_player_cards(game_id, get_current_turn_user_id(game_id))
            user_id = get_current_turn_user_id(game_id)
            cnt += 1

        if cnt == len(array):
            ms = f"Game has restarted! ♻️ \nYou all receive full cards again ✅ \nNow {get_user_nfgame(get_current_turn_user_id(game_id))}'s turn."
            players = get_all_players_in_game(game_id)
            for play in players:
                if not is_player_dead(game_id, play):
                    mss = await bot.send_message(chat_id=play, text=ms)
                    await save_message(play, game_id, mss.message_id)
            await reset_game_for_all_players(game_id)
            return
        rm = rm[0]
        addition_keyboard = InlineKeyboardButton(
            text="Send Cards 🟣",
            callback_data="send_cards",
        )
        remaining_cards = []
        for i in rm.split(","):
            remaining_cards.append(i)
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=card,
                        callback_data=f"select_card:{index}:{card}:unselected",
                    )
                    for index, card in enumerate(remaining_cards)
                ]
            ]
            + ([[addition_keyboard]])
        )
        mss = await bot.send_message(
            chat_id=user_id,
            text=f"Now it's your turn 🫵 \nCurrent table: {get_current_table(game_id)} \nHere are your cards: ",
            reply_markup=keyboard,
        )
        await save_message(user_id, game_id, mss.message_id)

    await callback_query.answer()


def get_previous_player_id(game_id, current_player_id):
    alive_players = get_all_players_in_game(game_id)
    if not alive_players:
        return None
    current_index = alive_players.index(current_player_id)
    previous_index = len(alive_players) - 1 if current_index == 0 else current_index - 1
    return alive_players[previous_index]


def get_next_player_id(game_id, current_player_id):
    players = get_all_players_in_game(game_id)
    for i in players:
        if is_player_dead(game_id, i) or not i:
            players.remove(i)
    current_index = players.index(current_player_id)
    ind = current_index + 1
    if ind > len(players):
        return players[0]
    else:
        return players[ind % len(players)]







async def reset_game_for_all_players(game_id):
    save_player_cards(game_id)
    await send_random_cards_to_players(game_id)



async def send_cards_update_to_players(game_id, player_id, num_cards_sent):
    players = get_all_players_in_game(game_id)
    for p_id in players:
        if not p_id:
            continue
        mss = await bot.send_message(
            chat_id=p_id,
            text=(
                f"Player {player_id} sent {num_cards_sent} cards."
                if p_id != player_id
                else "You sent your cards!"
            ),
        )
        await save_message(p_id, game_id, mss.message_id)

async def start_next_round(participants, tournament_id, round_number):
    groups = create_groups(participants)
    for nk in range(len(groups)):
        for jk in groups[nk]:
            save_tournament_round_info(tournament_id,round_number,jk, nk+1)
    await notify_groups(groups, round_number)
import uuid
async def notify_groups(groups, round_number):
    for idx, group in enumerate(groups, start=1):
        group_text = " ".join(
            f"\n{get_user_nfgame(user_id)} - {user_id}" for user_id in group
        )
        for user_id in group:
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=f"🏅 Round {round_number} - Group {idx}\n\n"
                    f"👥 Players in this game: \n{group_text}\n",
                )
            except Exception as e:
                print(f"Failed to notify user {user_id}: {e}")
    await asyncio.sleep(3)
    for gn in groups:
        gp = len(gn)
        for gt in gn:
            delete_user_from_all_games(gt)
        game_id = str(uuid.uuid4())
        conn = sqlite3.connect("users_database.db")
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO invitations (inviter_id, game_id, needed_players)
            VALUES (?, ?, ?)
            """,
            (gn[0], game_id, gp),
        )
        conn.commit()
        conn.close()
        for us in gn[1:]:
            insert_invitation(gn[0], us, game_id)
        mark_game_as_started(game_id)
        suits = ["heart ❤️", "diamond ♦️", "spade ♠️", "club ♣️"]
        current_table = random.choice(suits)
        cur_table = set_current_table(game_id, current_table)
        players = gn
        for player in players:
            create_game_record_if_not_exists(game_id, player)
            lent = len(players)
            if lent == 2:
                number = 19
            elif lent == 3:
                number = 23
            else:
                number = 27
            insert_number_of_cards(game_id, number)
            massiv = players
            s = ""
            rang = ["🔴", "🟠", "🟡", "🟢", "⚪️"]
            for row in range(len(massiv)):
                s += rang[row] + " " + get_user_nfgame(massiv[row]) + "\n"
            await bot.send_message(
                chat_id=player,
                text=(
                    f"Game has started. 🚀🚀🚀\n"
                    f"There are {number} cards in the game.\n"
                    f"{number//4} hearts — ♥️\n"
                    f"{number//4} diamonds — ♦️\n"
                    f"{number//4} spades — ♠️\n"
                    f"{number//4} clubs — ♣️\n"
                    f"2 universals — 🎴\n"
                    f"1 Joker — 🃏\n\n"
                    f"Players in the game: \n{s}\n"
                    f"Current table for cards: {cur_table}\n\n"
                ),
            )
        for player in players:
            set_real_bullet_for_player(game_id, player)
        set_current_turn(game_id, random.choice(players))
        save_player_cards(game_id)
        insert_number_of_cards(game_id, number)
        await send_random_cards_to_players(game_id)