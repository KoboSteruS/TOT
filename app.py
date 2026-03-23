import os
import json
import jwt
import threading
import time
import ssl
from datetime import datetime, timedelta
from functools import wraps
from urllib import request as urlrequest, parse as urlparse
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.exceptions import HTTPException
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['JWT_SECRET'] = os.getenv('JWT_SECRET', 'jwt-secret-key')
app.config['ADMIN_TOKEN'] = os.getenv('ADMIN_TOKEN', 'admin-token')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['ALLOWED_EXTENSIONS'] = {
    'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg',
    'bmp', 'tif', 'tiff', 'heic', 'heif', 'avif', 'jfif'
}


MIMETYPE_TO_EXT = {
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/gif': '.gif',
    'image/webp': '.webp',
    'image/svg+xml': '.svg',
    'image/bmp': '.bmp',
    'image/tiff': '.tiff',
    'image/heic': '.heic',
    'image/heif': '.heif',
    'image/avif': '.avif',
}


@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(_e):
    """Единый JSON-ответ для слишком больших файлов."""
    return jsonify({
        'success': False,
        'error': 'Файл слишком большой. Максимум 16MB.'
    }), 413


@app.errorhandler(Exception)
def handle_api_exceptions(e):
    """Для API всегда возвращаем JSON, а не HTML-страницы ошибок."""
    if request.path.startswith('/api/'):
        if isinstance(e, HTTPException):
            status = e.code or 500
            message = e.description or 'Ошибка запроса'
        else:
            status = 500
            message = 'Внутренняя ошибка сервера'
            print(f'[API] Unhandled exception on {request.path}: {e}')

        return jsonify({
            'success': False,
            'error': message
        }), status

    # Для не-API маршрутов оставляем стандартное поведение.
    if isinstance(e, HTTPException):
        return e
    raise e

# Пути к файлам данных
CONTENT_FILE = 'static/content.json'
FAQ_FILE = 'static/faq.json'
CERTIFICATES_FILE = 'static/certificates.json'
DATA_FOLDER = 'data'
TELEGRAM_CHATS_FILE = 'static/telegram_chats.json'

# Разрешённые файлы для скачивания (slug -> (имя файла, имя для скачивания))
DOWNLOAD_FILES = {
    'requisites': ('Реквизиты-ТОТ (1).doc', 'Реквизиты-ООО-ТОТ.doc'),
    'vedomost': ('Svodnaya_vedomost_provedenia_spetsotsenki_ot_18_10_2018.pdf', 'Ведомость-спецоценки-ТОТ.pdf'),
}


# Утилиты
def allowed_file(file_or_name):
    """Проверка, что это изображение.

    Поддерживаем как filename-строку, так и FileStorage.
    Для устойчивости сначала доверяем mimetype (если он image/*),
    затем fallback на расширение файла.
    """
    if hasattr(file_or_name, 'mimetype'):
        mimetype = (getattr(file_or_name, 'mimetype', '') or '').lower()
        if mimetype.startswith('image/'):
            return True

        filename = getattr(file_or_name, 'filename', '') or ''
    else:
        filename = str(file_or_name or '')

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


def deep_merge_dict(base, patch):
    """Рекурсивное объединение словарей без потери существующих ключей."""
    if not isinstance(base, dict) or not isinstance(patch, dict):
        return patch

    result = dict(base)
    for key, value in patch.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dict(result[key], value)
        else:
            result[key] = value
    return result


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


def _load_telegram_chat_ids() -> list[str]:
    """Загрузка chat_id из локального файла."""
    data = load_json(TELEGRAM_CHATS_FILE) or {}
    return [str(cid) for cid in data.get('chat_ids', [])]


def _save_telegram_chat_ids(chat_ids: list[str]) -> None:
    """Сохранение chat_id в локальный файл."""
    data = {'chat_ids': sorted({str(cid) for cid in chat_ids})}
    save_json(TELEGRAM_CHATS_FILE, data)


