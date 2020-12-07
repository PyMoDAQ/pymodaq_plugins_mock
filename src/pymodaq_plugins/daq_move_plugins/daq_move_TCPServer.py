from pymodaq.daq_move.utility_classes import DAQ_Move_TCP_server as MoveTCPServer


class DAQ_Move_TCPServer(MoveTCPServer):
    """

    """

    def __init__(self, parent=None, params_state=None):
        super().__init__(parent, params_state)
