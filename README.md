# Resumatic - Resume Tailoring Tool

## Overview
Resumatic is an AI-powered application that tailors your resume to match job descriptions. It analyzes your resume and a job posting, then suggests improvements and provides an optimized version.

## Features
- **Resume Input**: Paste your complete resume
- **Job Description Input**: Paste the target job posting
- **AI-Powered Analysis**: Uses Gemini API to analyze and suggest improvements
- **Tailored Output**: Generates a customized version of your resume
- **Web Scrapping**: Extracts key requirements from job url 
- **Actionable Suggestions**: Provides specific recommendations for improvement

## Setup Instructions

### Backend Setup

1. **Install Python Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**
   - Copy `.env.example` to `.env`
   - Add your Gemini AI API key:
     ```bash
     AI_API_KEY=your-gemini-api-key-here
     ```

3. **Run the Backend Server**
   ```bash
   python app.py
   ```
   The API will be available at `http://localhost:5000`

### Frontend Setup

1. **Install Dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Configure API Endpoint**
   The frontend is already configured to call `http://localhost:5000/api/tailor-resume`
   - Update the API URL in `main_page.tsx` if your backend runs on a different port

3. **Run the Development Server**
   ```bash
   npm run dev
   ```
   The app will be available at `http://localhost:3000`

## Usage

1. Open the application in your browser
2. Paste your complete resume in the "Your Resume" field
3. Paste the job description in the "Job Description" field
4. Click "Tailor Resume"
5. Review:
   - **Match Score**: How well your resume aligns with the job
   - **Suggestions**: Key improvements to consider
   - **Tailored Resume**: Your optimized resume
6. Copy the tailored resume to your clipboard

**Response:**
```json
{
  "tailored_resume": "Customized resume text",
  "suggestions": [
    "Suggestion 1",
    "Suggestion 2",
    "..."
  ],
}
```


## How It Works

1. **Requirement Extraction**: The AI analyzes the job description and extracts the top 10 requirements
2. **Resume Tailoring**: Your resume is reordered and emphasized to match those requirements
3. **Suggestions Generation**: Specific, actionable recommendations are provided
4. **Match Scoring**: The AI evaluates how well your resume aligns with the job (0-100%)

## Technologies Used

**Frontend:**
- Next.js 14+
- React 18+
- TypeScript
- CSS Modules

**Backend:**
- Python 3.8+
- Flask
- LangChain
- OpenAI GPT API
- python-dotenv

## Prerequisites

- Node.js 18+ (for frontend)
- Python 3.8+ (for backend)
- Gemini AI API key (get one at https://platform.google.com)

## Tips for Best Results

1. **Complete Resume**: Provide your full resume with all relevant experience
2. **Clear Job Description**: Use the complete job posting for better analysis
3. **Truthfulness**: The AI will maintain your actual qualifications while highlighting relevant ones
4. **Keywords**: The tool naturally incorporates job posting keywords into your resume
5. **Customization**: Review suggestions and the tailored resume before submitting

## Troubleshooting

- **API Connection Error**: Ensure backend is running on correct port
- **Gemini Error**: Check your API key and account balance
- **Parsing Errors**: Try with simpler, well-formatted resume and job description text

## Future Enhancements

- File upload support for resume and job descriptions
- Multiple format support (PDF, DOCX, etc.)
- Save and compare multiple tailored versions
- Export to various formats
- Batch processing multiple jobs
- Interview question generation
- Skill gap analysis

## License

MIT License

## Support

For issues or questions, please check your API keys and ensure both frontend and backend servers are running correctly.
