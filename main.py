import os
import sys
import json
import asyncio
from datetime import datetime
from json_io import read, write
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram import Bot, Dispatcher, types, filters, F, Router


# Забираем конфиг из файла
config = read('config.json')
bot_id = config['alert_bot_id']
user_id = config['alert_user_id']

# Создаём диспатчер
dp = Dispatcher()

# Создаём роутер
router = Router()

# Инициализируем ботов из файла
def create_bots():
    bots = {}
    tokens = read('bots.json')
    for data in tokens:
        if data['enable'] == 'True':
            token = data['api_key']
            bot = Bot(token)
            preaprove_msg = data['preaprove_msg']
            button_msg = data['button_msg']
            aprove_msg = data['aprove_msg']
            bots[bot.id] = {
                "bot": bot,
                "preaprove_msg": preaprove_msg,
                "button_msg": button_msg,
                "aprove_msg": aprove_msg
            }
    return bots

# Получаем словарь с ботами
bots = create_bots()

# Стартуем всех ботов
async def start_bots():
    print(f"[INFO]: Bots started!")
    bot = bots[bot_id]['bot']
    await bot.send_message(chat_id=user_id, text="[INFO]: Bots started!")
    bot_list = [data['bot'] for data in bots.values()]
    dp.include_router(router)
    await dp.start_polling(*bot_list)

# Ответ на стартовое сообщение 
@dp.message(filters.CommandStart())
async def command_start_handler(message: types.Message) -> None:
    if message.bot.id != bot_id:
        bot_data = bots[message.bot.id]
        preaprove_msg = bot_data['preaprove_msg']
        button_msg = bot_data['button_msg']
        await message.answer(text=preaprove_msg,
                        reply_markup=types.ReplyKeyboardMarkup(
                            keyboard=[[types.KeyboardButton(text=button_msg, request_contact=True)]],
                            resize_keyboard=True
                        ))

# Обрабатываем получение контакта
@dp.message(F.contact)
async def contact_handler(message: types.Message):
    if message.bot.id != bot_id:
        userId = message.from_user.id
        name = message.from_user.first_name
        botName = (await message.bot.get_me()).username
        if message.from_user.username:
            username = '@' + message.from_user.username
        else:
            username = 'Нет имени пользователя'
        phone_number = message.contact.phone_number
        sending = f'Получен номер телефона: id{userId}, {name}, {username}, {phone_number}, от бота {botName}.'
        bot_data = bots[message.bot.id]
        aprove_msg = bot_data['aprove_msg']
        await message.answer(text=aprove_msg, reply_markup=types.ReplyKeyboardRemove())
        bot = bots[bot_id]['bot']
        await bot.send_message(chat_id=user_id, text=sending)
        timestamp = datetime.now().strftime("%d.%m.%Y.%H.%M")
        log = f'{timestamp}:id{userId}:{username}:{phone_number}\n'
        with open('numbers.txt', 'a') as f:
            f.write(log)

# Кнопки управления по команде
@dp.message(F.text.lower() == 'бот')
async def bot_buttons(message: types.Message):
    await message.answer(text='Меню бота', reply_markup=types.ReplyKeyboardMarkup(
                                keyboard=[
                                    [
                                        types.KeyboardButton(text="/add"),
                                        types.KeyboardButton(text="/edit"),
                                        types.KeyboardButton(text="/delete"),
                                        types.KeyboardButton(text="/cancel"),   
                                    ]
                                ],
                                resize_keyboard=True
                             ))   

# Создаём форму для добавления бота в пул
class Form(StatesGroup):
    name = State()
    api_key = State()
    preaprove_msg = State()
    button_msg = State()
    aprove_msg = State()
    enable = State()

# Команда прерывания ввода
@router.message(F.text == '/cancel')
async def add_bot(message: types.Message, state: FSMContext):
    if (message.bot.id == bot_id) and (message.chat.id == user_id):
        current_state = await state.get_state()
        if current_state is None:
            return
        await state.clear()
        await message.answer("Ввод прерван.")    


# Добавление бота в пул
@router.message(F.text == '/add')
async def add_bot(message: types.Message, state: FSMContext):
    if (message.bot.id == bot_id) and (message.chat.id == user_id):
        await state.set_state(Form.name)
        await message.answer("Введите название бота:")

@router.message(Form.name)
async def process_name(message: types.Message, state: FSMContext):
    if (message.bot.id == bot_id) and (message.chat.id == user_id):
        await state.update_data(name=message.text)
        await state.set_state(Form.api_key)
        await message.answer("Введите API-ключ бота:")

@router.message(Form.api_key)
async def process_api_key(message: types.Message, state: FSMContext):
    if (message.bot.id == bot_id) and (message.chat.id == user_id):
        await state.update_data(api_key=message.text)
        await state.set_state(Form.preaprove_msg)
        await message.answer("Введите первое сообщение:")

@router.message(Form.preaprove_msg)
async def process_api_key(message: types.Message, state: FSMContext):
    if (message.bot.id == bot_id) and (message.chat.id == user_id):
        await state.update_data(preaprove_msg=message.text)
        await state.set_state(Form.button_msg)
        await message.answer("Введите текст на кнопке получения номера:")

@router.message(Form.button_msg)
async def process_api_key(message: types.Message, state: FSMContext):
    if (message.bot.id == bot_id) and (message.chat.id == user_id):
        await state.update_data(button_msg=message.text)
        await state.set_state(Form.aprove_msg)
        await message.answer("Введите текст после получения номера:")

