FROM docker:24-dind

RUN apk add --no-cache python3 py3-pip

WORKDIR /app

COPY requirements.txt .
RUN pip install --break-system-packages -r requirements.txt

COPY main.py .

EXPOSE 8080

CMD ["sh", "-c", "dockerd &>/var/log/dockerd.log & sleep 3 && uvicorn main:app --host 0.0.0.0 --port 8080"]