from contextlib import asynccontextmanager

from dependencies import *
from fastapi import APIRouter, Depends, FastAPI, File, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from serilalizers import *
from services.file_services import *
from typing import List

load_dotenv()

my_resources = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application starting up...")
    my_resources["database_connection"] = "connected_to_database"
    database()
    storage()
    vector_database()
    print("Database connection established.")
    yield
    print("Application shutting down...")
    if "database_connection" in my_resources:
        print("Closing database connection.")
        del my_resources["database_connection"]


app = FastAPI(lifespan=lifespan)
router = APIRouter()


origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@router.post("/get/user/single/doc")
def get_user_single_doc_public_path(
    document_id: int, store=Depends(storage), db=Depends(database)
):
    return File_Services.get_user_single_doc_public_path(
        document_id=document_id, store=store, db=db
    )


@router.post("/get/user/mulitple/docs")
def get_user_multiple_docs_public_path(
    store=Depends(storage), db=Depends(database), user=Depends(verify_token)
):
    return File_Services.get_user_multiple_docs_public_path(
        user_id=user["id"], store=store, db=db
    )


@router.post("/upload/single/file")
async def upload_file(
    file: UploadFile = File(...),
    store=Depends(storage),
    db=Depends(database),
    vdb=Depends(vector_database),
    user=Depends(verify_token),
):
    return await File_Services.upload_single_file(
        file=file, store=store, db=db, vdb=vdb, user_id=user["id"]
    )


@router.post("/upload/multiple/files")
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    store=Depends(storage),
    db=Depends(database),
    vdb=Depends(vector_database),
    user=Depends(verify_token),
):
    return await File_Services.upload_multiple_files(
        store=store, files=files, db=db, vdb=vdb, user_id=user["id"]
    )


@router.post("/delete/file")
def delete_file(doc_id: int, db=Depends(database), user=Depends(verify_token)):
    return File_Services.delete_file(doc_id=doc_id, db=db, user_id=user["id"])


@router.post("/get/user/context")
def get_user_context(
    question: str, file_names: List[str], vdb=Depends(vector_database)
):
    return File_Services.vector_db_semantic_search(
        vdb=vdb,
        question=question,
        file_names=file_names,
    )


@router.post("/ask")
def ask_question(
    data: Generate_Content_Serializer,
    vdb=Depends(vector_database),
    db=Depends(database),
    user=Depends(verify_token),
):
    response = File_Services.generate_from_context(
        vdb=vdb,
        question=data.question,
        file_names=data.file_names,
        db=db,
        user_id=user.id,
    )
    return response


@router.get("/get/user/history")
def get_user_history(db=Depends(database), user=Depends(verify_token)):
    return File_Services.get_user_history(user_id=user["id"], db=db)


@router.get("/get/user/docs")
def get_user_docs(db=Depends(database), user=Depends(verify_token)):
    return File_Services.get_user_docs(user_id=user["id"], db=db)


@router.get("/get/user/details")
def get_user_details(request: Request, db=Depends(database)):
    return verify_token(db=db, request=request)


@router.get("/get")
def get():
    for i in range(5):
        yield {"data": i}


app.include_router(router)
