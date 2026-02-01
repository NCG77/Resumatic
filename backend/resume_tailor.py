"""
Resume Tailoring Module with Vector Database
Handles storing resume details in FAISS vector DB and retrieving relevant context
for resume tailoring based on job descriptions.
"""

from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
import os
import json
from pathlib import Path
import PyPDF2

# Initialize LLM and embeddings
llm = ChatOpenAI(
    model_name="gpt-3.5-turbo",
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY")
)

embeddings = OpenAIEmbeddings(
    api_key=os.getenv("OPENAI_API_KEY")
)

# Vector database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'resume_db')
os.makedirs(DB_PATH, exist_ok=True)

def extract_text_from_file(filepath: str) -> str:
    """
    Extract text from various file formats.
    
    Args:
        filepath: Path to the file (TXT, PDF, or DOCX)
    
    Returns:
        Extracted text content
    """
    file_ext = Path(filepath).suffix.lower()
    
    if file_ext == '.txt':
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    
    elif file_ext == '.pdf':
        text = []
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text.append(page.extract_text())
        return '\n'.join(text)
    
    else:
        raise ValueError(f"Unsupported file format: {file_ext}")

def upload_resume_to_db(filepath: str) -> int:
    """
    Upload and process a resume file into the vector database.
    
    Args:
        filepath: Path to the resume file
    
    Returns:
        Number of chunks stored
    """
    # Extract text from file
    text_content = extract_text_from_file(filepath)
    
    # Split text into meaningful chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_text(text_content)
    
    # Create or update vector database
    if os.path.exists(os.path.join(DB_PATH, 'index.faiss')):
        # Load existing database
        db = FAISS.load_local(DB_PATH, embeddings)
        # Add new documents
        db.add_texts(chunks)
    else:
        # Create new database
        db = FAISS.from_texts(chunks, embeddings)
    
    # Save database
    db.save_local(DB_PATH)
    
    return len(chunks)

def retrieve_relevant_context(job_description: str, top_k: int = 5) -> list:
    """
    Retrieve relevant experience and projects from vector database
    based on the job description.
    
    Args:
        job_description: The target job description
        top_k: Number of relevant sections to retrieve
    
    Returns:
        List of relevant context strings from the database
    """
    db_path = os.path.join(DB_PATH, 'index.faiss')
    
    # Check if database exists
    if not os.path.exists(db_path):
        return []
    
    try:
        # Load the vector database
        db = FAISS.load_local(DB_PATH, embeddings)
        
        # Search for relevant documents
        results = db.similarity_search(job_description, k=top_k)
        
        # Extract and deduplicate the content
        context = []
        seen = set()
        for result in results:
            content = result.page_content.strip()
            if content and content not in seen:
                context.append(content)
                seen.add(content)
        
        return context[:top_k]
    
    except Exception as e:
        print(f"Error retrieving context: {e}")
        return []

def tailor_resume_to_job(retrieved_context: list, job_description: str) -> dict:
    """
    Tailor resume based on job description using retrieved context from vector DB.
    
    Args:
        retrieved_context: List of relevant experience/projects from vector database
        job_description: The target job description
    
    Returns:
        Dictionary containing:
        - tailored_resume: Customized resume optimized for the job
        - suggestions: List of key recommendations
        - match_score: Percentage match (0-100)
    """
    
    # Combine retrieved context into a single string
    context_str = "\n\n".join(retrieved_context) if retrieved_context else "No previous experience found in database"
    
    # Step 1: Extract key requirements from job description
    requirements_prompt = PromptTemplate(
        input_variables=["job_description"],
        template="""Analyze the following job description and extract the top 10 most important skills, qualifications, and requirements.

Job Description:
{job_description}

Provide the results as a JSON array of strings with the most critical requirements first."""
    )
    
    requirements_chain = LLMChain(llm=llm, prompt=requirements_prompt)
    requirements_result = requirements_chain.run(job_description=job_description)
    
    # Parse requirements
    try:
        requirements = json.loads(requirements_result)
    except:
        requirements = requirements_result.split('\n')
    
    # Step 2: Generate tailored resume combining context and requirements
    tailor_prompt = PromptTemplate(
        input_variables=["context", "job_description", "requirements"],
        template="""You are an expert resume writer. Create a tailored resume based on the candidate's background and the target job.

Candidate's Background and Experience:
{context}

Target Job Description:
{job_description}

Key Requirements to Highlight:
{requirements}

Instructions:
1. Create a resume highlighting the most relevant experience from the candidate's background
2. Organize by relevance to the job requirements
3. Use keywords from the job description naturally
4. Focus on quantifiable achievements where possible
5. Keep formatting professional and easy to read
6. Maintain truthfulness while emphasizing the most relevant qualifications

Return a well-formatted, tailored resume."""
    )
    
    tailor_chain = LLMChain(llm=llm, prompt=tailor_prompt)
    tailored_resume = tailor_chain.run(
        context=context_str,
        job_description=job_description,
        requirements=str(requirements)
    )
    
    # Step 3: Generate suggestions
    suggestions_prompt = PromptTemplate(
        input_variables=["context", "job_description"],
        template="""Based on the candidate's background and job description, provide 5-7 specific, actionable suggestions to improve their application for this role.

Candidate's Background:
{context}

Job Description:
{job_description}

Return your response as a JSON array of strings, each being a concise suggestion.
Example format: ["Add specific metrics to your achievements", "Highlight experience with X technology"]"""
    )
    
    suggestions_chain = LLMChain(llm=llm, prompt=suggestions_prompt)
    suggestions_result = suggestions_chain.run(
        context=context_str,
        job_description=job_description
    )
    
    # Parse suggestions
    try:
        suggestions = json.loads(suggestions_result)
    except:
        suggestions = [s.strip() for s in suggestions_result.split('\n') if s.strip()]
    
    # Step 4: Calculate match score
    match_prompt = PromptTemplate(
        input_variables=["context", "job_description"],
        template="""Rate how well the candidate's background matches the job description on a scale of 0-100.
Consider:
- Skills match
- Experience relevance
- Keywords alignment
- Qualification fit

Candidate Background:
{context}

Job Description:
{job_description}

Respond with ONLY a number between 0 and 100."""
    )
    
    match_chain = LLMChain(llm=llm, prompt=match_prompt)
    match_score_result = match_chain.run(
        context=context_str,
        job_description=job_description
    )
    
    # Parse match score
    try:
        match_score = int(''.join(filter(str.isdigit, match_score_result.strip()[:3])))
        match_score = min(100, max(0, match_score))  # Ensure 0-100 range
    except:
        match_score = 75  # Default if parsing fails
    
    return {
        "tailored_resume": tailored_resume.strip(),
        "suggestions": suggestions[:7] if isinstance(suggestions, list) else suggestions.split('\n')[:7],
        "match_score": match_score
    }

