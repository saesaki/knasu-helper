import requests
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, Router, types
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, BotCommand, BotCommandScopeDefault
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
import logging


BOT_TOKEN = '7908948704:AAHygKjTMkKHN_KqkrC9lfxwWLW_mVAkWLM'


#Инициализация бота
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()

#URL КнАГУ
BASE_URL = "https://www.knastu.ru"

#Загрузка страницы
def fetch_page(url: str):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logging.error(f"Ошибка при получении данных: {e}")
        return None

#Парсинг расписания указанной группы
def get_schedule_for_group(group_name: str):
    url = "https://www.knastu.ru/students/schedule"
    page_content = fetch_page(url)
    if not page_content:
        return "Не удалось получить данные о расписании."

    soup = BeautifulSoup(page_content, "html.parser")

    #Найти расписание для группы по названию
    group_schedule = None
    for item in soup.find_all("a", href=True):
        if group_name.lower() in item.text.lower():
            group_schedule = item["href"]
            break

    if not group_schedule:
        return "Расписание для данной группы не найдено."

    return f"Ссылка на расписание группы {group_name}: {BASE_URL}{group_schedule}"

#Парсинг расписания преподавателя
def get_teacher_schedule(teacher_name: str):
    url = "https://www.knastu.ru/teachers/schedule"
    page_content = fetch_page(url)
    if not page_content:
        return "Не удалось получить данные о расписании."

    soup = BeautifulSoup(page_content, "html.parser")

    #Найти расписание преподавателя
    teacher_schedule = None
    for item in soup.find_all("a", href=True):
        if teacher_name.lower() in item.text.lower():
            teacher_schedule = item["href"]
            break

    if not teacher_schedule:
        return "Расписание для данного преподавателя не найдено."

    return f"Ссылка на расписание преподавателя {teacher_name}: {BASE_URL}{teacher_schedule}"

#Расписание звонков
def get_bell_schedule_link():
    return ("Расписание звонков:\n1) 8:10 – 9:40\n2) 9:50 – 11:20\n3) 11:30 – 13:00\n4) 13:30 – 15:00\n5) 15:10 – 16:40\n6) 16:50 – 18:20\n7) 18:30 – 20:00\n8) 20:10 – 21:40")

#Клавиатура главная
main_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Расписание группы")],
    [KeyboardButton(text="Расписание преподавателя")],
    [KeyboardButton(text="Расписание звонков")],
    [KeyboardButton(text="Общая информация")],
    [KeyboardButton(text="Сайт КнАГУ")]
], resize_keyboard=True)

#Клавиатура для общей информации
info_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Личный кабинет")],
    [KeyboardButton(text="Ресурсы")],
    [KeyboardButton(text="Учёба")],
    [KeyboardButton(text="Назад в меню")]
], resize_keyboard=True)

#Клавиатура для ресурсов
resources_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Библиотека")],
    [KeyboardButton(text="Электронные образовательные ресурсы")],
    [KeyboardButton(text="Интернет-ресурсы")],
    [KeyboardButton(text="Методические материалы")],
    [KeyboardButton(text="Календарные учебные графики")],
    [KeyboardButton(text="Назад в меню")]
], resize_keyboard=True)

navigation_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Назад в меню")]
], resize_keyboard=True)

class Form(StatesGroup):
    waiting_for_group_name = State()
    waiting_for_teacher_name = State()

#Подсказка для команд
async def set_default_commands():
    commands = [
        BotCommand(command="start", description="Старт бота")
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())

#Хэндлер для команды /start
@router.message(Command("start"))
async def start_command(message: Message):
    await message.answer(
        "Привет! Выберите, что вы хотите узнать:",
        reply_markup=main_keyboard
    )

#Хэндлер для кнопки "Расписание группы"
@router.message(lambda message: message.text == "Расписание группы")
async def group_schedule_handler(message: Message, state: FSMContext):
    await message.answer("Введите название группы:", reply_markup=navigation_keyboard)
    await state.set_state(Form.waiting_for_group_name)

