import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file in the base directory
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / '.env')

class Config:
    # Keywords for job matching (can be overridden by env vars or config file)
    DEFAULT_KEYWORDS = {
        'roles': [
            'Software Engineer',
            'Senior Software Engineer',
            'Lead Software Engineer',
            'Principal Engineer',
            'Architect',
            'Tech Lead',
            'Engineering Manager',
            'Full Stack Developer',
            'Backend Developer',
            'Frontend Developer',
            'DevOps Engineer',
            'Site Reliability Engineer',
            'Data Engineer',
            'Machine Learning Engineer',
            'AI Engineer',
            'Cloud Engineer',
            'Solutions Architect',
            'Technical Architect'
        ],
        'technologies': [
            'Python',
            'Java',
            'JavaScript',
            'TypeScript',
            'React',
            'Node.js',
            'AWS',
            'Azure',
            'GCP',
            'Docker',
            'Kubernetes',
            'Microservices',
            'REST API',
            'GraphQL',
            'SQL',
            'NoSQL',
            'MongoDB',
            'PostgreSQL',
            'MySQL',
            'Redis',
            'Elasticsearch',
            'Spring Boot',
            '.NET',
            'C#',
            'Go',
            'Rust',
            'Terraform',
            'Ansible',
            'Jenkins',
            'GitLab CI',
            'GitHub Actions',
            'Prometheus',
            'Grafana',
            'ELK Stack'
        ],
        'experience_levels': [
            'Senior',
            'Lead',
            'Principal',
            'Architect',
            'Manager',
            'Director',
            'VP',
            'Head of',
            'Staff',
            'Distinguished'
        ]
    }

    # Target locations
    TARGET_LOCATIONS = [
        'Hyderabad',
        'Remote',
        'Remote-India',
        'Work from Home',
        'WFH',
        'Hybrid'
    ]

    # Target companies (Fortune 500, MAANG/FAANG, etc.)
    TARGET_COMPANIES = [
        # MAANG/FAANG
        'Meta',
        'Apple',
        'Amazon',
        'Netflix',
        'Google',
        'Microsoft',

        # Other Fortune 500 tech companies
        'ServiceNow',
        'Salesforce',
        'Oracle',
        'IBM',
        'Intel',
        'Cisco',
        'Adobe',
        'NVIDIA',
        'AMD',
        'Qualcomm',
        'IBM',  # Duplicate, but keeping as in original
        'Accenture',
        'TCS',
        'Infosys',
        'Wipro',
        'HCL Tech',
        'Tech Mahindra',
        'LTI',
        'Mindtree',
        'Persistent Systems',
        'Zensar',
        'Cyient',
        'L&T Infotech',
        'Mphasis',
        'Hexaware',
        'Larsen & Toubro',
        'Honeywell',
        'GE',
        'Siemens',
        'Bosch',
        'Philips',
        'SAP',
        'VMware',
        'Citrix',
        'PayPal',
        'Stripe',
        'Uber',
        'Lyft',
        'Airbnb',
        'Spotify',
        'Twitter/X',
        'LinkedIn',
        'PayPal',  # Duplicate
        'Square',
        'Shopify',
        'Instacart',
        'DoorDash',
        'Quora',
        'Reddit',
        'Pinterest',
        'Snapchat',
        'TikTok',
        'ByteDance',
        'Quora',   # Duplicate
        'Medium',
        'Dropbox'
    ]

    # Experience years for salary bargaining
    TARGET_EXPERIENCE_YEARS = int(os.getenv('TARGET_EXPERIENCE_YEARS', '8'))

    # Match thresholds
    INITIAL_MATCH_THRESHOLD = int(os.getenv('INITIAL_MATCH_THRESHOLD', '60'))  # 60-70% initial match
    TARGET_MATCH_THRESHOLD = int(os.getenv('TARGET_MATCH_THRESHOLD', '95'))   # 95% after tailoring

    # File paths
    BASE_DIR = Path(__file__).parent
    RESUMES_DIR = BASE_DIR / "outputs" / "resumes"
    LOGS_DIR = BASE_DIR / "logs"
    CACHE_DIR = BASE_DIR / "cache"

    # Create directories if they don't exist
    RESUMES_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Resume configuration
    BASE_RESUME_PATH = BASE_DIR / "resumes" / "Sivaramaraju_Kalidindi_Resume_2026.pdf"
    BASE_RESUME_TEXT = ""  # Will be loaded from file from file

# Create a .env.example