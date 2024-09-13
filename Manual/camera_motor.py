import RPi.GPIO as GPIO
import time
from flask import Flask, request, render_template_string, Response
import cv2
from picamera2 import Picamera2

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

# Initialize the camera
picam2 = Picamera2()
preview_config = picam2.create_preview_configuration(main={"format": "RGB888"})
picam2.configure(preview_config)
picam2.start()

@app.route('/')
def index():
    """Render the control interface and video feed."""
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Motor Control with Camera</title>
            <style>
                body { font-family: Arial, sans-serif; }
                .container { max-width: 600px; margin: auto; text-align: center; }
                .button { padding: 10px 20px; margin: 5px; font-size: 16px; }
                .slider { width: 300px; }
                video { max-width: 100%; margin-top: 20px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Motor Control with Camera</h1>
                <form id="control-form" action="/control" method="post">
                    <button type="submit" name="direction" value="forward" class="button">Forward</button>
                    <button type="submit" name="direction" value="backward" class="button">Backward</button>
                    <button type="submit" name="direction" value="left" class="button">Right</button>
                    <button type="submit" name="direction" value="right" class="button">Left</button>
                    <button type="submit" name="direction" value="stop" class="button">Stop</button>
                </form>
                <label for="speed">Speed:</label>
                <input type="range" id="speed" name="speed" min="0" max="100" value="100" class="slider" oninput="updateSpeed(this.value)">
                <h2>Live Camera Feed</h2>
                <img src="{{ url_for('video_feed') }}" alt="Camera Feed">
            </div>
            <script>
                function updateSpeed(value) {
                    fetch('/speed', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                        body: 'speed=' + value
                    });
                }
            </script>
        </body>
        </html>
    ''')

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
    set_motor_direction(True, True)  # Apply the new speed to both motors

    return ('', 204)  # Return no content response

def generate_frames():
    """Video streaming generator function."""
    while True:
        frame = picam2.capture_array()
        if frame is not None:
            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    """Video streaming route."""
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    finally:
        set_motor_direction(False, False)  # Ensure motors stop
        GPIO.cleanup()
        print("Cleanup Done")
