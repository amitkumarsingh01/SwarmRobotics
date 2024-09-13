import RPi.GPIO as GPIO
import time
import cv2
from flask import Flask, request, render_template, Response

# Pin Definitions
in1_pin = 27  # Motor 1 IN1
in2_pin = 17  # Motor 1 IN2
ena_pin = 9   # Motor 1 Enable
in3_pin = 10  # Motor 2 IN3
in4_pin = 22  # Motor 2 IN4
enb_pin = 11  # Motor 2 Enable

# Setup GPIO
GPIO.setmode(GPIO.BCM)  # Use Broadcom pin numbering
GPIO.setup(in1_pin, GPIO.OUT)
GPIO.setup(in2_pin, GPIO.OUT)
GPIO.setup(ena_pin, GPIO.OUT)
GPIO.setup(in3_pin, GPIO.OUT)
GPIO.setup(in4_pin, GPIO.OUT)
GPIO.setup(enb_pin, GPIO.OUT)

# Initialize PWM on Enable pins
pwm_ena = GPIO.PWM(ena_pin, 1000)  # Set frequency to 1 kHz
pwm_enb = GPIO.PWM(enb_pin, 1000)  # Set frequency to 1 kHz
pwm_ena.start(0)  # Start PWM with 0% duty cycle
pwm_enb.start(0)  # Start PWM with 0% duty cycle

app = Flask(__name__)

# Initialize speed
current_speed = 0

def set_motor_direction(left_motor_forward, right_motor_forward, speed):
    """Control both motors based on direction and speed."""
    GPIO.output(in1_pin, GPIO.HIGH if left_motor_forward else GPIO.LOW)
    GPIO.output(in2_pin, GPIO.LOW if left_motor_forward else GPIO.HIGH)
    GPIO.output(in3_pin, GPIO.HIGH if right_motor_forward else GPIO.LOW)
    GPIO.output(in4_pin, GPIO.LOW if right_motor_forward else GPIO.HIGH)
    pwm_ena.ChangeDutyCycle(speed)
    pwm_enb.ChangeDutyCycle(speed)

@app.route('/')
def index():
    """Render the control interface."""
    return render_template('index.html')

@app.route('/control', methods=['POST'])
def control():
    direction = request.form.get('direction')

    if direction == 'forward':
        set_motor_direction(True, True, current_speed)
    elif direction == 'backward':
        set_motor_direction(False, False, current_speed)
    elif direction == 'left':
        set_motor_direction(False, True, current_speed)
    elif direction == 'right':
        set_motor_direction(True, False, current_speed)
    elif direction == 'stop':
        set_motor_direction(False, False, 0)
    else:
        set_motor_direction(False, False, 0)

    return index()

@app.route('/speed', methods=['POST'])
def adjust_speed():
    global current_speed
    speed = request.form.get('speed', 0)  # Get the speed from the slider
    current_speed = int(speed)
    set_motor_direction(True, True, current_speed)  # Apply the new speed to both motors

    return ('', 204)  # Return no content response

def generate_frames():
    camera = cv2.VideoCapture(0)  # Open camera
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    """Return the video feed from the camera."""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    finally:
        set_motor_direction(False, False)  
        GPIO.cleanup()
        print("Cleanup Done")
