from typing import List, Dict, Any, Optional, Callable
import heapq
import itertools

_task_counter = itertools.count()

class TaskQueue:
    """
    Priority queue: priority thấp => ưu tiên cao.
    Task:
      id, type, priority, data, difficulty
    """
    def __init__(self):
        self._heap: List[tuple] = []
        self._idx: Dict[int, Dict[str, Any]] = {}

    def push(self, task: Dict[str, Any]):
        if "priority" not in task:
            task["priority"] = 10
        if "difficulty" not in task:
            task["difficulty"] = 1.0
        tid = next(_task_counter)
        task["id"] = tid
        heapq.heappush(self._heap, (task["priority"], tid, task))
        self._idx[tid] = task

    def pop(self) -> Optional[Dict[str, Any]]:
        while self._heap:
            _, tid, task = heapq.heappop(self._heap)
            if tid in self._idx:
                self._idx.pop(tid, None)
                return task
        return None

    def remove_where(self, predicate: Callable[[Dict[str,Any]], bool]):
        new_heap = []
        for (p, tid, task) in self._heap:
            if predicate(task):
                self._idx.pop(tid, None)
            else:
                new_heap.append((p, tid, task))
        heapq.heapify(new_heap)
        self._heap = new_heap

    def to_list(self) -> List[Dict[str, Any]]:
        return [t for (_,_,t) in self._heap]

    def __len__(self):
        return len(self._idx)