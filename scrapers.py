"""
Job scraping adapters for various platforms.
Supports Amazon Jobs, Microsoft Careers, Workday, Greenhouse, Lever.
"""

import json
import time
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, quote_plus
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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

    def __init__(self, company_name: str, base_url: str = ""):
        self.company_name = company_name
        self.base_url = base_url
        self.session = self._create_session()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        return session

    def normalize_location(self, location: str) -> str:
        """Normalize location string for comparison"""
        if not location:
            return ""
        # Convert to lowercase, strip, and normalize common variations
        location = location.lower().strip()
        # Handle common variations
        location = re.sub(r'[\s\-_]+', ' ', location)  # Replace spaces/hyphens/underscores with space
        location = re.sub(r'[^\w\s]', '', location)    # Remove punctuation
        return location

    def normalize_salary(self, salary_str: str) -> str:
        """Normalize salary string"""
        if not salary_str:
            return ""
        # Remove extra whitespace
        salary_str = re.sub(r'\s+', ' ', salary_str.strip())
        return salary_str

    @abstractmethod
    def fetch_jobs(self, keywords: List[str], location: str) -> List[JobListing]:
        """Fetch jobs based on keywords and location"""
        pass

class AmazonJobsAdapter(JobScraperAdapter):
    """Adapter for Amazon Jobs"""

    def __init__(self):
        super().__init__("Amazon", "https://www.amazon.jobs")

    def fetch_jobs(self, keywords: List[str], location: str) -> List[JobListing]:
        jobs = []
        try:
            # Build search query
            query = " ".join(keywords[:3])  # Limit keywords
            url = f"https://www.amazon.jobs/en/search.json"
            params = {
                "offset": 0,
                "result_limit": 50,
                "sort": "recent",
                "keyword": query,
                "location": location,
                "distance": 25
            }

            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            for job in data.get("jobs", []):
                job_listing = JobListing(
                    title=job.get("title", ""),
                    company="Amazon",
                    description=job.get("description", ""),
                    application_url=job.get("job_path", ""),
                    location=job.get("location", ""),
                    salary_range=job.get("compensation", ""),
                    source="Amazon Jobs",
                    posted_date=job.get("posted_date"),
                    raw_data=job
                )
                jobs.append(job_listing)

        except Exception as e:
            self.logger.error(f"Error fetching Amazon jobs: {e}")

        return jobs

class MicrosoftCareersAdapter(JobScraperAdapter):
    """Adapter for Microsoft Careers"""

    def __init__(self):
        super().__init__("Microsoft", "https://careers.microsoft.com")

    def fetch_jobs(self, keywords: List[str], location: str) -> List[JobListing]:
        jobs = []
        try:
            query = " ".join(keywords[:3])
            url = "https://careers.microsoft.com/v1.0/search"
            params = {
                "appsOpen": "false",
                "country": "us",  # TODO: make configurable
                "skip": 0,
                "take": 25,
                "keywords": query,
                "location": location
            }

            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            for job in data.get("operationResult", {}).get("result", {}).get("jobs", []):
                job_listing = JobListing(
                    title=job.get("title", ""),
                    company="Microsoft",
                    description=job.get("description", ""),
                    application_url=job.get("applyUrl", ""),
                    location=job.get("city", ""),
                    salary_range="",  # Microsoft doesn't usually provide salary in API
                    source="Microsoft Careers",
                    posted_date=job.get("postedDate"),
                    raw_data=job
                )
                jobs.append(job_listing)

        except Exception as e:
            self.logger.error(f"Error fetching Microsoft jobs: {e}")

        return jobs

class WorkdayAdapter(JobScraperAdapter):
    """Adapter for Workday-based career sites"""

    def __init__(self, company_name: str, wd_host: str, wd_site: str, wd_company: str):
        super().__init__(company_name)
        # Construct the API endpoint for Workday
        self.api_url = f"https://{wd_host}/wd/x/{wd_company}/{wd_site}/apply/json"
        self.wd_company = wd_company
        self.wd_site = wd_site

    def fetch_jobs(self, keywords: List[str], location: str) -> List[JobListing]:
        jobs = []
        try:
            query = " ".join(keywords[:3])
            # Workday API format may vary; this is a common pattern
            payload = {
                "appliedFields": [],
                "searchText": query,
                "locationHierarchy": [],
                "limit": 20,
                "offset": 0
            }

            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            response = self.session.post(self.api_url, json=payload, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()

            # Parse response based on Workday schema
            for job_group in data.get("body", {}).get("children", []):
                for job_item in job_group.get("children", []):
                    if "title" in job_item:
                        job_listing = JobListing(
                            title=job_item.get("title", ""),
                            company=self.company_name,
                            description=job_item.get("jobDescription", ""),
                            application_url=job_item.get("externalPath", ""),
                            location=job_item.get("locationsText", ""),
                            salary_range="",
                            source=f"Workday ({self.company_name})",
                            posted_date=job_item.postedOn if "postedOn" in job_item else None,
                            raw_data=job_item
                        )
                        jobs.append(job_listing)

        except Exception as e:
            self.logger.error(f"Error fetching Workday jobs for {self.company_name}: {e}")

        return jobs

class GreenhouseAdapter(JobScraperAdapter):
    """Adapter for Greenhouse"""

    def __init__(self, company_name: str, greenhouse_token: str):
        super().__init__(company_name)
        self.greenhouse_token = greenhouse_token
        self.api_url = f"https://boards-api.greenhouse.io/v1/boards/{greenhouse_token}/jobs"

    def fetch_jobs(self, keywords: List[str], location: str) -> List[JobListing]:
        jobs = []
        try:
            params = {
                "content": "true"
            }

            response = self.session.get(self.api_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            for job in data.get("jobs", []):
                # Filter by location if specified
                job_location = job.get("location", {}).get("name", "")
                if location.lower() != "any" and location.lower() not in job_location.lower():
                    continue

                job_listing = JobListing(
                    title=job.get("title", ""),
                    company=self.company_name,
                    description=job.get("content", ""),
                    application_url=job.get("absolute_url", ""),
                    location=job_location,
                    salary_range="",  # Greenhouse doesn't always provide salary
                    source=f"Greenhouse ({self.company_name})",
                    posted_date=job.get("updated_at"),
                    raw_data=job
                )
                jobs.append(job_listing)

        except Exception as e:
            self.logger.error(f"Error fetching Greenhouse jobs for {self.company_name}: {e}")

        return jobs

class LeverAdapter(JobScraperAdapter):
    """Adapter for Lever"""

    def __init__(self, company_name: str):
        super().__init__(company_name)
        self.api_url = f"https://api.lever.co/v0/postings/{company_name.lower()}?mode=json"

    def fetch_jobs(self, keywords: List[str], location: str) -> List[JobListing]:
        jobs = []
        try:
            response = self.session.get(self.api_url, timeout=15)
            response.raise_for_status()
            data = response.json()

            for job in data:
                # Filter by location if specified
                job_location = job.get("categories", {}).get("location", "")
                if location.lower() != "any" and location.lower() not in job_location.lower():
                    continue

                job_listing = JobListing(
                    title=job.get("text", ""),
                    company=self.company_name,
                    description=job.get("description", ""),
                    application_url=job.get("hostedUrl", ""),
                    location=job_location,
                    salary_range=job.get("compensation", ""),
                    source=f"Lever ({self.company_name})",
                    posted_date=job.get("createdAt"),
                    raw_data=job
                )
                jobs.append(job_listing)

        except Exception as e:
            self.logger.error(f"Error fetching Lever jobs for {self.company_name}: {e}")

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