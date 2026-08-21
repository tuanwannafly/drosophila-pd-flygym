class ThumbnailGenerator:
    @staticmethod
    def generate_placeholder() -> bytes:
        # Mock PNG signature for preview
        return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
