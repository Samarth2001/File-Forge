class StatsManager:
    def __init__(self):
        self.files_processed = 0
        self.size_processed = 0
        self.category_counts = {}

    def update_stats(self, file_info):
        self.files_processed += 1
        self.size_processed += file_info['size']
        category = file_info['category']
        self.category_counts[category] = self.category_counts.get(category, 0) + 1

    def get_stats(self):
        return {
            'files_processed': self.files_processed,
            'size_processed': self.size_processed,
            'category_counts': self.category_counts
        }