def _fetch_chat_ids_from_updates(token: str) -> list[str]:
    """Пробегаемся по getUpdates и вытаскиваем все chat_id, которые писали боту (fallback)."""
    api_url = f'https://api.telegram.org/bot{token}/getUpdates'
    try:
        with urlrequest.urlopen(api_url, timeout=10) as resp:
            if resp.status != 200:
                print(f'[Telegram] getUpdates status={resp.status}')
                return []
            payload = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f'[Telegram] getUpdates error: {e}')
        return []

    result = payload.get('result', [])
    chat_ids_all: set[str] = set()
    chat_ids_start: set[str] = set()

    for update in result:
        message = update.get('message') or update.get('channel_post')
        if not message:
            continue
        chat = message.get('chat') or {}
        cid = chat.get('id')
        if cid is None:
            continue
        cid_str = str(cid)
        chat_ids_all.add(cid_str)
        text = (message.get('text') or '').strip()
        if text.startswith('/start'):
            chat_ids_start.add(cid_str)

    # Если есть /start — используем их, иначе все найденные
    return sorted(chat_ids_start or chat_ids_all)


def _get_telegram_token_from_content() -> str | None:
    """Возвращает токен Telegram из content.json или .env."""
    content = load_json(CONTENT_FILE)
    notifications = content.get('notifications', {})
    token = notifications.get('telegram_bot_token') or os.getenv('TELEGRAM_BOT_TOKEN')
    return token or None


def telegram_bot_loop():
    """Фоновый поток: опрашивает getUpdates и реагирует на /start.

    При /start:
    - сохраняет chat_id в локальный файл
    - отправляет пользователю сообщение, что chat_id зарегистрирован
    """
    token = _get_telegram_token_from_content()
    if not token:
        print('[Telegram] токен не задан, бот не запущен')
        return

    print('[Telegram] бот запущен в режиме long polling')
    api_url = f'https://api.telegram.org/bot{token}'
    offset = 0

    while True:
        try:
            url = f'{api_url}/getUpdates?timeout=25&offset={offset}'
            with urlrequest.urlopen(url, timeout=30) as resp:
                if resp.status != 200:
                    time.sleep(5)
                    continue
                payload = json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            print(f'[Telegram] getUpdates error: {e}')
            time.sleep(5)
            continue

        for update in payload.get('result', []):
            offset = max(offset, update.get('update_id', 0) + 1)
            message = update.get('message') or update.get('channel_post')
            if not message:
                continue
            chat = message.get('chat') or {}
            cid = chat.get('id')
            if cid is None:
                continue

            text = (message.get('text') or '').strip()
            if text.startswith('/start'):
                cid_str = str(cid)
                current = _load_telegram_chat_ids()
                if cid_str not in current:
                    current.append(cid_str)
                    _save_telegram_chat_ids(current)
                    print(f'[Telegram] зарегистрирован chat_id={cid_str}')

                welcome_text = (
                    '👋 Здравствуйте!\n\n'
                    'Ваш chat_id зарегистрирован. Теперь заявки с формы на сайте ООО «ТОТ» '
                    'будут приходить в этот чат.'
                )
                payload_send = {
                    'chat_id': cid_str,
                    'text': welcome_text,
                }
                data = urlparse.urlencode(payload_send).encode('utf-8')
                req = urlrequest.Request(f'{api_url}/sendMessage', data=data, method='POST')
                try:
                    with urlrequest.urlopen(req, timeout=10) as resp:
                        if resp.status != 200:
                            print(f'[Telegram] ошибка отправки приветствия: {resp.status}')
                except Exception as e:
                    print(f'[Telegram] ошибка отправки приветствия: {e}')

        # небольшая пауза между циклами, чтобы не крутить впустую
        time.sleep(1)


