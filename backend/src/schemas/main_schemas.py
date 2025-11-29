from pydantic import BaseModel
from typing import List

class CombinationPayload(BaseModel):
    """
    用于接收包含食材列表的请求体。
    """
    combination: List[str]