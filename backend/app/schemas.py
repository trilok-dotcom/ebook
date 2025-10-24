from pydantic import BaseModel
from typing import Optional, List

class NotifyUploadBody(BaseModel):
    recordId: str

class NotifyResult(BaseModel):
    status: str
    channels: List[str]
    messageId: Optional[str] = None
