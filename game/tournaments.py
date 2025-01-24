import sqlite3
import uuid
import asyncio
from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from config import *
from keyboards.keyboard import *
from middlewares.registered import admin_required
from keyboards.inline import get_join_tournament_button, user_tournaments_keyboard
from db import *
from states.state import AddTournaments, EditRegistrationDates, EditStartAndEndTimes
from datetime import datetime, timezone, timedelta
from game.game_state import send_random_cards_to_players
@dp.message(F.text == "🏆 tournaments")
@admin_required()
async def tournaments_admin_panel(message: types.Message):
    # await message.answer(f"{create_groups([1,2,3,4,5,6,7,8,9])}")
    await message.answer(
        f"You are in tournaments section. \nPlease choose on of these options 👇",
        reply_markup=tournaments_admin_panel_button,
    )


@dp.message(F.text == "back to tournaments panel 🔙")
@admin_required()
async def back_to_tournaments_section(message: types.Message, state: FSMContext):
    await message.answer(
        f"You are in tournaments section. \nPlease choose on of these options.",
        reply_markup=tournaments_admin_panel_button,
    )
    await state.clear()


@dp.message(F.text == "⚡️ Ongoing")
@admin_required()
async def ongoing_tournaments_sekshn(message: types.Message):
    ongoing_tournaments = get_ongoing_tournaments()
    if not ongoing_tournaments:
        await message.answer(
            f"There are no ongoing tournaments 🤷‍♂️",
            reply_markup=tournaments_admin_panel_button,
        )
        return

    response = "⚡️ *Ongoing Tournaments:*\n\n"
    for tournament in ongoing_tournaments:
        response += (
            f"🌟 *{tournament['id']}*\n\n"
            f"🗓 Started: {tournament['start_time']}\n"
            f"🏁 Ends: {tournament['end_time']}\n\n"
            f"👥 Registered Players: {tournament['current_players']}/{tournament['maximum_players']}\n\n"
            f"🏆 Prize: \n{tournament['prize']}\n\n"
        )

    await message.answer(
        response,
        reply_markup=ongoing_tournaments_button,
        parse_mode="Markdown",
    )


@dp.message(F.text == "⏳ Upcoming")
@admin_required()
async def upcoming_tournaments_sekshn(message: types.Message):
    turnir = get_upcoming_tournaments()

    if not turnir:
        await message.answer(
            f"There are no upcoming tournaments 🤷‍♂️",
            reply_markup=tournaments_admin_panel_button,
        )
        return

    response = "🌟 *Upcoming Tournaments:*\n\n"
    for tournament in turnir:
        if "_" in tournament["name"]:
            nop = get_current_players(tournament["name"].split("_")[1])
        else:
            nop = get_current_players(tournament["name"])
        response += (
            f"🌟 Tournament ID: *{tournament['id']}*\n"
            f"🗓 Starts: {tournament['start_time']}\n"
            f"🏁 Ends: {tournament['end_time']}\n\n"
            f"🗓 Registration starts: {tournament['register_start']}\n"
            f"🏁 Registration ends: {tournament['register_end']}\n\n"
            f"👥 Registered Players: {nop}/{tournament['maximum_players']}\n\n"
            f"🏆 Prizes: \n\n{tournament['prize']}\n\n"
        )
    await message.answer(
        response,
        parse_mode="Markdown",
        reply_markup=upcoming_tournaments_button,
    )


@dp.message(F.text == "🗂 Archive")
@admin_required()
async def archive_tournaments_sekcsh(message: types.Message):
    tournaments = get_tournament_archive()
    if not tournaments:
        await message.answer(
            "No tournaments in the archive.",
            reply_markup=tournaments_admin_panel_button
        )
        return

    response = "📑 *Tournament Archive:*\n\n"
    for tournament in tournaments:
        response += f"🏆 ID: {tournament['id']}\n🌟 Started: {tournament["start_time"]}\n📅 Ended: {tournament["end_time"]}\n🥇 Winner: {tournament['winner']}\n\n"
    await message.answer(response, parse_mode="Markdown")


