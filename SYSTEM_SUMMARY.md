# Job Matcher AI - System Summary

## Overview
This system automates job matching by scraping job boards via Apify, scoring them against your base resume using powerful LLMs, and sending you the top results via Telegram on a daily basis.

## Core Components

### 1. Configuration System (`config.py`)
- Defines target locations (Hyderabad, Remote, etc.)
- Lists target companies (Fortune 500, MAANG/FAANG, etc.)
- Sets experience level for salary bargaining
- Manages file paths for outputs, logs, and cache

### 2. Job Scraping System (`scrapers.py`)
- Uses the `apify-client` python SDK.
- **ApifyLinkedInAdapter** - Uses the `curious-coder/linkedin-jobs-scraper` actor.
- **ApifyNaukriAdapter** - Uses the `themineworks/naukri-jobs` actor.
- **ApifyIndeedAdapter** - Uses the `apify/indeed-scraper` actor.
- **Orchestrator** - Manages all scrapers and deduplicates results to prevent redundant processing.

### 3. Resume Scoring (`resume_matcher.py`)
- **LLM Routing** - Tries Groq first (fastest/cheapest), falls back to NVIDIA NIM, and finally a local Regex system if all APIs fail.
- **Match Scoring** - Analyzes the job description against your `BASE_RESUME` and calculates an accurate, honest match score.

### 4. Main Orchestrator (`main.py`)
- Executes the daily job scraping process.
- Passes scraped jobs to the LLMs for scoring.
- Sorts results by match percentage.
- **Notification Integration** - Bundles the top jobs into a clean text format and posts an HTTP request directly to your Telegram Chat ID.

### 5. Keywords Configuration (`keywords.json`)
- Comprehensive list of job roles, technologies, and experience levels.
- Easily customizable via environment variables or file.

## How It Works

### Step 1: Job Collection
- Connects to Apify to spin up headless browser instances on the cloud.
- Scrapes the latest postings from LinkedIn, Naukri, and Indeed.
- Normalizes all job data to a common format: `{title, company, description, url, location, salary}`.
- Deduplicates using application URL as primary key.

### Step 2: Resume Matching & Scoring
- Sends your base resume and the job description to Groq/NVIDIA.
- Calculates a percentage match score based strictly on actual skills.

### Step 3: Notification Delivery
- Saves the full JSON results locally in the `outputs/` directory for historical tracking.
- Formats a message containing the top jobs:
  `1. [Company] - [Score]% Match - Link: [URL]`
- Sends the message instantly to your Telegram via the Telegram Bot API.

## Installation & Setup

### Prerequisites
- Python 3.8+
- Accounts for Apify, Groq (or NVIDIA NIM), and Telegram.

### Setup Steps
1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` to set:
   - `BASE_RESUME_TEXT` or place resume in `resumes/` folder
   - `TARGET_EXPERIENCE_YEARS` (your years of experience)
   - `APIFY_API_TOKEN`
   - `GROK_API_KEY`
   - `TELEGRAM_BOT_TOKEN` & `TELEGRAM_CHAT_ID`

3. **Run the System**
   ```bash
   python main.py
   ```

## Files
```
JobMatcherAI/
├── config.py                 # Configuration management
├── .env.example              # Environment template
├── requirements.txt          # Python dependencies
├── keywords.json             # Job search keywords
├── main.py                   # Main orchestrator & Telegram Logic
├── scrapers.py               # Apify job scraping adapters
├── resume_matcher.py         # Resume scoring
├── resumes/                  # Base resume storage
│   └── Sivaramaraju_Kalidindi_Resume_2026.pdf
├── outputs/                  # JSON job match outputs
└── logs/                     # Application logs
```