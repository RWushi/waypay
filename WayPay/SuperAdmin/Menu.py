from aiogram.types import Message, InputFile
from Config import bot, dp, UserState
from HelloMessages.SuperAdmin import admin, black_list
from .Statistics import get_file
from datetime import datetime, timezone
from SuperAdmin.Add_Delete import check_role


@dp.message_handler(state=UserState.menu)
async def menu_handler(message: Message):
    chat_id = message.chat.id
    role = await check_role(chat_id)
    if role == 'superadmin':
        if message.text == "⛔ Черный список":
            await black_list(chat_id)

        elif message.text == "🧑‍💻 Администраторы":
            await admin(chat_id)

        elif message.text == "📊 Статистика":
            await message.answer("Ваш файл готовится...")
            file = await get_file()
            current_date_utc = datetime.now(timezone.utc).date()
            formatted_date = current_date_utc.strftime("%d.%m.%Y")
            filename = f"{formatted_date} WayPay статистика по пользователям.xlsx"
            file_input = InputFile(file, filename=filename)
            await bot.send_document(chat_id, file_input)

    else:
        await message.answer("У Вас недостаточно прав")


import SuperAdmin.Admin, SuperAdmin.BlackList
