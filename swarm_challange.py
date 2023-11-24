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

# PID = 1
# Mellenger = 2
# INDI = 3
# Brescianini = 4

URI0 = 'radio://0/57/2M/EE5C21CFA8'
URI1 = 'radio://0/57/2M/EE5C21CFF8'
URI2 = 'radio://0/57/2M/EE5C21CFC8'


# d: diameter of circle
# z: altitude
params0 = {'z': 0.3}
params1 = {'z': 0.3}
params2 = {'z': 0.3}


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
# Scale factor for the heart shape
scale_factor = 0.03  # To fit the heart in a 1m^2 box
def poshold(cf, t, z):
  steps = t * 10

  for r in range(steps):
    cf.commander.send_hover_setpoint(0, 0, 0, z)
    time.sleep(0.1)

# Function to run the heart shape sequence
def run_heart_sequence(scf, params):
  cf = scf.cf
  fs = 4  # Number of setpoints sent per second
  fsi = 1.0 / fs
  base = 0.15

  heart_time = 8  # Duration of the heart shape flight
  steps = heart_time * fs
  previous_x = scale_factor * 16 * math.sin(0) ** 3
  previous_y = scale_factor * (13 * math.cos(0) - 5 * math.cos(0) - 2 * math.cos(0) - math.cos(0))

  poshold(cf, 2, base)

  ramp = fs * 2
  for r in range(ramp):
    cf.commander.send_hover_setpoint(0, 0, 0, 0)
    time.sleep(fsi)

  z = params['z']

  poshold(cf, 2, z)

  for i in range(1, steps):
    t = (2 * math.pi * i) / steps  # t goes from 0 to 2π

    # Calculate x and y positions using the heart equations
    x = 16 * math.sin(t) ** 3
    y = 13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t)

    # Apply the scale factor
    x_scaled = scale_factor * x
    y_scaled = scale_factor * y

    # Calculate velocities
    vx = (x_scaled - previous_x) / fsi
    vy = (y_scaled - previous_y) / fsi

    # Update previous x and y for the next iteration
    previous_x = x_scaled
    previous_y = y_scaled

    # Send the hover setpoint to the drone
    cf.commander.send_hover_setpoint(vx, vy, 0, params['z'])
    time.sleep(fsi)

  poshold(cf, 2, z)

  for r in range(ramp):
    cf.commander.send_hover_setpoint(0, 0, 0,0)
    time.sleep(fsi)

  poshold(cf, 1, base)

  cf.commander.send_stop_setpoint()
  cf.commander.send_notify_setpoint_stop()

# Function to generate the heart shape velocities
def generate_heart_shape_velocities(scale_factor, steps, fsi):
  vx_coords = []
  vy_coords = []

  previous_x = scale_factor * 16 * np.sin(0) ** 3
  previous_y = scale_factor * (13 * np.cos(0) - 5 * np.cos(0) - 2 * np.cos(0) - np.cos(0))

  for i in range(1, steps):
    t = (2 * np.pi * i) / steps  # t goes from 0 to 2π

    x = 16 * np.sin(t) ** 3
    y = 13 * np.cos(t) - 5 * np.cos(2*t) - 2 * np.cos(3*t) - np.cos(4*t)

    x_scaled = scale_factor * x
    y_scaled = scale_factor * y

    vx = (x_scaled - previous_x) / fsi
    vy = (y_scaled - previous_y) / fsi

    previous_x = x_scaled
    previous_y = y_scaled

    vx_coords.append(vx)
    vy_coords.append(vy)

  return vx_coords, vy_coords

def generate_heart_shape_positions(scale_factor, steps):
  x_coords = []
  y_coords = []
  
  for i in range(steps):
    t = (2 * np.pi * i) / steps  # t goes from 0 to 2π

    # Calculate x and y positions using the heart equations
    x = 16 * np.sin(t) ** 3
    y = 13 * np.cos(t) - 5 * np.cos(2*t) - 2 * np.cos(3*t) - np.cos(4*t)

    # Apply the scale factor
    x_scaled = scale_factor * x
    y_scaled = scale_factor * y

    x_coords.append(x_scaled)
    y_coords.append(y_scaled)

  return x_coords, y_coords

# Plotting function for velocities
def plot_velocities(vx_coords, vy_coords):
  plt.figure()

  plt.subplot(1, 2, 1)
  plt.plot(vx_coords, color='blue')
  plt.title("X Velocities")
  plt.xlabel("Step")
  plt.ylabel("Velocity (m/s)")
  plt.grid(True)

  plt.subplot(1, 2, 2)
  plt.plot(vy_coords, color='green')
  plt.title("Y Velocities")
  plt.xlabel("Step")
  plt.ylabel("Velocity (m/s)")
  plt.grid(True)

  plt.tight_layout()
  plt.show()

# Function to plot position graph with velocity vectors
def plot_position_with_velocity_vectors(x_coords, y_coords, vx_coords, vy_coords, step_interval):

  plt.figure(figsize=(8, 8))
  plt.plot(x_coords, y_coords, color='red', label='Flight Path')

  # Plot velocity vectors every 'step_interval' steps
  for i in range(0, len(x_coords), step_interval):
    # Calculate the magnitude of the velocity vector
    velocity_magnitude = np.sqrt(vx_coords[i]**2 + vy_coords[i]**2)

    # Normalize the velocity components to represent the direction
    if velocity_magnitude != 0:
      vx_norm = vx_coords[i] / velocity_magnitude
      vy_norm = vy_coords[i] / velocity_magnitude
    else:
      vx_norm, vy_norm = 0, 0

    # Plot the vector with length equal to the velocity magnitude
    plt.arrow(x_coords[i], y_coords[i], vx_norm * velocity_magnitude, vy_norm * velocity_magnitude, 
              head_width=0.02, head_length=0.03, fc='blue', ec='blue')

  plt.title("Position Graph with Velocity Vectors")
  plt.xlabel("X Coordinate (meters)")
  plt.ylabel("Y Coordinate (meters)")
  plt.grid(True)
  plt.axis('equal')
  plt.legend()
  plt.show()


if __name__ == '__main__':
    cflib.crtp.init_drivers()

    # Parameters for plotting
    fs = 40  # Frequency of updates
    fsi = 1.0 / fs
    heart_time = 8  # Duration of the heart shape flight
    steps = heart_time * fs

    # # Generate velocities for the heart shape path
    # vx_coords, vy_coords = generate_heart_shape_velocities(scale_factor, steps, fsi)

    # # Generate positions for the heart shape path
    # x_coords, y_coords = generate_heart_shape_positions(scale_factor, steps)

    # # Plotting the velocities
    # plot_velocities(vx_coords, vy_coords)

    # # Plotting the position graph with velocity vectors
    # plot_position_with_velocity_vectors(x_coords, y_coords, vx_coords, vy_coords, 10)  # Vector every 10 steps

    # Run the actual drone flight sequence (commented out for safety)
    factory = CachedCfFactory(rw_cache='./cache')
    with Swarm(uris, factory=factory) as swarm:
       swarm.reset_estimators()
       swarm.parallel(run_heart_sequence, args_dict=params)


