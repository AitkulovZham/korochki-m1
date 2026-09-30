-- korochki.sql — схема БД учебного проекта «Корочки.есть» (ПМ.09), вариант 1: онлайн-курсы ДПО.
-- Импорт: mysql -u root < db/korochki.sql   (или phpMyAdmin → Импорт)
-- Индексы под целевые запросы — в разделе «Индексы» (см. также db/indexes.sql и db/drop_indexes.sql).

CREATE DATABASE IF NOT EXISTS korochki CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE korochki;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS applications, courses, categories, payment_methods, application_statuses, users, roles;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE roles (
  id   TINYINT UNSIGNED PRIMARY KEY,
  name VARCHAR(20) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE users (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  login         VARCHAR(50)  NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role_id       TINYINT UNSIGNED NOT NULL,
  created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_users_role FOREIGN KEY (role_id) REFERENCES roles(id)
) ENGINE=InnoDB;

CREATE TABLE application_statuses (
  id   TINYINT UNSIGNED PRIMARY KEY,
  name VARCHAR(30) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE payment_methods (
  id   INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(50) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE categories (
  id   INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(80) NOT NULL UNIQUE
) ENGINE=InnoDB;

-- Внешние ключи у «больших» таблиц (courses, applications) не объявлены намеренно:
-- целостность проверяет сервер, а индексы создаются явно, и эффект виден в EXPLAIN до/после.
CREATE TABLE courses (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  name        VARCHAR(200) NOT NULL UNIQUE,
  category_id INT NOT NULL,
  hours       INT NOT NULL,
  price       DECIMAL(8,2) NOT NULL,
  is_active   TINYINT(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB;

CREATE TABLE applications (
  id                INT AUTO_INCREMENT PRIMARY KEY,
  user_id           INT NOT NULL,
  course_id         INT NOT NULL,
  start_date        DATE NOT NULL,
  payment_method_id INT NOT NULL,
  status_id         TINYINT UNSIGNED NOT NULL DEFAULT 1,
  created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Индексы
CREATE INDEX idx_courses_category_active ON courses (category_id, is_active);
CREATE INDEX idx_apps_user_created       ON applications (user_id, created_at);
CREATE INDEX idx_apps_status_created     ON applications (status_id, created_at);

-- Справочники
INSERT INTO roles (id, name) VALUES (1,'admin'),(2,'operator'),(3,'user');
INSERT INTO application_statuses (id, name) VALUES (1,'Новая'),(2,'В обработке'),(3,'Подтверждена'),(4,'Отклонена');
INSERT INTO payment_methods (name) VALUES ('Банковская карта'),('Безналичный расчёт (счёт)'),('Рассрочка');

INSERT INTO categories (id, name) VALUES (1,'Программирование'),(2,'Веб-дизайн'),(3,'Аналитика данных'),(4,'Управление проектами'),(5,'Цифровой маркетинг'),(6,'Кибербезопасность');

INSERT INTO courses (name, category_id, hours, price, is_active) VALUES
  ('Python для автоматизации',1,48,8640.00,1),
  ('Основы C# и .NET',1,36,5400.00,1),
  ('JavaScript и Node.js',1,24,2880.00,1),
  ('Проектирование REST API',1,36,7560.00,1),
  ('Git и командная разработка',1,72,8640.00,1),
  ('Алгоритмы и структуры данных',1,36,4320.00,1),
  ('UI/UX-дизайн интерфейсов',2,96,20160.00,0),
  ('Figma: от макета к прототипу',2,24,5040.00,1),
  ('Адаптивная вёрстка',2,96,20160.00,1),
  ('Типографика и цвет',2,24,3600.00,1),
  ('Доступность веб-интерфейсов',2,24,2880.00,1),
  ('Дизайн-системы',2,16,2400.00,1),
  ('SQL для аналитиков',3,72,8640.00,1),
  ('Power BI и визуализация',3,144,30240.00,1),
  ('Статистика для бизнеса',3,144,17280.00,1),
  ('Python для анализа данных',3,36,5400.00,1),
  ('A/B-тестирование',3,96,14400.00,1),
  ('Основы машинного обучения',3,96,20160.00,1),
  ('Agile и Scrum',4,16,2880.00,1),
  ('Управление ИТ-проектами',4,24,5040.00,1),
  ('Управление рисками',4,36,6480.00,1),
  ('Бережливое производство',4,144,17280.00,0),
  ('Product Management',4,24,2880.00,1),
  ('Проектный офис',4,48,5760.00,1),
  ('SEO-продвижение',5,48,10080.00,1),
  ('Контекстная реклама',5,24,2880.00,1),
  ('SMM-стратегия',5,24,5040.00,1),
  ('Email-маркетинг',5,96,11520.00,1),
  ('Веб-аналитика',5,72,8640.00,1),
  ('Контент-маркетинг',5,16,2400.00,1),
  ('Основы информационной безопасности',6,144,21600.00,1),
  ('Защита веб-приложений',6,36,4320.00,1),
  ('Сетевая безопасность',6,16,2400.00,1),
  ('Криптография на практике',6,72,8640.00,1),
  ('Расследование инцидентов',6,72,8640.00,1),
  ('Безопасная разработка',6,72,15120.00,1);

-- Тестовые учётные записи (пароли хранятся как хеши werkzeug pbkdf2:sha256)
INSERT INTO users (login, password_hash, role_id) VALUES
  ('Admin','pbkdf2:sha256:1000000$gS67ik4JliKa$b248bde2b5d7cb674adf1a12cb7ae9cc0e1838201e4adee7a80918671a1071a0',1),
  ('operator1','pbkdf2:sha256:1000000$VivmBxEdgBU7$8e540e337e8ed207f2664c3b5177224c49473b2d954b9450df0dd71d7b848622',2),
  ('testuser','pbkdf2:sha256:1000000$Khyd9TO1BIZm$8276badfc3eb0b6e296a81bca5ca650a3400828b960764a70a4bb53aa2887687',3);

INSERT INTO applications (user_id, course_id, start_date, payment_method_id, status_id) VALUES
  (3, 1, '2026-09-01', 1, 1),
  (3, 8, '2026-09-15', 2, 2),
  (3, 14, '2026-10-01', 3, 3);
