from typing import Optional
from pydantic import BaseModel, Field

class PolicyChunk(BaseModel):
    text: str = Field(...,description="The text content of the policy chunk")
    source: Optional[str] = Field(..., description="source of the policy chunk, such as a URL or document name")
    page: int = Field(None,gt=0,description="Page number must be greater than 0") 
    section:Optional[str] = Field(None,description="Section of the document where the chunk is located, if applicable") 
    metadata: dict = Field(default_factory=dict, description="Additional metadata about the policy chunk, such as tags or categories")

