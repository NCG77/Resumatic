from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Pinecone
from langchain.embeddings import HuggingFaceEmbeddings
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import os
import tempfile
import json
from io import BytesIO
from pinecone import Pinecone as PineconeClient
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


@require_http_methods(["POST"])
def query_vector_store(request):
    try:
        data = json.loads(request.body)
        query = data.get('query')
        index_name = data.get('index_name')
        
        if not query or not index_name:
            return JsonResponse({'error': 'Missing query or index_name'}, status=400)

        index = pc.Index(index_name)
        vector_store = Pinecone(index, embedding.embed_query, "text")
        results = vector_store.similarity_search(query, k=3)
        
        return JsonResponse({
            'success': True,
            'results': [
                {
                    'content': result.page_content,
                    'metadata': result.metadata
                }
                for result in results
            ]
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
