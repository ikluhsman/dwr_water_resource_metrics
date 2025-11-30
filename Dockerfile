FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY dwr_exporter.py .
COPY ./dwr_gauges.yaml /config/dwr_gauges.yaml
CMD ["python", "dwr_exporter.py"]
