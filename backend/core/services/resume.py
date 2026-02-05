from pinecone import Pinecone
from langchain_community.vectorstores import Pinecone
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os
import json

def data_fetching(query, index_name, pc, embedding):
    try:
        if not query or not index_name:
            return ["No additional data found (No index passed)"]

        index = pc.Index(index_name)
        vector_store = Pinecone(index, embedding.embed_query, "text")
        results = vector_store.similarity_search(query, k=3)
        
        return [{'content': result.page_content,
                 'metadata': result.metadata} for result in results]
    
    except Exception as e:
        return ["No additional data found"]
    
def user_summary(user_context, JD):
    try:
        load_dotenv()
        llm = ChatGoogleGenerativeAI(
            api_key=os.getenv("GEMINI_API_KEY"),
            model="gemini-2.0-flash-exp"
        )
        if isinstance(user_context, list):
            context = "\n\n".join([item.get('content', '') if isinstance(item, dict) else str(item) for item in user_context])
        else:
            context = str(user_context)
            
        prompt = f"""
            You are a user data summarizer assistant. Use ONLY the context below and 
            match the things with the Job description to give a summary of only required 
            details matching the Job description.
            Context:
            {context}
            Job Description:
            {JD}
        """

        response = llm.invoke(prompt)
        return response.content
    
    except Exception as e:
        return f"No summary formed: {str(e)}"

def research(c_name):
    try:
        if not c_name or not c_name.strip():
            return "No Company Name found"
        
        load_dotenv()
        llm = ChatGoogleGenerativeAI(
            api_key=os.getenv("GEMINI_API_KEY"),
            model="gemini-2.5-pro"
        )
            
        prompt = f"""
            You are a company research assistant. Research the company and provide details 
            about its authenticity and reputation. Give a straightforward answer to whether 
            the user should apply to this company or not. Include information about company 
            credibility, work environment, and growth opportunities.
            
            Company Name: {c_name}
        """

        response = llm.invoke(prompt)
        return response.content
    
    except Exception as e:
        return f"Error researching company: {str(e)}"

    
def Resume_maker():
    ...
