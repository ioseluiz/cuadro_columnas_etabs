
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
        
        view_height = h / self.zoom_factor
        view_width = w / self.zoom_factor
        
        glOrtho(-view_width / 2, view_width / 2, -view_height / 2, view_height / 2, -1, 1)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
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
            if group_col_id in self.columns and group_col_id != self.selected_column_id:
                col = self.columns[group_col_id]
                self._draw_circle(col.x, col.y, self.selection_radius, (1.0, 0.6, 0.0))

        if self.selected_column_id and self.selected_column_id in self.columns:
            col = self.columns[self.selected_column_id]
            self._draw_circle(col.x, col.y, self.selection_radius, (1.0, 1.0, 0.0))


    def _draw_circle(self, cx, cy, r, color):
        """Función auxiliar para dibujar un círculo."""
        num_segments = 30
        glLineWidth(2.0)
        glColor3f(*color)
        glBegin(GL_LINE_LOOP)
        for i in range(num_segments):
            theta = 2.0 * math.pi * i / num_segments
            x = r * math.cos(theta)
            y = r * math.sin(theta)
            glVertex2f(x + cx, y + cy)
        glEnd()

    def _draw_column_ids(self):
        """Dibuja los IDs de las columnas usando QPainter."""
        painter = QPainter(self)
        painter.beginNativePainting()
        painter.endNativePainting()

        painter.setPen(QColor(255, 255, 255))
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)

        for col in self.columns.values():
            window_pos = self.world_to_screen(col.x, col.y)
            if window_pos:
                painter.drawText(window_pos.x() + 10, window_pos.y() + 5, col.id)
        
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
        self.zoom_factor = max(0.1, min(self.zoom_factor, 10.0))
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

class RenameDialog(QDialog):
    """Diálogo para renombrar el ID de una columna."""
    def __init__(self, current_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Renombrar Columna")
        self.layout = QFormLayout(self)
        self.new_id_input = QLineEdit(current_id)
        self.layout.addRow(f"Nuevo ID para '{current_id}':", self.new_id_input)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)
    def get_new_id(self):
        return self.new_id_input.text().strip()

class GroupManagerDialog(QDialog):
    """Diálogo para crear y asignar columnas a grupos."""
    def __init__(self, columns, groups, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestor de Grupos")
        self.setMinimumSize(500, 400)
        self.columns = columns
        self.groups = groups 
        
        # Layout principal vertical para todo el diálogo
        dialog_layout = QVBoxLayout(self)

        # Layout horizontal para las listas y botones de acción
        lists_layout = QHBoxLayout()
        
        # Panel izquierdo: Lista de grupos
        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("Grupos Existentes"))
        self.group_list_widget = QListWidget()
        self.group_list_widget.itemSelectionChanged.connect(self.update_column_lists)
        left_panel.addWidget(self.group_list_widget)
        new_group_button = QPushButton("Crear Nuevo Grupo")
        new_group_button.clicked.connect(self.create_new_group)
        left_panel.addWidget(new_group_button)
        lists_layout.addLayout(left_panel)
        
        # Panel central: Botones para mover columnas
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
        
        # Panel derecho: Listas de columnas
        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("Columnas en Grupo"))
        self.in_group_list = QListWidget()
        right_panel.addWidget(self.in_group_list)
        right_panel.addWidget(QLabel("Columnas Sin Asignar"))
        self.out_group_list = QListWidget()
        right_panel.addWidget(self.out_group_list)
        lists_layout.addLayout(right_panel)
        
        # Se añade el layout de las listas al layout principal
        dialog_layout.addLayout(lists_layout)
        
        # Botones de Aceptar/Cancelar
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        # Se añaden los botones al layout principal
        dialog_layout.addWidget(self.button_box)
        
        self.refresh_groups()

        # Seleccionar el primer grupo por defecto para mejorar la UX
        if self.group_list_widget.count() > 0:
            self.group_list_widget.setCurrentRow(0)

    def refresh_groups(self):
        self.group_list_widget.clear()
        for group_id in self.groups.keys():
            self.group_list_widget.addItem(group_id)

    def update_column_lists(self):
        self.in_group_list.clear()
        self.out_group_list.clear()

        # 1. Determinar qué columnas están asignadas a cualquier grupo.
        assigned_in_any_group = set()
        for group_cols in self.groups.values():
            assigned_in_any_group.update(group_cols)
            
        # 2. Rellenar la lista de "sin asignar".
        all_col_ids = set(self.columns.keys())
        unassigned_cols = all_col_ids - assigned_in_any_group
        for col_id in sorted(list(unassigned_cols)):
            self.out_group_list.addItem(col_id)
            
        # 3. Si hay un grupo seleccionado, rellenar la lista de "en grupo".
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
        self.update_column_lists()
        
    def remove_column_from_group(self):
        selected_group_items = self.group_list_widget.selectedItems()
        selected_col_items = self.in_group_list.selectedItems()
        if not selected_group_items or not selected_col_items: return
        group_id = selected_group_items[0].text()
        col_id = selected_col_items[0].text()
        if col_id in self.groups.get(group_id, []):
            self.groups[group_id].remove(col_id)
            self.update_column_lists()

# --- Ventana Principal de la Aplicación ---

