# Farm Animal Counter

A computer vision and Django REST API project for counting farm animals from video streams. The system detects and tracks animals crossing a virtual line, stores unique events in a database, and exposes simple statistics through an API.

## Overview

This project combines two parts:

1. A Django backend that stores detected animal records and returns daily statistics.
2. A Python computer vision script that uses YOLOv8 + ByteTrack to process a video or webcam feed and send detections to the backend.

The current implementation is best suited for local demo and portfolio use.

## Features

- Detects and tracks animals from a video or webcam feed
- Counts animals when they cross a virtual line
- Prevents duplicate records using `animal_type + track_id`
- Stores events in SQLite
- Exposes simple REST endpoints for logging and statistics
- Includes a sample video and YOLO model for quick testing

## Tech Stack

- Python 3.12
- Django 5
- Django REST Framework
- OpenCV
- Ultralytics YOLOv8
- ByteTrack
- SQLite

## Project Structure

```text
.
├── animal_counter.py      # Video processing, tracking, and API integration
├── animals_count/         # Django app
├── config/                # Django project settings and URLs
├── manage.py
├── requirements.txt
├── test_video.mp4         # Sample video for demo
└── yolov8n.pt             # Local YOLO model
```

## How It Works

1. `animal_counter.py` opens a video file or webcam stream.
2. YOLO detects animals in each frame.
3. ByteTrack assigns stable tracking IDs.
4. When an animal crosses the counting line, the script sends a `POST` request to the Django API.
5. The backend stores the event and prevents duplicates.
6. Statistics can be retrieved from the API.

## API Endpoints

### `POST /`

Creates a new animal log.

Example request:

```json
{
  "animal_type": "cow",
  "track_id": 101
}
```

Successful response:

```json
{
  "id": 1,
  "animal_type": "cow",
  "track_id": 101,
  "timestamp": "2026-01-26T19:30:00Z"
}
```

### `GET /logs/`

Returns the newest saved animal records ordered from newest to oldest.

Example response:

```json
[
  {
    "id": 52,
    "animal_type": "cow",
    "track_id": 292,
    "timestamp": "2026-05-20T13:34:01.506053Z"
  },
  {
    "id": 51,
    "animal_type": "cow",
    "track_id": 40,
    "timestamp": "2026-05-20T13:33:44.977940Z"
  }
]
```

### `GET /stats/`

Returns daily grouped statistics.

Example response:

```json
[
  {
    "date": "2026-01-26",
    "animal_type": "cow",
    "count": 4
  },
  {
    "date": "2026-01-26",
    "animal_type": "sheep",
    "count": 2
  }
]
```

### `GET /dashboard/`

Returns a simple browser dashboard that auto-refreshes every 3 seconds and shows recent logs plus daily stats.

## Local Setup

```bash
cd /path/to/Animals_count
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

The backend will start at:

```text
http://127.0.0.1:8000/
```

## Test the API

Open a second terminal and run:

```bash
cd /path/to/Animals_count
source .venv/bin/activate

curl -X POST http://127.0.0.1:8000/ \
  -H "Content-Type: application/json" \
  -d '{"animal_type":"cow","track_id":101}'

xdg-open http://127.0.0.1:8000/dashboard/

curl http://127.0.0.1:8000/logs/

curl http://127.0.0.1:8000/stats/
```

## Run the Animal Counter

With the included sample video:

```bash
cd /path/to/Animals_count
source .venv/bin/activate
python animal_counter.py --source test_video.mp4
```

With a webcam:

```bash
python animal_counter.py --source 0
```

## Notes

- The default local YOLO model works well for `cow` and `sheep`.
- `goat` support is intended for a custom model or Roboflow-based workflow.
- The backend is ready for API usage, while the OpenCV window-based demo is primarily designed for local execution.
- The dashboard page auto-refreshes, but it uses polling rather than WebSockets.
- Old records are automatically cleaned using retention settings in `config/settings.py`.

## Portfolio Value

This project demonstrates:

- backend API development with Django REST Framework
- computer vision pipeline integration
- object tracking and event-based counting
- practical database design with duplicate prevention
- end-to-end local system integration

## Possible Improvements

- add automated tests
- add Docker support
- add video upload processing instead of local-only display
- add deployment-ready API configuration
- add charts or dashboard for statistics

## Author

Built as a portfolio project for demonstrating practical computer vision and backend integration skills.
