"""
ocr4all-ajax-client

Public package API. Re-exports selected helpers from the internal modules so
users can import directly from `ocr4all_ajax_client`.
"""

from .ocr4all_client import (
    ocr4all_open_project,
    ocr4all_get_page_ids,
    ocr4all_threads,
    ocr4all_processflow_execute,
    ocr4all_processflow_wait,
    ocr4all_checkpdf,
    ocr4all_convert_project_files,
    ocr4all_processflow_current,
)

__all__ = [
    "ocr4all_open_project",
    "ocr4all_get_page_ids",
    "ocr4all_threads",
    "ocr4all_processflow_execute",
    "ocr4all_processflow_wait",
    "ocr4all_checkpdf",
    "ocr4all_convert_project_files",
    "ocr4all_processflow_current",
]
