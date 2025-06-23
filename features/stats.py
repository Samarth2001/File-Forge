from typing import Dict, Any
import time
import json
import os

class StatsManager:
    def __init__(self):
        self.files_processed: int = 0
        self.size_processed: int = 0
        self.category_counts: Dict[str, int] = {}
        self.start_time: float = time.time()
        self.last_reset: float = time.time()
        self.errors_count: int = 0

    def update_stats(self, file_info: Dict[str, Any]) -> None:
        """Update processing statistics"""
        try:
            self.files_processed += 1
            self.size_processed += file_info.get('size', 0)
            category = file_info.get('category', 'Others')
            self.category_counts[category] = self.category_counts.get(category, 0) + 1
        except Exception as e:
            self.errors_count += 1

    def record_error(self) -> None:
        """Record an error occurrence"""
        self.errors_count += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        current_time = time.time()
        runtime = current_time - self.start_time
        
        return {
            'files_processed': self.files_processed,
            'size_processed': self.size_processed,
            'size_processed_mb': round(self.size_processed / (1024 * 1024), 2),
            'category_counts': self.category_counts,
            'runtime_seconds': round(runtime, 2),
            'runtime_hours': round(runtime / 3600, 2),
            'files_per_hour': round(self.files_processed / (runtime / 3600), 2) if runtime > 0 else 0,
            'errors_count': self.errors_count,
            'last_reset': self.last_reset
        }

    def reset_stats(self) -> None:
        """Reset all statistics"""
        self.files_processed = 0
        self.size_processed = 0
        self.category_counts.clear()
        self.errors_count = 0
        self.last_reset = time.time()

    def save_stats_to_file(self, filepath: str) -> bool:
        """Save current statistics to a JSON file"""
        try:
            stats = self.get_stats()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2)
            return True
        except Exception:
            return False

    def get_category_percentages(self) -> Dict[str, float]:
        """Get percentage breakdown by category"""
        if self.files_processed == 0:
            return {}
        
        return {
            category: round((count / self.files_processed) * 100, 2)
            for category, count in self.category_counts.items()
        }