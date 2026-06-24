"""
Job scraping adapters using python-jobspy.
Supports LinkedIn, Naukri, Indeed, Glassdoor.
"""

import json
import time
import logging
import re
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import pandas as pd

try:
    # pyrefly: ignore [missing-import]
    from jobspy import scrape_jobs
    JOBSPY_AVAILABLE = True
except ImportError:
    JOBSPY_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class JobListing:
    """Represents a job listing"""
    title: str
    company: str
    description: str
    application_url: str
    location: str
    salary_range: str
    source: str
    posted_date: Optional[str] = None
    raw_data: dict = field(default_factory=dict)

class JobScraperAdapter(ABC):
    """Abstract base class for job scrapers"""

    def __init__(self, platform_name: str):
        self.company_name = platform_name # legacy name for compatibility
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def fetch_jobs(self, keywords: List[str], location: str) -> List[JobListing]:
        """Fetch jobs based on keywords and location"""
        pass

class JobSpyAdapter(JobScraperAdapter):
    """Adapter that uses python-jobspy for multiple sources"""

    def __init__(self, site_names: List[str] = None):
        super().__init__("JobSpy (LinkedIn, Indeed, Glassdoor, etc.)")
        if site_names is None:
            self.site_names = ["linkedin", "indeed", "glassdoor", "naukri"]
        else:
            self.site_names = site_names

    def fetch_jobs(self, keywords: List[str], location: str) -> List[JobListing]:
        jobs = []
        if not JOBSPY_AVAILABLE:
            self.logger.error("python-jobspy client not installed.")
            return jobs

        query = " ".join(keywords[:3])
        self.logger.info(f"Starting JobSpy search for '{query}' in '{location}' across {self.site_names}")

        try:
            df = scrape_jobs(
                site_name=self.site_names,
                search_term=query,
                location=location,
                results_wanted=20,
                country_indeed='USA',  # optional
            )
            
            if df is None or df.empty:
                self.logger.warning("JobSpy returned no jobs.")
                return jobs

            # Convert Pandas DataFrame rows to JobListing objects
            for index, row in df.iterrows():
                # Handling NaNs from pandas
                title = str(row.get("title", "")) if pd.notna(row.get("title")) else ""
                company = str(row.get("company", "")) if pd.notna(row.get("company")) else ""
                description = str(row.get("description", "")) if pd.notna(row.get("description")) else ""
                job_url = str(row.get("job_url", "")) if pd.notna(row.get("job_url")) else ""
                loc = str(row.get("location", "")) if pd.notna(row.get("location")) else ""
                
                # Format salary if present
                min_amount = row.get("min_amount")
                max_amount = row.get("max_amount")
                currency = row.get("currency", "USD")
                salary_range = ""
                if pd.notna(min_amount) and pd.notna(max_amount):
                    salary_range = f"{min_amount} - {max_amount} {currency}"
                elif pd.notna(min_amount):
                    salary_range = f"Min {min_amount} {currency}"
                elif pd.notna(max_amount):
                    salary_range = f"Max {max_amount} {currency}"

                source = str(row.get("site", "JobSpy")) if pd.notna(row.get("site")) else "JobSpy"
                date_posted = str(row.get("date_posted", "")) if pd.notna(row.get("date_posted")) else ""
                
                job_listing = JobListing(
                    title=title,
                    company=company,
                    description=description,
                    application_url=job_url,
                    location=loc,
                    salary_range=salary_range,
                    source=source.capitalize(),
                    posted_date=date_posted,
                    raw_data=row.to_dict()
                )
                jobs.append(job_listing)
                
            self.logger.info(f"JobSpy returned {len(jobs)} jobs.")

        except Exception as e:
            self.logger.error(f"Error fetching jobs with JobSpy: {e}")

        return jobs

class JobScraperOrchestrator:
    """Orchestrates multiple job scrapers"""

    def __init__(self, adapters: List[JobScraperAdapter]):
        self.adapters = adapters
        self.logger = logging.getLogger(f"{__name__}.JobScraperOrchestrator")

    def search_all(self, keywords: List[str], location: str) -> List[JobListing]:
        """Search all configured job sources"""
        all_jobs = []

        for adapter in self.adapters:
            try:
                self.logger.info(f"Searching {adapter.company_name} for '{' '.join(keywords[:3])}' in {location}")
                jobs = adapter.fetch_jobs(keywords, location)
                self.logger.info(f"Found {len(jobs)} jobs from {adapter.company_name}")
                all_jobs.extend(jobs)
                # Be nice to APIs - small delay between requests
                time.sleep(0.5)
            except Exception as e:
                self.logger.error(f"Error searching {adapter.company_name}: {e}")

        # Deduplicate by application URL (or title+company if URL missing)
        seen = set()
        unique_jobs = []
        for job in all_jobs:
            key = job.application_url if job.application_url else f"{job.title}|{job.company}|{job.location}"
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)

        self.logger.info(f"Total unique jobs after deduplication: {len(unique_jobs)}")
        return sorted(unique_jobs, key=lambda j: j.title.lower())