FROM python:3.10

WORKDIR /app

COPY . .

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install --no-cache-dir fastapi uvicorn[standard]

EXPOSE 8003

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
