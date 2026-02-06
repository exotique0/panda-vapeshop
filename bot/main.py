import asyncio
import re
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from states import OrderFSM
from keyboards import *
from api import get_products, create_order, get_order



TOKEN = "8237120392:AAF0TJtG3CTpN3futulT1rqEOPEpTWa3JAI"

bot = Bot(TOKEN)
dp = Dispatcher()

# ======================
# ✅ ВАЛИДАЦИЯ
# ======================

NAME_REGEX = re.compile(r"^[A-Z][a-z]+ [A-Z][a-z]+$")
ADDRESS_REGEX = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿß0-9 ,.\-/]{10,}$")

ADDRESS_EXAMPLES = {
    "Germany": "Berlin, Müllerstraße 12, Apt 5",
    "France": "Paris, Avenue des Champs-Élysées 15",
    "Italy": "Rome, Via del Corso 21",
    "Spain": "Madrid, Calle de Alcalá 45",
    "Netherlands": "Amsterdam, Damrak 10",
    "Poland": "Warsaw, Nowy Świat 18",
    "Austria": "Vienna, Kärntner Straße 7",
    "Switzerland": "Zurich, Bahnhofstrasse 22",
}


def valid_name(value: str) -> bool:
    return bool(NAME_REGEX.match(value.strip()))


def valid_address(value: str) -> bool:
    return bool(ADDRESS_REGEX.match(value.strip()))


# ======================
# 🚀 START
# ======================

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(OrderFSM.country)

    await message.answer(
        "🐼💨 *Добро пожаловать в Panda VapeShop EU!*\n\n"
        "Премиальные вкусы • Быстрая доставка • Только EU 🇪🇺\n\n"
        "Выберите страну доставки ⬇️",
        parse_mode="Markdown",
        reply_markup=countries_kb(),
    )


# ======================
# 🌍 COUNTRY
# ======================

@dp.callback_query(F.data.startswith("country"))
async def choose_country(callback: CallbackQuery, state: FSMContext):
    country = callback.data.split(":", 1)[1]

    await state.update_data(country=country, cart={})
    await state.set_state(OrderFSM.catalog)

    products = await get_products()
    await callback.message.answer(
        "🧃 *Каталог*",
        parse_mode="Markdown",
        reply_markup=products_kb(products),
    )


# ======================
# 🧃 CATALOG
# ======================

@dp.callback_query(F.data.startswith("product"))
async def select_product(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split(":", 1)[1])

    await state.update_data(
        selected_product=product_id,
        quantity=1,
    )
    await state.set_state(OrderFSM.quantity)

    await callback.message.answer(
        "Выберите количество:",
        reply_markup=quantity_kb(1),
    )


