FROM tiangolo/uwsgi-nginx-flask:python3.11
RUN apk --update add bash nano
ENV STATIC_URL /static
ENV STATIC_PATH /var/www/app/static
COPY ./requirements.txt /var/www/requirements.txt
RUN pip3 install --upgrade pip -r /var/www/requirements.txt