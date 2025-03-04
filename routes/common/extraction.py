#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Main script to run the OCR pipeline.
"""

import os, sys

project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.append(project_root)

print(project_root)

from utils.file_utils import ensure_directories, clean_directories
from processors.layout_processor import LayoutProcessor
from processors.text_processor import TextProcessor
from Table_extraction.main import extract
import pandas as pd



model_path="./routes/common/models/model_doclayout/DocLayout-YOLO-DocStructBench/doclayout_yolo_docstructbench_imgsz1024.pt"

def text_extraction(img_path):
    # args = parse_arguments()
    
    # Setup directories
    root_path = os.path.abspath(os.getcwd())
    dirs = {
        'original': os.path.join(root_path, 'routes', 'common', 'images', 'original'),
        'resized': os.path.join(root_path, 'routes', 'common', 'images', 'resized'),
        'visualization': os.path.join(root_path, 'routes', 'common', 'images', 'visualization'),
    }
    
    ensure_directories(list(dirs.values()))
    
    clean_directories([dirs['original'], dirs['resized'], dirs['visualization']])
    
    # Process the document
    input_path = img_path

    clean_directories([dirs['original'], dirs['resized'], dirs['visualization']])

    layout_processor = LayoutProcessor(model_path=model_path, img_path=input_path)
    layout_processor.crop_images()
    layout_processor.visualize_bbox()
    
    # Step 3: OCR processing
    text_processor = TextProcessor()
    image_results, ocr = text_processor.process_directory(dirs['original'])

    ocr_texts = []
    for text in image_results:
        ocr_texts.append(f"{text['text']}")

    table_texts = []
    for image in image_results:
      if 'Table' in os.path.basename(image['image_path']):
        outputs=extract(ocr,image['image_path'])
        df = pd.DataFrame(outputs[1:], columns=outputs[0])
        table_texts=df.to_string(index=False)

    print('\n'.join(ocr_texts), '\n\n\n', table_texts)

    # for image in image_results:
    #     print(image['text'])
    # # Step 4: Text correction
    # correction_processor = CorrectionProcessor()
    # final_texts = correction_processor.correct_all(image_results)

    # Save results
    # final_texts = []
    # for text in image_results:
    #     final_texts.append(f"{text['text']}")

    # clean_directories([dirs['original'], dirs['resized'], dirs['visualization']])

    return '\n'.join(ocr_texts), table_texts
      
# if __name__ == "__main__":
#     main()
