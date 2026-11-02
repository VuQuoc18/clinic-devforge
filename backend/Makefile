# Chạy trực tiếp trong backend/ thì mặc định là backend/app.db; chạy từ gốc repo
# (make ở gốc) thì Makefile gốc truyền đường dẫn tuyệt đối, mặc định <gốc>/app.db.
DATABASE_PATH ?= app.db

.PHONY: migrate migrate-status test
migrate:  ## Apply all pending migrations (one command)
	python3 db/migrate.py up --db $(DATABASE_PATH)

migrate-status:
	python3 db/migrate.py status --db $(DATABASE_PATH)

test:
	python3 -m pytest tests
