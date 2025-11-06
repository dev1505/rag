FROM python:3.12.12-slim-bookworm

WORKDIR /rag_backend

COPY requirements.txt /rag_backend/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY rag_backend ./rag_backend

EXPOSE 8000

CMD ["uvicorn", "rag_backend.main:app", "--host", "0.0.0.0", "--port", "8000"]