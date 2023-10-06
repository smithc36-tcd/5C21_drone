#!/usr/bin/env python3
import logging
import time
from math import degrees
from math import radians

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils import uri_helper
from cflib.utils.multiranger import Multiranger

URI = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E7E7')

def handle_range_measurement(range):
    if range is None:
        range = 999
    return range

if __name__ == '__main__':
    cflib.crtp.init_drivers()
    logging.basicConfig(level=logging.ERROR)

    # Initialize the Crazyflie and Multiranger
    cf = Crazyflie(rw_cache='./cache')
    with SyncCrazyflie(URI, cf=cf) as scf:
        with MotionCommander(scf) as motion_commander:
            with Multiranger(scf) as multiranger:
                while True:
                    # Get front and side range measurements
                    front_range = handle_range_measurement(multiranger.front)
                    left_range = handle_range_measurement(multiranger.left)
                    right_range = handle_range_measurement(multiranger.right)

                    # Define obstacle avoidance logic
                    if front_range < 0.2:  # Obstacle in front, turn right
                        motion_commander.start_linear_motion(0.0, 0.0, 0.0, rate_yaw=45)
                    elif left_range < 0.2:  # Obstacle on the left, turn right
                        motion_commander.start_linear_motion(0.0, 0.0, 0.0, rate_yaw=45)
                    elif right_range < 0.2:  # Obstacle on the right, turn left
                        motion_commander.start_linear_motion(0.0, 0.0, 0.0, rate_yaw=-45)
                    else:
                        # No obstacles, move forward
                        motion_commander.start_linear_motion(0.2, 0.0, 0.0)
                    
                    time.sleep(0.1)  # Control loop rate
