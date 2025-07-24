import sys
import math
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox, QGroupBox, QDockWidget,
    QInputDialog, QMessageBox
)
from PyQt5.QtOpenGL import QGLWidget
from OpenGL.GL import (glBegin, glBlendFunc, glClear, glClearColor, glColor3f, glColor4f,
                       glEnd, glEnable, glLineWidth, glLoadIdentity, glMatrixMode,
                       glRotatef, glScalef, glTranslatef, glVertex2f, glViewport,
                       GL_BLEND, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, GL_LINES,
                       GL_LINE_SMOOTH, GL_LINE_STRIP, GL_MODELVIEW, GL_POLYGON,
                       GL_PROJECTION, GL_QUADS, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA,
                       glGetDoublev, glGetIntegerv, GL_MODELVIEW_MATRIX, GL_PROJECTION_MATRIX,
                       GL_VIEWPORT)
from OpenGL.GLU import gluOrtho2D, gluUnProject

# --- Constantes y Datos de Referencia ---

BAR_DIAMETERS_IN = {
    '#3': 0.375, '#4': 0.500, '#5': 0.625, '#6': 0.750,
    '#7': 0.875, '#8': 1.000, '#9': 1.128, '#10': 1.270,
    '#11': 1.410, '#12': 1.500, '#14': 1.693,
}

CONVERSION_FACTORS = {
    'pulgadas': 1.0,
    'cm': 1 / 2.54,
    'mm': 1 / 25.4,
}


# --- Clases del Modelo de Datos (Orientado a Objetos) ---

class BaseDrawable:
    def draw(self):
        raise NotImplementedError("Cada objeto dibujable debe implementar el método 'draw'.")

class Columna(BaseDrawable):
    def __init__(self, x, y, b, h):
        self.x, self.y, self.b, self.h = x, y, b, h

    def draw(self):
        glColor3f(0.8, 0.8, 0.8)
        glBegin(GL_QUADS)
        glVertex2f(self.x, self.y)
        glVertex2f(self.x + self.b, self.y)
        glVertex2f(self.x + self.b, self.y + self.h)
        glVertex2f(self.x, self.y + self.h)
        glEnd()

class EstriboPrincipal(BaseDrawable):
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
        centro_barra_x = x1 + self.bar_long_diam/2
        centro_barra_y = y2 - self.bar_long_diam/2
        hook_center_x, hook_center_y = centro_barra_x, centro_barra_y
        angle_hook = math.radians(45)
        tail_start_x = centro_barra_x + self.bar_long_diam/2 * math.cos(angle_hook)
        tail_start_y = centro_barra_y + self.bar_long_diam/2 * math.sin(angle_hook)
        tail_start_x_inf = centro_barra_x - self.bar_long_diam/2 * math.cos(angle_hook)
        tail_start_y_inf = centro_barra_y - self.bar_long_diam/2 * math.sin(angle_hook)
        tail_end_x = tail_start_x + self.hook_tail_len * math.cos(angle_hook)
        tail_end_y = tail_start_y - self.hook_tail_len * math.sin(angle_hook)
        tail_end_x_inf = tail_start_x_inf + self.hook_tail_len * math.cos(angle_hook)
        tail_end_y_inf = tail_start_y_inf - self.hook_tail_len * math.sin(angle_hook)
        glBegin(GL_LINES); glVertex2f(tail_start_x, tail_start_y); glVertex2f(tail_end_x, tail_end_y); glEnd()
        glBegin(GL_LINES); glVertex2f(tail_start_x_inf, tail_start_y_inf); glVertex2f(tail_end_x_inf, tail_end_y_inf); glEnd()

    def _draw_arc(self, cx, cy, radius, start_angle, end_angle, num_segments=10):
        glBegin(GL_LINE_STRIP)
        for i in range(num_segments + 1):
            angle = math.radians(start_angle + (end_angle - start_angle) * i / num_segments)
            glVertex2f(cx + radius * math.cos(angle), cy + radius * math.sin(angle))
        glEnd()

