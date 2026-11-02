DATABASE_PATH ?= app.db

.PHONY: migrate migrate-status test
migrate:  ## Apply all pending migrations (one command)
	python3 db/migrate.py up --db $(DATABASE_PATH)

migrate-status:
	python3 db/migrate.py status --db $(DATABASE_PATH)

test:
	python3 -m unittest discover -s tests -t . -v
