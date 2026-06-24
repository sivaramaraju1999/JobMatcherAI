Instructions to Set Up GitHub Actions with Grok, Telegram & NVIDIA NIM Secrets

## 1. Create the GitHub Actions Workflow File

Create the directory `.github/workflows` in your repository root (if it doesn't exist).
Inside that directory, create a file named `daily-job-match.yml` with the following content:

```yaml
name: Daily Job Match

on:
  schedule:
    - cron: '0 9 * * *'   # Every day at 09:00 UTC
  workflow_dispatch:   # Allow manual trigger from GitHub UI

jobs:
  build:
    runs-on: ubuntu-latest
    env:
      # These will be set from repository secrets
      GROK_API_KEY: ${{ secrets.GROK_API_KEY }}
      TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
      TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
      NVIDIA_NIM_API_KEY: ${{ secrets.NVIDIA_NIM_API_KEY }}
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'  # Adjust if needed
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Run Job Matcher
        run: |
          python main.py
```

## 2. Configure Repository Secrets

Go to your GitHub repository:
1. Click **Settings** > **Secrets and variables** > **Actions**
2. Click **New repository secret** and add these four secrets:
   - `GROK_API_KEY`: Your Grok API key (from https://console.groq.com/keys)
   - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token (from @BotFather)
   - `TELEGRAM_CHAT_ID`: Your Telegram chat ID (get by messaging @userinfobot or using getUpdates)
   - `NVIDIA_NIM_API_KEY`: Your NVIDIA NIM API key (from https://build.nvidia.com/)

## 3. Enable Telegram Notifications in the Code (Optional but Recommended)

To have the job matcher send the daily report to your Telegram chat, add this method to the `JobMatcherAI` class in `main.py`:

```python
    def send_telegram_message(self, message: str):
        """Send a message via Telegram bot."""
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        if not bot_token or not chat_id:
            logger.warning("Telegram credentials not set. Skipping notification.")
            return
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            logger.info("Telegram message sent successfully.")
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
```

Then, in the `generate_daily_report` method, after you build and print the report string, add:
```python
        # Send the report via Telegram
        self.send_telegram_message(report_string)
```

**Note**: You'll need to ensure `report_string` contains the full report. If your current `generate_daily_report` prints line-by-line without storing the full string, you may need to:
- Build the report in a variable (e.g., `report_lines = []`, append each line, then `report_string = '\n'.join(report_lines)`)
- Print the string
- Then send it via Telegram

## 4. How It Works

- The workflow runs every day at 09:00 UTC (adjust the cron time as needed)
- It checks out your code, sets up Python, installs dependencies, and runs `main.py`
- The secrets are available as environment variables in the workflow:
  - `GROK_API_KEY` - For future LLM integration (not used in current NIM-based matching)
  - `TELEGRAM_BOT_TOKEN` & `TELEGRAM_CHAT_ID` - For sending Telegram notifications
  - `NVIDIA_NIM_API_KEY` - Powers the resume matching, keyword extraction, and optimization via NVIDIA NIM models
- If Telegram credentials are configured, the daily report will be sent to your chat
- The NVIDIA NIM API key enables advanced LLM-powered resume tailoring that understands context and can produce more natural, ATS-optimized resumes than keyword-only approaches

## 5. Important Notes

⚠️ **Telegram Message Limits**: Telegram has a 4096-character limit per message. If your report exceeds this, consider:
   - Truncating the report
   - Splitting into multiple messages
   - Sending as a document (requires additional code)

🔒 **Security**: Never commit your actual API keys to the repository. GitHub Secrets keep them safe.

🔧 **Customization**: Adjust the schedule (`cron`) in the workflow file to change when the job runs.
   - You can also configure the NIM model via the `NVIDIA_NIM_MODEL` secret or environment variable if you want to use a different model.

## 6. Verification

After pushing the workflow file and setting up secrets:
1. Go to the **Actions** tab in your GitHub repo
2. You should see the workflow run according to the schedule
3. Check the logs to confirm it ran successfully
4. Verify you received the Telegram message (if you added the code changes)
5. Check the `outputs/resumes/` directory in the workflow artifacts for tailored resumes

Your automated job matching system is now running daily in the cloud with secure API key handling and leveraging NVIDIA NIM for intelligent resume optimization!