#!/bin/bash
set -e
pip install -r requirements.txt --break-system-packages
python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py set_curiosidades_32vos || true
