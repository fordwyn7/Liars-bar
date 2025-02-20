import asyncio
import logging
import sqlite3
import uuid
import hendlers
import register
from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.deep_linking import create_start_link
from config import *
from keyboards.keyboard import *
from states.state import registration, registration_game, new_game
from keyboards.inline import *
from db import *
from aiogram.types import Update
import admin_panel
import game.tournaments

MAIN_ADMIN_ID = 1155076760
conn = sqlite3.connect("users_database.db")
cursor = conn.cursor()
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS users_database (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    registration_date TEXT, 
    nfgame TEXT
    )
    """
)
cursor.execute("PRAGMA table_info(users_database);")
columns = cursor.fetchall()
column_names = [column[1] for column in columns]

if "unity_coin" not in column_names:
    cursor.execute(
        """
        ALTER TABLE users_database
        ADD COLUMN unity_coin INTEGER DEFAULT 0
        """
    )
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS user_game_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    game_id TEXT NOT NULL,
    message_id INTEGER NOT NULL,
    UNIQUE(user_id, game_id, message_id)
);
"""
)
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS game_archive (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    game_id TEXT,
    game_start_time TEXT,
    game_end_time TEXT,
    game_winner TEXT
)
"""
)
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS invitations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        inviter_id INTEGER,
        invitee_id INTEGER,
        game_id TEXT,
        players_cnt INTEGER,
        needed_players INTEGER,
        is_started INTEGER,
        current_turn_user_id INTEGER,  
        number_of_cards INTEGER,
        FOREIGN KEY(inviter_id) REFERENCES users_database(user_id),
        FOREIGN KEY(invitee_id) REFERENCES users_database(user_id),
        UNIQUE(inviter_id, invitee_id, game_id)
    )
    """
)
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER UNIQUE
    );
"""
)
cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (MAIN_ADMIN_ID,))
cursor.execute(
    """
        CREATE TABLE IF NOT EXISTS game_state (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id TEXT,
            player_id TEXT,
            cards TEXT,
            last_cards TEXT,
            current_table TEXT, 
            real_bullet TEXT,
            blanks_count INTEGER,
            life_status TEXT,
            UNIQUE(game_id, player_id)
        )
    """
)
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS tournaments_table (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_id TEXT,
    tournament_prize TEXT,
    tournament_start_time TEXT,
    tournament_end_time TEXT,
    tournament_register_start_time TEXT,
    tournament_register_end_time TEXT,
    tournament_winner TEXT,
    maximum_players INTEGER
)
"""
)
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS tournament_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_id TEXT,
    user_id INTEGER,
    UNIQUE(tournament_id, user_id)

)
"""
)
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS tournament_rounds_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_id TEXT,
    round_number TEXT,
    round_user_id TEXT,
    group_number TEXT,
    round_winner TEXT,
    UNIQUE (tournament_id, round_number, group_number, round_user_id, round_winner)
)
"""
)
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS withdraw_options (
        three_month_premium TEXT,
        six_month_premium TEXT,
        twelve_month_premium TEXT,
        hundrad_stars TEXT,
        five_hundrad_stars TEXT,
        thousand_stars TEXT
    )
    """
)
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS users_referral (
    user_id INTEGER PRIMARY KEY,
    referred_by INTEGER
)
"""
)
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS unity_coin_referral (
    unity_coin_refferal INTEGER
)
"""
)
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS game_coin_table (
    game_coin INTEGER DEFAULT 5
)
"""
)
cursor.execute("SELECT COUNT(*) FROM unity_coin_referral")
count = cursor.fetchone()[0]
if count == 0:
    cursor.execute("INSERT INTO unity_coin_referral (unity_coin_refferal) VALUES (10)")
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS excludeds (
    game_id TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    number_of_excluded INTEGER DEFAULT 0,
    UNIQUE(game_id, user_id)
);
"""
)
cursor.execute(
    """
        CREATE TABLE IF NOT EXISTS daily_bonus (
            user_id INTEGER PRIMARY KEY,
            last_claim TEXT
        )
        """
)
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS user_languages (
    user_id INTEGER PRIMARY KEY,
    language TEXT NOT NULL,
    UNIQUE(user_id, language)
    );
    """
)
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS channels_earn (
    channel_id TEXT PRIMARY KEY,
    channel_link TEXT,
    UNIQUE(channel_id)
);
"""
)

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS channel_subscriptions (
    user_id TEXT,
    channel_id TEXT,
    PRIMARY KEY (user_id, channel_id),
    FOREIGN KEY (channel_id) REFERENCES channels_earn(channel_id)
);
"""
)

