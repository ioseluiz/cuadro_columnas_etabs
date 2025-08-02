import sys
import math
import json
import os
import copy
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QOpenGLWidget,
    QSplitter, QHeaderView, QAbstractItemView, QDialog, QLineEdit,
    QLabel, QDialogButtonBox, QFormLayout, QMessageBox, QListWidget,
    QListWidgetItem
)
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QRectF
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPolygonF
from OpenGL.GL import *
from OpenGL.GLU import *

# --- Clases del Modelo de Datos ---

class Column:
    """
    Clase que representa una columna con sus propiedades.
    """
    def __init__(self, col_id, x, y, group_id=None):
        self.id = col_id
        self.x = float(x)
        self.y = float(y)
        self.group_id = group_id

    def __repr__(self):
        return f"Column(id={self.id}, x={self.x}, y={self.y}, group={self.group_id})"


# --- Widgets Personalizados (OpenGL y Diálogos) ---

class OpenGLWidget(QOpenGLWidget):
    """
    Widget para renderizar la escena 2D de las columnas usando OpenGL.
    """
    # Señales para comunicar interacciones a la ventana principal
    column_clicked_signal = pyqtSignal(str)
    selection_changed_by_click_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.columns = {}
        self.selected_column_id = None
        self.group_highlight_ids = []

        # Atributos para navegación (pan y zoom)
        self.zoom_factor = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.last_mouse_pos = QPoint()
        
        # Tamaño de los elementos en el dibujo
        self.point_size = 10.0
        self.selection_radius = 12.0

    def set_data(self, columns_data):
        """Actualiza los datos de las columnas a dibujar."""
        self.columns = columns_data
        self.update()

    def set_selection(self, selected_id, group_ids):
        """Actualiza la columna seleccionada y las del mismo grupo."""
        self.selected_column_id = selected_id
        self.group_highlight_ids = group_ids
        self.update()

    # ### INICIO DE CAMBIOS ###
    def fit_to_screen(self):
        """Ajusta el zoom y el paneo para centrar todas las columnas en la vista."""
        if not self.columns:
            # Resetea la vista si no hay columnas
            self.pan_x = 0.0
            self.pan_y = 0.0
            self.zoom_factor = 1.0
            self.update()
            return

        # Calcular el bounding box de todas las columnas
        min_x = min(c.x for c in self.columns.values())
        max_x = max(c.x for c in self.columns.values())
        min_y = min(c.y for c in self.columns.values())
        max_y = max(c.y for c in self.columns.values())

        # Añadir un pequeño margen
        padding = 20
        bbox_width = (max_x - min_x) + padding * 2
        bbox_height = (max_y - min_y) + padding * 2

        if bbox_width == 0 or bbox_height == 0:
            # Si solo hay un punto o todos están en la misma línea, evitar división por cero
            bbox_width = max(bbox_width, 100)
            bbox_height = max(bbox_height, 100)

        # Centrar la vista en el centro del bounding box
        center_x = min_x + (max_x - min_x) / 2
        center_y = min_y + (max_y - min_y) / 2
        self.pan_x = -center_x
        self.pan_y = -center_y
        
        # Calcular el factor de zoom necesario para ajustar el bounding box
        widget_w = self.width()
        widget_h = self.height()
        
        if widget_w == 0 or widget_h == 0: return

        zoom_x = widget_w / bbox_width
        zoom_y = widget_h / bbox_height
        
        self.zoom_factor = min(zoom_x, zoom_y) * 0.95 # 0.95 para un pequeño margen extra

        self.update() # Vuelve a dibujar la escena con la nueva vista
    # ### FIN DE CAMBIOS ###

    def initializeGL(self):
        """Configuración inicial de OpenGL."""
        glClearColor(0.1, 0.1, 0.15, 1.0) # Fondo oscuro

    def resizeGL(self, w, h):
        """Se llama al cambiar el tamaño del widget."""
        glViewport(0, 0, w, h)

    def paintGL(self):
        """El corazón del dibujado en OpenGL."""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        w = self.width()
        h = self.height()

        # Prevenir división por cero
        if self.zoom_factor == 0: self.zoom_factor = 1.0
        if h == 0: h = 1 
        
        view_height = self.height() / self.zoom_factor
        view_width = self.width() / self.zoom_factor
        
        glOrtho(-view_width / 2.0, view_width / 2.0, -view_height / 2.0, view_height / 2.0, -1, 1)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        # Aplicar paneo aquí
        glTranslated(self.pan_x, self.pan_y, 0)
        
        self._draw_axes()
        self._draw_grid()
        self._draw_highlights()
        self._draw_columns()
        self._draw_column_ids()

    def _draw_axes(self):
        """Dibuja los ejes X e Y."""
        glColor3f(0.5, 0.5, 0.5)
        glLineWidth(2.0)
        glBegin(GL_LINES)
        glVertex2f(-10000, 0)
        glVertex2f(10000, 0)
        glVertex2f(0, -10000)
        glVertex2f(0, 10000)
        glEnd()

    def _draw_grid(self):
        """Dibuja una grilla de fondo."""
        glColor3f(0.2, 0.2, 0.25)
        glLineWidth(1.0)
        glBegin(GL_LINES)
        grid_spacing = 50 * (1/self.zoom_factor if self.zoom_factor > 0.5 else 2.0)
        
        for i in range(-100, 101):
            pos = i * grid_spacing
            glVertex2f(-10000, pos)
            glVertex2f(10000, pos)
            glVertex2f(pos, -10000)
            glVertex2f(pos, 10000)
        glEnd()


    def _draw_columns(self):
        """Dibuja las columnas como puntos."""
        glPointSize(self.point_size)
        glBegin(GL_POINTS)
        for col in self.columns.values():
            if col.id == self.selected_column_id:
                glColor3f(1.0, 1.0, 0.0)
            else:
                glColor3f(0.3, 0.7, 1.0)
            glVertex2f(col.x, col.y)
        glEnd()

    def _draw_highlights(self):
        """Dibuja círculos de resaltado para la selección y el grupo."""
        for group_col_id in self.group_highlight_ids:
            print(f"group_col_id: {group_col_id}")
            if group_col_id in self.columns and group_col_id != self.selected_column_id:
                col = self.columns[group_col_id]
                print(f"col: {col.id}, x: {col.x}, y: {col.y}")
                print(f"type col id: {type(col.id)}")
                print(f"type col x: {type(col.x)}")
                print(f"type col y: {type(col.y)}")
                
                print(self.columns)
                print(self.selection_radius)
                self._draw_circle(col.x, col.y, self.selection_radius, (1.0, 0.6, 0.0))

        if self.selected_column_id and self.selected_column_id in self.columns:
            col = self.columns[self.selected_column_id]
            self._draw_circle(col.x, col.y, self.selection_radius, (1.0, 1.0, 0.0))


    def _draw_circle(self, cx, cy, r, color):
        """Función auxiliar para dibujar un círculo."""
        scaled_r = r / self.zoom_factor

        num_segments = 30
        glLineWidth(2.0)  # Puedes hacer esto también escalado si quieres: 2.0 / self.scale
        glColor3f(*color)
        glBegin(GL_LINE_LOOP)
        for i in range(num_segments):
            theta = 2.0 * math.pi * i / num_segments
            
            # Usamos el radio escalado para calcular las posiciones de los vértices
            x = scaled_r * math.cos(theta)
            y = scaled_r * math.sin(theta)
            
            glVertex2f(x + cx, y + cy)
        glEnd()

    def _draw_column_ids(self):
        """Dibuja los IDs de las columnas usando QPainter."""
        painter = QPainter(self)
        painter.beginNativePainting()
        # No es necesario llamar a endNativePainting() inmediatamente aquí.
        # Se debe llamar después de haber configurado la transformación de OpenGL
        gl_modelview_matrix = glGetDoublev(GL_MODELVIEW_MATRIX)
        gl_projection_matrix = glGetDoublev(GL_PROJECTION_MATRIX)
        gl_viewport = glGetIntegerv(GL_VIEWPORT)
        painter.endNativePainting() # Fin de la pintura nativa para configurar QPainter

        painter.setPen(QColor(255, 255, 255))
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)

        for col in self.columns.values():
            # Usar gluProject para convertir coordenadas del mundo a pantalla
            # Es más robusto que un cálculo manual
            winX, winY, _ = gluProject(col.x, col.y, 0, 
                                       gl_modelview_matrix, 
                                       gl_projection_matrix, 
                                       gl_viewport)
            
            # La coordenada Y de OpenGL va de abajo hacia arriba, QPainter de arriba hacia abajo
            winY = gl_viewport[3] - winY 
            
            if winX is not None and winY is not None:
                painter.drawText(QPoint(int(winX) + 10, int(winY) + 5), col.id)
        
        painter.end()


    def world_to_screen(self, world_x, world_y):
        """Convierte coordenadas del mundo a coordenadas de pantalla."""
        screen_x = (world_x + self.pan_x) * self.zoom_factor + self.width() / 2
        screen_y = (-world_y - self.pan_y) * self.zoom_factor + self.height() / 2
        return QPoint(int(screen_x), int(screen_y))

    def screen_to_world(self, screen_pos):
        """Convierte coordenadas de pantalla a coordenadas del mundo."""
        x = (screen_pos.x() - self.width() / 2) / self.zoom_factor - self.pan_x
        y = -((screen_pos.y() - self.height() / 2) / self.zoom_factor + self.pan_y)
        return x, y

    def wheelEvent(self, event):
        """Maneja el zoom con la rueda del mouse."""
        delta = event.angleDelta().y()
        if delta > 0:
            self.zoom_factor *= 1.1
        else:
            self.zoom_factor /= 1.1
        self.zoom_factor = max(0.01, min(self.zoom_factor, 100.0))
        self.update()

    def mousePressEvent(self, event):
        """Maneja el inicio del paneo y la selección de columnas."""
        self.last_mouse_pos = event.pos()
        if event.button() == Qt.LeftButton:
            world_x, world_y = self.screen_to_world(event.pos())
            pick_radius = self.point_size / self.zoom_factor
            found_col = None
            min_dist_sq = (pick_radius * 2)**2 
            for col in self.columns.values():
                dist_sq = (col.x - world_x)**2 + (col.y - world_y)**2
                if dist_sq < min_dist_sq:
                    min_dist_sq = dist_sq
                    found_col = col
            if found_col:
                if event.modifiers() == Qt.ControlModifier:
                    self.column_clicked_signal.emit(found_col.id)
                else:
                    self.selection_changed_by_click_signal.emit(found_col.id)

    def mouseMoveEvent(self, event):
        """Maneja el movimiento de paneo."""
        if event.buttons() == Qt.MidButton or (event.buttons() == Qt.LeftButton and event.modifiers() == Qt.ShiftModifier):
            delta = event.pos() - self.last_mouse_pos
            self.pan_x += delta.x() / self.zoom_factor
            self.pan_y -= delta.y() / self.zoom_factor
            self.last_mouse_pos = event.pos()
            self.update()
            
    def set_columns_data(self, columns_data):
        """
        Método público para recibir nuevos datos de columnas,
        actualizar el estado interno y forzar un redibujado completo.
        """
        self.columns = columns_data
        
        # Aquí puedes añadir cualquier lógica que necesites para 
        # "re-compilar" los datos para OpenGL, si la tuvieras.
        # Por ejemplo, regenerar texturas de texto, VBOs, etc.
        
        # Finalmente, solicita la actualización del pintado.
        self.update()

