from __future__ import annotations

import os
import re
import uuid
from typing import Dict, List

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


UPLOAD_BASE = os.path.join('Data', 'uploads')


def _clean_filename(name: str) -> str:
    name = name or 'file'
    name = secure_filename(name)
    # keep some unicode-ish safety; secure_filename already strips a lot.
    name = name[:180] if len(name) > 180 else name
    return name or 'file'


def save_attachments(conversation_id: str, files: List[FileStorage]) -> List[Dict]:
    """Save uploaded files and return attachment metadata list."""
    conv = conversation_id or 'unknown'
    conv = re.sub(r'[^a-zA-Z0-9_-]', '_', conv)

    folder = os.path.join(UPLOAD_BASE, conv)
    os.makedirs(folder, exist_ok=True)

    out: List[Dict] = []
    for f in files:
        if not f or not getattr(f, 'filename', None):
            continue

        orig_name = f.filename
        safe_name = _clean_filename(orig_name)
        file_id = uuid.uuid4().hex
        stored_name = f"{file_id}__{safe_name}"
        full = os.path.join(folder, stored_name)
        f.save(full)
        size = os.path.getsize(full) if os.path.exists(full) else None

        # Public URL served via /uploads/<conv>/<stored_name>
        url = f"/uploads/{conv}/{stored_name}"

        out.append({
            'id': file_id,
            'name': orig_name,
            'stored_name': stored_name,
            'size': size,
            'mimetype': getattr(f, 'mimetype', None),
            'url': url,
        })

    return out
