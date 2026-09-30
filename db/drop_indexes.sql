-- Убрать индексы, чтобы снять EXPLAIN «до оптимизации»
USE korochki;
DROP INDEX idx_courses_category_active ON courses;
DROP INDEX idx_apps_user_created       ON applications;
DROP INDEX idx_apps_status_created     ON applications;
