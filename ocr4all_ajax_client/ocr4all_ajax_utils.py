"""
OCR4All Ajax client

The uniwuezpd/ocr4all does not provide a REST API, but many operations can be
performed via AJAX calls. This module provides Python functions to invoke these
AJAX endpoints, mimicking the behavior of the OCR4All web UI.
"""

import json
import os
import time
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

from logger import logger

load_dotenv()

OCR4ALL_EXEC_TIMEOUT_S = int(os.getenv("OCR4ALL_EXEC_TIMEOUT_S", "60"))
OCR4ALL_WAIT_TIMEOUT_S = int(os.getenv("OCR4ALL_WAIT_TIMEOUT_S", "3600"))
OCR4ALL_HTTP_TIMEOUT_S = int(os.getenv("OCR4ALL_HTTP_TIMEOUT_S", "30"))


def ocr4all_open_project(
        session: requests.Session,
        base_url: str,
        project_dir: str,
        image_type: str = "Original",
        reset_session: bool = True,
) -> None:
    """
    Opens an OCR4all project.

    Mirrors overview.jsp:
      1) ajax/overview/checkDir
      2) ajax/overview/validate
      3) ajax/overview/validateProject

    Args:
        session: requests.Session with cookies etc.
        base_url: Base URL of OCR4all server, e.g. "http://ocr4all:8080"
        project_dir: Project directory
        image_type: Image type to use
        reset_session: Whether to reset session state

    Raises:
        RuntimeError: If any step fails
    """
    # Ensure session cookie exists
    session.get(f"{base_url}/", timeout=OCR4ALL_HTTP_TIMEOUT_S).raise_for_status()

    # 1) checkDir
    r = session.get(
        f"{base_url}/ajax/overview/checkDir",
        params={
            "projectDir": project_dir,
            "imageType": image_type,
            "resetSession": str(reset_session).lower(),
        },
        timeout=OCR4ALL_HTTP_TIMEOUT_S,
    )
    r.raise_for_status()
    if r.text.strip() != "true":
        raise RuntimeError(f"ocr4all checkDir returned {r.text!r} for projectDir={project_dir}")

    # 2) validate
    r = session.get(f"{base_url}/ajax/overview/validate", timeout=OCR4ALL_HTTP_TIMEOUT_S)
    r.raise_for_status()
    if r.text.strip() != "true":
        # UI does invalidateSession here
        session.get(f"{base_url}/ajax/overview/invalidateSession", timeout=OCR4ALL_HTTP_TIMEOUT_S)
        raise RuntimeError(f"ocr4all validate returned {r.text!r}")

    # 3) validateProject
    r = session.get(
        f"{base_url}/ajax/overview/validateProject",
        params={"projectDir": project_dir, "imageType": image_type},
        timeout=OCR4ALL_HTTP_TIMEOUT_S,
    )
    r.raise_for_status()
    if r.text.strip() != "true":
        raise RuntimeError(
            f"ocr4all validateProject returned:\n {r.text!r}"
        )


def ocr4all_get_page_ids(
        session: requests.Session,
        base_url: str,
        image_type: str = "Binary",
) -> List[str]:
    """
    Retrieves the list of page IDs for the specified image type.

    Args:
        session: requests.Session with cookies etc.
        base_url: Base URL of OCR4all server, e.g. "http://ocr4all:8080"
        param image_type: Image type to use

    Returns:
        List of page IDs.
    """
    r = session.get(
        f"{base_url}/ajax/generic/pagelist",
        params={"imageType": image_type},
        timeout=OCR4ALL_HTTP_TIMEOUT_S,
    )
    r.raise_for_status()

    # OCR4all returns JSON array, e.g. ["0001", "0002", ...] or []
    try:
        data = r.json()
    except Exception as e:
        raise RuntimeError(f"pagelist did not return JSON. head={r.text[:200]!r}") from e

    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected pagelist payload: {type(data)} {str(data)[:200]}")

    return [str(x) for x in data]


def ocr4all_threads(session: requests.Session, base_url: str) -> int:
    """
    Retrieves the number of threads configured in OCR4all.

    Args:
        session: requests.Session with cookies etc.
        base_url: Base URL of OCR4all server, e.g. "http://ocr4all:8080"

    Returns:
        Number of threads.
    """
    r = session.get(f"{base_url}/ajax/generic/threads", timeout=OCR4ALL_HTTP_TIMEOUT_S)
    r.raise_for_status()
    try:
        return max(1, int(r.text.strip()))
    except Exception:
        return 1


def ocr4all_processflow_execute(
        session: requests.Session,
        base_url: str,
        page_ids: List[str],
        processes: List[str],
        process_settings: Dict[str, Any],
) -> None:
    """
    Executes the OCR4all process flow.

    Args:
        session: requests.Session with cookies etc.
        base_url: Base URL of OCR4all server, e.g. "http://ocr
        page_ids: List of page IDs to process.
        processes: List of process steps to execute.
        process_settings: Dictionary of process settings.

    Raises:
        RuntimeError: If the execution fails (HTTP status != 200).
    """
    payload = {
        "pageIds": page_ids,
        "processesToExecute": processes,
        "processSettings": process_settings,
    }
    r = session.post(
        f"{base_url}/ajax/processFlow/execute",
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=OCR4ALL_EXEC_TIMEOUT_S,
    )
    if r.status_code != 200:
        raise RuntimeError(f"processFlow/execute failed: HTTP {r.status_code}: {r.text[:500]}")