# cursor.execute("DELETE FROM channels_earn;")
# cursor.execute("DELETE FROM channel_subscriptions;")
# cursor.execute("DELETE FROM tournaments_table;")

conn.commit()
conn.close()


@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT language FROM user_languages WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row and message.text == "/start":
        await message.answer(
            "🟣 Please select your language: \n\n🔴 Пожалуйста, выберите язык: \n\n🔵 Iltimos, tilni tanlang:",
            reply_markup=select_language_button,
        )
        return

    payload = message.text.split(" ", 1)[-1] if " " in message.text else ""
    await state.update_data(payload=payload)
    ln = get_user_language(user_id)
    if "game_" in payload:
        if not is_user_registered(user_id):
            if ln == "ru":
                ms = "🎭 Добро пожаловать в Liar's Fortune! 🎭\nПожалуйста, введите *правильное* имя пользователя ✍️"
            elif ln == "uz":
                ms = "🎭 Liar's Fortune botiga hush kelibsiz! 🎭\nIltimos. o'zingiz uchun username kiriting ✍️"
            else:
                ms = "🎭 Welcome to Liar's Fortune! 🎭\nPlease enter *correct* username ✍️\n\n"
            await message.answer(ms, reply_markup=get_username_button(ln))
            await state.set_state(registration_game.pref1_name)
            return

        game_id = payload.split("game_")[1]
        if get_player_count(game_id) == 0:
            if ln == "ru":
                ms = "Игра уже завершена или остановлена. ☹️"
            elif ln == "uz":
                ms = "O'yin allaqachon tugagan yoki to'xtatilgan. ☹️"
            else:
                ms = "Game has already finished or been stopped. ☹️"
            await message.answer(ms)
            return
        if game_id == get_game_id_by_user(user_id):
            if user_id == get_game_inviter_id(game_id):
                if ln == "ru":
                    ms = "Вы уже в этой игре как создатель 🧑‍💻"
                elif ln == "uz":
                    ms = "Siz yaratuvchi sifatida allaqochon ushbu o'yindasiz 🧑‍💻"
                else:
                    ms = "You are already in this game as a creator 🧑‍💻"
                await message.answer(ms)
            else:
                if ln == "ru":
                    ms = "Вы уже в этой игре 😇"
                elif ln == "uz":
                    ms = "Siz allaqochon ushbu o'yindasiz 😇"
                else:
                    ms = "You are already in this game 😇"
                await message.answer(ms)
            return
        if get_needed_players(game_id) <= get_player_count(game_id):
            if ln == "ru":
                ms = "Нет свободного места для другого игрока или игра уже закончена 😞"
            elif ln == "uz":
                ms = "Boshqa o'yinchi uchun bo'sh joy qolmagan yoki o'yin allaqachon tugagan 😞"
            else:
                ms = "There is no available space for another player or the game has already finished 😞"
            await message.answer(ms)
            await state.clear()
            return

        user = message.from_user
        inviter_id = get_game_inviter_id(game_id)
        if not inviter_id:
            if ln == "ru":
                ms = "Эта игра завершена или остановлена ​​создателем."
            elif ln == "uz":
                ms = "Ushbu o'yin tugagan yoki yaratuvchi tomonidan to'xtatilgan."
            else:
                ms = "This game has finished or been stopped by the creator."
            await message.answer(ms)
            await state.clear()
            return
        if inviter_id and inviter_id == user.id:
            if ln == "ru":
                ms = "Вы уже в этой игре как создатель 🧑‍💻"
            elif ln == "uz":
                ms = "Siz yaratuvchi sifatida allaqochon ushbu o'yindasiz 🧑‍💻"
            else:
                ms = "You are already in this game as a creator 🧑‍💻"
            await message.answer(ms)
            return
        if is_user_in_game(game_id, user.id):
            if ln == "ru":
                ms = "Вы уже в этой игре 😇"
            elif ln == "uz":
                ms = "Siz allaqochon ushbu o'yindasiz 😇"
            else:
                ms = "You are already in this game 😇"
            await message.answer(ms)
            return
        if not inviter_id:
            if ln == "ru":
                ms = "Эта игра завершена или остановлена ​​создателем."
            elif ln == "uz":
                ms = "Ushbu o'yin tugagan yoki yaratuvchi tomonidan to'xtatilgan."
            else:
                ms = "This game has finished or been stopped by the creator."
            await message.answer(ms)
            await state.clear()
            return
        if has_incomplete_games(user_id):
            if ln == "ru":
                ms = "У вас есть незавершенные игры! \nПожалуйста, сначала остановите их и попробуйте снова. ♻️"
                kb = stop_incomplete_games_ru
            elif ln == "uz":
                ms = "Sizda hali tugallanmagan o'yin bot! \nIltimos avval shuni tugating so'ng qaytadan urinib ko'ring. ♻️"
                kb = stop_incomplete_games_uz
            else:
                ms = "You have incomplete games! \nPlease stop them first and try again. ♻️"
                kb = stop_incomplete_games
            await message.answer(
                ms,
                reply_markup=kb,
            )
            await state.clear()
            return

        insert_invitation(inviter_id, user.id, game_id)
        player_count = get_player_count(game_id)
        if player_count < 2:
            if ln == "ru":
                ms = "Эта игра завершена или остановлена ​​создателем."
            elif ln == "uz":
                ms = "Ushbu o'yin tugagan yoki yaratuvchi tomonidan to'xtatilgan."
            else:
                ms = "This game has finished or been stopped by the creator."
            await message.answer(ms)
            await state.clear()
            return
        name = get_user_nfgame(user.id)
        ln1 = get_user_language(inviter_id)
        if ln1 == "ru":
            ms1 = (
                f"Игрок {name} присоединился к игре 🎉 \nИгроки в игре: {player_count}"
            )
        elif ln1 == "uz":
            ms1 = f"{name} o'yinga qo'shildi 🎉\nO'yinchilar soni: {player_count}"
        else:
            ms1 = f"Player {name} has joined the game 🎉 \nPlayers in the game: {player_count}"
        if ln == "ru":
            ms = f"Вы успешно присоединились к игре! 🤩\nТекущее количество игроков: {player_count}\nДождитесь начала игры. 😊"
        elif ln == "uz":
            ms = f"Siz o'yinga muvaffaqiyatli qo'shildingiz! 🤩\nO'yindagi o'yinchilar soni: {player_count}\nO'yin boshlangunicha kutib turing. 😊"
        else:
            ms = f"You have successfully joined the game! 🤩\nCurrent number of players: {player_count}\nWaiting for everyone to be ready. 😊"

        await message.answer(ms)
        await bot.send_message(inviter_id, ms1)
        if get_needed_players(game_id) == get_player_count(game_id):
            if ln1 == "ru":
                ms = "Все игроки готовы. Вы можете начать игру прямо сейчас. "
                kb = start_stop_game_ru
            elif ln1 == "uz":
                ms = "Barcha o'yinchilar tayyor. O'yinni hoziroq boshlashingiz mumkin."
                kb = start_stop_game_uz
            else:
                ms = "All players ready. You can start the game right now."
                kb = start_stop_game
            await bot.send_message(
                inviter_id,
                ms,
                reply_markup=kb,
            )
        await state.clear()
    else:
        user = message.from_user
        if is_user_registered(user.id):
            if ln == "ru":
                ms = "Вы находитесь в главном меню 👇"
            elif ln == "uz":
                ms = "Siz asosiy menudasiz 👇 "
            else:
                ms = "You are in main menu 👇"
            await message.answer(
                ms,
                reply_markup=get_main_menu(user.id),
            )
        else:
            if ln == "ru":
                ms = "🎭 Добро пожаловать в Liar's Fortune! 🎭\nПожалуйста, введите *правильное* имя пользователя ✍️"
            elif ln == "uz":
                ms = "🎭 Liar's Fortune botiga hush kelibsiz! 🎭\nIltimos. o'zingiz uchun username kiriting ✍️"
            else:
                ms = "🎭 Welcome to Liar's Fortune! 🎭\nPlease enter *correct* username ✍️\n\n"
            await message.answer(ms, reply_markup=get_username_button(ln))
            await state.set_state(registration.pref_name)


