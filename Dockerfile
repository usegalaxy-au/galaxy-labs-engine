FROM python:3.12

RUN apt-get update
WORKDIR /srv/labs-engine/app
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
EXPOSE 8000
