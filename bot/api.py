import httpx

API_URL = "http://localhost:8000/api"

async def get_products():
    async with httpx.AsyncClient() as client:
        return (await client.get(f"{API_URL}/products")).json()

async def create_order(data: dict):
    async with httpx.AsyncClient() as client:
        return (await client.post(f"{API_URL}/orders", json=data)).json()

async def get_order(order_id: int):
    async with httpx.AsyncClient() as client:
        return (await client.get(f"{API_URL}/orders/{order_id}")).json()
