import sqlite3
from telegram import Update, BotCommand, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "I am alive!"

def run():
    app.run(host='0.0.0.0', port=8000)

def keep_alive():
    t = Thread(target=run)
    t.start()


# --- Настройки базы ---
DB_FILE = "recipes.db"

# --- Главное меню ---
main_menu = ReplyKeyboardMarkup(
    [["🍽 Случайный рецепт", "🔍 Поиск по ингредиенту"], ["📖 Помощь"]],
    resize_keyboard=True
)

# --- Меню после поиска ---
search_menu = ReplyKeyboardMarkup(
    [["🔄 Ещё рецепт"], ["⬅️ Главное меню"]],
    resize_keyboard=True
)

# --- Получить случайный рецепт из всей базы ---
def get_random_recipe():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT title, ingredients, instructions FROM recipes ORDER BY RANDOM() LIMIT 1")
    recipe = cursor.fetchone()
    conn.close()
    return recipe

# --- Поиск рецептов по ингредиенту ---
def search_recipes_by_ingredient(ingredient):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT title, ingredients, instructions FROM recipes WHERE LOWER(ingredients) LIKE ? COLLATE NOCASE",
        (f"%{ingredient.lower()}%",)
    )
    results = cursor.fetchall()
    conn.close()
    return results

# --- Команда /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот с рецептами.\n\n"
        "Нажми кнопку ниже, чтобы получить случайный рецепт или найти блюдо по продукту 👇",
        reply_markup=main_menu
    )

# --- Команда /recipe (случайный рецепт) ---
async def recipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    recipe = get_random_recipe()
    if recipe:
        title, ingredients, instructions = recipe
        caption = f"<b>{title}</b>\n\n🧺 <b>Ингредиенты:</b>\n{ingredients}\n\n👨‍🍳 <b>Приготовление:</b>\n{instructions}"
        await update.message.reply_text(caption, parse_mode="HTML", reply_markup=main_menu)
    else:
        await update.message.reply_text("😕 В базе пока нет рецептов.", reply_markup=main_menu)

# --- Команда /search (поиск по ингредиенту) ---
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ingredient = " ".join(context.args).strip()
    if not ingredient:
        await update.message.reply_text(
            "❗ Напиши после команды продукт, например:\n/search курица",
            reply_markup=main_menu
        )
        return

    recipes = search_recipes_by_ingredient(ingredient)
    if not recipes:
        await update.message.reply_text("😔 Рецептов с этим продуктом не найдено.", reply_markup=main_menu)
        return

    # Сохраняем результаты поиска и индекс
    context.user_data["search_results"] = recipes
    context.user_data["search_index"] = 0

    # Отправляем первый рецепт
    await send_search_recipe(update, context)

# --- Функция для отправки следующего рецепта из поиска ---
async def send_search_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    recipes = context.user_data.get("search_results")
    index = context.user_data.get("search_index", 0)

    if not recipes:
        await update.message.reply_text("😔 Нет сохранённых рецептов.", reply_markup=main_menu)
        return

    # Берём рецепт по индексу
    title, ingredients, instructions = recipes[index]

    caption = f"<b>{title}</b>\n\n🧺 <b>Ингредиенты:</b>\n{ingredients}\n\n👨‍🍳 <b>Приготовление:</b>\n{instructions}"
    await update.message.reply_text(caption, parse_mode="HTML", reply_markup=search_menu)

    # Увеличиваем индекс циклично
    context.user_data["search_index"] = (index + 1) % len(recipes)

# --- Команда /help ---
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 Команды:\n"
        "/start — начать работу с ботом\n"
        "/recipe — случайный рецепт\n"
        "/search [ингредиент] — поиск по продукту\n"
        "/help — помощь\n\n"
        "Или используй кнопки ниже 👇",
        reply_markup=main_menu
    )

# --- Обработка нажатий кнопок ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    if "рецепт" in text and "случайный" in text:
        await recipe(update, context)
    elif "поиск" in text:
        await update.message.reply_text(
            "🔎 Напиши команду /search [продукт], например: /search курица",
            reply_markup=main_menu
        )
    elif "ещё" in text:
        if "search_results" in context.user_data:
            await send_search_recipe(update, context)
        else:
            await update.message.reply_text(
                "😅 Сначала нужно сделать поиск по ингредиенту.",
                reply_markup=main_menu
            )
    elif "помощ" in text or "главное меню" in text:
        await help_command(update, context)
    else:
        await update.message.reply_text("😅 Не понял. Используй кнопки ниже 👇", reply_markup=main_menu)

# --- Устанавливаем команды в меню Telegram ---
async def set_commands(application):
    commands = [
        BotCommand("start", "Начать работу с ботом"),
        BotCommand("recipe", "Получить случайный рецепт"),
        BotCommand("search", "Найти рецепт по продукту"),
        BotCommand("help", "Показать помощь"),
    ]
    await application.bot.set_my_commands(commands)
    print("✅ Команды успешно установлены в меню Telegram")

# --- Основной запуск ---
def main():
    application = ApplicationBuilder().token("8448630510:AAFEmNnwoqRgKRJZvA1VhxQH9yHCIpuz4uo").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("recipe", recipe))
    application.add_handler(CommandHandler("search", search))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.post_init = set_commands

    print("🚀 Бот запущен. Работает и поиск, и случайные рецепты.")
    application.run_polling()

if __name__ == "__main__":
    keep_alive()
    main()



    

