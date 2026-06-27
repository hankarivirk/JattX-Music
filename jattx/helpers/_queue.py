"""jattx/helpers/_queue.py — In-memory per-group queue."""
from jattx.helpers._dataclass import Track, Media

_queues: dict[int, list] = {}
_current: dict[int, Track | Media | None] = {}


class Queue:
    def add(self, chat_id: int, track: Track | Media):
        _queues.setdefault(chat_id, []).append(track)

    def pop(self, chat_id: int) -> Track | Media | None:
        q = _queues.get(chat_id, [])
        if not q:
            return None
        track = q.pop(0)
        _current[chat_id] = track
        return track

    def current(self, chat_id: int) -> Track | Media | None:
        return _current.get(chat_id)

    def get_queue(self, chat_id: int) -> list:
        return list(_queues.get(chat_id, []))

    def clear(self, chat_id: int):
        _queues.pop(chat_id, None)
        _current.pop(chat_id, None)

    def shuffle(self, chat_id: int):
        import random
        q = _queues.get(chat_id, [])
        random.shuffle(q)

    def remove(self, chat_id: int, pos: int) -> bool:
        q = _queues.get(chat_id, [])
        if 0 < pos <= len(q):
            q.pop(pos - 1)
            return True
        return False

    def size(self, chat_id: int) -> int:
        return len(_queues.get(chat_id, []))

    def is_empty(self, chat_id: int) -> bool:
        return self.size(chat_id) == 0
