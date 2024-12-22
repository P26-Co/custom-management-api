FROM python:3.12-slim
LABEL authors="abhishekjain"

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./alembic.ini /code/alembic.ini
COPY ./alembic /code/alembic
COPY ./app /code/app

RUN alembic upgrade head

CMD ["fastapi", "run", "app/main.py", "--proxy-headers", "--port", "80"]
