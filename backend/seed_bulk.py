"""Наполнение БД большим объёмом данных, чтобы EXPLAIN и Lighthouse показывали реальную разницу.
Запуск: python backend/seed_bulk.py [число_курсов] [число_заявок]   (по умолчанию 400 и 60000)"""
import random
import sys
from datetime import date, timedelta

import pymysql

from app import DB_CONFIG

courses_n = int(sys.argv[1]) if len(sys.argv) > 1 else 400
apps_n = int(sys.argv[2]) if len(sys.argv) > 2 else 60000
random.seed(1)

with pymysql.connect(**DB_CONFIG) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT MAX(id) FROM courses")
        start_id = (cur.fetchone()[0] or 0) + 1
        cur.executemany(
            "INSERT INTO courses (name, category_id, hours, price, is_active) VALUES (%s, %s, %s, %s, %s)",
            [(f"Тестовый курс №{start_id + i}", random.randint(1, 6), random.choice([16, 24, 36, 72, 144]),
              random.choice([5000, 8900, 12900, 25000]), 1 if random.random() > 0.05 else 0) for i in range(courses_n)],
        )
        cur.execute("SELECT id FROM users")
        users = [r[0] for r in cur.fetchall()]
        base = date.today()
        cur.executemany(
            "INSERT INTO applications (user_id, course_id, start_date, payment_method_id, status_id) VALUES (%s,%s,%s,%s,%s)",
            [(random.choice(users), random.randint(1, start_id + courses_n - 1), base + timedelta(days=random.randint(1, 120)),
              random.randint(1, 3), random.randint(1, 4)) for _ in range(apps_n)],
        )
    conn.commit()
print(f"Добавлено курсов: {courses_n}, заявок: {apps_n}")
