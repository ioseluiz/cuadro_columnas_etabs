from PyQt5.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QSplitter, QWidget, QLabel,
    QComboBox, QPushButton, QGraphicsView, QGraphicsScene, QTableWidget
)
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainter, QPen, QBrush, QFont, QColor

class IdentificarColumnasScreen(QDialog):
    def __init__(self, parent=None, stories=None):
        super().__init__(parent)
        self.setWindowTitle("Ventana para Identificar Columnas")
        self.setGeometry(150, 150, 1200, 700) # Initial Size bigger
        
        # Main Layout
        main_layout = QHBoxLayout(self)
        
        # Divider para panel izquierdo y derecho
        splitter = QSplitter(Qt.Horizontal)
        
        # -- Left Panel
        left_pane_widget = QWidget()
        left_pane_layout = QVBoxLayout(left_pane_widget)
        left_pane_layout.setSpacing(15) # Space between groupboxes
        
        # Placeholder para Rectangular
        group_rectangular_layout = QVBoxLayout()
        lbl_rectangular_armado = QLabel("Datos de Detalles")
        self.table_detalles = QTableWidget(5, 5) # Filas, Columnas de ejemplo
        self.table_detalles.setHorizontalHeaderLabels(["col 1", "col 2", "col 3","col 4", "col 5"])
        
        group_rectangular_layout.addWidget(lbl_rectangular_armado)
        group_rectangular_layout.addWidget(self.table_detalles)
        
        left_pane_layout.addLayout(group_rectangular_layout)
        
        ########################
        
        # -- Right Panel
        right_pane_widget = QWidget()
        right_pane_layout = QVBoxLayout(right_pane_widget)
        
        # Controles superiores panel derecho
        layout_controles_superiores_derecha = QHBoxLayout()
        label_escoger_piso = QLabel("Escoger Piso")
        self.combo_piso = QComboBox()
        self.combo_piso.addItems(stories)
        self.btn_zoom = QPushButton("Zoom x1.0")
        
        layout_controles_superiores_derecha.addWidget(label_escoger_piso)
        layout_controles_superiores_derecha.addWidget(self.combo_piso)
        layout_controles_superiores_derecha.addStretch() # Empuja el zoom a la derecha
        layout_controles_superiores_derecha.addWidget(self.btn_zoom)
        right_pane_layout.addLayout(layout_controles_superiores_derecha)
        
        # Area Grafica (placeholder)
        self.graphics_view = QGraphicsView()
        self.scene = QGraphicsScene()
        self.graphics_view.setScene(self.scene)
        self.graphics_view.setRenderHint(QPainter.Antialiasing)
        # Dibujar algunos elementos de ejemplo en la escena
        self.dibujar_elementos_ejemplo_escena()
        
        right_pane_layout.addWidget(self.graphics_view)
        
        # Add paneles al splitter
        splitter.addWidget(left_pane_widget)
        splitter.addWidget(right_pane_widget)
        
        # Configurar tamano relativo inicial del splitter
        splitter.setSizes([400, 400]) # Dar mas espacio al panel derecho
        
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
        
    def dibujar_elementos_ejemplo_escena(self):
        # Limpiar escena por si se llama múltiples veces
        self.scene.clear()
        
        # Estilos comunes
        pen = QPen(Qt.black)
        brush_rect = QBrush(QColor(220, 220, 220)) # Gris claro para rectángulos
        brush_circle = QBrush(QColor(180, 180, 180)) # Gris más oscuro para círculos
        font_label = QFont("Arial", 8)
        font_val = QFont("Arial", 7, QFont.Bold)

        # Elemento C73 (rectángulo con texto y círculo)
        rect_c73 = self.scene.addRect(50, 50, 60, 30, pen, brush_rect)
        text_c73_label = self.scene.addText("C73", font_label)
        text_c73_label.setPos(rect_c73.rect().topLeft() + QPointF(5, 2))
        circle_c73 = self.scene.addEllipse(50 + 60/2 - 5, 50 + 30 + 2, 10, 10, pen, brush_circle) # Debajo

        # Elemento C8 (rectángulo con texto arriba y valor abajo)
        rect_c8 = self.scene.addRect(120, 50, 40, 40, pen, brush_rect)
        text_c8_c = self.scene.addText("C", font_label)
        text_c8_c.setPos(rect_c8.rect().center().x() - text_c8_c.boundingRect().width()/2,
                         rect_c8.rect().top() + 3)
        text_c8_8 = self.scene.addText("8", font_val)
        text_c8_8.setPos(rect_c8.rect().center().x() - text_c8_8.boundingRect().width()/2,
                         rect_c8.rect().top() + 15)
        circle_c8 = self.scene.addEllipse(120 + 40/2 - 5, 50 + 40 + 2, 10, 10, pen, brush_circle)

        # Elemento C195 (similar a C73)
        rect_c195 = self.scene.addRect(30, 120, 60, 30, pen, brush_rect)
        text_c195_label = self.scene.addText("C195", font_label)
        text_c195_label.setPos(rect_c195.rect().topLeft() + QPointF(5, 2))
        circle_c195 = self.scene.addEllipse(30 + 60/2 - 5, 120 + 30 + 2, 10, 10, pen, brush_circle)

        # Elemento C33
        rect_c33 = self.scene.addRect(150, 120, 60, 30, pen, brush_rect)
        text_c33_label = self.scene.addText("C33", font_label)
        text_c33_label.setPos(rect_c33.rect().topLeft() + QPointF(5, 2))
        circle_c33 = self.scene.addEllipse(150 + 60/2 - 5, 120 + 30 + 2, 10, 10, pen, brush_circle)

        # Círculos sueltos de ejemplo
        self.scene.addEllipse(100, 100, 20, 20, pen, brush_circle) # Círculo grande
        self.scene.addEllipse(200, 180, 15, 15, pen, brush_circle)
        self.scene.addEllipse(210, 220, 25, 25, pen, brush_circle)
        dot_inside = self.scene.addEllipse(210 + 25/2 - 3, 220 + 25/2 - 3, 6, 6, QPen(Qt.black), QBrush(Qt.black))

        # Línea de ejemplo (entre C195 y un punto)
        # Para conectar centros de círculos o bordes de rectángulos, necesitarías sus coordenadas
        # P1 = circle_c195.rect().center()
        # P2 = QPointF(80, 180) # Un punto arbitrario
        # self.scene.addLine(P1.x(), P1.y(), P2.x(), P2.y(), pen)
        
        # Establecer un fondo para la escena si se desea
        self.scene.setBackgroundBrush(QColor(245, 245, 255)) # Un blanco ligeramente azulado
        
        