@dp.callback_query(F.data.startswith("qty"))
async def change_quantity(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    delta = int(callback.data.split(":", 1)[1])

    qty = max(1, data["quantity"] + delta)
    await state.update_data(quantity=qty)

    await callback.message.edit_reply_markup(
        reply_markup=quantity_kb(qty)
    )


@dp.callback_query(F.data == "add_to_cart")
async def add_to_cart(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cart = data["cart"]

    pid = data["selected_product"]
    qty = data["quantity"]

    cart[pid] = cart.get(pid, 0) + qty

    await state.update_data(cart=cart)
    await state.set_state(OrderFSM.catalog)

    products = await get_products()
    await callback.message.answer(
        "✅ Добавлено в корзину",
        reply_markup=products_kb(products),
    )


@dp.callback_query(F.data == "back_to_catalog")
async def back_to_catalog(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OrderFSM.catalog)

    products = await get_products()
    await callback.message.answer(
        "🧃 *Каталог*",
        parse_mode="Markdown",
        reply_markup=products_kb(products),
    )


# ======================
# 🛒 CART
# ======================

@dp.callback_query(F.data == "open_cart")
async def open_cart(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cart = data.get("cart", {})

    if not cart:
        await callback.answer("Корзина пуста")
        return

    products = await get_products()
    products_map = {p["id"]: p for p in products}

    await state.set_state(OrderFSM.cart)

    for pid, qty in cart.items():
        product = products_map.get(pid)
        if not product:
            continue

        await callback.message.answer(
            f"{product['name']} × {qty} ({product['price']}€)",
            reply_markup=cart_item_kb(pid),
        )

    await callback.message.answer(
        "Что дальше?",
        reply_markup=cart_kb(),
    )


@dp.callback_query(F.data.startswith("cart_inc"))
async def cart_inc(callback: CallbackQuery, state: FSMContext):
    pid = int(callback.data.split(":", 1)[1])
    data = await state.get_data()

    data["cart"][pid] += 1
    await state.update_data(cart=data["cart"])
    await callback.answer("➕")


@dp.callback_query(F.data.startswith("cart_dec"))
async def cart_dec(callback: CallbackQuery, state: FSMContext):
    pid = int(callback.data.split(":", 1)[1])
    data = await state.get_data()

    data["cart"][pid] -= 1
    if data["cart"][pid] <= 0:
        del data["cart"][pid]

    await state.update_data(cart=data["cart"])
    await callback.answer("➖")


@dp.callback_query(F.data.startswith("cart_del"))
async def cart_del(callback: CallbackQuery, state: FSMContext):
    pid = int(callback.data.split(":", 1)[1])
    data = await state.get_data()

    data["cart"].pop(pid, None)
    await state.update_data(cart=data["cart"])
    await callback.answer("❌ Удалено")


# ======================
# 📝 CHECKOUT
# ======================

@dp.callback_query(F.data == "checkout")
async def checkout(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OrderFSM.name)

    await callback.message.answer(
        "Введите *Имя и Фамилию латиницей*, как в паспорте.\n\n"
        "Пример:\n"
        "`Matvei Braun`",
        parse_mode="Markdown",
    )


@dp.message(OrderFSM.name)
async def set_name(message: Message, state: FSMContext):
    name = message.text.strip()

    if not valid_name(name):
        await message.answer(
            "❌ Неверный формат имени.\n\n"
            "Введите *Имя и Фамилию латиницей*.\n"
            "Пример: `Matvei Braun`",
            parse_mode="Markdown",
        )
        return

    await state.update_data(name=name)

    data = await state.get_data()
    country = data.get("country")
    example = ADDRESS_EXAMPLES.get(country, "Berlin, Müllerstraße 12")

    await state.set_state(OrderFSM.address)
    await message.answer(
        "Введите адрес доставки *латиницей*.\n\n"
        f"Пример для {country}:\n"
        f"`{example}`",
        parse_mode="Markdown",
    )


@dp.message(OrderFSM.address)
async def set_address(message: Message, state: FSMContext):
    address = message.text.strip()

    if not valid_address(address):
        await message.answer(
            "❌ Неверный формат адреса.\n\n"
            "Пример:\n"
            "`Berlin, Müllerstraße 12, Apt 5`",
            parse_mode="Markdown",
        )
        return

    await state.update_data(address=address)
    data = await state.get_data()

    products = await get_products()
    products_map = {p["id"]: p for p in products}

    text = (
        "📦 *Подтверждение заказа*\n\n"
        f"👤 {data['name']}\n"
        f"📍 {data['country']}, {data['address']}\n\n"
        "🧃 *Товары:*\n"
    )

    total = 0
    for pid, qty in data["cart"].items():
        p = products_map.get(pid)
        if not p:
            continue
        total += p["price"] * qty
        text += f"- {p['name']} × {qty}\n"

    text += f"\n💶 *Итого: {total}€*"

    await state.set_state(OrderFSM.confirm)
    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=confirm_order_kb(),
    )


@dp.callback_query(F.data == "confirm_order")
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    items = [
        {"product_id": pid, "quantity": qty}
        for pid, qty in data["cart"].items()
    ]

    order = await create_order({
        "telegram_id": str(callback.from_user.id),
        "username": callback.from_user.username,
        "country": data["country"],
        "customer_name": data["name"],
        "customer_address": data["address"],
        "items": items,
    })

    await state.clear()
    await state.update_data(last_order_id=order["order_id"])

    await callback.message.answer(
        f"✅ Заказ #{order['order_id']} оформлен\n"
        f"💶 Сумма: {order['total_price']}€"
    )


# ======================
# 📦 TRACKING
# ======================

@dp.message(F.text == "/track")
async def track(message: Message, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("last_order_id")

    if not order_id:
        await message.answer("У вас нет активных заказов.")
        return

    order = await get_order(order_id)
    await message.answer(
        f"📦 Заказ #{order_id}\n"
        f"Статус: *{order['status']}*",
        parse_mode="Markdown",
    )


# ======================
# ▶️ RUN
# ======================

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
