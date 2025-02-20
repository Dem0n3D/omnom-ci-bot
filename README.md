
# Telegram Bot for Release Notes Translation

This is a Telegram bot designed to help manage and translate release notes for software projects. The bot integrates with **DeepL** for automatic translation and supports user input to review and modify the translated release notes before final approval.

## Features
- **Automatic Translation**: The bot translates release notes using DeepL API.
- **User Interaction**: Users can review and edit the translated release notes.
- **CI/CD Integration**: It can be integrated with CI/CD pipelines (like GitLab CI, GitHub Actions) to automatically send release notes to the bot for translation.

## Installation

### Requirements
- Python 3.9+
- Poetry (for dependency management and virtual environments)
- Telegram Bot API Token
- DeepL API Key
- Ruff (for linting)
- Black (for code formatting)

### Setting Up the Project

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/telegram-bot-release-notes.git
   cd telegram-bot-release-notes
   ```

2. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

3. Set up environment variables:
   - Create a `.env` file in the root of your project and add your Telegram bot token and DeepL API key:
     ```env
     TELEGRAM_BOT_TOKEN=your-telegram-bot-token
     TELEGRAM_CHAT_ID=your-telegram-bot-chat-id
     DEEPL_API_KEY=your-deepl-api-key
     ```

4. Run the bot:
   ```bash
   poetry run uvicorn src.main:app --reload
   ```

## Docker Support

This project can also be run in Docker containers.

### Building and Running with Docker

1. Ensure Docker and Docker Compose are installed on your system.

2. Build and start the application using Docker Compose:
   ```bash
   docker compose up --build
   ```

3. The bot will be accessible at `http://localhost:8000`.

4. Make sure to set your environment variables in a `.env` file:
   ```env
   TELEGRAM_BOT_TOKEN=your-telegram-bot-token
   TELEGRAM_CHAT_ID=your-telegram-bot-chat-id
   DEEPL_API_KEY=your-deepl-api-key
   ```

### Docker Compose Configuration

The project uses **docker-compose.yml** for easy setup and deployment. It builds the image from the `Dockerfile`, passes environment variables, and maps port 8000.

## Usage

### Linting with Ruff

Ruff is used to lint your Python code. To run Ruff, use the following command:

```bash
poetry run ruff .
```

This will check the entire codebase for any linting issues.

### Formatting with Black

Black is used to automatically format your code. To format your code with Black, use:

```bash
poetry run black .
```

This will format all Python files in the project according to the Black style guide.

### Sending Release Notes to the Bot

The bot listens for release notes in the form of commit messages or any text you send. It automatically translates the text into your preferred language (configured through the bot's settings) and sends the translated release notes back to you for review.

1. **Start a conversation** with the bot in Telegram.
2. **Send a message** with the release notes or commits.
3. The bot will **translate** the message automatically and send it back for review.
4. Once the user approves the translated text, the bot can **confirm** the final release notes and return them to the CI/CD pipeline for deployment.

### Integration with CI/CD

You can integrate this bot with your CI/CD pipeline (e.g., GitLab CI, GitHub Actions) to automatically send commit messages or release notes to the bot for translation and approval.

### GitLab CI/CD Integration

Here's an example of a GitLab CI pipeline (`.gitlab-ci.yml`) that sends release notes to the Telegram bot, waits for user input to approve the translation, and then continues with the deployment:

```yaml
stages:
  - lint
  - test
  - release

variables:
  TELEGRAM_BOT_TOKEN: "your-telegram-bot-token"
  DEEPL_API_KEY: "your-deepl-api-key"
  TELEGRAM_CHAT_ID: "your-chat-id"  # Chat ID where the bot will send messages

lint:
  stage: lint
  image: python:3.9
  script:
    - pip install poetry
    - poetry install
    - poetry run ruff .
    - poetry run black --check .

test:
  stage: test
  image: python:3.9
  script:
    - poetry run pytest --maxfail=1 --disable-warnings -q

release:
  stage: release
  image: python:3.9
  script:
    - poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 &
    - >
      curl -X POST \
        -F "chat_id=$TELEGRAM_CHAT_ID" \
        -F "text=Release notes: $(git log --oneline -n 10)" \
        https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage
    - >
      # This part waits for user input to confirm the release notes
      echo "Waiting for user to approve release notes in Telegram"
      sleep 60  # Adjust this as needed to allow the user time to review and approve
    - >
      curl -X POST \
        -F "chat_id=$TELEGRAM_CHAT_ID" \
        -F "text=Release notes approved. Proceeding with deployment." \
        https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage
    - # Add your deployment steps here (e.g., Docker deployment, server restart)
```

### GitHub Actions Integration

If you're using GitHub Actions for your CI/CD pipeline, here’s an example workflow (`.github/workflows/release.yml`) for the integration:

```yaml
name: Release Pipeline

on:
  push:
    tags:
      - 'v*'

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install poetry
          poetry install
      - name: Lint code with Ruff
        run: poetry run ruff .
      - name: Format code with Black
        run: poetry run black --check .

  release:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - name: Checkout code
        uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Send release notes to Telegram Bot
        run: |
          curl -X POST\
            -H "Content-Type: application/json"\
            -d '{"text": "Release notes:
            $(git log --oneline -n 10)", "chat_id": "${{ secrets.TELEGRAM_CHAT_ID }}"}'\
            https://api.telegram.org/bot${{ secrets.TELEGRAM_BOT_TOKEN }}/sendMessage
      - name: Wait for user approval
        run: |
          echo "Waiting for user to approve release notes in Telegram"
          sleep 60  # Adjust this as needed to allow the user time to review and approve
      - name: Proceed with deployment
        run: |
          curl -X POST\
            -H "Content-Type: application/json"\
            -d '{"text": "Release notes approved. Proceeding with deployment.", "chat_id": "${{ secrets.TELEGRAM_CHAT_ID }}"}'\
            https://api.telegram.org/bot${{ secrets.TELEGRAM_BOT_TOKEN }}/sendMessage
          # Add your deployment steps here (e.g., Docker deployment, server restart)
```

### Example Workflow Breakdown:
1. **Linting**: **Ruff** is used for code linting, and **Black** is used for formatting.
2. **Testing**: Tests are run using **pytest**.
3. **Release**:
   - The bot sends the latest commits to Telegram.
   - The script waits for user approval in the Telegram chat.
   - After approval, it continues with the deployment process.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements
- [FastAPI](https://fastapi.tiangolo.com/) - For building the web application.
- [aiogram](https://github.com/aiogram/aiogram) - For interacting with Telegram API.
- [DeepL API](https://www.deepl.com/pro#developer) - For automatic translation.
- [Ruff](https://github.com/charliermarsh/ruff) - For Python linting.
- [Black](https://black.readthedocs.io/en/stable/) - For automatic code formatting.

## Contributing

Feel free to open issues or pull requests if you'd like to contribute to the project. Make sure to follow the code of conduct and adhere to the project's guidelines.

---

For more information, please refer to the project's [documentation](https://github.com/your-username/telegram-bot-release-notes).
