# Корочки.есть — ПМ.09, вариант 1 «Онлайн-курсы ДПО»

Учебное трёхуровневое веб-приложение: каталог курсов дополнительного профессионального образования
с фильтром по направлению, регистрация и вход, запись на курс, личный кабинет, панель оператора.

**Стек:** Python 3.10+, Flask, Flask-CORS, Flask-Caching, Flask-Compress, PyMySQL, MySQL 8 / MariaDB 10,
HTML5, CSS3 (Grid, `clamp`, `aspect-ratio`), JavaScript ES6+ (Fetch API, IntersectionObserver, AbortController).

## Структура

```
korochki-m1/
├── backend/
│   ├── app.py            # REST API, кэширование, сжатие, раздача клиента
│   └── seed_bulk.py      # генерация большого объёма данных для EXPLAIN / Lighthouse
├── db/
│   ├── korochki.sql      # схема, индексы и тестовые данные (актуальный дамп)
│   ├── indexes.sql       # создание индексов
│   └── drop_indexes.sql  # удаление индексов (для замера EXPLAIN «до»)
├── frontend/             # login / register / applications / create_application / admin + index (каталог)
│   ├── styles.css
│   ├── js/               # common.js, auth.js, catalog.js, applications.js, create_application.js, admin.js
│   └── img/              # иллюстрации направлений (SVG)
├── tests/smoke_api.py    # контрольные сценарии API
└── requirements.txt
```

## Запуск

```bash
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 1. База данных (MySQL должен быть запущен)
mysql -u root < db/korochki.sql      # если у root есть пароль: mysql -u root -p < db/korochki.sql

# 2. Сервер (при другом пароле БД: export DB_PASSWORD=...)
python backend/app.py                # http://127.0.0.1:5000
```

Переменные окружения: `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `KOROCHKI_SECRET`.

## Тестовые учётные записи

| Логин | Пароль | Роль |
|---|---|---|
| Admin | KorokNET | admin |
| operator1 | Operator123 | operator |
| testuser | qazqaz123 | user |

## REST API

| Метод | Маршрут | Доступ | Назначение |
|---|---|---|---|
| POST | /api/register | все | регистрация (роль user) |
| POST | /api/login | все | вход, возвращает token и role_id |
| GET | /api/categories | все | направления (кэш 600 с) |
| GET | /api/payment_methods | все | способы оплаты (кэш 600 с) |
| GET | /api/catalog?category_id=&page=&per_page= | все | каталог курсов, фильтр и пагинация (кэш 120 с) |
| GET | /api/catalog/<id> | все | один курс |
| POST | /api/applications | авторизованный | запись на курс (status_id = 1) |
| GET | /api/applications/my?page=&per_page= | авторизованный | свои заявки |
| DELETE | /api/applications/<id> | владелец | отмена заявки со статусом «Новая» |
| GET | /api/admin/applications | operator, admin | все заявки, фильтр status_id |
| PATCH | /api/admin/applications/<id>/status | operator, admin | смена статуса |
| POST | /api/admin/payment_methods | admin | добавить способ оплаты (сбрасывает кэш) |
| PATCH | /api/admin/courses/<id> | admin | включить/отключить курс (сбрасывает кэш) |

## Проверка

```bash
python tests/smoke_api.py            # сервер должен быть запущен
python backend/seed_bulk.py          # добавить 400 курсов и 60 000 заявок (для замеров)
```

### EXPLAIN до/после

```sql
USE korochki;
-- «до»: убрать индексы
SOURCE db/drop_indexes.sql;
EXPLAIN SELECT id, name, hours, price FROM courses WHERE is_active = 1 AND category_id = 3 ORDER BY id LIMIT 12;
EXPLAIN SELECT id, course_id, start_date, status_id FROM applications WHERE user_id = 3 ORDER BY created_at DESC LIMIT 20;
-- «после»: вернуть индексы
SOURCE db/indexes.sql;
-- и повторить те же EXPLAIN
```

### Lighthouse до/после

В репозитории есть теги: `baseline` — версия до оптимизаций (разделы 9–13 методички), `optimized` — итоговая.

```bash
git checkout baseline   # перезапустить сервер, снять Lighthouse (Chrome DevTools → Lighthouse, Desktop)
git checkout main       # снова снять Lighthouse
```
