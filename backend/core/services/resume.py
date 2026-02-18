from pinecone import Pinecone
from langchain_pinecone import Pinecone as LangChainPinecone
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os
import traceback
import requests
from bs4 import BeautifulSoup
import re

load_dotenv()


def scrape_job_posting(url):
    try:
        if not url or not url.startswith(('http://', 'https://')):
            return None
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        text = soup.get_text(separator='\n', strip=True)
        
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        cleaned_text = '\n'.join(lines)
        
        if len(cleaned_text) > 8000:
            cleaned_text = cleaned_text[:8000]
        
        return cleaned_text
        
    except Exception as e:
        print(f"Web scraping error: {e}")
        return None


def scrape_company_info(company_name):
    try:
        if not company_name:
            return None
        
        search_url = f"https://html.duckduckgo.com/html/?q={company_name}+company+about+careers"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        for result in soup.select('.result__snippet')[:5]:
            snippet = result.get_text(strip=True)
            if snippet:
                results.append(snippet)
        
        return '\n'.join(results) if results else None
        
    except Exception as e:
        print(f"Company search error: {e}")
        return None


def extract_company_from_jd(jd):
    try:
        prompt = f"""Extract only the company name from this job description. 
        Return ONLY the company name, nothing else. If no company name is found, return 'Unknown'.
        
        Job Description:
        {jd[:2000]}
        """
        return call_gemini(prompt, timeout=15)
    except:
        return "Unknown"

def data_fetching(query, index_name, pc, embedding):
    try:
        if not query or not index_name:
            return []

        index = pc.Index(index_name)
        vector_store = LangChainPinecone(index=index, embedding=embedding)

        results = vector_store.similarity_search(query, k=10)

        return [
            {
                "content": r.page_content,
                "metadata": r.metadata or {}
            }
            for r in results
        ]

    except Exception as e:
        print("Vector search error:", e)
        return []


def call_gemini(prompt, timeout=30):
    try:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return "Missing Gemini API key."

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            api_key=api_key,
            timeout=timeout,
            max_retries=1
        )

        response = llm.invoke(prompt)
        return response.content

    except Exception as e:
        print("Gemini error:", e)
        return "AI service is temporarily unavailable. Please retry."


def user_summary(user_context, JD):
    try:
        if not JD:
            return "No Job Description provided."

        if not user_context:
            context = "No resume data found."
        else:
            context = "\n\n".join(
                item.get("content", "") for item in user_context if isinstance(item, dict)
            )

        prompt = f"""
            You are an expert ATS resume strategist and hiring manager.

            Your task is NOT to rewrite the resume.
            Your task is to STRATEGICALLY DECIDE what should go into each resume section
            to maximize shortlisting for this job.

            You must analyze both:
            1. The Job Description
            2. The Candidate's actual experience (from vector search)

            --------------------------------------------------
            STEP 1 — Analyze the Job Description
            Extract and list:
            - Core technical skills required
            - Tools & technologies mentioned
            - Responsibilities
            - Keywords ATS will scan for
            - Experience expectations

            --------------------------------------------------
            STEP 2 — Analyze Candidate Data
            From the candidate context:
            - Identify relevant projects
            - Identify technical skills actually used
            - Identify measurable outcomes
            - Identify leadership / ownership
            - Ignore irrelevant things

            --------------------------------------------------
            STEP 3 — Decide what belongs where

            Decide what should go into:
            A) Experience
            B) Projects
            C) Skills
            D) Achievements
            E) Tools & Technologies

            Only include things that help THIS job.

            --------------------------------------------------
            STEP 4 — Generate Optimized Resume Content

            Generate content in this EXACT format:

            EXPERIENCE:
            • Bullet points here

            PROJECTS:
            • Bullet points here

            SKILLS:
            • Comma separated list

            ACHIEVEMENTS:
            • Bullet points here

            TOOLS & TECHNOLOGIES:
            • Comma separated list

            Rules:
            - Use strong action verbs
            - Quantify wherever possible
            - Mirror JD keywords naturally
            - Use ATS-friendly wording
            - Do not hallucinate skills
            - Do not include anything not supported by context

            --------------------------------------------------
            Candidate Context:
            {context}

            Job Description:
            {JD}

            """

        return call_gemini(prompt, timeout=60)

    except Exception:
        traceback.print_exc()
        return "Failed to generate resume summary."


def query_vector_store(jd, index_name, pc, embedding):
    return data_fetching(jd, index_name, pc, embedding)

def resume_strategist(jd_analysis, candidate_context, company_info=None):
    try:
        context = "\n".join(
            chunk["content"] if isinstance(chunk, dict) else str(chunk)
            for chunk in candidate_context
        )

        company_section = ""
        if company_info:
            company_section = f"""
        -----------------------------------
        COMPANY RESEARCH (from web):
        {company_info}
        
        Use this to:
        - Align language with company culture
        - Highlight relevant domain experience
        - Match company values in positioning
        """

        prompt = f"""
        You are a **Senior FAANG Resume Strategist**.

        Your job is NOT to rewrite.
        Your job is to "optimize this candidate for THIS job".

        You are given:
        1) A structured Job Description analysis
        2) The candidate's real project and experience data
        3) Company research insights (if available)
        Your task:
        Decide what should be:
        - Highlighted
        - Reframed
        - Omitted
        - Emphasized

        To make this candidate appear as the "perfect match" for the job.

        -----------------------------------
        JOB DESCRIPTION ANALYSIS:
        {jd_analysis}

        -----------------------------------
        CANDIDATE DATA:
        {context}
        {company_section}
        -----------------------------------
        Produce a structured resume strategy in JSON.

        Use this format:

        {{
        "experience": [
            {{
            "title": "...",
            "company": "...",
            "bullets": ["...", "..."]
            }}
        ],
        "projects": [
            {{
            "name": "...",
            "why_it_matters_for_this_job": "...",
            "bullets": ["...", "..."]
            }}
        ],
        "skills_to_highlight": ["..."],
        "skills_to_downplay": ["..."],
        "keywords_for_ATS": ["..."],
        "achievements": ["..."],
        "overall_candidate_positioning": "1–2 sentence recruiter summary of how this candidate should be perceived",
        "company_alignment_tips": ["tip1", "tip2"]
        }}

        Rules:
        - Use JD keywords heavily
        - Rewrite everything in recruiter language
        - Focus on business impact + relevance
        - Do NOT hallucinate new projects
        - Only use what exists in the candidate data
        - Include company-specific alignment tips if company info is available

        Return ONLY valid JSON.
        """

        return call_gemini(prompt, timeout=90)

    except Exception:
        traceback.print_exc()
        return "Failed to generate resume strategy."
