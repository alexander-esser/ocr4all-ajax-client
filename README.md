# ocr4all-ajax-client

A lightweight Python client for automating **OCR4All** via its internal AJAX endpoints.

**What is this?**  
*ocr4all-ajax-client* is a small Python library that exposes OCR4All’s AJAX endpoints as reusable Python functions.  

**Why?**
The OCR4All Docker image `uniwuezpd/ocr4all` does not provide a public REST API. Therefore, this library provides Python functions to invoke these AJAX endpoints, mimicking the behavior of the OCR4All web UI.  

---

## Installation

```bash
pip install ocr4all-ajax-client
```

or directly from source:

```bash
git clone https://github.com/alexander-esser/ocr4all-ajax-client.git
cd ocr4all-ajax-client
pip install -e .
```

---

## Basic usage

```python
import requests
from ocr4all_ajax_client import (
    ocr4all_open_project,
    ocr4all_get_page_ids,
    ocr4all_processflow_execute,
    ocr4all_processflow_wait,
)

BASE_URL = "http://localhost:8080/ocr4all"
PROJECT_DIR = "/var/ocr4all/data/my_project"

session = requests.Session()

# Open and validate project
ocr4all_open_project(session, BASE_URL, PROJECT_DIR)

# Get page IDs
page_ids = ocr4all_get_page_ids(session, BASE_URL)

# Execute OCR4All process flow
ocr4all_processflow_execute(
    session=session,
    base_url=BASE_URL,
    page_ids=page_ids,
    processes=[
        "preprocessing",
        "layout-analysis",
        "ocr",
        "postprocessing",
    ],
    process_settings={
        "ocr": {
            "model": "Fraktur",
        }
    },
)

# Wait until OCR4All is finished
ocr4all_processflow_wait(session, BASE_URL)
```

More examples can be found in the *examples/* folder.

--- 

## Docker demo

A minimal *docker-compose.yml* is included in the *docker/* folder to start OCR4All locally for testing:

```bash
docker compose build
docker compose up -d
```

OCR4All will then be available at:  
http://localhost:8080/ocr4all

---

## Supported workflows

- Project opening and validation
- PDF to image conversion (including blank-page handling)
- Page listing
- ProcessFlow execution
- ProcessFlow monitoring / waiting

---

## Tested with

- uniwuezpd/ocr4all:latest
- Apache Tomcat 9.x

---

## Limitations

- This is not an official OCR4All API. This project does not replace OCR4All - it enables automation around it.
- Endpoints may change with future OCR4All releases.
- Designed for controlled environments (Docker, local servers).

---

## Credits

Please credit the original OCR4All Docker image `uniwuezpd/ocr4all`, the corresponding [paper by Reul et al. (2019)](https://scholar.google.com/scholar?cluster=13735508718290237214), and the OCR4All project.

---

If you find this project useful, you can support my work with a [coffee ☕](https://www.buymeacoffee.com/aesser).

Developed with ♥ in Cologne.