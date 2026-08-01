run:
	docker compose up

stop:
	docker compose down

compose-mig:
	docker compose exec backend uv run python manage.py makemigrations

compose-up:
	docker compose exec backend uv run python manage.py migrate


mig:
	python manage.py makemigrations

up:
	python manage.py migrate

