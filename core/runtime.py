import os
import json
import subprocess
import json


class Config(object):
    runtime = os.path.join("runtime")
    notepad = "notepad.exe"


class Parameter(object):
    _data = None

    def __init__(self, data):
        self._data = data

    def json(self):
        return json.loads(self._data)

    def data(self):
        return self._data


class Space(object):
    _space = None

    def __init__(self, space):
        self._space = space

    #
    def parameter(self, file):
        _space_file = os.path.join(self._space, file)
        if os.path.isfile(_space_file) is False:
            open(_space_file, 'w')
            subprocess.call([Config.notepad, _space_file])
        with open(_space_file, 'r') as _parameter:
            return Parameter(_parameter.read())


class Setting(object):

    @classmethod
    def space(cls, name):
        _space = os.path.join(Config.runtime, name)
        os.makedirs(_space, exist_ok=True)
        return Space(_space)
