import hashlib
import os

class DuplicateHandler:
    def __init__(self):
        self.hash_cache = {}
        
    def get_file_hash(self, filepath):
        hasher = hashlib.md5()
        with open(filepath, 'rb') as f:
            buf = f.read(65536)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(65536)
        return hasher.hexdigest()
        
    def is_duplicate(self, filepath):
        file_hash = self.get_file_hash(filepath)
        is_dup = file_hash in self.hash_cache
        self.hash_cache[file_hash] = filepath
        return is_dup