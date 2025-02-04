import sqlite3
from aiogram import types
from aiogram.fsm.context import FSMContext
from middlewares.registered import admin_required
from keyboards.keyboard import *
from config import *
from db import *
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from states.state import *
from hendlers import get_user_game_archive
from datetime import datetime, timedelta

# from aiogram.utils.markdown import mention


def generate_callback(action: str, admin_id: int) -> str:
    return f"{action}:{admin_id}"


def get_admins2():
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM admins")
    admins = [
        {"id": row[0], "name": f"{get_user_nfgame(row[0])}"}
        for row in cursor.fetchall()
    ]
    conn.close()
    return admins


def get_statistics():
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()

    # Total users
    cursor.execute("SELECT COUNT(*) FROM users_database")
    total_users = cursor.fetchone()[0]

    # Total games played
    cursor.execute("SELECT COUNT(DISTINCT game_id) FROM game_archive")
    total_games = cursor.fetchone()[0]

    week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime(
        "%Y-%m-%d"
    )
    cursor.execute(
        "SELECT COUNT(*) FROM users_database WHERE registration_date >= ?",
        (week_start,),
    )
    users_joined_this_week = cursor.fetchone()[0]

    # Number of tournaments ended
    cursor.execute(
        "SELECT COUNT(*) FROM tournaments_table WHERE tournament_end_time <= datetime('now',  '+5 hours')"
    )
    tournaments_ended = cursor.fetchone()[0]

    # Number of upcoming tournaments
    cursor.execute(
        "SELECT COUNT(*) FROM tournaments_table WHERE tournament_start_time > datetime('now',  '+5 hours')"
    )
    upcoming_tournaments = cursor.fetchone()[0]

    # Create the statistics message
    stats_message = (
        "📊 *Game Statistics*\n\n"
        f"👥 *Total Users:* {total_users}\n"
        f"🎮 *Total Games Played:* {total_games}\n"
        f"🆕 *Users Joined This Week:* {users_joined_this_week}\n"
        f"🏁 *Tournaments Ended:* {tournaments_ended}\n"
        f"⏳ *Upcoming Tournaments:* {upcoming_tournaments}\n"
    )

    conn.close()
    return stats_message


@dp.message(F.text == "📊 statistics")
@admin_required()
async def main_to_menu(message: types.Message, state: FSMContext):
    try:
        stats_message = get_statistics()
        await message.answer(stats_message, parse_mode="Markdown")
    except Exception as e:
        await message.answer("❌ An error occurred while fetching statistics.")
        print(f"Error: {e}")


USERS_PER_PAGE = 10


def generate_user_list(users, page):
    start_index = (page - 1) * USERS_PER_PAGE
    end_index = start_index + USERS_PER_PAGE
    page_users = users[start_index:end_index]

    user_list = []
    for index, (user_id, nfgame) in enumerate(page_users, start=start_index + 1):
        user_list.append(
            f"{index}. <a href='tg://openmessage?user_id={user_id}'>{user_id}</a> — {nfgame}"
        )

    return user_list


def create_pagination_buttons(page, total_users):
    keyboard = []
    if page > 1:
        keyboard.append(
            InlineKeyboardButton(text="⬅️", callback_data=f"page_{page - 1}")
        )
    if page * USERS_PER_PAGE < total_users:
        keyboard.append(
            InlineKeyboardButton(text="➡️", callback_data=f"page_{page + 1}")
        )
    return InlineKeyboardMarkup(inline_keyboard=[keyboard])


