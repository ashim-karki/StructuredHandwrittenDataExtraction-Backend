# File: routes/extraction_routes.py

from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

from db.data_access import get_db

import re

# Define router
router = APIRouter(
    prefix="/extraction",
    tags=["extraction"],
    responses={404: {"description": "Not found"}},
)

# Define request and response models
class ExtractionRequest(BaseModel):
    text: str
    profile: Optional[str] = None

class ExtractionResponse(BaseModel):
    extracted_data: Dict[str, Any]
    status: str


def extract_form_data(text):
    """
    Extract key information from the evaluation form text using delimiters.
    
    Args:
        text (str): The OCR-extracted text from the form
        
    Returns:
        dict: Dictionary containing the extracted information
    """
    # Define regex patterns with delimiters
    # Name pattern (delimited by "Student (Name):" and "Roll No:")
    name_pattern = r"Student\s+\(Name\):\s*([^\n]+?)(?=\s*Roll\s+No:)"
    
    # Roll Number pattern (delimited by "Roll No:" and typically the next line)
    roll_pattern = r"Roll\s+No:\s*([^\n]+)"
    
    # Total Marks pattern (delimited by "Total Marks Obtained" and "Comments:")
    # total_marks_pattern = r"Total\s+Marks\s+Obtained.*?:\s*(\w+(?:-\w+)*)(?=.*?Comments:)"
    # total_marks_pattern = r"Total\s+Marks\s+Obtained.*?:\s*(.+?)\.\nComments:"
    total_marks_pattern = r"Total\s+Marks\s+Obtained.*?:\s*(.+?)\s*\nComments:"
    
    # Alternative marks pattern from table (delimited by "Total Marks" row and the next row)
    
    # Comments pattern (delimited by "Comments:" and "Suggestions & Recommendations:")
    comments_pattern = r"Comments:\s*\n(.*?)(?=\s*Suggestions\s+&\s+Recommendations:)"
    
    # Suggestions & Recommendations pattern (delimited by "Suggestions & Recommendations:" and "Examiner:")
    suggestions_pattern = r"Suggestions\s+&\s+Recommendations:\s*\n(.*?)(?=\s*Examiner:)"
    
    # Extract information
    name_match = re.search(name_pattern, text, re.DOTALL)
    roll_match = re.search(roll_pattern, text, re.DOTALL)
    marks_match = re.search(total_marks_pattern, text, re.DOTALL)
    comments_match = re.search(comments_pattern, text, re.DOTALL)
    suggestions_match = re.search(suggestions_pattern, text, re.DOTALL)
    
    # Create result dictionary
    result = {
        "name": name_match.group(1).strip() if name_match else None,
        "roll_number": roll_match.group(1).strip() if roll_match else None,
        "marks": marks_match.group(1).strip() if marks_match else None,
        "comments": comments_match.group(1).strip() if comments_match else None,
        "suggestions": suggestions_match.group(1).strip() if suggestions_match else None
    }
    
    return result


def extract_fields(text):
    patterns = {
        "name": r"Student\s*\(Name\)\s*:\s*([A-Za-z\s\.\-']+?)(?=\s*Roll\s*No|Supervisor|Thesis|Project|Credit|$)",
        "roll_no": r"Roll\s*No\.?\s*[:\-]?\s*([0-9a-zA-Z]+)",
        "total_marks": r"Total\s*Marks\s*Obtained\s*\(in\s*words\)\s*[:\-]?\s*([A-Za-z\s\-]+?)(?=[\.\n\r]*(Comments|Suggestions|Examiner|Name|Signature|$))",
        "suggestions": r"Suggestions\s*&?\s*recommendations?\s*[:\-]?\s*([\s\S]*?)(?=\s*(Examiner|Name\s*:|Signature|Date|$))",
        "examiner_name": r"(?:Examiner\s*:?\s*(?:Name\s*:?)?)\s*([A-Za-z\s\.\-]+?)(?=\s*(Organization|Designation|Date|Signature|$))"
    }

    results = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        results[key] = match.group(1).strip() if match else None

    return results


