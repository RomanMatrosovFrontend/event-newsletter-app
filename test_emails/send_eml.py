import smtplib

# Параметры Яндекс.Почты
SMTP_HOST = 'smtp.yandex.ru'
SMTP_PORT = 587
USER = 'roman.matrosov.frontend@yandex.ru'          # замените на ваш логин
PASS = 'walwwrlialdfboay'  # если включено двухфакторная авторизация, используйте пароль приложения

# Читаем содержимое .eml-файла
with open('crazy98life@gmail.com_20250920_123638.eml', 'rb') as f:
    raw_email = f.read()

# Устанавливаем соединение с SMTP-сервером
server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
server.starttls()               # инициируем защищённое соединение
server.login(USER, PASS)        # авторизуемся

# Отправляем письмо самому себе
server.sendmail(USER, USER, raw_email)

# Закрываем соединение
server.quit()

print("Письмо отправлено на ваш ящик и скоро будет доступно в Яндекс.Почте")

