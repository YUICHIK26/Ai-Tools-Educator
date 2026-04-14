import json
import os
import time
import uuid
from typing import Any, Dict, List, Optional


DEFAULT_PATH = os.path.join('Data', 'ChatConversations.json')


def _now_ms() -> int:
    return int(time.time() * 1000)


def _new_id() -> str:
    # short but unique enough for single-user local apps
    return uuid.uuid4().hex


class ConversationStore:
    """Simple JSON-file conversation store.

    Format:
    {
      "version": 1,
      "conversations": [
        {
          "id": "...",
          "title": "New Chat",
          "pinned": false,
          "created_at": 1710000000000,
          "updated_at": 1710000000000,
          "messages": [
            {"role": "user"|"assistant"|"system", "content": "...", "ts": 171...}
          ]
        }
      ]
    }
    """

    def __init__(self, path: str = DEFAULT_PATH):
        self.path = path
        self._ensure_file()

    def _ensure_file(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            self._write({"version": 1, "conversations": []})

    def _read(self) -> Dict[str, Any]:
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if not isinstance(data, dict) or 'conversations' not in data:
                return {"version": 1, "conversations": []}
            if not isinstance(data.get('conversations'), list):
                data['conversations'] = []
            data.setdefault('version', 1)
            return data
        except Exception:
            return {"version": 1, "conversations": []}

    def _write(self, data: Dict[str, Any]) -> None:
        tmp = self.path + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.path)

    def list_conversations(self) -> List[Dict[str, Any]]:
        data = self._read()
        convs = data['conversations']

        def _key(c: Dict[str, Any]):
            # pinned first, then updated desc
            return (
                0 if c.get('pinned') else 1,
                -(int(c.get('updated_at') or 0))
            )

        out = []
        for c in sorted(convs, key=_key):
            out.append({
                'id': c.get('id'),
                'title': c.get('title') or 'New Chat',
                'pinned': bool(c.get('pinned')),
                'created_at': c.get('created_at'),
                'updated_at': c.get('updated_at'),
                'message_count': len(c.get('messages') or []),
            })
        return out

    def get_conversation(self, conv_id: str) -> Optional[Dict[str, Any]]:
        data = self._read()
        for c in data['conversations']:
            if c.get('id') == conv_id:
                return c
        return None

    def create_conversation(self, title: str = 'New Chat') -> Dict[str, Any]:
        data = self._read()
        now = _now_ms()
        conv = {
            'id': _new_id(),
            'title': title or 'New Chat',
            'pinned': False,
            'created_at': now,
            'updated_at': now,
            'messages': []
        }
        data['conversations'].append(conv)
        self._write(data)
        return conv

    def update_conversation(self, conv_id: str, *, title: Optional[str] = None, pinned: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        data = self._read()
        for c in data['conversations']:
            if c.get('id') == conv_id:
                if title is not None:
                    c['title'] = title.strip()[:80] if title.strip() else 'New Chat'
                if pinned is not None:
                    c['pinned'] = bool(pinned)
                c['updated_at'] = _now_ms()
                self._write(data)
                return c
        return None

    def delete_conversation(self, conv_id: str) -> bool:
        data = self._read()
        before = len(data['conversations'])
        data['conversations'] = [c for c in data['conversations'] if c.get('id') != conv_id]
        if len(data['conversations']) == before:
            return False
        self._write(data)
        return True

    def append_message(
        self,
        conv_id: str,
        role: str,
        content: str,
        *,
        attachments: Optional[List[Dict[str, Any]]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Append a message to a conversation.

        attachments: list of dicts like {id, name, size, mimetype, url}
        meta: optional free-form metadata (e.g., model, tool, etc.)
        """
        data = self._read()
        now = _now_ms()
        for c in data['conversations']:
            if c.get('id') == conv_id:
                c.setdefault('messages', [])
                msg: Dict[str, Any] = {'role': role, 'content': content, 'ts': now}
                if attachments:
                    msg['attachments'] = attachments
                if meta:
                    msg['meta'] = meta
                c['messages'].append(msg)
                c['updated_at'] = now
                self._write(data)
                return c
        return None
