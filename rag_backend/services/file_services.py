from fastapi import HTTPException, FastAPI, UploadFile, File
from serilalizers import *
from datetime import datetime
from typing import Callable, Any, Dict


def safe_supabase_action(action: Callable[[], Any]) -> Dict[str, Any]:
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


class File_Services:
    @staticmethod
    def upload_file(file: UploadFile = File(...)):
        file_path = f"user_docs/{file.filename}"

        return Upload_File_Serializer(
            filename=file.filename,
            content_type=file.content_type,
            file_path=file_path,
            upload_time=datetime.now(),
        )

    @staticmethod
    def ask_question(data: Input_Question_Serializer, db):
        response = safe_supabase_action(
            lambda: db.table("questions").insert(data.model_dump()).execute()
        )

        output_response = Output_Response_Serializer(answer=data.question)
        return {
            "success": True,
            "insert_result": response["data"],
            "data": output_response.model_dump(),
        }
