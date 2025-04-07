import socket
import serial
import logging
import time
import threading
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
                if wait_motion and "movej" in message or "amovel" in message and "movel" in message \
                or "set_digital_output" in message or "stop" in message:
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

    def force(self, force_threshold, target_posx):
        """Waits until the given force is detected or the position is reached without force."""
        check = True
        import ast

        # Convert target_posx to list if it's a string like "posx([...])"
        if isinstance(target_posx, str):
            try:
                if "posx" in target_posx:
                    target_posx = target_posx.replace("posx", "").strip("()")
                target_posx = ast.literal_eval(target_posx)
            except Exception as e:
                print(f"Error parsing target_posx: {target_posx} | {e}")
                return False

        while check:
            # Request force condition check
            self.send(f"check_force_condition(axis=DR_AXIS_Z, max={force_threshold}, ref=DR_TOOL)")
            response = self.receive()
            time.sleep(0.05)

            # Get current position
            self.send("get_current_posx()")
            time.sleep(0.05)
            pos_raw = self.receive()

            # Get tool force
            self.send("get_tool_force()")
            time.sleep(0.05)
            force_raw = self.receive()

            # Parse position safely
            try:
                pos_data = ast.literal_eval(pos_raw)
                if isinstance(pos_data, tuple) and isinstance(pos_data[0], list):
                    pos = pos_data[0]
                else:
                    raise ValueError("Unexpected position structure")
            except Exception as e:
                print(f"Error parsing position: {pos_raw} | {e}")
                continue

            # Parse force safely
            try:
                force_data = ast.literal_eval(force_raw)
                if isinstance(force_data, list) and len(force_data) >= 3:
                    current_fz = force_data[2]
                else:
                    raise ValueError("Unexpected force data")
            except Exception as e:
                print(f"Error parsing force: {force_raw} | {e}")
                continue

            print(f"Current Fz: {current_fz} | Pos: {pos}")

            # Force condition met
            if response == "0":
                print("Force condition met!")
                check = False
                robot.send("stop(DR_QSTOP)")  # Stop the robot


                return True

            # Optional: check if we reached the target position without force
            # Uncomment if you want to use this check
            if all(abs(p1 - p2) < 1.0 for p1, p2 in zip(pos, target_posx)):
                print("No force detected, target position reached.")
                return False

            time.sleep(0.1)

    def startup(self):
        """Before starting all the actions, start up the robot and put all the digital outputs off."""
        robot.send(f"set_digital_output(1, ON)")
        robot.send(f"set_digital_output(10, ON)")
        robot.send(f"set_digital_output(14, ON)")
        robot.send(f"set_digital_output(3, ON)")
        robot.send(f"set_digital_output(5, ON)")
        for i in range(1, 13):
            robot.send(f"set_digital_output({i}, OFF)")
        robot.send(f"set_digital_output(11, ON)")
        # robot.send(f"movej({start_pos}, v=10, a=20)")

    def monitor_sensor(self):
        """Continuously checks the digital input for changes."""
        while True:
            self.send("get_digital_input(3)")  # Request the sensor state
            sensor_state2 = self.receive()

            if sensor_state2 == '0':  # Adjust based on sensor logic
                print("Button off pressed!")
                time.sleep(1)  # Avoid spamming


# Pistons are connected at D/O 1/2 and 9/10

# Create instance and connect to the robot
robot = DoosanRobot()
robot.connect()

# sensor_thread = threading.Thread(target=robot.monitor_sensor(), args=(robot,), daemon=True)
# sensor_thread.start()

# Predetermined variables, should be edited with care.
start_pos = "posj(-1.2, 25.0, -102.6, 0.3, -97.6, -90.3)"
access1_pos = "posx(37.4, 517.3, 515.7, 41.7, 177.5, 128.1)"
access1_down = "posx(50.1, 530.3, 62.6, 26.4, 179.1, 113.0)"
access2_pos = "posj(-55.0, -9.2, -95.4, -4.3, -74.4, -86.2)"
lid_pos = "posj(-57.7, -2.3, -85.3, -1.1, -91.6, -90.3)"
down_pos = "posj(-61.2, -19.8, -113.2, -1.1, -44.4, -90.3)"
bucket_pos = "unknown"

count_amount = '5'
on_button = 0


# Start up the robot and move it to the starting position
robot.startup()