class SectionDesignerScreen(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visor de Columnas 2D")
        self.setGeometry(100, 100, 1200, 800)

        # Nombre del archivo para guardar y cargar datos
        self.save_file = "layout_data.json"

        self.columns = {} 
        self.groups = {} 
        self.column_counter = 0

        self._setup_ui()
        self._load_data_from_file()

    def _setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QHBoxLayout(self.central_widget)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Tabla de columnas
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Coordenada X", "Coordenada Y"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        left_layout.addWidget(self.table)
        
        # Botones de control
        table_buttons_layout = QHBoxLayout()
        add_button = QPushButton("Añadir Columna")
        remove_button = QPushButton("Eliminar Columna")
        table_buttons_layout.addWidget(add_button)
        table_buttons_layout.addWidget(remove_button)
        left_layout.addLayout(table_buttons_layout)
        group_button = QPushButton("Gestionar Grupos")
        left_layout.addWidget(group_button)

        # NUEVO: Tabla resumen de grupos
        left_layout.addWidget(QLabel("Resumen de Grupos"))
        self.groups_table = QTableWidget()
        self.groups_table.setColumnCount(2)
        self.groups_table.setHorizontalHeaderLabels(["Nombre", "Columnas"])
        self.groups_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.groups_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.groups_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.groups_table.setSelectionMode(QAbstractItemView.NoSelection)
        left_layout.addWidget(self.groups_table)
        
        # Panel Derecho con OpenGL
        self.gl_widget = OpenGLWidget()
        
        splitter.addWidget(left_panel)
        splitter.addWidget(self.gl_widget)
        splitter.setSizes([400, 800]) # Ajustar tamaño inicial

        # Conexiones
        add_button.clicked.connect(self.add_column)
        remove_button.clicked.connect(self.remove_column)
        group_button.clicked.connect(self.manage_groups)
        self.table.itemChanged.connect(self.update_column_from_table)
        self.table.itemSelectionChanged.connect(self.update_selection_from_table)
        self.gl_widget.column_clicked_signal.connect(self.rename_column)
        self.gl_widget.selection_changed_by_click_signal.connect(self.update_selection_from_gl)

    def _load_sample_data(self):
        """Carga datos de ejemplo si no hay archivo de guardado."""
        sample_cols = [
            ("C-1", 100, 50), ("C-2", 250, 150), ("C-3", 100, 250),
            ("C-4", -50, -80), ("C-5", -150, 100),
        ]
        for cid, x, y in sample_cols:
            self._create_column(cid, x, y, refresh_ui=False)
        self.refresh_ui()

    def _load_data_from_file(self):
        """Carga el estado de las columnas y grupos desde un archivo JSON."""
        if not os.path.exists(self.save_file):
            self._load_sample_data()
            return
        
        try:
            with open(self.save_file, 'r') as f:
                data = json.load(f)
            
            self.columns.clear()
            for col_data in data.get("columns", []):
                col = Column(col_data['id'], col_data['x'], col_data['y'], col_data.get('group_id'))
                self.columns[col.id] = col
                
            self.groups = data.get("groups", {})
            self.column_counter = data.get("column_counter", 0)

            self.refresh_ui()
            print(f"Datos cargados desde {self.save_file}")

        except (json.JSONDecodeError, KeyError) as e:
            QMessageBox.warning(self, "Error al cargar", f"No se pudo cargar el archivo de datos: {e}\nSe usarán datos de ejemplo.")
            self._load_sample_data()

    def _save_data_to_file(self):
        """Guarda el estado actual de columnas y grupos en un archivo JSON."""
        data_to_save = {
            "column_counter": self.column_counter,
            "groups": self.groups,
            "columns": [
                {"id": col.id, "x": col.x, "y": col.y, "group_id": col.group_id}
                for col in self.columns.values()
            ]
        }
        
        try:
            with open(self.save_file, 'w') as f:
                json.dump(data_to_save, f, indent=4)
            print(f"Datos guardados en {self.save_file}")
        except Exception as e:
            QMessageBox.critical(self, "Error al guardar", f"No se pudieron guardar los datos: {e}")

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
        """Sincroniza la tabla de resumen de grupos con el diccionario de grupos."""
        self.groups_table.setRowCount(0) # Limpiar tabla
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
        """Actualiza todos los componentes de la UI que dependen de los datos."""
        self.refresh_table()
        self.refresh_gl_widget()
        self.refresh_groups_table() # Actualizar tabla de grupos
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
            self.column_counter = max(self.column_counter, int(id_num_str))

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
        col_id = self._get_selected_row_id()
        group_ids_to_highlight = []
        if col_id:
            col_obj = self.columns.get(col_id)
            if col_obj and col_obj.group_id:
                group_ids_to_highlight = self.groups.get(col_obj.group_id, [])
        self.gl_widget.set_selection(col_id, group_ids_to_highlight)
        
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

    def rename_column(self, old_id):
        dialog = RenameDialog(old_id, self)
        if dialog.exec_():
            new_id = dialog.get_new_id()
            if not new_id or new_id == old_id: return
            if new_id in self.columns:
                QMessageBox.warning(self, "Error", f"El ID '{new_id}' ya existe.")
                return
            col_obj = self.columns.pop(old_id)
            col_obj.id = new_id
            self.columns[new_id] = col_obj
            for group_id, cols in self.groups.items():
                if old_id in cols:
                    cols.remove(old_id)
                    cols.append(new_id)
            if self.gl_widget.selected_column_id == old_id:
                 self.gl_widget.selected_column_id = new_id
            self.refresh_ui()
            self.update_selection_from_gl(new_id)

    def manage_groups(self):
        if len(self.columns) < 2:
            QMessageBox.information(self, "Información", "Necesita al menos dos columnas para crear grupos.")
            return

        dialog = GroupManagerDialog(self.columns, copy.deepcopy(self.groups), self)
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
        self._save_data_to_file()
        super().closeEvent(event)