def get_user_statistics(user_id):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT username, first_name, last_name, registration_date, nfgame, unity_coin
            FROM users_database WHERE user_id = ?
            """,
            (user_id,),
        )
        user_data = cursor.fetchone()
        if not user_data:
            return "❌ No user found with the given ID."
        username, first_name, last_name, registration_date, nfgame, unity_coin = (
            user_data
        )
        is_admin = "admin 🧑‍💻" if is_user_admin(user_id) else "user 🙍‍♂️"

        stats_message = (
            f"📊 **User Statistics** 📊\n\n"
            f"🙇‍♂️ **Role**: {is_admin} \n\n"
            f"👤 **Username**: {"@" + username if username else 'N/A'}\n\n"
            f"📛 **First Name**: {first_name if first_name else 'N/A'}\n\n"
            f"📜 **Last Name**: {last_name if last_name else 'N/A'}\n\n"
            f"🗓️ **Registr Date**: {registration_date if registration_date else 'N/A'}\n\n"
            f"🎮 **Username in bot**: {nfgame if nfgame else 'N/A'}\n\n"
            f"👥 referrals: {get_number_of_referrals(user_id)}\n\n"
            f"💰 Unity Coins: {unity_coin}"
        )

    except sqlite3.Error as e:
        stats_message = f"❌ Database error occurred: {e}"
    finally:
        conn.close()

    return stats_message


@dp.message(F.text == "🔙 main menu")
@admin_required()
async def main_to_menu(message: types.Message, state: FSMContext):
    await message.answer(
        f"You are in main menu.", reply_markup=get_main_menu(message.from_user.id)
    )


@dp.message(F.text == "🧑‍💻 admin panel")
@admin_required()
async def admin_panel(message: types.Message):
    await message.answer("You are in admin panel ⬇️", reply_markup=admin_panel_button)


@dp.message(F.text == "cancel 🚫")
@admin_required()
async def cancel_butt(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"Action is canceled. ✔️\You are in admin panel ⬇️",
        reply_markup=admin_panel_button,
    )


@dp.message(F.text == "back to admin panel 🔙")
@admin_required()
async def back_buttton(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(f"You are in admin panel ⬇️", reply_markup=admin_panel_button)


@dp.message(F.text == "👤 Admins")
@admin_required()
async def admins_button(message: types.Message):
    await message.answer(
        f"In this section, you can add, delete admins or see the list of them. ",
        reply_markup=admins_list_button,
    )


@dp.message(F.text == "➕ add admin")
@admin_required()
async def add_admin_command(message: types.Message, state: FSMContext):
    await message.answer(
        f"Enter the ID of the user that you want to make admin",
        reply_markup=back_button,
    )
    await state.set_state(Adminid.admin_id)


@dp.message(Adminid.admin_id)
async def add_admin_state(message: types.Message, state: FSMContext):
    i_d = message.text.strip()
    if not i_d.isdigit():
        await message.answer(
            f"❌ You entered wrong information. Please try again.",
            reply_markup=back_button,
        )
    elif not is_user_registered(i_d):
        await message.answer(
            f"❌ User not found or is not membor of the bot",
            reply_markup=admin_panel_button,
        )
        await state.clear()
    else:
        try:
            user_id = int(message.text.strip())
            add_admin(user_id)
            await message.answer(
                f"✅ User {user_id} has been added as an admin.",
                reply_markup=admin_panel_button,
            )
            await bot.send_message(
                chat_id=user_id,
                text="You are given an admin ✅",
                reply_markup=get_main_menu(user_id),
            )
            await state.clear()
        except ValueError:
            await message.answer(
                "❌ You entered wrong information. Please try again.",
                reply_markup=back_button,
            )
        await state.clear()


@dp.message(F.text == "🧾 list of admins")
@admin_required()
async def list_admins(message: types.Message):
    admins = get_admins2()
    keyboard = InlineKeyboardBuilder()
    for admin in admins:
        callback_data = generate_callback("delete_admin", admin["id"])
        keyboard.row(
            InlineKeyboardButton(
                text=f"❌ {admin['name']}",
                callback_data=callback_data,
            )
        )
    await message.answer(
        "Here is the list of admins:", reply_markup=keyboard.as_markup()
    )


@dp.callback_query(F.data.startswith("delete_admin"))
async def delete_admin_callback(query: types.CallbackQuery):
    callback_data = query.data.split(":")
    action = callback_data[0]
    admin_id = int(callback_data[1])

    if int(query.from_user.id) != 1155076760 and int(query.from_user.id) != 6807731973:
        await query.answer(
            f"You can not delete admin's because you are not the main admin ❗️"
        )
        return
    elif admin_id in [1155076760, 6807731973]:
        await query.answer(f"It is not possible to delete main admins.")
    else:
        if action == "delete_admin":
            conn = sqlite3.connect("users_database.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM admins WHERE user_id = ?", (admin_id,))
            conn.commit()
            conn.close()
            await query.answer("Admin was deleted successfully.")

            conn = sqlite3.connect("users_database.db")
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM admins")
            remaining_admins = [get_user_nfgame(row[0]) for row in cursor.fetchall()]
            conn.close()
            keyboard_builder = InlineKeyboardBuilder()
            for admin in remaining_admins:
                keyboard_builder.button(
                    text=f"❌ {admin}", callback_data=f"delete_admin:{admin}"
                )
            keyboard = keyboard_builder.as_markup()
            await query.message.edit_reply_markup(reply_markup=keyboard)


@dp.message(F.text == "📤 send message")
@admin_required()
async def choose_send_option(message: types.Message, state: FSMContext):
    await message.answer(
        "Here you can send a message anonymously.\nChoose one of these options ⏬",
        reply_markup=send_messages,
    )


@dp.message(F.text == "📨 send message to all")
@admin_required()
async def send_to_all_anonymously(message: types.Message, state: FSMContext):
    await message.answer(
        "Send me the message or post to forward anonymously to all users 📝",
        reply_markup=back_button,
    )
    await state.set_state(msgtoall.sendallanonym)


@dp.message(msgtoall.sendallanonym)
async def forward_to_all_users(message: types.Message, state: FSMContext):
    users = get_all_user_ids()
    from_chat_id = message.chat.id
    message_id = message.message_id
    cnt = 0
    for user_id in users:
        if user_id == message.from_user.id:
            continue
        try:
            await bot.copy_message(
                chat_id=user_id,
                from_chat_id=from_chat_id,
                message_id=message_id,
            )
        except Exception:
            cnt += 1
            continue
    await message.answer(
        f"Message was forwarded anonymously to {len(users) - cnt} users from {len(users)} successfully ✅",
        reply_markup=admin_panel_button,
    )
    await state.clear()


@dp.message(F.text == "📩 send message to one")
@admin_required()
async def send_to_one_anonymously(message: types.Message, state: FSMContext):
    await message.answer(
        "Enter the ID of the user you want to send the message to 📝",
        reply_markup=back_button,
    )
    await state.set_state(msgtoindividual.userid)


@dp.message(msgtoindividual.userid)
async def capture_user_id(message: types.Message, state: FSMContext):
    user_id = message.text.strip()
    if not user_id.isdigit():
        await message.answer("❌ You entered an invalid ID. Please try again.")
        return
    user_id = int(user_id)
    if user_id == message.from_user.id:
        await message.answer(
            "You cannot send a message to yourself.",
            reply_markup=admin_panel_button,
        )
        await state.clear()
        return
    await state.update_data(userid=user_id)
    await message.answer("Now send me the message or post to forward anonymously 📝")
    await state.set_state(msgtoindividual.sendtoone)


@dp.message(msgtoindividual.sendtoone)
async def forward_to_individual(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = int(data["userid"])

    try:
        await bot.copy_message(
            chat_id=user_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
        )
        await message.answer(
            "Message was forwarded anonymously to the user successfully ✅",
            reply_markup=admin_panel_button,
        )
    except Exception as e:
        await message.answer(
            f"An error occurred while sending the message: {e}",
            reply_markup=admin_panel_button,
        )
    finally:
        await state.clear()


@dp.message(F.text == "🧑‍🎓 users")
@admin_required()
async def users_butn(message: types.Message):
    await message.answer(
        f"In this section, you can get information of users.",
        reply_markup=users_control_button,
    )


@dp.message(F.text == "🪪 List of users")
@admin_required()
async def list_users(message: types.Message):
    try:
        with sqlite3.connect("users_database.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, nfgame FROM users_database")
            users = cursor.fetchall()
    except sqlite3.Error as e:
        await message.answer("An error has occured ...")
        return

    async def show_users(page=1):
        user_list = generate_user_list(users, page)
        user_details = "\n".join(user_list)
        pagination_buttons = create_pagination_buttons(page, len(users))
        await message.answer(
            f"Here is the list of users (page {page}):\n\n{user_details}",
            parse_mode="HTML",
            reply_markup=pagination_buttons,
        )

    await show_users(page=1)


@dp.callback_query(lambda c: c.data.startswith("page_"))
async def paginate_users(callback_query: types.CallbackQuery):
    page = int(callback_query.data.split("_")[1])
    try:
        with sqlite3.connect("users_database.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, nfgame FROM users_database")
            users = cursor.fetchall()
    except sqlite3.Error as e:
        print(e)
        await callback_query.answer(
            "An error has occured, please try again later", show_alert=True
        )
        return
    if page < 1 or (page - 1) * USERS_PER_PAGE >= len(users):
        await callback_query.answer(
            "You are in the first page!" if page < 1 else "You are in the last page!",
            show_alert=True,
        )
        return

    user_list = generate_user_list(users, page)
    user_details = "\n".join(user_list)
    pagination_buttons = create_pagination_buttons(page, len(users))
    await callback_query.message.edit_text(
        f"List of users (page {page}):\n\n{user_details}",
        parse_mode="HTML",
        reply_markup=pagination_buttons,
    )
    await callback_query.answer()


@dp.message(F.text == "🗒 information of user")
@admin_required()
async def info_users(message: types.Message, state: FSMContext):
    await message.answer(
        f"Enter the ID or username of the user that you want to get information",
        reply_markup=back_button,
    )
    await state.set_state(UserInformations.userid_state)


@dp.message(UserInformations.userid_state)
@admin_required()
async def state_info_users(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        user_id = get_id_by_nfgame(message.text)
        if not user_id:
            await message.answer(
                "❌ Please send a valid user ID or username",
                reply_markup=back_to_admin_panel,
            )
    else:
        user_id = int(message.text)
    if not is_user_registered(int(user_id)):
        await message.answer(
            f"No user found from given ID ☹️",
            reply_markup=admin_panel_button,
        )
    else:
        user_id = int(user_id)
        await message.answer(
            get_user_statistics(user_id),
            parse_mode="Markdown",
            reply_markup=admin_panel_button,
        )
    await state.clear()


@dp.message(F.text == "🎯 Game archive")
@admin_required()
async def admin_game_archive(message: types.Message, state: FSMContext):
    await message.answer(
        "Please send me the user ID or username to view their game archive 📋.",
        reply_markup=back_to_admin_panel,
    )
    await state.set_state(awaiting_user_id.await_id)


@dp.message(awaiting_user_id.await_id)
async def get_user_archive_by_id(message: types.Message, state: FSMContext):

    if not message.text.isdigit():
        user_id = get_id_by_nfgame(message.text)
        if not user_id:
            await message.answer(
                "❌ Please send a valid user ID or username",
                reply_markup=back_to_admin_panel,
            )
    else:
        user_id = int(message.text)
    games = get_user_game_archive(user_id)
    if not games:
        await message.answer(
            "No games found for this user.", reply_markup=admin_panel_button
        )
        await state.clear()
        return

    response = f"📜 *Game Archive for User {user_id}:*\n\n"
    for idx, (_, start_time, _, _) in enumerate(games, start=1):
        response += f"{idx}. game — {start_time.split(' ')[0]} 📅\n"

    response += "\n📋 *Send the game number to view its details.*"
    await message.answer(
        response, parse_mode="Markdown", reply_markup=back_to_admin_panel
    )
    await state.update_data(selected_user_id=user_id)
    await state.set_state(awaiting_admin_game_number.selected_user)


@dp.message(awaiting_admin_game_number.selected_user)
async def send_selected_user_game_statistics(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("selected_user_id")
    games = get_user_game_archive(user_id)
    if not message.text.isdigit():
        await message.answer(
            "❌ Please send a valid game number.", reply_markup=back_to_admin_panel
        )

    game_number = int(message.text)
    if game_number < 1 or game_number > len(games):
        await message.answer(
            "❌ Invalid game number. Please try again.",
            reply_markup=back_to_admin_panel,
        )
    record_id, start_time, end_time, winner = games[game_number - 1]
    game_status = (
        f"🕹 *Game Details:*\n"
        f"🆔 Game ID: {record_id}\n"
        f"⏰ Start Time: {start_time}\n"
        f"🏁 End Time: {end_time if end_time else 'Has not finished'}\n"
        f"🏆 Winner: {winner if winner else 'No Winner'}"
    )
    await message.answer(
        game_status, parse_mode="Markdown", reply_markup=back_to_admin_panel
    )


from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


@dp.message(F.text == "🚫 delete the tournament")
@admin_required()
async def delete_tournament_handler(message: types.Message):
    upcoming_tournament = get_upcoming_tournaments()
    if upcoming_tournament:
        tournament = upcoming_tournament[0]
        if "_" in tournament["name"]:
            nop = get_current_players(tournament["name"].split("_")[1])
        else:
            nop = get_current_players(tournament["name"])
        tournament_id = tournament["name"]
        response = (
            f"🌟 Tournament ID: {tournament['id']}\n\n"
            f"🗓 Starts: {tournament['start_time']}\n"
            f"🏁 Ends: {tournament['end_time']}\n\n"
            f"🗓 Registration starts: {tournament['register_start']}\n"
            f"🏁 Registration ends: {tournament['register_end']}\n\n"
            f"👥 Registered Players: {nop}\n"
            f"🏆 Prize: \n\n{tournament['prize']}\n\n"
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Yes", callback_data=f"confirm_delete:{tournament_id}"
                    ),
                    InlineKeyboardButton(text="❌ No", callback_data="cancel_delete"),
                ]
            ]
        )
        await message.answer(response, reply_markup=keyboard)
    else:
        await message.reply("There is no upcoming tournament to delete.")


@dp.callback_query(F.data == "cancel_delete")
async def cancel_delete_tournament(callback_query: types.CallbackQuery):
    await asyncio.sleep(1)
    await callback_query.message.answer(
        "Tournament deletion has been canceled.",
        reply_markup=ongoing_tournaments_button,
    )
    await callback_query.message.delete()


@dp.callback_query(F.data.startswith("confirm_delete:"))
async def confirm_delete_tournament(callback_query: types.CallbackQuery):
    tournament_id = callback_query.data.split(":")[1]

    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT user_id FROM tournament_users WHERE tournament_id = ?
            """,
            (tournament_id,),
        )
        registered_users = cursor.fetchall()
    finally:
        conn.close()

    delete_tournament(tournament_id)
    await callback_query.message.delete()

    for user in registered_users:
        try:
            await bot.send_message(
                chat_id=user[0],
                text=f"⚠️ The tournament you registered has been canceled. We apologize for any inconvenience. 😕",
            )
        except Exception as e:
            print(f"Failed to send message to user {user[0]}: {e}")

    await callback_query.message.answer(
        f"Tournament has been deleted. ✅\nYou are in tournaments section 👇",
        reply_markup=tournaments_admin_panel_button,
    )


