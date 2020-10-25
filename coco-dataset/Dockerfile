FROM jainal09/pp-detection:coco

# Set the locale
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

# CMD ["python", "-u", "main.py"]