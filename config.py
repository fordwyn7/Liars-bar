from aiogram import Bot, Dispatcher, F
from aiogram.fsm.storage.memory import MemoryStorage

bot = Bot(token="7952533006:AAEWbC0VNlxXAqnNPU_oiHeGOq4XDyKZQEk")
dp = Dispatcher(storage=MemoryStorage())
from middlewares.registered import RegistrationMiddleware

dp.update.middleware(RegistrationMiddleware())
import sqlite3
def is_user_admin(user_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None