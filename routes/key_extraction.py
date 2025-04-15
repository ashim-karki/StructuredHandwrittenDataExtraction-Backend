# File: routes/extraction_routes.py

from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

from db.data_access import get_db
from routes.common.processors.key_value_extraction import extract_key_value_with_llm

# Define router
router = APIRouter(
    prefix="/extraction",
    tags=["extraction"],
    responses={404: {"description": "Not found"}},
)

# Define the default prompt template
DEFAULT_PROMPT = """
Please extract all key-value pairs from the following text.
Return the result as a JSON object where the keys are the entity names and the values are their corresponding values.

Text:
{text}

JSON Output:
"""

# Define request and response models
class ExtractionRequest(BaseModel):
    text: str
    custom_prompt: Optional[str] = None

class ExtractionResponse(BaseModel):
    extracted_data: Dict[str, Any]
    status: str

# Routes
@router.post("/extract-key-value", response_model=ExtractionResponse)
def extract_key_value(request: ExtractionRequest):
    """
    Extract key-value pairs from provided text.
    """
    try:
        print("request type", type(request))
        print("request text", request.text)
        if request.custom_prompt:
            extracted_data = extract_key_value_with_llm(
                request.text, 
                prompt_template=request.custom_prompt
            )
        else:
            extracted_data = extract_key_value_with_llm(
                request.text,
                prompt_template=DEFAULT_PROMPT
            )
        
        if not extracted_data:
            raise HTTPException(status_code=422, detail="Failed to extract data from the provided text")
        
        return {
            "extracted_data": extracted_data,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction error: {str(e)}")

@router.post("/extract-from-file")
async def extract_from_file(
    file: UploadFile = File(...),
    custom_prompt: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Extract key-value pairs from an uploaded file.
    """
    try:
        # Read file content
        content = await file.read()
        text = content.decode("utf-8")
        
        # Process the text
        if custom_prompt:
            extracted_data = extract_key_value_with_llm(text, prompt_template=custom_prompt)
        else:
            extracted_data = extract_key_value_with_llm(text, prompt_template=DEFAULT_PROMPT)
            
        if not extracted_data:
            raise HTTPException(status_code=422, detail="Failed to extract data from the file")
        
        return {
            "filename": file.filename,
            "extracted_data": extracted_data,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File processing error: {str(e)}")
    

# extract_key_value(
#     ExtractionRequest(
#         text="Sample text for key-value extraction. name: anil",
#         custom_prompt="Custom prompt for extraction."
#     )
# )