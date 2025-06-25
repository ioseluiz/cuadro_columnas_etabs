from .column import RectangularColumn

class Detail:
    def __init__(self, name:str,origin: tuple[int],width: int, height: int):
        self.name = name
        self.width = width
        self.height = height
        self.origin = origin # tuple (x,y)
        self.rectangle_area_coord = self.get_coordinates_detail_area() # list of tuples with coord x,y
        # self.title_coor = self.get_coordinates_title() # tuple (x,y)
        self.center_point = self.get_area_center_point() # tuple (x,y)
        

    def get_coordinates_detail_area(self):
        coordinates = [
            (self.origin[0], self.origin[1]),
            (self.origin[0] + self.width, self.origin[1]),
            (self.origin[0] + self.width, self.origin[1] - self.height),
            (self.origin[0], self.origin[1] -  self.height),
            (self.origin[0], self.origin[1])
        ]
        return coordinates
    
    def get_coordinates_title(self):
        coordinates = (self.column.origin[0]+self.column.width/2 - 100, self.column.origin[1] - self.column.height-180-200)
        return coordinates
    
    def get_area_center_point(self):
        center_point = (
            self.origin[0] + self.width/2,
            self.origin[1] - self.height/2
        )

        return center_point
    
    def set_column(self, column: RectangularColumn):
        self.column = column

    def set_origin_for_col(self, col_width, col_heigth):
        self.origin_for_col = (
            self.center_point[0] - self.column.width/2,
            self.center_point[1] + self.column.height/2,
        )
        self.column.set_origin_point(self.origin_for_col)
        # Column
        self.column.get_column_coordinates()
        # Longitudinal Rebar
        self.column.set_rebar_r2_coordinates()
        self.column.set_rebar_r3_coordinates()
        # Outer Stirrup
        self.column.set_main_stirrup_inner_vert_left_coordinates()
        self.column.set_main_stirrup_outer_vert_left_coordinates()
        self.column.set_main_stirrup_inner_vert_right_coordinates()
        self.column.set_main_stirrup_outer_vert_right_coordinates()
        self.column.set_main_stirrup_inner_horizontal_top_coordinates()
        self.column.set_main_stirrup_outer_horizontal_top_coordinates()
        self.column.set_main_stirrup_inner_horizontal_bottom_coordinates()
        self.column.set_main_stirrup_outer_horizontal_bottom_coordinates()
        # Arcs
        self.column.set_top_right_arc()
        self.column.set_top_left_arc()
        self.column.set_bottom_left_arc()
        self.column.set_bottom_right_arc()
        #Corner Hook
        self.column.set_corner_hook()
        # Crossties
        self.column.generar_cross_ties()
        # Title Position
        self.title_coor = self.get_coordinates_title() # tuple (x,y)