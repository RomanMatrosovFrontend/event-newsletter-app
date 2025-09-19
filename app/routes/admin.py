from fastapi import APIRouter, BackgroundTasks, Body, Depends, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Dict, List
from app import schemas, models
from app.core.auth import create_access_token, get_current_admin
from app.database import get_db
from app.models import AdminUser
from app.schemas import AdminUserCreate, ChangeCredentialsRequest, EventCountResponse, Token
from app.services.email_service import send_email_via_postmark
from app.utils.event_matcher import get_events_for_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["admin"])
templates = Jinja2Templates(directory="app/templates")

def generate_newsletter_html(events: list, user: models.User) -> str:
    events_html = ""
    for event in events:
        events_html += f"""
        <div style="margin: 20px 0; padding: 15px; border: 1px solid #e0e0e0; border-radius: 8px; background: #fafafa;">
            <h3 style="margin: 0 0 10px 0; color: #333;">{event.title}</h3>
            <p style="margin: 5px 0; color: #666;">
                <strong>📅 Даты:</strong> {', '.join(event.dates) if event.dates else 'Не указано'}
            </p>
            <p style="margin: 5px 0; color: #666;">
                <strong>🏙️ Город:</strong> {event.city or 'Не указан'}
            </p>
            <p style="margin: 5px 0; color: #666;">
                <strong>👥 Возраст:</strong> {event.age_restriction or 'Не указано'}
            </p>
            <p style="margin: 10px 0; color: #444;">{event.description or ''}</p>
            <a href="{event.url}" style="display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; font-weight: bold;">
                📍 Узнать подробнее
            </a>
        </div>
        """
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Ваши рекомендации событий</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; color: white; text-align: center;">
            <h1 style="margin: 0; font-size: 28px;">🎭 Event Newsletter</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.9;">Ваши персональные рекомендации</p>
        </div>
        
        <div style="padding: 30px;">
            <h2 style="color: #333; margin-bottom: 20px;">Привет, {user.email}!</h2>
            <p style="color: #666;">Мы подобрали для вас события по вашим интересам:</p>
            
            {events_html if events_html else '<p style="color: #666; text-align: center; padding: 40px;">На этой неделе нет подходящих событий 😔<br>Но мы сообщим, когда появятся новые!</p>'}
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                <p style="color: #999; font-size: 14px; text-align: center;">
                    С уважением,<br>
                    Команда Event Newsletter<br>
                    <a href="https://your-site.com/unsubscribe?email={user.email}" style="color: #667eea; text-decoration: none;">
                        🔕 Отписаться от рассылки
                    </a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """

def generate_newsletter_text(events: list, user: models.User) -> str:
    events_text = ""
    for event in events:
        events_text += f"""
{event.title}
Даты: {', '.join(event.dates) if event.dates else 'Не указано'}
Город: {event.city or 'Не указан'}
Возраст: {event.age_restriction or 'Не указано'}
Описание: {event.description or ''}
Ссылка: {event.url}
{"-" * 50}
        """
    
    return f"""
Привет, {user.email}!
Мы подобрали для вас события по вашим интересам:
{events_text if events_text else 'На этой неделе нет подходящих событий. Но мы сообщим, когда появятся новые!'}
С уважением,
Команда Event Newsletter
Отписаться от рассылки: https://your-site.com/unsubscribe?email={user.email}
"""

async def send_newsletter_to_user(user_id: int):
    try:
        from app.database import get_db
        db = next(get_db())
        
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            logger.warning(f"User not found: {user_id}")
            return
        
        events = get_events_for_user(db, user)
        if not events:
            logger.info(f"No events for user: {user.email}")
            return
        
        html_content = generate_newsletter_html(events, user)
        text_content = generate_newsletter_text(events, user)
        
        send_email_via_postmark(
            to_email=user.email,
            subject="🎉 Ваши персональные рекомендации событий",
            html_body=html_content,
            text_body=text_content,
            tag="newsletter"
        )
        
        logger.info(f"Newsletter sent to {user.email}")
        
    except Exception as e:
        logger.error(f"Error sending newsletter to user {user_id}: {str(e)}")

@router.get("/events-manager", response_class=HTMLResponse)
async def events_manager_page(
    request: Request,
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Страница управления событиями для админов"""
    return templates.TemplateResponse("events-manager.html", {"request": request})

