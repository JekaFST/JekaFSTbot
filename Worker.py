from queue import PriorityQueue
from TaskMathodMap import TaskMethodMap


class Queue:
    def __init__(self):
        self.queue = PriorityQueue()

    def worker(self, bot):
        while True:
            if not self.queue.empty():
                TaskMethodMap.run_task(self.queue.get()[1], bot)
                self.queue.task_done()


queue = Queue()
