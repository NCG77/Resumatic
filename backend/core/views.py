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
from dotenv import load_dotenv
from .services import resume

load_dotenv()
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
embedding = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

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
        existing = [i["name"] for i in pc.list_indexes()]
        if index_name not in existing:
            pc.create_index(
                name=index_name,
                dimension=384,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )

        index = pc.Index(index_name)
        vectorstore = PineconeVectorStore(
            index=index,
            embedding=embedding
        )

        vectorstore.add_documents(chunks)
        os.unlink(tmp_path)
        return JsonResponse({
            "success": True,
            "message": f"{len(chunks)} chunks uploaded",
            "index_name": index_name
        })

    except Exception as e:
        import traceback
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

        scraped_jd = None
        if job_url:
            scraped_jd = resume.scrape_job_posting(job_url)
            if scraped_jd:
                jd = f"{jd}\n\n--- Additional Details from Job Posting ---\n{scraped_jd}"

        company_name = resume.extract_company_from_jd(jd)
        company_info = None
        if company_name and company_name.lower() != "unknown":
            company_info = resume.scrape_company_info(company_name)

        user_chunks = resume.query_vector_store(jd, index_name, pc, embedding)
        
        jd_analysis = resume.user_summary(user_chunks, jd)
        
        strategy = resume.resume_strategist(jd_analysis, user_chunks, company_info)
        
        strategy_json = None
        try:
            clean_strategy = strategy
            if "```json" in strategy:
                clean_strategy = strategy.split("```json")[1].split("```")[0].strip()
            elif "```" in strategy:
                clean_strategy = strategy.split("```")[1].split("```")[0].strip()
            strategy_json = json.loads(clean_strategy)
        except:
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
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)
