import sqlite3
from aiogram import types
from aiogram.fsm.context import FSMContext
from middlewares.registered import admin_required
from keyboards.keyboard import *
from config import *
from db import *
# from middlewares.registered import get_admins
from states.state import *
def generate_callback(action: str, admin_id: int) -> str:
    return f"{action}:{admin_id}"

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
    elif not is_user_registered(message.from_user.id):
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
            await state.clear()
        except ValueError:
            await message.answer(
                "❌ You entered wrong information. Please try again.",
                reply_markup=back_button,
            )












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
