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

class Rebar:
    def __init__(self, type: str, id: str=None):
        self.type = type
        self.diameter = self.get_diameter()
        self.is_soportada = False
        self.is_corner = False
        self.has_crosstie = False
        self.id = id

    def set_coord_x(self, coord_x: float):
        self.coord_x = coord_x

    def set_coord_y(self, coord_y: float):
        self.coord_y = coord_y

    def get_diameter(self):
        for bar in REBAR_PROPERTIES_MM:
            if bar['type'] == self.type:
                return bar['diameter']
        return None
    
    def get_coords(self):
        return (self.coord_x, self.coord_y)