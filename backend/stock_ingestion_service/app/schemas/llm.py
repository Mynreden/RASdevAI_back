from pydantic import BaseModel

class LLMPromptRequest(BaseModel):
    message: str
