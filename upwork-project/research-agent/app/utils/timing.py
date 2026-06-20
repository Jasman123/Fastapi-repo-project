import time

class Timer:
    def __enter__(self) -> "Timer":
        self._start = time.monotonic()
        return self

    @property
    def elapsed(self) -> float:
        return round(time.monotonic() - self._start, 2)

    def __exit__(self, *_) -> None:
        pass
        