"""
LECO Director instrument plugin are to be used to communicate (and control) remotely real
instrument plugin through TCP/IP using the LECO Protocol

For this to work a coordinator must be instantiated can be done within the dashboard or directly
running: `python -m pyleco.coordinators.coordinator`

"""

from pymodaq.utils.leco.daq_move_LECODirector import DAQ_Move_LECODirector, main  # noqa


if __name__ == '__main__':
    main(__file__, init=False)
