import asyncio
import logging

from config import *

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("hello")


@dp.message()
async def any_word(msg: types.message):
    await msg.answer(f"Siz noto'g'ri buyruq yubordingiz !")
    
async def main():
    await bot.delete_webhook(drop_pending_updates=True) 
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())