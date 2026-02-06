from fastapi import Request
from fastapi.responses import RedirectResponse


def require_login(request: Request):
    if not request.session.get("admin"):
        return RedirectResponse("/admin/login", 302)
