import socket
import json
import logging

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


robot = DoosanRobot()

robot.connect()

robot.connect()

robot.connect()

robot.send("movej(posj[175.5, 6.2, -137.9, -181.6, 46.5, 0.0], v=10, a=20)")

print(robot.receive())