@dp.message(F.text == "➕ create a new Tournament")
@admin_required()
async def create_a_new_truine(message: types.Message, state: FSMContext):
    turnir = get_upcoming_tournaments()
    if turnir:
        await message.answer(
            f"⚠️ There is upcoming tournament and you can not create a new one unless you delete it.",
            reply_markup=tournaments_admin_panel_button,
        )
        await state.clear()
        return
    await message.answer(
        f"You are creating a new tournament ❗️\nPlease enter the maximum number of players: ",
        reply_markup=back_to_tournaments_button,
    )
    await state.set_state(AddTournaments.number_of_players)


@dp.message(AddTournaments.number_of_players)
async def set_number_of_players(message: types.Message, state: FSMContext):
    if message.text == "back to tournaments panel 🔙":
        await message.answer(
            f"You are in tournaments section.", reply_markup=tournaments_admin_panel_button
        )
        await state.clear()
        return
    if not message.text.isdigit():
        await message.answer("Please enter a valid number.", reply_markup=back_to_tournaments_button)
        return
    await state.update_data(number_of_players=int(message.text))
    await message.answer("Please enter the registration start date (YYYY-MM-DD HH:MM):", reply_markup=back_to_tournaments_button)
    await state.set_state(AddTournaments.registr_start_date)


@dp.message(AddTournaments.registr_start_date)
async def set_registration_start_date(message: types.Message, state: FSMContext):
    if message.text == "back to tournaments panel 🔙":
        await message.answer(
            f"You are in tournaments section.", reply_markup=tournaments_admin_panel_button
        )
        await state.clear()
        return
    try:
        start_date = datetime.strptime(message.text, "%Y-%m-%d %H:%M")
        await state.update_data(registration_start=start_date)
        await message.answer(
            "Please enter the registration end date (YYYY-MM-DD HH:MM):", reply_markup=back_to_tournaments_button
        )
        await state.set_state(AddTournaments.registr_end_date)
    except ValueError:
        await message.answer("Invalid date format. Please use YYYY-MM-DD HH:MM.", reply_markup=back_to_tournaments_button)


@dp.message(AddTournaments.registr_end_date)
async def set_registration_end_date(message: types.Message, state: FSMContext):
    if message.text == "back to tournaments panel 🔙":
        await message.answer(
            f"You are in tournaments section.", reply_markup=tournaments_admin_panel_button
        )
        await state.clear()
        return
    try:
        end_date = datetime.strptime(message.text, "%Y-%m-%d %H:%M")
        data = await state.get_data()
        if end_date <= data["registration_start"]:
            await message.answer("End date must be after the start date. Try again.", reply_markup=back_to_tournaments_button)
            return
        await state.update_data(registration_end=end_date)
        await message.answer(
            "Please enter the tournament start date (YYYY-MM-DD HH:MM):", reply_markup=back_to_tournaments_button
        )
        await state.set_state(AddTournaments.turnir_start_date)
    except ValueError:
        await message.answer("Invalid date format. Please use YYYY-MM-DD HH:MM.", reply_markup=back_to_tournaments_button)


@dp.message(AddTournaments.turnir_start_date)
async def set_tournament_start_date(message: types.Message, state: FSMContext):
    if message.text == "back to tournaments panel 🔙":
        await message.answer(
            f"You are in tournaments section.", reply_markup=tournaments_admin_panel_button
        )
        await state.clear()
        return
    try:
        start_date = datetime.strptime(message.text, "%Y-%m-%d %H:%M")
        data = await state.get_data()
        if start_date <= data["registration_end"]:
            await message.answer(
                "Tournament start date must be after registration end date. Try again.", reply_markup=back_to_tournaments_button
            )
            return
        await state.update_data(tournament_start=start_date)
        await message.answer("Please enter the tournament end date (YYYY-MM-DD HH:MM):", reply_markup=back_to_tournaments_button)
        await state.set_state(AddTournaments.turnir_end_date)
    except ValueError:
        await message.answer("Invalid date format. Please use YYYY-MM-DD HH:MM.", reply_markup=back_to_tournaments_button)


@dp.message(AddTournaments.turnir_end_date)
async def set_tournament_end_date(message: types.Message, state: FSMContext):
    if message.text == "back to tournaments panel 🔙":
        await message.answer(
            f"You are in tournaments section.", reply_markup=tournaments_admin_panel_button
        )
        await state.clear()
        return
    try:
        end_date = datetime.strptime(message.text, "%Y-%m-%d %H:%M")
        data = await state.get_data()
        if end_date <= data["tournament_start"]:
            await message.answer(
                "Tournament end date must be after the start date. Try again.", reply_markup=back_to_tournaments_button
            )
            return
        await state.update_data(tournament_end=end_date)
        await message.answer("Please enter the tournament prize:", reply_markup=back_to_tournaments_button)
        await state.set_state(AddTournaments.turnir_prize)
    except ValueError:
        await message.answer("Invalid date format. Please use YYYY-MM-DD HH:MM.", reply_markup=back_to_tournaments_button)


