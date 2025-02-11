FROM python:3.9-alpine AS bot

RUN apk add --update --no-cache pipx

RUN adduser -D bot
USER bot

RUN pipx install poetry

ENV PATH="/home/bot/.local/bin:${PATH}"

WORKDIR /app

COPY pyproject.toml poetry.lock /app/

RUN poetry install --only=main

EXPOSE 8000

COPY . /app

CMD ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
