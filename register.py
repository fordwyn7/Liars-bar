from config import bot, dp
from aiogram import types
from aiogram.fsm.context import FSMContext
from states.state import registration, registration_game
from keyboards.keyboard import get_main_menu
from keyboards.inline import *
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
    get_unity_coin_referral,
    get_user_language,
)
import sqlite3


def generate_referral_link(user_id):
    return f"https://t.me/liarsbar_game_robot?start={user_id}"


def add_user(user_id, referred_by):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO users_referral (user_id, referred_by) VALUES (?, ?)",
        (user_id, referred_by),
    )
    conn.commit()


@dp.message(registration.pref_name)
async def get_name_fem(message: types.Message, state: FSMContext):
    ln = get_user_language(message.from_user.id)
    if ln == "uz":
        m1 = "Iltimos avval username kiriting."
        m2 = "Noto'g'ri username! Iltimos, usernameni berilgan formatda kiriting"
        m3 = "Botda bu username bilan allaqachon foydalanuvchi mavjud. Iltimos, boshqa username kiriting."
        m4 = f"🎉 Muvaffaqiyatli roʻyxatdan oʻtganingiz bilan tabriklaymiz, {preferred_name}!\nUshbu variantlardan birini tanlang👇"
    elif ln == "ru":
        m1 = "Сначала введите свое имя пользователя."
        m2 = "Ваши данные неверны! Введите имя пользователя в указанном формате"
        m3 = "Пользователь с таким именем уже есть в боте. Введите другое имя пользователя."
        m4 = f"🎉 Поздравляем с успешной регистрацией, {preferred_name}!\nВыберите один из этих вариантов 👇"
    else:
        m1 = "Please enter your username first."
        m2 = "Your data is incorrect! Please enter your username in a given format"
        m3 = "There is already user with this username in the bot. Please enter another username."
        m4 = f"🎉 Congratulations on successfully registering, {preferred_name}!\nChoose one of these options 👇"
    user_data = await state.get_data()
    payload = user_data.get("payload", "")
    preferred_name = message.text.strip()
    if "/start" in message.text:
        await message.answer(m1)
        return
    h = is_name_valid(preferred_name)
    if not h:
        await message.answer(m2)
    elif h == 2:
        await message.answer(m3)
    else:
        user = message.from_user
        register_user(
            user.id, user.username, user.first_name, user.last_name, preferred_name
        )
        await message.answer(m4, reply_markup=get_main_menu(message.from_user.id))
        if payload.isdigit():
            try:
                referred_by = int(payload)
                add_user(message.from_user.id, referred_by)
                u_coin = get_unity_coin_referral()
                conn = sqlite3.connect("users_database.db")
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users_database SET unity_coin = unity_coin + ? WHERE user_id = ?",
                    (u_coin, referred_by),
                )
                conn.commit()
                conn.close()
                ln = get_user_language(referred_by)
                if ln == "uz":
                    ms = f"🎉 {preferred_name} taklif havolangiz orqali roʻyxatdan oʻtdi va siz +{u_coin} Unity Coinlarga ega boldingiz! 💰"
                elif ln == "ru":
                    ms = f"🎉 {preferred_name} успешно зарегистрировался по вашей реферальной ссылке, и вы получили +{u_coin} Unity Coin! 💰"
                else:
                    ms = f"🎉 {preferred_name} has successfully registered via your referral link, and you have received +{u_coin} Unity Coins! 💰"
                await bot.send_message(chat_id=referred_by, text=ms)
            except:
                pass
        await state.clear()


