import cv2
from picamera2 import Picamera2

def main():
    # Initialize Picamera2
    picam2 = Picamera2()
    preview_config = picam2.create_preview_configuration(main={"format": "RGB888"})
    picam2.configure(preview_config)
    picam2.start()

    # Capture video frames in a loop
    try:
        while True:
            # Get a frame from the camera
            frame = picam2.capture_array()

            if frame is not None:
                # Display the frame using OpenCV
                cv2.imshow('Video', frame)

            # Exit the loop when 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    except IndexError as e:
        print(f"Index error: {e}")
    finally:
        # Release resources
        picam2.stop()
        cv2.destroyAllWindows()


main()