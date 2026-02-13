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

        if not jd or not index_name:
            return JsonResponse({"error": "jd and index_name required"}, status=400)

        user_chunks = resume.query_vector_store(jd, index_name, pc, embedding)
        final = resume.user_summary(user_chunks, jd)
        
        suggestions = []
        if isinstance(final, str) and final.startswith("•"):
            suggestions = [line.strip() for line in final.split("\n") if line.strip().startswith("•")]
            suggestions = [s.lstrip("•").strip() for s in suggestions]

        return JsonResponse({
            "success": True,
            "tailored_resume": final,
            "suggestions": suggestions[:5] if suggestions else [],
            "retrieved_context": [chunk.get('content', '') if isinstance(chunk, dict) else str(chunk) for chunk in user_chunks]
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)