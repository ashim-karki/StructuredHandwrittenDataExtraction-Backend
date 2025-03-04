#!/usr/bin/env python
"""
Initialization file for processors package.
"""

from .pdf_processor import PDFProcessor
from .layout_processor import LayoutProcessor
from .text_processor import TextProcessor
from .text_detection import TextDetection
from .text_recognition import TextRecognition
from .correction_processor import TextValidityChecker

all = [
    'PDFProcessor',
    'LayoutProcessor',
    'TextProcessor',
    'TextDetection',
    'TextRecognition',
    'TextValidityChecker'
]