from aiogram import Bot, Dispatcher, F
from aiogram.fsm.storage.memory import MemoryStorage

bot = Bot(token="7952533006:AAEWbC0VNlxXAqnNPU_oiHeGOq4XDyKZQEk")
dp = Dispatcher(storage=MemoryStorage())
from middlewares.registered import RegistrationMiddleware

dp.update.middleware(RegistrationMiddleware())