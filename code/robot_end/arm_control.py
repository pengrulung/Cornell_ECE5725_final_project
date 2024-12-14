# Authors:  Chenxin Xun (cx258)
#           Pengru Lung (pl649)
# Final project, Monday Section
# 2024-12-13

import pigpio
import time
# Initialize pigpio and check connection
pi = pigpio.pi()
if not pi.connected:
    exit("Failed to connect to pigpio daemon") # Exit if unable to connect
# Define the minimum duty cycles for each servo motor
min_duties = [4.3, 5.8, 4, 5]
# Define specifications for each servo motor (pin numbers and pulse width ranges)
servo_specs = {
    'base': {
        'pin': 12,
        'min_pw': min_duties[0]*200,              # e.g. 4 * 200 = 800µs
        'max_pw': (min_duties[0]+8.5)*200         # e.g. (4+8.5)*200 = 2500µs
    },
    'shoulder': {
        'pin': 13,
        'min_pw': min_duties[1]*200,              # 5.5 * 200 = 1100µs
        'max_pw': (min_duties[1]+5.6)*200         # (5.5+5.6)*200 = 2220µs
    },
    'elbow': {
        'pin': 26,
        'min_pw': min_duties[2]*200,              # 4 * 200 = 800µs
        'max_pw': (min_duties[2]+3.4)*200         # (4+3.4)*200 = 1480µs
    },
    'wrist': {
        'pin': 4,
        'min_pw': min_duties[3]*200,              # 4.5 * 200 = 900µs
        'max_pw': (min_duties[3]+1.7)*200         # (4.5+1.7)*200 = 1240µs
    }
}
# Initialize all servo pins and set them to their default position (pulse width = 0)
for joint, specs in servo_specs.items():
    pi.set_mode(specs['pin'], pigpio.OUTPUT) # Set pin mode to OUTPUT
    pi.set_servo_pulsewidth(specs['pin'], 0)
    
# Function to generate a range of float values with a specified step
def frange(start, stop, step):
    r = start
    if step > 0:
        while r < stop:
            yield r
            r += step
    else:
        while r > stop:
            yield r
            r += step
            
# Function to move a servo motor to a target pulse width
def move_servo_slowly(pin, start_pw, end_pw, step=25, delay=0.1):
    # Determine the movement based on start and end pulse width
    if start_pw < end_pw:
        pw_range = frange(start_pw, end_pw, step)
    else:
        pw_range = frange(start_pw, end_pw, -step)
    # Gradually adjust the pulse width and delay to allow smooth movement
    for pw in pw_range:
        pi.set_servo_pulsewidth(pin, pw)
        time.sleep(delay)
    pi.set_servo_pulsewidth(pin, end_pw)
    
# Function to move servos to their default (home) positions
def default():
    # set default points for each servo
    sh_mid = ((servo_specs['shoulder']['max_pw'] + servo_specs['shoulder']['min_pw']) / 2) - (0.5*200)
    ba_mid = ((servo_specs['base']['max_pw'] + servo_specs['base']['min_pw']) / 2)
    el_mid = (servo_specs['elbow']['max_pw'])  
    # Move each servo to its default position
    pi.set_servo_pulsewidth(servo_specs['shoulder']['pin'], sh_mid)
    time.sleep(1)
    pi.set_servo_pulsewidth(servo_specs['shoulder']['pin'], 0)

    pi.set_servo_pulsewidth(servo_specs['base']['pin'], ba_mid)
    time.sleep(1)
    pi.set_servo_pulsewidth(servo_specs['base']['pin'], 0)

    pi.set_servo_pulsewidth(servo_specs['elbow']['pin'], el_mid)
    time.sleep(1)
    pi.set_servo_pulsewidth(servo_specs['elbow']['pin'], 0)
    
