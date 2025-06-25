from PyQt5.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout,QTableWidget, QTableWidgetItem,
    QScrollArea, QFrame,QLabel, QComboBox, QOpenGLWidget, QHBoxLayout,
    QSizePolicy
)
from PyQt5.QtCore import pyqtSignal, QPoint, Qt
from PyQt5.QtGui import QPainter, QColor, QFont

from OpenGL.GL import (
    glClearColor, glViewport, glMatrixMode, GL_PROJECTION,
    glLoadIdentity, glOrtho, GL_MODELVIEW, glClear,
    GL_COLOR_BUFFER_BIT, glColor4f, glBegin, glEnd,
    glVertex2f, GL_QUADS, glLineWidth,
    glColor3f, GL_LINE_LOOP, glPointSize,
    GL_POINTS, glEnable, GL_DEPTH_TEST,
    glTranslatef, glScalef, glRotatef, GL_LINES,
    GL_DEPTH_BUFFER_BIT, glGetDoublev, GL_MODELVIEW_MATRIX,
    GL_PROJECTION_MATRIX, glGetIntegerv, GL_VIEWPORT
    
)

from OpenGL.error import GLError

from OpenGL.GLU import *


class OpenGLDrawingWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super(OpenGLDrawingWidget, self).__init__(parent)
        self.setMinimumSize(200,200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        
        # --- NUEVO: Parámetros de Mundo Configurables ---
        # Centralizamos aquí los valores que definen la escala de la vista.
        # Cambia estos valores para que se ajusten a tus datos.
        self.INITIAL_WORLD_WIDTH = 6000  # Ancho inicial visible en unidades de mundo
        self.GRID_SPACING = 500          # Espaciado de la rejilla
        self.GRID_RANGE = 5000           # Tamaño total de la rejilla a dibujar
        
        # --- Variables de estado para la navegación ---
        self.zoom_level = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.rotation_angle = 0.0

        # --- Variables para el control del ratón ---
        self.last_mouse_pos = QPoint()

        # Datos a dibujar
        self.points_to_draw = []
        self.rects_to_draw = []
        
        # Factores de conversión de píxeles a coordenadas de mundo
        self._pixel_to_world_x = 1.0
        self._pixel_to_world_y = 1.0
        
    def update_data(self, points=None, rects=None):
        self.points_to_draw = points if points is not None else []
        self.rects_to_draw = rects if rects is not None else []
        self.update() # Importante: Agenda llamada a paintGL()
        
    def initializeGL(self):
        # Color de fondo gris claro
        glClearColor(0.1, 0.1, 0.15, 1.0)  # Fondo gris oscuro
        glEnable(GL_DEPTH_TEST)
        
        
    def resizeGL(self, width, height):
        # El viewport es el area de la ventana donde se renderizara
        glViewport(0, 0, width, height)
        
        # Configurar la proyección ortográfica 2D
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        
        # Usamos los parámetros de mundo configurables
        world_width = self.INITIAL_WORLD_WIDTH
        world_height = (world_width * height) / width if width > 0 else world_width

        self._pixel_to_world_x = world_width / width if width > 0 else 1
        self._pixel_to_world_y = world_height / height if height > 0 else 1

        glOrtho(-world_width / 2, world_width / 2, 
                world_height / 2, -world_height / 2, 
                -1.0, 1.0)
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
    def paintGL(self):
        # Limpiar el buffer de color
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Cargar la matriz de identidad para empezar a dibujar desde cero
        glLoadIdentity()
        
         # --- 1. APLICAR TRANSFORMACIONES DE LA VISTA (CÁMARA) ---
        # El orden es importante: Escala y Rota primero, luego Traslada (Paneo).
        glTranslatef(self.pan_x, self.pan_y, 0)
        glScalef(self.zoom_level, self.zoom_level, 1.0)
        glRotatef(self.rotation_angle, 0.0, 0.0, 1.0)

        # --- 2. DIBUJAR LOS ELEMENTOS DE LA ESCENA ---
        self._draw_axes_and_grid()
        self._draw_scene_objects()
        
        # -- Preparar QPainter para dibujar overlays (texto) --
        
        # --- 3. DIBUJAR TEXTO Y OVERLAYS CON QPAINTER ---
        # QPainter es ideal para dibujar texto 2D sobre la escena de OpenGL.
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Dibujar las etiquetas de los elementos
        self._draw_element_labels(painter)
        
        painter.setPen(QColor(200, 200, 200))
        painter.setFont(QFont('Arial', 8))
        # Muestra información de estado en una esquina
        painter.drawText(20, 30, f"Zoom: {self.zoom_level:.2f}x | Pan: ({self.pan_x:.0f}, {self.pan_y:.0f}) | Rot: {self.rotation_angle:.1f}°")
        painter.drawText(20,50, "Doble Clic para reiniciar vistas")
        painter.end() # Importante para finalizar el painter
        
    def _get_screen_coords(self, world_x, world_y):
        try:
            # Obtenemos las matrices de transformación y el viewport actuales de OpenGL
            modelview_matrix = glGetDoublev(GL_MODELVIEW_MATRIX)
            projection_matrix = glGetDoublev(GL_PROJECTION_MATRIX)
            viewport = glGetIntegerv(GL_VIEWPORT)
            
            # gluProject hace la magia de convertir mundo -> pantalla
            screen_x, screen_y, _ = gluProject(world_x, world_y, 0, modelview_matrix, projection_matrix, viewport)
            
            # La coordenada Y de OpenGL es opuesta a la de QPainter
            return QPoint(int(screen_x), int(self.height() - screen_y))
        except GLError:
            # Puede ocurrir un error si el contexto no está listo, devolvemos un punto fuera de la pantalla
            return QPoint(-1, -1)
        
    def _draw_element_labels(self, painter):
        """
        NUEVO: Dibuja las etiquetas de texto para cada elemento usando QPainter.
        """
        # Solo muestra las etiquetas si el zoom es suficientemente grande
        # para evitar que la pantalla se sature.
        if self.zoom_level < 0.3:
            return

        painter.setPen(QColor(255, 255, 100)) # Color amarillo para las etiquetas
        painter.setFont(QFont('Arial', 9))

        # Etiquetas para los rectángulos (en su centro)
        for rect in self.rects_to_draw:
            if 'name' in rect:
                center_x = rect['x'] + rect['w'] / 2
                center_y = rect['y'] + rect['h'] / 2
                screen_pos = self._get_screen_coords(center_x, center_y)
                if screen_pos.x() > 0:
                    painter.drawText(screen_pos, rect['name'])

        # Etiquetas para los puntos (ligeramente desplazadas)
        for point in self.points_to_draw:
            if 'name' in point:
                screen_pos = self._get_screen_coords(point['x'], point['y'])
                if screen_pos.x() > 0:
                    # Desplazamos el texto para que no se dibuje encima del punto
                    painter.drawText(screen_pos.x() + 8, screen_pos.y() - 8, point['name'])
        
    def _draw_axes_and_grid(self):
        # --- Dibuja la rejilla ---
        grid_spacing = 500  # Espaciado de la rejilla en coordenadas de mundo
        grid_range = 5000   # Extensión de la rejilla
        
        glLineWidth(1.0)
        glColor3f(0.2, 0.2, 0.25) # Color de la rejilla (gris oscuro)
        glBegin(GL_LINES)
        # Líneas verticales
        for x in range(-grid_range, grid_range + 1, grid_spacing):
            glVertex2f(x, -grid_range)
            glVertex2f(x, grid_range)
        # Líneas horizontales
        for y in range(-grid_range, grid_range + 1, grid_spacing):
            glVertex2f(-grid_range, y)
            glVertex2f(grid_range, y)
        glEnd()

        # --- Dibuja los ejes X e Y ---
        glLineWidth(2.0)
        glBegin(GL_LINES)
        # Eje X (Rojo)
        glColor3f(1.0, 0.0, 0.0)
        glVertex2f(-grid_range, 0)
        glVertex2f(grid_range, 0)
        # Eje Y (Verde)
        glColor3f(0.0, 1.0, 0.0)
        glVertex2f(0, -grid_range)
        glVertex2f(0, grid_range)
        glEnd()
        
    def _draw_scene_objects(self):
    # Dibuja los rectángulos y puntos (código de la respuesta anterior)
        if self.rects_to_draw:
            glColor4f(0.20, 0.59, 0.85, 0.4) 
            for rect_data in self.rects_to_draw:
                x, y, w, h = rect_data['x'], rect_data['y'], rect_data['w'], rect_data['h']
                glBegin(GL_QUADS)
                glVertex2f(x, y); glVertex2f(x + w, y); glVertex2f(x + w, y + h); glVertex2f(x, y + h)
                glEnd()
        
            glLineWidth(2.0)
            glColor3f(0.20, 0.59, 0.85)
            for rect_data in self.rects_to_draw:
                x, y, w, h = rect_data['x'], rect_data['y'], rect_data['w'], rect_data['h']
                glBegin(GL_LINE_LOOP)
                glVertex2f(x, y); glVertex2f(x + w, y); glVertex2f(x + w, y + h); glVertex2f(x, y + h)
                glEnd()
    
        if self.points_to_draw:
            glPointSize(8.0)
            glColor3f(0.90, 0.30, 0.23)
            glBegin(GL_POINTS)
            for point_data in self.points_to_draw:
                glVertex2f(point_data['x'], point_data['y'])
            glEnd()
        
    # --- Métodos de Eventos del Ratón ---
    
    def mousePressEvent(self, event):
        # Almacena la posición inicial al hacer clic
        self.last_mouse_pos = event.pos()
        
    def mouseMoveEvent(self, event):
        delta = event.pos() - self.last_mouse_pos
        
        # Comprobar qué botón del ratón y qué teclas modificadoras se están usando
        if event.buttons() & Qt.MiddleButton:
            modifiers = event.modifiers()
            if modifiers & Qt.ControlModifier:
                # Rotación con Ctrl + Botón Central
                self.rotation_angle += delta.x() * 0.5  # Ajusta la sensibilidad
            else:
                # Paneo con Botón Central
                # Convertimos el delta de píxeles a coordenadas de mundo
                self.pan_x += delta.x() * self._pixel_to_world_x / self.zoom_level
                self.pan_y += delta.y() * self._pixel_to_world_y / self.zoom_level

        self.last_mouse_pos = event.pos()
        self.update() # Solicitar redibujado
        
    def wheelEvent(self, event):
        # --- MODIFICADO: Implementación de Zoom Inteligente ---
        
        # 1. Obtenemos la posición del ratón en coordenadas del widget
        screen_pos = event.pos()
        
        # 2. Calculamos la posición en el mundo que está debajo del cursor *antes* de hacer zoom
        # Para esto, necesitamos "deshacer" las transformaciones actuales (pan, zoom, rotación)
        # La fórmula se simplifica a:
        world_x_before_zoom = (screen_pos.x() - self.width() / 2) * self._pixel_to_world_x / self.zoom_level - self.pan_x / self.zoom_level
        world_y_before_zoom = (screen_pos.y() - self.height() / 2) * self._pixel_to_world_y / self.zoom_level - self.pan_y / self.zoom_level
        
        # 3. Calculamos el factor de zoom
        delta = event.angleDelta().y()
        zoom_factor = 1.15 if delta > 0 else 1 / 1.15
        
        new_zoom_level = self.zoom_level * zoom_factor
        new_zoom_level = max(0.01, min(new_zoom_level, 100.0)) # Limitar
        
        # 4. La magia: ajustamos el paneo para que el punto bajo el cursor no se mueva.
        # El nuevo paneo será una interpolación entre el paneo antiguo y la posición del mundo.
        self.pan_x = world_x_before_zoom * (1 - zoom_factor) + self.pan_x * zoom_factor
        self.pan_y = world_y_before_zoom * (1 - zoom_factor) + self.pan_y * zoom_factor
        
        self.zoom_level = new_zoom_level

        self.update()
        
    def mouseDoubleClickEvent(self, event):
        # --- NUEVO: Restablecer la vista con doble clic ---
        print("Vista restablecida.")
        self.zoom_level = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.rotation_angle = 0.0
        self.update()

class InfoGridLinesScreen(QWidget):
    datos_para_renombrar = pyqtSignal(dict)
    def __init__(self, gridlines ,stories,parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gridlines Data")
        self.resize(800, 450)
        
        stories_data = []
        for story in stories:
            stories_data.append(story['nombre'])
        
        # Datos de ejemplo para el dibujo
        points_data = []
        for gridline in gridlines:
            # print(gridline['GridLine'], gridline['pos_x'], gridline['pos_y'])
            points_data.append({
                'name': str(gridline['GridLine']),
                'x': gridline['pos_x'],
                'y': gridline['pos_y']
            })
            
            
        self.drawing_data_by_story = {key['nombre']: {'points': points_data, 'rects': []} for key in stories}
        
        # Agregar "No selection"
        self.drawing_data_by_story['No selection'] = {
             "points": [],
                "rects": []
        }
        
           
        combo_items = list(self.drawing_data_by_story.keys())
            
            
#         self.drawing_data_by_story = {
#     "Story 1": {
#         "points": [
#             {'name': 'P1', 'x': -1000, 'y': -500}, 
#             {'name': 'P2', 'x': 1000, 'y': 500}
#         ],
#         "rects": [
#             {'name': 'Muro-A', 'x': -2000, 'y': -1500, 'w': 800, 'h': 3000}
#         ]
#     },
#     "Story 2": {
#         "points": [
#             {'name': 'P3', 'x': -500, 'y': 1800}
#         ],
#         "rects": [
#             {'name': 'Viga-B1', 'x': 200, 'y': 800, 'w': 1200, 'h': 600},
#             {'name': 'Viga-B2', 'x': 200, 'y': 1800, 'w': 1200, 'h': 600}
#         ]
#     },
#     "No selection": {
#         "points": [],
#         "rects": []
#     }
# }
        
        
        
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(10,10,10,10)
        self.main_layout.setSpacing(10)
        
        # -- Panel Izquierdo
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)
        self.left_layout.setContentsMargins(0,0,0,0)
        
        self.title_label = QLabel("Stories Info")
        self.table_gridlines_info = QTableWidget(len(gridlines),4) # Modify with len of stories list
        self.table_gridlines_info.setHorizontalHeaderLabels(["GridLine", "Pos X", "Pos Y", "New GridLine Name"])
    
        # Configure QTable
        
        for gridline_idx, gridline in enumerate(gridlines):
            # Col 0: Gridline
            item_name = QTableWidgetItem(str(gridline['GridLine']))
            self.table_gridlines_info.setItem(gridline_idx, 0, item_name)
            
            # Col 1: Pos X
            item_pos_x = QTableWidgetItem(str(gridline['pos_x']))
            self.table_gridlines_info.setItem(gridline_idx, 1, item_pos_x)
            
            # Col 2: Pos Y
            item_pos_y = QTableWidgetItem(str(gridline['pos_y']))
            self.table_gridlines_info.setItem(gridline_idx, 2, item_pos_y)
            
        self.table_gridlines_info.resizeColumnsToContents()
        
        self.btn_modificar_gridlines = QPushButton("Modificar Gridlines")
        
        self.left_layout.addWidget(self.title_label)
        self.left_layout.addWidget(self.table_gridlines_info)
        self.left_layout.addWidget(self.btn_modificar_gridlines)
        
    
        # -- Panel Derecho (OpenGL)
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(0,0,0,0)
        
        self.story_selector_label = QLabel("Select Story to View")
        self.story_selector_combo = QComboBox()
        self.story_selector_combo.addItems(combo_items)
        
        # Se instancia el widget de OpenGL en lugar del de QPainter.
        self.drawing_canvas = OpenGLDrawingWidget(self)
        
        # *** LÍNEA CLAVE A AÑADIR ***
        # Le decimos al widget que se expanda en ambas direcciones
        self.drawing_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.right_layout.addWidget(self.story_selector_label)
        self.right_layout.addWidget(self.story_selector_combo)
        self.right_layout.addWidget(self.drawing_canvas)
        
        # --- Añadir paneles al layout principal ---
        self.main_layout.addWidget(self.left_panel, 1) 
        self.main_layout.addWidget(self.right_panel, 1)
        
        # Conectar el click del boton a la funcion que emite la senal
        self.btn_modificar_gridlines.clicked.connect(self._emitir_datos_mapeo)
        self.story_selector_combo.currentIndexChanged.connect(self._on_story_changed)
        
        self._on_story_changed()
        
    def _on_story_changed(self):
        """
        Slot que se activa cuando el usuario cambia la selección. (Sin cambios)
        """
        selected_story = self.story_selector_combo.currentText()
        data = self.drawing_data_by_story.get(selected_story, self.drawing_data_by_story["No selection"])
        self.drawing_canvas.update_data(points=data["points"], rects=data["rects"])
        
    def _emitir_datos_mapeo(self):
        print('modificar nombres GriLines')
        mapa = {}
        for fila in range(self.table_gridlines_info.rowCount()):
            item_original = self.table_gridlines_info.item(fila, 0)
            item_nuevo = self.table_gridlines_info.item(fila,3)
           
        
            # Asegurarse de que ambas celdas tengan texto
            if item_original and item_original.text() and item_nuevo and item_nuevo.text():
                valor_original = item_original.text().strip()
                valor_nuevo = item_nuevo.text().strip()
                 # Cambiar en la tabla y borrar nuevo valor
                self.table_gridlines_info.item(fila,0).setText(item_nuevo.text())
                self.table_gridlines_info.item(fila,3).setText("")
            
                if valor_original:
                    mapa[valor_original] = valor_nuevo
            
        # Emitir la senal con el diccionario como payload
        self.datos_para_renombrar.emit(mapa)
            
        