FROM python:3.9

ADD ./flask /flask

WORKDIR /flask

RUN pip install -r requirements.txt

EXPOSE 80

CMD gunicorn --worker-class gevent --workers 2 --bind 0.0.0.0:80 wsgi:app --max-requests 10000 --timeout 5 --keep-alive 5 --log-level info
