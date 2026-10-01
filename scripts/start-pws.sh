#!/bin/sh
set -eu

# Run this from the repository root in PWS's application environment.
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Explicit opt-in only; never create an account with a built-in password.
if [ "${PWS_SEED_DEMO:-false}" = "true" ]; then
  : "${DEMO_PASSWORD:?Set a unique DEMO_PASSWORD before enabling PWS_SEED_DEMO}"
  python manage.py seed_demo --username "${DEMO_USERNAME:-demo}"
fi

exec gunicorn PandaCrumbs.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --access-logfile - --error-logfile -
