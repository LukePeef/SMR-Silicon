from DRCF import *  # Doosan API
import powerup.remote as remote  # Remote control module
set_digital_output(1,OFF)
def wait_touch():
    c1 = True
    while c1:
        c1 = check_force_condition(axis=DR_AXIS_Z, max=10, ref=DR_TOOL)

start = posj(181.3, 5.4, -144.5, -355.1, 46.4, -88.2)
movej(start, v=20, a=20)
lid =posj(222.3, -9.9, -154.2, -356.8, 69.8, -88.2)
downpos = posj(222.8, -38.0, -156.3, -358.2, 100.3, -88.2)
movej(lid, v= 20, a = 20)
amovej(downpos, v=5 , a=10)
wait_touch()
stop(DR_QSTOP)
set_digital_output(1,ON)
# sleep(5000)
# set_digital_output(1,OFF)
sleep(1000)
down = posj(175.8, -29.7, -153.6, -360.1, 88.4, -88.2)
movej(lid, v=10,a=20)
sleep(1000)
movej(start, v=20, a=20)
movej(down, v=10, a=20)
set_digital_output(1,OFF)
movej(start, v=20, a=20)

#remote.start_tcp_remote_api(9225, logging=True)