class BarraLongitudinal(BaseDrawable):
    def __init__(self, centro, tamano_barra):
        self.x, self.y = centro
        self.diameter = BAR_DIAMETERS_IN.get(tamano_barra, 0)
        self.radius = self.diameter / 2

    def draw(self):
        glColor3f(0.5, 0.3, 0.2)
        glBegin(GL_POLYGON)
        for i in range(20):
            angle = 2 * math.pi * i / 20
            glVertex2f(self.x + self.radius * math.cos(angle), self.y + self.radius * math.sin(angle))
        glEnd()

class CrossTie(BaseDrawable):
    def __init__(self, punto_inicio, punto_fin, tamano_barra_tie, tamano_barra_long, direction, index):
        self.x1, self.y1 = punto_inicio
        self.x2, self.y2 = punto_fin
        self.tie_diameter = BAR_DIAMETERS_IN.get(tamano_barra_tie, 0)
        self.long_diameter = BAR_DIAMETERS_IN.get(tamano_barra_long, 0)
        self.hook_len = 6 * self.tie_diameter
        self.direction = direction
        self.index = index

    def is_clicked(self, world_x, world_y, pick_radius):
        """Verifica si un clic está cerca de la línea del crosstie."""
        dx, dy = self.x2 - self.x1, self.y2 - self.y1
        len_sq = dx*dx + dy*dy
        if len_sq == 0: return False

        t = max(0, min(1, ((world_x - self.x1) * dx + (world_y - self.y1) * dy) / len_sq))
        closest_x, closest_y = self.x1 + t * dx, self.y1 + t * dy
        
        dist_sq = (world_x - closest_x)**2 + (world_y - closest_y)**2
        return dist_sq < pick_radius**2

    def _draw_arc(self, cx, cy, radius, start_angle_deg, end_angle_deg, num_segments=20):
        glBegin(GL_LINE_STRIP)
        for i in range(num_segments + 1):
            angle_deg = start_angle_deg + (end_angle_deg - start_angle_deg) * i / num_segments
            rad = math.radians(angle_deg)
            x, y = cx + radius * math.cos(rad), cy + radius * math.sin(rad)
            glVertex2f(x, y)
        glEnd()

    def _draw_hook_at_point(self, hook_center, is_start_hook, tangent_offset_vector):
        C, R_long = hook_center, self.long_diameter / 2
        arc_radius = R_long
        P = (C[0] + tangent_offset_vector[0] * arc_radius, C[1] + tangent_offset_vector[1] * arc_radius)
        start_angle_rad = math.atan2(P[1] - C[1], P[0] - C[0])
        sweep_deg = 135 if is_start_hook else -135
        start_angle_deg, end_angle_deg = math.degrees(start_angle_rad), math.degrees(start_angle_rad) + sweep_deg
        self._draw_arc(C[0], C[1], arc_radius, start_angle_deg, end_angle_deg)
        end_angle_rad = math.radians(end_angle_deg)
        arc_end_point = (C[0] + arc_radius * math.cos(end_angle_rad), C[1] + arc_radius * math.sin(end_angle_rad))
        tangent_angle_rad = end_angle_rad + math.radians(90 if is_start_hook else -90)
        tail_end_point = (arc_end_point[0] + self.hook_len * math.cos(tangent_angle_rad), arc_end_point[1] + self.hook_len * math.sin(tangent_angle_rad))
        glBegin(GL_LINES); glVertex2f(arc_end_point[0], arc_end_point[1]); glVertex2f(tail_end_point[0], tail_end_point[1]); glEnd()
        return P

    def draw(self):
        glColor3f(0.6, 0.4, 0.3)
        glLineWidth(self.tie_diameter)
        C1, C2 = (self.x1, self.y1), (self.x2, self.y2)
        dx, dy = C2[0] - C1[0], C2[1] - C1[1]
        dist = math.hypot(dx, dy)
        if dist == 0: return
        tangent_dir_vec = (-dy / dist, dx / dist)
        p1 = self._draw_hook_at_point(C1, True, tangent_dir_vec)
        p2 = self._draw_hook_at_point(C2, False, tangent_dir_vec)
        glBegin(GL_LINES); glVertex2f(p1[0], p1[1]); glVertex2f(p2[0], p2[1]); glEnd()

