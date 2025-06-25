from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSpacerItem, QSizePolicy, QFileDialog,
    QTableWidget, QTableWidgetItem, QScrollArea, QFrame, QComboBox
    
)
from PyQt5.QtGui import QFont, QPixmap 
from PyQt5.QtCore import Qt, QSize, QT_VERSION_STR, PYQT_VERSION_STR

class ColumnModifyScreen(QWidget):
    def __init__(self, column_data_screen_ref,table_data, parent=None):
        super().__init__(parent)
        self.column_data_screen_ref = column_data_screen_ref
        self.table_data = table_data
        
        
        self.setWindowTitle("Modificar Secciones de Columnas")
        self.setGeometry(50, 50, 800, 400)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10,10,10,10)
        self.main_layout.setSpacing(10)
        
        # -- Seccion de Botones Superiores
        top_button_layout = QHBoxLayout()
        top_button_layout.setSpacing(5) # Menor espaciado para botones de accion
        
        self.btn_modificar_datos = QPushButton("Modificar Datos")
        self.btn_regresar = QPushButton("Regresar")
        
        top_button_layout.addWidget(self.btn_modificar_datos)
        top_button_layout.addWidget( self.btn_regresar)
        
        self.main_layout.addLayout(top_button_layout)
        
        # -- Area de Tabs para Datos de Columnas
        self.tabs_layout = QHBoxLayout()
        
         # Placeholder para Rectangular
        group_rectangular_layout = QVBoxLayout()
        lbl_rectangular_armado = QLabel("[Rectangular] Armado transversal")
        lbl_rectangular_resultados = QLabel("[Rectangular] Resultados")
        self.table_rectangular_armado = QTableWidget(5, 3) # Filas, Columnas de ejemplo
        self.table_rectangular_armado.setHorizontalHeaderLabels(["col 1", "col 2", "col 3"])
        
        group_rectangular_layout.addWidget(lbl_rectangular_armado)
        group_rectangular_layout.addWidget(self.table_rectangular_armado)
        group_rectangular_layout.addWidget(lbl_rectangular_resultados)
        
        self.tabs_layout.addLayout(group_rectangular_layout)
        # self.tabs_layout.addLayout(group_circular_layout)

        # Para hacer scrollable el contenido principal si excede el tamaño
        scroll_content_widget = QWidget()
        scroll_content_widget.setLayout(self.tabs_layout)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_content_widget)
        scroll_area.setFrameShape(QFrame.NoFrame) # Sin borde para el área de scroll

        self.main_layout.addWidget(scroll_area) # Añadir el área de scroll al layout principal
        
        self.apply_styles() # Aplicar algunos estilos básicos
        
    def apply_styles(self):
        # Estilo básico para los botones de acción
        action_button_style = """
            QPushButton {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11px;
                color: #FFFFFF;
                background-color: #0078D7; /* Azul similar al de Office/Windows */
                border: 1px solid #005A9E;
                padding: 6px 10px;
                border-radius: 3px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #005A9E;
            }
            QPushButton:pressed {
                background-color: #003C6A;
            }
        """
        
        
        self.btn_modificar_datos.setStyleSheet(action_button_style)
       

        # Estilo para el botón de volver (más grande y centrado)
        self.btn_regresar.setStyleSheet("""
            QPushButton {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                color: #2c3e50;
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #d5d9db; }
            QPushButton:pressed { background-color: #bdc3c7; }
        """)
        self.setStyleSheet("QWidget { background-color: #E1E1E1; } QLabel { font-size: 12px; font-weight: bold; }")
        
    def go_back_to_main_menu(self):
        """Oculta esta pantalla y muestra el menú principal."""
        self.hide()
        if self.column_data_screen_ref:
            self.column_data_screen_ref.show()
            # self.main_menu_ref.sap_model_connected = None # Limpiar referencia en el menú principal
        
    def closeEvent(self, event):
        """Maneja el cierre de la ventana."""
        self.go_back_to_main_menu() # Asegura que el menú principal se muestre
        super().closeEvent(event)
        
       
        
        