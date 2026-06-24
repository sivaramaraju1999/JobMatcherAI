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
from scrapers import JobScraperOrchestrator, JobListing, AmazonJobsAdapter, MicrosoftCareersAdapter
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

        # Initialize job scrapers - start with those that don't require API keys
        adapters = []

        # Add Amazon Jobs adapter (no API key required)
        try:
            adapters.append(AmazonJobsAdapter())
            logger.info("Initialized Amazon Jobs adapter")
        except Exception as e:
            logger.warning(f"Failed to initialize Amazon Jobs adapter: {e}")

        # Add Microsoft Careers adapter (no API key required)
        try:
            adapters.append(MicrosoftCareersAdapter())
            logger.info("Initialized Microsoft Careers adapter")
        except Exception as e:
            logger.warning(f"Failed to initialize Microsoft Careers adapter: {e}")

        # Optional: Add adapters that require API keys if credentials are available
        # Greenhouse Adapter (requires token)
        greenhouse_token = os.getenv('GREENHOUSE_TOKEN')
        if greenhouse_token:
            try:
                # Note: In a real implementation, you'd specify which companies to track
                # For demo, we'll use a placeholder - in practice, you'd configure specific companies
                from scrapers import GreenhouseAdapter
                adapters.append(GreenhouseAdapter("demo_company", greenhouse_token))
                logger.info("Initialized Greenhouse adapter")
            except Exception as e:
                logger.warning(f"Failed to initialize Greenhouse adapter: {e}")
        else:
            logger.info("Greenhouse token not provided - skipping Greenhouse adapter")

        # Lever Adapter (requires company name - no token needed for public companies)
        lever_company = os.getenv('LEVER_COMPANY')
        if lever_company:
            try:
                from scrapers import LeverAdapter
                adapters.append(LeverAdapter(lever_company))
                logger.info(f"Initialized Lever adapter for {lever_company}")
            except Exception as e:
                logger.warning(f"Failed to initialize Lever adapter for {lever_company}: {e}")
        else:
            # Add a few common tech companies that use Lever as examples
            lever_companies = ["netflix", "shopify", "videoconferencing"]  # Examples
            for company in lever_companies:
                try:
                    from scrapers import LeverAdapter
                    adapters.append(LeverAdapter(company))
                    logger.info(f"Initialized Lever adapter for {company}")
                except Exception as e:
                    logger.debug(f"Could not initialize Lever adapter for {company}: {e}")

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

                        # If initial match is below threshold, try to optimize resume
                        if match_score < self.config.TARGET_MATCH_THRESHOLD:
                            logger.info(f"Attempting to optimize resume for {self.config.TARGET_MATCH_THRESHOLD}% match")
                            match_result = self.resume_matcher.optimize_resume(
                                self.base_resume, job.description, self.config.TARGET_MATCH_THRESHOLD
                            )

                            # Save optimized resume
                            resume_filename = f"{job.company}_{job.title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                            resume_path = self.resume_storage.save_resume(
                                match_result.optimized_resume_text, resume_filename
                            )

                            result = {
                                'company': job.company,
                                'position': job.title,
                                'match_percentage': match_result.match_score,
                                'resume_path': resume_path,
                                'apply_link': job.application_url,
                                'salary': job.salary_range,
                                'location': job.location,
                                'source': job.source,
                                'missing_keywords': missing_keywords,
                                'matching_keywords': matching_keywords,
                                'optimization_suggestions': match_result.suggestions
                            }
                        else:
                            # Use original resume if already meets threshold
                            resume_filename = f"{job.company}_{job.title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_original.txt"
                            resume_path = self.resume_storage.save_resume(
                                self.base_resume, resume_filename
                            )

                            result = {
                                'company': job.company,
                                'position': job.title,
                                'match_percentage': match_score,
                                'resume_path': resume_path,
                                'apply_link': job.application_url,
                                'salary': job.salary_range,
                                'location': job.location,
                                'source': job.source,
                                'missing_keywords': missing_keywords,
                                'matching_keywords': matching_keywords,
                                'optimization_suggestions': ["Resume already meets target match threshold"]
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
        for i, result in enumerate(sorted_results[:5], 1):  # Top 5
            print(f"{i}. {result['position']} at {result['company']} - {result['match_percentage']:.1f}% match")
            print(f"   Resume saved to: {result['resume_path']}")
            print(f"   Apply here: {result['apply_link']}")
            if result['salary']:
                print(f"   Salary: {result['salary']}")
            print()
    else:
        print("No jobs were processed. Check logs for details.")
        print("Note: This may be expected if API keys for job boards are not configured.")
        print("The system is designed to work with NVIDIA NIM for resume optimization even without job scraping.")

    print("="*60)