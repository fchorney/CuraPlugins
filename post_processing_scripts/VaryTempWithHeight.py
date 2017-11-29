# -*- coding: utf-8 -*-

import json
import re

from ..Script import Script


class VaryTempWithHeight(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        # Create settings as an object
        settings = {
            'name': 'Vary Temp With Height',
            'key': 'VaryTempWithHeight',
            'metadata': {},
            'version': 2,
            'settings': {
                'start_temperature': {
                    'label': 'Start Temperature',
                    'description': 'Initial nozzle temperature',
                    'unit': '°C',
                    'type': 'int',
                    'default_value': 200
                },
                'height_increment': {
                    'label': 'Height Increment',
                    'description': (
                        'Adjust temperature each time height param '
                        'changes by this much'
                    ),
                    'unit': 'mm',
                    'type': 'int',
                    'default_value': 10
                },
                'temperature_increment': {
                    'label': 'Temperature Increment',
                    'description': (
                        'Decrease temperature by this much with each '
                        'height increment'
                    ),
                    'unit': '°C',
                    'type': 'int',
                    'default_value': 4
                }
            }
        }

        # Dump to json string
        json_settings = json.dumps(settings)
        return json_settings

    def execute(self, data):
        # Grab settings variables
        start_temp = self.getSettingValueByKey('start_temperature')
        height_inc = self.getSettingValueByKey('height_increment')
        temp_inc = self.getSettingValueByKey('temperature_increment')

        # Set our command regex
        cmd_re = re.compile((
            r'G[0-9]+\.?[0-9]* X[0-9]+\.?[0-9]* '
            r'Y[0-9]+\.?[0-9]* Z([0-9]+\.?[0-9]*)'
        ))

        # Set initial state
        output = []
        current_temp = start_temp
        started = False
        z = 0.0
        new_temp = 0

        for layer in data:
            output_line = ''
            for line in layer.split('\n'):
                # If we see LAYER:0, this means we are in the main layer code
                if 'LAYER:0' in line:
                    started = True

                # output any comment lines or pre-start lines
                # without modification
                if line.startswith(';') or not started:
                    output_line += '%s\n' % line
                    continue

                # Find the X,Y,Z Line (ex. G0 X60.989 Y60.989 Z1.77)
                match = cmd_re.search(line)

                # If we've found our line
                if match is not None:
                    # Grab the z value
                    new_z = float(match.groups()[0])

                    # If our z value has changed
                    if new_z != z:
                        z = new_z

                        # Determine new temperature
                        new_temp = int(z / height_inc) * temp_inc
                        new_temp = start_temp - new_temp

                        # If we hit a spot where we need to change the
                        # temperature, then write the gcode command
                        if new_temp < current_temp:
                            current_temp = new_temp
                            output_line += ';TYPE:CUSTOM\n'
                            output_line += 'M104 S%d\n' % new_temp
                # output the current line
                output_line += '%s\n' % line
            # Append the current possibly modified layer to the output
            output.append(output_line)
        return output
