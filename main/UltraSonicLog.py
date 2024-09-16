import RPi.GPIO as GPIO
import cv2
import mediapipe as mp
import time
from gpiozero import DistanceSensor



# Pin Definitions
servo_pin = 13
in1_pin = 27  # Motor 1 IN1
in2_pin = 17  # Motor 1 IN2
ena_pin = 9  # Motor 1 Enable
in3_pin = 10  # Motor 2 IN3
in4_pin = 22  # Motor 2 IN4
enb_pin = 11  # Motor 2 Enable
hall_sensor_pin = 23  # Hall effect sensor pin
TRIG_PIN = 20
ECHO_PIN = 21

sensor = DistanceSensor(echo=ECHO_PIN, trigger=TRIG_PIN)

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup([in1_pin, in2_pin, ena_pin, in3_pin, in4_pin, enb_pin, servo_pin, hall_sensor_pin], GPIO.OUT)
GPIO.setup(hall_sensor_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Set pull-up resistor

# Initialize PWM
pwm = GPIO.PWM(servo_pin, 50)  # 50Hz for servo
pwm.start(0)
pwm_ena = GPIO.PWM(ena_pin, 1000)
pwm_enb = GPIO.PWM(enb_pin, 1000)
pwm_ena.start(0)
pwm_enb.start(0)

# Initialize MediaPipe Pose module
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)


# Global variable for current movement direction
current_direction = "None"
human_detected=False
file_path='/home/sujith/LF3.txt'


def start_file():
    with open(file_path,'w')as file:
        file.write('N\n\n')


start_file()


def write_data(x):
    with open(file_path,'a') as file:
        file.write(x)


def get_distance():
    distance_cm = sensor.distance * 100
    return round(distance_cm,2)


# Function to set the angle of the servo motor
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
            # print('Area ',x_max*y_max)
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
            area = x_max * y_max
            print('Area', area)
            if frame_center_x - 100 < bbox_center_x < frame_center_x + 100 and area > 5000:
                print(f"Human detected at center. Servo angle: {angle}")
                set_angle(90)  # Reset to forward position
                return angle, bbox_center_x

        # Display the frame with bounding box (if detected)
        cv2.imshow('Frame', frame)
        # time.sleep(4)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    set_angle(90)  # Reset servo to forward
    return None, None


# Motor control functions
def set_motor_speed(left_speed, right_speed):
    pwm_ena.ChangeDutyCycle(left_speed)
    pwm_enb.ChangeDutyCycle(right_speed)


def stop_motors():
    global current_direction
    current_direction='S'
    set_motor_speed(0, 0)


def set_motor_direction(left_forward, right_forward):
    GPIO.output(in1_pin, GPIO.HIGH if left_forward else GPIO.LOW)
    GPIO.output(in2_pin, GPIO.LOW if left_forward else GPIO.HIGH)
    GPIO.output(in3_pin, GPIO.HIGH if right_forward else GPIO.LOW)
    GPIO.output(in4_pin, GPIO.LOW if right_forward else GPIO.HIGH)


def move_forward(speed):
    global current_direction
    current_direction = "F"
    set_motor_direction(False, False)
    set_motor_speed(speed, speed)


def turn_left(speed):
    global current_direction
    current_direction = "L"
    set_motor_direction(False, True)
    set_motor_speed(speed, speed)


def turn_right(speed):
    global current_direction
    current_direction = "R"
    set_motor_direction(True, False)
    set_motor_speed(speed, speed)


def move_forward_for_time(speed, duration):
    move_forward(speed)
    time.sleep(duration)
    stop_motors()


def move_forward_for_steps(speed,steps):
    move_forward(speed)
    step=0
    while step<=steps:
        if GPIO.input(hall_sensor_pin)==GPIO.LOW:
            step+=1
    stop_motors()


def move_right_for_time(speed, duration):
    turn_right(speed)
    time.sleep(duration)
    stop_motors()


def move_left_for_time(speed, duration):
    turn_left(speed)
    time.sleep(duration)
    stop_motors()


# Function to monitor the Hall effect sensor and log data
'''def monitor_hall_sensor(duration):
    start_time = time.time()
    counter = 0
    while time.time() - start_time < duration:
        if not GPIO.input(hall_sensor_pin):  # Hall effect sensor is active low
            counter += 1
            log_data = f"Direction: {current_direction}, Counter: {counter}\n"
            print(log_data)
            write_data(f'F,{counter}')
        time.sleep(0.1)  # Avoid checking too frequently'''


# Function to follow human by adjusting motor direction based on bounding box center
def human_follow(cap):
    global human_detected
    counter = 0
    moves = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture image.")
            break

        bbox, bbox_center_x = detect_pose(frame)
        if bbox:
            frame_width = frame.shape[1]
            frame_center_x = frame_width // 2

            if bbox_center_x < frame_center_x - 80:
                print("Human is to the left. Turning left.")
                turn_left(40)
                # monitor_hall_sensor(1)  # Monitor the sensor during left turn
                moves += 1
            elif bbox_center_x > frame_center_x + 80:
                print("Human is to the right. Turning right.")
                turn_right(40)
                moves += 1
            else:
                print("Human is centered. Moving forward.")
                move_forward(60)
                moves += 1

            # Draw bounding box and display frame
            x_min, y_min, x_max, y_max = bbox
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
        else:
            stop_motors()
            counter+=1
            print("No human detected. Stopping.")
            if moves>3:
                if get_distance()<=35:
                    human_detected=True
                break  # Exit loop if no human detected for an extended time

            if counter > 10:
                break
        # Display the frame
        cv2.imshow('Frame', frame)
        write_data(f'{current_direction},0.2')
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


# Main function that handles scanning, alignment, and human-following behavior
def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    try:
        while True and not human_detected:
            stop_motors()
            print("Scanning with servo...")

            detected_angle, _ = rotate_servo_and_detect(cap)

            if detected_angle is not None:
                print(f"Human detected at angle: {detected_angle}. Aligning.")
                if 0 < detected_angle < 70:
                    print("Turning left to align with human.")
                    move_left_for_time(60, 1)
                    write_data('L,1')
                elif 110 < detected_angle < 180:
                    print("Turning right to align with human.")
                    move_right_for_time(60, 1)
                    write_data('R,1')
                else:
                    move_forward_for_steps(60, 2)
                    print('Moving forward to align with human')
                    write_data('F,2')

                print("Following human.")
                human_follow(cap)
            else:
                print("No human detected. Moving forward.")
                move_forward_for_steps(60, 3)
                write_data('F,3')

    finally:
        cap.release()
        cv2.destroyAllWindows()
        stop_motors()
        pwm_ena.stop()
        pwm_enb.stop()
        pwm.stop()
        GPIO.cleanup()


if __name__ == "__main__":
    main()
