from pymodaq.daq_move.utility_classes import DAQ_Move_base
from pymodaq.daq_move.utility_classes import comon_parameters

from pymodaq.daq_utils.daq_utils import ThreadCommand, getLineInfo
from easydict import EasyDict as edict
from pymodaq.daq_move.utility_classes import DAQ_Move_TCP_server as MoveTCPServer
import sys
import clr


class DAQ_Move_TCPServer(MoveTCPServer):
    """

    """

    def __init__(self,parent=None,params_state=None):
        super().__init__(parent,params_state)
