import asyncio
import logging

from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from states.state import STATE_NAME
from keyboards.keyboard import KEYBOAR_NAME

bot = Bot(token="YOUR_TOKEN")

dispatcher = Dispatcher()
dp = Router()
dispatcher.include_router(dp)

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("hello")


@dp.message()
async def any_word(msg: types.message):
    await msg.answer(f"Siz noto'g'ri buyruq yubordingiz !")
    
async def main():
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())