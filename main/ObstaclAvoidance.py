import RPi.GPIO as GPIO
from gpiozero import DistanceSensor
import cv2
import numpy as np
import mediapipe as mp
import time

# Pin Definitions
servo_pin = 13
in1_pin = 27  # Motor 1 IN1
in2_pin = 17  # Motor 1 IN2
ena_pin = 9  # Motor 1 Enable
in3_pin = 10  # Motor 2 IN3
in4_pin = 22  # Motor 2 IN4
enb_pin = 11  # Motor 2 Enable
hall_sensor_pin = 23  # Hall effect sensor pin
TRIG_PIN = 20  # GPIO pin connected to the Trigger pin of the sensor
ECHO_PIN = 21  # GPIO pin connected to the Echo pin of the sensor

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup([in1_pin, in2_pin, ena_pin, in3_pin, in4_pin, enb_pin, servo_pin, hall_sensor_pin], GPIO.OUT)
GPIO.setup(TRIG_PIN, GPIO.OUT)  # Set Trigger pin as output
GPIO.setup(ECHO_PIN, GPIO.IN)   # Set Echo pin as input
GPIO.setup(hall_sensor_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Set pull-up resistor

# Initialize PWM
pwm = GPIO.PWM(servo_pin, 50)  # 50Hz for servo
pwm.start(0)
pwm_ena = GPIO.PWM(ena_pin, 1000)
pwm_enb = GPIO.PWM(enb_pin, 1000)
pwm_ena.start(0)
pwm_enb.start(0)

# Initialize distance sensor
sensor = DistanceSensor(echo=ECHO_PIN, trigger=TRIG_PIN)

# Initialize MediaPipe Pose module
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Open a log file
def open_file():
  with open('motion_log1.txt', 'w') as file :
    file.write('N\n\n')

def write_data(x):
  with open('motion_log1.txt', 'a') as file :
    file.write(f'{x}\n')

# Global variable for current movement direction
current_direction = "None"
human_reached = False

def set_angle(angle):
    duty_cycle = 2 + (angle / 18)
    pwm.ChangeDutyCycle(duty_cycle)
    time.sleep(0.5)
    pwm.ChangeDutyCycle(0)

# Function to detect human pose and get bounding box center
def detect_pose(image):
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = pose.process(image_rgb)

    if results.pose_landmarks:
        h, w, _ = image.shape
        x_coords = [int(landmark.x * w) for landmark in results.pose_landmarks.landmark]
        y_coords = [int(landmark.y * h) for landmark in results.pose_landmarks.landmark]

        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)

        return (x_min, y_min, x_max, y_max), (x_min + x_max) // 2

    return None, None

# Function to rotate servo and detect human in the frame
def rotate_servo_and_detect(cap):
    frame_center_x = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) // 2

    for angle in range(10, 171, 5):
        print('Servo angle:', angle)
        set_angle(angle)
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture image.")
            break

        bbox, bbox_center_x = detect_pose(frame)
        if bbox:
            x_min, y_min, x_max, y_max = bbox
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
            area = x_max * y_max
            print('Area', area)
            if frame_center_x - 100 < bbox_center_x < frame_center_x + 100 and area > 5000:
                print(f"Human detected at center. Servo angle: {angle}")
                set_angle(90)  # Reset to forward position
                return angle, bbox_center_x

        # Display the frame with bounding box (if detected)
        cv2.imshow('Frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    set_angle(90)  # Reset servo to forward
    return None, None

# Motor control functions
def set_motor_speed(left_speed, right_speed):
    pwm_ena.ChangeDutyCycle(left_speed)
    pwm_enb.ChangeDutyCycle(right_speed)

def stop_motors():
    set_motor_speed(0, 0)

def set_motor_direction(left_forward, right_forward):
    GPIO.output(in1_pin, GPIO.HIGH if left_forward else GPIO.LOW)
    GPIO.output(in2_pin, GPIO.LOW if left_forward else GPIO.HIGH)
    GPIO.output(in3_pin, GPIO.HIGH if right_forward else GPIO.LOW)
    GPIO.output(in4_pin, GPIO.LOW if right_forward else GPIO.HIGH)

def move_forward(speed):
    global current_direction
    current_direction = "Forward"
    set_motor_direction(False, False)
    set_motor_speed(speed, speed)

def turn_left(speed):
    global current_direction
    current_direction = "Left"
    set_motor_direction(False, True)
    set_motor_speed(speed, speed)

def turn_right(speed):
    global current_direction
    current_direction = "Right"
    set_motor_direction(True, False)
    set_motor_speed(speed, speed)

def move_forward_for_time(speed, duration):
    move_forward(speed)
    monitor_hall_sensor(duration)
    stop_motors()

def move_right_for_time(speed, duration):
    turn_right(speed)
    monitor_hall_sensor(duration)
    stop_motors()

def move_left_for_time(speed, duration):
    turn_left(speed)
    monitor_hall_sensor(duration)
    stop_motors()

# Function to monitor the Hall effect sensor and log data
def monitor_hall_sensor(duration):
    start_time = time.time()
    counter = 0
    while time.time() - start_time < duration:
        if not GPIO.input(hall_sensor_pin):  # Hall effect sensor is active low
            counter += 1
            log_data = f"Direction: {current_direction}, Counter: {counter}\n"
            print(log_data)
            log_file.write(log_data)
        time.sleep(0.1)  # Avoid checking too frequently

# Main function that handles scanning, alignment, and human-following behavior
def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    try:
        while True:
            stop_motors()
            print("Scanning with servo...")

            detected_angle, _ = rotate_servo_and_detect(cap)

            if detected_angle is not None:
                print(f"Human detected at angle: {detected_angle}. Aligning.")
                if 0 < detected_angle < 70:
                    print("Turning left to align with human.")
                    move_left_for_time(60, 1)
                elif 110 < detected_angle < 180:
                    print("Turning right to align with human.")
                    move_right_for_time(60, 1)
                else:
                    move_forward_for_time(60, 1)

    finally:
        cap.release()
        log_file.close()
        GPIO.cleanup()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()