import os
from supabase import create_client, Client
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from fastapi import Request, HTTPException, Depends

load_dotenv()

_db: Client = None
_storage: Client = None
_vdb = None

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")


def database():
    global _db
    _db = create_client(
        SUPABASE_URL,
        SUPABASE_ANON_KEY,
    )
    return _db


from qdrant_client import QdrantClient, models as qmodels
from qdrant_client.http.exceptions import UnexpectedResponse
import os

QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")


def vector_database():
    global _vdb
    _vdb = QdrantClient(
        url="https://d03eed59-6786-4359-8a9d-2efdb3676ea0.eu-west-1-0.aws.cloud.qdrant.io",
        api_key=QDRANT_API_KEY,
    )
    try:
        _vdb.create_collection(
            collection_name="user_docs",
            vectors_config=qmodels.VectorParams(
                size=384,
                distance=qmodels.Distance.COSINE,
            ),
            optimizers_config=qmodels.OptimizersConfigDiff(default_segment_number=2),
            hnsw_config=qmodels.HnswConfigDiff(
                m=16,
                ef_construct=100,
            ),
        )
        print("✅ Qdrant collection created.")
    except UnexpectedResponse as e:
        if "already exists" in str(e):
            print("ℹ️ Collection already exists — using existing one.")
        else:
            raise e
    return _vdb


def verify_token(request: Request, db=Depends(database)):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Authorization header missing or invalid"
        )
    token = auth_header.split(" ")[1]
    try:
        user = db.auth.get_user(token)
        if not user or not user.user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return user.uid
    except Exception as e:
        raise HTTPException(
            status_code=401, detail=f"Token verification failed: {str(e)}"
        )


def storage():
    global _storage
    _storage = create_client(
        SUPABASE_URL,
        SUPABASE_SERVICE_ROLE_KEY,
    )
    return _storage
