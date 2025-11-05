import os
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastembed import TextEmbedding
from parsers import *
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from serilalizers import *
from services.llm_service import *

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)


def safe_supabase_database_action(action: Callable[[], Any]) -> Dict[str, Any]:
    try:
        response = action()
        data = getattr(response, "data", None)
        error = getattr(response, "error", None)
        if not data and hasattr(response, "__dict__"):
            data = response.__dict__.get("data")
        if error:
            raise HTTPException(status_code=500, detail=f"Supabase Error: {error}")
        if data is None:
            raise HTTPException(
                status_code=500, detail="No data returned from Supabase"
            )
        return {"success": True, "data": data, "error": None}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Unexpected Supabase error: {str(e)}"
        )


def safe_supabase_storage_action(action: Callable[[], Any]) -> Dict[str, Any]:
    try:
        response = action()
        if hasattr(response, "error") and response.error:
            raise HTTPException(
                status_code=500, detail=f"Supabase Storage Error: {response.error}"
            )
        if hasattr(response, "__dict__"):
            data = response.__dict__
        elif isinstance(response, dict):
            data = response
        else:
            data = {"result": str(response)}
        return {"success": True, "data": data, "error": None}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Unexpected Supabase Storage error: {str(e)}"
        )


class File_Services:
    @staticmethod
    def chunk_to_embeddings(text):
        chunk_size = 500
        words = text.split()
        chunks = [
            " ".join(words[i : i + chunk_size])
            for i in range(0, len(words), chunk_size)
        ]
        embeddings = TextEmbedding().embed(chunks)
        return list(embeddings), chunks

    @staticmethod
    def query_embedding(text):
        embeddings = TextEmbedding().embed([text])
        return list(embeddings)[0].tolist()

    @staticmethod
    def insert_question(db, question, chat_space, user_id):
        response = safe_supabase_database_action(
            lambda: db.table("questions")
            .insert(
                {"question": question, "user_id": user_id, "chat_space": chat_space}
            )
            .execute()
        )
        return response

    @staticmethod
    def insert_response(db, question_id, response):
        response = safe_supabase_database_action(
            lambda: db.table("questions")
            .update({"response": response})
            .eq("id", question_id)
            .execute()
        )
        return response

    @staticmethod
    def get_user_single_doc_public_path(db, document_id, store):
        database_response = safe_supabase_database_action(
            lambda: db.table("documents").select("*").eq("id", document_id).execute()
        )
        path = []
        for docs in database_response["data"]:
            storage_response = safe_supabase_storage_action(
                lambda: store.storage.from_("user_docs").get_public_url(str(docs["id"]))
            )
            path.append(storage_response["data"]["result"])
        return path

    @staticmethod
    def get_user_multiple_docs_public_path(db, user_id, store):
        database_response = safe_supabase_database_action(
            lambda: db.table("documents").select("*").eq("user_id", user_id).execute()
        )
        path = []
        for docs in database_response["data"]:
            storage_response = safe_supabase_storage_action(
                lambda: store.storage.from_("user_docs").get_public_url(str(docs["id"]))
            )
            path.append(storage_response["data"]["result"])
        return path

    @staticmethod
    def store_embeddings(chunks, embeddings, vdb, file_name):
        vector_db_response = vdb.upsert(
            collection_name="user_docs",
            points=[
                qmodels.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedd,
                    payload={
                        "file_name": file_name,
                        "text": chunk,
                    },
                )
                for chunk, embedd in zip(chunks, embeddings)
            ],
        )
        return vector_db_response

    @staticmethod
    def parse_uploaded_docs(mime_type, file_bytes):
        if mime_type == "application/pdf":
            return {
                "data": Parsers.pdf_parser_from_upload(pdf_bytes=file_bytes),
                "success": True,
            }
        elif (
            mime_type
            == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ):
            return {
                "data": Parsers.word_parser_from_upload(file_bytes=file_bytes),
                "success": True,
            }
        elif (
            mime_type == "image/png"
            or mime_type == "image/jpeg"
            or mime_type == "image/webp"
        ):
            return {
                "data": Parsers.image_parser_from_upload(image_bytes=file_bytes),
                "success": True,
            }
        elif mime_type == "text/plain":
            return {
                "data": (file_bytes).decode("utf-8"),
                "success": True,
            }
        else:
            return {
                "data": "File of this type is not supported",
                "success": False,
            }

    @staticmethod
    def vector_db_semantic_search(vdb, question: str, file_names: List[str]):
        embeddings = File_Services.query_embedding(text=question)
        print(file_names)
        filter_condition = qmodels.Filter(
            must=[
                qmodels.FieldCondition(
                    key="file_name",
                    match=qmodels.MatchAny(any=file_names),
                )
            ]
        )
        search_result = vdb.search(
            collection_name="user_docs",
            query_vector=embeddings,
            query_filter=filter_condition,
            limit=5,
        )
        contexts = []
        for hit in search_result:
            payload = hit.payload
            score = str(hit.score)
            if "text" in payload:
                contexts.append({"text": payload["text"], "score": score})
        return contexts

    @staticmethod
    def generate_from_context(vdb, db, chat_space, question, file_names, user_id):
        question_response = File_Services.insert_question(
            db=db, chat_space=chat_space, question=question, user_id=user_id
        )
        if question_response["success"]:
            if file_names:
                vdb_context = File_Services.vector_db_semantic_search(
                    vdb=vdb, question=question, file_names=file_names
                )
                context = f"question: {question}, context: " + "\n\n".join(
                    [r["text"] for r in vdb_context[:3]]
                )
            else:
                context = question
            llm_response = LlmService.generate_blog(prompt=context)
            response_insertion = File_Services.insert_response(
                question_id=question_response["data"][0]["id"],
                response=llm_response,
                db=db,
            )
            if response_insertion["success"]:
                return {
                    "data": llm_response,
                    "success": True,
                }
            else:
                return {
                    "data": "Your response was not stored",
                    "success": False,
                }
        else:
            return {
                "data": "Error inserting data",
                "success": False,
            }

    @staticmethod
    async def upload_single_file(
        db,
        vdb,
        store,
        user_id,
        file: UploadFile = File(...),
    ):
        file_bytes = await file.read()
        file_name = file.filename
        mime_type = file.content_type
        parsing = File_Services.parse_uploaded_docs(
            mime_type=mime_type,
            file_bytes=file_bytes,
        )
        if parsing["success"]:
            embeddings, chunks = File_Services.chunk_to_embeddings(text=parsing["data"])
            store_embeddings_response = File_Services.store_embeddings(
                embeddings=embeddings,
                file_name=file_name,
                vdb=vdb,
                chunks=chunks,
            )
            if store_embeddings_response.status == "completed":
                print("✅ Embeddings stored successfully!")
                database_response = safe_supabase_database_action(
                    lambda: db.table("documents")
                    .insert(
                        {
                            "doc_name": file_name,
                            "user_id": user_id,
                            "doc_size": round(len(file_bytes) / 1024, 2),
                        }
                    )
                    .execute()
                )
                file_id = str(database_response["data"][0]["id"])
                storage_response = safe_supabase_storage_action(
                    lambda: store.storage.from_("user_docs").upload(
                        path=file_id,
                        file=file_bytes,
                        file_options={
                            "cache-control": "3600",
                            "upsert": "false",
                            "content-type": mime_type,
                        },
                    )
                )
                return storage_response
            else:
                print("❌ Failed to store embeddings:", store_embeddings_response)
                return {
                    "data": "Embeddings not stored",
                    "success": False,
                }
        else:
            print(f"❌ {parsing['data']}")
            return {
                "data": parsing["data"],
                "success": False,
            }

    @staticmethod
    async def upload_multiple_files(
        db,
        vdb,
        user_id,
        store,
        files: List[UploadFile] = File(...),
    ):
        for file in files:
            storage_response = await File_Services.upload_single_file(
                db=db,
                store=store,
                file=file,
                vdb=vdb,
                user_id=user_id,
            )
            if storage_response["success"]:
                continue
            else:
                return {
                    "data": "files not uploaded",
                    "success": False,
                }
        return {
            "data": "files uploaded successfully",
            "success": True,
        }

    @staticmethod
    def delete_file(db, user_id, doc_id):
        db_response = safe_supabase_storage_action(
            lambda: db.table("documents")
            .delete()
            .in_("id", [doc_id])
            .eq("user_id", user_id)
            .execute()
        )
        if db_response["success"]:
            storage_response = safe_supabase_storage_action(
                lambda: db.storage.from_("user_docs").remove([str(doc_id)])
            )
        else:
            return db_response
        return storage_response

    @staticmethod
    def delete_session(db, user_id, chat_space):
        db_response = safe_supabase_storage_action(
            lambda: db.table("questions")
            .delete()
            .in_("chat_space", [chat_space])
            .eq("user_id", user_id)
            .execute()
        )
        return db_response

    @staticmethod
    def get_user_history(db, user_id):
        user_history = safe_supabase_database_action(
            lambda: db.table("questions").select("*").eq("user_id", user_id).execute()
        )
        return user_history

    @staticmethod
    def get_user_chat(db, chat_space, user_id):
        user_history = safe_supabase_database_action(
            lambda: db.table("questions")
            .select("*")
            .eq("chat_space", chat_space)
            .eq("user_id", user_id)
            .execute()
        )
        return user_history

    @staticmethod
    def get_user_docs(db, user_id):
        user_docs = safe_supabase_database_action(
            lambda: db.table("documents").select("*").eq("user_id", user_id).execute()
        )
        return user_docs