@router.message(Form.aprove_msg)
async def process_api_key(message: types.Message, state: FSMContext):
    if (message.bot.id == bot_id) and (message.chat.id == user_id):
        await state.update_data(aprove_msg=message.text)
        await state.set_state(Form.enable)
        await message.answer(text="Выберите будет ли активен бот.",
                             reply_markup=types.ReplyKeyboardMarkup(
                                keyboard=[
                                    [
                                        types.KeyboardButton(text="True"),
                                        types.KeyboardButton(text="False"),   
                                    ]
                                ],
                                resize_keyboard=True
                             ))
        
@router.message(Form.enable)
async def process_api_key(message: types.Message, state: FSMContext):
    if (message.bot.id == bot_id) and (message.chat.id == user_id):
        await state.update_data(enable=message.text)
        await message.answer("Данные успешно заполнены.", reply_markup=types.ReplyKeyboardRemove())
        data = await state.get_data()
        write('bots.json', data)
        await state.clear()
        await message.answer("[INFO]: Bots reloaded!")
        os.execl(sys.executable, sys.executable, *sys.argv)


# Удаление бота из пула
@dp.message(F.text == '/delete')
async def delete_bot(message: types.Message):
    if (message.bot.id == bot_id) and (message.chat.id == user_id):
        bots = read('bots.json')
        if len(bots) <= 1:
            await message.answer("Нет доступных для удаления ботов.")
            return    
        keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[] 
        )
        for bot in bots:
            if int(bot['api_key'].split(':')[0]) == bot_id:
                continue
            keyboard.keyboard.append([types.KeyboardButton(text=f"Удалить {bot['name']}")])
        keyboard.keyboard.append([types.KeyboardButton(text="Отмена удаления")])
        await message.reply("Выберите бота для удаления:", reply_markup=keyboard)

@dp.message(F.text == 'Отмена удаления')
async def cancel_delete(message: types.Message):
    if (message.bot.id == bot_id) and (message.chat.id == user_id):
        await message.answer("Удаление отменено.", reply_markup=types.ReplyKeyboardRemove())

@dp.message(F.text.startswith('Удалить'))
async def delete_process(message: types.Message):
    if (message.bot.id == bot_id) and (message.chat.id == user_id):
        bot_name = message.text.split()[1]
        bots = read('bots.json')
        for bot in bots:
            if bot['name'] == bot_name:
              bots.remove(bot)
              break
        with open('bots.json', 'w', encoding='utf-8') as f:
            json.dump(bots, f, indent=4, ensure_ascii=False)
        await message.answer("Бот успешно удалён.", reply_markup=types.ReplyKeyboardRemove())
        await message.answer("[INFO]: Bots reloaded!")
        os.execl(sys.executable, sys.executable, *sys.argv)


# Редактирование ботов
class Edit(StatesGroup):
    name = State()
    field = State()
    new_value = State()        

@router.message(F.text == '/edit')
async def edit_bot(message: types.Message, state: FSMContext):
    if (message.bot.id == bot_id) and (message.chat.id == user_id):
        bots = read('bots.json')
        if len(bots) <= 1:
            await message.answer("Нет доступных для редактирования ботов.")
            return
        keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[] 
        )
        for bot in bots:
            if int(bot['api_key'].split(':')[0]) == bot_id:
                continue
            keyboard.keyboard.append([types.KeyboardButton(text=f"{bot['name']}")])
        keyboard.keyboard.append([types.KeyboardButton(text="Отмена изменения")])
        await state.clear()
        await state.set_state(Edit.name)
        await message.reply("Выберите бота для изменения:", reply_markup=keyboard)

@router.message(F.text == 'Отмена изменения')
async def cancel_edit(message: types.Message, state: FSMContext):
    if (message.bot.id == bot_id) and (message.chat.id == user_id):
        await message.answer("Изменение отменено.", reply_markup=types.ReplyKeyboardRemove())

@router.message(Edit.name)
async def edit_process(message: types.Message, state: FSMContext):
    if (message.bot.id == bot_id) and (message.chat.id == user_id):
        bot_name = message.text
        await state.update_data(name=bot_name)
        bots = read('bots.json')
        for bot in bots:
            if bot['name'] == bot_name:
              selected_bot = bot
              break
        keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[] 
        )
        for field in selected_bot:
            keyboard.keyboard.append([types.KeyboardButton(text=f"{field}")])
        keyboard.keyboard.append([types.KeyboardButton(text="Отмена изменения")])
        await message.reply("Выберите поле для изменения:", reply_markup=keyboard)
        await state.set_state(Edit.field)

@router.message(Edit.field)
async def edit_field(message: types.Message, state: FSMContext):
    if (message.bot.id == bot_id) and (message.chat.id == user_id):
        field_name = message.text
        await state.update_data(field=field_name)
        await message.reply(f"Введите новое значение для {field_name}", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(Edit.new_value)

@router.message(Edit.new_value)
async def edit_field(message: types.Message, state: FSMContext):
    if (message.bot.id == bot_id) and (message.chat.id == user_id):
        await state.update_data(new_value=message.text)
        data = await state.get_data()
        await state.clear()
        bots = read('bots.json')
        for bot in bots:
            if bot['name'] == data['name']:
                bot[data['field']] = data['new_value']
                break
        with open('bots.json', 'w', encoding='utf-8') as f:
            json.dump(bots, f, indent=4, ensure_ascii=False)
        await message.answer("Бот успешно изменён.", reply_markup=types.ReplyKeyboardRemove())
        await message.answer("[INFO]: Bots reloaded!")
        os.execl(sys.executable, sys.executable, *sys.argv)     


if __name__ == '__main__':
    asyncio.run(start_bots())