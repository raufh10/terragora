FROM python:3.11-slim-bookworm

WORKDIR /
COPY . .

# Install stable CPU-only PyTorch wheel
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
    torch==2.4.1

# Install the rest (requirements.txt should NOT include torch)
RUN pip install --no-cache-dir -r requirements.txt

RUN adduser --disabled-password --gecos "" appuser
USER appuser

CMD ["sh", "-c", "uvicorn app:app --host :: --port ${PORT}"]
