# -*- coding: utf-8 -*-

import json
import re

from ..Script import Script


class VaryFlowWithHeight(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        # Create settings as an object
        settings = {
            'name': 'Vary Flow With Height',
            'key': 'VaryFlowWithHeight',
            'metadata': {},
            'version': 2,
            'settings': {
                'start_flow': {
                    'label': 'Start Flow',
                    'description': 'Initial nozzle flow',
                    'unit': '%',
                    'type': 'int',
                    'default_value': 105
                },
                'height_increment': {
                    'label': 'Height Increment',
                    'description': (
                        'Adjust flow each time height param '
                        'changes by this much'
                    ),
                    'unit': 'mm',
                    'type': 'int',
                    'default_value': 10
                },
                'flow_increment': {
                    'label': 'Flow Increment',
                    'description': (
                        'Decrease flow by this much with each '
                        'height increment'
                    ),
                    'unit': '%',
                    'type': 'int',
                    'default_value': 2
                }
            }
        }

        # Dump to json string
        json_settings = json.dumps(settings)
        return json_settings

    def execute(self, data):
        # Grab settings variables
        start_flow = self.getSettingValueByKey('start_flow')
        height_inc = self.getSettingValueByKey('height_increment')
        flow_inc = self.getSettingValueByKey('flow_increment')

        # Set our command regex
        cmd_re = re.compile((
            r'G[0-9]+\.?[0-9]* X[0-9]+\.?[0-9]* '
            r'Y[0-9]+\.?[0-9]* Z([0-9]+\.?[0-9]*)'
        ))

        # Set initial state
        output = []
        current_flow = start_flow
        started = False
        z = 0.0
        new_flow = 0

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

                        # Determine new flow
                        new_flow = int(z / height_inc) * flow_inc
                        new_flow = start_flow - new_flow

                        # If we hit a spot where we need to change the
                        # flow, then write the gcode command
                        if new_flow < current_flow:
                            current_flow = new_flow
                            output_line += ';Post-processing: Vary Flow with Height by Fernando Chorney\n'
                            output_line += 'M221 S%d\n' % new_flow
                # output the current line
                output_line += '%s\n' % line
            # Append the current possibly modified layer to the output
            output.append(output_line)
        return output