@dp.message(F.text == "💳 user's balance")
@admin_required()
async def users_balance(message: types.Message, state: FSMContext):
    await message.answer(
        f"Here you can do changes with users' balances 👇",
        reply_markup=users_balance_button,
    )


@dp.message(F.text == "➕ Add Unity Coins to All Users")
@admin_required()
async def add_unity_coins_to_all(message: types.Message, state: FSMContext):
    await message.answer(
        "Please enter the amount of Unity Coins you want to add to all users:",
        reply_markup=back_to_admin_panel,
    )
    await state.set_state(waiting_for_coin_amount.unity_coin_amount)


@dp.message(waiting_for_coin_amount.unity_coin_amount)
@admin_required()
async def process_coin_amount(message: types.Message, state: FSMContext):
    if message.text == "back to admin panel 🔙":
        await message.answer(
            f"You are in admin panel 👇", reply_markup=admin_panel_button
        )
        await state.clear()
        return
    try:
        coin_amount = int(message.text.strip())
    except ValueError:
        await message.answer(
            "Please enter a valid number of Unity Coins.",
            reply_markup=back_to_admin_panel,
        )
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users_database")
    user_ids = cursor.fetchall()
    conn.close()
    if not user_ids:
        await message.answer("No users found in the database.")
        return
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    for user_id in user_ids:
        cursor.execute(
            "UPDATE users_database SET unity_coin = unity_coin + ? WHERE user_id = ?",
            (coin_amount, user_id[0]),
        )
    conn.commit()
    conn.close()
    await message.answer(
        f"✅ Successfully added {coin_amount} Unity Coins to all users.",
        reply_markup=users_balance_button,
    )
    await state.clear()


