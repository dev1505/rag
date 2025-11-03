from fastapi import APIRouter, FastAPI, UploadFile, File, Depends
from contextlib import asynccontextmanager
from serilalizers import *
from services.file_services import *
from dependencies import *

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


@router.post("/get/user/single/doc")
def get_user_single_doc_public_path(
    document_id: int, store=Depends(storage), db=Depends(database)
):
    return File_Services.get_user_single_doc_public_path(
        document_id=document_id, store=store, db=db
    )


@router.post("/get/user/mulitple/docs")
def get_user_multiple_docs_public_path(
    question_id: int, store=Depends(storage), db=Depends(database)
):
    return File_Services.get_user_multiple_docs_public_path(
        question_id=question_id, store=store, db=db
    )


@router.post("/upload/single/file")
async def upload_file(
    file: UploadFile = File(...),
    store=Depends(storage),
    db=Depends(database),
    vdb=Depends(vector_database),
):
    return await File_Services.upload_single_file(
        file=file, store=store, db=db, vdb=vdb
    )


@router.post("/upload/multiple/files")
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    store=Depends(storage),
    db=Depends(database),
    vdb=Depends(vector_database),
):
    return await File_Services.upload_multiple_files(
        store=store, files=files, db=db, vdb=vdb
    )


@router.post("/get/user/context")
def get_user_context(
    question: str,
    vdb=Depends(vector_database),
):
    return File_Services.vector_db_semantic_search(vdb=vdb, question=question)


@router.post("/ask")
def ask_question(data=Generate_Content_Serializer, vdb=Depends(vector_database)):
    return File_Services.generate_from_context(
        vdb=vdb, question=data.question, file_names=data.file_names
    )


app.include_router(router)
