import os

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Request
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from supabase import Client, create_client

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


import os

from qdrant_client import QdrantClient
from qdrant_client import models as qmodels
from qdrant_client.http.exceptions import UnexpectedResponse

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
        _vdb.create_payload_index(
            collection_name="user_docs",
            field_name="file_name",
            field_schema=qmodels.PayloadSchemaType.KEYWORD,
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
        response = db.auth.get_user(token)
        user_data = response.user
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return {
            "id": user_data.id,
            "email": user_data.email,
            "role": user_data.role,
            "app_metadata": user_data.app_metadata,
            "user_metadata": user_data.user_metadata,
            "created_at": user_data.created_at,
            "aud": user_data.aud,
        }
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