@dp.message(F.text == "👀 View User Unity Coins")
@admin_required()
async def view_users_balance(message: types.Message, state: FSMContext):
    await message.answer(
        "Please provide the user ID or username to view the Unity coin balance.",
        reply_markup=back_to_admin_panel,
    )
    await state.set_state(waiting_for_user_id_or_username.waiting_amount)


@dp.message(waiting_for_user_id_or_username.waiting_amount)
async def handle_user_input_for_balance(message: types.Message, state: FSMContext):
    if message.text == "back to admin panel 🔙":
        await message.answer(
            f"You are in admin panel 👇", reply_markup=admin_panel_button
        )
        await state.clear()
        return
    user_input = message.text.strip()
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, nfgame, unity_coin FROM users_database WHERE user_id = ? OR nfgame = ?",
        (user_input, user_input),
    )
    user = cursor.fetchone()

    if user:
        global username
        user_id, username, unity_coin = user
        await message.answer(
            f"📊 User Information: \n\n"
            f"👤 Username: {username}\n"
            f"💰 Unity Coins: {unity_coin}\n"
            f"🆔 User ID: {user_id}\n\n"
            "Choose an action below:",
            reply_markup=change_users_balance,
        )
        await state.clear()

    else:
        await message.answer("❌ User not found. :(", reply_markup=users_balance_button)
        await state.clear()
        return


