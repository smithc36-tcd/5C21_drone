import logging
import sys
import time
from threading import Event

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils import uri_helper
from cflib.utils.power_switch import PowerSwitch


URI = uri_helper.uri_from_env(default='radio://0/57/2M/EE5C21CFA8')

DEFAULT_HEIGHT = 0.5

deck_attached_event = Event()

logging.basicConfig(level=logging.ERROR)

position_estimate = [0, 0]


def move_linear_simple(scf):
    with MotionCommander(scf, default_height=DEFAULT_HEIGHT) as mc:
        time.sleep(1)
        mc.forward(0.5)
        time.sleep(1)
        mc.turn_left(180)
        time.sleep(1)
        mc.forward(0.5)
        time.sleep(1)


def take_off_simple(scf):
    with MotionCommander(scf, default_height=DEFAULT_HEIGHT) as mc:
        time.sleep(1)
        mc.stop()


def test(scf):
    with MotionCommander(scf, default_height=DEFAULT_HEIGHT) as mc:
        # @ 0.5m
        mc.left(0.5, 0.25)
        mc.forward(0.5, 0.25)
        mc.up(0.5, 0.25)
        # @ 1m
        mc.move_distance(-1, -1, 0, 0.25)
        mc.down(0.5, 0.25)
        mc.forward(0.5, 0.25)
        mc.left(0.5, 0.25)
        mc.circle_right(0.25, 0.25, 360)
        mc.circle_left(0.25, 0.25, 360)


def log_pos_callback(timestamp, data, logconf):
    print(data)
    global position_estimate
    position_estimate[0] = data['stateEstimate.x']
    position_estimate[1] = data['stateEstimate.y']


def param_deck_flow(name, value_str):
    value = int(value_str)
    print(value)
    if value:
        deck_attached_event.set()
        print('Deck is attached!')
    else:
        print('Deck is NOT attached!')


def reboot():
    if URI is not None:
        PowerSwitch(sys.argv[1]).stm_power_cycle()
    else:
        pass


if __name__ == '__main__':
    cflib.crtp.init_drivers()

    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:

        scf.cf.param.add_update_callback(group='deck', name='bcZRanger2',
                                         cb=param_deck_flow)
        time.sleep(1)

        logconf = LogConfig(name='Position', period_in_ms=10)
        logconf.add_variable('stateEstimate.x', 'float')
        logconf.add_variable('stateEstimate.y', 'float')
        scf.cf.log.add_config(logconf)
        logconf.data_received_cb.add_callback(log_pos_callback)

        if not deck_attached_event.wait(timeout=5):
            print('No flow deck detected!')
            sys.exit(1)

        logconf.start()

        # move_linear_simple(scf)
        # take_off_simple(scf)
        test(scf)
        logconf.stop()
        reboot()