def ocr4all_processflow_wait(
        session: requests.Session,
        base_url: str,
        timeout_s: int = OCR4ALL_WAIT_TIMEOUT_S,
) -> None:
    """
    Waits for the OCR4all process flow to complete.

    Args:
        session: requests.Session with cookies etc.
        base_url: Base URL of OCR4all server, e.g. "http://ocr4all:8080"
        timeout_s: Maximum time to wait in seconds.
    """
    t0 = time.time()
    last = None
    while True:
        cur = ocr4all_processflow_current(session, base_url)

        if cur != last:
            logger.info(f"OCR4all current: {cur!r}")
            last = cur

        if cur == "":
            return

        if time.time() - t0 > timeout_s:
            raise TimeoutError("Timed out waiting for OCR4all process flow to finish")

        time.sleep(1)


def ocr4all_checkpdf(session: requests.Session, base_url: str) -> bool:
    """ Checks if the project contains PDF files which need to be converted to images. """
    r = session.get(f"{base_url}/ajax/overview/checkpdf", timeout=OCR4ALL_HTTP_TIMEOUT_S)
    r.raise_for_status()
    return r.text.strip().lower() == "true"


def ocr4all_convert_project_files(session: requests.Session, base_url, delete_blank: bool, dpi: int,
                                  timeout_s: int = 600) -> str:
    """
    Triggers OCR4all PDF -> PNG conversion.

    Important: conversion may take minutes. OCR4all may not respond quickly.
    Therefore:
      - use a higher timeout
      - tolerate ReadTimeout and continue (conversion might still be running server-side)

    Args:
        session: requests.Session with cookies etc.
        base_url: Base URL of OCR4all server, e.g. "http://ocr4all:8080"
        delete_blank: Whether to delete blank pages.
        dpi: DPI for conversion.
        timeout_s: HTTP timeout in seconds.

    Returns:
        Server response text, or empty string if timeout occurred.
    """
    try:
        r = session.post(
            f"{base_url}/ajax/overview/convertProjectFiles",
            data={"deleteBlank": str(delete_blank).lower(), "dpi": str(int(dpi))},
            timeout=timeout_s,
        )
        r.raise_for_status()
        return r.text
    except requests.exceptions.ReadTimeout:
        # OCR4all often keeps converting even if the HTTP response doesn't arrive in time.
        logger.warning(
            f"convertProjectFiles timed out after {timeout_s}s; assuming conversion continues in background."
        )
        return ""


def ocr4all_processflow_current(session: requests.Session, base_url: str) -> str:
    """ Returns current process flow step. Empty string if idle. """
    r = session.get(f"{base_url}/ajax/processFlow/current", timeout=OCR4ALL_HTTP_TIMEOUT_S)
    r.raise_for_status()
    return r.text.strip()


def ocr4all_processflow_execute_json(
        session: requests.Session,
        base_url: str,
        page_ids: List[str],
        processes: List[str],
        process_settings: Dict[str, Any],
        timeout_s: float = 3600,
        retries: int = 12,
        retry_sleep_s: float = 2.0,
) -> None:
    """
    Executes the OCR4all process flow with JSON payload and retries.

    Args:
        session: requests.Session with cookies etc.
        base_url: Base URL of OCR4all server, e.g. "http://ocr4all:8080"
        page_ids: List of page IDs to process.
        processes: List of process steps to execute.
        process_settings: Dictionary of process settings.
        timeout_s: (optional) HTTP timeout in seconds for each attempt.
        retries: (optional) Number of retries if execution fails.
        retry_sleep_s: (optional) Sleep time between retries in seconds.

    Raises:
        RuntimeError: If the execution fails after retries.
    """
    url = f"{base_url}/ajax/processFlow/execute"

    payload = {
        "pageIds": page_ids,
        "processesToExecute": processes,
        "processSettings": process_settings,
    }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",

        "Origin": os.getenv("OCR4ALL_ORIGIN", "http://ocr4all:8080"),
        "Referer": os.getenv("OCR4ALL_REFERER", f"{base_url}/ProcessFlow"),
    }

    for attempt in range(1, retries + 1):
        # If OCR4All is busy, don't even try
        cur = ocr4all_processflow_current(session, base_url)
        if cur != "":
            time.sleep(retry_sleep_s)
            continue

        r = session.post(url, headers=headers, json=payload, timeout=timeout_s)

        logger.info(
            f"processFlow/execute attempt {attempt}/{retries} -> HTTP {r.status_code}, len={len(r.text or '')}"
        )

        if r.status_code == 200:
            return

        logger.error(f"processFlow/execute failed: HTTP {r.status_code}: {r.text[:1000]}")
        if r.text:
            logger.error(f"processFlow/execute response head: {r.text[:500]!r}")
        time.sleep(retry_sleep_s)

    raise RuntimeError("processFlow/execute failed after retries")
