## Updated README: PDF Resume Support

### 📄 Using Your PDF Resume

The system now supports **PDF resumes** in addition to plain text files. Here's how to use your PDF resume:

#### 1. Prepare Your Resume
- Place your resume PDF in the `resumes/` directory (e.g., `resumes/my_resume.pdf`)
- OR update the `BASE_RESUME_PATH` in your `.env` file to point to your PDF location

#### 2. Configuration Options
In your `.env` file, you can specify:
```dotenv
# Option 1: PDF file in resumes/ directory
BASE_RESUME_PATH=./resumes/your_resume.pdf

# Option 2: Absolute path
BASE_RESUME_PATH=/full/path/to/your/resume.pdf

# Option 3: Keep using text (original method still works)
BASE_RESUME_PATH=./resumes/base_resume.txt
```

#### 3. How It Works
- The system automatically detects `.pdf` file extensions
- Uses **PyPDF2** to extract text from all pages
- Falls back to text reading if PDF processing fails
- Maintains all existing functionality (NVIDIA NIM matching, optimization, etc.)

#### 4. Requirements
Make sure you have the PDF dependency installed:
```bash
pip install -r requirements.txt  # Now includes PyPDF2>=3.0.0
```

#### 5. Troubleshooting
- If PDF text extraction produces garbled output, your PDF might be image-based/scanned
- For scanned resumes, you'll need OCR (consider using Adobe Acrobat or online tools to extract text first)
- The system logs PDF processing errors and falls back gracefully

### Example Workflow
1. Place your resume: `cp ~/Downloads/MyResume.pdf ./resumes/my_resume.pdf`
2. Edit `.env`: `BASE_RESUME_PATH=./resumes/my_resume.pdf`
3. Run: `python main.py`
4. Check outputs: `outputs/resumes/` for tailored resumes

The system will extract text from your PDF, perform NVIDIA NIM-powered analysis against job descriptions, and generate optimized text resumes that you can then format as needed for your applications.