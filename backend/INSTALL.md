
# Backend Installation

## Requirements

- Python 3.12
- FFmpeg
- CPU-only PyTorch
- OpenCV

## Setup

Create and activate virtual environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Install CPU-only PyTorch:

```bash
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

Install application dependencies:

```bash
python -m pip install -r requirements.txt
```

## Start API

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The RVM model is loaded through PyTorch Hub on first processing.
