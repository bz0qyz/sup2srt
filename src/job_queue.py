import queue

class jobQueue:
    def __init__(self):
        self.mkv = queue.Queue(maxsize=20)
        self.sup = queue.Queue(maxsize=20)
        self.sub = queue.Queue(maxsize=20)

class QueueItem:
    def __init__(self, input_file, output_path=None):
        self.input_file = input_file
        self.output_path = output_path


    def __str__(self):
        return self.input_file

        