FROM python:3.9

WORKDIR /app

RUN pip install --no-cache-dir pymongo flask dnspython

ENV FLASK_APP=main.py

COPY . .

CMD [ "flask",  "run" ]