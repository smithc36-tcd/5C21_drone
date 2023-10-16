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

def land(scf):
    with PositionHlCommander(scf, default_height=DEFAULT_HEIGHT) as hl:
        hl.go_to(0, 0, 0.5, 0.5)

def lighthouse(scf):
    with PositionHlCommander(scf, default_height=DEFAULT_HEIGHT) as hl:
        hl.go_to(0, 0)
        hl.go_to(0.8, 0)
        hl.go_to(0.8, 0.8)
        hl.go_to(-0.8, 0.8)
        hl.go_to(-0.8, 0)
        hl.go_to(0, 0)


def high_lighthouse(scf):
    hlc = HighLevelCommander()
    hlc._cf = scf.cf
    hlc.takeoff(0.5, 1, 0, 180)
        
   

def test(scf):
    hl = PositionHlCommander(scf, default_height=DEFAULT_HEIGHT)
    with MotionCommander(scf, default_height=DEFAULT_HEIGHT) as mc:    
        # around wall
        mc.forward(0.5, 0.5)
        mc.circle_left(0.5, 0.5, 180)
        mc.forward(1, 0.5)
        mc.circle_left(0.5, 0.5, 180)
        mc.forward(0.5, 0.5)
        # around wall
        mc.forward(0.5, 0.5)
        mc.circle_right(0.5, 0.5, 180)
        mc.forward(0.8, 0.5)
        mc.turn_right(90, 45)
        # over wall
        mc.up(0.7, 0.5)
        #mc.forward(0.90, 0.5)
        hl.go_to(0, 0, 1.2, 0.5)
        time.sleep(10)
        hl.land
        time.sleep(10)





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
        #lighthouse(scf)
        logconf.stop()