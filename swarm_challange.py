import time

import cflib.crtp
from cflib.crazyflie.swarm import CachedCfFactory
from cflib.crazyflie.swarm import Swarm
from cflib.positioning.position_hl_commander import PositionHlCommander
import numpy as np


# PID = 1
# Mellenger = 2
# INDI = 3
# Brescianini = 4

DEFAULT_HEIGHT = 0.5

def activate_mellinger_controller(scf, use_mellinger):
    controller = 1
    if use_mellinger:
        controller = 2
    scf.cf.param.set_value('stabilizer.controller', controller)

def gen_heart(num_points):

  points = []
  
  for i in range(0, num_points):

    t = (i / num_points) * 2 * np.pi
    
    x = 16 * np.power(np.sin(t), 3)
    y = 13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t)

    points.append([x, y])

  return points


def heart(scf):
    with PositionHlCommander(scf, default_height=DEFAULT_HEIGHT) as hl:
        points = gen_heart(50)
        for i in range (len(points)):
            hl.go_to(points[i][0]/20, points[i][1]/20)

def swarm_heart(scf):
    activate_mellinger_controller(scf, True)

    commander = scf.cf.high_level_commander
    points = gen_heart(50)

    commander.takeoff(1.0, 2.0)
    time.sleep(3)

    for i in range (len(points)):
        commander.go_to(points[i][0]/20, points[i][1]/20, 0, 0, 0.1, relative=True)

    commander.land(0.0, 2.0)
    time.sleep(2)

    commander.stop()

def run_shared_sequence(scf):
    activate_mellinger_controller(scf, True)

    box_size = 0.5
    flight_time = 2

    commander = scf.cf.high_level_commander

    commander.takeoff(1.0, 2.0)
    time.sleep(3)

    commander.go_to(box_size, 0, 0, 0, flight_time, relative=True)
    time.sleep(flight_time)

    commander.go_to(0, box_size, 0, 0, flight_time, relative=True)
    time.sleep(flight_time)

    commander.go_to(-box_size, 0, 0, 0, flight_time, relative=True)
    time.sleep(flight_time)

    commander.go_to(0, -box_size, 0, 0, flight_time, relative=True)
    time.sleep(flight_time)

    commander.land(0.0, 2.0)
    time.sleep(2)

    commander.stop()


uris = {
    #'radio://0/57/2M/EE5C21CFC8',
    'radio://0/57/2M/EE5C21CFA8',
    'radio://0/57/2M/EE5C21CFF8',
    # Add more URIs if you want more copters in the swarm
}

if __name__ == '__main__':
    cflib.crtp.init_drivers()

    factory = CachedCfFactory(rw_cache='./cache')
    with Swarm(uris, factory=factory) as swarm:
        swarm.reset_estimators()
        swarm.parallel_safe(swarm_heart)
