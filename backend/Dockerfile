FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt --no-cache-dir

COPY backend/ .
COPY data/ /app/data/

CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && python manage.py load_ingredients && gunicorn foodgram_backend.wsgi:application --bind 0.0.0.0:8000"]
