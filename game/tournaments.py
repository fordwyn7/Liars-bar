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
from states.state import AddTournaments


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
    await message.answer(
        f"Here are what you can do with upcoming tournaments.",
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
        await message.answer("Please enter a valid number.")
        return
    await state.update_data(number_of_players=int(message.text))
    await message.answer("Please enter the registration start date (YYYY-MM-DD HH:MM):")
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
            "Please enter the registration end date (YYYY-MM-DD HH:MM):"
        )
        await state.set_state(AddTournaments.registr_end_date)
    except ValueError:
        await message.answer("Invalid date format. Please use YYYY-MM-DD HH:MM.")


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
            await message.answer("End date must be after the start date. Try again.")
            return
        await state.update_data(registration_end=end_date)
        await message.answer(
            "Please enter the tournament start date (YYYY-MM-DD HH:MM):"
        )
        await state.set_state(AddTournaments.turnir_start_date)
    except ValueError:
        await message.answer("Invalid date format. Please use YYYY-MM-DD HH:MM.")


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
                "Tournament start date must be after registration end date. Try again."
            )
            return
        await state.update_data(tournament_start=start_date)
        await message.answer("Please enter the tournament end date (YYYY-MM-DD HH:MM):")
        await state.set_state(AddTournaments.turnir_end_date)
    except ValueError:
        await message.answer("Invalid date format. Please use YYYY-MM-DD HH:MM.")


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
                "Tournament end date must be after the start date. Try again."
            )
            return
        await state.update_data(tournament_end=end_date)
        await message.answer("Please enter the tournament prize:")
        await state.set_state(AddTournaments.turnir_prize)
    except ValueError:
        await message.answer("Invalid date format. Please use YYYY-MM-DD HH:MM.")


# Step 6: Tournament prize and generate link
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
