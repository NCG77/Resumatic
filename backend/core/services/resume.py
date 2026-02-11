from pinecone import Pinecone
from langchain_pinecone import Pinecone as LangChainPinecone
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os
import json

def data_fetching(query, index_name, pc, embedding):
    try:
        if not query or not index_name:
            return ["No additional data found (No index passed)"]

        index = pc.Index(index_name)
        vector_store = LangChainPinecone(index=index, embedding=embedding)
        results = vector_store.similarity_search(query, k=10)
        
        return [{'content': result.page_content,
                 'metadata': result.metadata} for result in results]
    
    except Exception as e:
        return ["No additional data found"]
    
def user_summary(user_context, JD):
    try:
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return "Missing API key: set GEMINI_API_KEY or GOOGLE_API_KEY"
        
        model = "gemini-2.5-pro"
            
        if isinstance(user_context, list):
            context = "\n\n".join([item.get('content', '') if isinstance(item, dict) else str(item) for item in user_context])
        else:
            context = str(user_context)
            
        prompt = f"""
            You are an expert resume writer. Your task is to analyze a job description and create 
            tailored resume bullet points based on the candidate's experience.
            
            STEP 1: Carefully analyze the Job Description below and extract:
            - Required skills and technologies
            - Key responsibilities mentioned
            - Qualifications and experience required
            - Important keywords and phrases
            
            STEP 2: Review the candidate's context and identify relevant:
            - Projects that match the job requirements
            - Skills and technologies they've used
            - Achievements and accomplishments
            - Experience that aligns with the role
            
            STEP 3: Generate 8-12 powerful, ATS-friendly resume bullet points that:
            - Start with strong action verbs (Developed, Engineered, Led, Implemented, Designed, etc.)
            - Quantify achievements with numbers, percentages, or metrics when possible
            - Incorporate keywords from the job description naturally
            - Highlight relevant technical skills and tools
            - Demonstrate impact and results
            - Are specific and concrete (avoid vague statements)
            
            Format each bullet point starting with "•" and use clear, professional language.
            Focus ONLY on experiences from the context that are relevant to this specific job.
            
            Candidate's Experience and Projects:
            {context}
            
            Job Description:
            {JD}
            
                    Generate the tailored resume bullet points now:
        """

        last_error = None
        try:
            llm = ChatGoogleGenerativeAI(
                api_key=api_key,
                model=model,
                timeout=60,
                max_retries=2
            )
            response = llm.invoke(prompt)
            return response.content
        except Exception as e:
            last_error = e
        
        return f"No summary formed: All models failed. Last error: {str(last_error)}"
    
    except Exception as e:
        return f"No summary formed: {str(e)}"

def query_vector_store(jd, index_name, pc, embedding):
    try:
        user_chunks = data_fetching(jd, index_name, pc, embedding)
        return user_chunks

    except Exception as e:
        return "error" + str(e)

def research(c_name):
    try:
        if not c_name or not c_name.strip():
            return "No Company Name found"
        
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return "Missing API key: set GEMINI_API_KEY or GOOGLE_API_KEY"
        
        model = "gemini-2.5-pro"
            
        prompt = f"""
            You are a company research assistant. Research the company and provide details 
            about its authenticity and reputation. Give a straightforward answer to whether 
            the user should apply to this company or not. Include information about company 
            credibility, work environment, and growth opportunities.
            
            Company Name: {c_name}
        """

        last_error = None
        try:
            llm = ChatGoogleGenerativeAI(
                api_key=api_key,
                model=model,
                timeout=30,
                max_retries=2
            )
            response = llm.invoke(prompt)
            return response.content
        except Exception as e:
            last_error = e
        
        return f"Error researching company: All models failed. Last error: {str(last_error)}"
    
    except Exception as e:
        return f"Error researching company: {str(e)}"

    
def Resume_maker():
    ...
