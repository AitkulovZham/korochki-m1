USE korochki;
CREATE INDEX idx_courses_category_active ON courses (category_id, is_active);
CREATE INDEX idx_apps_user_created       ON applications (user_id, created_at);
CREATE INDEX idx_apps_status_created     ON applications (status_id, created_at);