class RenameDialog(QDialog):
    """Diálogo para renombrar el ID de una columna."""
    def __init__(self, old_name, main_column_table,parent=None):
        super().__init__(parent)
        self.setWindowTitle("Renombrar Columna")
        self.old_name = old_name
        self.new_name = old_name
        self.main_column_table = main_column_table # Guardamos la referencia a la tabla principal
        
        self.name_edit = QLineEdit(old_name)
        rename_button = QPushButton("Renombrar")
        cancel_button = QPushButton("Cancelar")

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Nuevo nombre:"))
        layout.addWidget(self.name_edit)
        button_layout = QHBoxLayout()
        button_layout.addWidget(rename_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        self.setLayout(layout)

        rename_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        
        # self.layout = QFormLayout(self)
        # self.new_id_input = QLineEdit(current_id)
        # self.layout.addRow(f"Nuevo ID para '{current_id}':", self.new_id_input)
        # self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        # self.button_box.accepted.connect(self.accept)
        # self.button_box.rejected.connect(self.reject)
        # self.layout.addWidget(self.button_box)
       
    def textValue(self):
         return self.new_name
 
    def accept(self):
        self.new_name = self.name_edit.text()
         
        # >>> INICIO DE LA MODIFICACIÓN <<<
        if self.old_name != self.new_name and self.main_column_table:
            table = self.main_column_table
            GRIDLINE_COL_IDX = 1
            for row in range(table.rowCount()):
                item = table.item(row, GRIDLINE_COL_IDX)
                if item and item.text() == self.old_name:
                    item.setText(self.new_name)
                     
        
        super().accept()
    
        
        
    # def get_new_id(self):
    #     return self.new_id_input.text().strip()

class GroupManagerDialog(QDialog):
    """Diálogo para crear y asignar columnas a grupos."""
    def __init__(self, columns, groups,main_column_table, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestor de Grupos")
        self.setMinimumSize(500, 400)
        self.columns = columns
        self.groups = groups
        self.main_column_table = main_column_table # Referencia de tabla en ventana principal
        
        # PASO 1: Crear toda la interfaz de usuario PRIMERO.
        # Todo este bloque de código se mueve hacia arriba.
        dialog_layout = QVBoxLayout(self)
        lists_layout = QHBoxLayout()
        
        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("Grupos Existentes"))
        self.group_list_widget = QListWidget() # << WIDGET CREADO AQUÍ
        self.group_list_widget.itemSelectionChanged.connect(self.update_column_lists)
        left_panel.addWidget(self.group_list_widget)
        new_group_button = QPushButton("Crear Nuevo Grupo")
        new_group_button.clicked.connect(self.create_new_group)
        left_panel.addWidget(new_group_button)
        lists_layout.addLayout(left_panel)
        
        mid_panel = QVBoxLayout()
        mid_panel.addStretch()
        add_button = QPushButton(">>")
        add_button.clicked.connect(self.assign_column_to_group)
        remove_button = QPushButton("<<")
        remove_button.clicked.connect(self.remove_column_from_group)
        mid_panel.addWidget(add_button)
        mid_panel.addWidget(remove_button)
        mid_panel.addStretch()
        lists_layout.addLayout(mid_panel)
        
        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("Columnas en Grupo"))
        self.in_group_list = QListWidget()
        right_panel.addWidget(self.in_group_list)
        right_panel.addWidget(QLabel("Columnas Sin Asignar"))
        self.out_group_list = QListWidget()
        right_panel.addWidget(self.out_group_list)
        lists_layout.addLayout(right_panel)
        
        dialog_layout.addLayout(lists_layout)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        dialog_layout.addWidget(self.button_box)

        # PASO 2: Ahora que los widgets existen, se pueden poblar y manipular.
        # Estas líneas ahora se ejecutan al final.
        self.refresh_groups()

        if self.group_list_widget.count() > 0:
            self.group_list_widget.setCurrentRow(0)
    def refresh_groups(self):
        self.group_list_widget.clear()
        for group_id in self.groups.keys():
            self.group_list_widget.addItem(group_id)

    def update_column_lists(self):
        self.in_group_list.clear()
        self.out_group_list.clear()
        assigned_in_any_group = set()
        for group_cols in self.groups.values():
            assigned_in_any_group.update(group_cols)
        all_col_ids = set(self.columns.keys())
        unassigned_cols = all_col_ids - assigned_in_any_group
        for col_id in sorted(list(unassigned_cols)):
            self.out_group_list.addItem(col_id)
        selected_items = self.group_list_widget.selectedItems()
        if selected_items:
            selected_group_id = selected_items[0].text()
            cols_in_selected_group = self.groups.get(selected_group_id, [])
            for col_id in sorted(cols_in_selected_group):
                self.in_group_list.addItem(col_id)
            
    def create_new_group(self):
        num = len(self.groups) + 1
        new_group_id = f"Grupo {num}"
        while new_group_id in self.groups:
            num += 1
            new_group_id = f"Grupo {num}"
        self.groups[new_group_id] = []
        self.refresh_groups()
        self.group_list_widget.setCurrentRow(self.group_list_widget.count() - 1)
        
    def assign_column_to_group(self):
        selected_group_items = self.group_list_widget.selectedItems()
        selected_col_items = self.out_group_list.selectedItems()
        if not selected_group_items or not selected_col_items: return
        group_id = selected_group_items[0].text()
        col_id = selected_col_items[0].text()
        for g_id, cols in self.groups.items():
            if col_id in cols: cols.remove(col_id)
        self.groups[group_id].append(col_id)
        
        # Lógica para actualizar la tabla principal
        self.update_main_table(col_id, group_id)
        
        self.update_column_lists()
        
        
        
    def remove_column_from_group(self):
        selected_group_items = self.group_list_widget.selectedItems()
        selected_col_items = self.in_group_list.selectedItems()
        if not selected_group_items or not selected_col_items: return
        group_id = selected_group_items[0].text()
        col_id = selected_col_items[0].text()
        if col_id in self.groups.get(group_id, []):
            self.groups[group_id].remove(col_id)
            
            # Lógica para limpiar la celda en la tabla principal
            self.update_main_table(col_id, "") # Pasa un string vacío para limpiar
            
            self.update_column_lists()
            
    def update_main_table(self, gridline_id, group_name):
        """Busca en la tabla principal las filas que coinciden con el gridline_id y actualiza su grupo."""
        if not self.main_column_table:
            return

        table = self.main_column_table
        # Basado en column_data.py, "GridLine" es la columna 1 y "Group" es la 24 (índices 1 y 24)
        GRIDLINE_COL_IDX = 1
        GROUP_COL_IDX = 26

        for row in range(table.rowCount()):
            gridline_item = table.item(row, GRIDLINE_COL_IDX)
            if gridline_item and gridline_item.text() == gridline_id:
                group_item = table.item(row, GROUP_COL_IDX)
                if not group_item:
                    # Si no existe el QTableWidgetItem en la celda "Group", lo creamos
                    group_item = QTableWidgetItem(group_name)
                    table.setItem(row, GROUP_COL_IDX, group_item)
                else:
                    # Si ya existe, solo actualizamos el texto
                    group_item.setText(group_name)

