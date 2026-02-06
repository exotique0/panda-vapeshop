from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from app.database import get_db
from app.models import Product, Order, OrderItem

router = APIRouter(prefix="/api")


# ---------- SCHEMAS ----------

class OrderItemIn(BaseModel):
    product_id: int
    quantity: int


class OrderCreateIn(BaseModel):
    telegram_id: str
    username: str | None
    country: str
    customer_name: str
    customer_address: str
    items: List[OrderItemIn]



# ---------- PRODUCTS ----------

@router.get("/products")
def get_products(db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.quantity > 0).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "price": p.price,
            "quantity": p.quantity,
        }
        for p in products
    ]


# ---------- ORDERS ----------

@router.post("/orders")
def create_order(data: OrderCreateIn, db: Session = Depends(get_db)):
    total = 0
    items = []

    for i in data.items:
        product = db.get(Product, i.product_id)
        if not product or product.quantity < i.quantity:
            raise HTTPException(400, "Not enough stock")

        product.quantity -= i.quantity
        total += product.price * i.quantity

        items.append(
            OrderItem(
                product_name=product.name,
                quantity=i.quantity,
                price=product.price,
            )
        )

    order = Order(
        status="new",
        total_price=total,
        customer_name=data.customer_name,
        customer_username=data.username,
        customer_telegram_id=data.telegram_id,
        customer_address=f"{data.country}, {data.customer_address}",
    )

    order.items = items
    db.add(order)
    db.commit()
    db.refresh(order)

    return {
        "order_id": order.id,
        "total_price": order.total_price,
    }


@router.post("/orders/{order_id}/paid")
def mark_paid(order_id: int, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(404)

    order.status = "paid"
    db.commit()
    return {"ok": True}

@router.get("/orders/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(404)

    return {
        "id": order.id,
        "status": order.status,
        "total_price": order.total_price,
    }