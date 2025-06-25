import sys
import math
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox, QGroupBox, QDockWidget,
    QInputDialog, QMessageBox ### MODIFICACIÓN ###: Importaciones adicionales
)
from PyQt5.QtOpenGL import QGLWidget
# Es posible que necesites instalar PyOpenGL: pip install PyOpenGL PyOpenGL_accelerate
from OpenGL.GL import (glBegin, glBlendFunc, glClear, glClearColor, glColor3f, glColor4f,
                       glEnd, glEnable, glLineWidth, glLoadIdentity, glMatrixMode,
                       glRotatef, glScalef, glTranslatef, glVertex2f, glViewport,
                       GL_BLEND, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, GL_LINES,
                       GL_LINE_SMOOTH, GL_LINE_STRIP, GL_MODELVIEW, GL_POLYGON,
                       GL_PROJECTION, GL_QUADS, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
from OpenGL.GLU import gluOrtho2D

# --- Constantes y Datos de Referencia ---

# Diámetros de barras de refuerzo estándar de EE. UU. en pulgadas.
# La aplicación convierte todas las unidades a pulgadas internamente.
BAR_DIAMETERS_IN = {
    '#3': 0.375, '#4': 0.500, '#5': 0.625, '#6': 0.750,
    '#7': 0.875, '#8': 1.000, '#9': 1.128, '#10': 1.270,
    '#11': 1.410, '#12': 1.500, '#14': 1.693,
}

# Factores de conversión a pulgadas
CONVERSION_FACTORS = {
    'pulgadas': 1.0,
    'cm': 1 / 2.54,
    'mm': 1 / 25.4,
}


# --- Clases del Modelo de Datos (Orientado a Objetos) ---

class BaseDrawable:
    """Clase base para todos los objetos que se pueden dibujar."""
    def draw(self):
        raise NotImplementedError("Cada objeto dibujable debe implementar el método 'draw'.")

class Columna(BaseDrawable):
    """Representa el contorno de concreto de la sección de la columna."""
    def __init__(self, x, y, b, h):
        self.x = x
        self.y = y
        self.b = b  # Ancho (eje 2)
        self.h = h  # Altura (eje 3)

    def draw(self):
        """Dibuja un rectángulo que representa la sección de la columna."""
        glColor3f(0.8, 0.8, 0.8)  # Color concreto (gris claro)
        glBegin(GL_QUADS)
        glVertex2f(self.x, self.y)
        glVertex2f(self.x + self.b, self.y)
        glVertex2f(self.x + self.b, self.y + self.h)
        glVertex2f(self.x, self.y + self.h)
        glEnd()

class EstriboPrincipal(BaseDrawable):
    """Representa el estribo principal rectangular."""
    def __init__(self, col_b, col_h, recubrimiento, tamano_barra, tamano_barra_long):
        self.bar_diameter = BAR_DIAMETERS_IN.get(tamano_barra, 0)
        self.bar_long_diam = BAR_DIAMETERS_IN.get(tamano_barra_long, 0)
        self.x = recubrimiento + self.bar_diameter
        self.y = recubrimiento + self.bar_diameter
        self.ancho = col_b - 2 * recubrimiento - 2*self.bar_diameter
        self.alto = col_h - 2 * recubrimiento - 2 * self.bar_diameter
        self.radio_doblado = 2 * self.bar_diameter
        self.hook_tail_len = 6 * self.bar_diameter

    def draw(self):
        """Dibuja un rectángulo con esquinas redondeadas para el estribo."""
        glColor3f(0.5, 0.3, 0.2)
        glLineWidth(self.bar_diameter)
        x1, y1, x2, y2, r = self.x, self.y, self.x + self.ancho, self.y + self.alto, self.radio_doblado
        glBegin(GL_LINES)
        glVertex2f(x1  + r, y1); glVertex2f(x2 - r, y1)
        glVertex2f(x1 + r, y2); glVertex2f(x2 - r, y2)
        glVertex2f(x1, y1 + r); glVertex2f(x1, y2 - r)
        glVertex2f(x2, y1 + r); glVertex2f(x2, y2 - r)
        glEnd()
        self._draw_arc(x2 - r, y2 - r, r, 0, 90)
        self._draw_arc(x1 + r, y2 - r, r, 90, 180)
        self._draw_arc(x1 + r, y1 + r, r, 180, 270)
        self._draw_arc(x2 - r, y1 + r, r, 270, 360)

        # Centro de Barra Long de Esquina Superior Izquierda
        centro_barra_x = x1 + self.bar_long_diam/2
        centro_barra_y = y2 - self.bar_long_diam/2 

        # centro_barra_x_inf = x1 + self.bar_long_diam/2 - self.bar_diameter/2
        # centro_barra_y_inf = y2 + self.bar_long_diam/2 + self.bar_diameter/2

        # El centro del arco de la esquina es el punto de referencia para el gancho
        hook_center_x = x1 + self.bar_long_diam/2
        hook_center_y = y2 - self.bar_long_diam/2

        # Dibuja la cola recta del gancho (longitud 6*diametro)
        # Dibuja el doblez adicional de 135 grados para el gancho
        # hook_start_angle = 180
        # hook_end_angle = 180 + 135 # 315 grados
        angle_hook = math.radians(45)
        # end_angle_rad = math.radians(hook_end_angle)
        tail_start_x = centro_barra_x + self.bar_long_diam/2 * math.cos(angle_hook)
        tail_start_y = centro_barra_y + self.bar_long_diam/2 * math.sin(angle_hook)

        tail_start_x_inf = centro_barra_x - self.bar_long_diam/2 * math.cos(angle_hook)
        tail_start_y_inf = centro_barra_y - self.bar_long_diam/2 * math.sin(angle_hook)
        
        # # La cola es tangente al final del arco del gancho
        # tail_vector_x = math.cos(end_angle_rad)
        # tail_vector_y = math.sin(end_angle_rad)
        
        tail_end_x = tail_start_x + self.hook_tail_len * math.cos(angle_hook)
        tail_end_y = tail_start_y - self.hook_tail_len * math.sin(angle_hook)

        tail_end_x_inf = tail_start_x_inf + self.hook_tail_len * math.cos(angle_hook)
        tail_end_y_inf = tail_start_y_inf - self.hook_tail_len * math.sin(angle_hook)

        glBegin(GL_LINES)
        glVertex2f(tail_start_x, tail_start_y)
        glVertex2f(tail_end_x, tail_end_y)
        glEnd()

        glBegin(GL_LINES)
        glVertex2f(tail_start_x_inf, tail_start_y_inf)
        glVertex2f(tail_end_x_inf, tail_end_y_inf)
        glEnd()

    def _draw_arc(self, cx, cy, radius, start_angle, end_angle, num_segments=10):
        glBegin(GL_LINE_STRIP)
        for i in range(num_segments + 1):
            angle = math.radians(start_angle + (end_angle - start_angle) * i / num_segments)
            glVertex2f(cx + radius * math.cos(angle), cy + radius * math.sin(angle))
        glEnd()

class BarraLongitudinal(BaseDrawable):
    """Representa una única barra de acero de refuerzo longitudinal."""
    def __init__(self, centro, tamano_barra):
        self.x, self.y = centro
        self.diameter = BAR_DIAMETERS_IN.get(tamano_barra, 0)
        self.radius = self.diameter / 2

    def draw(self):
        """Dibuja un círculo relleno para la barra de refuerzo."""
        glColor3f(0.5, 0.3, 0.2)
        glBegin(GL_POLYGON)
        for i in range(20):
            angle = 2 * math.pi * i / 20
            glVertex2f(self.x + self.radius * math.cos(angle), self.y + self.radius * math.sin(angle))
        glEnd()

class CrossTie(BaseDrawable):
    """Representa un gancho suplementario (cross tie) con ganchos sísmicos de 135 grados."""
    def __init__(self, punto_inicio, punto_fin, tamano_barra_tie, tamano_barra_long):
        self.x1, self.y1 = punto_inicio
        self.x2, self.y2 = punto_fin
        self.tie_diameter = BAR_DIAMETERS_IN.get(tamano_barra_tie, 0)
        self.long_diameter = BAR_DIAMETERS_IN.get(tamano_barra_long, 0)
        # La longitud de la cola del gancho es típicamente 6 veces el diámetro
        self.hook_len = 6 * self.tie_diameter

    def _draw_arc(self, cx, cy, radius, start_angle_deg, end_angle_deg, num_segments=20):
        """Dibuja un arco."""
        glBegin(GL_LINE_STRIP)
        for i in range(num_segments + 1):
            angle_deg = start_angle_deg + (end_angle_deg - start_angle_deg) * i / num_segments
            rad = math.radians(angle_deg)
            x = cx + radius * math.cos(rad)
            y = cy + radius * math.sin(rad)
            glVertex2f(x, y)
        glEnd()
    
    def _draw_hook_at_point(self, hook_center, is_start_hook, tangent_offset_vector):
        """Dibuja un gancho completo (arco + cola) en un extremo del tie."""
        C = hook_center
        R_long = self.long_diameter / 2
        
        # El radio del arco del gancho envuelve la barra longitudinal.
        arc_radius = R_long
        
        # El punto base del gancho es donde empieza el arco (tangente a la barra long.)
        P = (C[0] + tangent_offset_vector[0] * arc_radius, 
             C[1] + tangent_offset_vector[1] * arc_radius)

        # --- Dibuja el arco de 135 grados ---
        start_angle_rad = math.atan2(P[1] - C[1], P[0] - C[0])
        
        # La dirección del arco depende de si es el gancho de inicio o fin para simetría.
        sweep_deg = 135 if is_start_hook else -135
        
        start_angle_deg = math.degrees(start_angle_rad)
        end_angle_deg = start_angle_deg + sweep_deg
        
        self._draw_arc(C[0], C[1], arc_radius, start_angle_deg, end_angle_deg)

        # --- Dibuja la cola recta ---
        end_angle_rad = math.radians(end_angle_deg)
        arc_end_point = (C[0] + arc_radius * math.cos(end_angle_rad),
                         C[1] + arc_radius * math.sin(end_angle_rad))
        
        # La cola es tangente al final del arco
        tangent_angle_rad = end_angle_rad + math.radians(90 if is_start_hook else -90)
        
        tail_end_point = (arc_end_point[0] + self.hook_len * math.cos(tangent_angle_rad),
                          arc_end_point[1] + self.hook_len * math.sin(tangent_angle_rad))
                          
        glBegin(GL_LINES)
        glVertex2f(arc_end_point[0], arc_end_point[1])
        glVertex2f(tail_end_point[0], tail_end_point[1])
        glEnd()

        return P # Devuelve el punto de inicio del arco para dibujar la línea recta

    def draw(self):
        """Dibuja el gancho completo: línea recta tangente y dos ganchos de 135 grados."""
        glColor3f(0.6, 0.4, 0.3)
        glLineWidth(self.tie_diameter)

        C1, C2 = (self.x1, self.y1), (self.x2, self.y2)
        
        dx, dy = C2[0] - C1[0], C2[1] - C1[1]
        dist = math.hypot(dx, dy)
        if dist == 0: return

        # Vector unitario perpendicular a la línea que une los centros
        # Este vector define la dirección de la línea tangente.
        tangent_dir_vec = (-dy / dist, dx / dist)

        # Dibuja cada gancho y obtiene los puntos de inicio/fin de la línea recta
        p1 = self._draw_hook_at_point(C1, True, tangent_dir_vec)
        p2 = self._draw_hook_at_point(C2, False, tangent_dir_vec)

        # Dibuja la línea recta que conecta los dos ganchos
        glBegin(GL_LINES)
        glVertex2f(p1[0], p1[1])
        glVertex2f(p2[0], p2[1])
        glEnd()


# --- Widget de OpenGL para el Dibujo ---

class OpenGLCanvas(QGLWidget):
    """El lienzo de dibujo que utiliza OpenGL."""
    statusMessage = pyqtSignal(str)

    def __init__(self, parent=None):
        super(OpenGLCanvas, self).__init__(parent)
        self.objetos_a_dibujar = []
        self.zoom_level, self.pan_x, self.pan_y, self.rotation_angle = 1.0, 0.0, 0.0, 0.0
        self.last_mouse_pos = QPoint()
        self.ancho_escena, self.alto_escena = 40, 40

    def set_draw_objects(self, objetos, b, h):
        """Establece la lista de objetos a dibujar y centra la vista (fit-to-size)."""
        self.objetos_a_dibujar = objetos
        
        # Resetear la vista para la función "fit to size"
        self.rotation_angle = 0.0

        if b <= 0 or h <= 0:
            self.updateGL()
            return

        # Calcular el zoom para ajustar la columna (b, h) dentro de la vista
        # con un margen del 10%.
        margin = 0.90
        
        # La escala de zoom es inversamente proporcional al tamaño del objeto en la pantalla
        zoom_x = self.ancho_escena / b
        zoom_y = self.alto_escena / h
        self.zoom_level = min(zoom_x, zoom_y) * margin

        # Calcular el pan para centrar la columna.
        # Apuntamos la cámara al centro de la columna (b/2, h/2).
        self.pan_x = b / 2
        self.pan_y = h / 2
        
        self.updateGL()


    def initializeGL(self):
        """Configuración inicial de OpenGL."""
        glClearColor(0.05, 0.05, 0.1, 1.0)
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self.statusMessage.emit("Clic izquierdo: Mover, Clic derecho: Rotar, Rueda: Zoom")

    def resizeGL(self, w, h):
        """Se llama al cambiar el tamaño del widget."""
        glViewport(0, 0, w, h)
        aspect_ratio = w / h if h > 0 else 1
        self.ancho_escena = 40 * aspect_ratio
        self.alto_escena = 40
        self._update_projection()

    def _update_projection(self):
        """Actualiza la matriz de proyección ortográfica."""
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, self.ancho_escena, 0, self.alto_escena)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        """El corazón del dibujo. Se llama para redibujar la escena."""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Configurar la cámara
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # 1. Mover al centro del viewport para que la rotación y el zoom sean centrados
        view_center_x = self.ancho_escena / 2
        view_center_y = self.alto_escena / 2
        glTranslatef(view_center_x, view_center_y, 0.0)

        # 2. Aplicar zoom y rotación
        glScalef(self.zoom_level, self.zoom_level, 1.0)
        glRotatef(self.rotation_angle, 0.0, 0.0, 1.0)
        
        # 3. Mover la cámara para que apunte al punto (pan_x, pan_y)
        glTranslatef(-self.pan_x, -self.pan_y, 0.0)

        # Dibujar la escena
        self._draw_axes()
        for obj in self.objetos_a_dibujar:
            obj.draw()

    def _draw_axes(self):
        """Dibuja los ejes 2 (X) y 3 (Y)."""
        glColor4f(1, 1, 1, 0.2)
        glLineWidth(1.0)
        glBegin(GL_LINES)
        glVertex2f(-1000, 0); glVertex2f(1000, 0)
        glVertex2f(0, -1000); glVertex2f(0, 1000)
        glEnd()

    def wheelEvent(self, event):
        self.zoom_level *= 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.updateGL()

    def mousePressEvent(self, event):
        self.last_mouse_pos = event.pos()

    def mouseMoveEvent(self, event):
        dx = event.x() - self.last_mouse_pos.x()
        dy = event.y() - self.last_mouse_pos.y()
        
        if event.buttons() & Qt.LeftButton: # Pan
            # Convertir el delta de píxeles del ratón a delta de coordenadas del mundo
            if self.width() > 0 and self.zoom_level != 0:
                world_dx = (dx / self.width()) * self.ancho_escena / self.zoom_level
                world_dy = (dy / self.height()) * self.alto_escena / self.zoom_level
                self.pan_x -= world_dx
                self.pan_y += world_dy # El eje Y del ratón está invertido
            self.statusMessage.emit(f"Pan: ({self.pan_x:.1f}, {self.pan_y:.1f})")

        elif event.buttons() & Qt.RightButton: # Rotate
            self.rotation_angle += dx * 0.2
            self.statusMessage.emit(f"Rotación: {self.rotation_angle:.1f}°")
            
        self.last_mouse_pos = event.pos()
        self.updateGL()

