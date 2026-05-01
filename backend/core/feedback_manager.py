import json
import os
from collections import defaultdict

FEEDBACK_FILE = "search_feedback.json"

class FeedbackManager:
    def __init__(self):
        self.feedback = defaultdict(lambda: defaultdict(int))
        self.load()

    def load(self):
        if os.path.exists(FEEDBACK_FILE):
            try:
                with open(FEEDBACK_FILE, 'r') as f:
                    data = json.load(f)
                    for query, urls in data.items():
                        for url, count in urls.items():
                            self.feedback[query][url] = count
            except:
                pass

    def save(self):
        with open(FEEDBACK_FILE, 'w') as f:
            json.dump(self.feedback, f)

    def record_click(self, query: str, url: str):
        self.feedback[query.lower()][url] += 1
        self.save()

    def get_boost_score(self, query: str, url: str) -> float:
        """Return a boost multiplier based on previous clicks."""
        clicks = self.feedback.get(query.lower(), {}).get(url, 0)
        return 1.0 + (min(clicks, 10) * 0.1) # Max 2x boost

feedback_manager = FeedbackManager()
