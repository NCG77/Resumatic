from pinecone import Pinecone as PineconeClient
import Langchain
from dotenv import load_dotenv

def data_fetching():
    try:
        data = json.loads(request.body)
        query = data.get('query')
        index_name = data.get('index_name')
        
        if not query or not index_name:
            return {"No additional data found (No index passed)"}

        index = pc.Index(index_name)
        vector_store = Pinecone(index, embedding.embed_query, "text")
        results = vector_store.similarity_search(query, k=3)
        
        return { 'content': result.page_content,
                 'metadata': result.metadata}
    
    except Exception as e:
        return {"No additional data found"}
    
def user_summary(user_context, JD):
    try:
        load_dotenv()
        llm = ChatGooglegenerativeAI(
            api_key=os.getenv("GEMINI_API_KEY"),
            model="gemini-2.5-flash"
        )
        context = "\n\n".join(user_context)
        prompt = f"""
            You are a user data summarizer assistant. Use ONLY the context below and match the things with the Job discription to 
            give a summary of only required details matching the Job discription.
            Context:
            {context}
            Job Discription:
            {JD}
        """

        response = llm.invoke(prompt)
        return response.content
    
    except Exception as e:
        return {"No summary formed"}
    
def Resume_maker():
    ...