def send_lead_to_telegram(name: str, phone: str, business_type: str, comment: str) -> tuple[bool, str | None]:
    """Отправка заявки из формы в Telegram-бота.

    Токен бота и chat_id читаются из блока notifications в content.json
    """
    content = load_json(CONTENT_FILE)
    notifications = content.get('notifications', {})
    token = notifications.get('telegram_bot_token') or os.getenv('TELEGRAM_BOT_TOKEN')
    explicit_chat_id = notifications.get('telegram_chat_id') or os.getenv('TELEGRAM_CHAT_ID')

    if not token:
        return False, 'Не настроен токен бота'

    # Список чатов: все, кто писал боту + явный chat_id (если указан)
    chat_ids: list[str] = _load_telegram_chat_ids()
    if explicit_chat_id:
        chat_ids.append(str(explicit_chat_id))
        chat_ids = list(dict.fromkeys(chat_ids))  # dedupe, preserve order

    # Если ещё ни одного chat_id не знаем — попробуем вытащить их через getUpdates
    if not chat_ids:
        fetched = _fetch_chat_ids_from_updates(token)
        if fetched:
            chat_ids.extend(fetched)
            _save_telegram_chat_ids(chat_ids)

    if not chat_ids:
        return False, 'Нет ни одного получателя (chat_id). Напишите боту /start и повторите отправку.'

    text_lines = [
        '🆕 <b>Новая заявка с сайта ООО «ТОТ»</b>',
        '',
        f'👤 Имя: <b>{name}</b>',
        f'📞 Телефон: <b>{phone}</b>',
    ]
    if business_type:
        text_lines.append(f'🏢 Форма бизнеса: <b>{business_type}</b>')
    if comment:
        text_lines.append('')
        text_lines.append(f'💬 Комментарий:\n{comment}')

    text = '\n'.join(text_lines)

    api_url = f'https://api.telegram.org/bot{token}/sendMessage'
    errors: list[str] = []

    for cid in chat_ids:
        payload = {
            'chat_id': cid,
            'text': text,
            'parse_mode': 'HTML',
        }

        data = urlparse.urlencode(payload).encode('utf-8')
        req = urlrequest.Request(api_url, data=data, method='POST')
        try:
            with urlrequest.urlopen(req, timeout=10) as resp:
                if resp.status != 200:
                    err = f'Ошибка Telegram API для chat_id={cid}: {resp.status}'
                    print(err)
                    errors.append(err)
        except Exception as e:
            err = f'Ошибка отправки для chat_id={cid}: {e}'
            print(err)
            errors.append(str(e))

    if errors and len(errors) == len(chat_ids):
        # Не удалось отправить ни в один чат
        return False, '; '.join(errors[:3])

    return True, None


def send_lead_to_vk(name: str, phone: str, business_type: str, comment: str) -> tuple[bool, str | None]:
    """Отправка заявки админам ВКонтакте через messages.send."""
    content = load_json(CONTENT_FILE)
    notifications = content.get('notifications', {})

    vk_token = notifications.get('vk_api_token') or os.getenv('VK_API_TOKEN')
    vk_admin_ids = notifications.get('vk_admin_ids') or os.getenv('VK_ADMIN_IDS', '')

    if not vk_token:
        return False, 'Не настроен VK API токен'

    # Разрешаем как массив, так и строку с ID через запятую
    if isinstance(vk_admin_ids, list):
        admin_ids = [str(x).strip() for x in vk_admin_ids if str(x).strip()]
    else:
        admin_ids = [x.strip() for x in str(vk_admin_ids).split(',') if x.strip()]

    if not admin_ids:
        return False, 'Не настроены VK admin IDs'

    lines = [
        'Новая заявка с сайта ООО «ТОТ»',
        '',
        f'Имя: {name}',
        f'Телефон: {phone}',
    ]
    if business_type:
        lines.append(f'Форма бизнеса: {business_type}')
    if comment:
        lines.extend(['', f'Комментарий: {comment}'])
    message = '\n'.join(lines)

    errors: list[str] = []
    vk_api_url = 'https://api.vk.com/method/messages.send'

    for idx, user_id in enumerate(admin_ids):
        payload = {
            'access_token': vk_token,
            'v': '5.199',
            'user_id': user_id,
            'random_id': int(time.time()) + idx,
            'message': message,
        }
        data = urlparse.urlencode(payload).encode('utf-8')
        req = urlrequest.Request(vk_api_url, data=data, method='POST')

        try:
            with urlrequest.urlopen(req, timeout=12) as resp:
                raw = resp.read().decode('utf-8')
                body = json.loads(raw)
                if 'error' in body:
                    vk_err = body['error']
                    err_msg = f"VK error user_id={user_id}: {vk_err.get('error_msg', 'unknown')}"
                    print(f"[VK] {err_msg}")
                    errors.append(err_msg)
        except Exception as e:
            # Частая проблема на Windows/корпоративных сетях: self-signed cert в цепочке.
            # Для VK делаем безопасный fallback: повтор с unverified SSL контекстом только
            # если стандартная валидация сертификата провалилась.
            if 'CERTIFICATE_VERIFY_FAILED' in str(e):
                try:
                    insecure_ctx = ssl._create_unverified_context()
                    with urlrequest.urlopen(req, timeout=12, context=insecure_ctx) as resp:
                        raw = resp.read().decode('utf-8')
                        body = json.loads(raw)
                        if 'error' in body:
                            vk_err = body['error']
                            err_msg = f"VK error user_id={user_id}: {vk_err.get('error_msg', 'unknown')}"
                            print(f"[VK] {err_msg}")
                            errors.append(err_msg)
                        else:
                            print(f"[VK] delivered (SSL fallback) user_id={user_id}")
                    continue
                except Exception as fallback_err:
                    err_msg = f'VK send failed user_id={user_id} (ssl fallback): {fallback_err}'
                    print(f"[VK] {err_msg}")
                    errors.append(err_msg)
                    continue

            err_msg = f'VK send failed user_id={user_id}: {e}'
            print(f"[VK] {err_msg}")
            errors.append(err_msg)

    if errors and len(errors) == len(admin_ids):
        return False, '; '.join(errors[:2])
    return True, None


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


