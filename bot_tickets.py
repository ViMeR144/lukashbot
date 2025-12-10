import asyncio
import logging
import os
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем токен из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден! Создайте файл .env и добавьте туда BOT_TOKEN=ваш_токен")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# База данных (в реальном проекте используйте БД)
user_tickets = {}  # Билеты пользователя
user_cart = {}     # Корзина пользователя

# Примеры событий
EVENTS = [
    {
        "id": "1",
        "name": "🎭 Концерт рок-группы",
        "date": "15.12.2024",
        "time": "19:00",
        "venue": "Концертный зал",
        "price": 1500,
        "available": 50
    },
    {
        "id": "2",
        "name": "🎬 Премьера фильма",
        "date": "20.12.2024",
        "time": "18:30",
        "venue": "Кинотеатр 'Звезда'",
        "price": 500,
        "available": 100
    },
    {
        "id": "3",
        "name": "⚽ Футбольный матч",
        "date": "25.12.2024",
        "time": "16:00",
        "venue": "Стадион 'Арена'",
        "price": 2000,
        "available": 30
    },
    {
        "id": "4",
        "name": "🎪 Цирковое представление",
        "date": "28.12.2024",
        "time": "15:00",
        "venue": "Цирк",
        "price": 1200,
        "available": 80
    },
    {
        "id": "5",
        "name": "🎼 Симфонический оркестр",
        "date": "30.12.2024",
        "time": "19:30",
        "venue": "Филармония",
        "price": 1800,
        "available": 40
    },
    {
        "id": "6",
        "name": "🎤 Стендап-шоу",
        "date": "05.01.2025",
        "time": "20:00",
        "venue": "Комеди-клуб",
        "price": 800,
        "available": 60
    }
]


# Функция создания главного меню
def get_main_menu():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="🎫 Каталог событий", callback_data="events"))
    keyboard.add(InlineKeyboardButton(text="🛒 Моя корзина", callback_data="cart"))
    keyboard.add(InlineKeyboardButton(text="🎟️ Мои билеты", callback_data="my_tickets"))
    keyboard.add(InlineKeyboardButton(text="🔍 Поиск событий", callback_data="search"))
    keyboard.add(InlineKeyboardButton(text="📚 Полезные ссылки", callback_data="links"))
    keyboard.add(InlineKeyboardButton(text="ℹ️ О боте", callback_data="about"))
    keyboard.adjust(2, 2, 1, 1)
    return keyboard.as_markup()


# Функция создания клавиатуры для каталога событий
def get_events_keyboard():
    keyboard = InlineKeyboardBuilder()
    for event in EVENTS:
        keyboard.add(InlineKeyboardButton(
            text=f"{event['name']} - {event['price']}₽",
            callback_data=f"event_{event['id']}"
        ))
    keyboard.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu"))
    keyboard.adjust(1)
    return keyboard.as_markup()


# Функция создания клавиатуры для конкретного события
def get_event_keyboard(event_id: str):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="🛒 Добавить в корзину", callback_data=f"add_cart_{event_id}"))
    keyboard.add(InlineKeyboardButton(text="💰 Купить сейчас", callback_data=f"buy_{event_id}"))
    keyboard.add(InlineKeyboardButton(text="⬅️ Назад к каталогу", callback_data="events"))
    keyboard.adjust(1, 1, 1)
    return keyboard.as_markup()


# Функция создания клавиатуры для корзины
def get_cart_keyboard(cart_items):
    keyboard = InlineKeyboardBuilder()
    for item in cart_items:
        event = next((e for e in EVENTS if e['id'] == item['event_id']), None)
        if event:
            keyboard.add(InlineKeyboardButton(
                text=f"❌ {event['name']}",
                callback_data=f"remove_cart_{item['event_id']}"
            ))
    keyboard.add(InlineKeyboardButton(text="💳 Оформить заказ", callback_data="checkout"))
    keyboard.add(InlineKeyboardButton(text="🗑️ Очистить корзину", callback_data="clear_cart"))
    keyboard.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu"))
    keyboard.adjust(1)
    return keyboard.as_markup()


# Функция создания клавиатуры для полезных ссылок
def get_links_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="🌐 Сайт колледжа", url="https://example-college.ru"))
    keyboard.add(InlineKeyboardButton(text="📱 Соцсети", url="https://vk.com/college"))
    keyboard.add(InlineKeyboardButton(text="📚 Библиотека", url="https://library.college.ru"))
    keyboard.add(InlineKeyboardButton(text="💬 Чат студентов", url="https://t.me/college_chat"))
    keyboard.add(InlineKeyboardButton(text="🎮 FunPay", url="https://funpay.com"))
    keyboard.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu"))
    keyboard.adjust(2, 2, 1, 1)
    return keyboard.as_markup()


# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    keyboard = get_main_menu()
    user_id = message.from_user.id
    
    # Инициализируем данные пользователя
    if user_id not in user_tickets:
        user_tickets[user_id] = []
    if user_id not in user_cart:
        user_cart[user_id] = []
    
    await message.answer(
        f"🎫 Привет, {message.from_user.first_name}!\n\n"
        "Добро пожаловать в бота для покупки билетов! 🎭\n\n"
        "Я помогу тебе:\n"
        "• 🎫 Найти интересные события\n"
        "• 🛒 Добавить билеты в корзину\n"
        "• 🎟️ Управлять своими билетами\n"
        "• 🔍 Искать события по названию\n\n"
        "Выбери действие:",
        reply_markup=keyboard
    )


# Обработчик команды /help
@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "🎫 <b>Команды бота:</b>\n\n"
        "/start - Главное меню\n"
        "/help - Помощь\n"
        "/events - Каталог событий\n"
        "/cart - Моя корзина\n"
        "/tickets - Мои билеты\n\n"
        "Используй кнопки для навигации! 🎭",
        parse_mode="HTML"
    )


# Обработчик callback для главного меню
@dp.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery):
    keyboard = get_main_menu()
    await callback.message.edit_text(
        "🎫 <b>Главное меню</b>\n\n"
        "Выбери действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# Обработчик callback для каталога событий
@dp.callback_query(F.data == "events")
async def callback_events(callback: CallbackQuery):
    keyboard = get_events_keyboard()
    events_text = "\n".join([
        f"🎫 {e['name']}\n"
        f"   📅 {e['date']} в {e['time']}\n"
        f"   📍 {e['venue']}\n"
        f"   💰 {e['price']}₽ | 🎟️ Осталось: {e['available']}\n"
        for e in EVENTS
    ])
    await callback.message.edit_text(
        f"🎫 <b>Каталог событий</b>\n\n{events_text}\n\nВыбери событие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# Обработчик callback для конкретного события
@dp.callback_query(F.data.startswith("event_"))
async def callback_event(callback: CallbackQuery):
    event_id = callback.data.replace("event_", "")
    event = next((e for e in EVENTS if e['id'] == event_id), None)
    
    if not event:
        await callback.answer("Событие не найдено", show_alert=True)
        return
    
    keyboard = get_event_keyboard(event_id)
    
    await callback.message.edit_text(
        f"🎫 <b>{event['name']}</b>\n\n"
        f"📅 <b>Дата:</b> {event['date']}\n"
        f"🕐 <b>Время:</b> {event['time']}\n"
        f"📍 <b>Место:</b> {event['venue']}\n"
        f"💰 <b>Цена:</b> {event['price']}₽\n"
        f"🎟️ <b>Осталось билетов:</b> {event['available']}\n\n"
        "Выбери действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# Обработчик callback для добавления в корзину
@dp.callback_query(F.data.startswith("add_cart_"))
async def callback_add_cart(callback: CallbackQuery):
    user_id = callback.from_user.id
    event_id = callback.data.replace("add_cart_", "")
    event = next((e for e in EVENTS if e['id'] == event_id), None)
    
    if not event:
        await callback.answer("Событие не найдено", show_alert=True)
        return
    
    if user_id not in user_cart:
        user_cart[user_id] = []
    
    # Проверяем, нет ли уже в корзине
    if any(item['event_id'] == event_id for item in user_cart[user_id]):
        await callback.answer("Это событие уже в корзине!", show_alert=True)
        return
    
    user_cart[user_id].append({
        "event_id": event_id,
        "added_at": datetime.now().isoformat()
    })
    
    await callback.answer(f"✅ {event['name']} добавлено в корзину!")


# Обработчик callback для покупки
@dp.callback_query(F.data.startswith("buy_"))
async def callback_buy(callback: CallbackQuery):
    user_id = callback.from_user.id
    event_id = callback.data.replace("buy_", "")
    event = next((e for e in EVENTS if e['id'] == event_id), None)
    
    if not event:
        await callback.answer("Событие не найдено", show_alert=True)
        return
    
    if user_id not in user_tickets:
        user_tickets[user_id] = []
    
    # Создаем билет
    ticket = {
        "id": f"{user_id}_{event_id}_{datetime.now().timestamp()}",
        "event_id": event_id,
        "purchase_date": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "status": "Активен"
    }
    
    user_tickets[user_id].append(ticket)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🎟️ Мои билеты", callback_data="my_tickets"),
        InlineKeyboardButton(text="⬅️ Главное меню", callback_data="main_menu")
    ]])
    
    await callback.message.edit_text(
        f"✅ <b>Билет куплен!</b>\n\n"
        f"🎫 <b>Событие:</b> {event['name']}\n"
        f"📅 <b>Дата:</b> {event['date']} в {event['time']}\n"
        f"📍 <b>Место:</b> {event['venue']}\n"
        f"💰 <b>Цена:</b> {event['price']}₽\n"
        f"🎟️ <b>Номер билета:</b> {ticket['id'][:20]}...\n\n"
        f"Билет сохранен в разделе 'Мои билеты'",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# Обработчик callback для корзины
@dp.callback_query(F.data == "cart")
async def callback_cart(callback: CallbackQuery):
    user_id = callback.from_user.id
    cart = user_cart.get(user_id, [])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")
    ]])
    
    if not cart:
        await callback.message.edit_text(
            "🛒 <b>Моя корзина</b>\n\n"
            "Корзина пуста. Добавь билеты из каталога!",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        total = 0
        cart_text = ""
        for item in cart:
            event = next((e for e in EVENTS if e['id'] == item['event_id']), None)
            if event:
                cart_text += f"🎫 {event['name']}\n   💰 {event['price']}₽\n\n"
                total += event['price']
        
        keyboard = get_cart_keyboard(cart)
        
        await callback.message.edit_text(
            f"🛒 <b>Моя корзина</b>\n\n{cart_text}"
            f"💰 <b>Итого:</b> {total}₽\n\n"
            "Выбери действие:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    await callback.answer()


# Обработчик callback для удаления из корзины
@dp.callback_query(F.data.startswith("remove_cart_"))
async def callback_remove_cart(callback: CallbackQuery):
    user_id = callback.from_user.id
    event_id = callback.data.replace("remove_cart_", "")
    event = next((e for e in EVENTS if e['id'] == event_id), None)
    
    if user_id in user_cart:
        user_cart[user_id] = [item for item in user_cart[user_id] if item['event_id'] != event_id]
    
    if event:
        await callback.answer(f"❌ {event['name']} удалено из корзины")
    else:
        await callback.answer("Удалено из корзины")
    
    # Обновляем отображение корзины
    await callback_cart(callback)


# Обработчик callback для очистки корзины
@dp.callback_query(F.data == "clear_cart")
async def callback_clear_cart(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id in user_cart:
        user_cart[user_id] = []
    await callback.answer("✅ Корзина очищена!")
    await callback_cart(callback)


# Обработчик callback для оформления заказа
@dp.callback_query(F.data == "checkout")
async def callback_checkout(callback: CallbackQuery):
    user_id = callback.from_user.id
    cart = user_cart.get(user_id, [])
    
    if not cart:
        await callback.answer("Корзина пуста!", show_alert=True)
        return
    
    if user_id not in user_tickets:
        user_tickets[user_id] = []
    
    total = 0
    tickets_text = ""
    
    for item in cart:
        event = next((e for e in EVENTS if e['id'] == item['event_id']), None)
        if event:
            ticket = {
                "id": f"{user_id}_{event['id']}_{datetime.now().timestamp()}",
                "event_id": event['id'],
                "purchase_date": datetime.now().strftime("%d.%m.%Y %H:%M"),
                "status": "Активен"
            }
            user_tickets[user_id].append(ticket)
            tickets_text += f"🎫 {event['name']}\n   💰 {event['price']}₽\n"
            total += event['price']
    
    # Очищаем корзину
    user_cart[user_id] = []
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🎟️ Мои билеты", callback_data="my_tickets"),
        InlineKeyboardButton(text="⬅️ Главное меню", callback_data="main_menu")
    ]])
    
    await callback.message.edit_text(
        f"✅ <b>Заказ оформлен!</b>\n\n"
        f"{tickets_text}\n"
        f"💰 <b>Итого:</b> {total}₽\n\n"
        f"Все билеты сохранены в разделе 'Мои билеты'",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# Обработчик callback для моих билетов
@dp.callback_query(F.data == "my_tickets")
async def callback_my_tickets(callback: CallbackQuery):
    user_id = callback.from_user.id
    tickets = user_tickets.get(user_id, [])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")
    ]])
    
    if not tickets:
        await callback.message.edit_text(
            "🎟️ <b>Мои билеты</b>\n\n"
            "У тебя пока нет билетов. Купи билеты из каталога!",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        tickets_text = ""
        for i, ticket in enumerate(tickets, 1):
            event = next((e for e in EVENTS if e['id'] == ticket['event_id']), None)
            if event:
                tickets_text += (
                    f"{i}. 🎫 <b>{event['name']}</b>\n"
                    f"   📅 {event['date']} в {event['time']}\n"
                    f"   📍 {event['venue']}\n"
                    f"   🎟️ Номер: {ticket['id'][:15]}...\n"
                    f"   ✅ Статус: {ticket['status']}\n"
                    f"   📅 Куплен: {ticket['purchase_date']}\n\n"
                )
        
        await callback.message.edit_text(
            f"🎟️ <b>Мои билеты</b>\n\n{tickets_text}",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    await callback.answer()


# Обработчик callback для поиска
@dp.callback_query(F.data == "search")
async def callback_search(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")
    ]])
    await callback.message.edit_text(
        "🔍 <b>Поиск событий</b>\n\n"
        "Введи название события для поиска:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# Обработчик callback для полезных ссылок
@dp.callback_query(F.data == "links")
async def callback_links(callback: CallbackQuery):
    try:
        keyboard = get_links_keyboard()
        await callback.message.edit_text(
            "📚 <b>Полезные ссылки</b>\n\n"
            "Быстрый доступ к важным ресурсам:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в callback_links: {e}", exc_info=True)
        try:
            keyboard = get_links_keyboard()
            await callback.message.answer(
                "📚 <b>Полезные ссылки</b>\n\n"
                "Быстрый доступ к важным ресурсам:",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            await callback.answer()
        except Exception as e2:
            logger.error(f"Ошибка при отправке нового сообщения: {e2}")
            await callback.answer("Произошла ошибка", show_alert=True)


# Обработчик callback для информации о боте
@dp.callback_query(F.data == "about")
async def callback_about(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")
    ]])
    await callback.message.edit_text(
        "ℹ️ <b>О боте</b>\n\n"
        "🎫 Бот для покупки билетов на события\n\n"
        "<b>Возможности:</b>\n"
        "• 🎫 Просмотр каталога событий\n"
        "• 🛒 Корзина для билетов\n"
        "• 🎟️ Управление своими билетами\n"
        "• 🔍 Поиск событий\n"
        "• 📚 Полезные ссылки\n\n"
        "<b>Версия:</b> 1.0\n"
        "<b>Разработчик:</b> Для колледжа\n\n"
        "Используй /help для списка команд",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# Обработчик текстовых сообщений для поиска
@dp.message(F.text)
async def handle_text(message: types.Message):
    user_id = message.from_user.id
    search_query = message.text.lower().strip()
    
    # Поиск событий
    found_events = []
    for event in EVENTS:
        if search_query in event['name'].lower() or search_query in event['venue'].lower():
            found_events.append(event)
            if len(found_events) >= 5:
                break
    
    if found_events:
        keyboard = InlineKeyboardBuilder()
        for event in found_events:
            keyboard.add(InlineKeyboardButton(
                text=f"🎫 {event['name']} - {event['price']}₽",
                callback_data=f"event_{event['id']}"
            ))
        keyboard.add(InlineKeyboardButton(text="⬅️ Главное меню", callback_data="main_menu"))
        keyboard.adjust(1)
        
        events_text = "\n".join([
            f"• {e['name']} - {e['price']}₽ ({e['date']})"
            for e in found_events
        ])
        await message.answer(
            f"🔍 <b>Результаты поиска:</b>\n\n{events_text}\n\nВыбери событие:",
            reply_markup=keyboard.as_markup(),
            parse_mode="HTML"
        )
    else:
        keyboard = get_main_menu()
        await message.answer(
            "❌ События не найдены. Попробуй другой запрос.\n\n"
            "Или используй кнопки меню:",
            reply_markup=keyboard
        )


# Главная функция для polling (локальный запуск)
async def main():
    logger.info("Бот запущен!")
    try:
        # Запускаем polling
        await dp.start_polling(bot, skip_updates=True)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

