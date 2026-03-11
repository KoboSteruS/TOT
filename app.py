import os
import json
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['JWT_SECRET'] = os.getenv('JWT_SECRET', 'jwt-secret-key')
app.config['ADMIN_TOKEN'] = os.getenv('ADMIN_TOKEN', 'admin-token')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}

# Пути к файлам данных
CONTENT_FILE = 'static/content.json'
FAQ_FILE = 'static/faq.json'


# Утилиты
def allowed_file(filename):
    """Проверка разрешённых расширений файлов"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def load_json(filepath):
    """Загрузка JSON файла"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def save_json(filepath, data):
    """Сохранение JSON файла"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving {filepath}: {e}")
        return False


def verify_jwt_token(token):
    """Проверка JWT токена"""
    try:
        payload = jwt.decode(token, app.config['JWT_SECRET'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def generate_jwt_token():
    """Генерация JWT токена для админа"""
    payload = {
        'admin': True,
        'exp': datetime.utcnow() + timedelta(days=30),  # Токен на 30 дней
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, app.config['JWT_SECRET'], algorithm='HS256')


# Декоратор для защиты API endpoints
def jwt_required(f):
    """Декоратор для проверки JWT токена в заголовках"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Токен отсутствует'}), 401
        
        if token.startswith('Bearer '):
            token = token[7:]
        
        payload = verify_jwt_token(token)
        if not payload:
            return jsonify({'error': 'Недействительный токен'}), 401
        
        return f(*args, **kwargs)
    return decorated


# ======================
# ПУБЛИЧНЫЕ РОУТЫ
# ======================

@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')


@app.route('/admin/<token>')
def admin_panel(token):
    """Вход в админ-панель через JWT токен в URL"""
    # Проверяем токен
    if token == app.config['ADMIN_TOKEN']:
        # Генерируем JWT для работы с API
        jwt_token = generate_jwt_token()
        return render_template('admin.html', jwt_token=jwt_token)
    else:
        return "Доступ запрещён", 403


# ======================
# API: КОНТЕНТ САЙТА
# ======================

@app.route('/api/content', methods=['GET'])
@jwt_required
def get_content():
    """Получение всего контента сайта"""
    content = load_json(CONTENT_FILE)
    return jsonify(content)


@app.route('/api/content', methods=['PUT'])
@jwt_required
def update_content():
    """Обновление контента сайта"""
    data = request.get_json()
    if save_json(CONTENT_FILE, data):
        return jsonify({'success': True, 'message': 'Контент обновлён'})
    return jsonify({'success': False, 'error': 'Ошибка сохранения'}), 500


@app.route('/api/content/<section>', methods=['GET'])
@jwt_required
def get_content_section(section):
    """Получение конкретной секции контента"""
    content = load_json(CONTENT_FILE)
    if section in content:
        return jsonify(content[section])
    return jsonify({'error': 'Секция не найдена'}), 404


@app.route('/api/content/<section>', methods=['PUT'])
@jwt_required
def update_content_section(section):
    """Обновление конкретной секции контента"""
    data = request.get_json()
    content = load_json(CONTENT_FILE)
    content[section] = data
    if save_json(CONTENT_FILE, content):
        return jsonify({'success': True, 'message': f'Секция {section} обновлена'})
    return jsonify({'success': False, 'error': 'Ошибка сохранения'}), 500


# ======================
# API: FAQ БОТА
# ======================

@app.route('/api/faq', methods=['GET'])
@jwt_required
def get_faq():
    """Получение всех FAQ"""
    faq_data = load_json(FAQ_FILE)
    return jsonify(faq_data)


@app.route('/api/faq', methods=['POST'])
@jwt_required
def add_faq():
    """Добавление нового FAQ"""
    new_faq = request.get_json()
    faq_data = load_json(FAQ_FILE)
    
    if 'faq' not in faq_data:
        faq_data['faq'] = []
    
    faq_data['faq'].append(new_faq)
    
    if save_json(FAQ_FILE, faq_data):
        return jsonify({'success': True, 'message': 'FAQ добавлен', 'faq': new_faq})
    return jsonify({'success': False, 'error': 'Ошибка сохранения'}), 500


@app.route('/api/faq/<int:index>', methods=['PUT'])
@jwt_required
def update_faq(index):
    """Обновление FAQ по индексу"""
    updated_faq = request.get_json()
    faq_data = load_json(FAQ_FILE)
    
    if 'faq' in faq_data and 0 <= index < len(faq_data['faq']):
        faq_data['faq'][index] = updated_faq
        if save_json(FAQ_FILE, faq_data):
            return jsonify({'success': True, 'message': 'FAQ обновлён'})
    
    return jsonify({'success': False, 'error': 'FAQ не найден'}), 404


@app.route('/api/faq/<int:index>', methods=['DELETE'])
@jwt_required
def delete_faq(index):
    """Удаление FAQ по индексу"""
    faq_data = load_json(FAQ_FILE)
    
    if 'faq' in faq_data and 0 <= index < len(faq_data['faq']):
        deleted = faq_data['faq'].pop(index)
        if save_json(FAQ_FILE, faq_data):
            return jsonify({'success': True, 'message': 'FAQ удалён', 'deleted': deleted})
    
    return jsonify({'success': False, 'error': 'FAQ не найден'}), 404


# ======================
# API: ЗАГРУЗКА ИЗОБРАЖЕНИЙ
# ======================

@app.route('/api/upload', methods=['POST'])
@jwt_required
def upload_image():
    """Загрузка изображения"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'Файл не найден'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Файл не выбран'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Добавляем timestamp для уникальности
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{timestamp}{ext}"
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Возвращаем относительный путь
        relative_path = f"/static/images/{filename}"
        return jsonify({
            'success': True,
            'message': 'Файл загружен',
            'url': relative_path,
            'filename': filename
        })
    
    return jsonify({'success': False, 'error': 'Недопустимый тип файла'}), 400


@app.route('/api/images', methods=['GET'])
@jwt_required
def list_images():
    """Список всех загруженных изображений"""
    images = []
    upload_folder = app.config['UPLOAD_FOLDER']
    
    if os.path.exists(upload_folder):
        for filename in os.listdir(upload_folder):
            if allowed_file(filename):
                images.append({
                    'filename': filename,
                    'url': f"/static/images/{filename}",
                    'size': os.path.getsize(os.path.join(upload_folder, filename))
                })
    
    return jsonify({'images': images})


@app.route('/api/images/<filename>', methods=['DELETE'])
@jwt_required
def delete_image(filename):
    """Удаление изображения"""
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
    
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            return jsonify({'success': True, 'message': 'Изображение удалено'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    return jsonify({'success': False, 'error': 'Файл не найден'}), 404


# ======================
# УТИЛИТНЫЕ РОУТЫ
# ======================

@app.route('/api/generate-token')
def generate_token():
    """Генерация нового админ токена (только для разработки!)"""
    if app.config['FLASK_ENV'] == 'development':
        token = generate_jwt_token()
        admin_url = f"/admin/{app.config['ADMIN_TOKEN']}"
        return jsonify({
            'admin_url': admin_url,
            'jwt_token': token,
            'note': 'Используйте admin_url для входа, jwt_token будет выдан автоматически'
        })
    return jsonify({'error': 'Доступно только в режиме разработки'}), 403


if __name__ == '__main__':
    # Создаём папку для загрузок, если её нет
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    print("=" * 50)
    print("ООО «ТОТ» - Админ-панель запущена!")
    print("=" * 50)
    print(f"URL админки: http://localhost:5000/admin/{app.config['ADMIN_TOKEN']}")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
