# Instructions to Set Up GitHub Actions with Apify, Groq, & Telegram Secrets

To run the job matcher automatically every day, you need to configure your GitHub repository with the correct secrets so the action can access Apify (for scraping), Groq/NVIDIA NIM (for scoring), and Telegram (for sending the notifications).

## 1. Get the Required Keys

### Apify
1. Go to [Apify Console](https://console.apify.com/) and create a free account.
2. Go to Settings -> Integrations.
3. Copy your API Token (`APIFY_API_TOKEN`).

### Groq 
1. Go to the [Groq Console](https://console.groq.com/).
2. Create an account or sign in.
3. Go to API Keys and generate a new key (`GROK_API_KEY`).

### Telegram Bot
1. Open Telegram and search for `@BotFather`.
2. Send `/newbot` and follow the instructions to create a bot.
3. Copy the HTTP API token (`TELEGRAM_BOT_TOKEN`).
4. Search for `@userinfobot` in Telegram and start a chat to get your Chat ID (`TELEGRAM_CHAT_ID`).
5. **Important**: Send a message to your new bot (e.g., "/start") so it has permission to message you.

### NVIDIA NIM (Optional Fallback)
1. Go to [build.nvidia.com](https://build.nvidia.com/).
2. Create an account or sign in.
3. Go to your dashboard and generate an API key (`NVIDIA_NIM_API_KEY`).

## 2. Add Secrets to GitHub

1. Go to your GitHub repository in the browser.
2. Click on **Settings** (the gear icon at the top right of the repo).
3. In the left sidebar, scroll down to **Secrets and variables** and click on **Actions**.
4. Click the green **New repository secret** button.
5. Add the following secrets one by one:

   - **Name:** `APIFY_API_TOKEN`
   - **Secret:** `your_apify_api_token`

   - **Name:** `GROK_API_KEY`
   - **Secret:** `your_groq_api_key`

   - **Name:** `TELEGRAM_BOT_TOKEN` 
   - **Secret:** `your_bot_token_from_botfather`

   - **Name:** `TELEGRAM_CHAT_ID`
   - **Secret:** `your_chat_id`

   - **Name:** `NVIDIA_NIM_API_KEY` (Optional)
   - **Secret:** `your_nvidia_api_key`

## 3. Verify GitHub Actions Run

1. Go to the **Actions** tab in your repository.
2. Click on the **Daily Job Match** workflow on the left.
3. Click the **Run workflow** dropdown on the right and click the green **Run workflow** button.
4. Wait a few minutes for it to complete.
5. Check your Telegram app for the daily report!