@dp.message(F.text == "➕ Add Unity Coins")
@admin_required()
async def add_unity_coins(message: types.Message, state: FSMContext):
    if username:
        await message.answer(
            "Please provide the amount of Unity coins to add.",
            reply_markup=back_to_admin_panel,
        )
        await state.set_state(
            waiting_for_user_id_or_username.waiting_for_add_coin_amount
        )
    else:
        await message.answer(
            "❌ No user selected. Please try again.", reply_markup=back_to_admin_panel
        )


@dp.message(waiting_for_user_id_or_username.waiting_for_add_coin_amount)
async def handle_add_unity_coins(message: types.Message, state: FSMContext):
    if message.text == "back to admin panel 🔙":
        await message.answer(
            f"You are in admin panel 👇", reply_markup=admin_panel_button
        )
        await state.clear()
        return
    try:
        add_amount = int(message.text.strip())
        if add_amount <= 0:
            await message.answer(
                "❌ The amount must be greater than 0.",
                reply_markup=back_to_admin_panel,
            )
            return

        conn = sqlite3.connect("users_database.db")
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users_database SET unity_coin = unity_coin + ? WHERE user_id = ? or nfgame = ?",
            (add_amount, username, username),
        )
        conn.commit()
        conn.close()

        await message.answer(
            f"✅ {add_amount} Unity Coins have been added to the user's balance!",
            reply_markup=change_users_balance,
        )
        await state.clear()
    except ValueError:
        await message.answer(
            "❌ Please provide a valid number for Unity coins.",
            reply_markup=back_to_admin_panel,
        )


@dp.message(F.text == "➖ Subtract Unity Coins")
@admin_required()
async def subtract_unity_coins(message: types.Message, state: FSMContext):
    if username:
        await message.answer(
            "Please provide the amount of Unity coins to subtract.",
            reply_markup=back_to_admin_panel,
        )
        await state.set_state(
            waiting_for_user_id_or_username.waiting_for_subtract_coin_amount
        )
    else:
        await message.answer(
            "❌ No user selected. Please try again.", reply_markup=back_to_admin_panel
        )


