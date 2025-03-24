# This program must be execute on robot 

from DRCF import * # type: ignore 

 import powerup.remote as remote # type: ignore

# Start remote API 

remote.start_tcp_remote_api(9225, logging=True)
