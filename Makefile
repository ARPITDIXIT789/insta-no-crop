PROJECT ?= insta-no-crop

.PHONY: up down rebuild-backend restart-backend rebuild-frontend logs certbot-renew verify

up:
	docker compose up -d

down:
	docker compose down

rebuild-backend:
	docker compose build backend

rebuild-frontend:
	docker compose build nginx

restart-backend:
	docker compose up -d --no-deps backend

logs:
	docker compose logs -f backend nginx

certbot-renew:
	docker compose run --rm certbot renew

# Nginx template properly render hua ya nahi check karo
verify:
	@echo "Checking rendered nginx config..."
	@docker compose exec nginx cat /etc/nginx/conf.d/default.conf
	@echo ""
	@echo "Backend health check..."
	@curl -fsS http://localhost/health || echo "Health check failed"
