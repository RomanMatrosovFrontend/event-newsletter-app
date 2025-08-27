from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from app.core.config import settings

class TemplateService:
    def __init__(self):
        self.template_dir = Path(__file__).parent.parent / "templates" / "emails"
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
    
    def render_newsletter_template(self, user, events, **kwargs):
        """Рендер шаблона рассылки для пользователя"""
        template = self.env.get_template("newsletter.html")
        
        context = {
            "user": user,
            "events": events,
            "unsubscribe_url": f"{settings.BASE_URL}/api/unsubscribe/{user.id}",
            **kwargs
        }
        
        return template.render(context)

# Создаем папку для шаблонов
template_service = TemplateService()