# Function to perform a "pick" action using the robotic arm
def pick(x, y):
    # Calculate initial midpoints for each joint
    wr_mid = (servo_specs['wrist']['max_pw'] + servo_specs['wrist']['min_pw']) / 2
    ba_mid = (servo_specs['base']['max_pw'] + servo_specs['base']['min_pw']) / 2
    sh_mid = (servo_specs['shoulder']['max_pw'] + servo_specs['shoulder']['min_pw']) / 2
    el_mid = (servo_specs['elbow']['max_pw'] + servo_specs['elbow']['min_pw']) / 2
    # Move wrist servo to target position
    wr_target = servo_specs['wrist']['max_pw']
    move_servo_slowly(servo_specs['wrist']['pin'], wr_mid, wr_target, step=10, delay=0.05)
    wr_mid = wr_target
    # Move base servo to calculated target position based on `x(find_color_cube)` input
    ba_target = ba_mid + (float(int((315 - x) / 25)) * 0.18 * 200)
    move_servo_slowly(servo_specs['base']['pin'], ba_mid, ba_target, step=10, delay=0.05)
    ba_mid = ba_target
    # Move elbow servo to its minimum position
    el_target = servo_specs['elbow']['min_pw']
    move_servo_slowly(servo_specs['elbow']['pin'], el_mid, el_target, step=10, delay=0.05)
    el_mid = el_target
    # Move shoulder servo to its caculated target
    sh_target = servo_specs['shoulder']['max_pw'] + (0.2 * 200) # 0.2 duty ~ 40µs step
    move_servo_slowly(servo_specs['shoulder']['pin'], sh_mid, sh_target, step=20, delay=0.02)
    sh_mid = sh_target
    # Move elbow servo to its caculated target
    el_target = servo_specs['elbow']['min_pw'] + float(int((y - 350) / 25)) * (0.2 * 200)
    move_servo_slowly(servo_specs['elbow']['pin'], el_mid, el_target, step=10, delay=0.05)
    el_mid = el_target
    # Move wrist servo to its caculated target
    wr_target = (servo_specs['wrist']['max_pw'] + servo_specs['wrist']['min_pw']) / 2
    move_servo_slowly(servo_specs['wrist']['pin'], wr_mid, wr_target, step=10, delay=0.05)
    wr_mid = wr_target
    # Move shoulder servo to its caculated target
    sh_target = ((servo_specs['shoulder']['max_pw'] + servo_specs['shoulder']['min_pw']) / 2) - (0.5*200)
    move_servo_slowly(servo_specs['shoulder']['pin'], sh_mid, sh_target, step=20, delay=0.02)
    sh_mid = sh_target
    # Move elbow servo to its caculated target
    el_target = servo_specs['elbow']['max_pw'] + (1*200)
    move_servo_slowly(servo_specs['elbow']['pin'], el_mid, el_target, step=10, delay=0.05)
    el_mid = el_target
    # Move base servo to its caculated target
    ba_target = (servo_specs['base']['max_pw'] + servo_specs['base']['min_pw']) / 2
    move_servo_slowly(servo_specs['base']['pin'], ba_mid, ba_target, step=10, delay=0.05)
    ba_mid = ba_target
    
# Function to perform returning item to a specified position)
def release(x, y):
    ba_mid = (servo_specs['base']['max_pw'] + servo_specs['base']['min_pw']) / 2
    sh_mid = (servo_specs['shoulder']['max_pw'] + servo_specs['shoulder']['min_pw']) / 2

    ba_target = ba_mid + float(int((300 - x) / 25)) * (0.2 * 200)
    move_servo_slowly(servo_specs['base']['pin'], ba_mid, ba_target, step=10, delay=0.05)
    ba_mid = ba_target

    sh_target = servo_specs['shoulder']['min_pw']
    move_servo_slowly(servo_specs['shoulder']['pin'], sh_mid, sh_target, step=10, delay=0.05)
    sh_mid = sh_target

    pi.set_servo_pulsewidth(servo_specs['wrist']['pin'], servo_specs['wrist']['max_pw'] + (0.2*200))
    time.sleep(1)
    pi.set_servo_pulsewidth(servo_specs['wrist']['pin'], 0)

 # Function to move servos to their default (home) positions when returing the object
def go_back_default():
    # Calculate the midpoint of the pulse width range for the shoulder servo
    sh_mid = (servo_specs['shoulder']['max_pw'] + servo_specs['shoulder']['min_pw']) / 2
    sh_target = sh_mid - (0.5*200)
    # Gradually move the shoulder servo to the calculated target position
    move_servo_slowly(servo_specs['shoulder']['pin'], sh_mid, sh_target, step=10, delay=0.05)
    
# Function to safely turn off all servo signals and clean up
def ac_quit():
    for joint, specs in servo_specs.items():
        pi.set_servo_pulsewidth(specs['pin'], 0)
    pi.stop()  # Stop pigpio daemon


