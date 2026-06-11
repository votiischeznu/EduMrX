run:
	docker compose up

stop:
	docker compose down

mig:
	docker compose exec backend uv run python manage.py makemigrations

up:
	docker compose exec backend uv run python manage.py migrate

