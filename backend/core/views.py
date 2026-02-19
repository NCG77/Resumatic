from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore, Pinecone as LangChainPinecone
from langchain_huggingface import HuggingFaceEmbeddings
from pinecone import Pinecone, ServerlessSpec
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import os
import tempfile
import json
import re
import traceback
from dotenv import load_dotenv
from .services import resume

load_dotenv()

# Initialize Pinecone and HuggingFace with error handling
pc = None
embedding = None

def get_pc():
    global pc
    if pc is None:
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("PINECONE_API_KEY not set")
        pc = Pinecone(api_key=api_key)
    return pc

def get_embedding():
    global embedding
    if embedding is None:
        embedding = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
    return embedding

@csrf_exempt
@require_http_methods(["POST"])
def upload_and_chunk(request):
    try:
        if "file" not in request.FILES:
            return JsonResponse({"error": "No file provided"}, status=400)

        uploaded_file = request.FILES["file"]

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            for chunk in uploaded_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        loader = PyPDFLoader(tmp_path)
        docs = loader.load()
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150
        )
        chunks = splitter.split_documents(docs)

        file_name = uploaded_file.name.replace(".pdf", "").replace(" ", "-").lower()
        index_name = f"resume-{file_name}"
        
        pinecone_client = get_pc()
        embedding_model = get_embedding()
        
        existing = [i["name"] for i in pinecone_client.list_indexes()]
        if index_name not in existing:
            pinecone_client.create_index(
                name=index_name,
                dimension=384,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )

        index = pinecone_client.Index(index_name)
        vectorstore = PineconeVectorStore(
            index=index,
            embedding=embedding_model
        )

        vectorstore.add_documents(chunks)
        os.unlink(tmp_path)
        return JsonResponse({
            "success": True,
            "message": f"{len(chunks)} chunks uploaded",
            "index_name": index_name
        })

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def company_search(request):
    try:
        data = json.loads(request.body)
        name = data.get("company_name", "").strip()

        if not name:
            return JsonResponse({"error": "Company name required"}, status=400)

        result = resume.research(name)

        if not result:
            return JsonResponse({"error": "No data found"}, status=404)

        if result.startswith("Error") or result.startswith("No"):
            return JsonResponse({"error": result}, status=500)

        return JsonResponse({
            "success": True,
            "company_details": result
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def tailor_resume(request):
    try:
        data = json.loads(request.body)
        jd = data.get("jd")
        index_name = data.get("index_name")
        job_url = data.get("job_url", "")

        if not jd or not index_name:
            return JsonResponse({"error": "jd and index_name required"}, status=400)

        pinecone_client = get_pc()
        embedding_model = get_embedding()

        scraped_jd = None
        if job_url:
            scraped_jd = resume.scrape_job_posting(job_url)
            if scraped_jd:
                jd = f"{jd}\n\n--- Additional Details from Job Posting ---\n{scraped_jd}"

        company_name = resume.extract_company_from_jd(jd)
        company_info = None
        if company_name and company_name.lower() != "unknown":
            company_info = resume.scrape_company_info(company_name)

        user_chunks = resume.query_vector_store(jd, index_name, pinecone_client, embedding_model)
        
        jd_analysis = resume.user_summary(user_chunks, jd)
        
        strategy = resume.resume_strategist(jd_analysis, user_chunks, company_info)
        
        strategy_json = None
        try:
            clean_strategy = strategy.strip() if strategy else ""
            
            # Handle various markdown code block formats
            json_block_match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)```', clean_strategy)
            if json_block_match:
                clean_strategy = json_block_match.group(1).strip()
            else:
                # Try to find JSON object directly if no code block
                json_start = clean_strategy.find('{')
                json_end = clean_strategy.rfind('}')
                if json_start != -1 and json_end != -1:
                    clean_strategy = clean_strategy[json_start:json_end + 1]
            
            strategy_json = json.loads(clean_strategy)
            print("Successfully parsed strategy JSON")
        except Exception as parse_error:
            print(f"JSON parse error: {parse_error}")
            print(f"Raw strategy (first 500 chars): {strategy[:500] if strategy else 'None'}")
            strategy_json = None

        return JsonResponse({
            "success": True,
            "jd_analysis": jd_analysis,
            "strategy": strategy_json if strategy_json else strategy,
            "strategy_raw": strategy,
            "company_info": company_name if company_name and company_name.lower() != "unknown" else None,
            "retrieved_context": [chunk.get('content', '') if isinstance(chunk, dict) else str(chunk) for chunk in user_chunks]
        })

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)
