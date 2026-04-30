import cv2
import numpy as np
import os
import pickle
import math

# Live undistortion parameters
CAMERA_ID = 2  # Camera ID (usually 0 for built-in webcam)
CALIBRATION_FILE = 'output/calibration_data.pkl'  # Path to calibration data

# Resolution of camera
IMAGE_RES = (1920,1080) # (1280,720)
# Scale of window
SCALE = 1

# Amount to crop in where 0 is just the center of the image with no edges and 1 contains the full undistorted image
# You will probably have to change this to fit the area of interest from your camera
CROP_FACTOR = 1

# Values from 0 to 1 of how much to crop in individual sides
# You may have to change these if your camera winds up asymmetric after distortion
CROP_LEFT = 0.0
CROP_RIGHT = 0.0
CROP_TOP = 0.0
CROP_BOTTOM = 0.0


def live_undistortion():
    """
    Demonstrate live camera undistortion using calibration results.
    """
    # Check if calibration file exists
    if not os.path.exists(CALIBRATION_FILE):
        print(f"Error: Calibration file not found at {CALIBRATION_FILE}")
        print("Please run camera_calibration.py first to generate calibration data.")
        return
    
    # Load calibration data
    with open(CALIBRATION_FILE, 'rb') as f:
        calibration_data = pickle.load(f)
    
    mtx = calibration_data['camera_matrix']
    dist = calibration_data['distortion_coefficients']
    
    print("Loaded camera calibration data:")
    print(f"Camera Matrix:\n{mtx}")
    print(f"Distortion Coefficients: {dist.ravel()}")
    
    # Open camera
    cap = cv2.VideoCapture(CAMERA_ID)
    
    # Set width and height
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, IMAGE_RES[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, IMAGE_RES[1])
    
    if not cap.isOpened():
        print(f"Error: Could not open camera {CAMERA_ID}")
        return
    
    # Get camera resolution
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Camera resolution: {width}x{height}")
    
    # Calculate optimal camera matrix
    newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (width, height), CROP_FACTOR, (width * 4, height * 4), True)
    
    def points_from_angles(angles):
        """
        Convert angles to points on the image plane.
        angles[n][2]: list of horizontal and vertical angles pairs in degrees
        """
        # Convert angles to radians
        angles_rad = np.radians(angles)
        
        # Calculate 3D points on the unit sphere where the rotations are away from [0,0,1]
        object_points_array = []
        for angle_pair in angles_rad:
            h_angle, v_angle = angle_pair
            # x = 0
            # y = 0
            # z = 1
            # # Apply rotation around y-axis (horizontal angle)
            # y2 = y * math.cos(h_angle) + z * math.sin(h_angle)
            # z2 = -y * math.sin(h_angle) + z * math.cos(h_angle)
            # y = y2
            # z = z2
            # # Apply rotation around x-axis (vertical angle)
            # x2 = x * math.cos(v_angle) + z * math.sin(v_angle)
            # z2 = -x * math.sin(v_angle) + z * math.cos(v_angle)
            # x = x2
            # z = z2
            x = math.sin(v_angle)
            y = math.sin(h_angle)
            z = math.cos(h_angle) + math.cos(v_angle)
            z /= 2
            object_points_array.append([x, y, z])
        
        object_points = np.array(object_points_array, dtype=np.float32)
        # print("object_points", object_points)
        # No translation or rotation
        rvec = np.array([0, 0, 0], dtype=np.float32)
        tvec = np.array([[0.0], [0.0], [0.0]], dtype=np.float32)
        # Project the 3D points to the 2D image plane
        zero_dist_coeffs = np.zeros((4, 1)) 
        image_points, jacobian = cv2.projectPoints(object_points, rvec, tvec, newcameramtx, zero_dist_coeffs)
        # undistorted_points = cv2.undistortPoints(image_points, mtx, dist, None, newcameramtx)
        return image_points.reshape(-1, 2)
        # return np.array(image_points.reshape(-1, 2), dtype=np.int32)
        # return undistorted_points.reshape(-1, 2)
    
    print("points_from_angles", points_from_angles([[0, 0], [90, 0], [0, 90]]))
    print("points_from_angles", points_from_angles([[30, 30], [30, -30], [-30,30], [-30,-30]]))
    print("center of roi rect", (roi[0] + roi[2]//2, roi[1] + roi[3]//2))
    # exit()
    
    # Create undistortion maps
    mapx, mapy = cv2.initUndistortRectifyMap(mtx, dist, None, newcameramtx, (width * 4, height * 4), 5)
    
    print("Press 'q' to quit, 'd' to toggle distortion correction, 'a' to toggle angle marks, 'c' to toggle circles")
    
    # Flag to toggle distortion correction
    correct_distortion = True
    show_angles = True
    draw_circles = False
    
    while True:
        # Capture frame
        ret, frame = cap.read()
        
        if not ret:
            print("Error: Failed to capture image")
            break
        
        if correct_distortion:
            # upscale frame before undistortion
            # frame = cv2.resize(frame, (width * 2, height * 2))
            # Apply undistortion
            undistorted = cv2.remap(frame, mapx, mapy, cv2.INTER_LINEAR, borderValue=(100,100,100))
            original_width = undistorted.shape[1]
            original_height = undistorted.shape[0]
            
            # Crop the image (optional)
            x, y, w, h = roi
            # expand_x = 600
            # x -= expand_x
            # w += expand_x
            # expand_y = 100
            # y -= expand_y
            # h += expand_y
            expand_x = 1200
            x -= expand_x
            w += expand_x * 2
            expand_y = 200
            y -= expand_y
            h += expand_y * 2
            # x = int(undistorted.shape[1] * 0.1)
            # y = int(undistorted.shape[0] * 0.1)
            # w = int(undistorted.shape[1] * 0.7)
            # h = int(undistorted.shape[0] * 0.65)
            x = int(undistorted.shape[1] * CROP_LEFT)
            y = int(undistorted.shape[0] * CROP_TOP)
            w = int(undistorted.shape[1] * (1 - CROP_LEFT - CROP_RIGHT))
            h = int(undistorted.shape[0] * (1 - CROP_TOP - CROP_BOTTOM))
            undistorted = undistorted[y:y+h, x:x+w]
            # Or don't
            # x = 0
            # y = 0
            # w = undistorted.shape[1]
            # h = undistorted.shape[0]
            
            # Resize to original size for display
            # undistorted = cv2.resize(undistorted, (width, height))
            
            # aspect_point = points_from_angles([[0, 0],[60, 60]])
            # aspect_ratio = ((aspect_point[0][1] - aspect_point[1][1])) / ((aspect_point[0][0] - aspect_point[1][0]))
            # print(aspect_ratio)
            # current_aspect = undistorted.shape[1] / undistorted.shape[0]
            
            # Resize to original height while maintaining aspect ratio
            undistorted = cv2.resize(undistorted, (int(height / undistorted.shape[0] * undistorted.shape[1] * SCALE), int(height * SCALE)), interpolation=cv2.INTER_AREA)
            # undistorted = cv2.resize(undistorted, (int(height * aspect_ratio * SCALE), int(height * SCALE)), interpolation=cv2.INTER_AREA)
            
            final_scale_x = undistorted.shape[1] / w
            final_scale_y = undistorted.shape[0] / h
            
            ui = np.zeros_like(undistorted)
            
            if show_angles:
                # undistorted = np.zeros_like(undistorted)
                # Draw a cross across the entire center of the image
                center_points = points_from_angles([[-50, 0], [50, 0], [0, 50], [0, -50]])
                center_points[:, 0] -= x
                center_points[:, 1] -= y
                center_points[:, 0] *= final_scale_x
                center_points[:, 1] *= final_scale_y
                center_points = center_points.astype(int)
                # print("center_points", center_points)
                cv2.line(undistorted, tuple(center_points[0]), tuple(center_points[1]), (255, 255, 255), 1)
                cv2.line(undistorted, tuple(center_points[2]), tuple(center_points[3]), (255, 255, 255), 1)
                
                #
                
                # Draw concentric labeled boxes with angles using points_from_angles
                step = int(5) / 2
                for i in range(1, math.ceil(70 / step) + 1):
                    angle = i * step
                    # Draw a box with the angle
                    points = points_from_angles([[angle, angle], [angle, -angle], [-angle, -angle], [-angle, angle]])
                    # adjust for crop
                    points[:, 0] -= x
                    points[:, 1] -= y
                    points[:, 0] *= final_scale_x
                    points[:, 1] *= final_scale_y
                    # print("points", points)
                    # Draw the box or circle with a color based on the angle
                    # Colors are defined in hsv using i*sqrt(2) for the hue
                    # color = (int(i * math.sqrt(2) * 180) % 180, 150, 255)
                    color = (int(i * (1.0 / 6.0) * 180) % 180, 150, 255)
                    # Convert
                    hsv = cv2.cvtColor(np.uint8([[color]]), cv2.COLOR_HSV2BGR)[0][0]
                    hsv = (int(hsv[0]), int(hsv[1]), int(hsv[2]))
                    # print(hsv)
                    
                    if draw_circles:
                        # Draw a circle using the center and radius matching the square's sides (not corners)
                        center = (int(np.mean(points[:, 0])), int(np.mean(points[:, 1])))
                        # Calculate radius as half the width/height of the square (distance from center to side midpoint)
                        # Use the full bounding box span to get proper width and height
                        bbox_width = np.max(points[:, 0]) - np.min(points[:, 0])
                        bbox_height = np.max(points[:, 1]) - np.min(points[:, 1])
                        radius = int(min(bbox_width, bbox_height) / 2)
                        cv2.circle(ui, center, radius, hsv, 2)
                    else:
                        # Draw the box
                        cv2.polylines(ui, [np.int32(points).reshape(-1, 1, 2)], True, hsv, 2)
                    
                    # Add text to inner of each side
                    points_int = np.int32(points).reshape(-1, 1, 2)
                    for j in range(4):
                        # Calculate the midpoint of the side
                        midpoint = (int((points_int[j][0][0] + points_int[(j+1)%4][0][0]) / 2), int((points_int[j][0][1] + points_int[(j+1)%4][0][1]) / 2))
                        # add offset to bring it inside the box
                        if j == 0:
                            midpoint = (midpoint[0] - 20, midpoint[1] - 7)
                        elif j == 1:
                            midpoint = (midpoint[0], midpoint[1] - 5)
                        elif j == 2:
                            midpoint = (midpoint[0] - 20, midpoint[1] + 15)
                        else:
                            midpoint = (midpoint[0] - 25, midpoint[1] - 5)
                        # Add text to the midpoint
                        if draw_circles:
                            # Show radius (half FOV) for circles, include .5 when applicable
                            radius_val = angle
                            text = f"{radius_val:g}"
                        else:
                            text = f"{int(angle * 2)}"
                        if j == 0 or j == 2:
                            text += " deg" if draw_circles else " FOV"
                        cv2.putText(ui, text, midpoint, cv2.FONT_HERSHEY_SIMPLEX, 0.5, hsv, 1)

                
            
            # Add text to indicate undistorted view
            cv2.putText(ui, "Undistorted", (50, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            combined = cv2.addWeighted(undistorted, 0.5, ui, 0.5, 0)
            combined = np.where(ui == 0, undistorted, combined)
            # combined = np.where(undistorted == 0, 100, combined)
            
            # Display the undistorted frame
            cv2.imshow('Camera Feed', combined)
        else:
            # Add text to indicate original view
            cv2.putText(frame, "Original", (50, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            # Resize to original height while maintaining aspect ratio
            frame = cv2.resize(frame, (int(width * SCALE), int(height * SCALE)), interpolation=cv2.INTER_AREA)
            
            # Display the original frame
            cv2.imshow('Camera Feed', frame)
        
        # Wait for key press
        key = cv2.waitKey(1) & 0xFF
        
        
        # 'q' to quit
        if key == ord('q'):
            break
        
        # 'd' to toggle distortion correction
        elif key == ord('d'):
            correct_distortion = not correct_distortion
            print(f"Distortion correction {'ON' if correct_distortion else 'OFF'}")
        
        # 'a' to toggle angle marks
        elif key == ord('a'):
            show_angles = not show_angles
            print(f"Angle marks {'ON' if show_angles else 'OFF'}")
        
        # 'c' to toggle circles
        elif key == ord('c'):
            draw_circles = not draw_circles
            print(f"Circles {'ON' if draw_circles else 'OFF'}")
    
    # Release camera and close windows
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    live_undistortion()