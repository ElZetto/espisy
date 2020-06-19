class ESPNotFoundError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class NoGPIOError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
