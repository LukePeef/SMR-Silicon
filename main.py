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

    def send(self, message):
        """Sends a message to the robot."""
        try:
            if self.sock and self.is_connected:  # Ensure connection is established
                self.sock.sendall(message.encode())
                self.logger.info(f"Sent: {message}")

                # Wait for motion to complete if enabled
                if any(cmd in message for cmd in ["movej", "amovel", "movel", "set_digital_output", "stop"]):
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

    def force(self, force_threshold, target_posx, access):
        """Waits until the given force is detected or the position is reached without force."""
        check = True

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
            time.sleep(0.1)

            # Get current position
            self.send("get_current_posx()")
            time.sleep(0.1)
            pos_raw = self.receive()

            # # Get tool force
            # self.send("get_tool_force()")
            # time.sleep(0.05)
            # force_raw = self.receive()

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

            # Force condition met
            if response == "0" and access == "1":
                print("Force condition met!")
                check = False
                self.send("stop(DR_QSTOP)")  # Stop the robot
                posx_str = f"posx({', '.join(map(str, pos))})"
                print(posx_str)
                time.sleep(2)
                # Send the command to move with 'addto' and 'movel'
                self.send(f"movel(trans({posx_str}, posx(0, 0, 10, 0, 0, 0)), v=10, a=20)")
                # self.send(f"movel(trans({posx_str}, posx(0, 0, -2, 0, 0, 0)), v=10, a=20)")
                # self.wait_motion()
                # self.send(f"movel(trans({posx_str}, posx(0, 0, 10, 0, 0, 0)), v=10, a=20)")
                # # self.wait_motion()
                # # self.send(f"movel(trans({posx_str}, posx(0, 0, -2, 0, 0, 0)), v=10, a=20)")
                # self.wait_motion()
                return True
            if response == "0" and access == "0":
                print("Force condition met!")
                check = False
                return True
            # Optional: check if we reached the target position without force
            # Uncomment if you want to use this check
            if all(abs(p1 - p2) < 1.0 for p1, p2 in zip(pos, target_posx)):
                print("No force detected, target position reached.")
                return False

            # time.sleep(0.1)

    def startup(self):
        """Before starting all the actions, start up the robot and put all the digital outputs off."""
        robot.send(f"set_digital_output(10, ON)")
        robot.send(f"set_digital_output(14, ON)")
        robot.send(f"set_digital_output(3, ON)")
        robot.send(f"set_digital_output(7, ON)")
        robot.send(f"set_digital_output(5, ON)")
        for i in range(1, 13):
            robot.send(f"set_digital_output({i}, OFF)")
        robot.send(f"set_digital_output(11, OFF)")
        robot.send(f"set_digital_output(12, ON)")

        # robot.send(f"movej({start}, v=5, a=20)")

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

# Predetermined variables, should be edited with care.
start = "posj(-58.4, 4.5, -91.9, -5.7, -92.0, -45.9)"
start_pos = "posj(-59.8, -35.1, -70.9, -3.0, -69.9, -141.8)"
access1_pos = "posx(130.1, 513.4, 479.3, 77.7, 176.6, 74.9)"

access1_down = "posx(130.0, 506.5, 114.8, 77.7, 176.6, 74.9)"
access2_pos = "posj(-55.0, -9.2, -95.4, -4.3, -74.4, -86.2)"
lid_pos = "posj(61.8, 21.0, -128.4, 1.4, -67.7, -209.9)"
lid_posx = "posx(-248.7, -46.4, 664.1, 12.2, -177.9, 12.8)"
bucket_pos = "posx(-756.0, 529.2, 574.4, 9.5, -175.5, -78.8)"
bucket_posx = "posx(-765.3, 471.1, 532.7, 153.7, -177.4, 64.1)"
push_buck1= "posj(-46.9, -54.6, -33.0, -3.0, -85.1, -141.8)"
push_buck2= "posj(-38.9, -44.3, -53.0, 0.2, -80.5, -131.6)"
push_side1= "posj(-47.4, -9.9, -105.3, -6.5, -63.7, -47.8)"
push_side2= "posj(-41.0, -12.9, -101.8, -7.9, -64.4, -38.7)"
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
        time.sleep(1)
        robot.send("set_digital_output(9, ON)")
        robot.send("set_digital_output(9, OFF)")
    #         time.sleep(5)
    #         robot.send("set_digital_output(11, OFF)")


