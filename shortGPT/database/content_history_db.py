import json
import os

class ContentHistoryDatabase:
    _instance = None

    def __new__(cls, db_path="content_history.json"):
        if cls._instance is None:
            cls._instance = super(ContentHistoryDatabase, cls).__new__(cls)
            cls._instance.db_path = db_path
            cls._instance.history = cls._instance._load_history()
        return cls._instance

    def _load_history(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {"facts": [], "reddit": []}
        return {"facts": [], "reddit": []}

    def save_history(self):
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=4)

    def add_fact(self, fact_text):
        if "facts" not in self.history:
            self.history["facts"] = []
        # Store only the first 50 chars to save space/tokens if we use this for filtering
        # Or store the whole thing. Let's store the whole thing for now but use a summary for the prompt.
        self.history["facts"].append(fact_text)
        self.save_history()

    def add_reddit_entry(self, question, script):
        if "reddit" not in self.history:
            self.history["reddit"] = []
        # Store as a dict
        self.history["reddit"].append({"question": question, "script": script})
        self.save_history()

    def get_recent_facts(self, limit=10):
        if "facts" not in self.history:
            return []
        return self.history["facts"][-limit:]

    def get_recent_reddit_questions(self, limit=20):
        if "reddit" not in self.history:
            return []
        # Return just the questions from the dict list
        # Filter out non-dict entries if any exist from legacy
        entries = [e["question"] if isinstance(e, dict) else e for e in self.history["reddit"]]
        return entries[-limit:]

    def get_overused_questions(self, max_usage=10):
        if "reddit" not in self.history:
            return []
        
        counts = {}
        for entry in self.history["reddit"]:
            q = entry["question"] if isinstance(entry, dict) else entry
            counts[q] = counts.get(q, 0) + 1
            
        return [q for q, count in counts.items() if count >= max_usage]

    def get_scripts_for_question(self, question):
        if "reddit" not in self.history:
            return []
        # Find all scripts associated with this question
        scripts = []
        for entry in self.history["reddit"]:
            if isinstance(entry, dict) and entry.get("question") == question:
                scripts.append(entry.get("script"))
        return scripts
