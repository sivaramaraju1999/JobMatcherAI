# Job Matcher AI - Automated Job Matching & Resume Tailoring System

An automated system that scrapes job listings from various platforms, matches them against your resume, and tailors your resume to achieve a 95% ATS match score for suitable positions.

## Features

- **Multi-Platform Job Scraping**: 
  - Direct API integration with Amazon Jobs, Microsoft Careers
  - Workday-based career sites (Fortune 500 companies)
  - Greenhouse and Lever job boards (tech startups and mid-size companies)
  - Extensible architecture for adding more platforms

- **Smart Resume Matching**:
  - Initial matching target: 60-70% similarity
  - Automatic resume optimization to reach 95%+ match
  - Keyword extraction and integration
  - No fabrication - only uses your actual experience

- **Output Format** (as requested):
  ```
  1. Company Name: [ServiceNow]
  2. Optimized Resume: [file path]
  3. Direct Apply Link: [URL]
  ```
  Plus salary information for bargaining

- **Automated Workflow**:
  - Daily job scraping
  - Intelligent matching and filtering
  - Resume tailoring and saving
  - Detailed reporting

## System Architecture

![Architecture](https://via.placeholder.com/800x400?text=Job+Matcher+AI+Architecture)

1. **Job Scrapers** - Platform-specific adapters that normalize job data
2. **Orchestrator** - Manages multiple scrapers and deduplicates results
3. **Resume Matcher** - Calculates match scores and identifies gaps
4. **Resume Optimizer** - Strategically adds missing keywords
5. **Storage** - Saves optimized resumes and generates reports

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
   - Base resume text or file path
   - Optional API keys (for enhanced scraping)
   - Telegram bot token (for notifications - optional)
   - Experience level and location preferences

4. **Prepare your resume**:
   - Place your base resume (text format) in the `resumes/` folder
   - Or set `BASE_RESUME_TEXT` in your `.env` file
   - The system works best with a plain text version of your resume

## Usage

Run the complete system:
```bash
python main.py
```

For a demonstration with sample data:
```bash
python demo.py
```

## Configuration

### Key Configuration Options (`config.py`):

- `TARGET_LOCATIONS`: Locations to target (Hyderabad, Remote, etc.)
- `TARGET_COMPANIES**: List of target companies (Fortune 500, MAANG/FAANG, etc.)
- `TARGET_EXPERIENCE_YEARS`: Your years of experience for salary bargaining
- `INITIAL_MATCH_THRESHOLD`: Minimum % match to consider tailoring (default: 60)
- `TARGET_MATCH_THRESHOLD`: Target % match after tailoring (default: 95)

### Environment Variables (`.env`):

```
# Resume Configuration
BASE_RESUME_PATH=./resumes/my_resume.txt
# OR
BASE_RESUME_TEXT=Your resume text here...

# Experience & Location
TARGET_EXPERIENCE_YEARS=8
TARGET_LOCATIONS=Hyderabad,Remote,Hybrid
TARGET_ROLES=Software Engineer,Senior Software Engineer,Lead Software Engineer

# Match Thresholds
INITIAL_MATCH_THRESHOLD=60
TARGET_MATCH_THRESHOLD=95

# Salary Expectations (LPA - Lakhs Per Annum)
MIN_EXPECTED_SALARY_LPA=25
MAX_EXPECTED_SALARY_LPA=60

# Optional: Telegram notifications
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Optional: API keys for enhanced scraping (some work without keys)
# NOKRI_API_KEY=your_naukri_key
# LINKEDIN_API_KEY=your_linkedin_key
```

## Output Format

When the system finds a matching job, it produces output in the exact format you requested:

```
1. Company Name: ServiceNow
2. Optimized Resume: C:\Users\user\JobMatcherAI\outputs\resumes\ServiceNow_Senior_Software_Engineer_Optimized_Resume.txt
3. Direct Apply Link: https://servicenow.wd5.myworkdayjobs.com/en-US/Careers/job/Hyderabad/Senior-Software-Engineer_JR1029432
   Salary for Bargaining: 25-35 LPA
   Match Percentage: 92.5%
```

## Supported Platforms

### Direct API Integration (No API Key Required for Basic Use):
- **Amazon Jobs** - `https://www.amazon.jobs/en/search.json`
- **Microsoft Careers** - `https://careers.microsoft.com/api/search/searchjobs`

### Workday-Based Sites (Fortune 500 Companies):
- ServiceNow, Salesforce, Oracle, IBM, Intel, Cisco, Adobe, NVIDIA, AMD, and many more
- Uses pattern: `https://{company}.wd5.myworkdayjobs.com/wday/cxs/{company}/{career_site_id}/jobs`

### Job Board Platforms:
- **Greenhouse** - Airbnb, Uber, Lyft, Stripe, Shopify, etc.
- **Lever** - Netflix, Shopify, Atlassian, etc.

### Extensible Architecture:
New platforms can be added by creating a new class that inherits from `JobScraperAdapter` and implementing the `fetch_jobs` method.

## How It Works

### 1. Job Collection
- Queries multiple job platforms using your target keywords and locations
- Normalizes all job data to a common format: `{title, company, description, application_url, location, salary_range, source}`
- Deduplicates jobs using application URL as primary key
- Normalizes location (e.g., "Hyd", "Secunderabad" → "Hyderabad")
- Normalizes salary to LPA (Lakhs Per Annam) format for easy comparison

### 2. Resume Matching
- Extracts keywords from both resume and job description using TF-IDF and custom keyword extraction
- Calculates match score combining keyword overlap (60%) and semantic similarity (40%)
- Identifies missing keywords that would improve the match
- Only processes jobs with initial match between 60-70% (your "sweet spot" for tailoring)

### 3. Resume Optimization
- Strategically integrates missing keywords into:
  - Professional Summary section
  - Skills/Technical Expertise section
  - Existing bullet points (contextually where appropriate)
- Maintains strict adherence to your actual experience (no fabrication)
- Outputs optimized resume as text file (easily convertible to PDF/DOCX)

### 4. Reporting & Output
- Saves each optimized resume to `outputs/resumes/` with descriptive filenames
- Prints results in your requested format to console
- Generates detailed daily reports in `logs/`
- Maintains SQLite cache of processed jobs to avoid duplicate work

## Customization

### Adding New Job Platforms
1. Create a new class in `scrapers.py` that inherits from `JobScraperAdapter`
2. Implement the `fetch_jobs(keywords, location)` method
3. Add your scraper to the `scrapers` list in `JobScraperOrchestrator.__init__`
4. Follow the pattern of returning `JobListing` objects

### Changing Matching Algorithm
Modify the `ResumeMatcher` class in `resume_matcher.py`:
- Adjust keyword extraction logic in `extract_keywords()`
- Change weighting in `calculate_match_score()` 
- Enhance optimization strategies in `optimize_resume()`

### Output Formats
To change resume output format (DOCX, PDF, etc.):
- Modify the `save_text_to_docx()` method in `main.py`
- Or replace it with your preferred document generation library

## Requirements

See `requirements.txt` for exact versions:
- `requests>=2.25.1` - HTTP requests for API calls
- `python-dotenv>=0.19.0` - Environment variable management

## Ethical Usage & Disclaimer

⚠️ **Important Usage Guidelines**:

1. **Truthfulness**: This tool is designed to help you **truthfully** present your existing skills better matched to job descriptions. **Do not** use it to fabricate experience, skills, or qualifications.

2. **Rate Limiting**: Be respectful of target websites. The built-in delays (1 second between requests) help prevent overwhelming servers.

3. **Terms of Service**: Ensure your usage complies with each website's terms of service and robots.txt guidelines.

4. **Personal Use Only**: This tool is intended for personal job search assistance. Commercial redistribution or bulk scraping for resale is prohibited.

5. **Verification**: Always review tailored resumes before submission to ensure accuracy.

## Troubleshooting

### Common Issues:

**"No jobs found"**:
- Check your keywords and location settings
- Try broader search terms (e.g., "Engineer" instead of "Staff Engineer")
- Verify internet connectivity
- Some sites may block automated requests (consider using official APIs where available)

**Low match scores**:
- Ensure your base resume contains relevant keywords
- Consider adding a "Skills" or "Technical Expertise" section if missing
- The system works best when you have 60-70% baseline match

**Installation problems**:
- Ensure you have Python 3.8+
- Try installing packages individually if bundle fails: `pip install requests scikit-learn numpy python-dotenv`

## Future Enhancements

Planned features for future versions:
- [ ] LinkedIn and Naukri integration (via official APIs or careful scraping)
- [ ] Automatic PDF/DOCX resume generation
- [ ] Email notifications in addition to Telegram
- [ ] Interview preparation question generation based on job description
- [ ] Salary negotiation talking points based on role, company, and location
- [ ] Application tracking and follow-up reminders

## License

This project is for personal use. Please respect website terms of service and use responsibly.

---

**Ready to automate your job search?** Run `python demo.py` to see the system in action with sample data, then configure with your own resume and preferences!