@dp.callback_query(lambda c: c.data.startswith("lan_"))
async def set_language(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    language = callback.data.split("lan_")[1]
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO user_languages (user_id, language) VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET language = excluded.language
        """,
        (user_id, language),
    )
    conn.commit()
    conn.close()

    await callback.message.delete()
    await state.clear()
    await cmd_start(callback.message, state)


@dp.message(F.text.in_(["start game 🎮", "o'yinni boshlash 🎮", "новая игра 🎮"]))
async def start_game_handler(message: types.Message, state: FSMContext):
    ln = get_user_language(message.from_user.id)
    if ln == "ru":
        ms = "Вы участвуете в турнире и не сможете использовать эту кнопку до окончания турнира ❗️"
    elif ln == "uz":
        ms = "Siz turnirda ishtirok etyapsiz va turnir tugamaguncha bu tugmadan foydalana olmaysiz ❗️"
    else:
        ms = f"You are participating in a tournament and can't use this button until the tournament ends ❗️"
    if is_user_in_tournament_and_active(message.from_user.id):
        await message.answer(ms)
        return
    if ln == "ru":
        ms = "У вас есть незаконченная игра. Пожалуйста, сначала завершите это, прежде чем создавать новое."
        ms1 = "Выберите количество игроков: ⬇️"
        kb = stop_incomplete_games_ru
        kb1 = count_players_ru
    elif ln == "uz":
        ms = "Sizda hali tugallanmagan o'yin bor. Iltimos, yangi hosil qilishdan oldin avval shuni tugating."
        ms1 = "O'yinchilar sonini kiriting: ⬇️"
        kb = stop_incomplete_games_uz
        kb1 = count_players_uz
    else:
        ms = f"You have incomplete games. Please finish or stop them before creating a new one."
        ms1 = "Choose the number of players: ⬇️"
        kb = stop_incomplete_games
        kb1 = count_players
    if message.chat.type == "private":
        if has_incomplete_games(message.from_user.id):
            await message.answer(ms, reply_markup=kb)
            return
        await message.answer(ms1, reply_markup=kb1)
        await state.set_state(new_game.number_of_players)
    else:
        await message.answer("Please use this option in a private chat.")


@dp.message(
    F.text.in_(
        [
            "back to main menu 🔙",
            "вернуться в главное меню 🔙",
            "bosh menuga qaytish 🔙",
        ]
    )
)
async def start_game_handler(message: types.Message, state: FSMContext):
    await state.clear()
    ln = get_user_language(message.from_user.id)
    if ln == "ru":
        ms = "Вы находитесь в главном меню 👇"
    elif ln == "uz":
        ms = "Siz asosiy menudasiz 👇 "
    else:
        ms = "You are in main menu 👇"
    await message.answer(
        ms,
        reply_markup=get_main_menu(message.from_user.id),
    )


@dp.message(new_game.number_of_players)
async def get_name(message: types.Message, state: FSMContext):
    ln = get_user_language(message.from_user.id)
    if ln == "ru":
        ms = (
            "Вы ввели неверную информацию! Пожалуйста, выберите один из этих номеров: ⬇️"
        )
        kb = count_players_ru
    elif ln == "uz":
        ms = "Siz noto'g'ri ma'lumot kiritdingiz! Iltimos, quyidagi raqamlardan birini tanlang: ⬇️"
        kb = count_players_uz
    else:
        ms = "You have entered wrong information! Please choose one of these numbers: ⬇️"
        kb = count_players
    cnt = 0
    if message.text == "2️⃣":
        cnt = 2
    elif message.text == "3️⃣":
        cnt = 3
    elif message.text == "4️⃣":
        cnt = 4
    else:
        await message.answer(
            ms,
            reply_markup=kb,
        )
        await state.set_state(new_game.number_of_players)
        return

    user = message.from_user
    game_id = str(uuid.uuid4())
    invite_link = await create_start_link(bot, payload=f"game_{game_id}")
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO invitations (inviter_id, game_id, needed_players)
        VALUES (?, ?, ?)
        """,
        (user.id, game_id, cnt),
    )
    conn.commit()
    conn.close()
    if ln == "ru":
        ms = f"Вот ваша пригласительная ссылка. Поделитесь этой ссылкой с друзьями, чтобы играть в игру вместе 👇"
    elif ln == "uz":
        ms = f"Quida sizning o'yinga taklif havolangiz. Ushbu linkni birga o'ynamoqchi bo'lgan do'stlaringizga yuboring 👇"
    else:
        ms = f"Here is your invitation link. Share this link with your friends to play the game together 👇"
    await message.answer(
        ms,
        reply_markup=get_main_menu(user.id),
    )
    if ln == "ru":
        sharable_message = (
            "🎮 Присоединяйтесь к игре! 🎮\n\n"
            "Я только что создал игру и буду рад, если вы присоединитесь! 😊\n\n"
            "Нажмите на ссылку ниже, чтобы присоединиться к игре:\n"
            f"\n{invite_link}\n\n"
        )
    elif ln == "uz":
        sharable_message = (
            "🎮 O'yinga qo'shiling! 🎮\n\n"
            "Men siz bilan birga o'ynash uchun o'yin yaratdim va qoʻshilsangiz hursand bo'lar edim! 😊\n\n"
            "Oʻyinga qoʻshilish uchun quyidagi havolani bosing:\n"
            f"\n{invite_link}\n\n"
        )
    else:
        sharable_message = (
            "🎮 Join the Game! 🎮\n\n"
            "I just created a game, and I'd love for you to join! 😊\n\n"
            "Click the link below to join the game:\n"
            f"\n{invite_link}\n\n"
        )

    await message.answer(
        sharable_message,
    )
    await state.clear()


