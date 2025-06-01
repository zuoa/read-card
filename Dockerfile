FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt;
COPY . .
EXPOSE 9010
ENV TZ=Asia/Shanghai
ENV PYTHONPATH="/app:$PYTHONPATH"
CMD ["gunicorn", "-c", "gunicorn.conf.py", "main:app"]
