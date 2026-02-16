from pinecone import Pinecone
from langchain_pinecone import Pinecone as LangChainPinecone
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os
import traceback

load_dotenv()

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
            You are an expert resume writer.

            Generate 8–12 ATS-friendly resume bullet points based on the user's experience and job description.

            Candidate Experience:
            {context}

            Job Description:
            {JD}

            Rules:
            - Start each bullet with a strong action verb
            - Use numbers when possible
            - Match JD keywords
            - Use professional resume tone

            Return bullets only.
            """

        return call_gemini(prompt, timeout=60)

    except Exception:
        traceback.print_exc()
        return "Failed to generate resume summary."


def query_vector_store(jd, index_name, pc, embedding):
    return data_fetching(jd, index_name, pc, embedding)


def research(c_name):
    try:
        if not c_name:
            return "No company name provided."

        prompt = f"""
            Research the company: {c_name}

            Provide:
            - What the company does
            - Reputation
            - Whether it seems legitimate
            - Should a candidate apply or avoid
            """

        return call_gemini(prompt, timeout=30)

    except Exception:
        traceback.print_exc()
        return "Company research failed."
