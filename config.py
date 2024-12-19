from aiogram import Bot, Dispatcher, F
from aiogram.fsm.storage.memory import MemoryStorage

import os
from dotenv import load_dotenv
load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher(storage=MemoryStorage())
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 5000)) 
from middlewares.registered import RegistrationMiddleware

dp.update.middleware(RegistrationMiddleware())