@dp.message(waiting_for_user_id_or_username.waiting_for_subtract_coin_amount)
async def handle_subtract_unity_coins(message: types.Message, state: FSMContext):
    if message.text == "back to admin panel 🔙":
        await message.answer(
            f"You are in admin panel 👇", reply_markup=admin_panel_button
        )
        await state.clear()
        return
    if not message.text.isdigit():
        await message.answer(
            f"Please enter correct number !", reply_markup=back_to_admin_panel
        )
    else:
        subtract_amount = int(message.text.strip())
        if subtract_amount <= 0:
            await message.answer(
                "❌ The amount must be greater than 0.",
                reply_markup=change_users_balance,
            )
            await state.clear()
            return
        conn = sqlite3.connect("users_database.db")
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users_database SET unity_coin = unity_coin - ? WHERE user_id = ? or nfgame = ?",
            (subtract_amount, username, username),
        )
        conn.commit()
        conn.close()

        await message.answer(
            f"✅ {subtract_amount} Unity Coins have been subtracted from the user's balance!",
            reply_markup=change_users_balance,
        )
        await state.clear()


@dp.message(F.text == "/stop_all_incomplete_games")
@admin_required()
async def stop_all_incomplete_games_command(message: types.Message, state: FSMContext):
    users = get_all_user_ids()

    for userid in users:
        try:
            delete_user_from_all_games(userid)
        except:
            continue
    await message.answer(f"All users' incomplete games has been stopped ✅")


@dp.message(F.text == "💰 withdraw change")
@admin_required()
async def show_withdraw_options(message: types.Message):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM withdraw_options LIMIT 1")
    withdraw_options = cursor.fetchone()
    if not withdraw_options:
        await message.answer("❌ No withdrawal options found.")
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
    conn.close()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"❄️ 3 Months", callback_data="change_3_month"
                ),
                InlineKeyboardButton(
                    text=f"⭐ 100 Stars", callback_data="change_100_stars"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"❄️ 6 Months", callback_data="change_6_month"
                ),
                InlineKeyboardButton(
                    text=f"⭐ 500 Stars", callback_data="change_500_stars"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"❄️ 12 Months", callback_data="change_12_month"
                ),
                InlineKeyboardButton(
                    text=f"⭐ 1,000 Stars", callback_data="change_1000_stars"
                ),
            ],
        ]
    )
    withdraw_message = (
        "💰 *Withdrawal change section.*\n\n"
        f"🚀 *Telegram Premium*\n"
        f"❄️ *3 Months*: {three_month_premium} Unity Coins 💰\n"
        f"❄️ *6 Months*: {six_month_premium} Unity Coins 💰\n"
        f"❄️ *12 Months*: {twelve_month_premium} Unity Coins 💰\n\n"
        f"⭐️ *Telegram Stars* \n"
        f"✨ *100 Stars*: {hundrad_stars} Unity Coins 💰\n"
        f"✨ *500 Stars*: {five_hundrad_stars} Unity Coins 💰\n"
        f"✨ *1,000 Stars*: {thousand_stars} Unity Coins 💰\n\n"
        "Press a button to change the Unity Coins for each option 👇"
    )
    await message.answer(withdraw_message, parse_mode="Markdown", reply_markup=keyboard)


@dp.callback_query(lambda c: c.data.startswith("change_"))
async def change_withdraw_option(
    callback_query: types.CallbackQuery, state: FSMContext
):
    option = callback_query.data
    await callback_query.message.answer(
        f"💬 Please enter the new Unity Coins amount for {option.replace('change_', '').replace('_', ' ').title()}:",
        reply_markup=back_to_admin_panel,
    )
    await state.set_data({"option": option})
    await state.set_state(changeWithdraw.changee)


@dp.message(changeWithdraw.changee)
async def set_new_coin_amount(message: types.Message, state: FSMContext):
    if message.text == "back to admin panel 🔙":
        await message.answer(
            "You are in admin panel 👇", reply_markup=admin_panel_button
        )
        await state.clear()
        return
    new_coin_amount = message.text.strip()
    if not new_coin_amount.isdigit():
        await message.answer(
            "❌ Please enter a valid number for the Unity Coins amount."
        )
        return
    new_coin_amount = int(new_coin_amount)
    data = await state.get_data()
    if not data:
        return
    option = data.get("option")
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        conn = sqlite3.connect("users_database.db")
        cursor = conn.cursor()

        if option == "change_3_month":
            cursor.execute(
                "UPDATE withdraw_options SET three_month_premium = ? WHERE rowid = 1",
                (new_coin_amount,),
            )
        elif option == "change_6_month":
            cursor.execute(
                "UPDATE withdraw_options SET six_month_premium = ? WHERE rowid = 1",
                (new_coin_amount,),
            )
        elif option == "change_12_month":
            cursor.execute(
                "UPDATE withdraw_options SET twelve_month_premium = ? WHERE rowid = 1",
                (new_coin_amount,),
            )
        elif option == "change_100_stars":
            cursor.execute(
                "UPDATE withdraw_options SET hundrad_stars = ? WHERE rowid = 1",
                (new_coin_amount,),
            )
        elif option == "change_500_stars":
            cursor.execute(
                "UPDATE withdraw_options SET five_hundrad_stars = ? WHERE rowid = 1",
                (new_coin_amount,),
            )
        elif option == "change_1000_stars":
            cursor.execute(
                "UPDATE withdraw_options SET thousand_stars = ? WHERE rowid = 1",
                (new_coin_amount,),
            )

        conn.commit()
        conn.close()
        await message.answer(
            f"✅ The Unity Coins amount for {option.replace('change_', '').replace('_', ' ').title()} has been updated to {new_coin_amount} coins.",
            reply_markup=admin_panel_button,
        )
    except sqlite3.Error as e:
        await message.answer(f"❌ There was an error while updating the database: {e}")

    finally:
        await state.clear()


