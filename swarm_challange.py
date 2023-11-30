import time

import cflib.crtp
from cflib.crazyflie.swarm import CachedCfFactory
from cflib.crazyflie.swarm import Swarm
from cflib.positioning.position_hl_commander import PositionHlCommander
from cflib.crazyflie.high_level_commander import HighLevelCommander
from cflib.crazyflie.commander import Commander
from cflib.crazyflie.mem import CompressedSegment
from cflib.crazyflie.mem import CompressedStart
from cflib.crazyflie.mem import MemoryElement
import numpy as np
import math
import sys
import matplotlib.pyplot as plt

URI0 = 'radio://0/57/2M/EE5C21CFF8'
URI1 = 'radio://0/57/2M/EE5C21CFA8'
URI2 = 'radio://0/57/2M/EE5C21CFC8'

# z: altitude
params0 = {'id': 0, 'z': 0.3}
params1 = {'id': 2, 'z': 0}
params2 = {'id': 1, 'z': -0.3}


uris = {
    URI0,
    URI1,
    URI2,
}

params = {
    URI0: [params0],
    URI1: [params1],
    URI2: [params2],
}

# Scales x and y points to fit within a square of length 'size'. Maintains aspect ratio.
def scale(points, size):

  if max(points[:, 0]) > max(points[:, 1]):
    points = points * size / (max(points[:, 0]) - min(points[:, 0]))
  else:
    points = points * size / (max(points[:, 1]) - min(points[:, 1]))

  return points

# Generate points for a heart using a parametric equation I stole from desmos.
def gen_heart(num_points, size):

  points = np.zeros((num_points, 2))

  for i in range(0, num_points):

    t = (i / num_points) * 2 * np.pi

    x = 16 * np.power(np.sin(t), 3)
    y = 13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t)

    points[i, 0] = x
    points[i, 1] = y

  return scale(points, size)

# Generate points for a C, this uses the parametric equation for a circle with a
# the range of t set to -2 > t > 2
def gen_c(num_points, size):

  points = np.zeros((num_points, 2))

  t = np.arange(-2.5, 2.5, 5 / num_points)

  points[:, 0] = -1 * np.cos(t)
  points[:, 1] = -1 * np.sin(t)

  return scale(points, size)

# Generate points for an M, this is just hardcoded and scaled.
def gen_m(size):

  points = np.zeros((5, 2))

  points[:, 0] = np.array([-1, -0.75, 0, 0.75, 1])
  points[:, 1] = np.array([-1, 1, 0.25, 1, -1])

  return scale(points, size)

# Generate points for a heart, C and M. 'size' will be the maximum space required 
# to display the points.
def swarm_points(size):

  heart_points = gen_heart(50, size)
  c_points = gen_c(20, size / 5)
  m_points = gen_m(size / 5)

  c_points[:, 0] = c_points[:, 0] - size / 6
  m_points[:, 0] = m_points[:, 0] + size / 6

  return heart_points, c_points, m_points

# Calculates the total length of a path in metres. Can be used to inform velocity.
def path_length(points):

  length = 0

  for i in range(0, len(points[:, 1]) - 1):

    xlen = points[i + 1, 0] - points[i, 0]
    ylen = points[i + 1, 1] - points[i, 1]

    length += np.sqrt(np.power(xlen, 2) + np.power(ylen, 2))

  return np.round(length, 2)

# Run each individual path using the High Level Commander
def run_path(scf, points, velocity):
  with PositionHlCommander(scf) as hl:
    hl.go_to(points[0][0], points[0][1], 0.5, velocity)
    time.sleep(3)
    for i in range (len(points)-1):
      hl.go_to(points[i+1][0], points[i+1][1], 0.5, velocity)
    time.sleep(15)

# Function to split into different threads for each drone.
def swarm_path(scf, params):

  heart_points, c_points, m_points = swarm_points(1.8)

  if params['id'] == 0:
    run_path(scf, heart_points, path_length(heart_points) / 10)
  elif params['id'] == 1:
    run_path(scf, c_points, path_length(c_points)*1.2 / 10)
  elif params['id'] == 2:
    run_path(scf, m_points, path_length(m_points)*1.3 / 10)


if __name__ == '__main__':
    cflib.crtp.init_drivers()

    # Run the actual drone flight sequence (commented out for safety)
    factory = CachedCfFactory(rw_cache='./cache')
    with Swarm(uris, factory=factory) as swarm:
      swarm.reset_estimators()
      swarm.parallel(swarm_path, args_dict=params)



