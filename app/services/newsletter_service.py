import logging
from sqlalchemy.orm import Session
from typing import List
from app.models import User, NewsletterLog
from app.utils.event_matcher import get_events_for_user
from app.services.email_service import send_email_via_postmark
from app.services.template_service import template_service

logger = logging.getLogger(__name__)

def send_newsletter_to_all_users(db: Session):
    """
    Основная функция для отправки рассылки всем пользователям
    """
    import time  # Добавляем импорт для замера времени
    start_time = time.time()  # Засекаем время начала

    logger.info("🎯 Starting newsletter campaign...")
    try:
        # 1. Получаем всех подписанных пользователей
        users = db.query(User).filter(User.is_subscribed == True).all()
        total_users = len(users)
        logger.info(f"📋 Found {total_users} subscribed users.")

        successful = 0
        failed = 0

        # 2. Для каждого пользователя...
        for user in users:
            logger.info(f"   👤 Processing user: {user.email} (ID: {user.id})")
            try:
                # 2.1. Находим подходящие события
                events = get_events_for_user(db, user)
                logger.info(f"      ✅ Found {len(events)} events for user.")

                if events:
                    # 2.2. Здесь будет логика генерации и отправки письма
                    # Пока просто логируем, но это означает, что для этого пользователя есть что отправлять!
                    subject = f"Анонс мероприятий для вас!"
                    # Пока используем простой текст для теста
                    html_body = f"<h1>Привет!</h1><p>Для вас найдено {len(events)} мероприятий.</p>"
                    html_body += "<ul>"
                    for event in events:
                        html_body += f"<li><a href='{event.url}'>{event.title}</a> ({event.dates})</li>"
                    html_body += "</ul>"

                    # 2.3. ВЫЗОВ РЕАЛЬНОЙ ФУНКЦИИ ОТПРАВКИ!
                    logger.info(f"      📤 Attempting to send email to {user.email}...")
                    email_sent = send_email_via_postmark(
                        to_email=user.email,
                        subject=subject,
                        html_body=html_body
                    )

                    if email_sent:
                        logger.info(f"      📩 Email successfully sent to {user.email}")
                        successful += 1
                    else:
                        logger.error(f"      ❌ Failed to send email to {user.email}")
                        failed += 1
                else:
                    logger.info(f"      ℹ️  No events for user {user.email}. Skipping.")
                    successful += 1  # Не считать пропуск из-за отсутствия событий за ошибку

            except Exception as e:
                failed += 1
                logger.error(f"      ⚠️  Failed to process user {user.email}: {str(e)}")
                # Продолжаем обработку для остальных пользователей
                continue

        # 3. Считаем общее время выполнения
        duration_seconds = time.time() - start_time

        # 4. Сохраняем статистику
        log = NewsletterLog(
            total_users=total_users,
            successful_sends=successful,
            failed_sends=failed,
            duration_seconds=duration_seconds  # Теперь здесь число!
        )
        db.add(log)
        db.commit()
        logger.info(f"📊 Newsletter finished! Success: {successful}, Failed: {failed}, Duration: {duration_seconds:.2f}s")

        return successful, failed

    except Exception as e:
        logger.error(f"💥 Critical error in newsletter service: {str(e)}")
        return 0, 0

def send_newsletter_to_users(db: Session, user_ids: List[int]):
    """
    Отправляет рассылку только указанным пользователям
    """
    import time
    start_time = time.time()

    logger.info(f"🎯 Starting targeted newsletter for {len(user_ids)} users...")
    
    successful = 0
    failed = 0

    for user_id in user_ids:
        try:
            user = db.query(User).filter(User.id == user_id, User.is_subscribed == True).first()
            if not user:
                logger.warning(f"User {user_id} not found or unsubscribed")
                continue

            events = get_events_for_user(db, user)
            logger.info(f"   ✅ Found {len(events)} events for user {user.email}")

            if events:
                subject = f"Анонс мероприятий для вас!"
                html_body = f"<h1>Привет!</h1><p>Для вас найдено {len(events)} мероприятий.</p>"
                html_body += "<ul>"
                for event in events:
                    html_body += f"<li><a href='{event.url}'>{event.title}</a> ({event.dates})</li>"
                html_body += "</ul>"

                email_sent = send_email_via_postmark(
                    to_email=user.email,
                    subject=subject,
                    html_body=html_body
                )

                if email_sent:
                    successful += 1
                else:
                    failed += 1
            else:
                logger.info(f"      ℹ️  No events for user {user.email}. Skipping.")
                successful += 1

        except Exception as e:
            failed += 1
            logger.error(f"      ⚠️  Failed to process user {user_id}: {str(e)}")
            continue

    duration_seconds = time.time() - start_time
    logger.info(f"📊 Targeted newsletter finished! Success: {successful}, Failed: {failed}")
    
    return successful, failed