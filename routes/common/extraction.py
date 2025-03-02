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
from processors.pdf_processor import PDFProcessor
from processors.layout_processor import LayoutProcessor
from processors.text_processor import TextProcessor
from processors.correction_processor import CorrectionProcessor



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
    image_results = text_processor.process_directory(dirs['original'])
    
    # for image in image_results:
    #     print(image['text'])
    # # Step 4: Text correction
    # correction_processor = CorrectionProcessor()
    # final_texts = correction_processor.correct_all(image_results)
    
    # Save results
    final_texts = []
    for text in image_results:
        final_texts.append(f"{text['text']}")

    clean_directories([dirs['original'], dirs['resized'], dirs['visualization']])

    return '\n'.join(final_texts)
      
# if __name__ == "__main__":
#     main()
