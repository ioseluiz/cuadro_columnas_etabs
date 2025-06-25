from .rebar import Rebar

REBAR_PROPERTIES_MM = [
    {'type': '#2', 'diameter': 6.350},
    {'type': '#3', 'diameter': 9.525},
    {'type': '#4', 'diameter': 12.7},
    {'type': '#5', 'diameter': 15.875},
    {'type': '#6', 'diameter': 19.05},
    {'type': '#7', 'diameter': 22.225},
    {'type': '#8', 'diameter': 25.40},
    {'type': '#9', 'diameter': 28.65},
    {'type': '#10', 'diameter': 32.26},
    {'type': '#11', 'diameter': 35.81},
    {'type': '#14', 'diameter': 43.00},
]

class Stirrup:
    def __init__(self, rebar_type):
        self.rebar_type = rebar_type
        self.diameter = self.get_diameter() # rebar diameter in mm

    def get_diameter(self):
        for bar in REBAR_PROPERTIES_MM:
            if bar['type'] == self.rebar_type:
                return bar['diameter']
        return None