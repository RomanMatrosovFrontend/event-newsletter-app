from typing import Dict, Optional, List
from app import schemas

def parse_csv_row(row: Dict) -> Optional[schemas.EventCreate]:
    """
    Парсит строку CSV с разделителем ; и multiple values в ячейках
    """
    try:
        # Debug: выведем все ключи для проверки
        print("Available keys:", list(row.keys()))
        
        # Извлекаем характеристики
        characteristics = {}
        for key, value in row.items():
            key_str = str(key).strip().strip('"')
            if key_str.startswith('Characteristics:'):
                char_name = key_str.replace('Characteristics:', '').strip()
                characteristics[char_name] = str(value) if value is not None else ''
        
        # Получаем основные поля (обрабатываем возможные названия с кавычками)
        title = str(row.get('Title', row.get('"Title"', ''))).strip().strip('"')
        url = str(row.get('Url', row.get('"Url"', ''))).strip().strip('"')
        mark = str(row.get('Mark', row.get('"Mark"', ''))).strip().strip('"')
        category = str(row.get('Category', row.get('"Category"', ''))).strip().strip('"')
        description = str(row.get('Description', row.get('"Description"', ''))).strip().strip('"')
        photo = str(row.get('Photo', row.get('"Photo"', ''))).strip().strip('"')
        
        # Проверяем обязательные поля
        if not title or not url or title == 'None' or url == 'None':
            print(f"Skipping row - missing title or url: title='{title}', url='{url}'")
            return None

        # Обрабатываем категории (разделены ;)
        categories_list = []
        if category and category != 'None':
            if ';' in category:
                categories_list = [cat.strip() for cat in category.split(';') if cat.strip()]
            else:
                categories_list = [category]

        # Обрабатываем даты
        dates_str = characteristics.get('Дата', '').strip().strip('"')
        dates = []
        if dates_str and dates_str != 'None':
            # Убираем возможные скобки и текст в них "08.24 (24 августа)" -> "24 августа"
            clean_date = dates_str.split('(')[-1].replace(')', '').strip() if '(' in dates_str else dates_str
            dates = [clean_date]

        # Обрабатываем языки (приоритет: Язык мероприятия -> Language)
        languages_str = characteristics.get('Язык мероприятия', '').strip().strip('"') 
        if not languages_str or languages_str == 'None':
            languages_str = characteristics.get('Language', '').strip().strip('"')
        
        languages = []
        if languages_str and languages_str != 'None':
            if ';' in languages_str:
                languages = [lang.strip() for lang in languages_str.split(';') if lang.strip()]
            else:
                languages = [languages_str]

        # Обрабатываем город (приоритет: Город -> City)
        city = characteristics.get('Город', '').strip().strip('"')
        if not city or city == 'None':
            city = characteristics.get('City', '').strip().strip('"')

        # Обрабатываем возраст (приоритет: Возраст -> Age)
        age_restriction = characteristics.get('Возраст', '').strip().strip('"')
        if not age_restriction or age_restriction == 'None':
            age_restriction = characteristics.get('Age', '').strip().strip('"')

        print(f"Parsed: title='{title}', dates={dates}, languages={languages}, city='{city}'")
        
        return schemas.EventCreate(
            mark=mark if mark != 'None' else None,
            category=category if category != 'None' else None,
            title=title,
            description=description if description != 'None' else None,
            text=None,  # В вашем примере Text всегда пустой
            photo=photo if photo != 'None' else None,
            dates=dates,
            languages=languages,
            age_restriction=age_restriction if age_restriction != 'None' else None,
            city=city if city != 'None' else None,
            url=url
        )
        
    except Exception as e:
        print(f"Error parsing row: {e}")
        import traceback
        traceback.print_exc()
        return None