FROM python:3.12

WORKDIR /atom

COPY ./requirements.txt /atom/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /atom/requirements.txt

COPY ..

CMD ["pythin","main.py","--port", "80"]

