import sqlite3
import asyncio
import random
from config import bot, dp, F
from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from keyboards.keyboard import *
from db import *
from collections import Counter


@dp.callback_query(lambda c: c.data.startswith("confirm_remove_"))
async def remove_player_confirm(callback: types.CallbackQuery):
    player_id = int(callback.data.split("_")[2])
    game_id = get_game_id_by_user(player_id)
    ln = get_user_language(player_id)
    if ln == "uz":
        ms = "Siz qoidalarni quzganingiz uchun turnirdan chetlashtirildingiz 🤕"
    elif ln == "ru":
        ms = "Вы исключены из турнира из-за нарушения правил 🤕"
    else:
        ms = "You are elimitanated from the tournament because of breaking the rules 🤕"
    await bot.send_message(chat_id=player_id, text=ms)
    if game_id and is_user_turn(player_id, game_id):
        update_current_turn(game_id)
        remove_player(player_id)
        conn = sqlite3.connect("users_database.db")
        cursor = conn.cursor()
        cursor.execute(
            """
                    UPDATE game_state
                    SET life_status = 'dead'
                    WHERE game_id = ? AND player_id = ?
                    """,
            (game_id, player_id),
        )
        conn.commit()
        delete_user_from_all_games(player_id)
        winner = get_alive_number(game_id)
        if winner != 0:
            ln = get_user_language(winner)
            if ln == "uz":
                ms = "O'yin o'z nihoyasiga yetdi.\nSiz o'yinda g'olib bo'ldingiz 🥳🥳🥳🥳🥳\nG'olib bo'lganingiz bilan tabriklaymiz. \n🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉"
            elif ln == "ru":
                ms = "Игра окончена. \nВы победитель. 🥳🥳🥳🥳🥳\nПоздравляю с победой в игре. \n🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉"
            else:
                ms = "Game has finished. \nYou are winner. 🥳🥳🥳🥳🥳\nConguratulation on winning in the game. \n🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉"
            await bot.send_message(
                chat_id=winner,
                text=ms,
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
                    ln = get_user_language(users)
                    if ln == "uz":
                        ms = f"Siz mag'lub bo'lgan o'yin oz nihoyasiga yetdi ⭐️\nG'olib: {get_user_nfgame(winner)} (ID: {winner}) 🏆"
                    elif ln == "ru":
                        ms = f"Игра, в которой вы умерли, закончилась ⭐️\nПобедитель: {get_user_nfgame(winner)} (ID: {winner}) 🏆"
                    else:
                        ms = f"The game in which you died has ended ⭐️\nWinner: {get_user_nfgame(winner)} (ID: {winner}) 🏆"
                    await bot.send_message(
                        chat_id=users,
                        text=ms,
                    )
            tournament_id = get_tournament_id_by_user(winner)
            if tournament_id and is_user_in_tournament(tournament_id, winner):
                cur_round = int(get_current_round_number(tournament_id))
                await save_round_winner(tournament_id, str(winner), str(winner))
                nopir = int(get_number_of_groups_in_round(tournament_id, cur_round))
                # await bot.send_message(chat_id=1155076760, text=f"number of groups: {nopir}\nNumber of winners: {int(get_number_of_winners(tournament_id, cur_round))}\ncurrent round: {cur_round}")
                if (
                    int(get_number_of_winners(tournament_id, cur_round)) == nopir
                    and nopir != 1
                ):
                    await notify_round_results(tournament_id, cur_round)
                    await asyncio.sleep(5)
                    await start_next_round(tournament_id, cur_round + 1)
                elif (
                    nopir == 1
                    and int(get_number_of_winners(tournament_id, cur_round)) == 1
                ):
                    await update_tournament_winner_if_round_finished(
                        tournament_id, winner
                    )

            else:
                if not is_any_user_excluded(game_id):
                    coin = get_game_coin()
                    conn = sqlite3.connect("users_database.db")
                    cursor = conn.cursor()

                    cursor.execute(
                        "UPDATE users_database SET unity_coin = unity_coin + ? WHERE user_id = ? or nfgame = ?",
                        (coin, winner, winner),
                    )
                    conn.commit()
                    conn.close()
                    ln = get_user_language(winner)
                    if ln == "uz":
                        ms = f"Oʻyinda gʻalaba qozonganingiz uchun sizga {coin} Unity Coin mukofot berildi 🎁"
                    elif ln == "ru":
                        ms = f"Вы получили {coin} Unity coin за победу в игре 🎁"
                    else:
                        ms = f"You got {coin} Unity Coins for winning in the game 🎁"
                    await bot.send_message(
                        chat_id=winner,
                        text=ms,
                    )
            delete_game(game_id)
            await delete_all_game_messages(game_id)
            return
        players = get_all_players_in_game(game_id)
        for play in players:
            ln = get_user_language(play)
            if ln == "uz":
                ms = f"{get_user_nfgame(player_id)} turnir qoidalarini buzgani uchun admin tomonidan oʻyindan chetlashtirildi 🚷"
            elif ln == "ru":
                ms = f"Игрок {get_user_nfgame(player_id)} исключен из игры администраторами за нарушение правил турнира 🚷"
            else:
                ms = f"Player {get_user_nfgame(player_id)} excluded from game by admins for breaking the tournament rules 🚷"
            if not is_player_dead(game_id, play):
                mss = await bot.send_message(chat_id=play, text=ms)
                save_message(play, game_id, mss.message_id)
        for play in players:
            ln = get_user_language(play)
            if ln == "uz":
                ms = f"O'yin holati yangilandi! ♻️\nBarcha o'yinchilarga yana to'liq kartalar tarqatiladi ✅\nHozir {get_user_nfgame(get_current_turn_user_id(game_id))} ning yurish navbati."
            elif ln == "ru":
                ms = f"Игра перезапущена! ♻️ \nВы все снова получаете полные карты ✅ \nCейчас ход {get_user_nfgame(get_current_turn_user_id(game_id))}"
            else:
                ms = f"Game has restarted! ♻️ \nYou all receive full cards again ✅ \nNow {get_user_nfgame(get_current_turn_user_id(game_id))}'s turn."
            if not is_player_dead(game_id, play):
                mss = await bot.send_message(chat_id=play, text=ms)
                save_message(play, game_id, mss.message_id)
        await reset_game_for_all_players(game_id)
    else:
        remove_player(player_id)
        conn = sqlite3.connect("users_database.db")
        cursor = conn.cursor()
        cursor.execute(
            """
                    UPDATE game_state
                    SET life_status = 'dead'
                    WHERE game_id = ? AND player_id = ?
                    """,
            (game_id, player_id),
        )
        conn.commit()
        delete_user_from_all_games(player_id)
        players = get_all_players_in_game(game_id)
        for play in players:
            ln = get_user_language(play)
            if ln == "uz":
                ms = f"{get_user_nfgame(player_id)} turnir qoidalarini buzgani uchun admin tomonidan oʻyindan chetlashtirildi 🚷"
            elif ln == "ru":
                ms = f"Игрок {get_user_nfgame(player_id)} исключен из игры администраторами за нарушение правил турнира 🚷"
            else:
                ms = f"Player {get_user_nfgame(player_id)} excluded from game by admins for breaking the tournament rules 🚷"
            if not is_player_dead(game_id, play):
                mss = await bot.send_message(chat_id=play, text=ms)
                save_message(play, game_id, mss.message_id)
        winner = get_alive_number(game_id)
        if winner != 0:
            ln = get_user_language(winner)
            if ln == "uz":
                ms = "O'yin o'z nihoyasiga yetdi.\nSiz o'yinda g'olib bo'ldingiz 🥳🥳🥳🥳🥳\nG'olib bo'lganingiz bilan tabriklaymiz. \n🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉"
            elif ln == "ru":
                ms = "Игра окончена. \nВы победитель. 🥳🥳🥳🥳🥳\nПоздравляю с победой в игре. \n🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉"
            else:
                ms = "Game has finished. \nYou are winner. 🥳🥳🥳🥳🥳\nConguratulation on winning in the game. \n🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉"
            await bot.send_message(
                chat_id=winner,
                text=ms,
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
                    ln = get_user_language(users)
                    if ln == "uz":
                        ms = f"Siz mag'lub bo'lgan o'yin oz nihoyasiga yetdi ⭐️\nG'olib: {get_user_nfgame(winner)} (ID: {winner}) 🏆"
                    elif ln == "ru":
                        ms = f"Игра, в которой вы умерли, закончилась ⭐️\nПобедитель: {get_user_nfgame(winner)} (ID: {winner}) 🏆"
                    else:
                        ms = f"The game in which you died has ended ⭐️\nWinner: {get_user_nfgame(winner)} (ID: {winner}) 🏆"
                    await bot.send_message(
                        chat_id=users,
                        text=ms,
                    )
            tournament_id = get_tournament_id_by_user(winner)
            if tournament_id and is_user_in_tournament(tournament_id, winner):
                cur_round = int(get_current_round_number(tournament_id))
                await save_round_winner(tournament_id, str(winner), str(winner))
                nopir = int(get_number_of_groups_in_round(tournament_id, cur_round))
                # await bot.send_message(chat_id=1155076760, text=f"number of groups: {nopir}\nNumber of winners: {int(get_number_of_winners(tournament_id, cur_round))}\ncurrent round: {cur_round}")
                if (
                    int(get_number_of_winners(tournament_id, cur_round)) == nopir
                    and nopir != 1
                ):
                    await notify_round_results(tournament_id, cur_round)
                    await asyncio.sleep(5)
                    await start_next_round(tournament_id, cur_round + 1)
                elif (
                    nopir == 1
                    and int(get_number_of_winners(tournament_id, cur_round)) == 1
                ):
                    await update_tournament_winner_if_round_finished(
                        tournament_id, winner
                    )
            else:
                if not is_any_user_excluded(game_id):
                    coin = get_game_coin()
                    conn = sqlite3.connect("users_database.db")
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE users_database SET unity_coin = unity_coin + ? WHERE user_id = ? or nfgame = ?",
                        (coin, winner, winner),
                    )
                    conn.commit()
                    conn.close()
                    ln = get_user_language(winner)
                    if ln == "uz":
                        ms = f"Oʻyinda gʻalaba qozonganingiz uchun sizga {coin} Unity Coin mukofot berildi 🎁"
                    elif ln == "ru":
                        ms = f"Вы получили {coin} Unity coin за победу в игре 🎁"
                    else:
                        ms = f"You got {coin} Unity Coins for winning in the game 🎁"
                    await bot.send_message(
                        chat_id=winner,
                        text=ms,
                    )
            delete_game(game_id)
            await delete_all_game_messages(game_id)
            return
    await callback.message.edit_text("✅ Player removed successfully.")
    await callback.answer()


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


has_active_block = {}


async def send_random_cards_to_players(game_id):
    has_active_block.clear()
    selected_cards_count.clear()
    players = get_all_players_in_game(game_id)
    for player_id in players:
        ln = get_user_language(player_id)
        if not player_id or is_player_dead(game_id, player_id):
            continue
        pc = get_player_cards(game_id, player_id)
        player_cards = pc[0].split(",")
        is_turn = is_user_turn(player_id, game_id)
        if ln == "uz":
            sca = "Kartalarni tashlash 🟣"
            tms = (
                f"Endi yurish navbati sizda 🫵 \nBosh karta: {get_current_table(game_id)}\nSizning kartalaringiz: "
                if is_turn
                else f"Sizning kartalaringiz. \nHozir {get_user_nfgame(get_current_turn_user_id(game_id))} ning yurish navbati."
            )
        elif ln == "ru":
            sca = "Oтправлять карты 🟣"
            tms = (
                f"Теперь твоя очередь 🫵 \nОсновная карта: {get_current_table(game_id)}\nВот ваши карты: "
                if is_turn
                else f"Вот ваши карты. \nДождитесь своей очереди! Cейчас ход {get_user_nfgame(get_current_turn_user_id(game_id))}"
            )
        else:
            sca = "Send Cards 🟣"
            tms = (
                f"Now it's your turn 🫵 \nCurrent table: {get_current_table(game_id)} \nHere are your cards: "
                if is_turn
                else f"Here are your cards. \nWait for your turn! Now {get_user_nfgame(get_current_turn_user_id(game_id))}'s turn."
            )

        keyboard = [
            [
                InlineKeyboardButton(
                    text=f"{card}",
                    callback_data=(
                        f"select_card:{index}:{card}:unselected"
                        if is_turn
                        else "disabled"
                    ),
                )
                for index, card in enumerate(player_cards)
            ]
        ]

        if is_turn:
            keyboard.append(
                [InlineKeyboardButton(text=sca, callback_data="send_cards")]
            )
            tools = fetch_user_tools(player_id)
            if any(tools.values()):
                tool_buttons = []
                index = 6
                for tool, count in tools.items():
                    if count > 0:
                        tool_buttons.append(
                            InlineKeyboardButton(
                                text=tool.capitalize(),
                                callback_data=f"select_tool:{tool}:{index}:unselected",
                            )
                        )
                    index += 1
                keyboard.append(tool_buttons)
        await asyncio.sleep(2)
        message = await bot.send_message(
            chat_id=player_id,
            text=tms,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        )
        save_message(player_id, game_id, message.message_id)


selected_tool = {}


@dp.callback_query(lambda c: c.data.startswith("select_tool"))
async def select_super_tool(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    game_id = get_game_id_by_user(user_id)
    ln = get_user_language(user_id)
    data = callback_query.data.split(":")
    index = int(data[2])
    tool = data[1]
    current_state = data[3]
    if current_state == "unselected" and len(selected_tool) > 0:
        if ln == "uz":
            ut = "Siz faqat 1 ta tanlay olasiz holos."
        elif ln == "ru":
            ut = "Вы можете выбрать не более 1."
        else:
            ut = "You can only select 1 supper tool."
        await callback_query.answer(ut, show_alert=True)
        return
    new_state = "selected" if current_state == "unselected" else "unselected"
    new_text = f"{tool} ✅" if new_state == "selected" else tool
    if new_state == "selected":
        selected_tool[user_id] = tool
    elif current_state == "selected":
        selected_tool.clear()
    message = callback_query.message
    keyboard = message.reply_markup.inline_keyboard
    button = keyboard[2][index - 6]
    button.text = new_text
    button.callback_data = f"select_tool:{tool}:{index}:{new_state}"

    await bot.edit_message_reply_markup(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
    )
    await callback_query.answer(f"tool {tool} is now {new_state}.")


selected_cards_count = {}


@dp.callback_query(lambda c: c.data.startswith("select_card"))
async def toggle_card_selection(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    game_id = get_game_id_by_user(user_id)
    ln = get_user_language(user_id)
    if not is_user_turn(user_id, game_id):
        if ln == "uz":
            tn = "Hozir sining navbatining emas!"
        elif ln == "ru":
            tn = "Сейчас не твоя очередь!"
        else:
            tn = "It's not your turn!"
        await callback_query.answer(tn, show_alert=True)
        return
    data = callback_query.data.split(":")
    index = int(data[1])
    card = data[2]
    current_state = data[3]
    if user_id not in selected_cards_count:
        selected_cards_count[user_id] = 0
    if current_state == "unselected" and selected_cards_count[user_id] > 2:
        if ln == "uz":
            ut = "Siz 3 tagacha karta tanlay olasiz holos."
        elif ln == "ru":
            ut = "Вы можете выбрать не более 3 карт."
        else:
            ut = "You can only select up to 3 cards."
        await callback_query.answer(ut, show_alert=True)
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
    ln = get_user_language(user_id)
    if not is_user_turn(user_id, game_id):
        if ln == "uz":
            tn = "Hozir sining navbatining emas!"
        elif ln == "ru":
            tn = "Сейчас не твоя очередь!"
        else:
            tn = "It's not your turn!"
        await callback_query.answer(tn, show_alert=True)
        return

    selected_cards = [
        button.text.replace(" ✅", "")
        for row in keyboard
        for button in row
        if "✅" in button.text
    ]
    ty = []
    for i in selected_cards:
        if len(i)> 2:
            ty.append(i)
            selected_cards.remove(i)
            
    tool_used = ty
    if tool_used:
            tool_used = tool_used[0]
            conn = sqlite3.connect("users_database.db")
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE supper_tool
                SET {tool_used} = {tool_used} - 1
                WHERE user_id = ?
                """,
                (user_id,),
            )
            conn.commit()
            conn.close()
    selected_cards_count.clear()
    if selected_cards:
        await bot.delete_message(
            callback_query.from_user.id, callback_query.message.message_id
        )
        if ln == "uz":
            tn = f"Siz quyidagi kartalarni yubordingiz: {', '.join(selected_cards)}"
        elif ln == "ru":
            tn = f"Вы отправили следующие открытки: {', '.join(selected_cards)}"
        else:
            tn = f"You sent the following cards: {', '.join(selected_cards)}"
        mss = await bot.send_message(chat_id=callback_query.from_user.id, text=tn)
        save_message(callback_query.from_user.id, game_id, mss.message_id)
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
        if tool_used == "changer":
            insert_or_update_last_cards(
                game_id, [get_current_table(game_id).split()[-1]] * len(selected_cards)
            )
        else:
            insert_or_update_last_cards(game_id, selected_cards)
        update_current_turn(game_id)
    else:
        if ln == "uz":
            tn = "Hali kartalar tanlanmagan! Iltimos, avval kartalarni tanlang."
        elif ln == "ru":
            tn = "Карточки не выбраны! Сначала выберите карточки."
        else:
            tn = "No cards selected! Please choose cards first."
        callback_query.answer(tn, show_alert=True)
        return
    players = get_all_players_in_game(game_id)
    for p_id in players:
        if not p_id:
            continue
        ln = get_user_language(p_id)
        if ln == "uz":
            tn = f"O'yinchi {get_user_nfgame(user_id)} {len(selected_cards)} ta karta yubordi."
        elif ln == "ru":
            tn = (
                f"Игрок {get_user_nfgame(user_id)} отправил {len(selected_cards)} карту"
            )
        else:
            tn = f"Player {get_user_nfgame(user_id)} sent {len(selected_cards)} cards."
        if p_id != user_id:
            message = await bot.send_message(chat_id=p_id, text=tn)
            message_id = message.message_id
            save_message(p_id, game_id, message_id)
    user_id_change = False
    if tool_used == "skipper":
        next_player_id = get_next_player_id(game_id, user_id)
        update_current_turn(game_id)
        user_id_change = True
        for p_id in get_all_players_in_game(game_id):
            # if p_id != user
            ln = get_user_language(p_id)
            if ln == "uz":
                message = f"O'yinchi {get_user_nfgame(user_id)} {get_user_nfgame(next_player_id)} ning yurishini o'tkazib yubordi."
            elif ln == "ru":
                message = f"Игрок {get_user_nfgame(user_id)} пропустил ход {get_user_nfgame(next_player_id)}"
            else:
                message = f"{get_user_nfgame(user_id)} used Skipper! {get_user_nfgame(next_player_id)}'s turn is skipped."
            hjj = await bot.send_message(chat_id=p_id, text=message)
            save_message(p_id, game_id, hjj.message_id)
            await asyncio.sleep(2)
    if tool_used == "blocker":
        has_active_block[1] = True
    if user_id_change:
        user_id = next_player_id
    for p_id in players:
        if not p_id:
            continue
        ln = get_user_language(p_id)
        if ln == "uz":
            tn = f"Hozir {get_user_nfgame(get_next_player_id(game_id, user_id))} ning yurish navbati. \nSizning navbatingiz kelgunicha kutib turing. ⏰"
        elif ln == "ru":
            tn = f"Tекущий ход {get_user_nfgame(get_next_player_id(game_id, user_id))}. \nПожалуйста, подождите своей очереди ⏰"
        else:
            tn = f"Now {get_user_nfgame(get_next_player_id(game_id, user_id))}'s turn. \nPlease, wait until your turn ⏰"
        if p_id != get_next_player_id(game_id, user_id):
            message = await bot.send_message(
                chat_id=p_id,
                text=tn,
            )
            message_id = message.message_id
            save_message(p_id, game_id, message_id)
    next_player_id = get_next_player_id(game_id, user_id)
    ln = get_user_language(next_player_id)
    if ln == "uz":
        gb = "Davom ettirish 🚀"
        gb1 = "Yolg'on! 🙅‍♂️"
        mt = f"{get_user_nfgame(user_id)} o'z yurishini qildi. 🌟\n"
    elif ln == "ru":
        gb = "продолжить 🚀"
        gb1 = "лжец 🙅‍♂️"
        mt = f"{get_user_nfgame(user_id)} сделал свою очередь. 🌟"
    else:
        gb = "continue 🚀"
        gb1 = "liar 🙅‍♂️"
        mt = f"{get_user_nfgame(user_id)} made his turn 🌟"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=gb, callback_data="continue_game"),
            ]
        ]
    )
    if not has_active_block:
        keyboard.inline_keyboard[0].append(
            InlineKeyboardButton(text=gb1, callback_data="liar_game")
        )
    else:
        has_active_block.clear()
    message = await bot.send_message(
        chat_id=next_player_id,
        text=mt,
        reply_markup=keyboard,
    )
    message_id = message.message_id
    save_message(next_player_id, game_id, message_id)


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
            ln = get_user_language(previous_player_id)
            if ln == "uz":
                xb = f"{get_user_nfgame(user_id)} oxirgi kartani ochdi va bu Joker(🃏) kartasi bo'lib chiqdi 🫣. Endi barcha o'yinchilar o'zini o'zi otadi."
            elif ln == "ru":
                xb = f"Игрок {get_user_nfgame(user_id)} открыл последнюю отправленную карту, и это была карта Джокера(🃏), поэтому все игроки застрелятся."
            else:
                xb = f"Player {get_user_nfgame(user_id)} opened the last sent cards and it was a Joker(🃏) card, so all players will shoot themselves."
            message = await bot.send_message(chat_id=previous_player_id, text=xb)
            message_id = message.message_id
            save_message(previous_player_id, game_id, message_id)
            await asyncio.sleep(2)
            for player in players:
                ln = get_user_language(player)
                if ln == "uz":
                    xb = f"{get_user_nfgame(user_id)} oxirgi kartani ochdi va bu Joker(🃏) kartasi bo'lib chiqdi 🫣. Endi barchangiz o'zingizni otishga majbursiz."
                elif ln == "ru":
                    xb = f"Игрок {get_user_nfgame(user_id)} открыл последнюю отправленную карту, и это была карта Джокера(🃏), поэтому вы все должны застрелиться"
                else:
                    xb = f"Player {get_user_nfgame(user_id)} opened the last sent cards and it was a Joker(🃏) card,  so you all must shoot yourself."
                message = await bot.send_message(chat_id=player, text=xb)
                message_id = message.message_id
                save_message(player, game_id, message_id)
            await asyncio.sleep(3)
            for player in players:
                ln = get_user_language(player)
                bull = await shoot_self(game_id, player)
                if type(bull) == type(True):
                    await send_message_to_all_players(
                        game_id,
                        f"Player {get_user_nfgame(player)} shot himself and is dead by the real bullet 😵\nHe is now eliminated from the game.",
                        f"{get_user_nfgame(player)} o'zini otdi va qurolda haqiqiy o'q bo'lgani uchun halok bo'ldi 😵\nU endi o'yindan chetlashtirildi",
                        f"Игрок {get_user_nfgame(player)} застрелился и погиб от настоящей пули 😵\nТеперь он выбывает из игры.",
                    )
                    if is_user_turn(player, game_id):
                        update_current_turn(game_id)
                    if ln == "uz":
                        xb = f"Siz o'zingizni otib, qurolda haqiqiy o'q bo'lgani uchun halok bo'ldingiz va o'yindan chetlashtirildingiz 😵\nO'yin tugashi bilan sizga g'olib haqida xabar beramiz."
                    elif ln == "ru":
                        xb = f"Вы застрелились настоящей пулей 😵\nТеперь вы выбываете из игры. Мы сообщим победителю, когда игра закончится"
                    else:
                        xb = f"You shot yourself and dead by real bullet 😵\nNow you are eliminated from game. We will inform the winner when the game ends"
                    messa = await bot.send_message(chat_id=player, text=xb)
                    delete_user_from_all_games(player)
                    save_message(player, game_id, messa.message_id)
                else:
                    uz = f"{get_user_nfgame(player)} o'zini otdi va quroldagi oq haqiqiy bo'lmagani uchun TIRIK qoldi ⭕️. U o'yinda davom etadi ✅\nUning o'lish uchun keyingi ehtimolligi - 1/{6-bull}"
                    ru = f"Игрок {get_user_nfgame(player)} застрелился и НЕ умер из-за холостой пули ⭕️. Он может продолжить игру ✅\nЕго следующий шанс умереть - 1/{6-bull}"
                    await send_message_to_all_players(
                        game_id,
                        f"Player {get_user_nfgame(player)} shot himself and has NOT died because of the blank bullet ⭕️. He can continue the game ✅\nHis next chance to die - 1/{6-bull}",
                        uz,
                        ru,
                    )
                winner = get_alive_number(game_id)
                if winner != 0:
                    ln = get_user_language(winner)
                    if ln == "uz":
                        ms = "O'yin o'z nihoyasiga yetdi.\nSiz o'yinda g'olib bo'ldingiz 🥳🥳🥳🥳🥳\nG'olib bo'lganingiz bilan tabriklaymiz. \n🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉"
                    elif ln == "ru":
                        ms = "Игра окончена. \nВы победитель. 🥳🥳🥳🥳🥳\nПоздравляю с победой в игре. \n🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉"
                    else:
                        ms = "Game has finished. \nYou are winner. 🥳🥳🥳🥳🥳\nConguratulation on winning in the game. \n🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉"
                    await bot.send_message(
                        chat_id=winner,
                        text=ms,
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
                        ln = get_user_language(users)
                        if users and is_player_dead(game_id, users):
                            update_game_details(
                                game_id,
                                users,
                                get_user_nfgame(winner) + " - " + str(winner),
                            )
                            if ln == "uz":
                                ms = f"Siz mag'lub bo'lgan o'yin oz nihoyasiga yetdi ⭐️\nG'olib: {get_user_nfgame(winner)} (ID: {winner}) 🏆"
                            elif ln == "ru":
                                ms = f"Игра, в которой вы умерли, закончилась ⭐️\nПобедитель: {get_user_nfgame(winner)} (ID: {winner}) 🏆"
                            else:
                                ms = f"The game in which you died has ended ⭐️\nWinner: {get_user_nfgame(winner)} (ID: {winner}) 🏆"
                            await bot.send_message(chat_id=users, text=ms)
                    tournament_id = get_tournament_id_by_user(winner)
                    if tournament_id and is_user_in_tournament(tournament_id, winner):
                        cur_round = int(get_current_round_number(tournament_id))
                        await save_round_winner(tournament_id, str(winner), str(winner))
                        nopir = int(
                            get_number_of_groups_in_round(tournament_id, cur_round)
                        )
                        if (
                            int(get_number_of_winners(tournament_id, cur_round))
                            == nopir
                            and nopir != 1
                        ):
                            await notify_round_results(tournament_id, cur_round)
                            await asyncio.sleep(5)
                            await start_next_round(tournament_id, cur_round + 1)
                        elif (
                            nopir == 1
                            and int(get_number_of_winners(tournament_id, cur_round))
                            == 1
                        ):
                            await update_tournament_winner_if_round_finished(
                                tournament_id, winner
                            )
                    else:
                        if not is_any_user_excluded(game_id):
                            coin = get_game_coin()
                            conn = sqlite3.connect("users_database.db")
                            cursor = conn.cursor()
                            cursor.execute(
                                "UPDATE users_database SET unity_coin = unity_coin + ? WHERE user_id = ? or nfgame = ?",
                                (coin, winner, winner),
                            )
                            conn.commit()
                            conn.close()
                            ln = get_user_language(winner)
                            if ln == "uz":
                                ms = f"Oʻyinda gʻalaba qozonganingiz uchun sizga {coin} Unity Coin mukofot berildi 🎁"
                            elif ln == "ru":
                                ms = (
                                    f"Вы получили {coin} Unity coin за победу в игре 🎁"
                                )
                            else:
                                ms = f"You got {coin} Unity Coins for winning in the game 🎁"
                            await bot.send_message(
                                chat_id=winner,
                                text=ms,
                            )
                    delete_game(game_id)
                    await delete_all_game_messages(game_id)
                    return
            players = get_all_players_in_game(game_id)
            for play in players:
                ln = get_user_language(play)
                if ln == "uz":
                    ms = f"O'yin holati yangilandi! ♻️\nBarcha o'yinchilarga yana to'liq kartalar tarqatiladi ✅\nHozir {get_user_nfgame(get_current_turn_user_id(game_id))} ning yurish navbati."
                elif ln == "ru":
                    ms = f"Игра перезапущена! ♻️ \nВы все снова получаете полные карты ✅ \nCейчас ход {get_user_nfgame(get_current_turn_user_id(game_id))}"
                else:
                    ms = f"Game has restarted! ♻️ \nYou all receive full cards again ✅ \nNow {get_user_nfgame(get_current_turn_user_id(game_id))}'s turn."
                if not is_player_dead(game_id, play):
                    msss = await bot.send_message(chat_id=play, text=ms)
                    save_message(play, game_id, msss.message_id)
            await asyncio.sleep(2)
            await reset_game_for_all_players(game_id)
            return
        if not liar_bool:
            uz = f"{get_user_nfgame(user_id)} {get_user_nfgame(previous_player_id)} ni yolg'onchi deb hisobladi 🤥 \nVa u chindan ham haq edi 😎 \nYolg'onchining kartalari - {previous_player_cards}"
            ru = f"{get_user_nfgame(user_id)} предположил, что игрок {get_user_nfgame(previous_player_id)} солгал 🤥 \nОн был прав 😎 \nВот карты лжеца - {previous_player_cards}"
            await send_message_to_all_players(
                game_id,
                f"{get_user_nfgame(user_id)} has assumed that player {get_user_nfgame(previous_player_id)} lied 🤥 \nHe was actually right 😎 \nHere are the liar's cards - {previous_player_cards}",
                uz,
                ru,
            )
            bullet = await shoot_self(game_id, previous_player_id)
            await asyncio.sleep(3)
            uz = (
                f"Endi yolg'onchi o'zini otdi va qurolida haqiqiy o'q bor edi 🔰 \nOxir-oqibat u o'ldi va o'yindan chetlashtirildi 😵"
                if isinstance(bullet, bool) and bullet
                else f"Endi Yolg'onchi o'zini otdi va ammo to'pponchasida haqiqiy o'q YO'Q edi ⭕️\nU o'yinda qoladi ✅ \nUning keyingi safar o'lish imkoniyati 1/{6 - bullet}."
            )
            ru = (
                f"Теперь лжец застрелил себя, и в его пистолете была настоящая пуля 🔰 \nВ конце концов, он мертв и выбывает из игры 😵"
                if isinstance(bullet, bool) and bullet
                else f"Теперь лжец застрелил себя, и в его пистолете НЕТ настоящей пули ⭕️\nОн останется в игре ✅ \nЕго следующий шанс умереть — 1/{6 - bullet}."
            )
            msge = (
                f"Now liar shot himself and there was a real bullet in his gun 🔰 \nEventually, he is dead and eliminated from the game 😵"
                if isinstance(bullet, bool) and bullet
                else f"Now liar shot himself and there was NO real bullet in his pistol ⭕️\nHe will stay in the game ✅ \nHis next chance to die is 1/{6 - bullet}."
            )
            await send_message_to_all_players(
                game_id,
                msge,
                uz,
                ru,
            )
            if isinstance(bullet, bool) and bullet:
                ln = get_user_language(previous_player_id)
                if ln == "uz":
                    tt = "Siz o'zingizni otdingiz va qurolda haqiqiy o'q bo'lgani uchun halok bo'ldingiz 😵\nSiz o'yindan chetlashtirildingiz 😕"
                elif ln == "ru":
                    tt = "Теперь ты застрелился и умер от настоящей пули😵\nТы выбываешь из игры 😕"
                else:
                    tt = "Now you shot yourself and dead by real bullet 😵\nYou are eliminated from the game 😕"
                mjj = await bot.send_message(chat_id=previous_player_id, text=tt)
                if is_user_turn(previous_player_id, game_id):
                    update_current_turn(game_id)
                save_message(previous_player_id, game_id, mjj.message_id)
                delete_user_from_all_games(previous_player_id)
        else:
            await send_message_to_all_players(
                game_id,
                f"{get_user_nfgame(user_id)} has assumed that player {get_user_nfgame(previous_player_id)} lied 🤥. But he was NOT right 🫣. \nHere is his cards - {previous_player_cards}",
                f"{get_user_nfgame(user_id)} {get_user_nfgame(previous_player_id)} ni yolg'onchi deb hisobladi 🤥. Lekin u nohaq bo'lib chiqdi 🫣\nTashlangan kartalar - {previous_player_cards}",
                f"{get_user_nfgame(user_id)} предположил, что игрок {get_user_nfgame(previous_player_id)} солгал 🤥. Но он был НЕ прав 🫣. \nВот его карты - {previous_player_cards}",
            )
            bullet = await shoot_self(game_id, user_id)
            await asyncio.sleep(3)
            uz = (
                f"Endi {get_user_nfgame(user_id)} boshqalarni ayblagani uchun o'zini o'zi otdi 🔫\nQurolda haqiqiy o'q duch keldi 🥶\nOxir oqibat u o'ldi va o'yindan chetlashtirildi 😵"
                if isinstance(bullet, bool) and bullet
                else f"Endi {get_user_nfgame(user_id)} boshqalarni ayblagani uchun o'zini o'zi otdi 🔫\nLekin quroldagi o'q haqiqiy emas edi va u o'yinni davom etadi ✅\nUning o'lishga keyingi ehtimolligi - 1/{6 - bullet}"
            )
            ru = (
                f"Теперь игрок {get_user_nfgame(user_id)} застрелился из-за того, что обвинил других 🔫\nЭто была настоящая пуля в его пистолете 🥶 \nВ конце концов, он мертв и выбывает из игры 😵"
                if isinstance(bullet, bool) and bullet
                else f"Теперь игрок {get_user_nfgame(user_id)} застрелился из-за того, что обвинил других 🔫\nЭто была НЕ настоящая пуля, и она останется в игре ✅\nЕго следующий шанс умереть — 1/{6 - bullet}."
            )
            msge = (
                f"Now player {get_user_nfgame(user_id)} shot himself because of blaming others 🔫\nIt was a real bullet in his pistol 🥶 \nEventually, he is dead and eliminated from the game 😵"
                if isinstance(bullet, bool) and bullet
                else f"Now player {get_user_nfgame(user_id)} shot himself because of blaming others 🔫\nIt was NOT a real bullet and will stay in the game ✅\nHis next chance to die is 1/{6 - bullet}."
            )
            await send_message_to_all_players(game_id, msge, uz, ru)
            if isinstance(bullet, bool) and bullet:
                ln = get_user_language(user_id)
                if ln == "uz":
                    tt = "Siz boshqalarni ayblaganingiz uchun o'zingizni otdingiz va qurolda haqiqiy o'q bo'lgani uchun halok bo'ldingiz 😵\nSiz o'yindan chetlashtirildingiz 😕"
                elif ln == "ru":
                    tt = "Вы застрелились из-за того, что обвиняли других и умер от настоящей пули😵\nТы выбываешь из игры 😕"
                else:
                    tt = "You shot yourselef because of blaming others 🤥\nNow you are dead by real bullet, and eliminated from the game 😵"
                mjj = await bot.send_message(
                    chat_id=user_id,
                    text=tt,
                )
                if is_user_turn(user_id, game_id):
                    update_current_turn(game_id)
                delete_user_from_all_games(user_id)
                save_message(user_id, game_id, mjj.message_id)
        while is_player_dead(game_id, get_current_turn_user_id(game_id)):
            set_current_turn(
                game_id, get_next_player_id(game_id, get_current_turn_user_id(game_id))
            )
        winner = get_alive_number(game_id)
        if winner != 0:
            ln = get_user_language(winner)
            if ln == "uz":
                ms = "O'yin o'z nihoyasiga yetdi.\nSiz o'yinda g'olib bo'ldingiz 🥳🥳🥳🥳🥳\nG'olib bo'lganingiz bilan tabriklaymiz. \n🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉"
            elif ln == "ru":
                ms = "Игра окончена. \nВы победитель. 🥳🥳🥳🥳🥳\nПоздравляю с победой в игре. \n🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉"
            else:
                ms = "Game has finished. \nYou are winner. 🥳🥳🥳🥳🥳\nConguratulation on winning in the game. \n🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉"

            await bot.send_message(
                chat_id=winner,
                text=ms,
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
                    ln = get_user_language(users)
                    if ln == "uz":
                        ms = f"Siz mag'lub bo'lgan o'yin oz nihoyasiga yetdi ⭐️\nG'olib: {get_user_nfgame(winner)} (ID: {winner}) 🏆"
                    elif ln == "ru":
                        ms = f"Игра, в которой вы умерли, закончилась ⭐️\nПобедитель: {get_user_nfgame(winner)} (ID: {winner}) 🏆"
                    else:
                        ms = f"The game in which you died has ended ⭐️\nWinner: {get_user_nfgame(winner)} (ID: {winner}) 🏆"
                    await bot.send_message(
                        chat_id=users,
                        text=ms,
                    )
            tournament_id = get_tournament_id_by_user(winner)
            if tournament_id and is_user_in_tournament(tournament_id, winner):
                cur_round = int(get_current_round_number(tournament_id))
                await save_round_winner(tournament_id, str(winner), str(winner))
                nopir = int(get_number_of_groups_in_round(tournament_id, cur_round))
                if (
                    int(get_number_of_winners(tournament_id, cur_round)) == nopir
                    and nopir != 1
                ):
                    await notify_round_results(tournament_id, cur_round)
                    await asyncio.sleep(5)
                    await start_next_round(tournament_id, cur_round + 1)
                elif (
                    nopir == 1
                    and int(get_number_of_winners(tournament_id, cur_round)) == 1
                ):
                    await update_tournament_winner_if_round_finished(
                        tournament_id, winner
                    )
            else:
                if not is_any_user_excluded(game_id):
                    coin = get_game_coin()
                    conn = sqlite3.connect("users_database.db")
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE users_database SET unity_coin = unity_coin + ? WHERE user_id = ? or nfgame = ?",
                        (coin, winner, winner),
                    )
                    conn.commit()
                    conn.close()
                    ln = get_user_language(winner)
                    if ln == "uz":
                        ms = f"Oʻyinda gʻalaba qozonganingiz uchun sizga {coin} Unity Coin mukofot berildi 🎁"
                    elif ln == "ru":
                        ms = f"Вы получили {coin} Unity coin за победу в игре 🎁"
                    else:
                        ms = f"You got {coin} Unity Coins for winning in the game 🎁"
                    await bot.send_message(
                        chat_id=winner,
                        text=ms,
                    )
            delete_game(game_id)
            await delete_all_game_messages(game_id)
            return
        players = get_all_players_in_game(game_id)
        for play in players:
            if not is_player_dead(game_id, play):
                ln = get_user_language(play)
                if ln == "uz":
                    ms = f"O'yin holati yangilandi! ♻️\nBarcha o'yinchilarga yana to'liq kartalar tarqatiladi ✅\nHozir {get_user_nfgame(get_current_turn_user_id(game_id))} ning yurish navbati."
                elif ln == "ru":
                    ms = f"Игра перезапущена! ♻️ \nВы все снова получаете полные карты ✅ \nCейчас ход {get_user_nfgame(get_current_turn_user_id(game_id))}"
                else:
                    ms = f"Game has restarted! ♻️ \nYou all receive full cards again ✅ \nNow {get_user_nfgame(get_current_turn_user_id(game_id))}'s turn."
                mss = await bot.send_message(chat_id=play, text=ms)
                save_message(play, game_id, mss.message_id)
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
                    ln = get_user_language(i)
                    if ln == "uz":
                        ims = f"{get_user_nfgame(user_id)} da boshqa kartalar qolmagani uchun u navbatini o'tkazib yuboradi."
                    elif ln == "ru":
                        ims = f"У игрока {get_user_nfgame(user_id)} нет других карт, поэтому он пропускает свой ход."
                    else:
                        ims = f"Player {get_user_nfgame(user_id)} has no other cards so he skips his turn."
                    mss = await bot.send_message(
                        chat_id=i,
                        text=ims,
                    )
                    save_message(i, game_id, mss.message_id)
                    ln = get_user_language(user_id)
                    if ln == "uz":
                        ims = "Sizda boshqa karta yo'qligi uchun bu galgi navbatingizni o'tkizib yuborasiz."
                    elif ln == "ru":
                        ims = "Других карт у вас нет. Вы пропустили свою очередь."
                    else:
                        ims = "You have no other cards. You skipped your turn."
                    mss2 = await bot.send_message(
                        chat_id=user_id,
                        text=ims,
                    )
                    save_message(user_id, game_id, mss2.message_id)
                    update_current_turn(game_id)
            rm = get_player_cards(game_id, get_current_turn_user_id(game_id))
            user_id = get_current_turn_user_id(game_id)
            cnt += 1

        if cnt == len(array):
            players = get_all_players_in_game(game_id)
            for play in players:
                if not is_player_dead(game_id, play):
                    ln = get_user_language(play)
                    if ln == "uz":
                        ms = f"O'yin holati yangilandi! ♻️\nBarcha o'yinchilarga yana to'liq kartalar tarqatiladi ✅\nHozir {get_user_nfgame(get_current_turn_user_id(game_id))} ning yurish navbati."
                    elif ln == "ru":
                        ms = f"Игра перезапущена! ♻️ \nВы все снова получаете полные карты ✅ \nCейчас ход {get_user_nfgame(get_current_turn_user_id(game_id))}"
                    else:
                        ms = f"Game has restarted! ♻️ \nYou all receive full cards again ✅ \nNow {get_user_nfgame(get_current_turn_user_id(game_id))}'s turn."
                    mss = await bot.send_message(chat_id=play, text=ms)
                    save_message(play, game_id, mss.message_id)
            await reset_game_for_all_players(game_id)
            return
        rm = rm[0]
        ln = get_user_language(user_id)
        if ln == "uz":
            sca = "Kartalarni tashlash 🟣"
            tms = f"Endi yurish navbati sizda 🫵 \nBosh karta: {get_current_table(game_id)}\nSizning kartalaringiz: "
        elif ln == "ru":
            sca = "Oтправлять карты 🟣"
            tms = f"Теперь твоя очередь 🫵 \nОсновная карта: {get_current_table(game_id)}\nВот ваши карты: "
        else:
            sca = "Send Cards 🟣"
            tms = f"Now it's your turn 🫵 \nCurrent table: {get_current_table(game_id)} \nHere are your cards: "
        addition_keyboard = InlineKeyboardButton(
            text=sca,
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
        tools = fetch_user_tools(user_id)
        if any(tools.values()):
            tool_buttons = []
            index = 6
            for tool, count in tools.items():
                if count > 0:
                    tool_buttons.append(
                        InlineKeyboardButton(
                            text=tool.capitalize(),
                            callback_data=f"select_tool:{tool}:{index}:unselected",
                        )
                    )
                index += 1
            keyboard.inline_keyboard.append(tool_buttons)
        mss = await bot.send_message(
            chat_id=user_id,
            text=tms,
            reply_markup=keyboard,
        )
        save_message(user_id, game_id, mss.message_id)
    selected_tool.clear()
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
        ln = get_user_language(p_id)
        if ln == "uz":
            ims = f"{player_id} {num_cards_sent} ta karta tashladi."
            ims1 = "Siz kartalaringizni tashladingiz"
        elif ln == "ru":
            ims = f"Игрок {player_id} отправил {num_cards_sent} карточек."
            ims1 = f"Вы отправили свои открытки!"
        else:
            ims = f"Player {player_id} sent {num_cards_sent} cards."
            ims1 = f"You sent your cards!"
        mss = await bot.send_message(
            chat_id=p_id,
            text=(ims if p_id != player_id else ims1),
        )
        save_message(p_id, game_id, mss.message_id)


async def start_next_round(tournament_id, round_number):
    groups = create_groups(determine_round_winners(tournament_id, round_number - 1))
    for nk in range(len(groups)):
        for jk in groups[nk]:
            save_tournament_round_info(tournament_id, round_number, jk, nk + 1)
    await notify_groups(groups, round_number)


import uuid


async def notify_groups(groups, round_number):
    for idx, group in enumerate(groups, start=1):
        group_text = " ".join(
            f"\n{get_user_nfgame(user_id)} - {user_id}" for user_id in group
        )
        for user_id in group:
            try:
                ln = get_user_language(user_id)
                if ln == "uz":
                    rn = f"🏅 {round_number} chi Round - {idx} chi Guruh\n\n👥 O'yinchilar: \n{group_text}\n"
                elif ln == "ru":
                    rn = f"🏅 Раунд {round_number} - Группа {idx}\n\n👥 Игроки: \n{group_text}\n"
                else:
                    rn = f"🏅 Round {round_number} - Group {idx}\n\n👥 Players in this game: \n{group_text}\n"
                await bot.send_message(
                    chat_id=user_id,
                    text=rn,
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
            game_id = get_game_id_by_user(player)
            insert_number_of_cards(game_id, number)
            mark_game_as_started(game_id)
            massiv = players
            s = ""
            rang = ["🔴", "🟠", "🟡", "🟢", "⚪️"]
            for row in range(len(massiv)):
                s += rang[row] + " " + get_user_nfgame(massiv[row]) + "\n"
            ln = get_user_language(player)
            if ln == "uz":
                ims = (
                    f"O'yin boshlandi. 🚀🚀🚀\nO'yinda {number} ta karta mavjud:\n"
                    f"{number//4} hearts — ♥️\n"
                    f"{number//4} diamonds — ♦️\n"
                    f"{number//4} spades — ♠️\n"
                    f"{number//4} clubs — ♣️\n"
                    f"2 universals — 🎴\n"
                    f"1 Joker — 🃏\n\n"
                    f"O'yinchilar: \n{s}\n"
                    f"Bosh karta: {cur_table}"
                )
            elif ln == "ru":
                ims = (
                    f"Игра началась. 🚀🚀🚀\n"
                    f"В игре {number} карт.\n"
                    f"{number//4} hearts — ♥️\n"
                    f"{number//4} diamonds — ♦️\n"
                    f"{number//4} spades — ♠️\n"
                    f"{number//4} clubs — ♣️\n"
                    f"2 universals — 🎴\n"
                    f"1 Joker — 🃏\n\n"
                    f"Игроки: \n{s}\n"
                    f"Основная карта: {cur_table}"
                )
            else:
                ims = (
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
                )
            await bot.send_message(chat_id=player, text=ims)
        for player in players:
            set_real_bullet_for_player(game_id, player)
        set_current_turn(game_id, random.choice(players))
        save_player_cards(game_id)
        await send_random_cards_to_players(game_id)
