import re
import subprocess


class Sensors():

    def __init__(self):
        super().__init__()
        self._adapter = None
        self._new_adapter = True

    def read(self, response=None):
        ''' Read lm-sensors by calling `sensors -u`

        Parameters:
            respsonse (dict, optional): If included, returned dict includes
                these values. This dict is manipulated as well.

        Returns:
            sensors values (dict):
                Dictionary of sensors names (str) and values (float)
        '''
        if response is None:
            response = {}
        sensors = \
            subprocess.check_output("sensors -u", shell=True).strip().decode()
        lines = sensors.splitlines()
        for line in lines:
            adapter = self._get_adapter(line)
            temp = self._get_temp(line)
            if temp:
                temp_name = "{}_{}_{}".format('sensors', adapter, temp[0])
                response[temp_name] = temp[1]
        return response

    def _get_adapter(self, line):
        ''' Get the adapter for the line that we're on '''
        if self._new_adapter:
            # it's a new adapter, save it.
            self._adapter = line
            self._new_adapter = False
        elif not bool(line):
            # a blank line means we're starting a new adpater next
            self._new_adapter = True
        return self._adapter

    def _get_temp(self, line):
        ''' Get the temperature if this is a temperature line

        Returns: (temp_name(str), temp_value(float))
        '''
        line = line.strip()
        if line.startswith('temp'):
            reg = re.match("^(.*?)\:\s+(.*?)$", line)
            if reg:
                return (reg.group(1), float(reg.group(2)))


if __name__ == "__main__":
    s = Sensors()
    r = {'test_key': 'test_value'}
    try:
        print(s.read(r))
        print(r)
    except subprocess.CalledProcessError:
        print('Looks like lm-sensors is not installed')
