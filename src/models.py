"""Curated multilingual models and atomic, resumable-by-retry downloads."""
import os
import tempfile
from pathlib import Path

import requests

# Approximate download sizes; existing custom models are also supported.
MODELS = {
    'tiny': 'Tiny · 75 MB · fastest',
    'base': 'Base · 142 MB · fast',
    'small': 'Small · 466 MB · balanced',
    'medium': 'Medium · 1.5 GB · higher accuracy',
    'large-v3-turbo': 'Large Turbo · 1.6 GB · higher accuracy',
}


def find_model(name):
    for directory in (
        Path.home() / 'Library/Application Support/pywhispercpp/models',
        Path.home() / '.local/share/pywhispercpp/models',
    ):
        candidate = directory / f'ggml-{name}.bin'
        if candidate.is_file():
            return candidate
    return None


def download_model(name, directory, progress):
    """Publish a model only after a complete download; never overwrite on failure."""
    if name not in MODELS:
        raise ValueError('Select one of the downloadable multilingual models.')
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / f'ggml-{name}.bin'
    url = f'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-{name}.bin'
    temporary = None
    try:
        with requests.get(url, stream=True, timeout=(15, 60)) as response:
            response.raise_for_status()
            total = int(response.headers.get('content-length', 0))
            downloaded = 0
            with tempfile.NamedTemporaryFile(dir=directory, suffix='.part', delete=False) as output:
                temporary = output.name
                for chunk in response.iter_content(1024 * 1024):
                    output.write(chunk)
                    downloaded += len(chunk)
                    progress(downloaded, total)
                output.flush()
                os.fsync(output.fileno())
            if downloaded == 0 or (total and downloaded != total):
                raise ValueError('The model download was incomplete. Please retry.')
            with open(temporary, 'rb') as downloaded_file:
                if downloaded_file.read(4) != b'lmgg':
                    raise ValueError('The download is not a Whisper model. Please retry.')
            os.replace(temporary, destination)
        return destination
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)
