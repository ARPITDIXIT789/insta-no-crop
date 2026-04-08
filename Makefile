PROJECT ?= insta-no-crop

.PHONY: up down rebuild-backend restart-backend logs certbot-renew

up:
	docker compose up -d

down:
	docker compose down

rebuild-backend:
	docker compose build backend

restart-backend:
	docker compose up -d backend

logs:
	docker compose logs -f backend nginx

certbot-renew:
	docker compose run --rm certbot renew
