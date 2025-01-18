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


USERS_PER_PAGE = 10


def generate_user_list(users, page):
    start_index = (page - 1) * USERS_PER_PAGE
    end_index = start_index + USERS_PER_PAGE
    page_users = users[start_index:end_index]

    user_list = []
    for index, (user_id, phone) in enumerate(page_users, start=start_index + 1):
        user_list.append(f"{index}. <a href='tg://user?id={user_id}'>{user_id}</a>")

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
            SELECT username, first_name, last_name, registration_date, nfgame 
            FROM users_database WHERE user_id = ?
            """,
            (user_id,),
        )
        user_data = cursor.fetchone()
        if not user_data:
            return "❌ No user found with the given ID."
        username, first_name, last_name, registration_date, nfgame = user_data
        is_admin = "admin 🧑‍💻" if is_user_admin(user_id) else "user 🙍‍♂️"

        stats_message = (
            f"📊 **User Statistics** 📊\n\n"
            f"🙇‍♂️ **Role**: {is_admin} \n\n"
            f"👤 **Username**: {"@" + username if username else 'N/A'}\n\n"
            f"📛 **First Name**: {first_name if first_name else 'N/A'}\n\n"
            f"📜 **Last Name**: {last_name if last_name else 'N/A'}\n\n"
            f"🗓️ **Registr Date**: {registration_date if registration_date else 'N/A'}\n\n"
            f"🎮 **Name in bot**: {nfgame if nfgame else 'N/A'}\n"
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
            cursor.execute("SELECT user_id, phone FROM users")
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
        with sqlite3.connect("users.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, phone FROM users")
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
        f"Enter the ID of user that you want to get information", reply_markup=back_button
    )
    await state.set_state(UserInformations.userid_state)


@dp.message(UserInformations.userid_state)
@admin_required()
async def state_info_users(message: types.Message, state: FSMContext):
    user_id = message.text
    if not user_id.isdigit():
        await message.answer(
            "You entered wrong information! Please try again."
        )
    else:
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
