run:
	sudo systemctl stop postgresql redis
	docker compose up

stop:
	docker compose down