@dp.message(AddTournaments.turnir_prize)
async def set_tournament_prize(message: types.Message, state: FSMContext):
    await state.update_data(prize=message.text)
    data = await state.get_data()
    unique_id = f"{uuid.uuid4().hex}"
    await state.update_data(tournament_link=unique_id)
    save_tournament_to_db(data, unique_id)

    await message.answer(
        f"✅ Tournament created successfully:\n\n"
        f"🎮 Players: {data['number_of_players']}\n\n"
        f"🗓 Registration: {data['registration_start']} to {data['registration_end']}\n"
        f"🕹 Start: {data['tournament_start']} | End: {data['tournament_end']}\n\n"
        f"🏆 Prize: \n{data['prize']}\n\n"
        f"🔗 tournament id: {unique_id}",
        reply_markup=admin_panel_button,
    )
    await state.clear()


def save_tournament_to_db(data, tournamnet_link):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO tournaments_table (
                maximum_players, 
                tournament_register_start_time, 
                tournament_register_end_time, 
                tournament_start_time, 
                tournament_end_time, 
                tournament_prize, 
                tournament_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["number_of_players"],
                data["registration_start"],
                data["registration_end"],
                data["tournament_start"],
                data["tournament_end"],
                data["prize"],
                tournamnet_link,
            ),
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    finally:
        conn.close()


@dp.message(F.text == "🤩 tournaments")
@admin_required()
async def show_tournaments_menu(message: types.Message):
    await message.answer("Choose an option:", reply_markup=user_tournaments_keyboard)

@dp.message(F.text == "✏️ edit registration dates")
@admin_required()
async def edit_registration_dates_single(message: types.Message, state: FSMContext):
    tournaments = get_upcoming_tournaments()
    if not tournaments:
        await message.answer(
            "No upcoming tournaments available to edit.",
            reply_markup=tournaments_admin_panel_button,
        )
        await state.clear()
        return
    tournament = tournaments[0]
    tournament_id = tournament["name"]
    await state.update_data(tournament_id=tournament_id)
    await message.answer(
        f"You are editing the REGISTRATION date of current tournament\n\n📅 Current registration start time: {tournament['register_start']}.\n\n"
        "Please enter the new REGISTRATION *start date* in the format `YYYY-MM-DD HH:MM`:",
        parse_mode="Markdown",
        reply_markup=back_to_tournaments_button
    
    )
    await state.set_state(EditRegistrationDates.new_start_date)


@dp.message(EditRegistrationDates.new_start_date)
async def set_new_start_date_single(message: types.Message, state: FSMContext):
    if message.text == "back to tournaments panel 🔙":
        await message.answer(
            f"You are in tournaments section.", reply_markup=tournaments_admin_panel_button
        )
        await state.clear()
        return
    new_start_date = message.text.strip()
    try:
        datetime.strptime(new_start_date, "%Y-%m-%d %H:%M")
    except ValueError:
        await message.answer("Invalid date format. Please use `YYYY-MM-DD HH:MM`. Try again.", reply_markup=back_to_tournaments_button)
        return
    await state.update_data(new_start_date=new_start_date)
    tournaments = get_upcoming_tournaments()
    tournament = tournaments[0]
    await message.answer(
        f"📅 Current registration end time: {tournament['register_end']}.\n\nNow, enter the new REGISTRATION *end date* in the format `YYYY-MM-DD HH:MM`:",
        parse_mode="Markdown",
        reply_markup=back_to_tournaments_button
    )
    await state.set_state(EditRegistrationDates.new_end_date)


