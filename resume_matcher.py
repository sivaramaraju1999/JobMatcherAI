"""
Resume Matching and Tailoring Component using NVIDIA NIM
Based on the conversation history: targeting 60-70% initial match → 95% after tailoring
"""

import re
import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
import requests

# Optional PDF support
try:
    # pyrefly: ignore [missing-import]
    import PyPDF2
    _PDF_AVAILABLE = True
except ImportError:
    _PDF_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class MatchResult:
    """Result of resume-job matching"""
    match_score: float  # 0-100 percentage
    missing_keywords: List[str]
    matching_keywords: List[str]
    suggestions: List[str]
    optimized_resume_text: str

class LLMClient:
    """Client for Groq and NVIDIA NIM APIs (OpenAI-compatible endpoints)"""

    def __init__(self, groq_api_key: Optional[str] = None, nim_api_key: Optional[str] = None, 
                 groq_model: Optional[str] = None, nim_model: Optional[str] = None):
        self.groq_api_key = groq_api_key or os.getenv('GROK_API_KEY') or os.getenv('GROQ_API_KEY')
        self.nim_api_key = nim_api_key or os.getenv('NVIDIA_NIM_API_KEY')
        
        self.groq_model = groq_model or "llama-3.1-8b-instant"
        self.nim_model = nim_model or os.getenv('NVIDIA_NIM_MODEL', 'meta/llama-3.1-8b-instruct')
        
        self.groq_base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.nim_base_url = "https://integrate.api.nvidia.com/v1/chat/completions"
        
        if not self.groq_api_key and not self.nim_api_key:
            logger.warning("Neither Groq nor NVIDIA NIM API keys provided. LLM features will be disabled.")

    def _call_llm(self, messages: list, temperature: float = 0.2, max_tokens: int=1000) -> str:
        """Make a call to Groq (primary) or NVIDIA NIM (fallback) API"""
        if not self.groq_api_key and not self.nim_api_key:
            raise ValueError("No LLM API keys set")

        # Try Groq First
        if self.groq_api_key:
            payload = {
                "model": self.groq_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }
            try:
                response = requests.post(self.groq_base_url, headers=headers, json=payload, timeout=30)
                response.raise_for_status()
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            except requests.exceptions.HTTPError as e:
                if response.status_code == 401:
                    logger.error("Groq API key is invalid or unauthorized.")
                elif response.status_code == 404:
                    logger.error(f"Groq model '{self.groq_model}' not found.")
                else:
                    logger.error(f"Groq API HTTP error: {e}")
                logger.error("Falling back to NVIDIA NIM...")
            except Exception as e:
                logger.error(f"Groq API call failed: {e}. Falling back to NVIDIA NIM...")

        # Fallback to NVIDIA NIM
        if self.nim_api_key:
            payload = {
                "model": self.nim_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            headers = {
                "Authorization": f"Bearer {self.nim_api_key}",
                "Content-Type": "application/json"
            }
            try:
                response = requests.post(self.nim_base_url, headers=headers, json=payload, timeout=30)
                response.raise_for_status()
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            except requests.exceptions.HTTPError as e:
                if response.status_code == 401:
                    logger.error("NVIDIA NIM API key is invalid or unauthorized.")
                elif response.status_code == 404:
                    logger.error(f"NVIDIA NIM model '{self.nim_model}' not found.")
                else:
                    logger.error(f"NVIDIA NIM API HTTP error: {e}")
                raise
            except Exception as e:
                logger.error(f"NVIDIA NIM API call failed: {e}")
                raise
        
        raise ValueError("All LLM API calls failed.")

    def extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text using LLM"""
        if not self.groq_api_key and not self.nim_api_key:
            return self._fallback_extract_keywords(text)

        prompt = f"""Extract the most important technical skills, tools, technologies, methodologies, and key nouns from the following text.
Return ONLY a comma-separated list of lowercase keywords, no explanations, no extra text.
Focus on: programming languages, frameworks, tools, cloud platforms, methodologies, certifications, domain-specific terms.

Text:
{text}

Keywords:"""

        try:
            response = self._call_llm([{"role": "user", "content": prompt}], temperature=0.1, max_tokens=200)
            keywords = [k.strip().lower() for k in response.split(',') if k.strip()]
            keywords = [k for k in keywords if len(k) > 1 and k not in ['and', 'or', 'the', 'a', 'an', 'to', 'of', 'in', 'for', 'with', 'on', 'at', 'by']]
            return list(dict.fromkeys(keywords))
        except Exception as e:
            logger.error(f"Keyword extraction via LLM failed: {e}. Falling back to regex.")
            return self._fallback_extract_keywords(text)

    def calculate_match_score(self, resume_text: str, job_description: str) -> tuple:
        """Calculate match score between resume and job description using LLM"""
        if not self.groq_api_key and not self.nim_api_key:
            return self._fallback_calc_score_basic(resume_text, job_description)

        prompt = f"""You are an expert ATS (Applicant Tracking System) analyzer.
Compare the resume and job description below and provide:
1. A match percentage (0-100) representing how well the resume matches the job requirements
2. A list of matching keywords/skills (present in both)
3. A list of missing keywords/skills (important for the job but not in resume)

Be precise and focus on hard skills, technologies, methodologies, and relevant experience levels.

Resume:
{resume_text}

Job Description:
{job_description}

Respond in JSON format ONLY:
{{
  "match_score": <number between 0 and 100>,
  "matching_keywords": ["keyword1", "keyword2", ...],
  "missing_keywords": ["keyword1", "keyword2", ...]
}}"""

        try:
            response = self._call_llm([{"role": "user", "content": prompt}], temperature=0.1, max_tokens=500)
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                score = float(result.get('match_score', 0))
                matching = result.get('matching_keywords', [])
                missing = result.get('missing_keywords', [])
                matching = [str(k).lower().strip() for k in matching if isinstance(k, str)]
                missing = [str(k).lower().strip() for k in missing if isinstance(k, str)]
                return min(max(score, 0), 100), missing, matching
            else:
                raise ValueError("No JSON found in response")
        except Exception as e:
            logger.error(f"Match scoring via LLM failed: {e}. Falling back.")
            return self._fallback_calc_score_basic(resume_text, job_description)


    def _fallback_extract_keywords(self, text: str) -> List[str]:
        words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9+#.-]*\b', text.lower())
        stop_words = {'the', 'a', 'an', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'with'}
        return list(set(w for w in words if len(w) > 2 and w not in stop_words))

    def _fallback_calc_score_basic(self, resume_text: str, job_description: str) -> tuple:
        resume_kw = set(self._fallback_extract_keywords(resume_text))
        job_kw = set(self._fallback_extract_keywords(job_description))
        if not job_kw:
            return 0.0, list(job_kw), list(resume_kw)
        matching = list(resume_kw.intersection(job_kw))
        missing = list(job_kw.difference(resume_kw))
        score = (len(matching) / len(job_kw)) * 100 if job_kw else 0.0
        return min(max(score, 0), 100), missing, matching



class ResumeMatcher:
    """Matches resume against job descriptions and suggests optimizations"""

    def __init__(self):
        self.llm_client = LLMClient()

    def extract_keywords(self, text: str) -> List[str]:
        return self.llm_client.extract_keywords(text)

    def calculate_match_score(self, resume_text: str, job_description: str) -> Tuple[float, List[str], List[str]]:
        return self.llm_client.calculate_match_score(resume_text, job_description)




class ResumeStorage:
    """Handles saving and loading resumes"""

    def __init__(self, config):
        self.config = config

    def save_resume(self, resume_text: str, filename: str) -> str:
        """Save resume text to file"""
        # Ensure outputs/resumes directory exists
        self.config.RESUMES_DIR.mkdir(parents=True, exist_ok=True)

        filepath = self.config.RESUMES_DIR / filename

        # For simplicity, we're saving as text. In production, you might want PDF/DOCX
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(resume_text)

        return str(filepath.absolute())

    def load_base_resume(self) -> str:
        """Load base resume from file or environment - supports .txt and .pdf"""
        # Try to load from file first
        base_resume_path = getattr(self.config, 'BASE_RESUME_PATH', None)
        if base_resume_path:
            path_obj = Path(base_resume_path)
            if path_obj.exists():
                # Check if it's a PDF file
                if path_obj.suffix.lower() == '.pdf':
                    if _PDF_AVAILABLE:
                        try:
                            return self._extract_text_from_pdf(path_obj)
                        except Exception as e:
                            logger.error(f"Failed to extract text from PDF {path_obj}: {e}")
                            # Fall back to reading as text if PDF extraction fails
                            pass
                    else:
                        logger.warning("PyPDF2 not installed. Cannot read PDF files. Install with: pip install PyPDF2")

                # If not PDF or PDF extraction failed, try as text file
                try:
                    with open(path_obj, 'r', encoding='utf-8') as f:
                        return f.read()
                except UnicodeDecodeError:
                    # Try with different encoding if UTF-8 fails
                    try:
                        with open(path_obj, 'r', encoding='latin-1') as f:
                            return f.read()
                    except Exception as e:
                        logger.error(f"Failed to read text file {path_obj}: {e}")

        # Fall back to environment variable or default
        base_resume_text = getattr(self.config, 'BASE_RESUME_TEXT', '')
        if base_resume_text:
            return base_resume_text

        # Default placeholder - in real usage, you'd load actual resume
        return """
        John Doe
        Senior Software Engineer

        EXPERIENCE
        Senior Software Engineer | XYZ Corp | 2020-Present
        - Developed web applications using Java, Spring Boot
        - Worked with REST APIs and microservices architecture
        - Collaborated with cross-functional teams using Agile methodologies
        - Mentored junior developers and conducted code reviews

        Software Engineer | ABC Inc | 2018-2020
        - Built frontend components using React and JavaScript
        - Integrated with backend services using JSON/XML
        - Participated in daily standups and sprint planning

        SKILLS
        Languages: Java, JavaScript, Python
        Frameworks: Spring Boot, React
        Tools: Git, Jenkins, JIRA
        Concepts: OOP, REST, Microservices, Agile

        EDUCATION
        Bachelor of Technology in Computer Science
        University of Example, 2018
        """

    def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text content from a PDF file"""
        if not _PDF_AVAILABLE:
            raise ImportError("PyPDF2 is required to read PDF files. Install with: pip install PyPDF2")

        text_content = []
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)

                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text_content.append(page.extract_text())

                # Join all pages with double newlines for readability
                full_text = '\n\n'.join(text_content)

                # Basic cleanup
                lines = [line.strip() for line in full_text.split('\n') if line.strip()]
                cleaned_text = '\n'.join(lines)

                return cleaned_text
        except Exception as e:
            logger.error(f"Error parsing PDF {pdf_path}: {e}")
            raise