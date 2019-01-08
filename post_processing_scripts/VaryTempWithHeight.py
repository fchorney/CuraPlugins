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
            "name": "Vary Temp With Height",
            "key": "VaryTempWithHeight",
            "metadata": {},
            "version": 2,
            "settings": {
                "start_temperature": {
                    "label": "Start Temperature",
                    "description": "Sets the initial nozzle temperature",
                    "unit": "°C",
                    "type": "int",
                    "default_value": 225,
                },
                "height_increment": {
                    "label": "Height Increment",
                    "description": (
                        "Adjust temperature each time the z height "
                        "changes by this much"
                    ),
                    "unit": "mm",
                    "type": "int",
                    "default_value": 10,
                },
                "temperature_decrement": {
                    "label": "Temperature decrement",
                    "description": (
                        "Decrease temperature by this much with each "
                        "height increment"
                    ),
                    "unit": "°C",
                    "type": "int",
                    "default_value": 5,
                },
                "height_buffer": {
                    "label": "Height Buffer",
                    "description": (
                        "Add a buffer to the bottom of the model where no "
                        "temperature changes will happen. Temperature changes "
                        "will start above the height buffer that you have set"
                    ),
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0.0,
                },
            },
        }

        # Dump to json string
        json_settings = json.dumps(settings)
        return json_settings

    def execute(self, data):
        # Grab settings variables
        start_temp = self.getSettingValueByKey("start_temperature")
        height_inc = self.getSettingValueByKey("height_increment")
        temp_dec = self.getSettingValueByKey("temperature_decrement")
        height_buf = self.getSettingValueByKey("height_buffer")

        # Set our command regex
        # ex. G0 X60.989 Y60.989 Z1.77
        # ex. G0 F7200 X104.295 Y112.483 Z11.1
        cmd_re = re.compile(
            (
                r"G[0-9]+\.?[0-9]* (?:F[0-9]+\.?[0-9]* )?"
                r"X[0-9]+\.?[0-9]* Y[0-9]+\.?[0-9]* Z([0-9]+\.?[0-9]*)"
            )
        )

        # Set initial state
        output = []
        current_temp = start_temp
        started = False
        z = 0.0
        new_temp = 0
        set_initial = False

        # Cycle through each line of G-Code
        for layer in data:
            output_line = ""
            for line in layer.split("\n"):
                # If we see LAYER:0, this means we are in the main layer code
                if "LAYER:0" in line:
                    started = True

                # output any comment lines or pre-start lines
                # without modification
                if line.startswith(";") or not started:
                    output_line += "%s\n" % line
                    continue

                # Find the X,Y,Z Line
                match = cmd_re.search(line)

                # If we've found our line
                if match is not None:
                    # Grab the z value
                    new_z = float(match.groups()[0]) - height_buf

                    # If our z value has changed
                    if new_z != z:
                        z = new_z
                        layer = int(z / height_inc)

                        # Check if we're on the initial layer, or below our height
                        # buffer
                        if layer <= 0:
                            # If we haven't written out the initial temperature yet, do
                            # it here
                            if not set_initial:
                                set_initial = True
                                output_line += write_temp(start_temp)

                        # Determine new temperature
                        new_temp = start_temp - (layer * temp_dec)

                        # If we hit a spot where we need to change the
                        # temperature, then write the gcode command
                        if new_temp < current_temp:
                            current_temp = new_temp
                            output_line += write_temp(new_temp)
                # output the current line
                output_line += "%s\n" % line
            # Append the current possibly modified layer to the output
            output.append(output_line)
        return output


def write_temp(temp):
    return ";TYPE:CUSTOM\nM104 S%d\n" % temp
