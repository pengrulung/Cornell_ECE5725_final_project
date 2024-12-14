# Authors:  Chenxin Xun (cx258)
#           Pengru Lung (pl649)
# Final project, Monday Section
# 2024-12-13

# Import necessary libraries
import pygame, pigame  # pygame for GUI handling, pigame could be a typo or placeholder
from pygame.locals import *
import os
import RPi._GPIO as GPIO  # GPIO library for Raspberry Pi for pin control
import sys
from time import sleep
import time
import threading  # For multithreading
import color_detect as cd  # Custom module for color detection
import math
import arm_control as ac  # Custom module for robotic arm control
import cv2  # OpenCV for computer vision

# GPIO pin configuration for Raspberry Pi
GPIO.setmode(GPIO.BCM)  # Use Broadcom GPIO numbering
GPIO.setup(19, GPIO.OUT)  # PWM pin for left motor
GPIO.setup(5, GPIO.OUT)  # Left motor control pin
GPIO.setup(6, GPIO.OUT)  # Left motor control pin
GPIO.setup(16, GPIO.OUT)  # PWM pin for right motor
GPIO.setup(20, GPIO.OUT)  # Right motor control pin
GPIO.setup(21, GPIO.OUT)  # Right motor control pin

# Motor PWM setup
freq = 480  # PWM frequency in Hz
duty_cycleA = 0  # Initial duty cycle for motor A
duty_cycleB = 0  # Initial duty cycle for motor B
pwm24 = GPIO.PWM(19, freq)
pwm16 = GPIO.PWM(16, freq)
pwm24.start(duty_cycleA)
pwm16.start(duty_cycleB)

# Initialize Pygame for GUI or event handling
pygame.init()

# Global flags and variables
flag = 0
pause = False
category = ''  # Detected object category
x = 0  # X-coordinate of detected object
y = 0  # Y-coordinate of detected object
approx = []  # Contour approximation of the object
checking = True
lock = threading.Lock()  # Lock for thread-safe access to shared variables

# Control left motor counterclockwise
def lccw(speed):
    if not pause:
        GPIO.output(5, GPIO.HIGH)
        GPIO.output(6, GPIO.LOW)
        pwm24.ChangeDutyCycle(speed)

# Control right motor clockwise
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

# Main motor control function
def run_motor():
    global category, x, y, approx
    desired_center = 320  # Desired X-coordinate of the object center
    proportional_gain = 0.6  # Proportional gain for PID control
    dead_zone = 10  # Error threshold to avoid small corrections
    prev_left_speed = 0  # Previous left motor speed
    prev_right_speed = 0  # Previous right motor speed
    max_delta = 5  # Maximum change in speed to smooth transitions

    time.sleep(2)  # Initial delay for system setup

    # Loop for initial detection and alignment
    while True:
        with lock:
            category = cd.color_name
            x = cd.cx
            y = cd.cy
            approx = cd.approx

        if category == cd.target:
            break

        lccw(100)  # Move left motor counterclockwise
        time.sleep(0.15)  # Brief movement duration
        lstop()  # Stop left motor
        time.sleep(0.2)  # Short pause

    # Loop for precise object tracking
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

        if category == cd.target:
            checking = False
            object_center = x
            error = object_center - desired_center

            if abs(error) < dead_zone:  # Check if within acceptable range
                lstop()
                rstop()
                continue

            correction = proportional_gain * error / desired_center * 50
            base_speed = 80  # Base speed for motors
            left_speed = base_speed + correction
            right_speed = base_speed - correction

            # Clamp speeds to valid range and smooth transitions
            left_speed = max(0, min(100, left_speed))
            right_speed = max(0, min(100, right_speed))
            left_speed = max(prev_left_speed - max_delta, min(left_speed, prev_left_speed + max_delta))
            right_speed = max(prev_right_speed - max_delta, min(right_speed, prev_right_speed + max_delta))
            prev_left_speed = left_speed
            prev_right_speed = right_speed

            lccw(left_speed)  # Adjust left motor speed
            rcw(right_speed)  # Adjust right motor speed
            time.sleep(0.05)  # Brief control interval
        else:
            lstop()
            rstop()
            time.sleep(0.1)  # Pause when target not detected

# Main program logic
try:
    cd.enable_threshold_filter = True  # Enable threshold-based filtering
    cd.target = "Blue"  # Set target color
    cd.target_pos = 320  # Set target position
    ac.go_back_default()  # Reset robotic arm to default position

    # Create threads for motor control and color detection
    motor_thread = threading.Thread(target=run_motor)
    detect_thread = threading.Thread(target=cd.color_detection)

    motor_thread.start()
    detect_thread.start()

    motor_thread.join()  # Wait for motor thread to complete
    detect_thread.join()  # Wait for detection thread to complete

    pwm24.stop()
    pwm16.stop()

    ac.default()  # Reset robotic arm to default state
    cap = cv2.VideoCapture(0)  # Open video capture
    color_name = ''
    while color_name != cd.target:
        ret, frame = cap.read()
        color_name, x, y, approx = cd.find_color_cubes(frame)
    cd.cd_stop()

    ac.release(x, y)  # Release the object at detected position

    ac.ac_quit()
    sys.exit()  # Exit the program
    cd.cd_stop()

except KeyboardInterrupt:
    print("Keyboard interrupt received. Cleaning up...")
finally:
    cd.cd_stop()  # Ensure color detection stops on exit
