"""
LECO Director instrument plugin are to be used to communicate (and control) remotely real
instrument plugin through TCP/IP using the LECO Protocol

For this to work a coordinator must be instantiated can be done within the dashboard or directly
running: `python -m pyleco.coordinators.coordinator`

"""
from pymodaq.utils.leco.daq_xDviewer_LECODirector import DAQ_xDViewer_LECODirector, main


class DAQ_0DViewer_LECODirector(DAQ_xDViewer_LECODirector):
    """A control module, which in the dashboard, allows to control a remote Viewer module"""

    def __init__(self, parent=None, params_state=None, grabber_type: str = "0D", **kwargs) -> None:
        super().__init__(parent=parent, params_state=params_state, grabber_type=grabber_type,
                         **kwargs)


if __name__ == '__main__':
    main(__file__, init=False)
