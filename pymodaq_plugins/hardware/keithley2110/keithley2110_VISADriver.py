import pyvisa as visa


class Keithley2110VISADriver:
    """
        VISA class driver for the Keithley 2110  5 1/2 Digit DMM
        This class relies on pyvisa module to communicate with the instrument via VISA protocol
        Please refer to the instrument reference manual available at:
        https://download.tek.com/manual/2110-901-01(C-Aug2013)(Ref).pdf
    """
    def __init__(self, rsrc_name, pyvisa_backend='@ni'):
        """
        Parameters
        ----------
        rsrc_name   (string)        VISA Resource name
        pyvisa_backend  (string)    Expects a pyvisa backend identifier or a path to the visa backend dll (ref. to pyvisa)
        """
        rm = visa.highlevel.ResourceManager(pyvisa_backend)
        self._instr = rm.open_resource(rsrc_name)

        self._instr.read_termination = '\n'
        self._instr.write_termination = '\n'

    def close(self):
        self._instr.close()

    def get_identification(self):
        self._instr.query("*IDN?")

    def reset(self):
        self._instr.write("*CLS")
        self._instr.write("*RST")

    def read(self):
        return float(self._instr.query("READ?"))

    def set_mode(self, mode, **kwargs):
        """

        Parameters
        ----------
        mode    (string)    Measurement configuration ('VDC', 'VAC', 'IDC', 'IAC', 'R2W' and 'R4W' modes are supported)
        kwargs  (dict)      Used to pass optional arguments ('range' and 'resolution' are the only supported keys)

        Returns
        -------

        """
        assert (isinstance(mode, str))
        mode = mode.lower()

        cmd = ':CONF:'

        if mode == "Ohm2".lower() or mode == "R2W".lower():
            cmd += "RES"
        elif mode == "Ohm4".lower() or mode == "R4W".lower():
            cmd += "FRES"
        elif mode == "VDC".lower() or mode == "V".lower():
            cmd += "VOLT:DC"
        elif mode == "VAC".lower():
            cmd += "VOLT:AC"
        elif mode == "IDC".lower() or mode == "I".lower():
            cmd += "CURR:DC"
        elif mode == "IAC".lower():
            cmd += "CURR:AC"

        if 'range' in kwargs.keys():
            cmd += ' ' + str(kwargs['range'])
            if 'resolution' in kwargs.keys():
                cmd += ',' + str(kwargs['resolution'])
        elif 'resolution' in kwargs.keys():
            cmd += ' DEF,' + str(kwargs['resolution'])

        self._instr.write(cmd)


if __name__ == "__main__":
    try:
        k2110 = Keithley2110VISADriver("K2110")
        k2110.reset()
        k2110.set_mode('Ohm2')
        k2110.set_mode('R4W', range=10, resolution='MAX')
        k2110.set_mode('R4W', resolution='MIN')
        k2110.set_mode('IAC', range=0.001, resolution='MIN')
        k2110.set_mode('vdc', range=0.1, resolution='0.0001')

        print(k2110.read())

        k2110.close()

    except Exception as e:
        print("Exception ({}): {}".format(type(e), str(e)))
