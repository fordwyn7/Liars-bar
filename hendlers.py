import sqlite3
from config import dp, F, bot
from aiogram import types
from aiogram.fsm.context import FSMContext
from keyboards.keyboard import *
from keyboards.inline import *
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from states.state import NewGameState, MessagetoAdmin, awaiting_game_number
from db import *


@dp.message(F.text == "settings ⚙️")
async def settings(message: types.Message):
    await message.answer(f"Choose one of these options: ⬇️", reply_markup=change_name)


@dp.message(F.text == "❓ help")
async def help_butn(message: types.Message, state: FSMContext):
    await message.answer(
        "If you have any questions or suggestions, feel free to write here. An admin will respond as soon as possible. ⬇️",
        reply_markup=cancel_button,
    )

    await state.set_state(MessagetoAdmin.msgt)


@dp.message(MessagetoAdmin.msgt)
async def help_button_state(message: types.Message, state: FSMContext):
    if message.text != "back to main menu 🔙":
        await bot.send_message(
            chat_id=6807731973,
            text=f"User — {message.from_user.first_name} (<a href='tg://openmessage?user_id={message.from_user.id}'>{message.from_user.id}</a>) sent you message: \n{message.text}",
            parse_mode="HTML",
        )
        await message.answer(
            "Your message has been sent successfully ✅",
            reply_markup=get_main_menu(message.from_user.id),
        )

        await state.clear()
    else:
        await state.clear()
        await message.answer(
            f"You are in main menu 👇",
            reply_markup=get_main_menu(message.from_user.id),
        )


@dp.message(F.text == "change username 🖌")
async def changeee(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"Your current username is: {get_user_nfgame(message.from_user.id)}\nIf you'd like to change it, please type your new username:\n"
        f"⚠️ Note: Your username must be UNIQUE and can only contain:\n"
        f"- Latin alphabet characters (a-z, A-Z)\n"
        f"- Numbers (0-9)\n"
        f"- Underscores (_)\n"
        f"and you can use up to 20 characters",
        reply_markup=cancel_button,
    )
    await state.set_state(NewGameState.waiting_for_nfgame)


@dp.message(NewGameState.waiting_for_nfgame)
async def set_new_nfgame(message: types.Message, state: FSMContext):
    new_nfgame = message.text
    if is_game_started(get_game_id_by_user(message.from_user.id)):
        await message.answer(
            f"You are currently participating in a game and cannot change your username until the game ends.",
            reply_markup=get_main_menu(message.from_user.id),
        )
        await state.clear()
        return
    if new_nfgame == "back to main menu 🔙":
        await state.clear()
        await message.answer(
            f"You are in main menu ⬇️", reply_markup=get_main_menu(message.from_user.id)
        )
        return
    h = is_name_valid(new_nfgame)
    if not h:
        await message.answer(
            "Your data is incorrect! Please enter your username in a given format",
            reply_markup=cancel_button,
        )
    elif h == 2:
        await message.answer(
            "There is already user with this username in the bot. Please enter another username.",
            reply_markup=cancel_button,
        )
    else:
        user_id = message.from_user.id
        with sqlite3.connect("users_database.db") as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users_database SET nfgame = ? WHERE user_id = ?",
                (new_nfgame, user_id),
            )
            conn.commit()
        await message.answer(
            f"Your name has been successfully changed to: {new_nfgame} ✅",
            reply_markup=get_main_menu(message.from_user.id),
        )

        await state.clear()


@dp.message(F.text == "cancel 🚫")
async def cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"You have canceled changing the username.",
        reply_markup=get_main_menu(message.from_user.id),
    )


@dp.message(F.text == "information 📚")
async def statistics_a(message: types.Message, state: FSMContext):
    await state.clear()

    inline_buttons = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 Bot's Channel", url="https://t.me/liars_fortune_channel"
                ),
            ],
            [
                InlineKeyboardButton(text="👨‍💻 Creator", url="https://t.me/TechBotsy"),
            ],
        ]
    )

    await message.answer(
        f"Here are the bot's statistics 📈:\n\nTotal users in the bot 👥: {get_total_users()}\nBot has been active since 01.03.2025 📅\nBot's timezone ⏳: UTC +5\n\n❕ All data are presented in a bot's timezone",
        reply_markup=inline_buttons,
    )


