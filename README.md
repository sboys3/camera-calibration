# Camera Calibration

A comprehensive Python toolkit for camera calibration using OpenCV. This project provides tools to calibrate your camera, remove lens distortion, and apply the calibration to live video feeds.

## Overview

Camera calibration is the process of estimating the parameters of a camera's lens and image sensor. These parameters can be used to correct for lens distortion, measure the size of an object in world units, or determine the location of the camera in the scene.

This toolkit includes:

1. **Image Capture Tool**: Capture calibration images from your camera
2. **Calibration Tool**: Process the calibration images to compute camera parameters
3. **Live Undistortion**: Apply the calibration to a live video feed

## Requirements

- Python 3.6+
- OpenCV 4.5+
- NumPy 1.20+
- Matplotlib 3.4+ (for visualization)

Install the required packages:

```bash
pip install -r requirements.txt
```

## Calibrating a VR Headset

This section describes how to calibrate a VR headset camera using this toolkit. The process involves capturing calibration images, generating a calibration profile, and creating a distortion profile for the headset.

### Prerequisites

- A wide-angle camera
- A VR headset capable of displaying the calibration pattern
- The calibration checkerboard pattern (print `board.svg` or display digitally)
- Access to the shader files for displaying the pattern on your VR headset

### Step 1: Capture Images and Generate Calibration

1. Print or display the checkerboard pattern (`board.svg`)
2. Run the image capture script:
   ```
   python capture_calibration_images.py
   ```
3. Capture multiple images of the checkerboard from different angles and positions
4. Press `c` to capture each image, `q` to quit
5. Run the calibration script to process the captured images:
   ```
   python camera_calibration.py
   ```
6. This will generate a calibration profile saved in the `output` directory

### Step 2: View Undistorted Camera Feed

1. Run the live undistortion script:
   ```
   python live_undistortion.py
   ```
2. This displays the undistorted camera feed with calibration markers overlaid

### Step 3: Display Pattern on VR Headset

1. The calibration pattern needs to be displayed on your VR headset
2. Shader files for displaying the pattern are included in this repository
3. Apply these shaders to your VR headset or if you have my VRC avatar, you can use the test pattern on it

### Step 4: Check Distortion Profile

1. Hold the camera up to the VR headset
2. Position the white markers visible in the live undistortion view
3. Adjust until the markers align with the pattern displayed on the headset

### Step 5: Create Distortion Profile
Start with a few points and then work your way up to evenly spaced points every 5 degrees.
1. Mount the camera in front of the headset lens and align it (you will need to find a suitable mounting solution)
2. Check the how the patterns line up
3. Modify the distortion profile iteratively
4. Adjust until all markers and patterns line up perfectly
5. Smooth out the derivatives using line-smooth.html
6. Go back to step 2 and check that it still aligns if you made any modifications an repeat until it lines up and has smooth derivatives
7. Save the final distortion profile for use

## Usage

### Step 1: Capture Calibration Images

You need multiple images of a chessboard pattern from different angles and positions. The script `capture_calibration_images.py` helps you capture these images:

```bash
python capture_calibration_images.py
```

Controls:
- Press `c` to capture an image
- Press `q` or Escape to quit

The images will be saved in the `calibration_images` directory.

### Step 2: Run Camera Calibration

Process the calibration images to compute the camera matrix and distortion coefficients:

```bash
python camera_calibration.py
```

The calibration results will be saved in the `output` directory:
- `calibration_data.pkl`: Complete calibration data in pickle format
- `camera_matrix.txt`: Camera matrix in text format
- `distortion_coefficients.txt`: Distortion coefficients in text format
- Undistorted versions of the calibration images (if enabled)

### Step 3: Test the Calibration with Live Video

Apply the calibration to a live video feed:

```bash
python live_undistortion.py
```

Controls:
- Press `d` to toggle between distorted and undistorted view
- Press `q` to quit

## Configuration

All scripts use variables instead of command-line arguments for configuration. You can modify these variables at the top of each script:

### In `capture_calibration_images.py`:

```python
CAMERA_ID = 0  # Camera ID (usually 0 for built-in webcam)
CHESSBOARD_SIZE = (9, 6)  # Number of inner corners per chessboard row and column
OUTPUT_DIRECTORY = 'calibration_images'  # Directory to save calibration images
```

### In `camera_calibration.py`:

```python
CHESSBOARD_SIZE = (9, 6)  # Number of inner corners per chessboard row and column
SQUARE_SIZE = 2.5  # Size of a square in centimeters
CALIBRATION_IMAGES_PATH = 'calibration_images/*.jpg'  # Path to calibration images
OUTPUT_DIRECTORY = 'output'  # Directory to save calibration results
SAVE_UNDISTORTED = True  # Whether to save undistorted images
```

### In `live_undistortion.py`:

```python
CAMERA_ID = 0  # Camera ID (usually 0 for built-in webcam)
CALIBRATION_FILE = 'output/calibration_data.pkl'  # Path to calibration data
```

## How It Works

### Camera Calibration Process

1. **Image Collection**: Capture multiple images of a chessboard pattern from different angles
2. **Corner Detection**: Detect the chessboard corners in each image
3. **Calibration**: Use the detected corners to compute the camera matrix and distortion coefficients
4. **Undistortion**: Apply the calibration to remove lens distortion from images

### Camera Model

The camera model used is the pinhole camera model with radial and tangential distortion:

- **Camera Matrix**: A 3x3 matrix containing the focal lengths and optical centers
- **Distortion Coefficients**: A vector containing the radial and tangential distortion coefficients

## Example Results

After calibration, you can expect:

1. **Undistorted Images**: Straight lines in the real world will appear straight in the images
2. **Accurate Measurements**: You can measure distances and sizes in the real world from the images
3. **3D Reconstruction**: You can use the calibration for 3D reconstruction or augmented reality applications

## Troubleshooting

### Common Issues

1. **Chessboard Not Detected**: Make sure the entire chessboard is visible in the image and well-lit
2. **Poor Calibration Results**: Use more images from different angles and positions
3. **Camera Not Found**: Check the CAMERA_ID parameter (usually 0 for built-in webcams)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenCV for providing the computer vision algorithms
- The OpenCV documentation for the camera calibration tutorial