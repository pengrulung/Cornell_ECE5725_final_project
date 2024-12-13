# Import libraries
import pygame,pigame
from pygame.locals import *
import os
import RPi._GPIO as GPIO
import sys
from time import sleep
import time
import sys
import threading
import color_detect as cd
import math
import arm_control as ac
import cv2

# GPIO setup
GPIO.setmode(GPIO.BCM) 
GPIO.setup(19, GPIO.OUT)  # Pin for motor A PWM
GPIO.setup(5, GPIO.OUT) # Pin for motor A direction
GPIO.setup(6, GPIO.OUT) # Pin for motor A direction
GPIO.setup(16, GPIO.OUT) # Pin for motor B PWM
GPIO.setup(20, GPIO.OUT) # Pin for motor B direction
GPIO.setup(21, GPIO.OUT) # Pin for motor B direction

# Initialize PWM parameters
freq = 480
duty_cycleA = 0 # Initial duty cycle for motor A
duty_cycleB = 0 # Initial duty cycle for motor B
pwm24 = GPIO.PWM(19, freq) # PWM control for motor A
pwm16 = GPIO.PWM(16, freq) # PWM control for motor B
pwm24.start(duty_cycleA)
pwm16.start(duty_cycleB)

# Initialize pygame 
pygame.init()

flag = 0
pause = False
category = ''
x = 0
y = 0
approx = []
checking = True

# Threading lock to manage shared resources
lock = threading.Lock()

# Function to rotate left motor counter-clockwise at a given speed
def lccw(speed):
    if not pause:
        GPIO.output(5, GPIO.HIGH)
        GPIO.output(6, GPIO.LOW)
        pwm24.ChangeDutyCycle(speed)

# Function to rotate right motor clockwise at a given speed
def rcw(speed):
    if not pause:
        GPIO.output(21, GPIO.HIGH)
        GPIO.output(20, GPIO.LOW)
        pwm16.ChangeDutyCycle(speed)

# Function to stop the left motor
def lstop():
    pwm24.ChangeDutyCycle(0)

# Function to stop the right motor
def rstop():
    pwm16.ChangeDutyCycle(0)

# Main function to run the motor based on color detection
def run_motor():
    global category, x, y, approx
    desired_center = 320 # Target x-coordinate for object centering
    proportional_gain = 0.6
    dead_zone = 10
    prev_left_speed = 0
    prev_right_speed = 0
    max_delta = 5 

    time.sleep(2)
    # Initial detection loop (keep rotating left motor to find the target)
    while True:
        with lock:
            category = cd.color_name # Get current detected color
            x = cd.cx # Get x-coordinate of detected object
            y = cd.cy # Get y-coordinate of detected object
            approx = cd.approx
        # Stop initial detection if target color is found
        if category == cd.target:
            break

        lccw(100) # Rotate left motor
        time.sleep(0.15)
        lstop()  # Stop left motor
        time.sleep(0.2)
        # print("detection00000000000000000000000000: ", category)

    # Main control loop
    while True:
        with lock:
            # if color detection stop, stop the left motor and right motor
            if cd.stop:
                lstop()
                rstop()
                break
            category = cd.color_name # Get current detected color
            x = cd.cx # Get x-coordinate of detected object
            y = cd.cy # Get y-coordinate of detected object
            approx = cd.approx

        if  category == cd.target:
            checking = False
            # Calculate error and correction for centering
            object_center = x
            error = object_center - desired_center
            # move to the right return place, stop both motor
            if abs(error) < dead_zone:
                lstop()
                rstop()
                continue
            
            # Adjust to the right return place
            correction = proportional_gain * error / desired_center * 50
            base_speed = 80  # Base motor speed
            left_speed = base_speed + correction
            right_speed = base_speed - correction
            # Clamp speeds to allowable range
            left_speed = max(0, min(100, left_speed))
            right_speed = max(0, min(100, right_speed))
            # Smooth speed transitions
            left_speed = max(prev_left_speed - max_delta, min(left_speed, prev_left_speed + max_delta))
            right_speed = max(prev_right_speed - max_delta, min(right_speed, prev_right_speed + max_delta))
            prev_left_speed = left_speed
            prev_right_speed = right_speed
            # Set motor speeds
            lccw(left_speed)
            rcw(right_speed)

            time.sleep(0.05)
        else:
            lstop()
            rstop()
            time.sleep(0.1)

# Main program execution
try:
    cd.enable_threshold_filter = True # Enable threshold filtering for color detection
    cd.target = "Blue" # Set target color
    cd.target_pos = 320  # Set target position
    ac.go_back_default() # Move arm to default position
    
    # Create threads for motor and color detection
    motor_thread = threading.Thread(target=run_motor)
    detect_thread = threading.Thread(target=cd.color_detection)
    
    # Start motor and color detection thread
    motor_thread.start()
    detect_thread.start()

    motor_thread.join()  
    detect_thread.join() 

    # Stop PWM signals
    pwm24.stop()
    pwm16.stop()

    ac.default() # Reset arm to default state
    cap = cv2.VideoCapture(0) # Start video capture
    color_name = ''
    while color_name != cd.target:
        ret, frame = cap.read()
        color_name, x, y, approx = cd.find_color_cubes(frame)
    cd.cd_stop() # Stop color detection

    ac.release(x,y) # Release object using robotic arm
    ac.ac_quit() # Quit arm control
    sys.exit() 

except KeyboardInterrupt:
    print("Keyboard interrupt received. Cleaning up...")
finally:
    cd.cd_stop() # Color detection stops
