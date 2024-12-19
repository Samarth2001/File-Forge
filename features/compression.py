import zipfile
import os

class CompressionHandler:
    def compress_file(self, filepath, archive_name):
        with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(filepath)