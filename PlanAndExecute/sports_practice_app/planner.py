from typing import Dict, List, Any

class TaskPlanner:
    def __init__(self):
        pass

    def create_plan(self, query: str, user_location: str) -> List[Dict[str, Any]]:
        """Create a task execution plan based on the user query."""
        tasks = []

        # Check for keywords in the query to determine tasks
        if query.lower() in ["basketball", "football", "tennis", "cricket"]:
            tasks.append({
                "task_name": "YouTube",
                "should_execute": True,
                "search_query": f"{query} highlights"
            })
            tasks.append({
                "task_name": "Maps",
                "should_execute": True,
                "search_query": f"{query} facilities near {user_location}"
            })

        return tasks