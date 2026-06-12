import time

class Timer:
    def __enter__(self) -> "Timer":
        self._start = time.monotonic()
        return self
    def __exit__(self, *_) -> None:
        self.elapsed = round(time.monotonic() - self._start, 2)
        