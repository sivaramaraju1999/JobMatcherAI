"""
Main orchestrator for the Job Matching AI system
Ties together scraping, matching, resume tailoring, and output generation
Based on the conversation history: targeting 60-70% initial match → 95% after tailoring
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import time

# Import our custom modules
from config import Config
from scrapers import JobScraperOrchestrator, JobListing
from resume_matcher import ResumeMatcher, ResumeStorage

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOGS_DIR / f"job_matcher_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class JobMatcherAI:
    """Main orchestrator for the job matching and resume tailoring system"""

    def __init__(self):
        self.config = Config()

        # Initialize job scrapers
        adapters = []

        apify_token = os.getenv('APIFY_API_TOKEN')
        if apify_token:
            try:
                from scrapers import ApifyLinkedInAdapter, ApifyNaukriAdapter, ApifyIndeedAdapter
                adapters.append(ApifyLinkedInAdapter(apify_token))
                adapters.append(ApifyNaukriAdapter(apify_token))
                adapters.append(ApifyIndeedAdapter(apify_token))
                logger.info("Initialized Apify actors for LinkedIn, Naukri, and Indeed")
            except Exception as e:
                logger.warning(f"Failed to initialize Apify adapters: {e}")
        else:
            logger.warning("APIFY_API_TOKEN not found in environment. Please add it to your .env file or GitHub Secrets. No scraping will occur.")

        # Create the orchestrator with our adapters
        self.scraper = JobScraperOrchestrator(adapters)
        logger.info(f"Initialized JobScraperOrchestrator with {len(adapters)} adapters")

        self.resume_matcher = ResumeMatcher()
        self.resume_storage = ResumeStorage(self.config)

        # Load base resume
        self.base_resume = self.resume_storage.load_base_resume()
        logger.info("Base resume loaded")

        # Load keywords from file or environment
        self.keywords = self._load_keywords()
        logger.info(f"Loaded keywords: {self.keywords}")

    def _load_keywords(self) -> Dict[str, List[str]]:
        """Load keywords from keywords.json file or environment variables"""
        keywords_file = self.config.BASE_DIR / "keywords.json"

        # Try to load from file first
        if keywords_file.exists():
            try:
                with open(keywords_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load keywords from {keywords_file}: {e}")

        # Fall back to environment variables or defaults
        roles_env = os.getenv('TARGET_ROLES', ','.join(self.config.DEFAULT_KEYWORDS['roles']))
        tech_env = os.getenv('TARGET_TECHNOLOGIES', ','.join(self.config.DEFAULT_KEYWORDS['technologies']))
        exp_env = os.getenv('TARGET_EXPERIENCE_LEVELS', ','.join(self.config.DEFAULT_KEYWORDS['experience_levels']))

        return {
            'roles': [r.strip() for r in roles_env.split(',') if r.strip()],
            'technologies': [t.strip() for t in tech_env.split(',') if t.strip()],
            'experience_levels': [e.strip() for e in exp_env.split(',') if e.strip()]
        }

    def _save_results(self, results: List[Dict[str, Any]]) -> None:
        """Save results to JSON file"""
        if not results:
            logger.warning("No results to save")
            return

        # Ensure output directory exists
        self.config.RESUMES_DIR.mkdir(parents=True, exist_ok=True)

        # Create timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.config.RESUMES_DIR / f"job_matches_{timestamp}.json"

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"Results saved to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")

    def run(self) -> List[Dict[str, Any]]:
        """Main execution loop"""
        logger.info("Starting Job Matching AI system")
        results = []

        try:
            # Process each role category
            for role_category, role_list in self.keywords.items():
                if not role_list:
                    continue

                logger.info(f"Processing {role_category}: {role_list}")

                # For each role in the category, search for jobs
                for role in role_list[:3]:  # Limit to top 3 roles per category to avoid too many requests
                    logger.info(f"Searching for jobs: {role}")

                    # Determine location (use first target location or default)
                    location = self.config.TARGET_LOCATIONS[0] if self.config.TARGET_LOCATIONS else "any"

                    # Search for jobs
                    jobs = self.scraper.search_all([role], location)
                    logger.info(f"Found {len(jobs)} jobs for {role}")

                    # Process each job
                    for job in jobs[:5]:  # Limit to top 5 jobs per search to avoid too much processing
                        logger.info(f"Processing job: {job.title} at {job.company}")

                        # Calculate initial match score
                        match_score, missing_keywords, matching_keywords = self.resume_matcher.calculate_match_score(
                            self.base_resume, job.description
                        )

                        logger.info(f"Initial match score: {match_score:.1f}%")

                        result = {
                            'company': job.company,
                            'position': job.title,
                            'match_percentage': match_score,
                            'apply_link': job.application_url,
                            'salary': job.salary_range,
                            'location': job.location,
                            'source': job.source,
                            'missing_keywords': missing_keywords,
                            'matching_keywords': matching_keywords
                        }

                        results.append(result)
                        logger.info(f"Completed processing for {job.title} at {job.company}")

                    # Be nice to APIs - delay between role searches
                    time.sleep(2)

            # Save all results
            self._save_results(results)

            logger.info(f"Job matching completed. Processed {len(results)} jobs.")
            return results

        except Exception as e:
            logger.error(f"Error in main execution loop: {e}")
            return results

if __name__ == "__main__":
    # Run the job matching system
    matcher = JobMatcherAI()
    results = matcher.run()

    # Print summary
    print("\n" + "="*60)
    print("JOB MATCHING AI - EXECUTION SUMMARY")
    print("="*60)
    print(f"Total jobs processed: {len(results)}")

    if results:
        print("\nTop matches:")
        # Sort by match percentage descending
        sorted_results = sorted(results, key=lambda x: x['match_percentage'], reverse=True)
        for i, result in enumerate(sorted_results, 1):
            print(f"{i}. {result['company']} - {result['match_percentage']:.1f}% Match - Link: {result['apply_link']}")
    else:
        print("No jobs were processed. Check logs for details.")
        print("Note: This may be expected if API keys for job boards are not configured.")
        print("The system is designed to work with NVIDIA NIM for resume optimization even without job scraping.")

    print("="*60)