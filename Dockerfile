FROM python:3.9-alpine AS bot


ENV PATH="${HOME}/.local/bin:${PATH}"

WORKDIR /app

RUN apk add --update --no-cache pipx
RUN pipx install poetry

RUN pip install poetry && poetry install --no-dev

EXPOSE 8000

RUN adduser -D bot
USER bot

COPY . /app

CMD ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