class OpenGLCanvas(QGLWidget):
    statusMessage = pyqtSignal(str)
    canvasClicked = pyqtSignal(tuple)

    def __init__(self, parent=None):
        super(OpenGLCanvas, self).__init__(parent)
        self.objetos_a_dibujar = []
        self.zoom_level, self.pan_x, self.pan_y, self.rotation_angle = 1.0, 0.0, 0.0, 0.0
        self.last_mouse_pos = QPoint()
        self.ancho_escena, self.alto_escena = 40, 40

    def set_draw_objects(self, objetos, b, h, reset_view=True):
        self.objetos_a_dibujar = objetos
        if reset_view:
            self.rotation_angle = 0.0
            if b <= 0 or h <= 0:
                self.updateGL()
                return
            margin = 0.90
            zoom_x = self.ancho_escena / b if b > 0 else 1
            zoom_y = self.alto_escena / h if h > 0 else 1
            self.zoom_level = min(zoom_x, zoom_y) * margin
            self.pan_x, self.pan_y = b / 2, h / 2
        self.updateGL()

    def initializeGL(self):
        glClearColor(0.05, 0.05, 0.1, 1.0)
        glEnable(GL_LINE_SMOOTH); glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self.statusMessage.emit("Clic izquierdo: Mover/Seleccionar, Clic derecho: Rotar, Rueda: Zoom")

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        aspect_ratio = w / h if h > 0 else 1
        self.ancho_escena = 40 * aspect_ratio
        self.alto_escena = 40
        self._update_projection()

    def _update_projection(self):
        glMatrixMode(GL_PROJECTION); glLoadIdentity()
        gluOrtho2D(0, self.ancho_escena, 0, self.alto_escena)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW); glLoadIdentity()
        view_center_x, view_center_y = self.ancho_escena / 2, self.alto_escena / 2
        glTranslatef(view_center_x, view_center_y, 0.0)
        glScalef(self.zoom_level, self.zoom_level, 1.0)
        glRotatef(self.rotation_angle, 0.0, 0.0, 1.0)
        glTranslatef(-self.pan_x, -self.pan_y, 0.0)
        self._draw_axes()
        for obj in self.objetos_a_dibujar: obj.draw()

    def _draw_axes(self):
        glColor4f(1, 1, 1, 0.2); glLineWidth(1.0)
        glBegin(GL_LINES)
        glVertex2f(-1000, 0); glVertex2f(1000, 0)
        glVertex2f(0, -1000); glVertex2f(0, 1000)
        glEnd()

    def wheelEvent(self, event):
        self.zoom_level *= 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.updateGL()

    def screen_to_world(self, screen_pos):
        self.makeCurrent()
        modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
        projection = glGetDoublev(GL_PROJECTION_MATRIX)
        viewport = glGetIntegerv(GL_VIEWPORT)
        winX, winY = float(screen_pos.x()), float(viewport[3] - screen_pos.y())
        posX, posY, _ = gluUnProject(winX, winY, 0, modelview, projection, viewport)
        return posX, posY

    def mousePressEvent(self, event):
        self.last_mouse_pos = event.pos()
        if event.button() == Qt.LeftButton:
            world_pos = self.screen_to_world(event.pos())
            self.canvasClicked.emit(world_pos)

    def mouseMoveEvent(self, event):
        dx, dy = event.x() - self.last_mouse_pos.x(), event.y() - self.last_mouse_pos.y()
        if event.buttons() & Qt.LeftButton:
            if self.width() > 0 and self.zoom_level != 0:
                world_dx = (dx / self.width()) * self.ancho_escena / self.zoom_level
                world_dy = (dy / self.height()) * self.alto_escena / self.zoom_level
                self.pan_x -= world_dx; self.pan_y += world_dy
            self.statusMessage.emit(f"Pan: ({self.pan_x:.1f}, {self.pan_y:.1f})")
        elif event.buttons() & Qt.RightButton:
            self.rotation_angle += dx * 0.2
            self.statusMessage.emit(f"Rotación: {self.rotation_angle:.1f}°")
        self.last_mouse_pos = event.pos()
        self.updateGL()

