def test(scf):
    mc = MotionCommander(scf, default_height=DEFAULT_HEIGHT)

    # 环绕墙
    mc.forward(0.5, 0.5)
    mc.circle_left(0.5, 0.5, 180)
    mc.forward(1, 0.5)
    mc.circle_left(0.5, 0.5, 180)
    mc.forward(0.5, 0.5)
    # 环绕墙
    mc.forward(0.5, 0.5)
    mc.circle_right(0.5, 0.5, 180)
    mc.forward(0.8, 0.5)
    mc.turn_right(90, 45)
    # 越过墙
    mc.up(0.7, 0.5)
    mc.forward(0.90, 0.5)

    mc.stop()  # 停止 MotionCommander 实例

    # 使用 PositionHlCommander 降落到 (0, 0)
    with PositionHlCommander(scf, default_height=DEFAULT_HEIGHT) as hl:
        hl.go_to(0, 0, 0.5, 0.5)

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