@router.post("/newsletter/", response_model=Dict)
async def send_newsletter_to_all_users(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    username: str = Depends(get_current_admin)  # <--- Защита
):
    try:
        users = db.query(models.User).all()
        if not users:
            return {"status": "error", "message": "No users found"}
        
        for user in users:
            background_tasks.add_task(send_newsletter_to_user, user.id)
        
        return {
            "status": "started",
            "message": f"Started newsletter for {len(users)} users",
            "total_users": len(users),
            "note": "Emails are being sent in background"
        }
        
    except Exception as e:
        logger.error(f"Error starting newsletter: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting newsletter: {str(e)}")

@router.get("/newsletter/logs/", response_model=List[schemas.NewsletterLog])
def get_newsletter_logs(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    username: str = Depends(get_current_admin)  # <--- Защита
):
    logs = db.query(models.NewsletterLog).order_by(
        models.NewsletterLog.sent_at.desc()
    ).offset(skip).limit(limit).all()
    return logs

@router.post("/login", response_model=Token)
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    admin = db.query(AdminUser).filter(AdminUser.username == username).first()
    if not admin or not admin.check_password(password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": admin.username})
    response = JSONResponse({"access_token": access_token, "token_type": "bearer"})
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=86400,
        path="/"
    )
    return response

@router.post("/logout")
async def logout(response: Response):
    response.set_cookie(
        key="access_token",
        value="",
        httponly=True,
        max_age=1,
        path="/"
    )
    return {"status": "logged out"}

@router.put("/change-credentials")
async def change_admin_credentials(
    request: ChangeCredentialsRequest,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    admin = db.query(AdminUser).filter(AdminUser.username == current_admin).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    if not admin.check_password(request.current_password):
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    
    if request.new_username:
        existing = db.query(AdminUser).filter(AdminUser.username == request.new_username).first()
        if existing and existing.id != admin.id:
            raise HTTPException(status_code=400, detail="Username already exists")
        admin.username = request.new_username
    
    if request.new_password:
        admin.set_password(request.new_password)
    
    db.commit()
    return {"status": "success", "message": "Credentials updated"}

@router.post("/create-admin")
async def create_admin(
    request: AdminUserCreate,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)  # Только админ может создавать админов
):
    # Проверить что username не занят
    existing = db.query(AdminUser).filter(AdminUser.username == request.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Создать нового админа
    new_admin = AdminUser(username=request.username)
    new_admin.set_password(request.password)
    
    db.add(new_admin)
    db.commit()
    
    return {"status": "success", "message": f"Admin {request.username} created"}

@router.get("/count", response_model=EventCountResponse)
async def get_events_count(
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
) -> EventCountResponse:
    """Получение общего количества событий"""
    count = db.query(models.Event).count()
    return EventCountResponse(count=count)

@router.post("/get-users", response_model=list)
async def get_users_by_subscription_type(
    subscription_types: List[str] = Body([]),
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)  # Защита админским доступом
):
    if not subscription_types:
        return []
    
    # Получаем ID типов рассылки по их кодам
    type_ids = [
        t.id for t in db.query(models.SubscriptionType)
        .filter(models.SubscriptionType.code.in_(subscription_types))
        .all()
    ]
    if not type_ids:
        return []
    
    # Ищем пользователей, подписанных хотя бы на один из выбранных типов
    users = (
        db.query(models.User)
        .join(models.user_subscription_types)
        .filter(models.user_subscription_types.c.subscription_type_id.in_(type_ids))
        .distinct()
        .all()
    )
    return [{"id": user.id, "email": user.email} for user in users]

