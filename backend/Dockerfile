FROM python:3.7

WORKDIR /srv

RUN apt update
RUN apt-get install nginx supervisor less vim --yes

ADD requirements.txt /srv/
RUN pip install -r requirements.txt

ADD django/ /srv/

RUN python manage.py collectstatic --no-input

ADD etc_config/ /etc/
RUN rm -f /etc/nginx/sites-enabled/default
RUN mkdir -p /run/daphne
CMD supervisord -c /etc/supervisor/conf.d/elva.supervisor.conf --nodaemon
#   daphne -b 0.0.0.0 -p 80 elva.asgi:application
