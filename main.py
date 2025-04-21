import asyncio
import json
import logging
import pathlib
import datetime
import aiohttp
from aiohttp import web
import aiohttp_jinja2
import jinja2

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Пути к файлам
BASE_DIR = pathlib.Path(__file__).parent
STATIC_DIR = BASE_DIR
STORAGE_DIR = BASE_DIR / 'storage'
DATA_FILE = STORAGE_DIR / 'data.json'

# Инициализация данных, если файл пустой
def init_data_file():
    if not STORAGE_DIR.exists():
        STORAGE_DIR.mkdir(exist_ok=True)
        
    if not DATA_FILE.exists() or DATA_FILE.stat().st_size == 0:
        with open(DATA_FILE, 'w') as fd:
            json.dump({}, fd)

# Глобальный обработчик ошибок 404
async def handle_404(request):
    return web.FileResponse(BASE_DIR / 'error.html', status=404)

# Маршруты и обработчики
routes = web.RouteTableDef()

# Главная страница
@routes.get('/')
async def index(request):
    return web.FileResponse(BASE_DIR / 'index.html')

# Страница с сообщением
@routes.get('/message.html')
async def message_get(request):
    return web.FileResponse(BASE_DIR / 'message.html')

# Обработка формы
@routes.post('/message')
async def message_post(request):
    data = await request.post()
    username = data.get('username')
    message = data.get('message')
    
    # Валидация входных данных
    if not username or not username.strip():
        return web.Response(text="Имя пользователя не может быть пустым", status=400)
    
    if not message or not message.strip():
        return web.Response(text="Сообщение не может быть пустым", status=400)
    
    timestamp = datetime.datetime.now().isoformat()
    
    # Загрузка текущих данных
    with open(DATA_FILE, 'r') as fd:
        storage_data = json.load(fd)
    
    # Добавление нового сообщения
    storage_data[timestamp] = {
        "username": username,
        "message": message
    }
    
    # Сохранение обновленных данных
    with open(DATA_FILE, 'w') as fd:
        json.dump(storage_data, fd, indent=2)
    
    # Перенаправление на страницу чтения сообщений
    return web.HTTPFound('/read')

# Чтение сообщений через шаблон Jinja2
@routes.get('/read')
@aiohttp_jinja2.template('read.html')
async def read_messages(request):
    with open(DATA_FILE, 'r') as fd:
        storage_data = json.load(fd)
    
    return {"messages": storage_data}

# Обработка статических файлов
@routes.get('/style.css')
async def styles(request):
    return web.FileResponse(BASE_DIR / 'style.css')

@routes.get('/logo.png')
async def logo(request):
    return web.FileResponse(BASE_DIR / 'logo.png')

# Обработка всех остальных GET маршрутов - устарело и заменено на middleware
@routes.get('/{name}')
async def error_handler(request):
    name = request.match_info.get('name', '')
    if name not in ['', 'index.html', 'message.html', 'style.css', 'logo.png', 'read']:
        return web.FileResponse(BASE_DIR / 'error.html', status=404)
    raise web.HTTPNotFound()

async def init_app():
    # Инициализация приложения
    app = web.Application()
    
    # Настройка шаблонизатора Jinja2
    aiohttp_jinja2.setup(
        app,
        loader=jinja2.FileSystemLoader(str(BASE_DIR))
    )
    
    # Регистрация маршрутов
    app.add_routes(routes)
    
    # Добавляем глобальный обработчик 404 ошибок через middleware
    @web.middleware
    async def error_middleware(request, handler):
        try:
            return await handler(request)
        except web.HTTPNotFound:
            return await handle_404(request)
    
    # Применяем middleware к приложению
    app.middlewares.append(error_middleware)
    
    # Инициализация файла данных
    init_data_file()
    
    return app

def main():
    # Запуск приложения
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(init_app())
    web.run_app(app, host='0.0.0.0', port=3000)

if __name__ == '__main__':
    main()