from fastapi import APIRouter, FastAPI
from contextlib import asynccontextmanager
from supabase import create_client, Client, ClientOptions
from dotenv import load_dotenv
import os

load_dotenv()

my_resources = {}

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_ANON_KEY,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application starting up...")
    my_resources["database_connection"] = "connected_to_database"
    print("Database connection established.")
    yield
    print("Application shutting down...")
    if "database_connection" in my_resources:
        print("Closing database connection.")
        del my_resources["database_connection"]


app = FastAPI(lifespan=lifespan)
router = APIRouter()


# @router.get("/first")
# def first():
#     try:
#         # response = supabase.table("timpass").select("*").execute()
#         print("Response:", response)
#         return {"data": response.data}
#     except Exception as e:
#         print("Error:", e)
#         return {"error": str(e)}

@router.get("/first")
def first():
    return {"data":"data",}

app.include_router(router)
