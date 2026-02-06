from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def countries_kb():
    countries = [
        ("🇦🇹 Austria", "Austria"),
        ("🇧🇪 Belgium", "Belgium"),
        ("🇨🇿 Czech Republic", "Czech Republic"),
        ("🇩🇰 Denmark", "Denmark"),
        ("🇪🇪 Estonia", "Estonia"),
        ("🇫🇮 Finland", "Finland"),
        ("🇫🇷 France", "France"),
        ("🇩🇪 Germany", "Germany"),
        ("🇬🇷 Greece", "Greece"),
        ("🇭🇺 Hungary", "Hungary"),
        ("🇮🇸 Iceland", "Iceland"),
        ("🇮🇹 Italy", "Italy"),
        ("🇱🇻 Latvia", "Latvia"),
        ("🇱🇮 Liechtenstein", "Liechtenstein"),
        ("🇱🇹 Lithuania", "Lithuania"),
        ("🇱🇺 Luxembourg", "Luxembourg"),
        ("🇲🇹 Malta", "Malta"),
        ("🇳🇱 Netherlands", "Netherlands"),
        ("🇳🇴 Norway", "Norway"),
        ("🇵🇱 Poland", "Poland"),
        ("🇵🇹 Portugal", "Portugal"),
        ("🇸🇰 Slovakia", "Slovakia"),
        ("🇸🇮 Slovenia", "Slovenia"),
        ("🇪🇸 Spain", "Spain"),
        ("🇸🇪 Sweden", "Sweden"),
        ("🇨🇭 Switzerland", "Switzerland"),
    ]

    keyboard = []
    for i in range(0, len(countries), 2):
        row = [
            InlineKeyboardButton(
                text=countries[i][0],
                callback_data=f"country:{countries[i][1]}"
            )
        ]
        if i + 1 < len(countries):
            row.append(
                InlineKeyboardButton(
                    text=countries[i + 1][0],
                    callback_data=f"country:{countries[i + 1][1]}"
                )
            )
        keyboard.append(row)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def products_kb(products):
    keyboard = [
        [InlineKeyboardButton(
            text=f"{p['name']} — {p['price']}€",
            callback_data=f"product:{p['id']}"
        )]
        for p in products
    ]
    keyboard.append([InlineKeyboardButton(text="🛒 Корзина", callback_data="open_cart")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def quantity_kb(qty: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➖", callback_data="qty:-1"),
            InlineKeyboardButton(text=str(qty), callback_data="noop"),
            InlineKeyboardButton(text="➕", callback_data="qty:+1"),
        ],
        [InlineKeyboardButton(text="🛒 В корзину", callback_data="add_to_cart")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_catalog")],
    ])


def cart_item_kb(product_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➖", callback_data=f"cart_dec:{product_id}"),
            InlineKeyboardButton(text="➕", callback_data=f"cart_inc:{product_id}"),
            InlineKeyboardButton(text="❌", callback_data=f"cart_del:{product_id}"),
        ]
    ])


def cart_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")],
        [InlineKeyboardButton(text="⬅️ В каталог", callback_data="back_to_catalog")],
    ])


def confirm_order_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить заказ", callback_data="confirm_order")],
        [InlineKeyboardButton(text="⬅️ В корзину", callback_data="open_cart")],
    ])
