from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union


class WriteRequest(BaseModel):
    """
    数据写入请求的基础模型。
    operation 字段决定了具体执行哪种操作。
    """
    collection: str = Field(..., description="Data collection to handle")
    operation: str = Field(
        ...,
        description="Operation type: insert_one, insert_many, update_one, update_many, delete_one, delete_many")
    data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = Field(
        None,
        description="The data to be inserted or updated."
                    " For 'update', this refers to updating the document (such as {$set: ... }) }）")
    filter: Optional[Dict[str, Any]] = Field(None, description="Query filter, used for update and delete operations.")
    options: Optional[Dict[str, Any]] = Field(None, description="Operation options, such as 'upsert': True, etc.")

    class Config:
        json_schema_extra = {
            "example": {
                "collection": "users",
                "operation": "insert_one",
                "data": {"name": "John Doe", "age": 30, "email": "john@example.com"}
            }
        }