while on_button == 0:
    robot.send("get_digital_input(2)")
    sensor_state = robot.receive()

    if sensor_state == '1':
        on_button = 1
        print("Button on pressed")
        # time.sleep(1)
        # robot.send("set_digital_output(9, ON)")
        # robot.send("set_digital_output(9, OFF)")

print("Exited first while loop, entering second...")  # Debugging
# arduino = serial.Serial('COM11', 115200, timeout=1)  # Connect to Arduino
while True:

    # print(f"In the iff:")
    # if arduino.in_waiting > 0:
    #     count_value = arduino.readline().decode().strip()
    #     print(f"Count: {count_value}")
    #     robot.send(f"set_digital_output(13, ON)")
    #     robot.send(f"set_digital_output(13, OFF)")
    #
    #
    #
    #     if count_value == count_amount:  # If count reaches 10
    #         print(f"In the iff: {count_value}")
    #         time.sleep(0.5)
    #         robot.send("set_digital_output(2, ON)")
    #         robot.send("set_digital_output(2, OFF)")
    #         time.sleep(3.5)
    #         robot.send("set_digital_output(1, ON)")
    #         robot.send("set_digital_output(1, OFF)")
    #         robot.send("set_digital_output(10, ON)")
    #         robot.send("set_digital_output(10, OFF)")
    #         robot.send(f"set_digital_output(14, OFF)")
    #         time.sleep(0.5)
    #         robot.send(f"set_digital_output(14, ON)")
    #         time.sleep(5)
    #         robot.send("set_digital_output(9, ON)")
    #         robot.send("set_digital_output(9, OFF)")
            # Moving and picking up the accessorie bag and placing it in the bucket
            robot.send(f"movel({access1_pos}, v=20, a=20)")
            # robot.send("movej(posj(-90.4, -4.9, -115.6, -4.6, -59.8, -86.2), v=5,a=20)")
            robot.send(f"amovel({access1_down}, v=20, a=20)")
            time.sleep(0.1)

            force = robot.force(37, access1_down)

            if not force:
                # robot.send("set_reference(DR_TOOL)")  # Or DR_BASE depending on your use
                robot.send(f"movel({access1_pos}, v=20, a=20)")
                robot.send(f"movej({access2_pos}, v=5, a=20)")

            # robot.force(3)  # Will check the force on the robot and will go further when the force is met (when the arm is on the bag)
            else:
                # robot.send("get_current_pos")
                robot.send("set_digital_output(4, ON)")
                robot.send("set_digital_output(4, OFF)")
                robot.send("set_digital_output(6, ON)")
                robot.send("set_digital_output(6, OFF)")
                time.sleep(6)  # Wait for 3 seconds to guarantee a good suction
                robot.send(f"movel({access1_pos}, v=40, a=20)")
            #
            # robot.send("set_digital_output(1,ON)")
            #
            # # Moving to the bucket
            # #robot.send(f"movej({bucket_pos}, v=10, a=20)")
            # #robot.send(f"movej(addto({bucket_pos}, [0,0,-20,0,0,0]), v=10, a=20)")
            # robot.send("set_digital_output(1,OFF)")
            #
            # robot.send(f"movej({lid_pos}, v=10, a=20)")
            # robot.send(f"amovej({down_pos}, v=5, a=20)")  # in the actual situ only the Z axis will have to move down.
            #
            # if robot.force(10, down_pos) == 1:  # Will check the force on the robot and will go further when the force is met
            #     robot.send(f"movej({lid_pos}, v=10, a=20)")
            #     # go to different pos and go down there
            #     # robot.send(f"movej(addto(")
            #     # robot.send(f"amovej({down_pos}, v=5, a=20)")
            #     # robot.force(10, down_pos)
            # else:
            #     robot.send("stop(DR_QSTOP)")  # Stop the robot
            #
            #     robot.send("set_digital_output(2,ON)")
            #
            #     time.sleep(3)  # Wait for 3 seconds to guarantee a good suction
            #
            # robot.send(f"movej({lid_pos}, v=5, a=20)")
            #
            # # Moving the lid to the bucket and placing it there
            # # robot.send(f"movej({bucket_pos}, v=10, a=20)")
            # # robot.send(f"movej(addto({bucket_pos}, [0,0,-20,0,0,0]), v=5, a=20)") # Moving it down into position
            # robot.send("set_digital_output(2,OFF)")
            # # time.sleep(1)
            # # robot.send(f"movej({bucket_pos}, v=10, a=20)")
            #
            # robot.send(f"movej({start_pos}, v=10, a=20)")


# Close the connection
robot.close()
