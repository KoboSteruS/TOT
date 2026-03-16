# Инструкция по добавлению сертификатов

## Структура файлов

Все сертификаты хранятся в папке `static/images/partners/`.

## Добавление нового сертификата

### 1. Подготовка изображения

- Формат: PNG или JPG
- Рекомендуемое соотношение сторон: 3:4 (вертикальная ориентация)
- Оптимальный размер: 800x1066px
- Максимальный вес файла: 500KB

### 2. Размещение файла

Скопируйте изображение в папку:
```
static/images/partners/your-certificate-name.png
```

### 3. Добавление в HTML

Откройте `templates/index.html` и найдите блок с классом `.certificates-grid`:

```html
<div class="certificates-grid">
  <!-- Существующие сертификаты -->
  
  <!-- Добавьте новый сертификат -->
  <div class="certificate-item" data-cert="unique-name">
    <img src="{{ url_for('static', filename='images/partners/your-certificate-name.png') }}" 
         alt="Описание сертификата">
    <div class="certificate-overlay">
      <span>Нажмите для увеличения</span>
    </div>
  </div>
</div>
```

### 4. Параметры

- `data-cert` — уникальный идентификатор сертификата (латиница, дефисы)
- `alt` — описание сертификата для доступности и SEO
- `filename` — имя файла в папке `static/images/partners/`

## Примеры

### Сертификат партнёра банка
```html
<div class="certificate-item" data-cert="bank-partner">
  <img src="{{ url_for('static', filename='images/partners/bank-certificate.png') }}" 
       alt="Сертификат официального партнёра Альфа-Банка">
  <div class="certificate-overlay">
    <span>Нажмите для увеличения</span>
  </div>
</div>
```

### Сертификат соответствия
```html
<div class="certificate-item" data-cert="compliance">
  <img src="{{ url_for('static', filename='images/partners/compliance-certificate.png') }}" 
       alt="Сертификат соответствия стандартам">
  <div class="certificate-overlay">
    <span>Нажмите для увеличения</span>
  </div>
</div>
```

## Оптимизация изображений

Рекомендуется оптимизировать изображения перед загрузкой:

### Онлайн-инструменты:
- TinyPNG (tinypng.com)
- Squoosh (squoosh.app)
- ImageOptim (imageoptim.com)

### Командная строка:
```bash
# Для PNG
pngquant --quality=80-95 input.png -o output.png

# Для JPG
jpegoptim --max=85 input.jpg
```

## Адаптивность

Галерея автоматически адаптируется под разные экраны:
- **Desktop (>1024px):** 3 колонки
- **Tablet (860-1024px):** 2 колонки
- **Mobile (<860px):** 1 колонка

## Модальное окно

При клике на сертификат открывается модальное окно с полноразмерным изображением. JavaScript обработчик подключается автоматически.

## Советы

1. **Качество:** Используйте изображения высокого качества
2. **Единообразие:** Поддерживайте единый стиль всех сертификатов
3. **Водяной знак:** При необходимости добавьте водяной знак компании
4. **Актуальность:** Регулярно обновляйте устаревшие сертификаты
5. **Проверка:** После добавления проверьте отображение на всех устройствах

## Удаление сертификата

Чтобы удалить сертификат:
1. Удалите соответствующий блок `.certificate-item` из HTML
2. (Опционально) Удалите файл изображения из `static/images/partners/`
