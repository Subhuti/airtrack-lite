#!/bin/bash

echo "⏳ Waiting for MariaDB to be ready..."
until mariadb -h airtrack-db -u"$DB_USER" -p"$DB_PASSWORD" -e "SELECT 1;" &>/dev/null; do
    echo "⌛ Still waiting for MariaDB to accept connections..."
    sleep 2
done
echo "✅ MariaDB is ready!"
exec /venv/bin/python app.py