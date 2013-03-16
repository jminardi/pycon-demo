import time
import json
import os
import threading

import spidev
import zmq
import RPi.GPIO as GPIO

from robot_brain.pin import Pin
from robot_brain.servo import Servo

GPIO.setmode(GPIO.BCM)

GPIO_TRIGGER = 25
GPIO_ECHO    = 24
LED = Pin(18)
MOTOR = Pin(23)
SERVO = Servo(0)

GPIO.setup(GPIO_TRIGGER,GPIO.OUT)  # Trigger
GPIO.setup(GPIO_ECHO,GPIO.IN)      # Echo

GPIO.output(GPIO_TRIGGER, False)

# Allow ping sensor to settle
time.sleep(0.5)

spi = spidev.SpiDev()
spi.open(0,0)

class SensorServer(object):

    def __init__(self, port=2012):
        self.port = port

        # Whether or not to continue running the server
        self._run = True

        self.sensor_data = {}
        self.links = []

        self.start()

    def start(self):
        """ Initialize and start threads. """

        self._server_thread = threading.Thread(target=self._server_worker)
        self._server_thread.start()

        self.acc_thread = threading.Thread(target=self._read_worker)
        self.acc_thread.start()

        self._link_thread = threading.Thread(target=self._link_worker)
        self._link_thread.start()

    def stop(self):
        """ Shut down server and control threads. """
        self._run = False
        print 'joining threads'
        self._server_thread.join()
        self.acc_thread.join()
        print 'threads were joined'

    def _server_worker(self):
        context = zmq.Context()
        socket = context.socket(zmq.REP)
        socket.bind("tcp://*:{}".format(self.port))
        print 'bound to socket:', socket

        while self._run:
            time.sleep(.1)
            #  Wait for next request from client
            message = socket.recv()
            print "Received request: ", message

            request = json.loads(message)
            self._handle_request(request)

            #  Send current sensor values back to client
            socket.send(json.dumps(self.sensor_data))
        socket.close()

    def _read_worker(self):
        x_pin = 0
        y_pin = 1
        z_pin = 2
        pot_pin = 3
        switch_pin = 4

        while self._run:
                # read the analog pins
                x_val = readadc(x_pin)
                y_val = readadc(y_pin)
                z_val = readadc(z_pin)
                pot_val = readadc(pot_pin)
                switch_val = readadc(switch_pin) / 1024.0
                ping_val = read_ping_sensor()
                self.sensor_data['acc_x'] = x_val
                self.sensor_data['acc_y'] = y_val
                self.sensor_data['acc_z'] = z_val
                self.sensor_data['potentiometer'] = pot_val
                self.sensor_data['distance'] = ping_val
                self.sensor_data['switch'] = switch_val
                time.sleep(0.1)

    def _link_worker(self):
        while self._run:
            for i, out in self.links:
                if out == 'led':
                    val = self.sensor_data[i[0]] / i[1]
                    LED.output(val)
                if out == 'servo':
                    val = self.sensor_data[i[0]] / i[1]
                    SERVO.set(val)
                if out == 'motor':
                    val = self.sensor_data[i[0]] / i[1]
                    MOTOR.output(val)
            time.sleep(0.1)

    def _handle_request(self, request):
        if 'out' in request:
            out = request['out']
            if u'servo_value' in out:
                val = out[u'servo_value'] / 100.0
                SERVO.set(val)
            if u'led_value' in out:
                val = out[u'led_value'] / 100.0
                LED.output(val)
            if u'motor_value' in out:
                val = out[u'motor_value'] / 100.0
                MOTOR.output(val)
        if 'add_link' in request:
            print '!link set to:', request['add_link']
            self.links.extend(request['add_link'])
        if 'remove_link' in request:
            print '!link set to:', request['remove_link']
            for link in request['remove_link']:
                self.links.remove(link)



def readadc(adcnum):
    """ read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7).  """

    if ((adcnum > 7) or (adcnum < 0)):
        return -1
    r = spi.xfer2([1,(8+adcnum)<<4,0])
    adcout = ((r[1]&3) << 8) + r[2]
    return adcout

def read_ping_sensor():
    # Send 10us pulse to trigger
    GPIO.output(GPIO_TRIGGER, True)
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)

    start = time.time()
    while GPIO.input(GPIO_ECHO)==0:
        # Wait for echo to go high
        stop = time.time()
        if (stop - start) > .1:
            break

    start = time.time()
    while GPIO.input(GPIO_ECHO)==1:
        # wait for echo to go low
        stop = time.time()
        if (stop - start) > .1:
            break

    # Calculate pulse length
    elapsed = stop - start

    # Distance pulse travelled in that time is time
    # multiplied by the speed of sound (cm/s)
    distance = elapsed * 34300

    # That was the distance there and back so halve the value
    distance = distance / 2

    if distance > 100:
        distance = 100

    return distance
