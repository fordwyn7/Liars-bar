import sqlite3

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


@dp.message(F.text == "🆕 create a new Tournament")
@admin_required()
async def tournaments_admin_panel(message: types.Message, state: FSMContext):
    await message.answer(
        f"Here you can create a new tournament.",
        reply_markup=back_to_tournaments_button,
    )   
    # await state.set_state(AddTournaments.number_of_players)



@dp.message(F.text == "🤩 tournaments")
@admin_required()
async def show_tournaments_menu(message: types.Message):
    await message.answer("Choose an option:", reply_markup=user_tournaments_keyboard)

