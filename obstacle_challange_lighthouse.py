import logging
import sys
import time
from threading import Event

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.positioning.position_hl_commander import PositionHlCommander
from cflib.utils import uri_helper
from cflib.utils.power_switch import PowerSwitch
from cflib.crazyflie.high_level_commander import HighLevelCommander


URI = uri_helper.uri_from_env(default='radio://0/57/2M/EE5C21CFA8')

DEFAULT_HEIGHT = 0.5

deck_attached_event = Event()

logging.basicConfig(level=logging.ERROR)

position_estimate = [0, 0]


def test(scf):
    with HighLevelCommander(scf, default_height=DEFAULT_HEIGHT) as HC:
        with PositionHlCommander(scf, default_height=DEFAULT_HEIGHT) as hl:
            HC.go_to(0.5, 0, DEFAULT_HEIGHT, relative=False)
            HC.go_to(0.5, 0.5, DEFAULT_HEIGHT, 180, relative=False)


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
        PowerSwitch(URI).stm_power_cycle()
    else:
        pass


if __name__ == '__main__':
    cflib.crtp.init_drivers()

    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:

        print(URI)

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
        test(scf)
        logconf.stop()
        reboot()
