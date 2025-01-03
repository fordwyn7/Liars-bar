from aiogram import Bot, Dispatcher, F
from aiogram.fsm.storage.memory import MemoryStorage

import os
from dotenv import load_dotenv
load_dotenv()

bot = Bot(token="7848961116:AAFJgEs2Gq3xDAQlgCYyz4uSQsX9r3D7vCY")
dp = Dispatcher(storage=MemoryStorage())
from middlewares.registered import RegistrationMiddleware

dp.update.middleware(RegistrationMiddleware())