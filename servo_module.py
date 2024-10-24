from adafruit_servokit import ServoKit
import time

class ServoMotor:
    def __init__(self):
        self.kit = ServoKit(channels=16)
        self.kit.servo[0].set_pulse_width_range(2600, 500)  # Установка диапазонов сервопривода
        self.head_angle_ave = 90.0  # Начальный угол головы
        self.head_angle_alpha = 0.1  # Коэффициент сглаживания

    def remap(self, x, in_min, in_max, out_min, out_max):
        x_diff = x - in_min
        out_range = out_max - out_min
        in_range = in_max - in_min
        temp_out = x_diff * out_range / in_range + out_min
        if temp_out > out_max:
            return out_max
        elif temp_out < out_min:
            return out_min
        else:
            return temp_out

    def move_to_angle(self, x, in_min=30.0, in_max=160.0, out_min=160.0, out_max=30.0):
        head_angle = self.remap(float(x), in_min, in_max, out_min, out_max)
        self.head_angle_ave = head_angle * self.head_angle_alpha + self.head_angle_ave * (1.0 - self.head_angle_alpha)
        self.kit.servo[0].angle = int(self.head_angle_ave)

        # Добавляем небольшую задержку для плавности движения
        time.sleep(0.05)