@dp.callback_query(lambda c: c.data.startswith("get_"))
async def process_withdraw_user(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    option = callback_query.data
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
    conn.close()
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT unity_coin FROM users_database WHERE user_id = ?", (user_id,)
    )
    user_info = cursor.fetchone()

    if not user_info:
        await callback_query.answer("❌ You are not registered in the system.")
        conn.close()
        return

    user_unity_coins = user_info[0]
    cost = 0
    reward_name = ""

    if option == "get_3_month":
        cost = int(three_month_premium)
        reward_name = "🚀 3 Months Telegram Premium"
    elif option == "get_6_month":
        cost = int(six_month_premium)
        reward_name = "🚀 6 Months Telegram Premium"
    elif option == "get_12_month":
        cost = int(twelve_month_premium)
        reward_name = "🚀 12 Months Telegram Premium"
    elif option == "get_100_stars":
        cost = int(hundrad_stars)
        reward_name = "⭐️ 100 Stars"
    elif option == "get_500_stars":
        cost = int(five_hundrad_stars)
        reward_name = "⭐️ 500 Stars"
    elif option == "get_1000_stars":
        cost = int(thousand_stars)
        reward_name = "⭐️ 1,000 Stars"
    if user_unity_coins < cost:
        await callback_query.answer(
            f"❌ You need {cost - user_unity_coins} more Unity Coins to get this item.",
            show_alert=True,
        )
        return

    await callback_query.message.answer(
        f"💬 You selected - {reward_name}! \nPlease provide any Telegram username that you want to get item to:\n\n❗️Note that if the username you entered is incorrect, your reward won't be given."
    )
    await state.set_data({"reward_name": reward_name, "cost": cost})
    await state.set_state(waiting_for_username_withdraw.username_withdraw)


@dp.message(waiting_for_username_withdraw.username_withdraw)
async def get_username_for_withdraw(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.text.strip()
    state_data = await state.get_data()
    reward_name = state_data["reward_name"]
    cost = state_data["cost"]
    confirmation_message = (
        f"💬 Please confirm your withdrawal details:\n\n"
        f"🎁 *Item Name*: {reward_name}\n"
        f"👤 *To Who*: {username}\n"
        f"💰 *Cost*: {cost} Unity Coins\n\n"
        "Do you confirm?"
    )
    await state.clear()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Yes", callback_data="confirm_withdraw"),
            ],
            [
                InlineKeyboardButton(text="❌ No", callback_data="cancel_withdraw"),
            ],
        ]
    )

    await message.answer(
        confirmation_message, parse_mode="Markdown", reply_markup=keyboard
    )
    await state.set_data({"reward_name": reward_name, "cost": cost})
    await state.update_data(username=username)


@dp.callback_query(lambda c: c.data == "confirm_withdraw")
async def confirm_withdraw_queer(
    callback_query: types.CallbackQuery, state: FSMContext
):
    await bot.delete_message(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
    )
    user_id = callback_query.from_user.id
    state_data = await state.get_data()

    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT unity_coin FROM users_database WHERE user_id = ?", (user_id,)
    )
    user_info = cursor.fetchone()
    balance = user_info[0]
    conn.close()
    reward_name = state_data.get("reward_name")
    username = state_data.get("username")
    cost = state_data.get("cost")
    admin_channel_id = -1002261491678
    admin_message = (
        f"🛒 *New Withdrawal Request*\n\n"
        f"🎁 *Item*: {reward_name}\n"
        f"👤 *To Who*: {username}\n"
        f"💰 *Cost*: {cost} Unity Coins\n"
        f"🔢 *User ID*: {user_id}\n"
        f"💸 *User's balance: {balance} Unity coins 💰 *"
    )
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT unity_coin FROM users_database WHERE user_id = ?", (user_id,)
    )
    user_info = cursor.fetchone()
    user_unity_coins = user_info[0]
    new_balance = user_unity_coins - cost
    cursor.execute(
        "UPDATE users_database SET unity_coin = ? WHERE user_id = ?",
        (new_balance, user_id),
    )
    conn.commit()
    conn.close()
    await bot.send_message(
        admin_channel_id,
        admin_message,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Confirm", callback_data=f"admin_confirm_{user_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Cancel", callback_data=f"admin_cancel_{user_id}"
                    )
                ],
            ]
        ),
        parse_mode="Markdown",
    )

    await callback_query.message.answer(
        "✅ Your withdrawal request has been submitted to our admins.\nIt will be processed within 24 hours."
    )
    await state.clear()


