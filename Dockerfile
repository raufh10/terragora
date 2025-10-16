FROM python:3.13-alpine

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD uvicorn app:app --host :: --port ${PORT:-3000}