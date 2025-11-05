from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class Upload_File_Serializer(BaseModel):
    filename: str
    content_type: str
    file_path: str
    upload_time: datetime = datetime.now()


class Input_Question_Serializer(BaseModel):
    question: str
    # user_id: Optional[str] = None


class Generate_Content_Serializer(BaseModel):
    question: str
    file_names: Optional[List[str]] = None
    chat_space: str


class Output_Response_Serializer(BaseModel):
    answer: str