@dp.message(registration_game.pref1_name)
async def get_name(message: types.Message, state: FSMContext):
    ln = get_user_language(message.from_user.id)
    if ln == "uz":
        m1 = "Iltimos avval username kiriting."
        m2 = "Noto'g'ri username! Iltimos, usernameni berilgan formatda kiriting"
        m3 = "Botda bu username bilan allaqachon foydalanuvchi mavjud. Iltimos, boshqa username kiriting."
        m4 = f"🎉 Muvaffaqiyatli roʻyxatdan oʻtganingiz bilan tabriklaymiz, {preferred_name}!"
        m5 = "Bu ID bilan hech qanday oʻyin topilmadi yoki u allaqachon tugagan."
        m6 = "Siz yaratuvchi sifatida allaqochon ushbu o'yindasiz 🧑‍💻"
        m7 = "Siz allaqochon ushbu o'yindasiz 😇"
    elif ln == "ru":
        m1 = "Сначала введите свое имя пользователя."
        m2 = "Ваши данные неверны! Введите имя пользователя в указанном формате"
        m3 = "Пользователь с таким именем уже есть в боте. Введите другое имя пользователя."
        m4 = f"🎉 Поздравляем с успешной регистрацией, {preferred_name}!"
        m5 = "Игра с таким идентификатором не найдена или она уже завершена"
        m6 = "Вы уже в этой игре как создатель 🧑‍💻"
        m7 = "Вы уже в этой игре 😇"
    else:
        m1 = "Please enter your username first."
        m2 = "Your data is incorrect! Please enter your username in a given format"
        m3 = "There is already user with this username in the bot. Please enter another username."
        m4 = f"🎉 Congratulations on successfully registering, {preferred_name}!"
        m5 = "No game found with that ID or it has already finished."
        m6 = "You are already in this game as a creator 🧑‍💻"
        m7 = "You are already in this game 😇"
    user_data = await state.get_data()
    payload = user_data.get("payload", "")
    if "/start" in message.text:
        await message.answer(m1)
    if payload.startswith("game_"):
        game_id = payload.split("game_")[1]
        inviter_id = get_game_inviter_id(game_id)
        user = message.from_user
        preferred_name = message.text
        h = is_name_valid(preferred_name)
        if not h:
            await message.answer(m2)
        elif h == 2:
            await message.answer(m3)
        else:
            register_user(
                user.id, user.username, user.first_name, user.last_name, preferred_name
            )
            if not inviter_id:
                await message.answer(
                    m5, reply_markup=get_main_menu(message.from_user.id)
                )
                return
            if game_id == get_game_id_by_user(message.from_user.id):
                if message.from_user.id == get_game_inviter_id(game_id):
                    await message.answer(
                        m6, reply_markup=get_main_menu(message.from_user.id)
                    )
                else:
                    await message.answer(m7)
                return
            if get_player_count(game_id) == 0:
                if ln == "ru":
                    ms = "Игра уже завершена или остановлена. ☹️"
                elif ln == "uz":
                    ms = "O'yin allaqachon tugagan yoki to'xtatilgan. ☹️"
                else:
                    ms = "Game has already finished or been stopped. ☹️"
                await message.answer(
                    ms, reply_markup=get_main_menu(message.from_user.id)
                )
                return

            if get_needed_players(game_id) <= get_player_count(game_id):
                if ln == "ru":
                    ms = "Нет свободного места для другого игрока или игра уже закончена 😞"
                elif ln == "uz":
                    ms = "Boshqa o'yinchi uchun bo'sh joy qolmagan yoki o'yin allaqachon tugagan 😞"
                else:
                    ms = "There is no available space for another player or the game has already finished 😞"
                await message.answer(
                    ms, reply_markup=get_main_menu(message.from_user.id)
                )

                await state.clear()
                return
            insert_invitation(inviter_id, user.id, game_id)
            player_count = get_player_count(game_id)
            await message.answer(m4, reply_markup=get_main_menu(message.from_user.id))
            if ln == "ru":
                ms = f"Вы успешно присоединились к игре! 🤩\nТекущее количество игроков: {player_count}\nДождитесь начала игры. 😊"
            elif ln == "uz":
                ms = f"Siz o'yinga muvaffaqiyatli qo'shildingiz! 🤩\nO'yindagi o'yinchilar soni: {player_count}\nO'yin boshlangunicha kutib turing. 😊"
            else:
                ms = f"You have successfully joined the game! 🤩\nCurrent number of players: {player_count}\nWaiting for everyone to be ready. 😊"
            await message.answer(ms)
            ln1 = get_user_language(inviter_id)
            if ln1 == "ru":
                ms1 = f"Игрок {preferred_name} присоединился к игре 🎉 \nИгроки в игре: {player_count}"
            elif ln1 == "uz":
                ms1 = f"{preferred_name} o'yinga qo'shildi 🎉\nO'yinchilar soni: {player_count}"
            else:
                ms1 = f"Player {preferred_name} has joined the game 🎉 \nPlayers in the game: {player_count}"
            await bot.send_message(inviter_id, ms1)
            if ln1 == "ru":
                ms = "Все игроки готовы. Вы можете начать игру прямо сейчас. "
                kb = start_stop_game_ru
            elif ln1 == "uz":
                ms = "Barcha o'yinchilar tayyor. O'yinni hoziroq boshlashingiz mumkin."
                kb = start_stop_game_uz
            else:
                ms = "All players ready. You can start the game right now."
                kb = start_stop_game
            if get_needed_players(game_id) == get_player_count(game_id):
                await bot.send_message(inviter_id, ms, reply_markup=kb)

            await state.clear()
    else:
        await message.answer("Invalid game ID format. Please try again.")
