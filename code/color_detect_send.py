import cv2  # For video capture and image processing
import numpy as np
import threading
import socket
import time
import RPi._GPIO as GPIO # For Raspberry Pi GPIO control
import os
# Configure GPIO settings
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)

stop = False 
cap = None
lock = threading.Lock()
color_name = ''

# Server connection IP address and port number
HOST = '10.49.240.92'
PORT = 5000        

# Define HSV color ranges for different colors
color_ranges = {
    "Green": ([45, 35, 35], [75, 255, 255]),    
    "Blue": ([105, 125, 125], [135, 255, 255]),  
    "Yellow": ([20, 180, 180], [40, 255, 255]), 
}

# Function to identify the main color in a frame
def find_main_color(frame):
    # Convert the frame to HSV color space
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Initialize to store color count
    color_count = {color: 0 for color in color_ranges}
    # Loop through each color range and apply a mask
    for color_name, (lower, upper) in color_ranges.items():
        # Create lower and upper bound arrays
        lower_bound = np.array(lower, dtype=np.uint8)
        upper_bound = np.array(upper, dtype=np.uint8)

        # Create a binary mask where color is detected
        mask = cv2.inRange(hsv_frame, lower_bound, upper_bound)

        # Count the number of pixels matching the color
        color_count[color_name] = np.sum(mask)  # Sum the pixels that match the color

    # Determine the main color (the one with the highest count)
    main_color = max(color_count, key=color_count.get)
    # Ignore insignificant detections
    if color_count[main_color] < 300:
        return None
    print(f"The main color detected is: {main_color}")
    return main_color

# Function to send the detected color to a server
def send_color(message):
    # Create a client socket 
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            # Try to connect to the server
            client_socket.connect((HOST, PORT))
            print("Connected to the server successfully.")
            break  # Exit the loop once connected
        except socket.error as e:
            print(f"Connection failed: {e}. Retrying in 5 seconds...")
            time.sleep(5)  # Wait for 5 seconds before retrying

    # Send the encoded message to the server
    client_socket.send(message.encode('utf-8'))
    time.sleep(3) 

    # Close the connection
    client_socket.close()
    print("Connection closed.")

# Function to handle color detection    
def color_detection():
    global stop, cap, color_name
    cap = cv2.VideoCapture(0)  # Open the default camera
    
    while True:
        ret, frame = cap.read() # Capture a frame
        if not ret:
            cd_stop() # Stop if no frame is captured
            break

        # Process the frame to find color cubes
        with lock:
            color_name = find_main_color(frame) # Detect main color
        print("color_detection:::::::::::::::::::", color_name)  
        time.sleep(0.5)  
        # If a recognized color is detected, send it to the server
        if (color_name=="Green" or color_name=="Yellow" or color_name=="Blue"):
            message = f"{color_name}"
            cd_stop()
            send_color(message)

        # Exit the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop = True
            cd_stop()
            break
# Function to clean up video capture resources
def cd_stop():
    global cap
    cap.release() # Release the camera
    cv2.destroyAllWindows() # Close all OpenCV windows

try:
    while(True):
        flag17 = GPIO.input(17) # Monitor GPIO pin 17 for input
        while(flag17): 
            time.sleep(0.1)  
            flag17 = GPIO.input(17)
            if flag17==0: # Start color detection when flag17 is low
                color_detection()
except KeyboardInterrupt:
    print("Keyboard interrupt received. Cleaning up...")
finally:
    GPIO.cleanup() # Reset GPIO pins
    cd_stop()  # Release camera and clean up resources
