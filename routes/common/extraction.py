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
from blueprints.tasks import Type




model_path="./routes/common/models/model_doclayout/DocLayout-YOLO-DocStructBench/doclayout_yolo_docstructbench_imgsz1024.pt"
class main_extraction:
    def __init__(self,flag):
        self.flag=flag

    def text_extraction(self,dirs,input_path):
        layout_processor = LayoutProcessor(model_path=model_path, img_path=input_path)
        layout_processor.crop_images()
        layout_processor.visualize_bbox()
        
        # Step 3: OCR processing
        text_processor = TextProcessor()
        image_results, ocr = text_processor.process_directory(dirs['original'])

        return image_results,ocr
    
    def main(self,img_path):
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

        if self.flag==Type.ocr:
            image_results,_=self.text_extraction(dirs,input_path)
            ocr_texts = []
            for text in image_results:
                ocr_texts.append(f"{text['text']}")
            return '\n'.join(ocr_texts),[]
        
        elif self.flag==Type.table_and_ocr:
            image_results,ocr=self.text_extraction(dirs,input_path)
            ocr_texts = []
            for text in image_results:
                ocr_texts.append(f"{text['text']}")
            table_texts = []
            # print(ocr_texts)
            for image in image_results:
                if 'Table' in os.path.basename(image['image_path']):
                    outputs=extract(image['image_path'],ocr)
                    df = pd.DataFrame(outputs[1:], columns=outputs[0])
                    table_texts=df.to_string(index=False)

            return '\n'.join(ocr_texts), table_texts

        else:
            outputs=extract(image['image_path'])
            df = pd.DataFrame(outputs[1:], columns=outputs[0])
            table_texts=df.to_string(index=False)

            return [],table_texts

        

