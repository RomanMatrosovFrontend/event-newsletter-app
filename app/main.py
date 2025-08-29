import os
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.core.auth import get_current_admin
from app.database import engine, Base, get_db
from app import models
from app.services.advanced_scheduler import init_scheduler
from app.models import AdminUser

# Импортируем настройки
from app.core.config import settings

# Создаем таблицы
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Event Newsletter App", version="0.1.0")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Подключаем роутеры
from app.routes import events, users, subscribe, admin, schedules, unsubscribe
app.include_router(events.router, prefix="/events", tags=["events"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(subscribe.router, tags=["subscribe"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(schedules.router, prefix="/schedules", tags=["schedules"])
app.include_router(unsubscribe.router)

@app.get("/")
async def root():
    return {"message": "Event Newsletter API is working!"}

@app.get("/admin")
async def admin_dashboard(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

@app.on_event("startup")
async def startup_event():
    init_scheduler()
    # Создаём админа, если нет
    db = next(get_db())
    if not db.query(AdminUser).first():
        admin = AdminUser(username=os.getenv("ADMIN_USERNAME", "admin"))
        admin.set_password(os.getenv("ADMIN_PASSWORD", "password"))
        db.add(admin)
        db.commit()
        print("✅ Admin user created")
    db.close()


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

