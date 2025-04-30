import math
import pygame
from pygame.locals import *

from OpenGL.GL import *
from OpenGL.GLU import *
import time
import serial

COMPORT = 'COM11'  # Define the serial port.  Make sure this is correct for your setup.

# Define the vertices of a rectangular prism (cuboid)
# vertices[i] gives the (x, y, z) coordinate of the ith vertex.
verticies = (
    (2, -1, 0.4),
    (2, -1, -0.4),
    (-2, -1, -0.4),
    (-2, -1, 0.4),
    (2, 1, 0.4),
    (2, 1, -0.4),
    (-2, 1, 0.4),
    (-2, 1, -0.4)
)

# Define the edges of the rectangular prism by connecting vertex indices.
# edges[i] gives the indices of the vertices that form the ith edge.
edges = (
    (0, 1),  # Front right
    (0, 3),  # Front bottom
    (0, 4),  # Right bottom
    (2, 1),  # Front top
    (2, 3),  # Front left
    (2, 7),  # Left top
    (6, 3),  # Back left bottom
    (6, 4),  # Back bottom
    (6, 7),  # Back left top
    (5, 1),  # Back right top
    (5, 4),  # Back right bottom
    (5, 7)  # Back top
)


def Cube():
    """
    Draws the rectangular prism using OpenGL.
    """
    glColor3f(1.0, 1.0, 1.0)  # Set the color to white.  Arguments are RGB, 0.0 to 1.0.
    glBegin(GL_LINES)  # Start drawing lines
    for edge in edges:
        for vertex in edge: # Corrected from edeg to edge
            glVertex3fv(verticies[vertex])  # Specify the vertex for the line
    glEnd()  # Stop drawing lines



def draw_arrow(origin, vector, color):
    """
    Draws a 3D arrow in OpenGL.

    Args:
        origin: Tuple (x, y, z) for the starting point of the arrow.
        vector: Tuple (x, y, z) for the direction and magnitude of the arrow.
        color: Tuple (r, g, b) for the color of the arrow (values between 0.0 and 1.0).
    """
    glBegin(GL_LINES)
    glColor3fv(color)  # Set the arrow color
    glVertex3fv(origin)  # Starting point of the arrow
    glVertex3fv((origin[0] + vector[0],
                   origin[1] + vector[1],
                   origin[2] + vector[2]))  # Endpoint of the arrow
    glEnd()



def quaternion_to_euler(q):
    """
    Converts a quaternion (w, x, y, z) to Euler angles (roll, pitch, yaw) in degrees.

    Args:
        q: A tuple or list representing the quaternion (w, x, y, z).

    Returns:
        A tuple (roll_deg, pitch_deg, yaw_deg) representing the Euler angles in degrees.
    """
    w, x, y, z = q
    t0 = +2.0 * (w * x + y * z)
    t1 = +1.0 - 2.0 * (x * x + y * y)
    roll_deg = math.degrees(math.atan2(t0, t1))

    t2 = +2.0 * (w * y - z * x)
    t2 = +1.0 if t2 > +1.0 else t2  # Clamp to handle rounding errors
    t2 = -1.0 if t2 < -1.0 else t2
    pitch_deg = math.degrees(math.asin(t2))

    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (y * y + z * z)
    yaw_deg = math.degrees(math.atan2(t3, t4))

    return roll_deg, pitch_deg, yaw_deg



def get_imu_euler():
    """Simulates reading Euler angles from an IMU.  This function is NOT used."""
    # Replace this with your actual IMU data acquisition
    roll = time.time() * 10 % 360
    pitch = time.time() * 15 % 360
    yaw = time.time() * 20 % 360
    return roll, pitch, yaw



