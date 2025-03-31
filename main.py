import socket
import serial
import logging
import time
import ast
import re

class DoosanRobot:
    def __init__(self):
        self.ip = '192.168.137.100'  # Correct IP address
        self.port = 9225  # Port
        self.sock = None
        self.is_connected = False  # Track connection status
        self.logger = logging.getLogger()  # Use the same logger instance
        logging.basicConfig(level=logging.INFO)  # Setup basic logging

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            robot_address = (self.ip, self.port)  # Correct address
            self.sock.connect(robot_address)
            self.is_connected = True  # Set connection status
            self.logger.info(f"Connected to Doosan M1013 at {self.ip}:{self.port}")
        except Exception as e:
            self.is_connected = False  # Reset connection status on failure
            self.logger.error(f"Failed to connect: {e}")

    def send(self, message, wait_motion=True):
        """Sends a message to the robot."""
        try:
            if self.sock and self.is_connected:  # Ensure connection is established
                self.sock.sendall(message.encode())
                self.logger.info(f"Sent: {message}")

                # Wait for motion to complete if enabled
                if wait_motion and "movej" in message or "amovej" in message or "set_digital_output" in message:
                    self.wait_motion()
            else:
                self.logger.warning("Connection not established.")
        except Exception as e:
            self.logger.error(f"Failed to send: {e}")

    def receive(self, buffer_size=1024):
        """Receives a message from the robot."""
        try:
            if self.sock and self.is_connected:  # Ensure connection is established
                response = self.sock.recv(buffer_size).decode()
                self.logger.info(f"Received: {response}")
                return response
            else:
                self.logger.warning("Connection not established.")
        except Exception as e:
            self.logger.error(f"Failed to receive: {e}")

    def close(self):
        """Closes the connection to the robot."""
        if self.sock:
            self.sock.close()
            self.sock = None
            self.is_connected = False  # Reset connection status
            self.logger.info("Connection closed.")

    def wait_motion(self):
        """Wait until the robot stops moving."""
        while True:
            # Check if the robot is still moving
            response = self.receive()  # Get the robot's feedback
            print(response)
            if "0" in response:  # Check for motion completion message (you may need to adjust this)
                self.logger.info("Robot has finished moving.")
                break
            time.sleep(0.1)  # Wait for 100ms before checking again
            if "100" in response:
                self.logger.info("Digital output on.")
                break

    def force(self, force, target_posj):
        """Waits until the given force is detected on the robot."""
        check = True

        while check:
            # Check force condition
            self.send(f"check_force_condition(axis=DR_AXIS_Z, max={force}, ref=DR_TOOL)")
            response = self.receive()  # Ensure clean response

            # Get current joint position
            self.send("get_current_posj()")
            time.sleep(0.1)

            pos = self.receive()
            pos = eval(pos)
            posj_formatted = f"posj({', '.join(map(str, pos))})"

            # Force condition met
            if response == "0":
                print("Force condition met!")
                break

            # Position reached without force detection
            if posj_formatted == target_posj:
                print("No force detected, position reached!")
                return 1

            time.sleep(0.1)  # Small delay to avoid excessive checking


# arduino = serial.Serial('COM11', 9600, timeout=1)  # Connect to Arduino

# Pistons are connected at D/O 1/2 and 9/10

# Create instance and connect to the robot
robot = DoosanRobot()
robot.connect()

# Predetermined variables, should be edited with care.
start_pos = "posj(-1.2, 25.0, -102.6, 0.3, -97.6, -90.3)"
access_pos = "unknown"
lid_pos = "posj(-57.7, -2.3, -85.3, -1.1, -91.6, -90.3)"
down_pos = "posj(-61.2, -19.8, -113.2, -1.1, -44.4, -90.3)"
bucket_pos = "unknown"

count_amount = 5
# Send commands and wait for motion to complete
robot.send("set_digital_output(1,OFF)")

robot.send(f"movej({start_pos}, v=10, a=20)")

while True:

    # if arduino.in_waiting > 0:
    #     count_value = arduino.readline().decode().strip()
    #     print(f"Arduino Count: {count_value}")
    #
    #     if int(count_value % count_amount) == 0:  # If count reaches 10
            # Moving and picking up the accessorie bag and placing it in the bucket
            # robot.send(f"movej({acces_pos}, v=10, a=20)")
            # robot.send(f"amovej(addto({acces_pos}, [0,0,-20,0,0,0]), v=10, a=20)")
            # robot.force(3)  # Will check the force on the robot and will go further when the force is met (when the arm is on the bag)
            #
            # robot.send("stop(DR_QSTOP)")  # Stop the robot
            #
            # robot.send("set_digital_output(1,ON)")
            #
            # time.sleep(3)  # Wait for 3 seconds to guarantee a good suction
            # # Moving to the bucket
            # #robot.send(f"movej({bucket_pos}, v=10, a=20)")
            # #robot.send(f"movej(addto({bucket_pos}, [0,0,-20,0,0,0]), v=10, a=20)")
            # robot.send("set_digital_output(1,OFF)")

            robot.send(f"movej({lid_pos}, v=10, a=20)")
            robot.send(f"amovej({down_pos}, v=5, a=20)")  # in the actual situ only the Z axis will have to move down.

            if robot.force(10, down_pos) == 1:  # Will check the force on the robot and will go further when the force is met
                robot.send(f"movej({lid_pos}, v=10, a=20)")
                # go to different pos and go down there
                # robot.send(f"movej(addto(")
                # robot.send(f"amovej({down_pos}, v=5, a=20)")
                # robot.force(10, down_pos)
            else:
                robot.send("stop(DR_QSTOP)")  # Stop the robot

                robot.send("set_digital_output(2,ON)")

                time.sleep(3)  # Wait for 3 seconds to guarantee a good suction

            robot.send(f"movej({lid_pos}, v=5, a=20)")

            # Moving the lid to the bucket and placing it there
            # robot.send(f"movej({bucket_pos}, v=10, a=20)")
            # robot.send(f"movej(addto({bucket_pos}, [0,0,-20,0,0,0]), v=5, a=20)") # Moving it down into position
            robot.send("set_digital_output(2,OFF)")
            # time.sleep(1)
            # robot.send(f"movej({bucket_pos}, v=10, a=20)")

            robot.send(f"movej({start_pos}, v=10, a=20)")


# Close the connection
robot.close()
