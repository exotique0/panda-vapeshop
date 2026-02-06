from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.notifications import notify_user
from app.admin.constants import STATUS_MESSAGES
import asyncio

from app.database import get_db
from app.models import Admin, Product, Order, OrderItem
from app.admin.constants import STATUS_MAP, STATUS_COLORS
from app.admin.auth import require_login

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/admin/templates")


# ---------- AUTH ----------

@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
def login(
    request: Request,
    login: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    admin = db.query(Admin).filter_by(login=login, password=password).first()
    if admin:
        request.session["admin"] = True
        return RedirectResponse("/admin/products", status_code=302)
    return RedirectResponse("/admin/login", status_code=302)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/admin/login", status_code=302)


# ---------- PRODUCTS ----------

@router.get("/products")
def products(request: Request, db: Session = Depends(get_db)):
    if require_login(request):
        return require_login(request)

    products = db.query(Product).all()
    return templates.TemplateResponse(
        "products.html",
        {"request": request, "products": products},
    )


@router.post("/products")
def add_product(
    request: Request,
    name: str = Form(...),
    price: float = Form(...),
    quantity: int = Form(...),
    db: Session = Depends(get_db),
):
    if require_login(request):
        return require_login(request)

    db.add(Product(name=name, price=price, quantity=quantity))
    db.commit()
    return RedirectResponse("/admin/products", status_code=302)


# ---------- ORDERS ----------

@router.get("/orders")
def orders(request: Request, db: Session = Depends(get_db)):
    if require_login(request):
        return require_login(request)

    orders = db.query(Order).filter(Order.archived == False).all()
    return templates.TemplateResponse(
        "orders.html",
        {
            "request": request,
            "orders": orders,
            "statuses": STATUS_MAP,
            "colors": STATUS_COLORS,
        },
    )


@router.get("/orders/create")
def order_create_page(request: Request, db: Session = Depends(get_db)):
    if require_login(request):
        return require_login(request)

    products = db.query(Product).filter(Product.quantity > 0).all()
    return templates.TemplateResponse(
        "order_create.html",
        {"request": request, "products": products},
    )


@router.post("/orders/create")
async def order_create(request: Request, db: Session = Depends(get_db)):
    form = await request.form()

    customer_name = form.get("customer_name")
    customer_address = form.get("customer_address")

    if not customer_name or not customer_address:
        return RedirectResponse("/admin/orders/create", 302)

    total_price = 0
    items = []

    products = db.query(Product).all()

    for product in products:
        qty = int(form.get(f"qty_{product.id}", 0))
        if qty > 0:
            if product.quantity < qty:
                return RedirectResponse("/admin/orders/create", 302)

            product.quantity -= qty
            total_price += product.price * qty

            items.append(
                OrderItem(
                    product_name=product.name,
                    quantity=qty,
                    price=product.price,
                )
            )

    if not items:
        return RedirectResponse("/admin/orders/create", 302)

    order = Order(
        status="new",
        archived=False,
        total_price=total_price,
        customer_name=customer_name,
        customer_address=customer_address,
        stock_returned=False,
    )

    order.items = items
    db.add(order)
    db.commit()

    return RedirectResponse("/admin/orders", 302)


@router.post("/orders/status")
async def change_status(
    order_id: int = Form(...),
    status: str = Form(...),
    db: Session = Depends(get_db),
):
    order = db.get(Order, order_id)
    if not order:
        return RedirectResponse("/admin/orders", 302)

    old_status = order.status

    if status == "cancelled" and not order.stock_returned:
        for item in order.items:
            product = db.query(Product).filter_by(name=item.product_name).first()
            if product:
                product.quantity += item.quantity
        order.stock_returned = True
        order.archived = True

    if status == "completed":
        order.archived = True

    if status in ("new", "paid", "shipped"):
        order.archived = False

    order.status = status
    db.commit()

    # 🔔 TELEGRAM УВЕДОМЛЕНИЕ
    if order.customer_telegram_id and old_status != status:
        asyncio.create_task(
            notify_user(
                order.customer_telegram_id,
                STATUS_MESSAGES.get(status, f"📦 Статус заказа: {status}")
            )
        )

    return RedirectResponse("/admin/orders", 302)


@router.get("/orders/archive")
def archive(request: Request, db: Session = Depends(get_db)):
    if require_login(request):
        return require_login(request)

    orders = db.query(Order).filter(Order.archived == True).all()
    return templates.TemplateResponse(
        "orders_archive.html",
        {
            "request": request,
            "orders": orders,
            "statuses": STATUS_MAP,
            "colors": STATUS_COLORS,
        },
    )


@router.post("/orders/restore")
def restore_order(order_id: int = Form(...), db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        return RedirectResponse("/admin/orders/archive", 302)

    if order.stock_returned:
        for item in order.items:
            product = db.query(Product).filter_by(name=item.product_name).first()
            if not product or product.quantity < item.quantity:
                return RedirectResponse("/admin/orders/archive", 302)

        for item in order.items:
            product = db.query(Product).filter_by(name=item.product_name).first()
            product.quantity -= item.quantity

        order.stock_returned = False

    order.archived = False
    order.status = "new"
    db.commit()

    return RedirectResponse("/admin/orders", 302)

@router.post("/products/update-stock")
def update_stock(
    product_id: int = Form(...),
    delta: int = Form(...),
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)
    if not product:
        return RedirectResponse("/admin/products", 302)

    product.quantity += delta

    if product.quantity < 0:
        product.quantity = 0  # защита от минуса

    db.commit()
    return RedirectResponse("/admin/products", 302)


@router.post("/products/set-stock")
def set_stock(
    product_id: int = Form(...),
    quantity: int = Form(...),
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)
    if not product:
        return RedirectResponse("/admin/products", 302)

    if quantity < 0:
        quantity = 0  # защита

    product.quantity = quantity
    db.commit()
    return RedirectResponse("/admin/products", 302)

@router.post("/products/delete")
def delete_product(
    product_id: int = Form(...),
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)
    if product:
        db.delete(product)
        db.commit()
    return RedirectResponse("/admin/products", 302)

@router.post("/orders/delete")
def delete_order(
    order_id: int = Form(...),
    db: Session = Depends(get_db),
):
    order = db.get(Order, order_id)
    if order:
        db.delete(order)
        db.commit()
    return RedirectResponse("/admin/orders", 302)
