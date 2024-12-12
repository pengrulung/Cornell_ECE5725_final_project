#!/usr/bin/env bash
# Start the pigpio daemon, which is required for GPIO control
sudo pigpiod
# Infinite loop to continuously execute the Python scripts
while true
do
    # Run the motor control script
    sudo python3 motor_control.py
    # Run the go-back script
    sudo python3 go_back.py
    # Optionally, Pause for 1 second before the next iteration
done