# --- Ventana Principal de la Aplicación ---

class InfoGridLinesScreen(QMainWindow):
    datos_para_renombrar = pyqtSignal(dict)
    def __init__(self, gridlines_data, groups=None):
        """
        Constructor que inicializa la ventana.
        
        Args:
            gridlines_data (list): Una lista de tuplas, donde cada tupla representa una columna
                                 con el formato (id_str, x_float, y_float).
        """
        super().__init__()
        self.setWindowTitle("Visor de Columnas 2D")
        self.setGeometry(100, 100, 1200, 800)

        self.columns = {} 
        self.gridlines_data = gridlines_data if gridlines_data is not None else []
        self.groups = groups if groups is not None else {}
        self.column_counter = 0
        self.main_column_table = None # Añadir atributo para la tabla

        self._setup_ui()
        self._populate_from_initial_data(gridlines_data)


    def _setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QHBoxLayout(self.central_widget)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Coordenada X", "Coordenada Y"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        left_layout.addWidget(self.table)
        
        table_buttons_layout = QHBoxLayout()
        add_button = QPushButton("Añadir Columna")
        remove_button = QPushButton("Eliminar Columna")
        table_buttons_layout.addWidget(add_button)
        table_buttons_layout.addWidget(remove_button)
        left_layout.addLayout(table_buttons_layout)
        
        
        extra_buttons_layout = QHBoxLayout()
        group_button = QPushButton("Gestionar Grupos")
        fit_view_button = QPushButton("Centrar Vista") # Nuevo botón
        extra_buttons_layout.addWidget(group_button)
        extra_buttons_layout.addWidget(fit_view_button)
        left_layout.addLayout(extra_buttons_layout)
       

        left_layout.addWidget(QLabel("Resumen de Grupos"))
        self.groups_table = QTableWidget()
        self.groups_table.setColumnCount(2)
        self.groups_table.setHorizontalHeaderLabels(["Nombre", "Columnas"])
        self.groups_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.groups_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.groups_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.groups_table.setSelectionMode(QAbstractItemView.NoSelection)
        left_layout.addWidget(self.groups_table)
        
        self.gl_widget = OpenGLWidget()
        
        splitter.addWidget(left_panel)
        splitter.addWidget(self.gl_widget)
        splitter.setSizes([400, 800])

        add_button.clicked.connect(self.add_column)
        remove_button.clicked.connect(self.remove_column)
        group_button.clicked.connect(self.manage_groups)
        # ### INICIO DE CAMBIOS ###
        fit_view_button.clicked.connect(self.gl_widget.fit_to_screen) # Conectar la señal del botón
        # ### FIN DE CAMBIOS ###
        self.table.itemChanged.connect(self.update_column_from_table)
        self.table.itemSelectionChanged.connect(self.update_selection_from_table)
        self.gl_widget.column_clicked_signal.connect(self.rename_column)
        self.gl_widget.selection_changed_by_click_signal.connect(self.update_selection_from_gl)

    def _populate_from_initial_data(self, gridlines_data):
        """
        Puebla las columnas iniciales y la tabla a partir de la lista de datos,
        leyendo correctamente desde una lista de diccionarios.
        """
        if not isinstance(gridlines_data, list):
            print("Warning: gridlines_data no es una lista. No se cargarán columnas.")
            return

        for item in gridlines_data:
            try:
                
                # Se verifica si el 'item' es un diccionario o una lista para manejar ambos formatos de datos.
                if isinstance(item, dict):
                    # Procesa el formato de diccionario: {'GridLine': 'A', 'pos_x': 0, 'pos_y': 0}
                    cid = str(item.get('GridLine'))
                    x = float(item.get('pos_x'))
                    y = float(item.get('pos_y'))
                elif isinstance(item, list) and len(item) >= 3:
                    # Procesa el formato de lista: ['A', 0, 0]
                    cid = str(item[0])
                    x = float(item[1])
                    y = float(item[2])
                else:
                    # Si el formato es desconocido, se salta el item.
                    print(f"Warning: Saltando item con formato desconocido: {item}")
                    continue
                

                # Llamar a la función existente que crea el objeto y lo añade a la lista self.columns
                self._create_column(cid, x, y, refresh_ui=False)

            except (ValueError, TypeError, KeyError) as e:
                # Captura errores si las claves no existen o el tipo de dato es incorrecto
                print(f"Warning: Saltando item de datos con formato incorrecto o claves faltantes: {item} ({e})")

        # Una vez que todas las columnas se han creado en la lista self.columns,
        # se refresca la UI, lo que llama a update_table() para poblar la tabla.
        self.refresh_ui()
        self.gl_widget.fit_to_screen()
    
    def refresh_table(self):
        self.table.blockSignals(True)
        self.table.setRowCount(len(self.columns))
        sorted_ids = sorted(self.columns.keys())
        for row, col_id in enumerate(sorted_ids):
            col = self.columns[col_id]
            self.table.setItem(row, 0, QTableWidgetItem(col.id))
            self.table.item(row, 0).setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(row, 1, QTableWidgetItem(str(col.x)))
            self.table.setItem(row, 2, QTableWidgetItem(str(col.y)))
        self.table.blockSignals(False)
    
    def refresh_groups_table(self):
        self.groups_table.setRowCount(0)
        self.groups_table.setRowCount(len(self.groups))
        sorted_group_ids = sorted(self.groups.keys())
        for row, group_id in enumerate(sorted_group_ids):
            col_ids = self.groups[group_id]
            columns_text = ", ".join(sorted(col_ids))
            self.groups_table.setItem(row, 0, QTableWidgetItem(group_id))
            self.groups_table.setItem(row, 1, QTableWidgetItem(columns_text))

    def refresh_gl_widget(self):
        self.gl_widget.set_data(self.columns)

    def refresh_ui(self):
        self.refresh_table()
        self.refresh_gl_widget()
        self.refresh_groups_table()
        self.update_selection_from_table()
        
    def _get_selected_row_id(self):
        selected_items = self.table.selectedItems()
        if not selected_items: return None
        return self.table.item(selected_items[0].row(), 0).text()

    def _create_column(self, col_id, x, y, refresh_ui=True):
        if col_id in self.columns:
            QMessageBox.warning(self, "Error", f"El ID de columna '{col_id}' ya existe.")
            return None
        
        new_col = Column(col_id, x, y)
        self.columns[col_id] = new_col
        id_num_str = ''.join(filter(str.isdigit, col_id))
        if id_num_str:
            try:
                self.column_counter = max(self.column_counter, int(id_num_str))
            except ValueError:
                pass # Ignorar si la parte numérica no es un entero válido

        if refresh_ui:
            self.refresh_ui()
        
        return new_col

    def add_column(self):
        self.column_counter += 1
        new_id = f"COL-{self.column_counter}"
        while new_id in self.columns:
            self.column_counter += 1
            new_id = f"COL-{self.column_counter}"
        self._create_column(new_id, 0, 0)

    def remove_column(self):
        col_id = self._get_selected_row_id()
        if not col_id:
            QMessageBox.information(self, "Información", "Por favor, seleccione una columna para eliminar.")
            return

        reply = QMessageBox.question(self, "Confirmar", f"¿Seguro que desea eliminar la columna '{col_id}'?", 
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes and col_id in self.columns:
            del self.columns[col_id]
            for group_id in list(self.groups.keys()):
                if col_id in self.groups[group_id]: self.groups[group_id].remove(col_id)
                if not self.groups[group_id]: del self.groups[group_id]
            self.refresh_ui()
            # ### INICIO DE CAMBIOS ###
            self.gl_widget.fit_to_screen() # Re-centrar la vista después de eliminar un punto
            # ### FIN DE CAMBIOS ###
    
    def update_column_from_table(self, item):
        row, col_index = item.row(), item.column()
        id_item = self.table.item(row, 0)
        if not id_item: return
        col_id = id_item.text()
        column_obj = self.columns.get(col_id)
        if not column_obj: return
        try:
            if col_index == 1: column_obj.x = float(item.text())
            elif col_index == 2: column_obj.y = float(item.text())
        except (ValueError, TypeError):
            QMessageBox.warning(self, "Error de formato", "Por favor, introduzca un valor numérico.")
            self.refresh_table()
            return
        self.refresh_gl_widget()

    def update_selection_from_table(self):
        selected_col_id = self._get_selected_row_id()
        
        # Incializa una lista vacía para los IDs a resaltar.
        group_ids_to_highlight = []
        
        if selected_col_id:
            # Busca a qué grupo pertenece la columna seleccionada.
            # Esto es más robusto que depender del atributo 'group_id' del objeto de la columna.
            found_group = None
            for group_id, member_ids in self.groups.items():
                if selected_col_id in member_ids:
                    found_group = group_id
                    break
            
            # Si la columna está en un grupo, obtén todos los miembros de ese grupo para resaltarlos.
            if found_group:
                group_ids_to_highlight = self.groups.get(found_group, [])
                # Para depuración: imprime el grupo que se está resaltando.
                print(f"Resaltando el grupo '{found_group}': {group_ids_to_highlight}")
                
        # Pasa la selección y la lista de miembros del grupo al widget de OpenGL.
        self.gl_widget.set_selection(selected_col_id, group_ids_to_highlight)
        
    def update_selection_from_gl(self, col_id):
        if self._get_selected_row_id() == col_id:
             self.update_selection_from_table()
             return
        self.table.blockSignals(True)
        self.table.clearSelection()
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).text() == col_id:
                self.table.selectRow(row)
                break
        self.table.blockSignals(False)
        self.update_selection_from_table()

    def rename_column(self, old_name):
        """
        Renombra una columna. Es invocado por una señal desde el visor OpenGL 
        cuando se hace doble clic en una columna.
        """
        if not isinstance(old_name, str):
            return

        dialog = RenameDialog(old_name, self.main_column_table, self)
        
        if dialog.exec_():
            new_name = dialog.textValue()
            if not new_name or new_name == old_name:
                return # Salir si el nombre está vacío o no ha cambiado
            
            if new_name in self.columns:
                QMessageBox.warning(self, "Error", f"El ID '{new_name}' ya existe.")
                return

            # --- INICIO DE LA LÓGICA CORREGIDA ---

            # 1. Actualizar la tabla de esta pantalla (self.table)
            ID_COLUMN_INDEX = 0
            for row in range(self.table.rowCount()):
                item = self.table.item(row, ID_COLUMN_INDEX)
                if item and item.text() == old_name:
                    self.table.blockSignals(True)
                    item.setText(new_name)
                    self.table.blockSignals(False)
                    break

            # 2. Actualizar la estructura de datos interna 'self.columns'
            # Sacamos el objeto del diccionario usando el nombre antiguo
            col_obj = self.columns.pop(old_name) 
            # ¡Aquí está la magia! Actualizamos el atributo del objeto
            col_obj.id = new_name 
            # Lo volvemos a insertar en el diccionario con la nueva llave
            self.columns[new_name] = col_obj 

            # 3. Actualizar la estructura de datos interna 'self.groups'
            for group_id, cols in self.groups.items():
                if old_name in cols:
                    cols.remove(old_name)
                    cols.append(new_name)
            
            # 4. Refrescar el visor 2D y la tabla de resumen de grupos
            self.gl_widget.set_columns_data(self.columns)
            self.refresh_groups_table()

            # 5. (Opcional pero recomendado) Actualizar la selección si la columna renombrada estaba seleccionada
            if self.gl_widget.selected_column_id == old_name:
                self.update_selection_from_gl(new_name)
        
            
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
        
    def set_main_column_table(self, table: QTableWidget):
        """Recibe y almacena la referencia a la QTableWidget de la pantalla de datos de columnas."""
        self.main_column_table = table
    
    def manage_groups(self):
        if len(self.columns) < 2:
            QMessageBox.information(self, "Información", "Necesita al menos dos columnas para crear grupos.")
            return
        
        # dialog = GroupManagerDialog(self.columns, copy.deepcopy(self.groups),self.main_column_table, self)
        dialog = GroupManagerDialog(self.columns, copy.deepcopy(self.groups), self.main_column_table, self)
        if dialog.exec_():
            self.groups = dialog.groups
            for col in self.columns.values(): col.group_id = None 
            for group_id, col_ids in self.groups.items():
                for col_id in col_ids:
                    if col_id in self.columns:
                        self.columns[col_id].group_id = group_id
            self.refresh_ui()
            
    

    def closeEvent(self, event):
        """Se llama cuando la ventana está a punto de cerrarse."""
        # Se eliminó la llamada a _save_data_to_file()
        super().closeEvent(event)