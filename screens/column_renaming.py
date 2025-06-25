from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSpacerItem, QSizePolicy, QFileDialog,
    QTableWidget, QTableWidgetItem, QScrollArea, QFrame, QComboBox
    
)
from PyQt5.QtGui import QFont, QPixmap 
from PyQt5.QtCore import Qt, QSize, QT_VERSION_STR, PYQT_VERSION_STR


class ColumnRenamingScreen(QWidget):
    def __init__(self, main_menu_ref,sap_model_object=None, parent=None, column_data=None):
        self.main_menu_ref = main_menu_ref
        
        self.setWindowTitle("Renombrar Columnas - ETABS")
        self.setGeometry(50, 50, 1200, 700) # Size based on complexity
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10,10,10,10)
        self.main_layout.setSpacing(10)
        
        # -- Seccion de Botones Superiores
        top_button_layout = QHBoxLayout()
        top_button_layout.setSpacing(5) # Menor espaciado para botones de accion
        
        self.btn_read_data = QPushButton("1. Leer Label, Name and Story")
        self.btn_renombrar_cols = QPushButton("2. Renombrar Columnaa en Modelo")
        # self.btn_exportar_planos = QPushButton("3. Exportar Planos")
        
        top_button_layout.addWidget(self.btn_read_data)
        top_button_layout.addWidget( self.btn_renombrar_cols)
        
        self.main_layout.addLayout(top_button_layout)
        
        # -- Area de Tabs para Datos de Columnas
        self.tabs_layout = QHBoxLayout()
        
        # Placeholder para Rectangular
        group_rectangular_layout = QVBoxLayout()
        lbl_rectangular_armado = QLabel("[Rectangular] Armado transversal")
        lbl_rectangular_resultados = QLabel("[Rectangular] Resultados")
        self.table_rectangular_armado = QTableWidget(len(column_data), 14) # Filas, Columnas de ejemplo
        self.table_rectangular_armado.setHorizontalHeaderLabels(["Piso","GridLine","Frame_id", "Label","Sección", "depth","width", "Material", "Long. R2 Bars", "Long. R3 Bars","Rebar", "Rebar Est.","Cover","Detalle No."])
        
        print(column_data[0].keys())
        print(column_data[0])
        