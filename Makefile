.PHONY: migrate migrate-status test
migrate:  ## Apply all pending migrations (alembic upgrade head, needs DATABASE_URL or local compose DB)
	cd backend && python3 -m alembic upgrade head

migrate-status:
	cd backend && python3 -m alembic current

test:
	python3 -m unittest discover -s tests -t . -v