@router.message(Form.waiting_for_group_name)
async def group_name_handler(message: Message, state: FSMContext):
    if message.text == "Главное меню":
        await state.clear()
        await start_command(message)
        return

    group_name = message.text
    schedule = get_schedule_for_group(group_name)
    await message.answer(f"Расписание для группы {group_name}\n{schedule}", reply_markup=main_keyboard)
    await state.clear()

#Хэндлер для кнопки "Расписание преподавателя"
@router.message(lambda message: message.text == "Расписание преподавателя")
async def teacher_schedule_handler(message: Message, state: FSMContext):
    await message.answer("Введите фамилию преподавателя:", reply_markup=navigation_keyboard)
    await state.set_state(Form.waiting_for_teacher_name)

@router.message(Form.waiting_for_teacher_name)
async def teacher_name_handler(message: Message, state: FSMContext):
    if message.text == "Главное меню":
        await state.clear()
        await start_command(message)
        return

    teacher_name = message.text
    schedule = get_teacher_schedule(teacher_name)
    await message.answer(f"Расписание преподавателя {teacher_name}\n{schedule}", reply_markup=main_keyboard)
    await state.clear()

#Хэндлер для кнопки "Расписание звонков"
@router.message(lambda message: message.text == "Расписание звонков")
async def bell_schedule_handler(message: Message):
    schedule_link = get_bell_schedule_link()
    await message.answer(schedule_link, reply_markup=main_keyboard)

#Хэндлер для кнопки "Общая информация"
@router.message(lambda message: message.text == "Общая информация")
async def info_handler(message: Message):
    await message.answer("Выберите, что вас интересует:", reply_markup=info_keyboard)

# Хэндлер для кнопки "Ресурсы"
@router.message(lambda message: message.text == "Ресурсы")
async def resources_handler(message: Message):
    await message.answer("Выберите, что вас интересует:", reply_markup=resources_keyboard)

@router.message(lambda message: message.text == "Сайт КнАГУ")
async def info_handler(message: Message):
    await message.answer("Сайт КнАГУ: https://knastu.ru/", reply_markup=main_keyboard)

#Хэндлер для новых кнопок в разделе "Общая информация"
@router.message(lambda message: message.text in ["Личный кабинет", "Учёба"])
async def info_submenu_handler(message: Message):
    if message.text == "Личный кабинет":
        await message.answer("Ссылка на личный кабинет: https://student.knastu.ru/")
    elif message.text == "Учёба":
        await message.answer("Информация об учебном процессе: https://knastu.ru/page/1404")
    await message.answer("Выберите, что вас интересует:", reply_markup=info_keyboard)

#Хэндлер кнопок "Ресурсы"
@router.message(lambda message: message.text in ["Библиотека", "Электронные образовательные ресурсы", "Интернет-ресурсы", "Методические материалы", "Календарные учебные графики"])
async def resources_submenu_handler(message: Message):
    if message.text == "Библиотека":
        await message.answer("Ссылка на библиотеку: https://knastu.ru/page/470")
    elif message.text == "Электронные образовательные ресурсы":
        await message.answer("Ссылка на электронные образовательные ресурсы: https://knastu.ru/students/e_resources")
    elif message.text == "Интернет-ресурсы":
        await message.answer("Список интернет-ресурсов: https://knastu.ru/page/1236")
    elif message.text == "Методические материалы":
        await message.answer("Ссылка на методические материалы: https://knastu.ru/page/1714")
    elif message.text == "Календарные учебные графики":
        await message.answer("Информация об учебных графиках: https://knastu.ru/page/3602")
    await message.answer("Выберите, что вас интересует:", reply_markup=resources_keyboard)

#Хэндлер кнопки "Назад в меню"
@router.message(lambda message: message.text == "Назад в меню")
async def back_to_menu_handler(message: Message):
    await start_command(message)

#Хэндлер для обработки любых других текстовых сообщений
@router.message()
async def handle_text_message(message: Message):
    await message.answer("Пожалуйста, используйте кнопки.", reply_markup=main_keyboard)

#Регистрация хэндлеров и запуск бота
async def main():
    dp.include_router(router)
    await set_default_commands()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())