docker compose --env-file .env.docker up -d --build
docker compose --env-file .env.docker run --rm app alembic upgrade head
docker compose --env-file .env.docker logs -f app