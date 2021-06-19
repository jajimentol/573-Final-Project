FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

ENV FLASK_APP=main.py

ENV FLASK_ENV=debug

COPY . .

EXPOSE 5000

CMD [ "flask",  "run", "--host=0.0.0.0" ]