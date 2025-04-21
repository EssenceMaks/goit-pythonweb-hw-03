import asyncio
import json
import logging
import pathlib
import datetime
import aiohttp
from aiohttp import web
import aiohttp_jinja2
import jinja2

# Налаштування логування
logging.basicConfig(level=logging.INFO)

# Шляхи до файлів
BASE_DIR = pathlib.Path(__file__).parent
STATIC_DIR = BASE_DIR / 'styles'
TEMPLATES_DIR = BASE_DIR / 'templates'
STORAGE_DIR = BASE_DIR / 'storage'
DATA_FILE = STORAGE_DIR / 'data.json'

# Ініціалізація даних, якщо файл порожній
def init_data_file():
    if not STORAGE_DIR.exists():
        STORAGE_DIR.mkdir(exist_ok=True)
        
    if not DATA_FILE.exists() or DATA_FILE.stat().st_size == 0:
        with open(DATA_FILE, 'w') as fd:
            json.dump({}, fd)

# Глобальний обробник помилок 404
@aiohttp_jinja2.template('error.html')
async def handle_404(request):
    return {"active_page": "none"}

# Маршрути та обробники
routes = web.RouteTableDef()

# Головна сторінка
@routes.get('/')
@aiohttp_jinja2.template('index.html')
async def index(request):
    return {"active_page": "home"}

# Сторінка з повідомленням
@routes.get('/message.html')
@aiohttp_jinja2.template('message.html')
async def message_get(request):
    return {"active_page": "message"}

# Обробка форми
@routes.post('/message')
async def message_post(request):
    data = await request.post()
    username = data.get('username')
    message = data.get('message')
    
    # Валідація вхідних даних
    if not username or not username.strip():
        return web.Response(text="Ім'я користувача не може бути порожнім", status=400)
    
    if not message or not message.strip():
        return web.Response(text="Повідомлення не може бути порожнім", status=400)
    
    timestamp = datetime.datetime.now().isoformat()
    
    # Завантаження поточних даних
    with open(DATA_FILE, 'r') as fd:
        storage_data = json.load(fd)
    
    # Додавання нового повідомлення
    storage_data[timestamp] = {
        "username": username,
        "message": message
    }
    
    # Збереження оновлених даних
    with open(DATA_FILE, 'w') as fd:
        json.dump(storage_data, fd, indent=2)
    
    # Перенаправлення на сторінку читання повідомлень
    return web.HTTPFound('/read')

# Читання повідомлень через шаблон Jinja2
@routes.get('/read')
@aiohttp_jinja2.template('read.html')
async def read_messages(request):
    with open(DATA_FILE, 'r') as fd:
        storage_data = json.load(fd)
    
    return {"messages": storage_data, "active_page": "read"}

# Обробка статичних файлів
@routes.get('/styles/style.css')
async def styles(request):
    return web.FileResponse(STATIC_DIR / 'style.css')

@routes.get('/styles/logo.png')
async def logo(request):
    return web.FileResponse(STATIC_DIR / 'logo.png')

async def init_app():
    # Ініціалізація додатку
    app = web.Application()
    
    # Налаштування шаблонізатора Jinja2
    aiohttp_jinja2.setup(
        app,
        loader=jinja2.FileSystemLoader([str(BASE_DIR), str(TEMPLATES_DIR)])
    )
    
    # Реєстрація маршрутів
    app.add_routes(routes)
    
    # Додаємо глобальний обробник 404 помилок через middleware
    @web.middleware
    async def error_middleware(request, handler):
        try:
            return await handler(request)
        except web.HTTPNotFound:
            return await handle_404(request)
    
    # Застосовуємо middleware до додатку
    app.middlewares.append(error_middleware)
    
    # Ініціалізація файлу даних
    init_data_file()
    
    return app

def main():
    # Запуск додатку
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(init_app())
    web.run_app(app, host='0.0.0.0', port=3000)

if __name__ == '__main__':
    main()