# --- Ventana Principal de la Aplicación ---

class SectionDesignerScreen(QMainWindow):
    ### MODIFICACIÓN ###: Constructor ahora acepta 'sections_data'
    def __init__(self, sections_data=None):
        super(SectionDesignerScreen, self).__init__()

        ### MODIFICACIÓN ###: Almacenamiento de datos de secciones
        if sections_data and isinstance(sections_data, list):
            self.sections = sections_data
        else:
            # Si no se proporcionan datos, crear una sección por defecto
            self.sections = [{
                "section": "Columna C-1 (Default)", "b": 500.0, "h": 750.0,
                "cover": 40.0, "rebar_size": "#8", "num_bars_2": 3,
                "num_bars_3": 4, "stirrup_size": "#4", "num_crossties_2": 1,
                "num_crossties_3": 2
            }]
        self.current_section_index = 0

        self.setWindowTitle("Visor de Secciones de Columna")
        self.setGeometry(100, 100, 1200, 800)
        self.canvas = OpenGLCanvas(self)
        self.setCentralWidget(self.canvas)
        self.setup_controls_panel()
        self.statusBar().showMessage("Listo.")
        self.canvas.statusMessage.connect(self.statusBar().showMessage)

        self.units_input.setCurrentText("cm")
        
        ### MODIFICACIÓN ###: Cargar datos de la primera sección y dibujar
        self._load_section_data(self.current_section_index)


    def setup_controls_panel(self):
        """Crea el panel lateral con todos los widgets de entrada."""
        dock = QDockWidget("Controles", self)
        dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)
        
        controls_widget = QWidget()
        main_layout = QVBoxLayout(controls_widget)
        main_layout.setAlignment(Qt.AlignTop)

        ### MODIFICACIÓN ###: Nuevo grupo para gestionar secciones
        section_mgm_group = QGroupBox("Gestión de Secciones")
        section_mgm_layout = QVBoxLayout()
        self.section_selector = QComboBox()
        self.section_selector.currentIndexChanged.connect(self._on_section_selected)
        
        new_section_button = QPushButton("Crear Nueva Sección")
        new_section_button.clicked.connect(self._create_new_section)

        section_mgm_layout.addWidget(QLabel("Seleccionar Sección:"))
        section_mgm_layout.addWidget(self.section_selector)
        section_mgm_layout.addWidget(new_section_button)
        section_mgm_group.setLayout(section_mgm_layout)
        main_layout.addWidget(section_mgm_group)
        
        # --- Sección General ---
        general_group = QGroupBox("Configuración General de Unidades")
        general_layout = QVBoxLayout()
        self.units_input = QComboBox()
        self.units_input.addItems(CONVERSION_FACTORS.keys())
        general_layout.addWidget(QLabel("Unidades de Entrada (para b, h, cover):"))
        general_layout.addWidget(self.units_input)
        general_group.setLayout(general_layout)
        main_layout.addWidget(general_group)
        
        # --- Sección de Geometría ---
        geo_group = QGroupBox("Geometría de la Columna")
        geo_layout = QVBoxLayout()
        self.b_input = QLineEdit("500.0")
        self.h_input = QLineEdit("750.0")
        self.cover_input = QLineEdit("40.0")
        self.units_input.currentTextChanged.connect(self._update_defaults_on_unit_change)
        self.units_input.setCurrentText("mm")
        geo_layout.addWidget(QLabel("Ancho (b):"))
        geo_layout.addWidget(self.b_input)
        geo_layout.addWidget(QLabel("Altura (h):"))
        geo_layout.addWidget(self.h_input)
        geo_layout.addWidget(QLabel("Recubrimiento:"))
        geo_layout.addWidget(self.cover_input)
        geo_group.setLayout(geo_layout)
        main_layout.addWidget(geo_group)

        # --- Secciones de Refuerzo ---
        rebar_group = QGroupBox("Refuerzo Longitudinal")
        rebar_layout = QVBoxLayout()
        self.rebar_size_input = QComboBox()
        self.rebar_size_input.addItems(BAR_DIAMETERS_IN.keys())
        self.rebar_size_input.setCurrentText("#8")
        self.num_bars_2_input = QSpinBox()
        self.num_bars_2_input.setMinimum(2); self.num_bars_2_input.setValue(3)
        self.num_bars_3_input = QSpinBox()
        self.num_bars_3_input.setMinimum(2); self.num_bars_3_input.setValue(4)
        rebar_layout.addWidget(QLabel("Tamaño de Barra:")); rebar_layout.addWidget(self.rebar_size_input)
        rebar_layout.addWidget(QLabel("Barras en dirección 2:")); rebar_layout.addWidget(self.num_bars_2_input)
        rebar_layout.addWidget(QLabel("Barras en dirección 3:")); rebar_layout.addWidget(self.num_bars_3_input)
        rebar_group.setLayout(rebar_layout)
        main_layout.addWidget(rebar_group)
        
        trans_group = QGroupBox("Refuerzo Transversal")
        trans_layout = QVBoxLayout()
        self.stirrup_size_input = QComboBox()
        self.stirrup_size_input.addItems(['#3', '#4', '#5']); self.stirrup_size_input.setCurrentText('#4')
        self.num_crossties_2_input = QSpinBox(); self.num_crossties_2_input.setValue(1)
        self.num_crossties_3_input = QSpinBox(); self.num_crossties_3_input.setValue(2)
        trans_layout.addWidget(QLabel("Tamaño de Estribo:")); trans_layout.addWidget(self.stirrup_size_input)
        trans_layout.addWidget(QLabel("Ganchos Suplementarios Verticales:")); trans_layout.addWidget(self.num_crossties_2_input)
        trans_layout.addWidget(QLabel("Ganchos Suplementarios Horizontales:")); trans_layout.addWidget(self.num_crossties_3_input)
        trans_group.setLayout(trans_layout)
        main_layout.addWidget(trans_group)
        
        draw_button = QPushButton("Dibujar / Actualizar")
        draw_button.clicked.connect(self.generate_drawing)
        main_layout.addWidget(draw_button)
        dock.setWidget(controls_widget)

        ### MODIFICACIÓN ###: Llenar el ComboBox de secciones al final
        self._populate_sections_dropdown()

    ### MODIFICACIÓN ###: Nuevas funciones para gestionar datos y UI
    def _populate_sections_dropdown(self):
        """Llena el selector de secciones con los nombres de la lista `self.sections`."""
        self.section_selector.blockSignals(True)
        self.section_selector.clear()
        self.section_selector.addItems([s['section'] for s in self.sections])
        self.section_selector.setCurrentIndex(self.current_section_index)
        self.section_selector.blockSignals(False)

    def _on_section_selected(self, index):
        """Se activa al cambiar la selección en el QComboBox."""
        if index == -1 or index == self.current_section_index:
            return
        # Guardar los datos de la sección actual antes de cargar la nueva
        self._save_current_section_data()
        # Cargar los datos de la nueva sección seleccionada
        self._load_section_data(index)

    def _load_section_data(self, index):
        """Carga los datos de una sección de la lista a los controles de la UI y redibuja."""
        self.current_section_index = index
        data = self.sections[index]

        # Bloquear señales para evitar llamadas recursivas o indeseadas
        for widget in self.findChildren(QWidget):
            widget.blockSignals(True)

        # Actualizar widgets con los datos del diccionario
        self.setWindowTitle(f"Visor de Secciones - {data['section']}")
        self.b_input.setText(str(data['b']))
        self.h_input.setText(str(data['h']))
        self.cover_input.setText(str(data['cover']))
        self.rebar_size_input.setCurrentText(data['rebar_size'])
        self.num_bars_2_input.setValue(data['num_bars_2'])
        self.num_bars_3_input.setValue(data['num_bars_3'])
        self.stirrup_size_input.setCurrentText(data['stirrup_size'])
        self.num_crossties_2_input.setValue(data['num_crossties_2'])
        self.num_crossties_3_input.setValue(data['num_crossties_3'])
        
        # Sincronizar el selector de secciones por si la carga fue programática
        self.section_selector.setCurrentIndex(index)

        # Restaurar señales
        for widget in self.findChildren(QWidget):
            widget.blockSignals(False)

        # Generar el dibujo con los nuevos datos
        self.generate_drawing()

    def _save_current_section_data(self):
        """Guarda los valores actuales de la UI en el diccionario de la sección activa."""
        if self.current_section_index < 0 or self.current_section_index >= len(self.sections):
            return
        
        current_data = self.sections[self.current_section_index]
        try:
            current_data['b'] = float(self.b_input.text())
            current_data['h'] = float(self.h_input.text())
            current_data['cover'] = float(self.cover_input.text())
            current_data['rebar_size'] = self.rebar_size_input.currentText()
            current_data['num_bars_2'] = self.num_bars_2_input.value()
            current_data['num_bars_3'] = self.num_bars_3_input.value()
            current_data['stirrup_size'] = self.stirrup_size_input.currentText()
            current_data['num_crossties_2'] = self.num_crossties_2_input.value()
            current_data['num_crossties_3'] = self.num_crossties_3_input.value()
        except ValueError as e:
            self.statusBar().showMessage(f"Error al guardar datos: {e}. Entrada inválida.")

    def _create_new_section(self):
        """Crea una nueva sección basada en los valores actuales de la UI."""
        self._save_current_section_data() # Guardar cambios actuales primero
        
        new_name, ok = QInputDialog.getText(self, "Crear Nueva Sección", "Nombre de la nueva sección:")
        if ok and new_name:
            # Verificar que el nombre no exista
            if any(s['section'] == new_name for s in self.sections):
                QMessageBox.warning(self, "Error", "Ya existe una sección con ese nombre.")
                return

            # Crear el nuevo diccionario de sección copiando el actual
            new_section_data = self.sections[self.current_section_index].copy()
            new_section_data['section'] = new_name
            
            self.sections.append(new_section_data)
            self.current_section_index = len(self.sections) - 1
            self._populate_sections_dropdown()
            self.statusBar().showMessage(f"Sección '{new_name}' creada.")

    def _update_defaults_on_unit_change(self, unit):
        """Cambia los valores por defecto cuando el usuario cambia las unidades."""
        if unit == 'pulgadas':
            self.b_input.setText("20.0")
            self.h_input.setText("30.0")
            self.cover_input.setText("1.5")
        elif unit == 'cm':
            self.b_input.setText("50.0")
            self.h_input.setText("75.0")
            self.cover_input.setText("4.0")
        elif unit == 'mm':
            self.b_input.setText("500.0")
            self.h_input.setText("750.0")
            self.cover_input.setText("40.0")

    def generate_drawing(self):
        """Lee los datos de la UI, crea los objetos y los envía al canvas."""
        ### MODIFICACIÓN ###: Guarda los datos de la UI antes de dibujar
        self._save_current_section_data()
        
        try:
            # Obtener datos de la sección actual
            data = self.sections[self.current_section_index]

            unit = self.units_input.currentText()
            factor = CONVERSION_FACTORS[unit]
            b = data['b'] * factor
            h = data['h'] * factor
            cover = data['cover'] * factor
            
            rebar_size = data['rebar_size']
            stirrup_size = data['stirrup_size']
            num_bars_2 = data['num_bars_2']
            num_bars_3 = data['num_bars_3']
            num_ct_2 = data['num_crossties_2']
            num_ct_3 = data['num_crossties_3']

            # Validar y corregir el número de ganchos suplementarios
            if num_ct_2 > num_bars_2 - 2:
                num_ct_2 = max(0, num_bars_2 - 2)
                self.num_crossties_2_input.setValue(num_ct_2)
                data['num_crossties_2'] = num_ct_2 # Actualizar también en el modelo
            if num_ct_3 > num_bars_3 - 2:
                num_ct_3 = max(0, num_bars_3 - 2)
                self.num_crossties_3_input.setValue(num_ct_3)
                data['num_crossties_3'] = num_ct_3 # Actualizar también en el modelo


            objetos = [Columna(0, 0, b, h), EstriboPrincipal(b, h, cover, stirrup_size, rebar_size)]
            
            # --- Lógica de cálculo de refuerzo (en pulgadas) ---
            stirrup_bar_d = BAR_DIAMETERS_IN[stirrup_size]
            rebar_d = BAR_DIAMETERS_IN[rebar_size]
            x_start = cover + stirrup_bar_d + rebar_d / 2
            x_end = b - cover - stirrup_bar_d - rebar_d / 2
            y_start = cover + stirrup_bar_d + rebar_d / 2
            y_end = h - cover - stirrup_bar_d - rebar_d / 2
            spacing_x = (x_end - x_start) / (num_bars_2 - 1) if num_bars_2 > 1 else 0
            spacing_y = (y_end - y_start) / (num_bars_3 - 1) if num_bars_3 > 1 else 0
            
            positions = set()
            for i in range(num_bars_2):
                positions.add((x_start + i * spacing_x, y_start))
                positions.add((x_start + i * spacing_x, y_end))
            for i in range(1, num_bars_3 - 1):
                positions.add((x_start, y_start + i * spacing_y))
                positions.add((x_end, y_start + i * spacing_y))
            
            for pos in sorted(list(positions)):
                objetos.append(BarraLongitudinal(pos, rebar_size))
            
            interior_bars_x = [x_start + i * spacing_x for i in range(1, num_bars_2 - 1)]
            for i in range(min(num_ct_2, len(interior_bars_x))):
                start_pt = (interior_bars_x[i], y_start)
                end_pt = (interior_bars_x[i], y_end)
                objetos.append(CrossTie(start_pt, end_pt, stirrup_size, rebar_size))
            
            interior_bars_y = [y_start + i * spacing_y for i in range(1, num_bars_3 - 1)]
            for i in range(min(num_ct_3, len(interior_bars_y))):
                start_pt = (x_start, interior_bars_y[i])
                end_pt = (x_end, interior_bars_y[i])
                objetos.append(CrossTie(start_pt, end_pt, stirrup_size, rebar_size))

            self.canvas.set_draw_objects(objetos, b, h)
            self.statusBar().showMessage(f"Mostrando sección: {data['section']}. Dibujo actualizado.")

        except (ValueError, KeyError) as e:
            self.statusBar().showMessage(f"Error en datos: {e}")
        except Exception as e:
            self.statusBar().showMessage(f"Error inesperado: {e}")