print("Exited first while loop, entering second...")  # Debugging
arduino = serial.Serial('COM11', 115200, timeout=1)  # Connect to Arduino
while True:
    # if arduino.in_waiting > 0:
    #     count_value = arduino.readline().decode().strip()
    #     print(f"Count: {count_value}")
    #     robot.send(f"set_digital_output(13, ON)")
    #     robot.send(f"set_digital_output(13, OFF)")
    #
    #     if count_value == count_amount:  # If count reaches 10
    #         print(f"In the iff: {count_value}")
    #         time.sleep(0.5)
    #         robot.send("set_digital_output(11, ON)")
    #         time.sleep(5)
    #         robot.send("set_digital_output(11, OFF)")
    #         robot.send(f"set_digital_output(14, OFF)")
    #         time.sleep(0.5)
    #         robot.send(f"set_digital_output(14, ON)")
    #         robot.send("set_digital_output(9, ON)")
    #         robot.send("set_digital_output(9, OFF)")
    #         time.sleep(5)
    #         robot.send("set_digital_output(10, ON)")
    #         robot.send("set_digital_output(10, OFF)")

    # Push the bucket to make sure it is in position.
            time.sleep(5)
            robot.send(f"movej({start}, v=20,a=20)")
            robot.send("movej(posj(-58.8, -13.6, -110.0, -5.9, -55.6, -58.4), v=10, a=10)")
            robot.send(f"movej({start_pos}, v=20,a=20)")

            robot.send(f"movej({push_buck1}, v=10,a=20)")

            robot.send(f"movej({push_buck2}, v=5,a=20)")
            time.sleep(2)
            robot.send(f"movej({push_buck1}, v=10,a=20)")
            time.sleep(.5)
            robot.send(f"movej({start_pos}, v=10,a=20)")
            robot.send(f"movej({push_side1}, v=10,a=20)")
            time.sleep(.5)
            robot.send(f"movej({push_side2}, v=5,a=20)")
            time.sleep(2)
            robot.send(f"movej({push_side1}, v=10,a=20)")
            time.sleep(.5)
            # robot.send(f"movej({start_pos}, v=10,a=20)")
            robot.send(f"movej({start}, v=10,a=20)")

            # Moving and picking up the accessorie bag and placing it in the bucket
            robot.send(f"movel(trans({access1_pos}, posx(0,0,50,0,0,0)), v=60,a=20)")
            time.sleep(0.1)
    #
            robot.send(f"amovel({access1_down}, v=15, a=20)")
            robot.send("set_digital_output(4, ON)")
            robot.send("set_digital_output(4, OFF)")
            robot.send("set_digital_output(8, ON)")
            robot.send("set_digital_output(8, OFF)")
            robot.send("set_digital_output(6, ON)")
            robot.send("set_digital_output(6, OFF)")
            # time.sleep(2)
            # robot.send("set_digital_output(6, ON)")
            # robot.send("set_digital_output(6, OFF)")
            # robot.send("set_digital_output(11, OFF)")
            force = robot.force(11, access1_down, "1")


            if force:
                max_retries = 1
                attempt = 0
                while attempt < max_retries:
                    attempt += 1
                    # Attempt pickup
                    time.sleep(3)  # Wait for 3 seconds to guarantee a good suction
                    robot.send(f"movel({access1_pos}, v=20, a=20)")
                    time.sleep(0.5)
                    robot.send("get_tool_force()")
                    lift_force_raw = robot.receive()

                    print(f"Raw force received: {lift_force_raw}")  # Always inspect what comes back

                    try:
                        # Attempt to evaluate the string
                        lift_force = eval(lift_force_raw)

                        # Confirm it's a list and long enough
                        if isinstance(lift_force, list) and len(lift_force) >= 3:
                            lift_fz = float(lift_force[2])  # Fz = Z-axis
                            print(f"lift_fz: {lift_fz}")
                            time.sleep(0.5)
                        else:
                            raise ValueError("Invalid force data structure")

                    except Exception as e:
                        print(f"Failed to parse force data: {e}")
                        lift_fz = 0  # Or default to 0 if you'd prefer

                    # Compare forces
                    if lift_fz < -15:
                        print("Gelukttt!")
                        robot.send(f"movel(trans({access1_pos}, posx(0,0,100,0,0,0)), v=60,a=20)")
                        time.sleep(0.5)
                        robot.send(f"movel(trans({bucket_pos}, posx(0,0,150,0,0,0)), v=50,a=20)")
                        time.sleep(0.5)
                        robot.send(f"movel(trans({bucket_pos}, posx(0,0,-30,0,0,0)), v=30,a=20)")
                        time.sleep(0.5)


                        robot.send(f"set_digital_output(3, ON)")
                        robot.send(f"set_digital_output(5, ON)")
                        robot.send(f"set_digital_output(3, OFF)")
                        robot.send(f"set_digital_output(5, OFF)")
                        robot.send("set_digital_output(7, ON)")
                        robot.send("set_digital_output(7, OFF)")
                        robot.send(f"movej(posj(-31.6, -22.1, -45.4, 2.7, -111.4, -116.0), v=10, a=20)")
                        break  # Success!
                    else:
                        print("Retrying pickup...")
                        robot.send("set_digital_output(4, ON)")
                        robot.send("set_digital_output(4, OFF)")
                        robot.send("set_digital_output(8, ON)")
                        robot.send("set_digital_output(8, OFF)")
                        robot.send("set_digital_output(6, ON)")
                        robot.send("set_digital_output(6, OFF)")
                        robot.send(f"amovel({access1_down}, v=20, a=20)")
                        time.sleep(0.2)
                        force = robot.force(11, access1_down, "1")
    #         #
    #         # # # Picking up the lid and placing it on the bucket (position of the bucket has to be exact)
    #         # time.sleep(2)
            robot.send(f"movej({start}, v=5, a=20)")
            robot.send(f"movel(trans({lid_posx}, posx(0,0,0,0,0,0)), v=70,a=30)")
            robot.send(f"amovel(trans({lid_posx}, posx(0,0,-300,0,0,0)), v=10,a=20)")
            force = robot.force(19, "posx(-179.9, -268.0, 143.3, 76.5, -174.9, 165.3)", "0")
            # big suctioncup on
            robot.send("set_digital_output(2, ON)")
            robot.send("set_digital_output(2, OFF)")
            robot.send(f"movel(trans({lid_posx}, posx(0,0,250,0,0,0)), v=30,a=20)")
            robot.send(f"movej({start}, v=5, a=20)")
            robot.send(f"movel(trans({bucket_posx}, posx(0,0,150,0,0,0)), v=60,a=20)")
            robot.send(f"movel(trans({bucket_posx}, posx(0,0,0,0,0,0)), v=20,a=20)")
            # force = robot.force(15, "posx(-193.1, -289.4, 345.3, 118.8, 179.5, 26.1)", "0")
            # robot.send("set_digital_output(5, ON)")
            # robot.send("set_digital_output(5, OFF)")
            # robot.send("set_digital_output(3, ON)")
            # robot.send("set_digital_output(3, OFF)")
            # big suctioncup off
            robot.send("set_digital_output(1, ON)")
            robot.send("set_digital_output(1, OFF)")
            robot.send(f"movel(trans({bucket_posx}, posx(0,0,150,0,0,0)), v=60,a=20)")
            time.sleep(7)
            robot.send(f"movej(posj(-31.6, -22.1, -45.4, 2.7, -111.4, -116.0), v=10, a=20)")
            robot.send(f"movej({start}, v=5, a=20)")


            # # Lid closing mechanism
            # robot.send("set_digital_output(12, ON)")
            #
            # time.sleep(5)
            #
            # time.sleep(0.5)
            # robot.send("set_digital_output(12, OFF)")

# Close the connection
robot.close()
