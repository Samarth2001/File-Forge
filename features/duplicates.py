import hashlib
import os
from typing import Dict, Optional

class DuplicateHandler:
    def __init__(self, max_cache_size: int = 10000):
        self.hash_cache: Dict[str, str] = {}
        self.max_cache_size = max_cache_size

    def _get_file_hash(self, filepath: str) -> Optional[str]:
        try:
            hasher = hashlib.sha256()
            with open(filepath, 'rb') as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except OSError:
            return None

    def is_duplicate(self, filepath: str) -> bool:
        file_hash = self._get_file_hash(filepath)
        if file_hash is None:
            return False

        if file_hash in self.hash_cache.values():
            return True
        
        if len(self.hash_cache) >= self.max_cache_size:
            self._prune_cache()
            
        self.hash_cache[filepath] = file_hash
        return False

    def _prune_cache(self):
        # Remove the oldest entries to make space
        num_to_remove = len(self.hash_cache) - self.max_cache_size + 1
        for _ in range(num_to_remove):
            self.hash_cache.pop(next(iter(self.hash_cache)))
