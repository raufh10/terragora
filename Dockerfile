FROM python:3.13-alpine

WORKDIR /
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

RUN adduser -D appuser
USER appuser

CMD ["sh", "-c", "uvicorn app:app --host :: --port ${PORT}"]
