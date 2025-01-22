
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . synthetic_data_generator

EXPOSE 8000

CMD ["uvicorn", "synthetic_data_generator.app_fastapi:app", "--host", "0.0.0.0", "--port", "8000"]