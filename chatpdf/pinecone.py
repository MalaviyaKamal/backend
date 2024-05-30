# import os
# from pinecone import Pinecone
# from .utils import convert_to_ascii

# # Define Pinecone environment and API key directly
# PINECONE_ENVIRONMENT = "us-west1-gcp"
# PINECONE_API_KEY = "4a574746-607d-41cd-8a8e-51f9483cf45c"

# def get_pinecone_client():
#     return Pinecone(
#         environment=PINECONE_ENVIRONMENT,
#         api_key=PINECONE_API_KEY
#     )

# def upsert_vectors(index_name, vectors):
#     console.log("fsdvv")
#     client = get_pinecone_client()
#     pinecone_index = client.index('chat-pdf')
#     namespace = pinecone_index.namespace(convert_to_ascii('chat-pdf'))
#     namespace.upsert(vectors)
import os
import hashlib
from pinecone import Pinecone
from .s3_server import download_from_s3
from .embeddings import get_embeddings
from langchain_community.document_loaders import PyPDFLoader
from .utils import convert_to_ascii
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter


def get_pinecone_client():
    return Pinecone(
        environment="us-west1-gcp",
        api_key="4a574746-607d-41cd-8a8e-51f9483cf45c"
    )

async def load_s3_into_pinecone(file_key):
    try:
        # 1. Obtain the PDF -> Download and read from PDF
        print("Downloading from S3 into file system")
        file_name = await download_from_s3(file_key)
        if not file_name:
            raise Exception("Could not download from S3")

        print("Loading PDF into memory:", file_name)
        loader = PDFLoader(file_name)
        pages = await loader.load()

        # 2. Split and segment the PDF
        documents = await prepare_documents(pages)

        # 3. Vectorize and embed individual documents
        vectors = []
        for doc in documents:
            vectors.extend(await embed_document(doc))

        # 4. Upload to Pinecone
        client = get_pinecone_client()
        pinecone_index = await client.index("chat-pdf")
        namespace = pinecone_index.namespace(convert_to_ascii(file_key))

        print("Inserting vectors into Pinecone")
        await namespace.upsert(vectors)

        return documents[0]
    except Exception as e:
        print("Error:", e)
        raise

async def embed_document(doc):
    try:
        embeddings = await get_embeddings(doc.page_content)
        hash_val = hashlib.md5(doc.page_content.encode()).hexdigest()

        return PineconeRecord(
            id=hash_val,
            values=embeddings,
            metadata={
                'text': doc.metadata['text'],
                'pageNumber': doc.metadata['pageNumber']
            }
        )
    except Exception as e:
        print("Error embedding document:", e)
        raise

async def prepare_documents(pages):
    documents = []
    for page in pages:
        page_content = page['pageContent'].replace("\n", "")
        metadata = {
            'pageNumber': page['metadata']['loc']['pageNumber'],
            'text': truncate_string_by_bytes(page_content, 36000)
        }
        # Split the docs
        splitter = RecursiveCharacterTextSplitter()
        docs = await splitter.split_documents([
            Document(page_content=page_content, metadata=metadata)
        ])
        documents.extend(docs)
    return documents

def truncate_string_by_bytes(s, bytes):
    enc = s.encode('utf-8')
    return enc[:bytes].decode('utf-8', 'ignore')
