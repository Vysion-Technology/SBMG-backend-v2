#!/usr/bin/env bash
set -e

echo "=========================================="
echo "🚀 Running Backend Deployment..."
echo "=========================================="

PREV_COMMIT=$(git rev-parse HEAD@{1} 2>/dev/null || echo "")
NEW_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "")

if [ -n "$PREV_COMMIT" ] && [ "$PREV_COMMIT" != "$NEW_COMMIT" ]; then
  CHANGED_FILES=$(git diff --name-only "$PREV_COMMIT" "$NEW_COMMIT" 2>/dev/null || true)
else
  CHANGED_FILES=""
fi

echo "📄 Changed files since last pull:"
echo "${CHANGED_FILES:-"(no file diff detected)"}"

NEED_BUILD=false
NEED_MIGRATION=false

if echo "$CHANGED_FILES" | grep -Eq "(Dockerfile|requirements|pyproject\.toml|poetry\.lock|docker-compose)"; then
  NEED_BUILD=true
fi

if echo "$CHANGED_FILES" | grep -Eq "(alembic|backend/models)"; then
  NEED_MIGRATION=true
fi

if [ "$NEED_BUILD" = "true" ]; then
  echo "🔨 Dependency or Docker files changed. Rebuilding and restarting backend container..."
  docker compose up -d --build backend
  echo "⏳ Waiting 30s for container to initialize..."
  sleep 30
elif [ "$NEED_MIGRATION" = "true" ]; then
  echo "📦 Migrations/Models changed. Restarting container (entrypoint.sh will auto-run alembic upgrade head)..."
  docker compose restart backend
  echo "⏳ Waiting 30s for migrations and container startup..."
  sleep 30
else
  echo "⚡ Only app code changed. Uvicorn hot-reloads mounted volume automatically (no container restart needed)."
fi

echo "🔍 Checking backend health on port 8000..."
HEALTH_SUCCESS=false
for i in 1 2 3 4 5 6 7 8 9 10; do
  if curl -sf http://localhost:8000/health > /dev/null 2>&1 || curl -sf http://127.0.0.1:8000/health > /dev/null 2>&1; then
    HEALTH_SUCCESS=true
    echo "✅ Health check passed!"
    break
  fi
  echo "⏳ Backend not ready yet, retrying in 3s (attempt $i/10)..."
  sleep 3
done

if [ "$HEALTH_SUCCESS" = "true" ]; then
  echo ""
  echo "=========================================="
  echo "🚀 Deployment completed successfully!"
  echo "=========================================="
else
  echo ""
  echo "❌ Health check failed. Recent container logs:"
  docker compose logs --tail=50 backend
  exit 1
fi
