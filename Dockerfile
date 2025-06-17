FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt ./ 
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0", "--server.maxUploadSize=1000"]