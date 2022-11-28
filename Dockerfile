FROM python:3.7
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["gunicorn", "--bind", "0.0.0.0:80", "app:app"]