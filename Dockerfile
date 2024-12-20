FROM python:3.11-slim
LABEL authors="abhishekjain"

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

CMD ["fastapi", "run", "app/main.py", "--proxy-headers", "--port", "80"]
