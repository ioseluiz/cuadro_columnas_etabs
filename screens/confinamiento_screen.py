from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel
)
from PyQt5.QtGui import QFont

class ConfinamientoScreen(QWidget):
    """
    Pantalla para mostrar y calcular el confinamiento de columnas.
    """
    def __init__(self, data_sections):
        super(ConfinamientoScreen, self).__init__()
        self.setWindowTitle("Calculo de Confinamiento de Columnas")
        self.setGeometry(200,200,1400,800)
        
        # Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Titulo
        title_label = QLabel("Tabla de Resultados de Confinamiento")
        title_label.setFont(QFont('Segoe UI', 14, QFont.bold))
        self.main_layout.addWidget(title_label)
        
        # Tabla de Resultados
        self.tabla_confinamiento = QTableWidget()
        self.setup_table()
        self.main_layout.addWidget(self.tabla_confinamiento)
        
    def setup_table(self):
        """
        Configura las columnas de la tabla de confinamiento.
        """
        headers = [
            "Pu (kgf)", "b (cm)", "num_r2","h (cm)","num_r3","rec", "f'c (kg/cm²)",
            "rebar_size", "est_size", "fy", "X1", "X2"
        ]
        self.table_confinamiento.setColumnCount(len(headers))
        self.tabla_confinamiento.setHorizontalHeaderLabels(headers)
        self.tabla_confinamiento.horizontalHeader().setFont(QFont('Segoe UI'), 9, QFont.bold)
        self.tabla_confinamiento.resizeColumnsToContents()
        
    def populate_table(self, confinamiento_data: list[dict]):
        """
        Puebla la tabla con los datos de confinamiento extraídos.

        Args:
            confinement_data (list[dict]): Lista de diccionarios con los datos.
        """
        self.tabla_confinamiento.setRowCount(0) # Clean table before populating
        
        for row_idx, data_row in enumerate(confinamiento_data):
            self.tabla_confinamiento.insertRow(row_idx)
            
            # Extract values, applying default if neccesary
            pu = data_row.get('Pu', 3000)
            b = data_row.get('b', 0.0)
            h = data_row.get('h', 0.0)
            fc = data_row.get("fc", 0.0)
            fy = data_row.get('fy', 0.0)
            r3_bars = data_row.get('num_r3', 0)
            r2_bars = data_row.get('num_r2', 0)
            
            # Populate cells
            self.tabla_confinamiento.setItem(row_idx, 0, QTableWidgetItem(str(pu)))
            self.tabla_confinamiento.setItem(row_idx, 1, QTableWidgetItem(str(b)))
            self.tabla_confinamiento.setItem(row_idx, 2, QTableWidgetItem(str(h)))
            self.tabla_confinamiento.setItem(row_idx, 3, QTableWidgetItem(str(fc)))
            self.tabla_confinamiento.setItem(row_idx, 4, QTableWidgetItem(str(fy)))
            self.tabla_confinamiento.setItem(row_idx, 5, QTableWidgetItem(str(r3_bars)))
            self.tabla_confinamiento.setItem(row_idx, 6, QTableWidgetItem(str(r2_bars)))
            
            
            # Placeholder for future calculated columns
            self.tabla_confinamiento.setItem(row_idx, 7, QTableWidgetItem("X1"))
            self.tabla_confinamiento.setItem(row_idx, 8, QTableWidgetItem("X2"))
            
            
        self.tabla_confinamiento.resizeColumnsToContents()