def read_quaternion_from_serial(ser):
    """
    Reads quaternion data from the serial port, and converts it to Euler angles.

    Args:
        ser: The serial port object.

    Returns:
        A tuple (roll, pitch, yaw) in degrees, or None on error.
    """
    try:
        # Read the data as a string from the serial port.
        data_str = ser.readline().decode('utf-8').strip()
        # Parse the string.  The expected format is "Quaternion: w x y z"
        parts = data_str.split(':')
        if len(parts) == 2 and parts[0] == 'Quaternion':
            quat_values_str = parts[1].split()
            if len(quat_values_str) == 4:
                try:
                    q = [float(v) for v in quat_values_str] # Convert the string values to floats
                    return quaternion_to_euler(q) # Convert quaternion to euler
                except ValueError:
                    print("Error: Invalid quaternion values")
                    return None  # Indicate an error
            else:
                print("Error: Expected 4 quaternion values")
                return None
        else:
            print("Error: Invalid data format")
            return None

    except serial.SerialException as e:
        print(f"Error reading from serial port: {e}")
        return -1
    except UnicodeDecodeError as e:
        print(f"Error decoding data: {e}")
        return None

def connect_serial():
    i = 30
    while i > 0:
        try:
            ser = serial.Serial(COMPORT, 115200, timeout=1)  # Open the serial port.
            
            print(f"Connected to serial port: {ser.name}")
            return ser
        except serial.SerialException as e:
            print(f"Error: Could not connect to serial port: {e}")
            print("trying again")

        time.sleep(1)
        i -= 1
    return None

def main():
    """
    Main function to initialize Pygame, OpenGL, and the serial connection,
    and then enter the main loop to display the 3D cube and update its
    orientation based on IMU data.
    """
    pygame.init()  # Initialize Pygame
    display = (800, 600)  # Set the display size
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)  # Create the display with OpenGL support

    # Initialize OpenGL perspective projection
    gluPerspective(45, (display[0] / display[1]), 0.1, 50.0)
    glTranslatef(0.0, 0.0, -5)  # Move the camera back

    # Initialize serial communication
    ser = connect_serial()
    if ser is None:
        print("Exiting...")
        pygame.quit()

    # Main loop
    while True:
        for event in pygame.event.get():  # Handle events (e.g., quitting)
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        # Get Euler angles from the IMU via serial.
        euler_angles = read_quaternion_from_serial(ser)
        if euler_angles == -1:
            ser = connect_serial()
            if ser is None:
                print("Exiting...")
                pygame.quit()   
            continue
        if euler_angles is None:  # Skip the rest of the loop iteration on error
            continue
        
        roll, pitch, yaw =euler_angles  # Unpack the Euler angles
        print(f"Roll: {roll}, Pitch: {pitch}, Yaw: {yaw}")
        # Clear the screen and depth buffer
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()  # Reset the modelview matrix
        gluPerspective(45, (display[0] / display[1]), 0.1, 50.0)  # Set projection
        glTranslatef(0.0, 0.0, -5)  # Move camera
        
        glRotatef(30, 1, 0, 0)  # Yaw (rotation around the Z-axis)        
        glRotatef(30, 0, 1, 0)  # Yaw (rotation around the Z-axis)       
        glRotatef(-90, 1, 0, 0)  # Yaw (rotation around the Z-axis)     
        # Apply rotations to the cube.  Order is important!
        glPushMatrix()  # Save the current matrix
        glRotatef(yaw, 0, 0, 1)  # Yaw (rotation around the Z-axis)
        glRotatef(pitch, 0, 1, 0)  # Pitch (rotation around the y-axis)
        glRotatef(roll, 1, 0, 0)  # Roll (rotation around the x-axis)
        Cube()  # Draw the cube with the applied rotations
        glPopMatrix()  # Restore the saved matrix (undo rotations for other objects)

        # Draw coordinate axes
        draw_arrow((0, 0, 0), (1, 0, 0), (1, 0, 0))  # X-axis (red)
        draw_arrow((0, 0, 0), (0, 0, 1), (0, 0, 1))  # Y-axis (blue) now Z
        draw_arrow((0, 0, 0), (0, 1, 0), (0, 1, 0))  # Z-axis (green) now Y

        pygame.display.flip()  # Update the display
        pygame.time.wait(10)  # Add a small delay
    #The serial port is closed automatically when the program exits.

if __name__ == "__main__":
    main()  # Call the main function to start the program
