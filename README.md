# Job Matcher AI - Automated Job Matching System

An automated system that scrapes job listings using robust Apify actors, scores them against your resume using LLMs (Groq/NVIDIA NIM), and sends you the top daily matches directly via Telegram.

## Features

- **Robust Cloud Scraping (Apify)**: 
  - Integrated with `curious-coder/linkedin-jobs-scraper` for LinkedIn.
  - Integrated with `themineworks/naukri-jobs` for Naukri.
  - Integrated with `apify/indeed-scraper` for Indeed.
  - No need to maintain brittle Selenium/Playwright scripts.

- **Smart Resume Scoring**:
  - Uses Groq or NVIDIA NIM to calculate an intelligent match score between your base resume and the job description.
  - No fabricated resume writing—just pure, honest matching based on your real experience.

- **Automated Workflow**:
  - Runs daily via GitHub Actions.
  - Outputs a clean list of top matches.
  - Sends the daily report directly to your phone via Telegram.

- **Clean Output Format**:
  ```
  1. ServiceNow - 92.5% Match - Link: https://...
  2. Amazon - 85.0% Match - Link: https://...
  ```

## System Architecture

1. **Job Scrapers (Apify Actors)** - Fetches normalized job data securely.
2. **Orchestrator** - Manages multiple scrapers and deduplicates results.
3. **Resume Matcher** - Calculates match scores using LLMs.
4. **Notifier** - Pushes the final sorted list to Telegram.

## Installation

1. **Clone or copy this repository**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment** (copy example):
   ```bash
   cp .env.example .env
   ```
   Edit `.env` to add your:
   - `APIFY_API_TOKEN` (Required for scraping)
   - `GROK_API_KEY` or `NVIDIA_NIM_API_KEY` (For LLM scoring)
   - `TELEGRAM_BOT_TOKEN` & `TELEGRAM_CHAT_ID` (For daily notifications)

4. **Prepare your resume**:
   - Place your base resume (PDF or text format) in the `resumes/` folder, ensuring `BASE_RESUME_PATH` points to it in `config.py`.

## Usage

Run the complete system locally:
```bash
python main.py
```

## GitHub Actions Automated Deployment

This system is designed to run completely hands-off every morning.

1. Go to your GitHub Repository -> **Settings** -> **Secrets and variables** -> **Actions**
2. Add the following repository secrets:
   - `APIFY_API_TOKEN`
   - `GROK_API_KEY`
   - `NVIDIA_NIM_API_KEY`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`

The GitHub Action (`.github/workflows/daily-job-match.yml`) will run every day at 09:00 UTC and push the results to your Telegram chat.

## Ethical Usage Guidelines

⚠️ **Important**: This tool is designed to help you quickly identify jobs that match your existing skills.
- Be respectful of target websites. Apify handles rate-limiting and rotating proxies natively.
- This project is for personal use to streamline your job search.

## License

This project is for personal use. Please respect website terms of service and use responsibly.