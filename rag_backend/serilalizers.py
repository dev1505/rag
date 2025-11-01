from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Upload_File_Serializer(BaseModel):
    filename: str
    content_type: str
    file_path: str
    upload_time: datetime = datetime.now()


class Input_Question_Serializer(BaseModel):
    question: str
    # user_id: Optional[str] = None


class Output_Response_Serializer(BaseModel):
    answer: str
