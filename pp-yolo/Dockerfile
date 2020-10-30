FROM python:3.7

# Set the locale
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app
RUN chmod +rwx wait-for-it.sh

# CMD ["python", "-u", "main.py"]