@app.route('/privacy')
def privacy():
    """Страница политики конфиденциальности"""
    return render_template('privacy.html')


@app.route('/download/<slug>')
def download_file(slug):
    """Скачивание файла из папки data (безопасный список)"""
    if slug not in DOWNLOAD_FILES:
        return "Файл не найден", 404
    filename, download_as = DOWNLOAD_FILES[slug]
    filepath = os.path.join(DATA_FOLDER, filename)
    if not os.path.isfile(filepath):
        return "Файл не найден", 404
    return send_from_directory(
        DATA_FOLDER,
        filename,
        as_attachment=True,
        download_name=download_as
    )


@app.route('/api/public-content', methods=['GET'])
def get_public_content():
    """Публичный контент сайта (без авторизации)."""
    return jsonify(load_json(CONTENT_FILE))


@app.route('/telegram/webhook', methods=['POST'])
def telegram_webhook():
    """Webhook для Telegram‑бота: сохраняем chat_id всех, кто написал боту."""
    update = request.get_json() or {}
    message = update.get('message') or update.get('channel_post')
    if not message:
        return jsonify({'ok': True})

    chat = message.get('chat') or {}
    chat_id = chat.get('id')
    if not chat_id:
        return jsonify({'ok': True})

    chats_path = 'static/telegram_chats.json'
    data = load_json(chats_path) or {}
    ids = set(str(cid) for cid in data.get('chat_ids', []))
    ids.add(str(chat_id))
    data['chat_ids'] = sorted(ids)
    if save_json(chats_path, data):
        print(f"[Telegram] зарегистрирован chat_id={chat_id}")
    else:
        print(f"[Telegram] не удалось сохранить chat_id={chat_id}")

    return jsonify({'ok': True})


@app.route('/api/lead', methods=['POST'])
def submit_lead():
    """Приём заявки с формы и отправка в Telegram и VK"""
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    phone = (data.get('phone') or '').strip()
    business_type = (data.get('business_type') or '').strip()
    comment = (data.get('comment') or '').strip()

    if not name or not phone:
        return jsonify({'success': False, 'error': 'Имя и телефон обязательны'}), 400

    tg_ok, tg_error = send_lead_to_telegram(name, phone, business_type, comment)
    vk_ok, vk_error = send_lead_to_vk(name, phone, business_type, comment)

    if not tg_ok:
        print(f'[Telegram] lead send error: {tg_error}')
    if not vk_ok:
        print(f'[VK] lead send error: {vk_error}')

    if not tg_ok and not vk_ok:
        return jsonify({
            'success': False,
            'error': f'Не удалось отправить заявку. Telegram: {tg_error or "ошибка"}, VK: {vk_error or "ошибка"}'
        }), 500

    return jsonify({'success': True})


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
    data = request.get_json() or {}
    current_content = load_json(CONTENT_FILE)
    merged_content = deep_merge_dict(current_content, data)
    if save_json(CONTENT_FILE, merged_content):
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
# API: СЕРТИФИКАТЫ
# ======================

@app.route('/api/certificates', methods=['GET'])
def get_certificates():
    """Получение всех сертификатов (публично для вывода на сайте)."""
    cert_data = load_json(CERTIFICATES_FILE)
    return jsonify(cert_data)


