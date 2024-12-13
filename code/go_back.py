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


GPIO.setmode(GPIO.BCM)
GPIO.setup(19, GPIO.OUT)
GPIO.setup(5, GPIO.OUT)
GPIO.setup(6, GPIO.OUT)
GPIO.setup(16, GPIO.OUT)
GPIO.setup(20, GPIO.OUT)
GPIO.setup(21, GPIO.OUT)

freq = 480
duty_cycleA = 0
duty_cycleB = 0
pwm24 = GPIO.PWM(19, freq)
pwm16 = GPIO.PWM(16, freq)
pwm24.start(duty_cycleA)
pwm16.start(duty_cycleB)
     
pygame.init()


flag = 0
pause = False
category = ''
x = 0
y = 0
approx = []
checking = True

lock = threading.Lock()

def lccw(speed):
    if not pause:
        GPIO.output(5, GPIO.HIGH)
        GPIO.output(6, GPIO.LOW)
        pwm24.ChangeDutyCycle(speed)

def rcw(speed):
    if not pause:
        GPIO.output(21, GPIO.HIGH)
        GPIO.output(20, GPIO.LOW)
        pwm16.ChangeDutyCycle(speed)

# def rccw(speed):
#     if not pause:
#         GPIO.output(20, GPIO.HIGH)
#         GPIO.output(21, GPIO.LOW)
#         pwm16.ChangeDutyCycle(speed)

def lstop():
    pwm24.ChangeDutyCycle(0)

def rstop():
    pwm16.ChangeDutyCycle(0)

def run_motor():
    global category, x, y, approx
    desired_center = 320
    proportional_gain = 0.6
    dead_zone = 10
    prev_left_speed = 0
    prev_right_speed = 0
    max_delta = 5 

    time.sleep(2)



    while True:
        with lock:
            category = cd.color_name
            x = cd.cx
            y = cd.cy
            approx = cd.approx

        if category == cd.target:
            break

        lccw(100)
        time.sleep(0.15)
        lstop()
        time.sleep(0.2)
        # print("detection00000000000000000000000000: ", category)


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


        if  category == cd.target:
            checking = False

            object_center = x
            error = object_center - desired_center

            if abs(error) < dead_zone:
                lstop()
                rstop()
                continue

            correction = proportional_gain * error / desired_center * 50

            base_speed = 80  
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


try:
    cd.enable_threshold_filter = True
    cd.target = "Blue"
    cd.target_pos = 320
    ac.go_back_default()
    motor_thread = threading.Thread(target=run_motor)
    detect_thread = threading.Thread(target=cd.color_detection)
    
    motor_thread.start()
    detect_thread.start()

    motor_thread.join()  
    detect_thread.join() 

    pwm24.stop()
    pwm16.stop()

    ac.default()
    cap = cv2.VideoCapture(0)
    color_name = ''
    while color_name != cd.target:
        ret, frame = cap.read()
        color_name, x, y, approx = cd.find_color_cubes(frame)
    cd.cd_stop()

    ac.release(x,y)

    ac.ac_quit()
    sys.exit()
    cd.cd_stop()

except KeyboardInterrupt:
    print("Keyboard interrupt received. Cleaning up...")
finally:
    cd.cd_stop()
