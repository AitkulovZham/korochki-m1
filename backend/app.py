"""Корочки.есть — серверная часть (Flask + PyMySQL). Вариант 1: онлайн-курсы ДПО."""
import os
import re
from datetime import date, datetime
from decimal import Decimal
from functools import wraps

import pymysql
from flask import Flask, jsonify, request, send_from_directory
from flask_caching import Cache
from flask_compress import Compress
from flask_cors import CORS
from itsdangerous import BadSignature, URLSafeTimedSerializer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))

ROLE_ADMIN, ROLE_OPERATOR, ROLE_USER = 1, 2, 3
STATUS_NEW = 1
STATUS_IDS = {1, 2, 3, 4}
TOKEN_MAX_AGE = 8 * 3600
LOGIN_RE = re.compile(r"^[A-Za-z0-9_.-]{6,50}$")

app = Flask(__name__, static_folder=None)
app.config["SECRET_KEY"] = os.environ.get("KOROCHKI_SECRET", "dev-secret-change-me")
app.json.ensure_ascii = False
CORS(app)
Compress(app)
cache = Cache(config={"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 300})
cache.init_app(app)
serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"], salt="korochki-auth")

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "127.0.0.1"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_NAME", "korochki"),
    "charset": "utf8mb4",
}


# ---------- работа с БД ----------
def get_conn():
    return pymysql.connect(cursorclass=pymysql.cursors.DictCursor, **DB_CONFIG)


def jsonable(row):
    """Decimal -> float, date/datetime -> ISO-строка (для JSON)."""
    out = {}
    for key, value in row.items():
        if isinstance(value, Decimal):
            value = float(value)
        elif isinstance(value, (date, datetime)):
            value = value.isoformat()
        out[key] = value
    return out


def db_fetch_all(sql, params=()):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return [jsonable(r) for r in cur.fetchall()]


def db_fetch_one(sql, params=()):
    rows = db_fetch_all(sql, params)
    return rows[0] if rows else None


def db_execute(sql, params=()):
    """Выполняет INSERT/UPDATE/DELETE, возвращает (lastrowid, rowcount)."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            result = (cur.lastrowid, cur.rowcount)
        conn.commit()
    return result


# ---------- аутентификация без серверной сессии (stateless) ----------
def make_token(user_id, role_id):
    return serializer.dumps({"id": user_id, "role_id": role_id})


def current_user():
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    try:
        return serializer.loads(header[7:], max_age=TOKEN_MAX_AGE)
    except BadSignature:  # включает SignatureExpired
        return None


def current_user_id():
    user = current_user()
    return user["id"] if user else None


def require_roles(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = current_user()
            if user is None:
                return jsonify(error="Требуется вход в систему"), 401
            if roles and user["role_id"] not in roles:
                return jsonify(error="Недостаточно прав"), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def error(message, status=400):
    return jsonify(error=message), status


def page_params(default_per_page=20):
    """page >= 1, per_page от 1 до 100 (защита от огромных выборок)."""
    try:
        page = max(int(request.args.get("page", 1)), 1)
        per_page = min(max(int(request.args.get("per_page", default_per_page)), 1), 100)
    except ValueError:
        return None, None
    return page, per_page


# ---------- регистрация и вход ----------
@app.post("/api/register")
def register():
    from werkzeug.security import generate_password_hash
    data = request.get_json(silent=True) or {}
    login, password = str(data.get("login", "")).strip(), str(data.get("password", ""))
    if not LOGIN_RE.match(login):
        return error("Логин: 6–50 символов (латиница, цифры, _ . -)")
    if len(password) < 8:
        return error("Пароль должен содержать не менее 8 символов")
    try:
        user_id, _ = db_execute(
            "INSERT INTO users (login, password_hash, role_id) VALUES (%s, %s, %s)",
            (login, generate_password_hash(password, method="pbkdf2:sha256"), ROLE_USER),
        )
    except pymysql.err.IntegrityError:
        return error("Пользователь с таким логином уже существует", 409)
    return jsonify(id=user_id, login=login)


@app.post("/api/login")
def login():
    from werkzeug.security import check_password_hash
    data = request.get_json(silent=True) or {}
    login_value, password = str(data.get("login", "")).strip(), str(data.get("password", ""))
    user = db_fetch_one("SELECT id, login, password_hash, role_id FROM users WHERE login = %s", (login_value,))
    if not user or not check_password_hash(user["password_hash"], password):
        return error("Неверный логин или пароль", 401)
    return jsonify(token=make_token(user["id"], user["role_id"]), role_id=user["role_id"], login=user["login"])


# ---------- справочники (кэшируются) ----------
@app.get("/api/categories")
@cache.cached(timeout=600)
def categories():
    return jsonify(db_fetch_all("SELECT id, name FROM categories ORDER BY name"))


@app.get("/api/payment_methods")
@cache.cached(timeout=600)
def payment_methods():
    return jsonify(db_fetch_all("SELECT id, name FROM payment_methods ORDER BY id"))


@app.post("/api/admin/payment_methods")
@require_roles(ROLE_ADMIN)
def admin_create_payment_method():
    name = str((request.get_json(silent=True) or {}).get("name", "")).strip()
    if not 2 <= len(name) <= 50:
        return error("Название способа оплаты: 2–50 символов")
    try:
        new_id, _ = db_execute("INSERT INTO payment_methods (name) VALUES (%s)", (name,))
    except pymysql.err.IntegrityError:
        return error("Такой способ оплаты уже есть", 409)
    cache.delete("view//api/payment_methods")
    return jsonify(success=True, id=new_id)


# ---------- каталог курсов (вариант 1): фильтр по направлению + пагинация ----------
@app.get("/api/catalog")
@cache.cached(timeout=120, query_string=True)
def catalog():
    page, per_page = page_params(default_per_page=12)
    if page is None:
        return error("page и per_page должны быть числами")
    where, params = "is_active = 1", []
    category_id = request.args.get("category_id")
    if category_id:
        if not category_id.isdigit():
            return error("category_id должен быть числом")
        where += " AND category_id = %s"
        params.append(int(category_id))
    total = db_fetch_one(f"SELECT COUNT(*) AS n FROM courses WHERE {where}", params)["n"]
    items = db_fetch_all(
        f"SELECT id, name, category_id, hours, price FROM courses WHERE {where} "
        "ORDER BY id LIMIT %s OFFSET %s",
        params + [per_page, (page - 1) * per_page],
    )
    return jsonify(items=items, page=page, per_page=per_page, total=total,
                   has_next=page * per_page < total)


@app.get("/api/catalog/<int:course_id>")
def catalog_item(course_id):
    row = db_fetch_one(
        "SELECT id, name, category_id, hours, price FROM courses WHERE id = %s AND is_active = 1", (course_id,))
    return jsonify(row) if row else error("Курс не найден", 404)


@app.patch("/api/admin/courses/<int:course_id>")
@require_roles(ROLE_ADMIN)
def admin_toggle_course(course_id):
    is_active = (request.get_json(silent=True) or {}).get("is_active")
    if is_active not in (0, 1, True, False):
        return error("is_active должен быть 0 или 1")
    _, rows = db_execute("UPDATE courses SET is_active = %s WHERE id = %s", (int(is_active), course_id))
    if rows == 0 and db_fetch_one("SELECT id FROM courses WHERE id = %s", (course_id,)) is None:
        return error("Курс не найден", 404)
    cache.clear()  # каталог кэшируется по query string — сбрасываем целиком
    return jsonify(success=True)


# ---------- заявки пользователя ----------
@app.post("/api/applications")
@require_roles(ROLE_ADMIN, ROLE_OPERATOR, ROLE_USER)
def create_application():
    data = request.get_json(silent=True) or {}
    try:
        course_id = int(data.get("course_id"))
        payment_id = int(data.get("payment_method_id"))
        start = date.fromisoformat(str(data.get("start_date")))
    except (TypeError, ValueError):
        return error("Укажите курс, дату начала (ГГГГ-ММ-ДД) и способ оплаты")
    if start < date.today():
        return error("Дата начала не может быть в прошлом")
    if not db_fetch_one("SELECT id FROM courses WHERE id = %s AND is_active = 1", (course_id,)):
        return error("Курс не найден или недоступен", 404)
    if not db_fetch_one("SELECT id FROM payment_methods WHERE id = %s", (payment_id,)):
        return error("Неизвестный способ оплаты")
    new_id, _ = db_execute(
        "INSERT INTO applications (user_id, course_id, start_date, payment_method_id, status_id) "
        "VALUES (%s, %s, %s, %s, %s)",
        (current_user_id(), course_id, start, payment_id, STATUS_NEW),
    )
    return jsonify(id=new_id, status_id=STATUS_NEW)


@app.get("/api/applications/my")
@require_roles(ROLE_ADMIN, ROLE_OPERATOR, ROLE_USER)
def my_applications():
    page, per_page = page_params()
    if page is None:
        return error("page и per_page должны быть числами")
    items = db_fetch_all(
        "SELECT a.id, c.name AS course_name, a.start_date, a.status_id "
        "FROM applications a JOIN courses c ON c.id = a.course_id "
        "WHERE a.user_id = %s ORDER BY a.created_at DESC, a.id DESC LIMIT %s OFFSET %s",
        (current_user_id(), per_page, (page - 1) * per_page),
    )
    return jsonify(items=items, page=page, per_page=per_page)


@app.delete("/api/applications/<int:app_id>")
@require_roles(ROLE_ADMIN, ROLE_OPERATOR, ROLE_USER)
def cancel_application(app_id):
    row = db_fetch_one("SELECT user_id, status_id FROM applications WHERE id = %s", (app_id,))
    if row is None or row["user_id"] != current_user_id():
        return error("Заявка не найдена", 404)
    if row["status_id"] != STATUS_NEW:
        return error("Отменить можно только заявку со статусом «Новая»", 409)
    db_execute("DELETE FROM applications WHERE id = %s", (app_id,))
    return jsonify(success=True)


# ---------- панель оператора / администратора ----------
@app.get("/api/admin/applications")
@require_roles(ROLE_ADMIN, ROLE_OPERATOR)
def admin_applications():
    page, per_page = page_params()
    if page is None:
        return error("page и per_page должны быть числами")
    where, params = "1 = 1", []
    status_id = request.args.get("status_id")
    if status_id:
        if not status_id.isdigit() or int(status_id) not in STATUS_IDS:
            return error("Неизвестный статус")
        where, params = "a.status_id = %s", [int(status_id)]
    items = db_fetch_all(
        "SELECT a.id, u.login, c.name AS course_name, a.start_date, a.status_id, a.created_at "
        "FROM applications a JOIN users u ON u.id = a.user_id JOIN courses c ON c.id = a.course_id "
        f"WHERE {where} ORDER BY a.created_at DESC, a.id DESC LIMIT %s OFFSET %s",
        params + [per_page, (page - 1) * per_page],
    )
    return jsonify(items=items, page=page, per_page=per_page)


@app.patch("/api/admin/applications/<int:app_id>/status")
@require_roles(ROLE_ADMIN, ROLE_OPERATOR)
def admin_set_status(app_id):
    status_id = (request.get_json(silent=True) or {}).get("status_id")
    if status_id not in STATUS_IDS:
        return error("Неизвестный статус")
    if not db_fetch_one("SELECT id FROM applications WHERE id = %s", (app_id,)):
        return error("Заявка не найдена", 404)
    db_execute("UPDATE applications SET status_id = %s WHERE id = %s", (status_id, app_id))
    return jsonify(success=True, status_id=status_id)


# ---------- статические страницы клиента ----------
PAGES = {"/": "index.html", "/login": "login.html", "/register": "register.html",
         "/applications": "applications.html", "/create_application": "create_application.html",
         "/admin": "admin.html"}


@app.get("/")
@app.get("/login")
@app.get("/register")
@app.get("/applications")
@app.get("/create_application")
@app.get("/admin")
def page():
    return send_from_directory(FRONTEND_DIR, PAGES[request.path])


@app.get("/<path:filename>")
def static_files(filename):
    return send_from_directory(FRONTEND_DIR, filename)


@app.after_request
def cache_headers(response):
    if request.path.endswith((".css", ".js", ".svg", ".webp", ".png")):
        response.headers["Cache-Control"] = "public, max-age=86400"
    return response


@app.errorhandler(404)
def not_found(_):
    return error("Не найдено", 404)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