@app.route('/api/certificates', methods=['POST'])
@jwt_required
def add_certificate():
    """Добавление нового сертификата"""
    new_cert = request.get_json()
    cert_data = load_json(CERTIFICATES_FILE)
    
    if 'certificates' not in cert_data:
        cert_data['certificates'] = []
    
    # Генерируем ID если не указан
    if 'id' not in new_cert:
        import uuid
        new_cert['id'] = f"cert-{uuid.uuid4().hex[:8]}"
    
    cert_data['certificates'].append(new_cert)
    
    if save_json(CERTIFICATES_FILE, cert_data):
        return jsonify({'success': True, 'message': 'Сертификат добавлен', 'certificate': new_cert})
    return jsonify({'success': False, 'error': 'Ошибка сохранения'}), 500


@app.route('/api/certificates/<cert_id>', methods=['PUT'])
@jwt_required
def update_certificate(cert_id):
    """Обновление сертификата по ID"""
    updated_cert = request.get_json()
    cert_data = load_json(CERTIFICATES_FILE)
    
    if 'certificates' in cert_data:
        for i, cert in enumerate(cert_data['certificates']):
            if cert.get('id') == cert_id:
                cert_data['certificates'][i] = updated_cert
                if save_json(CERTIFICATES_FILE, cert_data):
                    return jsonify({'success': True, 'message': 'Сертификат обновлён'})
    
    return jsonify({'success': False, 'error': 'Сертификат не найден'}), 404


@app.route('/api/certificates/<cert_id>', methods=['DELETE'])
@jwt_required
def delete_certificate(cert_id):
    """Удаление сертификата по ID"""
    cert_data = load_json(CERTIFICATES_FILE)
    
    if 'certificates' in cert_data:
        for i, cert in enumerate(cert_data['certificates']):
            if cert.get('id') == cert_id:
                deleted = cert_data['certificates'].pop(i)
                if save_json(CERTIFICATES_FILE, cert_data):
                    return jsonify({'success': True, 'message': 'Сертификат удалён', 'deleted': deleted})
    
    return jsonify({'success': False, 'error': 'Сертификат не найден'}), 404


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

    if not (file and allowed_file(file)):
        return jsonify({'success': False, 'error': 'Недопустимый тип файла'}), 400

    # Если фронтенд прислал target_path — делаем точечную замену конкретного файла,
    # включая подпапки (например: hero/mountains.jpg).
    target_path = request.form.get('target_path')
    if target_path:
        # Нормализуем относительный путь: убираем /static/images/ и ведущие /
        rel = str(target_path).strip().replace('\\', '/').lstrip('/')
        if rel.startswith('static/images/'):
            rel = rel[len('static/images/'):]
        if rel.startswith('images/'):
            rel = rel[len('images/'):]

        # Защита от path traversal
        parts = [p for p in rel.split('/') if p]
        if not parts or any(p == '..' for p in parts):
            return jsonify({'success': False, 'error': 'Некорректный target_path'}), 400

        # secure_filename применяем к каждой части пути, но оставляем структуру папок.
        safe_parts = [secure_filename(p) for p in parts]
        safe_parts = [p for p in safe_parts if p]
        if not safe_parts:
            return jsonify({'success': False, 'error': 'Некорректный target_path'}), 400

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], *safe_parts)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        file.save(filepath)

        relative_url = f"/static/images/{'/'.join(safe_parts)}"
        return jsonify({
            'success': True,
            'message': 'Файл заменён',
            'url': relative_url,
            'filename': '/'.join(safe_parts)
        })

    # Обычная загрузка (без target_path) - добавляем timestamp только если файл не существует
    filename = secure_filename(file.filename)
    if filename and '.' not in filename:
        guessed_ext = MIMETYPE_TO_EXT.get((file.mimetype or '').lower(), '.img')
        filename = f'{filename}{guessed_ext}'
    if not filename:
        return jsonify({'success': False, 'error': 'Недопустимое имя файла'}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{timestamp}{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    file.save(filepath)

    relative_path = f"/static/images/{filename}"
    return jsonify({
        'success': True,
        'message': 'Файл загружен',
        'url': relative_path,
        'filename': filename
    })


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

    # Запускаем Telegram-бота в отдельном потоке
    bot_thread = threading.Thread(target=telegram_bot_loop, daemon=True)
    bot_thread.start()

    print("=" * 50)
    print("ООО «ТОТ» - сервер запущен!")
    print("=" * 50)
    print(f"URL админки: http://localhost:5000/admin/{app.config['ADMIN_TOKEN']}")
    print("=" * 50)

    app.run(host='0.0.0.0', port=5000, debug=True)
