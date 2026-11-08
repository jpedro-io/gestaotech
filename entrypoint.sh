#!/bin/sh
# Sobe o site: aplica migrations, opcionalmente semeia o banco e inicia o gunicorn.
set -e

echo "→ aplicando migrations…"
python manage.py migrate --noinput

if [ "${SEMEAR:-0}" = "1" ]; then
  echo "→ cadastrando oficinas…"
  python manage.py seed_oficinas
  CSV="${CSV_PARTICIPANTES:-importacao/participantes.csv}"
  if [ -f "$CSV" ]; then
    echo "→ importando participantes de $CSV…"
    python manage.py seed_participantes --csv "$CSV"
  fi
fi

echo "→ iniciando o servidor na porta ${PORT:-8000}"
exec gunicorn config.wsgi \
  --workers "${GUNICORN_WORKERS:-1}" \
  --threads "${GUNICORN_THREADS:-4}" \
  --timeout "${GUNICORN_TIMEOUT:-180}" \
  --bind "0.0.0.0:${PORT:-8000}" \
  --access-logfile - \
  --error-logfile -
