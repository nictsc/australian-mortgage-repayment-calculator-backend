web: cd calculator && gunicorn calculator.wsgi --bind 0.0.0.0:$PORT --workers 2
release: cd calculator && python manage.py migrate
