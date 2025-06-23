import hashlib
import os
from typing import Dict, Optional

class DuplicateHandler:
    def __init__(self):
        self.hash_cache: Dict[str, str] = {}
        self.max_cache_size: int = 10000  # Prevent unlimited memory growth
        
    def get_file_hash(self, filepath: str) -> Optional[str]:
        """Calculate MD5 hash of a file with error handling"""
        try:
            hasher = hashlib.md5()
            with open(filepath, 'rb') as f:
                # Read in chunks to handle large files efficiently
                while chunk := f.read(65536):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except (IOError, OSError, PermissionError) as e:
            return None
        
    def is_duplicate(self, filepath: str) -> bool:
        """Check if file is a duplicate based on content hash"""
        try:
            file_hash = self.get_file_hash(filepath)
            if file_hash is None:
                return False  # Can't determine, assume not duplicate
                
            is_dup = file_hash in self.hash_cache
            
            # Add to cache if not duplicate and cache isn't full
            if not is_dup and len(self.hash_cache) < self.max_cache_size:
                self.hash_cache[file_hash] = filepath
            elif len(self.hash_cache) >= self.max_cache_size:
                # Clear some old entries to prevent memory issues
                self._cleanup_cache()
                self.hash_cache[file_hash] = filepath
                
            return is_dup
        except Exception:
            return False  # On any error, assume not duplicate

    def _cleanup_cache(self) -> None:
        """Remove half of the cache entries to free memory"""
        items_to_remove = len(self.hash_cache) // 2
        keys_to_remove = list(self.hash_cache.keys())[:items_to_remove]
        for key in keys_to_remove:
            del self.hash_cache[key]

    def get_cache_stats(self) -> Dict[str, int]:
        """Get statistics about the duplicate cache"""
        return {
            'cached_files': len(self.hash_cache),
            'max_cache_size': self.max_cache_size
        }

    def clear_cache(self) -> None:
        """Clear the duplicate detection cache"""
        self.hash_cache.clear()