@dp.message(F.text == "how to play 📝")
async def how_to_play(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "📚 *Game Rules* 📚\n\n"
        "👥 *Players:* 2-4 people.\n"
        "🃏 *Cards:* Each player starts with 5 cards.\n\n"
        "🔄 *How to Play:*\n"
        "A card is placed on the table to set the suit (❤️ ♦️ ♣️ ♠️).\n"
        "On your turn, you can play 1-3 cards that match the suit.\n"
        "If you have no matching cards, use the *Universal Card* 🎴.\n"
        "After playing, the next player can either:\n"
        "1️⃣ *Continue* - Accept the move and play their turn.\n"
        "2️⃣ *Call LIAR!* - Challenge the played cards.\n\n"
        "❗ *If LIAR is called:*\n"
        "✔️ *Truth?* The challenger gets “shot.”\n"
        "❌ *Lie?* You get “shot.”\n\n"
        "🌟 *Special Cards:*\n"
        "🎴 *Universal Card* - Matches any suit.\n"
        "🃏 *Joker* - Play it alone. If someone challenges, *everyone else gets shot!*\n\n"
        "⚙️ *Other Rules:*\n"
        "🔹 If you run out of cards, you skip your turn.\n"
        "🔹 The gun has 6 spots, but only 1 real bullet.\n\n"
        "🏆 *Winning Condition:*\n"
        "The last player left standing wins!",
        parse_mode="Markdown"
    )


