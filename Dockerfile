FROM python:3.13-slim-bookworm

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "app.py"]