# @dp.message(F.text == "game status 🌟")
# async def start_game_handler(message: types.Message, state: FSMContext):
#     if is_user_in_tournament_and_active(message.from_user.id):
#         await message.answer(f"You are participating in a tournament and can't use this button until the tournament ends!")
#         return
#     game_id = get_game_id_by_user(message.from_user.id)
#     if not has_incomplete_games(message.from_user.id):
#         await message.answer(
#             f"You are not participating in any game currently.",
#             reply_markup=get_main_menu(message.from_user.id),
#         )
#     else:
#         msg = f"Current game status: active ✅\n"
#         if message.from_user.id == get_game_inviter_id(game_id):
#             msg += f"You are creator of this game 👨‍💻\nNumber of participants: {get_player_count(game_id)}"
#             await message.answer(msg, reply_markup=generate_exclude_keyboard(game_id))
#         else:
#             msg += f"You are participant in this game 👤\nNumber of participants: {get_player_count(game_id)}"
#             await message.answer(msg, reply_markup=cancel_g)


@dp.message()
async def any_word(msg: types.Message):
    if not is_user_registered(msg.from_user.id):
        await msg.delete()
    else:
        ln = get_user_language(msg.from_user.id)
        if ln == "ru":
            ms = f"Вы ввели незнакомую информацию."
        elif ln == "uz":
            ms = f"Siz noto'g'ri ma'lumot kiritdingiz."
        else:
            ms = f"You entered wrong information."
        await msg.answer(ms)


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
