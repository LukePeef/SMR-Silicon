import socket
import logging
import time
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

    def force(self, force):
        """Waits until the given force is detected on the robot."""
        check = True
        while check:
            # Send the check_force_condition command
            self.send(f"check_force_condition(axis=DR_AXIS_Z, max={force}, ref=DR_TOOL)")

            # Receive the response from the robot
            response = self.receive()

            # Check if the force condition is met
            if response == "0":
                check = False
                print("Force condition met!")
            time.sleep(1)


# Create instance and connect to the robot
robot = DoosanRobot()
robot.connect()

# Positions
start_pos = "posj([181.3, 5.4, -144.5, -355.1, 46.4, -88.2])"
acces_pos = "unknown"
lid_pos = "posj([222.3, -9.9, -154.2, -356.8, 69.8, -88.2])"
downlid_pos = "posj([222.8, -38.0, -156.3, -358.2, 100.3, -88.2])"
bucket_pos = "unknown"

# Send commands and wait for motion to complete
robot.send("set_digital_output(1,OFF)")

robot.send(f"movej({start_pos}, v=25, a=20)")

# Moving and picking up the accessorie bag and placing it in the bucket
# robot.send(f"movej({acces_pos}, v=10, a=20)")
# robot.send(f"amovej({acces_pos + ()}, v=10, a=20)")
# robot.force(5)  # Will check the force on the robot and will go further when the force is met (when the arm is on the bag)
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

robot.send(f"movej({lid_pos}, v=25, a=20)")
robot.send(f"amovej(addto({lid_pos}, [0, -28, -2, -2, 30, 0]), v=5, a=20)")  # in the actual situ only the Z axis will have to move down.

robot.force(2)  # Will check the force on the robot and will go further when the force is met

robot.send("stop(DR_QSTOP)")  # Stop the robot

robot.send("set_digital_output(2,ON)")

time.sleep(3)  # Wait for 3 seconds to guarantee a good suction

robot.send(f"movej({lid_pos}, v=10, a=20)")

# Moving the lid to the bucket and placing it there
# robot.send(f"movej({bucket_pos}, v=10, a=20)")
# robot.send(f"movej(addto({bucket_pos}, [0,0,-20,0,0,0]), v=5, a=20)") # Moving it down into position
robot.send("set_digital_output(2,OFF)")
# time.sleep(1)
# robot.send(f"movej({bucket_pos}, v=10, a=20)")

robot.send(f"movej({start_pos}, v=15, a=20)")


# Close the connection
robot.close()
