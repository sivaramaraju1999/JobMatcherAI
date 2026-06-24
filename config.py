import os
from pathlib import Path
from dotenv import load_dotenv  # type: ignore


# Load environment variables from .env file in the base directory
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / '.env')

class Config:
    BASE_DIR = BASE_DIR
    # Hyper-focused keywords to eliminate non-QA and hardware role bleeding
    DEFAULT_KEYWORDS = {
        'roles': [
            'Senior SDET',
            'Software Development Engineer in Test',
            'Software Quality Engineer',
            'Test Automation Engineer',
            'QA Framework Architect',
            'Automation Test Engineer',
            'QA Lead',
            'Automation Engineer'
        ],
        'technologies': [
            'Java', 
            'Java 21',
            'Python', 
            'SQL', 
            'NoSQL', 
            'REST API', 
            'Jenkins', 
            'GitHub Actions', 
            'GitLab CI', 
            'Docker', 
            'AWS', 
            'MySQL', 
            'PostgreSQL', 
            'Oracle', 
            'Snowflake', 
            'MongoDB', 
            'Redis', 
            'DynamoDB', 
            'Selenium', 
            'Selenium WebDriver',
            'Playwright', 
            'RestAssured', 
            'JMeter', 
            'Cucumber BDD', 
            'TestNG',
            'Healenium',
            'Allure'
        ],
        'experience_levels': [
            'Senior',
            'Lead',
            'Architect',
            'Mid-Senior'
        ]
    }

    # Strict target regional constraints matching your search parameters
    TARGET_LOCATIONS = [
        'Hyderabad',
        'Secunderabad',
        'HITEC City',
        'Gachibowli',
        'Remote',
        'Remote-India',
        'Work from Home',
        'WFH',
        'Hybrid'
    ]

    # Cleaned target enterprise clusters (Duplicates removed)
    TARGET_COMPANIES = [
        # MAANG / Tier 1 Engineering Portals
        'Meta', 'Apple', 'Amazon', 'Netflix', 'Google', 'Microsoft',
        
        # Enterprise Platforms & High-Value GCC Hubs
        'ServiceNow', 'Salesforce', 'Oracle', 'IBM', 'Intel', 'Cisco', 
        'Adobe', 'NVIDIA', 'AMD', 'Qualcomm', 'SAP', 'VMware', 'Citrix', 
        'PayPal', 'Stripe', 'Uber', 'Lyft', 'Airbnb', 'Spotify', 'Twitter/X', 
        'LinkedIn', 'Square', 'Shopify', 'Instacart', 'DoorDash', 'Reddit', 
        'Pinterest', 'Snapchat', 'TikTok', 'ByteDance', 'Medium', 'Dropbox',
        
        # Large Scale Tech Integrators
        'Accenture', 'TCS', 'Infosys', 'Wipro', 'HCL Tech', 'Tech Mahindra', 
        'Persistent Systems', 'Zensar', 'Cyient', 'Mphasis', 'Hexaware', 
        'Honeywell', 'GE', 'Siemens', 'Bosch', 'Philips'
    ]

    # Dynamically falls back to your actual 3+ years experience summary profile
    TARGET_EXPERIENCE_YEARS = int(os.getenv('TARGET_EXPERIENCE_YEARS', '3'))

    # Match thresholds for initial gatekeeper filter loops
    INITIAL_MATCH_THRESHOLD = int(os.getenv('INITIAL_MATCH_THRESHOLD', '60'))

    # Directory Structure Mappings
    OUTPUT_DIR = BASE_DIR / "outputs"
    LOGS_DIR = BASE_DIR / "logs"
    CACHE_DIR = BASE_DIR / "cache"

    # Synchronize physical workspace folders
    def __init__(self):
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Resume File Address Routing
    BASE_RESUME_PATH = BASE_DIR / "resumes" / "Sivaramaraju_Kalidindi_Resume_2026.pdf"
    BASE_RESUME_TEXT = ""  # Populated dynamically by PdfReader engine