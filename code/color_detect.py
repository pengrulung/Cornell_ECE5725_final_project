import cv2
import numpy as np
import threading
# from server_color import data

stop = False
cap = None # Video capture object
lock = threading.Lock()
color_name = '' # Detected color name
cx = 0 
cy = 0
approx = [] # Approximated contour points for the detected cube
target = 'Blue'
target_pos = 305 # Y-coordinate threshold to trigger a stop
step_stop = False

# New variables for threshold filtering
enable_threshold_filter = False
min_y_threshold = 130

# Define HSV color ranges for seven different colors
color_ranges = {
    "Green": ([36, 25, 25], [86, 255, 255]),
    "Blue": ([94, 80, 2], [126, 255, 255]),
    "Yellow": ([20, 80, 80], [30, 255, 255]),
    "Orange": ([3, 80, 100], [12, 255, 255]),
    "Purple": ([130, 50, 50], [160, 255, 255]),
    "Cyan": ([85, 100, 100], [95, 255, 255])
}

# Function to find and identify color cubes in a frame
def find_color_cubes(frame):
    # Convert the frame to HSV color space
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    # Loop through each defined color range
    for c_name, (lower, upper) in color_ranges.items():
        lower_bound = np.array(lower, dtype=np.uint8)
        upper_bound = np.array(upper, dtype=np.uint8)

        # Create a binary mask where color is detected
        mask = cv2.inRange(hsv_frame, lower_bound, upper_bound)
        mask = cv2.erode(mask, None, iterations=2) # Remove noise
        mask = cv2.dilate(mask, None, iterations=2) # Enhance detected regions

        # Find contours in the mask
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 300:  # Adjust area threshold as needed
                # Approximate the contour's shape
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx_pts = cv2.approxPolyDP(contour, epsilon, True)

                # Calculate the center of the contour
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx_local = int(M["m10"] / M["m00"])
                    cy_local = int(M["m01"] / M["m00"])
                else:
                    cx_local, cy_local = 0, 0

                # Apply the threshold filter if enabled
                if enable_threshold_filter and cy_local < min_y_threshold:
                    # Skip this contour since it's below the minimum y-threshold
                    continue

                # If the centroid is within the frame, print RGB values
                if 0 <= cx_local < frame.shape[1] and 0 <= cy_local < frame.shape[0]:
                    rgb_values = frame[cy_local, cx_local]
                    print(f"RGB values at ({cx_local}, {cy_local}): {rgb_values}")

                # Draw the contour and label on the frame
                cv2.drawContours(frame, [approx_pts], -1, (0, 255, 0), 2)
                cv2.putText(frame, f"{c_name} Cube", (cx_local, cy_local - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                cv2.circle(frame, (cx_local, cy_local), 5, (255, 0, 0), -1)
                print(f"Detected {c_name} cube at position: ({cx_local}, {cy_local})")

                return c_name, cx_local, cy_local, approx_pts # Return detected cube info

    return None, 0, 0, []  # Return default values if no color cube found

# Function for real-time color detection
def color_detection():
    global stop, cap, color_name, cx, cy, approx
    cap = cv2.VideoCapture(0)  # Open the default camera

    while True:
        # print("Target::::::::::::::::::", target)
        ret, frame = cap.read()
        if not ret:  # If frame capture fails, stop the program
            cd_stop()
            break
        # Detect color cubes in the current frame
        color_name1, cx1, cy1, approx1 = find_color_cubes(frame)
        # Process the frame to find color cubes
        with lock:
            color_name = color_name1
            cx = cx1
            cy = cy1
            approx = approx1
            # Stop if 'q' is pressed or the target conditions are met
            if cv2.waitKey(1) & 0xFF == ord('q'):
                stop = True
                cd_stop()
                break

            if cy > target_pos and target == color_name:
                stop = True
                cd_stop()
                break

            if cy > 260 and target == color_name:
                step_stop = True
                
# Function to release resources and close windows
def cd_stop():
    global cap
    cap.release()  # Release the video capture object
    cv2.destroyAllWindows() # Close all OpenCV windows
