FROM python:3.10 as builder

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app .

CMD [ "python3", "emotionAnalysis.py", "--mode", "realtime" ]