from flask import Flask, render_template, Response, request
from servo_module import ServoMotor
from video_stream import VideoStream
import cv2
import threading
import time
import os

# Инициализация Flask-приложения
app = Flask(__name__)

# Инициализация видеопотока и сервопривода
video_stream = VideoStream()
servo = ServoMotor()

# Порог для движения сервопривода (пиксели)
MOVEMENT_THRESHOLD = 10
MAX_STEP = 50

# Установка крайних углов сервопривода
LEFT_LIMIT = 0
RIGHT_LIMIT = 180

# Маршрут для главной страницы
@app.route('/')
def index():
    return render_template('index.html')

# Функция генерации кадров для веб-сервиса
def gen():
    while True:
        frame = video_stream.get_frame()
        if frame is None:
            continue
        ret, jpeg = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')

# Маршрут для видеопотока
@app.route('/video_feed')
def video_feed():
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Маршрут для завершения работы сервера через браузер
@app.route('/shutdown')
def shutdown():
    shutdown_server()
    return "Сервер завершает работу..."

# Функция завершения работы сервера
def shutdown_server():
    # Завершаем все потоки и работу системы
    print("Завершаем сервер через браузер...")
    video_stream.stop()  # Останавливаем видеопоток корректно
    os._exit(0)  # Завершаем процесс Flask и Python

# Функция для отслеживания лиц и управления сервоприводом
def track_face():
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    last_face_center_x = None
    last_direction = None

    try:
        while True:
            frame = video_stream.get_frame()
            if frame is None:
                continue

            resized_frame = cv2.resize(frame, (320, 240))
            gray = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=5, minSize=(30, 30))

            if len(faces) > 0:
                x, y, w, h = faces[0]
                face_center_x = x + w / 2

                if last_face_center_x is None:
                    last_face_center_x = face_center_x

                if abs(face_center_x - last_face_center_x) > MOVEMENT_THRESHOLD:
                    if abs(face_center_x - last_face_center_x) > MAX_STEP:
                        face_center_x = last_face_center_x + (MAX_STEP if face_center_x > last_face_center_x else -MAX_STEP)

                    if face_center_x > last_face_center_x:
                        direction = 'right'
                    elif face_center_x < last_face_center_x:
                        direction = 'left'
                    else:
                        direction = last_direction

                    target_angle = servo.remap(face_center_x, 30.0, 160.0, 160.0, 30.0)
                    target_angle = max(LEFT_LIMIT, min(target_angle, RIGHT_LIMIT))

                    if direction != last_direction:
                        servo.head_angle_alpha = 0.01
                        time.sleep(0.2)
                    else:
                        servo.head_angle_alpha = 0.05

                    servo.move_to_angle(face_center_x)
                    last_face_center_x = face_center_x
                    last_direction = direction

                time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nСервер завершает работу...")

# Запуск Flask-сервера в отдельном потоке
def start_flask():
    app.run(host='0.0.0.0', port=5000)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.daemon = True
    flask_thread.start()

    print("Откройте веб-браузер и перейдите на страницу '/shutdown' для завершения работы сервера.")
    
    try:
        track_face()
    except KeyboardInterrupt:
        print("\nЗавершение всех процессов...")
        video_stream.stop()  # Останавливаем видеопоток корректно
        flask_thread.join()  # Ждём завершения веб-сервера
        print("Сервер успешно остановлен.")