@dp.message(EditRegistrationDates.new_end_date)
async def set_new_end_date_single(message: types.Message, state: FSMContext):
    if message.text == "back to tournaments panel 🔙":
        await message.answer(
            f"You are in tournaments section.", reply_markup=tournaments_admin_panel_button
        )
        await state.clear()
        return
    new_end_date = message.text.strip()
    try:
        datetime.strptime(new_end_date, "%Y-%m-%d %H:%M")
    except ValueError:
        await message.answer("Invalid date format. Please use `YYYY-MM-DD HH:MM`. Try again.", reply_markup=back_to_tournaments_button)
        return
    data = await state.get_data()
    tournament_id = data["tournament_id"]
    new_start_date = data["new_start_date"]

    update_registration_dates(tournament_id, new_start_date, new_end_date)

    await message.answer(
        f"✅ Registration dates have been updated!\n\n"
        f"🗓 Start: {new_start_date}\n"
        f"🗓 End: {new_end_date}",
        reply_markup=tournaments_admin_panel_button,
    )
    await state.clear()

def update_registration_dates(tournament_id: str, start_date: str, end_date: str):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE tournaments_table
            SET tournament_register_start_time = ?, tournament_register_end_time = ?
            WHERE tournament_id = ?
            """,
            (start_date, end_date, tournament_id),
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    finally:
        conn.close()

@dp.message(F.text == "📝 edit starting dates")
@admin_required()
async def edit_start_and_end_times(message: types.Message, state: FSMContext):
    tournaments = get_upcoming_tournaments()
    if not tournaments:
        await message.answer(
            "No upcoming tournaments available to edit.",
            reply_markup=tournaments_admin_panel_button,
        )
        await state.clear()
        return
    await state.clear()
    tournament = tournaments[0]
    await state.update_data(tournament_id=tournament["name"])
    await message.answer(
        f"Editing the START time  for tournament.\n\n"
        f"📅 Current Start time: {tournament['start_time']}\n\n"
        "Please enter the new *start date* in the format `YYYY-MM-DD HH:MM`:",
        parse_mode="Markdown",
        reply_markup=back_to_tournaments_button
    )
    await state.set_state(EditStartAndEndTimes.new_start_date)


@dp.message(EditStartAndEndTimes.new_start_date)
async def set_new_start_date(message: types.Message, state: FSMContext):
    if message.text == "back to tournaments panel 🔙":
        await message.answer(
            f"You are in tournaments section.", reply_markup=tournaments_admin_panel_button
        )
        await state.clear()
        return
    new_start_date = message.text.strip()
    try:
        datetime.strptime(new_start_date, "%Y-%m-%d %H:%M")
    except ValueError:
        await message.answer("Invalid date format. Please use `YYYY-MM-DD HH:MM`. Try again.", reply_markup=back_to_tournaments_button)
        return
    await state.update_data(new_start_date=new_start_date)
    tournaments = get_upcoming_tournaments()
    tournament = tournaments[0]
    await message.answer(
        f"📅 Current End time: {tournament['end_time']}.\n\nNow, enter the new *end date* in the format `YYYY-MM-DD HH:MM`:",
        parse_mode="Markdown",
        reply_markup=back_to_tournaments_button
    )
    await state.set_state(EditStartAndEndTimes.new_end_date)


@dp.message(EditStartAndEndTimes.new_end_date)
async def set_new_end_date(message: types.Message, state: FSMContext):
    if message.text == "back to tournaments panel 🔙":
        await message.answer(
            f"You are in tournaments section.", reply_markup=tournaments_admin_panel_button
        )
        await state.clear()
        return
    new_end_date = message.text.strip()
    try:
        datetime.strptime(new_end_date, "%Y-%m-%d %H:%M")
    except ValueError:
        await message.answer("Invalid date format. Please use `YYYY-MM-DD HH:MM`. Try again.", reply_markup=back_to_tournaments_button)
        return

    data = await state.get_data()
    tournament_id = data["tournament_id"]
    new_start_date = data["new_start_date"]
    update_start_and_end_dates(tournament_id, new_start_date, new_end_date)
    await message.answer(
        f"✅ Start and end times for the tournament have been updated!\n\n"
        f"🗓 Start: {new_start_date}\n"
        f"🗓 End: {new_end_date}",
        reply_markup=tournaments_admin_panel_button,
    )
    await state.clear()

def update_start_and_end_dates(tournament_id: str, start_date: str, end_date: str):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE tournaments_table
            SET tournament_start_time = ?, tournament_end_time = ?
            WHERE tournament_id = ?
            """,
            (start_date, end_date, tournament_id),
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    finally:
        conn.close()






