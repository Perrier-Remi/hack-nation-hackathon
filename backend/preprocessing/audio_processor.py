class AudioProcessor:
    def __init__(self, audio: list[AudioSegment]):
        self.audio = audio

    def process(self) -> list[AudioSegment]:
        return self.audio