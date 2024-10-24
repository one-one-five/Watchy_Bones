import cv2
import threading

class VideoStream:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.frame = None
        self.is_running = True
        self.lock = threading.Lock()

        # Запуск потока
        self.thread = threading.Thread(target=self.update, args=())
        self.thread.start()

    def update(self):
        while self.is_running:
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.frame = frame

    def get_frame(self):
        with self.lock:
            return self.frame

    def stop(self):
        self.is_running = False
        self.thread.join()
        self.cap.release()