def extract_campus_facilities_survey_data(text):
    """
    Extract key information from the campus facilities survey form.
    
    Args:
        text (str): The OCR-extracted text from the form
        
    Returns:
        dict: Dictionary containing the extracted information
    """
    # Student Information patterns
    name_pattern = r"name:\s*([^\n]+)"
    roll_no_pattern = r"roll No:\s*([^\n]+)"
    department_pattern = r"Department:\s*([^\n]+)"
    
    # Survey Questions patterns
    food_service_pattern = r"How satisfied are you\?\s*([^\n]+)"
    library_pattern = r"Are the resources sufficient\?\s*([^\n]+)"
    hostel_pattern = r"Is it well-maintained\?\s*([^\n]+)"
    sports_pattern = r"Are facilities available\?\s*([^\n]+)"
    wifi_pattern = r"Is the connection reliable\?\s*([^\n]+)"
    
    # Suggestions pattern (this might capture multiple lines)
    suggestions_pattern = r"Any suggestions for improvement\?\s*([\s\S]+?)(?=Thank you for your participation|$)"
    
    # Extract information
    name_match = re.search(name_pattern, text, re.DOTALL)
    roll_match = re.search(roll_no_pattern, text, re.DOTALL)
    department_match = re.search(department_pattern, text, re.DOTALL)
    food_match = re.search(food_service_pattern, text, re.DOTALL)
    library_match = re.search(library_pattern, text, re.DOTALL)
    hostel_match = re.search(hostel_pattern, text, re.DOTALL)
    sports_match = re.search(sports_pattern, text, re.DOTALL)
    wifi_match = re.search(wifi_pattern, text, re.DOTALL)
    suggestions_match = re.search(suggestions_pattern, text, re.DOTALL)
    
    # Create result dictionary
    result = {
        "name": name_match.group(1).strip() if name_match else None,
        "roll_number": roll_match.group(1).strip() if roll_match else None,
        "department": department_match.group(1).strip() if department_match else None,
        "food_service_satisfaction": food_match.group(1).strip() if food_match else None,
        "library_resources_sufficient": library_match.group(1).strip() if library_match else None,
        "hostel_well_maintained": hostel_match.group(1).strip() if hostel_match else None,
        "sports_facilities_available": sports_match.group(1).strip() if sports_match else None,
        "wifi_connection_reliable": wifi_match.group(1).strip() if wifi_match else None,
        "improvement_suggestions": suggestions_match.group(1).strip() if suggestions_match else None
    }
    
    return result


def extract_survey_form(text):


    patterns = {
        "Name": r"(?i)\bname\b[^a-zA-Z0-9]*\s*(?P<Name>[A-Z][a-z]+\s+[A-Z][a-z]+)",
        
        "Roll No": r"(?i)\broll\s*no\.?\b[^a-zA-Z0-9]*\s*(?P<Roll>[A-Z0-9/]+)",
        
        "Department": r"(?i)\bdepartment\b[^a-zA-Z0-9]*\s*(?P<Department>[\w\s&().]+)",

        "Food Service Satisfaction": r"(?i)\bfood\s*service\b[^a-zA-Z0-9]*.*?(how\s+satisfied\s+are\s+you\??)?[^a-zA-Z0-9]*\s*(?P<Food>.+?)(?=\n|library|hostel|sports|wifi|internet|$)",

        "Library Resources": r"(?i)\blibrary\b.*?(resources|sufficient)?[^a-zA-Z0-9]*\s*(?P<Library>.+?)(?=\n|hostel|sports|wifi|internet|suggestions|$)",

        "Hostel Maintenance": r"(?i)\bhostel\b.*?(maintained)?[^a-zA-Z0-9]*\s*(?P<Hostel>.+?)(?=\n|sports|wifi|internet|suggestions|$)",

        "Sports & Recreation": r"(?i)(sports|recreation)\b.*?(facilities|available)?[^a-zA-Z0-9]*\s*(?P<Sports>.+?)(?=\n|internet|wifi|suggestions|$)",

        "Internet Reliability": r"(?i)\b(internet|wifi)\b.*?(connection|reliable)?[^a-zA-Z0-9]*\s*(?P<Internet>.+?)(?=\n|suggestions|$)",

        "Suggestions": r"(?i)\bsuggestions\b.*?(improvement)?[^a-zA-Z0-9]*\s*(?P<Suggestions>.+?)(?=thank\s+you|\Z)",
    }

    results = {}

    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            results[key] = match.group(match.lastgroup).strip()
        else:
            results[key] = None

    return results



# Routes
@router.post("/extract-key-value", response_model=ExtractionResponse)
def extract_key_value(request: ExtractionRequest):
    """
    Extract key-value pairs from provided text based on profile.
    """
    try:
        # Select extraction method based on profile
        if request.profile == "evaluation_form":
            extracted_data = extract_fields(str(request.text))
        elif request.profile == "survey_form":
            extracted_data = extract_survey_form(str(request.text))
        else:
            # If no profile is specified or unknown profile, use the default evaluation form extractor
            extracted_data = str(request.text)
        
        if not extracted_data:
            raise HTTPException(status_code=422, detail="Failed to extract data from the provided text")
        
        return {
            "extracted_data": extracted_data,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction error: {str(e)}")


