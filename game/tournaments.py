import sqlite3
import uuid
from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from config import *
from keyboards.keyboard import *
from middlewares.registered import admin_required
from keyboards.inline import get_join_tournament_button, user_tournaments_keyboard
from db import *
from states.state import AddTournaments, EditRegistrationDates, EditStartAndEndTimes



@dp.message(F.text == "🏆 tournaments")
@admin_required()
async def tournaments_admin_panel(message: types.Message):
    await message.answer(
        f"You are in tournaments section. \nPlease choose on of these options 👇",
        reply_markup=tournaments_admin_panel_button,
    )


@dp.message(F.text == "back to tournaments panel 🔙")
@admin_required()
async def tournaments_admin_panel(message: types.Message):
    await message.answer(
        f"You are in tournaments section. \nPlease choose on of these options.",
        reply_markup=tournaments_admin_panel_button,
    )


@dp.message(F.text == "⚡️ Ongoing")
@admin_required()
async def tournaments_admin_panel(message: types.Message):
    await message.answer(
        f"Here are what you can do with ongoing tournaments.",
        reply_markup=ongoing_tournaments_button,
    )


@dp.message(F.text == "⏳ Upcoming")
@admin_required()
async def tournaments_admin_panel(message: types.Message):
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
            f"👥 Registered Players: {nop}/{tournament['maximum_players']}\n"
            f"🏆 Prizes: \n\n{tournament['prize']}\n\n"
        )
    await message.answer(
        response,
        parse_mode="Markdown",
        reply_markup=upcoming_tournaments_button,
    )


@dp.message(F.text == "🗂 Archive")
@admin_required()
async def tournaments_admin_panel(message: types.Message):
    await message.answer(
        f"Here are ended tournaments' statistics: 👇\n\n[List of tournamnets]",
        reply_markup=tournaments_admin_panel_button,
    )


@dp.message(F.text == "➕ create a new Tournament")
@admin_required()
async def tournaments_admin_panel(message: types.Message, state: FSMContext):
    turnir = get_upcoming_tournaments()
    if turnir:
        await message.answer(
            f"There is upcoming tournament and you can not create a new one unless you delete it.",
            reply_markup=tournaments_admin_panel_button,
        )
        await state.clear()
        return
    await message.answer(
        f"You are creating a new tournament ❗️\nPlease enter the number of players: ",
        reply_markup=back_to_tournaments_button,
    )
    await state.set_state(AddTournaments.number_of_players)


@dp.message(AddTournaments.number_of_players)
async def set_number_of_players(message: types.Message, state: FSMContext):
    if message.text == "back to tournaments panel 🔙":
        await message.answer(
            f"You are in tournaments section.", reply_markup=tournaments_admin_panel
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
            f"You are in tournaments section.", reply_markup=tournaments_admin_panel
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
            f"You are in tournaments section.", reply_markup=tournaments_admin_panel
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
            f"You are in tournaments section.", reply_markup=tournaments_admin_panel
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
            f"You are in tournaments section.", reply_markup=tournaments_admin_panel
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
        f"🎮 Players: {data['number_of_players']}\n"
        f"🗓 Registration: {data['registration_start']} to {data['registration_end']}\n"
        f"🕹 Start: {data['tournament_start']} | End: {data['tournament_end']}\n"
        f"🏆 Prize: \n\n{data['prize']}\n"
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
        return
    tournament = tournaments[0]
    tournament_id = tournament["name"]
    await message.answer(tournament["name"])
    await state.update_data(tournament_id=tournament_id)
    await message.answer(
        f"You are editing the REGISTRATION date of current tournament\n\n📅 Current registration time: {tournament['start_time']}.\n\n"
        "Please enter the new REGISTRATION *start date* in the format `YYYY-MM-DD HH:MM`:",
        parse_mode="Markdown",
        reply_markup=back_to_tournaments_button
    
    )
    await state.set_state(EditRegistrationDates.new_start_date)


@dp.message(EditRegistrationDates.new_start_date)
async def set_new_start_date_single(message: types.Message, state: FSMContext):
    if message.text == "back to tournaments panel 🔙":
        await message.answer(
            f"You are in tournaments section.", reply_markup=tournaments_admin_panel
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
    await message.answer(
        f"Now, enter the new REGISTRATION *end date* in the format `YYYY-MM-DD HH:MM`: ",
        parse_mode="Markdown",
        reply_markup=back_to_tournaments_button
    )
    await state.set_state(EditRegistrationDates.new_end_date)


@dp.message(EditRegistrationDates.new_end_date)
async def set_new_end_date_single(message: types.Message, state: FSMContext):
    if message.text == "back to tournaments panel 🔙":
        await message.answer(
            f"You are in tournaments section.", reply_markup=tournaments_admin_panel
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
            WHERE id = ?
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
        return

    tournament = tournaments[0]
    await state.update_data(tournament_id=tournament["name"])
    await message.answer(
        f"Editing the START time  for tournament.\n"
        f"Current Start: {tournament['start_time']} \nCurrent End: {tournament['end_time']}.\n\n"
        "Please enter the new *start date* in the format `YYYY-MM-DD HH:MM`:",
        parse_mode="Markdown",
        reply_markup=back_to_tournaments_button
    )
    await state.set_state(EditStartAndEndTimes.new_start_date)


@dp.message(EditStartAndEndTimes.new_start_date)
async def set_new_start_date(message: types.Message, state: FSMContext):
    if message.text == "back to tournaments panel 🔙":
        await message.answer(
            f"You are in tournaments section.", reply_markup=tournaments_admin_panel
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
    await message.answer(
        "Now, enter the new *end date* in the format `YYYY-MM-DD HH:MM`:",
        parse_mode="Markdown",
        reply_markup=back_to_tournaments_button
    )
    await state.set_state(EditStartAndEndTimes.new_end_date)


@dp.message(EditStartAndEndTimes.new_end_date)
async def set_new_end_date(message: types.Message, state: FSMContext):
    if message.text == "back to tournaments panel 🔙":
        await message.answer(
            f"You are in tournaments section.", reply_markup=tournaments_admin_panel
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
            WHERE id = ?
            """,
            (start_date, end_date, tournament_id),
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    finally:
        conn.close()