### MODIFICACIÓN ###: Bloque principal para demostrar la nueva funcionalidad
if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Lista de ejemplo de diccionarios de secciones
    sample_sections = [
        {
            "section": "C-1 (50x75cm)", "b": 50.0, "h": 75.0, "cover": 4.0,
            "rebar_size": "#9", "num_bars_2": 3, "num_bars_3": 5,
            "stirrup_size": "#4", "num_crossties_2": 1, "num_crossties_3": 3
        },
        {
            "section": "C-2 (60x60cm)", "b": 60.0, "h": 60.0, "cover": 4.0,
            "rebar_size": "#8", "num_bars_2": 4, "num_bars_3": 4,
            "stirrup_size": "#3", "num_crossties_2": 2, "num_crossties_3": 2
        },
        {
            "section": "Viga V-1 (30x60cm)", "b": 30.0, "h": 60.0, "cover": 5.0,
            "rebar_size": "#6", "num_bars_2": 2, "num_bars_3": 4,
            "stirrup_size": "#3", "num_crossties_2": 0, "num_crossties_3": 1
        }
    ]
    
    # La ventana ahora se inicializa con la lista de datos.
    # El selector de unidades por defecto se establece en 'cm' para esta lista.
    main_window = SectionDesignerScreen(sections_data=sample_sections)
    
    main_window.show()
    
    sys.exit(app.exec_())