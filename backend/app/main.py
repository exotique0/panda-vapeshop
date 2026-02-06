from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.routes import router as api_router


from app.admin.routes import router

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key="secret")

app.mount("/admin/static", StaticFiles(directory="app/admin/static"), name="static")
app.include_router(router)


app.include_router(api_router)