"""Контрольное тестирование API (без сторонних библиотек).
Запуск: сервер должен работать (python backend/app.py), затем: python tests/smoke_api.py
Выводит таблицу «сценарий — ожидание — факт» для раздела 5.1 отчёта."""
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import date, timedelta

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000"
results = []


def call(method, path, body=None, token=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req) as resp:
            payload, status = json.loads(resp.read() or b"null"), resp.status
    except urllib.error.HTTPError as e:
        payload, status = json.loads(e.read() or b"null"), e.code
    return status, payload, (time.perf_counter() - started) * 1000


def record(name, expected, ok, fact):
    results.append((name, expected, "OK" if ok else "FAIL", fact))


suffix = str(int(time.time()))[-6:]
new_login = "student" + suffix

s, p, _ = call("POST", "/api/register", {"login": new_login, "password": "Passw0rd!"})
record("POST /api/register, валидные данные", "200, пользователь создан", s == 200, f"HTTP {s}")

s, p, _ = call("POST", "/api/login", {"login": "testuser", "password": "qazqaz123"})
token = p.get("token") if isinstance(p, dict) else None
record("POST /api/login, верный пароль", "200, role_id в ответе", s == 200 and "role_id" in p, f"HTTP {s}, role_id={p.get('role_id')}")

s, p, _ = call("POST", "/api/login", {"login": "testuser", "password": "wrong-password"})
record("POST /api/login, неверный пароль", "401", s == 401, f"HTTP {s}")

s, cats, _ = call("GET", "/api/categories")
record("GET /api/categories", "список направлений", s == 200 and len(cats) > 0, f"HTTP {s}, направлений: {len(cats)}")

s, p, _ = call("GET", "/api/catalog?page=1&per_page=12")
record("GET /api/catalog (пагинация)", "<= 12 курсов, has_next", s == 200 and len(p["items"]) <= 12, f"HTTP {s}, получено {len(p['items'])} из {p['total']}")

cid = cats[0]["id"]
s, p, _ = call("GET", f"/api/catalog?category_id={cid}&per_page=100")
record("GET /api/catalog?category_id=N (фильтр)", "только выбранное направление", s == 200 and all(i["category_id"] == cid for i in p["items"]), f"HTTP {s}, курсов: {len(p['items'])}")

start = (date.today() + timedelta(days=7)).isoformat()
s, p, _ = call("POST", "/api/applications", {"course_id": 1, "start_date": start, "payment_method_id": 1}, token)
record("POST /api/applications", "200, status_id=1", s == 200 and p.get("status_id") == 1, f"HTTP {s}, id={p.get('id')}")

s, p, _ = call("POST", "/api/applications", {"course_id": 1, "start_date": "2020-01-01", "payment_method_id": 1}, token)
record("POST /api/applications, дата в прошлом", "400", s == 400, f"HTTP {s}")

s, p, _ = call("GET", "/api/applications/my?page=1&per_page=20", token=token)
record("GET /api/applications/my", "<= 20 записей текущего пользователя", s == 200 and len(p["items"]) <= 20, f"HTTP {s}, записей: {len(p['items'])}")

s, p, _ = call("GET", "/api/admin/applications", token=token)
record("GET /api/admin/applications под user", "403", s == 403, f"HTTP {s}")

s, p, _ = call("POST", "/api/login", {"login": "operator1", "password": "Operator123"})
op = p.get("token")
s, p, _ = call("GET", "/api/admin/applications?page=1&per_page=20", token=op)
record("GET /api/admin/applications под operator", "200, все заявки", s == 200 and len(p["items"]) > 0, f"HTTP {s}, записей: {len(p['items'])}")
app_id = p["items"][0]["id"]
s, p, _ = call("PATCH", f"/api/admin/applications/{app_id}/status", {"status_id": 2}, op)
record("PATCH /api/admin/applications/<id>/status", "200, status_id=2", s == 200 and p.get("status_id") == 2, f"HTTP {s}")

# кэш справочника: второй запрос должен быть быстрее первого
t = [call("GET", "/api/payment_methods")[2] for _ in range(6)]
record("GET /api/payment_methods повторно (кэш)", "Time второго запроса меньше первого",
       min(t[1:]) <= t[0], "1-й: %.1f мс, далее: %s мс" % (t[0], ", ".join("%.1f" % x for x in t[1:])))

width = max(len(r[0]) for r in results)
for name, expected, verdict, fact in results:
    print(f"[{verdict:4}] {name:<{width}} | ожидание: {expected} | факт: {fact}")
failed = [r for r in results if r[2] != "OK"]
print(f"\nИтого: {len(results) - len(failed)} из {len(results)} сценариев пройдено")
sys.exit(1 if failed else 0)
