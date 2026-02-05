from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Pinecone
from langchain_community.embeddings import HuggingFaceEmbeddings
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from pinecone import Pinecone as PineconeClient
import os
import tempfile
import json
from io import BytesIO
from .services import resume
from dotenv import load_dotenv

load_dotenv()
pc = PineconeClient(api_key=os.getenv('PINECONE_API_KEY'))
embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

@require_http_methods(["POST"])
def upload_and_chunk(request):
    try:
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'No file provided'}, status=400)
        uploaded_file = request.FILES['file']

        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            for chunk in uploaded_file.chunks():
                tmp_file.write(chunk)
            tmp_path = tmp_file.name
        
        loader = PyPDFLoader(tmp_path)
        docs = loader.load()
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150
        )
        chunks = splitter.split_documents(docs)
        file_name = uploaded_file.name.replace('.pdf', '').replace(' ', '_').lower()
        index_name = f"resume-{file_name}"
        try:
            vector_store = Pinecone.from_documents(
                chunks,
                embedding,
                index_name=index_name
            )
        except Exception as e:
            vector_store = Pinecone(
                pc.Index(index_name),
                embedding.embed_query,
                "text"
            )
            vector_store.add_documents(chunks)
        
        os.unlink(tmp_path)
        return JsonResponse({
            'success': True,
            'message': f'Successfully uploaded {len(chunks)} chunks to Pinecone',
            'chunks_count': len(chunks),
            'index_name': index_name
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def company_search(request):
    try:
        data = json.loads(request.body)
        c_name = data.get('company_name', '').strip()
        
        if not c_name:
            return JsonResponse({'error': 'Company name is required'}, status=400)
        
        val = resume.research(c_name)
        
        if not val:
            return JsonResponse({'error': "Details not found"}, status=500)
        if val.startswith('No'):
            return JsonResponse({'error': val}, status=400)
        if val.startswith('Error'):
            return JsonResponse({'error': val}, status=500)

        return JsonResponse({
            'success': True,
            'company_details': val
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
def query_vector_store(request):
    try:
        data = json.loads(request.body)
        JD = data.get('jd')
        query = data.get('query')
        index_name = data.get('index_name')
        
        if not JD or not query or not index_name:
            return JsonResponse({'error': 'Missing required fields: jd, query, index_name'}, status=400)
        
        usr_data = resume.data_fetching(query, index_name, pc, embedding)
        value = resume.user_summary(usr_data, JD)
        
        return JsonResponse({
            'success': True,
            'summary': value
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
