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
    print("Database connection established.")
    yield
    print("Application shutting down...")
    if "database_connection" in my_resources:
        print("Closing database connection.")
        del my_resources["database_connection"]


app = FastAPI(lifespan=lifespan)
router = APIRouter()


@router.post("/upload/file", response_model=Upload_File_Serializer)
def upload_file(file: UploadFile = File(...)):
    return File_Services.upload_file(file=file)


@router.get("/first")
def first(db=Depends(database)):
    return {
        "data": db.table("questions").select("*").execute(),
    }


@router.post("/ask")
def ask_question(data: Input_Question_Serializer, db=Depends(database)):
    return File_Services.ask_question(data=data, db=db)


app.include_router(router)
