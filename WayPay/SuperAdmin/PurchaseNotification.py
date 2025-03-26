from Config import bot, DB, dp
from Keyboards.SuperAdmin import conf_payment_kb
from aiogram.types import CallbackQuery
from HelloMessages.Client import thank_you
from Client.HelpFunctions import save_order
from .BLRequest import get_admins
from LicenseKey import workplaces_keys
from aiogram.utils.exceptions import ChatNotFound

messages_ids = {}
order_info = {}
conf_info = {}
payment_id = 1


async def get_user_info(user_id):
    async with DB() as conn:
        full_name = await conn.fetchval('SELECT full_name FROM client WHERE ID = $1', user_id)
        contact = await conn.fetchval('SELECT contact FROM client WHERE ID = $1', user_id)
    return full_name, contact


async def purchase_notification(user_id, term, month_word, workplace, price):
    global payment_id
    full_name, contact = await get_user_info(user_id)
    kb = await conf_payment_kb(user_id, payment_id)
    text = (f"Пользователь {full_name} с ID {user_id} оплатил лицензию\n\n"
            f"*Срок:* {term} {month_word}\n"
            f"*Количество рабочих мест:* {workplace}\n"
            f"*Сумма:* {price}\n\n")

    if contact == '-':
        text += "У этого человека нет юзернейма"
        conf_info[user_id] = (full_name, None)
    else:
        new_contact = contact.replace('_', r'\_')
        text += f"Связаться с ним можно по {new_contact}"
        conf_info[user_id] = (full_name, contact)

    admin_ids = await get_admins()

    for admin_id in admin_ids:
        try:
            message = await bot.send_message(admin_id, text, 'Markdown', reply_markup=kb)
        except ChatNotFound:
            continue
        else:
            message_id = message.message_id
            messages_ids.setdefault(admin_id, []).append((payment_id, message_id))

    payment_id += 1
    order_info[user_id] = (term, month_word, workplace, price)


async def get_common_data(call):
    admin_id = call.from_user.id
    user_id = int(call.data.split(':')[0])
    choice = call.data.split(':')[2]
    current_payment = int(call.data.split(':')[1])
    term, month_word, workplace, price = order_info[user_id]
    return admin_id, user_id, choice, current_payment, term, month_word, price, workplace


async def handle_conf_payment(admin_id, user_id, current_payment, term, month_word, workplace, price, action, keys=None):
    if action == 'conf':
        action_msg = 'подтверждена'
        await save_order(user_id, term, workplace, price, keys)
        await thank_you(user_id, term, month_word, workplace, keys)
    elif action == 'no_conf':
        action_msg = 'октлонена'
        await bot.send_message(user_id, "Ваша лицензия была отклонена администратором")


    full_name, contact = await get_user_info(user_id)

    header = f"Лицензия {action_msg}"
    add_header = " другим администратором"
    body = (f"\n*Цена:* {price} рублей\n"
            f"*ФИО:* {full_name}\n")

    if contact == '-':
        body += "У этого пользователя нет юзернейма"
    else:
        new_contact = contact.replace('_', r'\_')
        body += f"*Юзернейм:* {new_contact}"

    text1 = header + body
    text2 = header + add_header + body

    for admin_chat, messages in messages_ids.items():
        for payment, message_id in messages:
            if payment == current_payment:
                if admin_chat == admin_id:
                    await bot.edit_message_text(text1, admin_id, message_id, parse_mode='Markdown', reply_markup=None)
                else:
                    await bot.edit_message_text(text2, admin_chat, message_id, parse_mode='Markdown', reply_markup=None)


@dp.callback_query_handler(lambda call: call.data.endswith('payment'), state="*")
async def confirmation_handler(call: CallbackQuery):
    admin_id, user_id, choice, current_payment, term, month_word, price, workplace = await get_common_data(call)

    if choice == "conf_payment":
        keys = await workplaces_keys(workplace)
        await handle_conf_payment(admin_id, user_id, current_payment, term, month_word, workplace, price, 'conf', keys)

    elif choice == "no_conf_payment":
        await handle_conf_payment(admin_id, user_id, current_payment, term, month_word, workplace, price, 'no_conf', None)
