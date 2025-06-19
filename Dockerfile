FROM python:3.10

WORKDIR /app

COPY . /app

RUN apt-get update && apt-get install -y libpango-1.0-0 libgdk-pixbuf2.0-0 libffi-dev libcairo2
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/outputs

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
