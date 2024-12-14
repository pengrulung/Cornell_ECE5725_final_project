# Authors:  Chenxin Xun (cx258)
#           Pengru Lung (pl649)
# Final project, Monday Section
# 2024-12-13

# Import necessary libraries
import pygame, pigame  # pygame for GUI handling, pigame possibly a typo (should be pygame)
from pygame.locals import *
import os
import RPi._GPIO as GPIO  # GPIO library for Raspberry Pi
import sys
from time import sleep
import time
import threading  # For multithreading support
import color_detect as cd  # Custom module for color detection
import math
import arm_control as ac  # Custom module for robotic arm control
import cv2  # OpenCV for computer vision tasks
import server_color as sc  # Custom module for server-based color communication

# GPIO pin setup for Raspberry Pi
GPIO.setmode(GPIO.BCM)  # Use Broadcom GPIO numbering
GPIO.setup(19, GPIO.OUT)  # Motor PWM pin
GPIO.setup(5, GPIO.OUT)  # Left motor control pin
GPIO.setup(6, GPIO.OUT)  # Left motor control pin
GPIO.setup(16, GPIO.OUT)  # Motor PWM pin
GPIO.setup(20, GPIO.OUT)  # Right motor control pin
GPIO.setup(21, GPIO.OUT)  # Right motor control pin

# Motor PWM configuration
freq = 480  # Frequency in Hz
duty_cycleA = 0  # Initial duty cycle for motor A
duty_cycleB = 0  # Initial duty cycle for motor B
pwm24 = GPIO.PWM(19, freq)
pwm16 = GPIO.PWM(16, freq)
pwm24.start(duty_cycleA)
pwm16.start(duty_cycleB)

# Initialize Pygame
pygame.init()

# Global flags and variables
flag = 0
pause = False
category = ''  # Detected color category
x = 0  # X-coordinate of detected object
y = 0  # Y-coordinate of detected object
approx = []  # Object contour approximation
checking = True
lock = threading.Lock()  # Thread synchronization lock

# Left motor counterclockwise rotation
def lccw(speed):
    if not pause:
        GPIO.output(5, GPIO.HIGH)
        GPIO.output(6, GPIO.LOW)
        pwm24.ChangeDutyCycle(speed)

# Right motor clockwise rotation
def rcw(speed):
    if not pause:
        GPIO.output(21, GPIO.HIGH)
        GPIO.output(20, GPIO.LOW)
        pwm16.ChangeDutyCycle(speed)

# Stop left motor
def lstop():
    pwm24.ChangeDutyCycle(0)

# Stop right motor
def rstop():
    pwm16.ChangeDutyCycle(0)

# Main motor control loop
def run_motor():
    global category, x, y, approx
    desired_center = 320  # Desired center X-coordinate
    proportional_gain = 0.6  # Proportional gain for PID control
    dead_zone = 10  # Dead zone to prevent jittering
    prev_left_speed = 0
    prev_right_speed = 0
    max_delta = 5  # Max change in speed to smooth transitions
    time.sleep(2)

    # Initial motor movement
    while True:
        lccw(100)
        time.sleep(0.15)
        with lock:
            category = cd.color_name
            x = cd.cx
            y = cd.cy
            approx = cd.approx

        if category == cd.target:
            break
        lstop()
        time.sleep(0.2)

    # Object tracking logic
    while True:
        with lock:
            if cd.stop:
                lstop()
                rstop()
                break
            category = cd.color_name
            x = cd.cx
            y = cd.cy
            approx = cd.approx
            step_stop = cd.step_stop

        if category == cd.target:
            checking = False
            object_center = x
            error = object_center - desired_center
            if abs(error) < dead_zone:
                lstop()
                rstop()
                continue

            correction = proportional_gain * error / desired_center * 50
            base_speed = 80  # Base speed for motors
            left_speed = base_speed + correction
            right_speed = base_speed - correction
            left_speed = max(0, min(100, left_speed))
            right_speed = max(0, min(100, right_speed))
            left_speed = max(prev_left_speed - max_delta, min(left_speed, prev_left_speed + max_delta))
            right_speed = max(prev_right_speed - max_delta, min(right_speed, prev_right_speed + max_delta))
            prev_left_speed = left_speed
            prev_right_speed = right_speed
            lccw(left_speed)
            rcw(right_speed)
            time.sleep(0.05)
        else:
            lstop()
            rstop()
            time.sleep(0.1)

# Main execution logic with threading for motor and detection tasks
try:
    sc.sending_color()  # Fetch target color from the server
    cd.target = sc.data
    if cd.target == "Green":
        cd.target_pos = 339 #calibriate positions
    if cd.target == "Yellow":
        cd.target_pos = 315 #calibriate positions
    if cd.target == "Blue":
        cd.target_pos = 329 #calibriate positions

    ac.default()  # Reset robotic arm to default position
    motor_thread = threading.Thread(target=run_motor)
    detect_thread = threading.Thread(target=cd.color_detection)

    motor_thread.start()
    detect_thread.start()

    motor_thread.join()
    detect_thread.join()

    pwm24.stop()
    pwm16.stop()
    ac.default()

    # Capture video and find the target object
    cap = cv2.VideoCapture(0)
    color_name = ''
    while color_name != cd.target:
        ret, frame = cap.read()
        color_name, x, y, approx = cd.find_color_cubes(frame)
    cd.cd_stop()
    ac.pick(x, y)

    ac.ac_quit()
    sys.exit()

except KeyboardInterrupt:
    print("Keyboard interrupt received. Cleaning up...")
finally:
    cd.cd_stop()  # Stop color detection

