"""
Job scraping adapters using Apify actors.
Supports LinkedIn, Naukri, and Indeed.
"""

import json
import time
import logging
import re
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

try:
    from apify_client import ApifyClient
    APIFY_AVAILABLE = True
except ImportError:
    APIFY_AVAILABLE = False

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

class ApifyLinkedInAdapter(JobScraperAdapter):
    """Adapter for curious-coder/linkedin-jobs-scraper"""

    def __init__(self, token: str):
        super().__init__("LinkedIn (Apify)")
        self.client = ApifyClient(token)

    def fetch_jobs(self, keywords: List[str], location: str) -> List[JobListing]:
        jobs = []
        if not APIFY_AVAILABLE:
            self.logger.error("Apify client not installed.")
            return jobs

        query = " ".join(keywords[:3])
        run_input = {
            "queries": f"{query} in {location}",
            "limit": 20,
            "publishedAt": "any",
            "searchType": "jobs"
        }
        
        try:
            self.logger.info(f"Starting LinkedIn Actor for {query} in {location}")
            run = self.client.actor("curious-coder/linkedin-jobs-scraper").call(run_input=run_input)
            dataset = self.client.dataset(run["defaultDatasetId"])
            
            for item in dataset.iterate_items():
                job_listing = JobListing(
                    title=item.get("title", ""),
                    company=item.get("companyName", ""),
                    description=item.get("description", ""),
                    application_url=item.get("url", ""),
                    location=item.get("location", ""),
                    salary_range="",
                    source="LinkedIn",
                    posted_date=item.get("postedAt"),
                    raw_data=item
                )
                jobs.append(job_listing)
        except Exception as e:
            self.logger.error(f"Error fetching LinkedIn jobs: {e}")

        return jobs

class ApifyNaukriAdapter(JobScraperAdapter):
    """Adapter for themineworks/naukri-jobs"""

    def __init__(self, token: str):
        super().__init__("Naukri (Apify)")
        self.client = ApifyClient(token)

    def fetch_jobs(self, keywords: List[str], location: str) -> List[JobListing]:
        jobs = []
        if not APIFY_AVAILABLE:
            return jobs

        query = " ".join(keywords[:3])
        run_input = {
            "keyword": query,
            "cities": location,
            "maxJobs": 20
        }
        
        try:
            self.logger.info(f"Starting Naukri Actor for {query} in {location}")
            run = self.client.actor("muhammetakkurtt/naukri-job-scraper").call(run_input=run_input)
            dataset = self.client.dataset(run["defaultDatasetId"])
            
            for item in dataset.iterate_items():
                job_listing = JobListing(
                    title=item.get("title", ""),
                    company=item.get("companyName", item.get("company", "")),
                    description=item.get("jobDescription", item.get("description", "")),
                    application_url=item.get("jobUrl", item.get("url", "")),
                    location=item.get("locations", item.get("location", "")),
                    salary_range=item.get("salary", item.get("salaryRange", "")),
                    source="Naukri",
                    posted_date=item.get("postedDate", item.get("postedAt", "")),
                    raw_data=item
                )
                jobs.append(job_listing)
        except Exception as e:
            self.logger.error(f"Error fetching Naukri jobs: {e}")

        return jobs

class ApifyIndeedAdapter(JobScraperAdapter):
    """Adapter for apify/indeed-scraper"""

    def __init__(self, token: str):
        super().__init__("Indeed (Apify)")
        self.client = ApifyClient(token)

    def fetch_jobs(self, keywords: List[str], location: str) -> List[JobListing]:
        jobs = []
        if not APIFY_AVAILABLE:
            return jobs

        query = " ".join(keywords[:3])
        run_input = {
            "query": query,
            "location": location,
            "country": "us",
            "maxRows": 20
        }
        
        try:
            self.logger.info(f"Starting Indeed Actor for {query} in {location}")
            run = self.client.actor("MXLpngmVpE8WTESQr").call(run_input=run_input)
            dataset = self.client.dataset(run["defaultDatasetId"])
            
            for item in dataset.iterate_items():
                job_listing = JobListing(
                    title=item.get("positionName", item.get("jobTitle", item.get("title", ""))),
                    company=item.get("company", item.get("companyName", "")),
                    description=item.get("description", item.get("jobDescription", "")),
                    application_url=item.get("url", item.get("jobUrl", "")),
                    location=item.get("location", ""),
                    salary_range=item.get("salary", item.get("salaryRange", "")),
                    source="Indeed",
                    posted_date=item.get("postedAt", item.get("datePosted", "")),
                    raw_data=item
                )
                jobs.append(job_listing)
        except Exception as e:
            self.logger.error(f"Error fetching Indeed jobs: {e}")

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