@dp.message(F.text == "✅ start the tournament")
@admin_required()
async def start_tournir_keyborar(message: types.Message, state: FSMContext):
    turnir = get_ongoing_tournaments()[0]
    tournament_id = turnir["name"]
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT tournament_id, tournament_start_time FROM tournaments_table WHERE tournament_id = ?",
        (tournament_id,)
    )
    tournament = cursor.fetchone()
    if not tournament:
        await message.answer(f"Tournament with ID {tournament_id} not found.", reply_markup=tournaments_admin_panel_button)
        return
    tournament_name, start_time = tournament
    uzbekistan_time = datetime.now(timezone.utc) + timedelta(hours=5)
    start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)

    if uzbekistan_time < start_time:
        await message.answer("Tournament cannot start before the scheduled time.", reply_markup=tournaments_admin_panel_button)
        return

    cursor.execute(
        "SELECT user_id FROM tournament_users WHERE tournament_id = ?",
        (tournament_id,)
    )
    # set_all_users_alive(tournament_id)
    participants = [row[0] for row in cursor.fetchall()]
    if len(participants) < 2:
        await message.answer("Not enough participants to start the tournament.", reply_markup=tournaments_admin_panel_button)
        return
    await notify_participants(participants, len(participants))
    round_number = 1
    while len(participants) > 1:
        groups = create_groups(participants)
        await notify_groups(groups, round_number)
        await asyncio.sleep(5 * 60)
        participants = determine_round_winners(groups)
        round_number += 1
    winner = participants[0]
    await announce_winner(winner, tournament_name)
    conn.close()
def create_groups(participants):
    random.shuffle(participants)
    groups = []
    nmb = len(participants)%4 
    nmd = len(participants)//4
    if nmb == 0:
        for i in range(0, len(participants), 4):
            groups.append(participants[i:i+4])
    elif nmb == 1:
        for i in range(0, nmd-1):
            groups.append(participants[:i+4])
            participants = participants[i+4:]
        groups.append(participants[:2])
        groups.append(participants[2:])
    else:
        for i in range(0, nmd):
            groups.append(participants[:i+4])
            participants = participants[i+4:]
        if participants:
            groups.append(participants)
    return groups
async def notify_participants(participants, num_participants):
    for user_id in participants:
        try:
            await bot.send_message(
                chat_id=user_id,
                text=f"🏆 The tournament is starting now❗️\n"
                     f"👥 Number of participants: {num_participants}\n"
                     "📋 Get ready for the first round!"
            )
        except Exception as e:
            print(f"Failed to notify user {user_id}: {e}")
def set_all_users_alive(tournament_id):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tournament_users SET user_status = 'alive' WHERE tournament_id = ?",
        (tournament_id,)
    )
    conn.commit()
    conn.close()

async def notify_groups(groups, round_number):
    for idx, group in enumerate(groups, start=1):
        group_text = ", ".join(f"Player {user_id}" for user_id in group)
        for user_id in group:
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=f"🏅 Round {round_number} - Group {idx}\n"
                         f"👥 Players in this game: {group_text}\n"
                )
            except Exception as e:
                print(f"Failed to notify user {user_id}: {e}")
    await asyncio.sleep(5)
    for gn in groups:
        gp = len(gn)
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
        suits = ["heart ❤️", "diamond ♦️", "spade ♠️", "club ♣️"]
        current_table = random.choice(suits)
        cur_table = set_current_table(game_id, current_table)
        players = gn
        await bot.send_message(chat_id=1155076760, text=f"{get_all_players_in_game(game_id)}")
        for player in players:
            delete_user_from_all_games(player)
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
            mark_game_as_started(game_id)
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
            set_real_bullet_for_player(game_id, player)
            set_current_turn(game_id, random.choice(players))
            save_player_cards(game_id)
            await send_random_cards_to_players(game_id)
def get_user_status(user_id):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_status FROM tournament_users WHERE user_id = ?",
        (user_id,)
    )
    status = cursor.fetchone()
    conn.close()
    if status:
        return status[0]
    return None


def determine_round_winners(groups):
    winners = []
    for group in groups:
        for user_id in group:
            user_status = get_user_status(user_id)
            if user_status == 'alive':
                winners.append(user_id)
                break
    return winners


async def announce_winner(winner, tournament_name):
    try:
        await bot.send_message(
            chat_id=winner,
            text=f"🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉\n\n Congratulations! You are the winner of the tournament! 🏆"
        )
    except Exception as e:
        print(f"Failed to notify the winner {winner}: {e}")