def get_user_game_archive(user_id: int):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT game_id, game_start_time, game_end_time, game_winner
            FROM game_archive
            WHERE user_id = ?
            """,
            (user_id,),
        )
        games = cursor.fetchall()
        return games
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return []
    finally:
        conn.close()


@dp.message(F.text == "🎯 game archive")
async def show_game_archive(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    games = get_user_game_archive(user_id)

    if not games:
        await message.answer("No games found in your archive.")
        return
    response = "📜 Your Game Archive:\n\n"
    for idx, (_, start_time, _, _) in enumerate(games, start=1):
        response += f"{idx}. game — {start_time.split(' ')[0]} 📅\n"

    response += "\n📋 Send the game number to view its details."
    await message.answer(response, reply_markup=cancel_button)
    await state.set_state(awaiting_game_number.waiting)

def get_start_of_week():
    today = datetime.now(timezone.utc) 
    start_of_week = today - timedelta(days=today.weekday()) 
    return start_of_week.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%d 00:00:00")
def get_weekly_leaderboard():
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    
    start_of_week = get_start_of_week()
    cursor.execute('''
        SELECT user_id, COUNT(*) as total_games, 
               SUM(CASE WHEN SUBSTR(game_winner, INSTR(game_winner, '-') + 2) = CAST(user_id AS TEXT) THEN 1 ELSE 0 END) as games_won
        FROM game_archive
        WHERE game_end_time >= ?
        GROUP BY user_id
        ORDER BY games_won DESC, total_games DESC
        LIMIT 10
    ''', (start_of_week,))
    
    leaderboard = cursor.fetchall()
    conn.close()
    
    return leaderboard

def format_weekly_leaderboard():
    leaderboard = get_weekly_leaderboard()
    if not leaderboard:
        return "📅 No games played since Monday!"

    leaderboard_text = "🏆 Weekly Leaderboard 🏆\n\n"
    medals = ["🥇", "🥈", "🥉"]  

    for rank, (user_id, total_games, games_won) in enumerate(leaderboard, start=1):
        username = get_user_nfgame(user_id)
        medal = f"{medals[rank - 1]}. "if rank <= 3 else f"{rank}."
        leaderboard_text += f"{medal} {username} — 🎮 {total_games} | 🏆 {games_won}\n"

    return leaderboard_text
@dp.message(F.text == "🏅 Leaderboard")
async def show_weekly_leaderboard(message: types.Message):
    leaderboard_text = format_weekly_leaderboard()
    await message.answer(leaderboard_text)

@dp.message(awaiting_game_number.waiting)
async def send_game_statistics(message: types.Message, state: FSMContext):
    if message.text == "back to main menu 🔙":
        await state.clear()
        await message.answer(
            f"You are in main menu.", reply_markup=get_main_menu(message.from_user.id)
        )
        return
    user_id = message.from_user.id
    games = get_user_game_archive(user_id)

    if not message.text.isdigit():
        await message.answer(
            "❌ Please send a valid game number.", reply_markup=get_main_menu(user_id)
        )
        await state.clear()
        return
    game_number = int(message.text)
    if game_number < 1 or game_number > len(games):
        await message.answer(
            "❌ Invalid game number. Please try again.",
            reply_markup=get_main_menu(user_id),
        )
        await state.clear()
        return
    record_id, start_time, end_time, winner = games[game_number - 1]
    game_status = (
        f"🕹 Game Details:\n"
        f"🆔 Game ID: {record_id}\n"
        f"⏰ Start Time: {start_time}\n"
        f"🏁 End Time: {end_time if end_time else 'Has not finished'}\n"
        f"🏆 Winner: {winner if winner else 'No Winner'}"
    )
    await message.answer(
        game_status,
        reply_markup=get_main_menu(message.from_user.id),
    )
    await state.clear()


from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


@dp.message(F.text == "📱 cabinet")
async def my_cabinet(message: types.Message):
    user_id = message.from_user.id
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT registration_date, nfgame, unity_coin FROM users_database WHERE user_id = ?",
        (user_id,),
    )
    user_info = cursor.fetchone()
    if not user_info:
        await message.answer("❌ You are not registered in the database.")
        conn.close()
        return
    registration_date, nfgame, unity_coins = user_info
    cursor.execute("SELECT COUNT(*) FROM game_archive WHERE user_id = ?", (user_id,))
    games_played = cursor.fetchone()[0]
    conn.close()

    # Create the inline keyboard with the withdraw button
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💸 Withdraw Unity coins", callback_data="withdraw"
                ),
            ],
        ]
    )

    user_cabinet_message = (
        f"📱 Your Cabinet\n\n"
        f"👤 Username: {nfgame}\n"
        f"🗓 Registration Date: {registration_date}\n"
        f"🎮 Games Played: {games_played}\n"
        f"👥 referrals: {get_number_of_referrals(message.from_user.id)}\n"
        f"💰 Unity Coins: {unity_coins}\n"
    )
    await message.answer(
        user_cabinet_message, reply_markup=keyboard
    )


@dp.callback_query(lambda c: c.data == "withdraw")
async def process_withdraw_user(callback_query: types.CallbackQuery):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM withdraw_options LIMIT 1")
    withdraw_options = cursor.fetchone()
    if not withdraw_options:
        await callback_query.answer("❌ No withdrawal options found.")
        conn.close()
        return
    (
        three_month_premium,
        six_month_premium,
        twelve_month_premium,
        hundrad_stars,
        five_hundrad_stars,
        thousand_stars,
    ) = withdraw_options
    cursor.execute(
        "SELECT unity_coin FROM users_database WHERE user_id = ?",
        (callback_query.from_user.id,),
    )
    unity_coin = cursor.fetchone()[0]
    conn.close()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"❄️ 3 Months", callback_data="get_3_month"),
                InlineKeyboardButton(
                    text=f"⭐ 100 Stars", callback_data="get_100_stars"
                ),
            ],
            [
                InlineKeyboardButton(text=f"❄️ 6 Months", callback_data="get_6_month"),
                InlineKeyboardButton(
                    text=f"⭐ 500 Stars", callback_data="get_500_stars"
                ),
            ],
            [
                InlineKeyboardButton(text=f"❄️ 12 Months", callback_data="get_12_month"),
                InlineKeyboardButton(
                    text=f"⭐ 1,000 Stars", callback_data="get_1000_stars"
                ),
            ],
        ]
    )

    withdraw_message = (
        f"💳 Your current balance: {unity_coin} Unity Coins 💰\n\n"
        "💰 *Withdrawal options.*\n"
        f"🚀 *Telegram Premium*\n"
        f"❄️ *3 Months*: {three_month_premium} Unity Coins 💰\n"
        f"❄️ *6 Months*: {six_month_premium} Unity Coins 💰\n"
        f"❄️ *12 Months*: {twelve_month_premium} Unity Coins 💰\n\n"
        f"⭐️ *Telegram Stars* \n"
        f"✨ *100 Stars*: {hundrad_stars} Unity Coins 💰\n"
        f"✨ *500 Stars*: {five_hundrad_stars} Unity Coins 💰\n"
        f"✨ *1,000 Stars*: {thousand_stars} Unity Coins 💰\n\n"
        "Choose a button to get 👇"
    )
    await callback_query.message.answer(
        withdraw_message, parse_mode="Markdown", reply_markup=keyboard
    )


@dp.message(F.text == "🤩 tournaments")
async def show_tournaments_menu(message: types.Message):
    get_o = get_ongoing_tournaments()
    if get_o:
        await message.answer(
            "⚡ There is an ongoing tournament! 🎮\n"
            "You can participate if it's still open. 🔥",
            reply_markup=archive_tournamnets,
        )
        return
    tournaments = get_upcoming_tournaments()
    if not tournaments:
        await message.answer(
            "No upcoming tournaments are scheduled. 🏆\n"
            "But you can explore the archive of past tournaments. 📜",
            reply_markup=archive_tournamnets,
        )
        return
    for tournament in tournaments:
        response = (
            f"🌟 Tournament ID: {tournament['id']}\n\n"
            f"🗓 Starts: {tournament['start_time']}\n"
            f"🏁 Ends: {tournament['end_time']}\n\n"
            f"🏆 Prize: \n{tournament['prize']}\n\n"
            f"📢 Before the tournament begins, everyone will receive a notification to join. So be online at that time ❗️❗️❗️*\n"
        )

    await message.answer(
        response,
        reply_markup=archive_tournamnets,
    )


@dp.message(F.text == "❄️ referral")
async def tournaments_users_button(message: types.Message):
    referral_link = generate_referral_link(message.from_user.id)
    u_coins = get_unity_coin_referral()
    await message.answer(
        f"Here is your refferal link 👇\nSend this to your friends and get {u_coins} Unity Coins 💰 for each new friend."
    )
    await message.answer(
        f"🎮 *Hey!* Join this bot to play fun games and earn rewards! 🚀\n\n"
        f"👉 Use this link to get started 👇\n\n{referral_link}\n\n"
        "Play, earn, and enjoy! 😉"
    )
