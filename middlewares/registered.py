from aiogram.types import Update
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from db import is_user_registered

from aiogram.fsm.context import FSMContext

class RegistrationMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Update, data: dict):
        user_id = None
        state: FSMContext = data.get("state")
        current_state = await state.get_state() if state else None

        if event.message:
            user_id = event.message.from_user.id
            command = event.message.text.strip().lower() if event.message.text else None
            if command == "/start" or "?start=game_" in command:
                return await handler(event, data)

        elif event.callback_query:
            user_id = event.callback_query.from_user.id

        if user_id:
            registered = is_user_registered(user_id)
            if not registered and current_state != "registration:pref_name" and current_state != "registration_game:pref1_name":
                if event.message:
                    await event.message.answer("Please register first by sending /start.")
                elif event.callback_query:
                    await event.callback_query.answer(
                        "Please register first by sending /start.", show_alert=True
                    )
                return
        return await handler(event, data)