@dp.callback_query(lambda c: c.data.startswith("admin_confirm_"))
async def admin_confirm_withdraw(callback_query: types.CallbackQuery):
    await bot.delete_message(
        chat_id=-1002261491678, message_id=callback_query.message.message_id
    )
    user_id = callback_query.data.split("_")[-1]
    await bot.send_message(
        user_id,
        "✅ Your withdrawal request has been confirmed! The item has been successfully delivered to the user you selected.",
    )
    await callback_query.answer("✅ Withdrawal confirmed!")


@dp.callback_query(lambda c: c.data.startswith("admin_cancel_"))
async def admin_cancel_withdraw(callback_query: types.CallbackQuery):
    await bot.delete_message(
        chat_id=-1002261491678, message_id=callback_query.message.message_id
    )

    user_id = callback_query.data.split("_")[-1]
    await bot.send_message(user_id, "❌ Your withdrawal request was canceled.")
    await callback_query.answer("❌ Withdrawal canceled.")


@dp.callback_query(lambda c: c.data == "cancel_withdraw")
async def cancel_withdraw_queer(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.delete_message(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
    )
    await callback_query.message.answer(f"You have canceled your order successfully ✅")
    await state.clear()


@dp.message(F.text == "👀 watch results")
@admin_required()
async def watch_results_f(message: types.Message):
    result = ""
    tournament = get_ongoing_tournaments()
    if not tournament:
        await message.answer(
            f"Tournamnet has already been finished.",
            reply_markup=tournaments_admin_panel_button,
        )
        return
    tournament_id = tournament[0]["name"]
    current_round = int(get_current_round_number(tournament_id))
    if current_round == 0:
        for i in range(1, current_round + 1):
            result += get_round_results(tournament_id, i) + "\n"
        if not result:
            result = "No results yet."
        await message.answer(result)
    else:
        await message.answer(
            f"Tournament has already finished. You can see the results in an archive 📈",
            reply_markup=tournaments_admin_panel_button,
        )


@dp.message(F.text == "👨‍👩‍👦‍👦 refferals")
@admin_required()
async def referrals_section(message: types.Message):
    await message.answer(
        f"You are in referrals section 👇", reply_markup=referrals_section_buttons
    )


@dp.message(F.text == "🔝 Top referrals")
@admin_required()
async def referrals_top_referrals(message: types.Message):
    await message.answer(
        f"{get_top_referrals()}", reply_markup=referrals_section_buttons
    )


@dp.message(F.text == "🔄 change referral amount")
@admin_required()
async def change_referrals_t(message: types.Message, state: FSMContext):
    await message.answer(
        f"Current referral amount is {get_unity_coin_referral()} Unity Coins 💰\nWrite the new amount for referral ✍️:",
        reply_markup=back_to_admin_panel,
    )
    await state.set_state(waitforreferralamount.amount)


@dp.message(waitforreferralamount.amount)
async def change_referrals_state(message: types.Message, state: FSMContext):
    new_amount = message.text
    if not new_amount.isdigit():
        await message.answer(
            f"You entered wrong amount ‼️. Please, enter a valid number.",
            reply_markup=back_to_admin_panel,
        )
    elif int(new_amount) < 0:
        await message.answer(
            f"You can't enter negative numbers ‼️. Please, enter a valid intager.",
            reply_markup=back_to_admin_panel,
        )
    else:
        update_unity_coin_referral(int(new_amount))
        await message.answer(
            f"New referral amount is successfully set ✅",
            reply_markup=referrals_section_buttons,
        )


@dp.message(F.text == "⛹️ players")
@admin_required()
async def players_in_tournament(message: types.Message):
    tournament = get_ongoing_tournaments()
    if not tournament:
        await message.answer(f"No ongoing tournaments found or has already been finished.", reply_markup=tournaments_admin_panel_button)
        return
    tournament_id = tournament[0]["name"]
    players = get_tournament_users_list(tournament_id)
    if not players:
        await message.answer("No players have joined the tournament yet.")
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for player_id in players:
        keyboard.inline_keyboard.append(
            [
                InlineKeyboardButton(
                    f"🧑 Player {get_user_nfgame(player_id)}", callback_data=f"remove_{player_id}"
                )
            ]
        )

    await message.answer(
        "Here is the list of players in the tournament:", reply_markup=keyboard
    )

