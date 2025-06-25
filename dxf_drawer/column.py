from .rebar import Rebar
from .stirrup import Stirrup

import math

MAX_ESPACIAMIENTO_LIBRE_SIN_SOPORTE = 150 #mm

class Arc:
    def __init__(self, center_point: tuple[int], radius: int, start_angle: int, end_angle: int):
        self.center_point = center_point
        self.radius = radius
        self.start_angle = start_angle
        self.end_angle = end_angle

class RectangularColumn:
    def __init__(self, width: int, height: int, fc: str, number_of_bars: int, rebar_type: str, r2_bars: int, r3_bars: int, stirrup_type: str, cover: float):
        self.width = width # mm
        self.height = height # mm
        self.number_of_bars = number_of_bars
        self.rebar_type = rebar_type # Example: #3, #4...#14
        self.r2_bars = r2_bars # Long Direction (Height)
        self.r3_bars = r3_bars # Short Direction (Width)
        self.stirrup_type = stirrup_type
        self.cover = cover # cover in mm
        self.main_stirrup = self.set_stirrup()
        self.rebars = []
        self.rebar_soportadas = []
        self.rebar_no_soportadas = []
        self.coor_y_sup = None # Centro del rebar
        self.coor_y_inf = None # Centro del rebar
        self.coor_x_izq = None # Centro del rebar
        self.coor_x_der = None # Centro del rebar
        self.espaciamiento_rebar_x_center = None
        self.espaciamiento_rebar_x_libre = None
        self.espaciamiento_rebar_y_center = None
        self.espaciamiento_rebar_y_libre = None
        self.crossties_vert = []
        self.crossties_horizontal = []
        self.tie_top_arcs = []
        self.tie_bottom_arcs = []
        self.tie_left_arcs = []
        self.tie_right_arcs = []
        self.tie_top_hook_points = []
        self.tie_bottom_hook_points = []
        self.tie_left_hook_points = []
        self.tie_right_hook_points = []


    def get_rebars(self):
        return self.rebars


    def set_origin_point(self,  origin_point: tuple[int]):
        self.origin= origin_point # tuple (x,y)

    def get_column_coordinates(self):
        self.coordinates = self.set_column_coordinates() # list of tuples (x,y)

    def set_stirrup(self):
        return Stirrup(self.stirrup_type)
 

    def set_column_coordinates(self):
        coordinates = (
            (self.origin[0], self.origin[1]),
            (self.origin[0] + self.width, self.origin[1]),
            (self.origin[0] + self.width, self.origin[1] - self.height),
            (self.origin[0], self.origin[1] - self.height),
            (self.origin[0], self.origin[1])
        )

        return coordinates
    
    def set_rebar_r2_coordinates(self):
        rebar = Rebar(type=self.rebar_type)
        r2_spacing = (self.height - 2 * self.cover - 2 *self.main_stirrup.diameter - rebar.diameter )/(self.r2_bars-1)
        self.espaciamiento_rebar_x_center = r2_spacing
        self.espaciamiento_rebar_x_libre = self.espaciamiento_rebar_x_center - rebar.diameter
        start_x = self.origin[0] + self.cover + self.main_stirrup.diameter + rebar.diameter/2
        start_y = self.origin[1] - self.cover - self.main_stirrup.diameter - rebar.diameter/2
        self.coor_y_sup = start_y
        self.coor_x_izq = start_x
        end_x = self.origin[0] + self.width - self.cover - self.main_stirrup.diameter - rebar.diameter/2
        # end_y = self.origin[1] - self.height + self.cover + self.main_stirrup + rebar.diameter/2
        self.coor_x_der = end_x
        counter = 0
        for x in range(self.r2_bars):
            rebar_1 = Rebar(type=self.rebar_type)
            rebar_1.set_coord_x(start_x)
            rebar_1.set_coord_y(start_y - counter * r2_spacing)
            self.rebars.append(rebar_1)
            rebar_1.id = (2*counter-1)
            rebar_2 = Rebar(type=self.rebar_type)
            rebar_2.set_coord_x(end_x)
            rebar_2.set_coord_y(start_y - counter * r2_spacing)
            rebar_2.id  =(2*counter)
            self.rebars.append(rebar_2)
            if counter == 0 or counter == self.r2_bars - 1:
                rebar_1.is_soportada = True
                rebar_2.is_soportada = True
                rebar_1.is_corner = True
                
                rebar_2.is_corner = True
                
            counter += 1
        self.rebar_counter = counter
    
    def set_rebar_r3_coordinates(self):
        rebar = Rebar(type=self.rebar_type)
        r3_spacing = (self.width - 2*self.cover - 2*self.main_stirrup.diameter - rebar.diameter)/(self.r3_bars-1)
        self.espaciamiento_rebar_y_center = r3_spacing
        self.espaciamiento_rebar_y_libre = self.espaciamiento_rebar_y_center - rebar.diameter
        start_x = self.origin[0] + self.cover + self.main_stirrup.diameter + rebar.diameter/2
        start_y = self.origin[1] - self.cover - self.main_stirrup.diameter - rebar.diameter/2
        end_x = self.origin[0] + self.width - self.cover - self.main_stirrup.diameter - rebar.diameter/2
        end_y = self.origin[1] - self.height + self.cover + self.main_stirrup.diameter + rebar.diameter/2
        self.coor_y_inf = end_y
        counter = 0
        for x in range(self.r3_bars):
            if counter !=0 and counter != (self.r3_bars-1):
                rebar_1 = Rebar(type=self.rebar_type)
                rebar_1.set_coord_x(start_x + counter * r3_spacing)
                rebar_1.set_coord_y(start_y)
                rebar_1.id = self.rebar_counter + (2*counter-1)
                self.rebars.append(rebar_1)
                rebar_2 = Rebar(type=self.rebar_type)
                rebar_2.set_coord_x(start_x + counter * r3_spacing)
                rebar_2.set_coord_y(end_y)
                rebar_2.id = self.rebar_counter + (2*counter)
                self.rebars.append(rebar_2)
            counter += 1

     # Outer Stirrup       
     # Vertical
    def set_main_stirrup_inner_vert_left_coordinates(self):
        rebar = Rebar(type=self.rebar_type)
        start_point = (
            self.origin[0] + self.cover + self.main_stirrup.diameter,
            self.origin[1] - self.cover - self.main_stirrup.diameter - rebar.diameter/2
        )
        end_point = (
            self.origin[0] + self.cover + self.main_stirrup.diameter,
            self.origin[1] - self.height + self.cover + self.main_stirrup.diameter  + rebar.diameter/2
        )
        self.vert_left_leg_inner_points = [start_point, end_point]

    def set_main_stirrup_outer_vert_left_coordinates(self):
        rebar = Rebar(type=self.rebar_type)
        start_point = (
            self.origin[0] + self.cover,
            self.origin[1] - self.cover - self.main_stirrup.diameter  - rebar.diameter/2
        )
        end_point = (
            self.origin[0] + self.cover,
            self.origin[1] - self.height + self.cover + self.main_stirrup.diameter  + rebar.diameter/2
        )
        self.vert_left_leg_outer_points = [start_point, end_point]


    def set_main_stirrup_inner_vert_right_coordinates(self):
        rebar = Rebar(type=self.rebar_type)
        start_point = (
            self.origin[0] + self.width - self.cover - self.main_stirrup.diameter,
            self.origin[1] - self.cover - self.main_stirrup.diameter  - rebar.diameter/2
        )
        end_point = (
            self.origin[0] + self.width - self.cover - self.main_stirrup.diameter,
            self.origin[1] - self.height + self.cover + self.main_stirrup.diameter  + rebar.diameter/2
        )
        self.vert_right_leg_inner_points = [start_point, end_point]

    def set_main_stirrup_outer_vert_right_coordinates(self):
        rebar = Rebar(type=self.rebar_type)
        start_point = (
            self.origin[0] + self.width - self.cover,
            self.origin[1] - self.cover - self.main_stirrup.diameter  - rebar.diameter/2
        )
        end_point = (
            self.origin[0] + self.width - self.cover,
            self.origin[1] - self.height + self.cover + self.main_stirrup.diameter  + rebar.diameter/2
        )
        self.vert_right_leg_outer_points = [start_point, end_point]

    # Horizontal
    def set_main_stirrup_inner_horizontal_top_coordinates(self):
        rebar = Rebar(type=self.rebar_type)
        start_point = (
            self.origin[0] + self.cover + self.main_stirrup.diameter + rebar.diameter/2,
            self.origin[1] - self.cover - self.main_stirrup.diameter
        )
        end_point = (
            self.origin[0] + self.width - self.cover - self.main_stirrup.diameter - rebar.diameter/2,
            self.origin[1] - self.cover - self.main_stirrup.diameter
        )
        self.top_leg_inner_points = [start_point, end_point]

    def set_main_stirrup_outer_horizontal_top_coordinates(self):
        rebar = Rebar(type=self.rebar_type)
        start_point = (
            self.origin[0] + self.cover + self.main_stirrup.diameter + rebar.diameter/2,
            self.origin[1] - self.cover
        )
        end_point = (
            self.origin[0] + self.width - self.cover - self.main_stirrup.diameter - rebar.diameter/2,
            self.origin[1] - self.cover
        )
        self.top_leg_outer_points = [start_point, end_point]

    def set_main_stirrup_inner_horizontal_bottom_coordinates(self):
        rebar = Rebar(type=self.rebar_type)
        start_point = (
            self.origin[0] + self.cover + self.main_stirrup.diameter + rebar.diameter/2,
            self.origin[1] - self.height + self.cover + self.main_stirrup.diameter
        )
        end_point = (
            self.origin[0] + self.width - self.cover - self.main_stirrup.diameter - rebar.diameter/2,
            self.origin[1] - self.height + self.cover + self.main_stirrup.diameter
        )
        self.bottom_leg_inner_points = [start_point, end_point]

    def set_main_stirrup_outer_horizontal_bottom_coordinates(self):
        rebar = Rebar(type=self.rebar_type)
        start_point = (
            self.origin[0] + self.cover + self.main_stirrup.diameter + rebar.diameter/2,
            self.origin[1] - self.height + self.cover
        )
        end_point = (
            self.origin[0] + self.width - self.cover - self.main_stirrup.diameter - rebar.diameter/2,
            self.origin[1] - self.height + self.cover
        )
        self.bottom_leg_outer_points = [start_point, end_point]

    def set_top_right_arc(self):
        rebar = Rebar(type=self.rebar_type)
        center_point = (
            self.origin[0] + self.cover + self.main_stirrup.diameter + rebar.diameter/2,
            self.origin[1] - self.cover - self.main_stirrup.diameter - rebar.diameter/2
        )
        self.arc_tr = Arc(
            center_point=center_point,
            radius = rebar.diameter/2 + self.main_stirrup.diameter,
            start_angle=90,
            end_angle=180
        )
        
    def set_top_left_arc(self):
        rebar = Rebar(type=self.rebar_type)
        center_point = (
            self.origin[0] +  self.width - self.cover - self.main_stirrup.diameter - rebar.diameter/2,
            self.origin[1] - self.cover - self.main_stirrup.diameter - rebar.diameter/2
        )
        self.arc_tl = Arc(
            center_point=center_point,
            radius = rebar.diameter/2 + self.main_stirrup.diameter,
            start_angle=0,
            end_angle=90,
        )
        
    def set_bottom_left_arc(self):
        rebar = Rebar(type=self.rebar_type)
        center_point = (
           self.origin[0] + self.cover + self.main_stirrup.diameter + rebar.diameter/2,
            self.origin[1] - self.height + self.cover + self.main_stirrup.diameter + rebar.diameter/2
        )
        self.arc_bl = Arc(
            center_point=center_point,
            radius = rebar.diameter/2 + self.main_stirrup.diameter,
            start_angle=180,
            end_angle=270
        )
        
    def set_bottom_right_arc(self):
        rebar = Rebar(type=self.rebar_type)
        center_point = (
           self.origin[0] +  self.width - self.cover - self.main_stirrup.diameter - rebar.diameter/2,
            self.origin[1] - self.height + self.cover + self.main_stirrup.diameter + rebar.diameter/2
        )
        self.arc_br = Arc(
            center_point=center_point,
            radius = rebar.diameter/2 + self.main_stirrup.diameter,
            start_angle=270,
            end_angle=0
        )
        
    def set_corner_hook(self):
        # Arc
        rebar = Rebar(type=self.rebar_type)
        center_point = (
             self.origin[0] + self.cover + self.main_stirrup.diameter + rebar.diameter/2,
            self.origin[1] - self.cover - self.main_stirrup.diameter - rebar.diameter/2
        )
        self.hook_arc = Arc(
            center_point=center_point,
            radius = rebar.diameter/2 +self.main_stirrup.diameter,
            start_angle=45,
            end_angle=225
        )
        # Polyline
        angle_degrees = 45
        # convert angle to radians
        angle_radians = math.radians(angle_degrees)
        # Calculate sin 45
        sin_45 = math.sin(angle_radians)
        # Calculate cos 45
        cos_45 = math.cos(angle_radians)
        x_coord = center_point[0] - cos_45*rebar.diameter/2
        y_coord = center_point[1] - sin_45*rebar.diameter/2
        _6db = 3*rebar.diameter
        x1_coord = x_coord + cos_45 * _6db
        y1_coord = y_coord - sin_45 * _6db
        x2_coord = x1_coord - cos_45 * self.main_stirrup.diameter
        y2_coord = y1_coord - sin_45 * self.main_stirrup.diameter
        x3_coord =x2_coord - cos_45 * _6db
        y3_coord = y2_coord + sin_45 * _6db
        self.corner_hook_coords_left = [
            (x_coord, y_coord), 
            (x1_coord, y1_coord),
            (x2_coord, y2_coord),
            (x3_coord, y3_coord),
            
        ]

        x_coord = center_point[0] + cos_45*rebar.diameter/2
        y_coord = center_point[1] + sin_45*rebar.diameter/2
        x1_coord = x_coord + cos_45 * _6db
        y1_coord = y_coord - sin_45 * _6db
        x2_coord = x1_coord + cos_45 * self.main_stirrup.diameter
        y2_coord = y1_coord + sin_45 * self.main_stirrup.diameter
        x3_coord = x2_coord - cos_45 *_6db
        y3_coord = y2_coord + sin_45 * _6db
        self.corner_hook_coords_right = [
            (x_coord, y_coord),
            (x1_coord, y1_coord),
            (x2_coord, y2_coord),
            (x3_coord, y3_coord),
            
            
        ]

    
        

    def calcular_distancia_rebar(self, rebar_1, rebar_2):
        rebar_1_x, rebar_1_y = rebar_1.get_coords()
        rebar_2_x, rebar_2_y = rebar_2.get_coords()
        return math.sqrt((rebar_2_y - rebar_1_y)**2 + (rebar_2_x - rebar_1_x)**2)
    
    # def calcular_distancia_rebar_soportada_mas_cercana(self, rebar_actual, coord_verificar):

    
    def generar_cross_ties(self):
        print(f"Generar Cross Ties col {self.width}x{self.height}")
        counter = 0
        # Revision barras en direccion X (Crossties verticales)

        # Identificar, separar y ordenar las barras de la capa superior
        rebar_capa_sup = []
        for indice, rebar in enumerate(self.rebars):
            if rebar.coord_y == self.coor_y_sup:
                rebar_capa_sup.append(rebar)

        rebar_capa_sup_sorted = sorted(rebar_capa_sup, key=lambda barra: barra.coord_x)
        
        # 2. Iniciar un bucle que se repita hasta que no se añadan nuevos soportes.
        # Esto es clave para que un nuevo crosstie pueda dar soporte a la siguiente barra.
        hubo_cambios = True
        while hubo_cambios:
            hubo_cambios = False
            
            # Obtenemos la lista actualizada de barras ya soportadas en cada iteración.
            barras_ya_soportadas = [b for b in rebar_capa_sup_sorted if b.is_soportada]

            # 3. Recorrer cada barra para ver si necesita soporte.
            for barra_a_revisar in rebar_capa_sup_sorted:
                if not barra_a_revisar.is_soportada:
                    # 4. Calcular la distancia a la barra soportada más cercana.
                    # Se asume que la distancia relevante es en el eje X para barras en una cara.
                    distancia_minima = min(
                        abs(barra_a_revisar.coord_x - b_soportada.coord_x) 
                        for b_soportada in barras_ya_soportadas
                    )

                    # 5. Aplicar la regla del ACI 318-19.
                    if distancia_minima > MAX_ESPACIAMIENTO_LIBRE_SIN_SOPORTE:
                        barra_a_revisar.has_crosstie = True
                        barra_a_revisar.is_soportada = True
                        hubo_cambios = True  # Marcamos que se hizo un cambio para re-evaluar.
                        print(f"INFO: Barra {barra_a_revisar.id} necesita crosstie (distancia_min={distancia_minima:.1f} mm > {MAX_ESPACIAMIENTO_LIBRE_SIN_SOPORTE} mm). Se añade soporte.")


        self.tie_top_arcs = []
        for rebar in rebar_capa_sup_sorted:
            if rebar.has_crosstie == True:
                print(f"Barra {rebar.get_coords()} and is_soportada: {rebar.is_soportada}")
                point_1 = (rebar.coord_x - rebar.diameter/2, rebar.coord_y)
                point_2 = (rebar.coord_x - rebar.diameter/2, self.coor_y_inf)
                point_3 = (point_1[0] - self.main_stirrup.diameter, rebar.coord_y)
                point_4 = (point_2[0] - self.main_stirrup.diameter, self.coor_y_inf)
                print(point_1, point_2)
                self.crossties_vert.append({
                    'points_1': [point_1, point_2],
                    'points_2': [point_3, point_4]
                })
                # Seismic Hooks (135)
                ## Top Hook
                self.tie_top_arcs.append(Arc((rebar.coord_x, rebar.coord_y), rebar.diameter/2 + self.main_stirrup.diameter, start_angle=180, end_angle=45))

                ## Top Hook Polyline
                angle_degrees = 45
                # convert angle to radians
                angle_radians = math.radians(angle_degrees)
                # Calculate sin 45
                sin_45 = math.sin(angle_radians)
                # Calculate cos 45
                cos_45 = math.cos(angle_radians)
                x_coord = rebar.coord_x + cos_45*rebar.diameter/2
                y_coord = rebar.coord_y + sin_45*rebar.diameter/2
                _6db = 3*rebar.diameter
                x1_coord = x_coord + cos_45 * _6db
                y1_coord = y_coord - sin_45 * _6db
                x2_coord = x1_coord + cos_45 * self.main_stirrup.diameter
                y2_coord = y1_coord + sin_45 * self.main_stirrup.diameter
                x3_coord =x2_coord - cos_45 * _6db
                y3_coord = y2_coord + sin_45 * _6db
                self.tie_top_hook_points.append([
                    (x_coord, y_coord), 
                    (x1_coord, y1_coord),
                    (x2_coord, y2_coord),
                    (x3_coord, y3_coord),
                    
                ])
                ## Bottom Hook
                self.tie_bottom_arcs.append(Arc((rebar.coord_x, self.coor_y_inf),self.main_stirrup.diameter + rebar.diameter/2, start_angle=315, end_angle=180))
                
                x_coord = rebar.coord_x + cos_45*rebar.diameter/2
                y_coord = self.coor_y_inf - sin_45*rebar.diameter/2
                _6db = 3*rebar.diameter
                x1_coord = x_coord + cos_45 * _6db
                y1_coord = y_coord + sin_45 * _6db
                x2_coord = x1_coord + cos_45 * self.main_stirrup.diameter
                y2_coord = y1_coord - sin_45 * self.main_stirrup.diameter
                x3_coord =x2_coord - cos_45 * _6db
                y3_coord = y2_coord - sin_45 * _6db
                self.tie_bottom_hook_points.append([
                    (x_coord, y_coord), 
                    (x1_coord, y1_coord),
                    (x2_coord, y2_coord),
                    (x3_coord, y3_coord),
                    
                ])
        
        # Revision barras en direccion Y (Crossties horizontales)

        # Identificar, separar y ordenar las barras de la capa superior
        rebar_capa_izq = []
        for indice, rebar in enumerate(self.rebars):
            if rebar.coord_x == self.coor_x_izq:
                rebar_capa_izq.append(rebar)

        rebar_capa_izq_sorted = sorted(rebar_capa_izq, key=lambda barra: barra.coord_y)

        # 2. Iniciar un bucle que se repita hasta que no se añadan nuevos soportes.
        # Esto es clave para que un nuevo crosstie pueda dar soporte a la siguiente barra.
        hubo_cambios = True
        while hubo_cambios:
            hubo_cambios = False
            
            # Obtenemos la lista actualizada de barras ya soportadas en cada iteración.
            barras_ya_soportadas = [b for b in rebar_capa_izq_sorted if b.is_soportada]

            # 3. Recorrer cada barra para ver si necesita soporte.
            for barra_a_revisar in rebar_capa_izq_sorted:
                if not barra_a_revisar.is_soportada:
                    # 4. Calcular la distancia a la barra soportada más cercana.
                    # Se asume que la distancia relevante es en el eje Y para barras en una cara.
                    distancia_minima = min(
                        abs(barra_a_revisar.coord_y - b_soportada.coord_y) 
                        for b_soportada in barras_ya_soportadas
                    )

                    # 5. Aplicar la regla del ACI 318-19.
                    if distancia_minima > MAX_ESPACIAMIENTO_LIBRE_SIN_SOPORTE:
                        barra_a_revisar.has_crosstie = True
                        barra_a_revisar.is_soportada = True
                        hubo_cambios = True  # Marcamos que se hizo un cambio para re-evaluar.
                        print(f"INFO: Barra {barra_a_revisar.id} necesita crosstie (distancia_min={distancia_minima:.1f} mm > {MAX_ESPACIAMIENTO_LIBRE_SIN_SOPORTE} mm). Se añade soporte.")


        print(f"Barras Capa Izquierda: {len(rebar_capa_izq_sorted)}")
        for rebar in rebar_capa_izq_sorted:
            if rebar.has_crosstie == True:
                print(rebar.id, "CrossTie Horizontal")
                print(f"Barra {rebar.get_coords()} and is_soportada: {rebar.is_soportada}")
                point_1 = (rebar.coord_x,rebar.coord_y - rebar.diameter/2, )
                point_2 = (self.coor_x_der,rebar.coord_y - rebar.diameter/2)
                point_3 = (rebar.coord_x, point_1[1] - self.main_stirrup.diameter )
                point_4 = (self.coor_x_der, point_2[1] - self.main_stirrup.diameter)
                print(point_1, point_2)
                self.crossties_horizontal.append({
                    'points_1': [point_1, point_2],
                    'points_2': [point_3, point_4]
                })

                # Seismic Hooks (135)
                ## Left Hook
                self.tie_left_arcs.append(
                    Arc(
                        center_point=(rebar.coord_x, rebar.coord_y),
                        radius=self.main_stirrup.diameter + rebar.diameter/2,
                        start_angle=135,
                        end_angle=270
                    )
                )
                angle_degrees = 45
                # convert angle to radians
                angle_radians = math.radians(angle_degrees)
                # Calculate sin 45
                sin_45 = math.sin(angle_radians)
                cos_45 = math.cos(angle_degrees)
                x_coord = rebar.coord_x - cos_45*rebar.diameter/2
                y_coord = rebar.coord_y + sin_45*rebar.diameter/2
                _6db = 3*rebar.diameter
                x1_coord = x_coord + cos_45 * _6db
                y1_coord = y_coord + sin_45 * _6db
                x2_coord = x1_coord - cos_45 * self.main_stirrup.diameter
                y2_coord = y1_coord + sin_45 * self.main_stirrup.diameter
                x3_coord =x2_coord - cos_45 * _6db
                y3_coord = y2_coord - sin_45 * _6db
                self.tie_bottom_hook_points.append([
                    (x_coord, y_coord), 
                    (x1_coord, y1_coord),
                    (x2_coord, y2_coord),
                    (x3_coord, y3_coord),
                    
                ])

                ## Right Hook
                self.tie_right_arcs.append(
                    Arc(
                    center_point=(self.coor_x_der, rebar.coord_y),
                    radius=self.main_stirrup.diameter + rebar.diameter/2,
                    start_angle=270,
                    end_angle=45
                    )
                )

                x_coord = self.coor_x_der + cos_45*rebar.diameter/2
                y_coord = rebar.coord_y + sin_45*rebar.diameter/2
                _6db = 3*rebar.diameter
                x1_coord = x_coord - cos_45 * _6db
                y1_coord = y_coord + sin_45 * _6db
                x2_coord = x1_coord + cos_45 * self.main_stirrup.diameter
                y2_coord = y1_coord + sin_45 * self.main_stirrup.diameter
                x3_coord =x2_coord + cos_45 * _6db
                y3_coord = y2_coord - sin_45 * _6db
                self.tie_bottom_hook_points.append([
                    (x_coord, y_coord), 
                    (x1_coord, y1_coord),
                    (x2_coord, y2_coord),
                    (x3_coord, y3_coord),
                    
                ])