class SectionDesignerScreen(QMainWindow):
    def __init__(self, sections_data=None):
        super(SectionDesignerScreen, self).__init__()
        self.sections = sections_data if sections_data and isinstance(sections_data, list) else [{
            "section": "Columna C-1 (Default)", "b": 500.0, "h": 750.0, "cover": 40.0,
            "rebar_size": "#8", "num_bars_2": 3, "num_bars_3": 4, "stirrup_size": "#4",
            "crossties_2_active": [True], "crossties_3_active": [True, True, False]
        }]
        self.drawn_crossties = []
        self.potential_crossties = []
        self.current_section_index = 0
        self.setWindowTitle("Visor de Secciones de Columna")
        self.setGeometry(100, 100, 1200, 800)
        self.canvas = OpenGLCanvas(self); self.setCentralWidget(self.canvas)
        self.setup_controls_panel()
        self.statusBar().showMessage("Listo.")
        self.canvas.statusMessage.connect(self.statusBar().showMessage)
        self.canvas.canvasClicked.connect(self.handle_canvas_click)
        self.units_input.setCurrentText("cm")
        self._load_section_data(self.current_section_index)

    def setup_controls_panel(self):
        dock = QDockWidget("Controles", self); dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)
        controls_widget = QWidget(); main_layout = QVBoxLayout(controls_widget); main_layout.setAlignment(Qt.AlignTop)
        section_mgm_group = QGroupBox("Gestión de Secciones"); section_mgm_layout = QVBoxLayout()
        self.section_selector = QComboBox(); self.section_selector.currentIndexChanged.connect(self._on_section_selected)
        new_section_button = QPushButton("Crear Nueva Sección"); new_section_button.clicked.connect(self._create_new_section)
        section_mgm_layout.addWidget(QLabel("Seleccionar Sección:")); section_mgm_layout.addWidget(self.section_selector)
        section_mgm_layout.addWidget(new_section_button); section_mgm_group.setLayout(section_mgm_layout)
        main_layout.addWidget(section_mgm_group)
        general_group = QGroupBox("Configuración General de Unidades"); general_layout = QVBoxLayout()
        self.units_input = QComboBox(); self.units_input.addItems(CONVERSION_FACTORS.keys())
        general_layout.addWidget(QLabel("Unidades de Entrada (para b, h, cover):")); general_layout.addWidget(self.units_input)
        general_group.setLayout(general_layout); main_layout.addWidget(general_group)
        geo_group = QGroupBox("Geometría de la Columna"); geo_layout = QVBoxLayout()
        self.b_input = QLineEdit("500.0"); self.h_input = QLineEdit("750.0"); self.cover_input = QLineEdit("40.0")
        self.units_input.currentTextChanged.connect(self._update_defaults_on_unit_change); self.units_input.setCurrentText("mm")
        geo_layout.addWidget(QLabel("Ancho (b):")); geo_layout.addWidget(self.b_input)
        geo_layout.addWidget(QLabel("Altura (h):")); geo_layout.addWidget(self.h_input)
        geo_layout.addWidget(QLabel("Recubrimiento:")); geo_layout.addWidget(self.cover_input)
        geo_group.setLayout(geo_layout); main_layout.addWidget(geo_group)
        rebar_group = QGroupBox("Refuerzo Longitudinal"); rebar_layout = QVBoxLayout()
        self.rebar_size_input = QComboBox(); self.rebar_size_input.addItems(BAR_DIAMETERS_IN.keys()); self.rebar_size_input.setCurrentText("#8")
        self.num_bars_2_input = QSpinBox(); self.num_bars_2_input.setMinimum(2); self.num_bars_2_input.setValue(3)
        self.num_bars_3_input = QSpinBox(); self.num_bars_3_input.setMinimum(2); self.num_bars_3_input.setValue(4)
        rebar_layout.addWidget(QLabel("Tamaño de Barra:")); rebar_layout.addWidget(self.rebar_size_input)
        rebar_layout.addWidget(QLabel("Barras en dirección 2:")); rebar_layout.addWidget(self.num_bars_2_input)
        rebar_layout.addWidget(QLabel("Barras en dirección 3:")); rebar_layout.addWidget(self.num_bars_3_input)
        rebar_group.setLayout(rebar_layout); main_layout.addWidget(rebar_group)
        trans_group = QGroupBox("Refuerzo Transversal"); trans_layout = QVBoxLayout()
        self.stirrup_size_input = QComboBox(); self.stirrup_size_input.addItems(['#3', '#4', '#5']); self.stirrup_size_input.setCurrentText('#4')
        self.num_crossties_2_input = QSpinBox() 
        self.num_crossties_3_input = QSpinBox()
        trans_layout.addWidget(QLabel("Tamaño de Estribo:")); trans_layout.addWidget(self.stirrup_size_input)
        trans_layout.addWidget(QLabel("Ganchos Suplementarios Verticales:")); trans_layout.addWidget(self.num_crossties_2_input)
        trans_layout.addWidget(QLabel("Ganchos Suplementarios Horizontales:")); trans_layout.addWidget(self.num_crossties_3_input)

        crosstie_buttons_layout = QHBoxLayout()
        self.btn_add_crosstie = QPushButton("Agregar Crosstie")
        self.btn_add_crosstie.setCheckable(True)
        self.btn_add_crosstie.clicked.connect(self.crosstie_button_clicked)
        self.btn_remove_crosstie = QPushButton("Eliminar Crosstie")
        self.btn_remove_crosstie.setCheckable(True)
        self.btn_remove_crosstie.clicked.connect(self.crosstie_button_clicked)
        crosstie_buttons_layout.addWidget(self.btn_add_crosstie)
        crosstie_buttons_layout.addWidget(self.btn_remove_crosstie)
        trans_layout.addLayout(crosstie_buttons_layout)

        trans_group.setLayout(trans_layout); main_layout.addWidget(trans_group)
        draw_button = QPushButton("Dibujar / Actualizar"); draw_button.clicked.connect(lambda: self.generate_drawing(reset_view=True))
        main_layout.addWidget(draw_button); dock.setWidget(controls_widget)
        self._populate_sections_dropdown()
        
    def set_selected_section(self, section_name):
        """
        Busca una sección por su nombre en el QComboBox y la selecciona.
        
        Args:
            section_name (str): El nombre de la sección a seleccionar.
        """
        index = self.section_selector.findText(section_name, Qt.MatchFixedString)
        if index >= 0:
            self.section_selector.setCurrentIndex(index)
            # El cambio de índice activará automáticamente _on_section_selected,
            # que cargará y dibujará la sección correcta.
        else:
            print(f"Advertencia: No se encontró la sección '{section_name}' en el Section Designer.")

    def handle_canvas_click(self, world_pos):
        world_x, world_y = world_pos
        pick_radius = 1.0 / self.canvas.zoom_level
        
        # Modo Eliminar
        if self.btn_remove_crosstie.isChecked():
            for ct in self.drawn_crossties:
                if ct.is_clicked(world_x, world_y, pick_radius):
                    data = self.sections[self.current_section_index]
                    if ct.direction == 'vertical':
                        data['crossties_2_active'][ct.index] = False
                    else:
                        data['crossties_3_active'][ct.index] = False
                    self.statusBar().showMessage(f"Crosstie específico eliminado. Actualizando...")
                    self.generate_drawing(reset_view=False)
                    return
        
        # Modo Agregar
        elif self.btn_add_crosstie.isChecked():
            closest_ct = None
            min_dist_sq = float('inf')
            
            for pot_ct in self.potential_crossties:
                mid_x, mid_y = (pot_ct.x1 + pot_ct.x2) / 2, (pot_ct.y1 + pot_ct.y2) / 2
                dist_sq = (world_x - mid_x)**2 + (world_y - mid_y)**2
                
                if dist_sq < min_dist_sq:
                    min_dist_sq = dist_sq
                    closest_ct = pot_ct
            
            if closest_ct:
                data = self.sections[self.current_section_index]
                if closest_ct.direction == 'vertical':
                    if not data['crossties_2_active'][closest_ct.index]:
                        data['crossties_2_active'][closest_ct.index] = True
                        self.statusBar().showMessage("Crosstie específico agregado. Actualizando...")
                        self.generate_drawing(reset_view=False)
                    else:
                        self.statusBar().showMessage("Ya existe un crosstie en esta posición.")
                else: # Horizontal
                    if not data['crossties_3_active'][closest_ct.index]:
                        data['crossties_3_active'][closest_ct.index] = True
                        self.statusBar().showMessage("Crosstie específico agregado. Actualizando...")
                        self.generate_drawing(reset_view=False)
                    else:
                        self.statusBar().showMessage("Ya existe un crosstie en esta posición.")

    def crosstie_button_clicked(self):
        sender = self.sender()
        if sender.isChecked():
            if sender == self.btn_add_crosstie:
                self.btn_remove_crosstie.setChecked(False)
                self.statusBar().showMessage("Modo 'Agregar Crosstie' activado. Haga clic para añadir un gancho.")
            else:
                self.btn_add_crosstie.setChecked(False)
                self.statusBar().showMessage("Modo 'Eliminar Crosstie' activado. Haga clic en un gancho para eliminarlo.")
        else:
            self.statusBar().showMessage(f"Modo '{sender.text()}' desactivado.")

    def _populate_sections_dropdown(self):
        self.section_selector.blockSignals(True)
        self.section_selector.clear()
        self.section_selector.addItems([s['section'] for s in self.sections])
        self.section_selector.setCurrentIndex(self.current_section_index)
        self.section_selector.blockSignals(False)

    def _on_section_selected(self, index):
        if index == -1 or index == self.current_section_index: return
        self._save_current_section_data()
        self._load_section_data(index)

    def _load_section_data(self, index):
        self.current_section_index = index
        data = self.sections[index]
        for widget in self.findChildren(QWidget): widget.blockSignals(True)
        self.setWindowTitle(f"Visor de Secciones - {data['section']}")
        self.b_input.setText(str(data.get('b', '50.0')))
        self.h_input.setText(str(data.get('h', '75.0')))
        self.cover_input.setText(str(data.get('cover', '4.0')))
        self.rebar_size_input.setCurrentText(data.get('rebar_size', '#8'))
        self.num_bars_2_input.setValue(data.get('num_bars_2', 3))
        self.num_bars_3_input.setValue(data.get('num_bars_3', 4))
        self.stirrup_size_input.setCurrentText(data.get('stirrup_size', '#4'))
        self.section_selector.setCurrentIndex(index)
        for widget in self.findChildren(QWidget): widget.blockSignals(False)
        self.generate_drawing(reset_view=True)

    def _save_current_section_data(self):
        if self.current_section_index < 0 or self.current_section_index >= len(self.sections): return
        data = self.sections[self.current_section_index]
        try:
            data['b'] = float(self.b_input.text())
            data['h'] = float(self.h_input.text())
            data['cover'] = float(self.cover_input.text())
            data['rebar_size'] = self.rebar_size_input.currentText()
            data['num_bars_2'] = self.num_bars_3_input.value()
            data['num_bars_3'] = self.num_bars_2_input.value()
            data['stirrup_size'] = self.stirrup_size_input.currentText()
        except ValueError as e: self.statusBar().showMessage(f"Error al guardar datos: {e}. Entrada inválida.")

    def _create_new_section(self):
        self._save_current_section_data()
        new_name, ok = QInputDialog.getText(self, "Crear Nueva Sección", "Nombre de la nueva sección:")
        if ok and new_name:
            if any(s['section'] == new_name for s in self.sections):
                QMessageBox.warning(self, "Error", "Ya existe una sección con ese nombre."); return
            new_section_data = self.sections[self.current_section_index].copy()
            new_section_data['section'] = new_name
            new_section_data['crossties_2_active'] = new_section_data.get('crossties_2_active', []).copy()
            new_section_data['crossties_3_active'] = new_section_data.get('crossties_3_active', []).copy()
            self.sections.append(new_section_data)
            self.current_section_index = len(self.sections) - 1
            self._populate_sections_dropdown()
            self.statusBar().showMessage(f"Sección '{new_name}' creada.")

    def _update_defaults_on_unit_change(self, unit):
        if unit == 'pulgadas': self.b_input.setText("20.0"); self.h_input.setText("30.0"); self.cover_input.setText("1.5")
        elif unit == 'cm': self.b_input.setText("50.0"); self.h_input.setText("75.0"); self.cover_input.setText("4.0")
        elif unit == 'mm': self.b_input.setText("500.0"); self.h_input.setText("750.0"); self.cover_input.setText("40.0")

    def generate_drawing(self, reset_view=True):
        self._save_current_section_data()
        try:
            data = self.sections[self.current_section_index]
            unit, factor = self.units_input.currentText(), CONVERSION_FACTORS[self.units_input.currentText()]
            b, h, cover = data['b'] * factor, data['h'] * factor, data['cover'] * factor
            rebar_size, stirrup_size = data['rebar_size'], data['stirrup_size']
            num_bars_2, num_bars_3 = data['num_bars_2'], data['num_bars_3']
            
            max_ct_2 = max(0, num_bars_2 - 2)
            if 'crossties_2_active' not in data or len(data['crossties_2_active']) != max_ct_2:
                data['crossties_2_active'] = [False] * max_ct_2
            max_ct_3 = max(0, num_bars_3 - 2)
            if 'crossties_3_active' not in data or len(data['crossties_3_active']) != max_ct_3:
                data['crossties_3_active'] = [False] * max_ct_3
            
            self.num_crossties_2_input.setValue(sum(data['crossties_2_active']))
            self.num_crossties_3_input.setValue(sum(data['crossties_3_active']))

            objetos = [Columna(0, 0, b, h), EstriboPrincipal(b, h, cover, stirrup_size, rebar_size)]
            self.drawn_crossties.clear(); self.potential_crossties.clear()

            stirrup_bar_d, rebar_d = BAR_DIAMETERS_IN[stirrup_size], BAR_DIAMETERS_IN[rebar_size]
            x_start = cover + stirrup_bar_d + rebar_d / 2; x_end = b - cover - stirrup_bar_d - rebar_d / 2
            y_start = cover + stirrup_bar_d + rebar_d / 2; y_end = h - cover - stirrup_bar_d - rebar_d / 2
            spacing_x = (x_end - x_start) / (num_bars_2 - 1) if num_bars_2 > 1 else 0
            spacing_y = (y_end - y_start) / (num_bars_3 - 1) if num_bars_3 > 1 else 0
            positions = set()
            for i in range(num_bars_2): positions.add((x_start + i * spacing_x, y_start)); positions.add((x_start + i * spacing_x, y_end))
            for i in range(1, num_bars_3 - 1): positions.add((x_start, y_start + i * spacing_y)); positions.add((x_end, y_start + i * spacing_y))
            for pos in sorted(list(positions)): objetos.append(BarraLongitudinal(pos, rebar_size))
            
            interior_bars_x = [x_start + i * spacing_x for i in range(1, num_bars_2 - 1)]
            for i in range(len(interior_bars_x)):
                ct = CrossTie((interior_bars_x[i], y_start), (interior_bars_x[i], y_end), stirrup_size, rebar_size, 'vertical', i)
                self.potential_crossties.append(ct)
                if i < len(data['crossties_2_active']) and data['crossties_2_active'][i]:
                    objetos.append(ct)
                    self.drawn_crossties.append(ct)

            interior_bars_y = [y_start + i * spacing_y for i in range(1, num_bars_3 - 1)]
            for i in range(len(interior_bars_y)):
                ct = CrossTie((x_start, interior_bars_y[i]), (x_end, interior_bars_y[i]), stirrup_size, rebar_size, 'horizontal', i)
                self.potential_crossties.append(ct)
                if i < len(data['crossties_3_active']) and data['crossties_3_active'][i]:
                    objetos.append(ct)
                    self.drawn_crossties.append(ct)
            
            self.canvas.set_draw_objects(objetos, b, h, reset_view=reset_view)
            
        except (ValueError, KeyError) as e: self.statusBar().showMessage(f"Error en datos: {e}")
        except Exception as e: self.statusBar().showMessage(f"Error inesperado: {e}")