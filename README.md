# 📝 Structured Handwritten Data Extraction Backend

This repository contains the backend for our final year project: **Structured Handwritten Data Extraction**. It is a FastAPI-based system that automatically extracts structured text—both printed and handwritten—from scanned documents such as marksheets, forms, and survey sheets using advanced OCR and layout analysis techniques.

---

## Frontend

Link to the frontend code [here](https://github.com/paudelanil/StructuredHandwrittenDataExtraction-Frontend)

---

## 🚀 Overview

Despite the shift to digital systems, handwritten documents are still widely used in sectors like healthcare, education, and finance. Manual data entry is time-consuming and error-prone. This system automates the process using:

- **DocLayout-YOLO** for layout detection  
- **YOLOv8** for word-level handwritten detection  
- **PaddleOCR** for printed text recognition  
- **TrOCR** for handwritten text recognition  
- **Table Transformer** for tabular data extraction

The pipeline ensures **layout-independent**, **accurate**, and **structured** output, ideal for digitization workflows.

---

## ⚙️ Configuration

To set up the project:

1. **Install dependencies**  
   ```bash
   pip install -r requirements.txt

2. **Create a .env file and add your Google API key for Gemini**  
   ```bash
   GOOGLE_API_KEY='your_key_here'

3. **Run the FastAPI development server**  
   ```bash
    uvicorn main:app --reload

4. **Configure Frontend**  
   Link to the frontend code [here](https://github.com/paudelanil/StructuredHandwrittenDataExtraction-Frontend)
  

## 📂 Using the Project

1. **Create a folder**
Navigate to the UI or backend storage path and create a folder to hold your document images.

![Screenshot 2025-04-22 at 10 02 30 AM](https://github.com/user-attachments/assets/73318881-e8dd-47a6-9994-f599b1abdf40)




2. **Upload images to the folder**
Add all scanned or captured documents (e.g., survey forms, marksheets) into the created folder.

![Screenshot 2025-04-22 at 10 02 54 AM](https://github.com/user-attachments/assets/81e04f3a-8a29-4c25-9305-e13548620bab)




3. **Go to Tasks section → Select Task Type → Run the task**
You can choose between OCR task or Table extraction or both based on your document content.

![Screenshot 2025-04-22 at 10 03 15 AM](https://github.com/user-attachments/assets/17027970-a73b-46b4-a817-cbc179e66b72)




4. **View the completed tasks → Make necessary edits or run heuristic evaluation**
Open the completed tasks tab to make any necessary changes to extracted data. You can also download them individually.

![Screenshot 2025-04-22 at 10 04 28 AM](https://github.com/user-attachments/assets/6138685e-d282-4078-b112-8543b43f623c)

![Screenshot 2025-04-22 at 10 05 20 AM](https://github.com/user-attachments/assets/f918436e-1d55-4a9d-9711-6b9a79768e69)




5. **Batch Download Results**
Once processing is complete, you can download all the extracted results in structured formats like CSV or JSON.

![Screenshot 2025-04-22 at 10 06 17 AM](https://github.com/user-attachments/assets/15bab92e-c746-4891-b95e-aaa6fdb8718e)
