FROM python:3.10-slim

RUN apt update && apt upgrade -y && apt install -y libpq-dev gcc netcat-traditional

WORKDIR /code

COPY requirements.txt /code/

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /code/

RUN chmod +x eismoinfo_app_starter.sh
RUN chmod +x celery_starter.sh
ENTRYPOINT ["sh", "/code/eismoinfo_app_starter.sh"]
