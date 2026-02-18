import sqlite3
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

#  ТОКЕН
TOKEN = ""


# БАЗА ДАННЫХ (SQLite)


db = sqlite3.connect("shop.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    login TEXT UNIQUE,
    password TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seller_id INTEGER,
    name TEXT,
    description TEXT,
    price INTEGER,
    photo TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    buyer_id INTEGER,
    buyer_username TEXT,
    seller_id INTEGER,
    seller_username TEXT,
    product_name TEXT,
    price INTEGER
)
""")

db.commit()


# КЛАВИАТУРЫ


start_kb = ReplyKeyboardMarkup(
    [["🔑 Войти", "📝 Регистрация"]],
    resize_keyboard=True
)

main_kb = ReplyKeyboardMarkup(
    [["🧑‍💼 Продавец", "🛒 Покупатель"], ["👤 Профиль"]],
    resize_keyboard=True
)

seller_kb = ReplyKeyboardMarkup(
    [["➕ Добавить товар", "📦 Мои товары"],
     ["🧾 История продаж"],
     ["🔙 Назад"]],
    resize_keyboard=True
)

buyer_kb = ReplyKeyboardMarkup(
    [["📦 Смотреть товары", "🧾 История покупок"],
     ["🔙 Назад"]],
    resize_keyboard=True
)

profile_kb = ReplyKeyboardMarkup(
    [["🔙 Назад"]],
    resize_keyboard=True
)


# СОСТОЯНИЯ


state = {}
temp = {}



# /start


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cur.execute(
        "INSERT OR IGNORE INTO users (user_id, username) VALUES (?,?)",
        (user.id, user.username)
    )
    db.commit()

    state[user.id] = None
    await update.message.reply_text(
        "Добро пожаловать!\nВойдите или зарегистрируйтесь:",
        reply_markup=start_kb
    )

# ТЕКСТ

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    username = update.effective_user.username
    text = update.message.text
    s = state.get(uid)

    if text == "🔙 Назад":
        await start(update, context)
        return

    #  РЕГИСТРАЦИЯ 
    if text == "📝 Регистрация":
        state[uid] = "reg_login"
        temp[uid] = {}
        await update.message.reply_text("Придумайте логин:")
        return

    if s == "reg_login":
        # Проверка на уникальность логина
        cur.execute("SELECT login FROM users WHERE login=?", (text,))
        if cur.fetchone():
            await update.message.reply_text("Этот логин уже занят, придумайте другой:")
            return
        temp[uid]["login"] = text
        state[uid] = "reg_password"
        await update.message.reply_text("Придумайте пароль:")
        return

    if s == "reg_password":
        temp[uid]["password"] = text
        # Сохраняем пользователя с логином и паролем
        cur.execute(
            "UPDATE users SET login=?, password=? WHERE user_id=?",
            (temp[uid]["login"], temp[uid]["password"], uid)
        )
        db.commit()
        state[uid] = None
        await update.message.reply_text(
            "Регистрация успешна! Теперь войдите в аккаунт:",
            reply_markup=start_kb
        )
        return

    #  ВХОД 
    if text == "🔑 Войти":
        state[uid] = "login"
        await update.message.reply_text("Введите логин:")
        return

    if s == "login":
        temp[uid] = {"login": text}
        state[uid] = "password"
        await update.message.reply_text("Введите пароль:")
        return

    if s == "password":
        cur.execute(
            "SELECT user_id FROM users WHERE login=? AND password=?",
            (temp[uid]["login"], text)
        )
        user_data = cur.fetchone()

        if user_data and user_data[0] == uid:
            state[uid] = None
            await update.message.reply_text(
                "Вход выполнен успешно!",
                reply_markup=main_kb
            )
        else:
            state[uid] = None
            await update.message.reply_text(
                "Неверный логин или пароль. Попробуйте снова:",
                reply_markup=start_kb
            )
        return

    #  ПРОФИЛЬ 
    if text == "👤 Профиль":
        cur.execute("SELECT login FROM users WHERE user_id=?", (uid,))
        login = cur.fetchone()
        if not login or not login[0]:
            await update.message.reply_text(
                "Сначала войдите в аккаунт!",
                reply_markup=start_kb
            )
            return

        cur.execute("SELECT COUNT(*) FROM products WHERE seller_id=?", (uid,))
        products = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM history WHERE buyer_id=?", (uid,))
        buys = cur.fetchone()[0]

        await update.message.reply_text(
            f"👤 Профиль\n\n"
            f"ID: {uid}\n"
            f"Логин: {login[0]}\n"
            f"Тег: @{username}\n\n"
            f"📦 Товаров: {products}\n"
            f"🛒 Покупок: {buys}",
            reply_markup=profile_kb
        )
        return

    #  РЕЖИМЫ 
    if text == "🧑‍💼 Продавец":
        cur.execute("SELECT login FROM users WHERE user_id=?", (uid,))
        if not cur.fetchone()[0]:
            await update.message.reply_text("Сначала войдите в аккаунт!", reply_markup=start_kb)
            return
        state[uid] = "seller"
        await update.message.reply_text("Режим продавца", reply_markup=seller_kb)
        return

    if text == "🛒 Покупатель":
        cur.execute("SELECT login FROM users WHERE user_id=?", (uid,))
        if not cur.fetchone()[0]:
            await update.message.reply_text("Сначала войдите в аккаунт!", reply_markup=start_kb)
            return
        state[uid] = "buyer"
        await update.message.reply_text("Режим покупателя", reply_markup=buyer_kb)
        return

    #  ДОБАВИТЬ ТОВАР 
    if s == "seller" and text == "➕ Добавить товар":
        state[uid] = "add_name"
        temp[uid] = {}
        await update.message.reply_text("Введите название товара:")
        return

    if s == "add_name":
        temp[uid]["name"] = text
        state[uid] = "add_desc"
        await update.message.reply_text("Введите описание:")
        return

    if s == "add_desc":
        temp[uid]["desc"] = text
        state[uid] = "add_price"
        await update.message.reply_text("Введите цену:")
        return

    if s == "add_price" and text.isdigit():
        temp[uid]["price"] = int(text)
        state[uid] = "add_photo"
        await update.message.reply_text("Отправьте фото товара:")
        return

    #  МОИ ТОВАРЫ 
    if s == "seller" and text == "📦 Мои товары":
        cur.execute(
            "SELECT id,name,description,price,photo FROM products WHERE seller_id=?",
            (uid,)
        )
        rows = cur.fetchall()

        if not rows:
            await update.message.reply_text("У вас нет товаров")
            return

        for r in rows:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🗑 Удалить", callback_data=f"del_{r[0]}")]
            ])
            await context.bot.send_photo(
                uid,
                r[4],
                caption=f"{r[1]}\n{r[2]}\n💰 {r[3]} ₽",
                reply_markup=kb
            )

    #  ИСТОРИЯ ПРОДАЖ 
    if s == "seller" and text == "🧾 История продаж":
        cur.execute(
            "SELECT buyer_username,product_name,price FROM history WHERE seller_id=?",
            (uid,)
        )
        rows = cur.fetchall()

        if not rows:
            await update.message.reply_text("Продаж нет")
            return

        total = 0
        msg = "🧾 История продаж:\n\n"
        for r in rows:
            msg += f"👤 @{r[0]}\n📦 {r[1]}\n💰 {r[2]} ₽\n\n"
            total += r[2]

        msg += f"Итого: {total} ₽"
        await update.message.reply_text(msg)

    #  ТОВАРЫ 
    if s == "buyer" and text == "📦 Смотреть товары":
        cur.execute(
            "SELECT id,name,description,price,photo FROM products WHERE seller_id!=?",
            (uid,)
        )
        rows = cur.fetchall()

        if not rows:
            await update.message.reply_text("Товаров нет")
            return

        for r in rows:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("📞 Связаться", callback_data=f"buy_{r[0]}")]
            ])
            await context.bot.send_photo(
                uid,
                r[4],
                caption=f"{r[1]}\n{r[2]}\n💰 {r[3]} ₽",
                reply_markup=kb
            )

    #  ИСТОРИЯ ПОКУПОК 
    if s == "buyer" and text == "🧾 История покупок":
        cur.execute(
            "SELECT seller_username,product_name,price FROM history WHERE buyer_id=?",
            (uid,)
        )
        rows = cur.fetchall()

        if not rows:
            await update.message.reply_text("Покупок нет")
            return

        total = 0
        msg = "🧾 История покупок:\n\n"
        for r in rows:
            msg += f"👤 @{r[0]}\n📦 {r[1]}\n💰 {r[2]} ₽\n\n"
            total += r[2]

        msg += f"Потрачено: {total} ₽"
        await update.message.reply_text(msg)

# ФОТО

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if state.get(uid) == "add_photo":
        photo_id = update.message.photo[-1].file_id
        d = temp[uid]

        cur.execute(
            "INSERT INTO products VALUES (NULL,?,?,?,?,?)",
            (uid, d["name"], d["desc"], d["price"], photo_id)
        )
        db.commit()

        state[uid] = "seller"
        await update.message.reply_text("Товар добавлен", reply_markup=seller_kb)

# CALLBACK

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data.startswith("del_"):
        pid = int(q.data.split("_")[1])
        cur.execute("DELETE FROM products WHERE id=?", (pid,))
        db.commit()
        await q.message.edit_caption("Товар удалён")

    if q.data.startswith("buy_"):
        pid = int(q.data.split("_")[1])

        cur.execute(
            "SELECT seller_id,name,price FROM products WHERE id=?",
            (pid,)
        )
        seller_id, name, price = cur.fetchone()

        cur.execute("SELECT username FROM users WHERE user_id=?", (seller_id,))
        seller_username = cur.fetchone()[0]

        cur.execute(
            "INSERT INTO history VALUES (NULL,?,?,?,?,?,?)",
            (
                q.from_user.id,
                q.from_user.username,
                seller_id,
                seller_username,
                name,
                price
            )
        )

        cur.execute("DELETE FROM products WHERE id=?", (pid,))
        db.commit()

        await context.bot.send_message(
            seller_id,
            f"Продан товар «{name}» за {price} ₽"
        )
        await q.message.reply_text("Покупка завершена")

# ЗАПУСК

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
app.add_handler(CallbackQueryHandler(callback_handler))

print("Бот запущен")
app.run_polling()
    





