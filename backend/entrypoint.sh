#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."
python <<'PY'
import os
import time

import psycopg2

for _ in range(30):
    try:
        connection = psycopg2.connect(
            dbname=os.environ['POSTGRES_DB'],
            user=os.environ['POSTGRES_USER'],
            password=os.environ['POSTGRES_PASSWORD'],
            host=os.environ.get('DB_HOST', 'db'),
            port=os.environ.get('DB_PORT', '5432'),
        )
        connection.close()
    except psycopg2.OperationalError:
        time.sleep(1)
    else:
        break
else:
    raise SystemExit('PostgreSQL is not available.')
PY

python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py load_initial_data
exec "$@"
