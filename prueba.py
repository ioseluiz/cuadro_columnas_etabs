import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel
)
from PyQt5.QtGui import QFont

# Un diccionario para mapear el nombre de la barra a su diámetro en cm.
# Puedes expandir esto según las barras que utilices.
BAR_DIAMETERS = {
    '#2': 0.64,
    '#3': 0.95,  # 3/8"
    '#4': 1.27,  # 4/8"
    '#5': 1.59,  # 5/8"
    '#6': 1.91,  # 6/8"
    '#7': 2.22,  # 7/8"
    '#8': 2.54,  # 8/8"
}

class ConfinamientoScreen(QWidget):
    """
    Pantalla para mostrar y calcular el confinamiento de columnas.
    """
    def __init__(self, data_sections: list[dict]):
        """
        Constructor de la ventana.

        Args:
            data_sections (list[dict]): Lista de diccionarios, cada uno 
                                         representando una sección de columna.
        """
        super().__init__()
        
        self.data_sections = data_sections
        
        self.setWindowTitle("Cálculo de Confinamiento de Columnas")
        self.setGeometry(200, 200, 1400, 600)
        
        # Layout principal
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Título
        title_label = QLabel("Tabla de Propiedades de Secciones")
        title_label.setFont(QFont('Segoe UI', 14, QFont.Bold))
        self.main_layout.addWidget(title_label)
        
        # Tabla de Resultados
        self.tabla_confinamiento = QTableWidget()
        self.main_layout.addWidget(self.tabla_confinamiento)
        
        # Configurar y poblar la tabla
        self.setup_table()
        self.populate_table()
        
    def setup_table(self):
        """
        Configura las columnas y cabeceras de la tabla de confinamiento.
        """
        headers = [
            "Sección", "b (cm)", "h (cm)", "rec (cm)",
            "Acero Long.", "Ø Long. (cm)", "# Barras Eje 2", "# Barras Eje 3",
            "Estribo", "Ø Estribo (cm)", "f'c (kg/cm²)", "fy (kg/cm²)", "bc1","bc2",
            "X1","X2","hx", "a(cm)","b(cm)","c(cm)", "d(cm)", "Smax,", "Cuantia REQ", "Cuantia", "DCR"
        ]
        self.tabla_confinamiento.setColumnCount(len(headers))
        self.tabla_confinamiento.setHorizontalHeaderLabels(headers)
        self.tabla_confinamiento.horizontalHeader().setFont(QFont('Segoe UI', 10, QFont.Bold))
        self.tabla_confinamiento.resizeColumnsToContents()
        
    def populate_table(self):
        """
        Puebla la tabla con los datos de las secciones de columnas.
        """
        self.tabla_confinamiento.setRowCount(len(self.data_sections))
        
        for row_idx, section_data in enumerate(self.data_sections):
            
            # --- Extracción de datos del diccionario con valores por defecto ---
            b = section_data.get('b', 0.0)
            h = section_data.get('h', 0.0)
            rec = section_data.get('cover', 0.0)
            rebar_long_size = section_data.get('rebar_long_size', '#5')
            estribo_size = section_data.get('estribo_size', '#3')
            num_bars_2 = section_data.get('num_bars_2', 0)
            num_bars_3 = section_data.get('num_bars_3', 0)
            fc = section_data.get("fc", 0.0)
            fy = section_data.get('fy', 0.0)

            # --- Cálculos adicionales (diámetros) ---
            long_diam_cm = BAR_DIAMETERS.get(rebar_long_size, 0.0)
            estribo_diam_cm = BAR_DIAMETERS.get(estribo_size, 0.0)

            # --- Creación y asignación de celdas en el orden correcto ---
            self.tabla_confinamiento.setItem(row_idx, 0, QTableWidgetItem(f"Columna {row_idx + 1}"))
            self.tabla_confinamiento.setItem(row_idx, 1, QTableWidgetItem(str(b)))
            self.tabla_confinamiento.setItem(row_idx, 2, QTableWidgetItem(str(h)))
            self.tabla_confinamiento.setItem(row_idx, 3, QTableWidgetItem(str(rec)))
            self.tabla_confinamiento.setItem(row_idx, 4, QTableWidgetItem(rebar_long_size))
            self.tabla_confinamiento.setItem(row_idx, 5, QTableWidgetItem(f"{long_diam_cm:.2f}"))
            self.tabla_confinamiento.setItem(row_idx, 6, QTableWidgetItem(str(num_bars_2)))
            self.tabla_confinamiento.setItem(row_idx, 7, QTableWidgetItem(str(num_bars_3)))
            self.tabla_confinamiento.setItem(row_idx, 8, QTableWidgetItem(estribo_size))
            self.tabla_confinamiento.setItem(row_idx, 9, QTableWidgetItem(f"{estribo_diam_cm:.2f}"))
            self.tabla_confinamiento.setItem(row_idx, 10, QTableWidgetItem(str(fc)))
            self.tabla_confinamiento.setItem(row_idx, 11, QTableWidgetItem(str(fy)))
            # bc1
            bc1 = h-rec-2*estribo_diam_cm - long_diam_cm
            self.tabla_confinamiento.setItem(row_idx, 12, QTableWidgetItem(str(bc1)))
            # bc2
            bc2 = b-rec-2*estribo_diam_cm - long_diam_cm
            self.tabla_confinamiento.setItem(row_idx, 13, QTableWidgetItem(str(bc2)))
            # X1
            x1 = (bc1 - estribo_diam_cm - long_diam_cm)/(num_bars_3 - 1)
            self.tabla_confinamiento.setItem(row_idx, 14, QTableWidgetItem(str(x1)))
            # X2
            x2 = (bc2 - estribo_diam_cm - long_diam_cm)/ (num_bars_2 - 1)
            self.tabla_confinamiento.setItem(row_idx, 15, QTableWidgetItem(str(x2)))
            #hx
            hx = max(x1,x2)
            self.tabla_confinamiento.setItem(row_idx, 16, QTableWidgetItem(str(hx)))
            # a(cm)
            a = b/4
            self.tabla_confinamiento.setItem(row_idx, 17, QTableWidgetItem(str(a)))
            # b (cm)
            if fy <= 4200:
                b_c = long_diam_cm * 6
            else:
                b_c = 0
            self.tabla_confinamiento.setItem(row_idx, 18, QTableWidgetItem(str(b_c)))
            
            # c (cm)
            if fy > 4200:
                c = 5 * long_diam_cm
            else:
                c = 0
            self.tabla_confinamiento.setItem(row_idx, 19, QTableWidgetItem(str(c)))
            
            # d (cm)
            d = 10 + (35 - hx)/3
            self.tabla_confinamiento.setItem(row_idx, 20, QTableWidgetItem(str(d)))
            
            
        self.tabla_confinamiento.resizeColumnsToContents()

# --- Bloque para probar la ventana de forma independiente ---
if __name__ == '__main__':
    # Datos de ejemplo (lista de diccionarios)
    SAMPLE_DATA = [
        {
            'b': 40, 'h': 60, 'cover': 4, 'rebar_long_size': '#8', 
            'estribo_size': '#3', 'num_bars_2': 3, 'num_bars_3': 4, 
            'fc': 280, 'fy': 4200
        },
        {
            'b': 50, 'h': 50, 'cover': 5, 'rebar_long_size': '#6', 
            'estribo_size': '#3', 'num_bars_2': 4, 'num_bars_3': 4, 
            'fc': 250, 'fy': 4200
        },
        {
            'b': 45, 'h': 70, 'cover': 4, 'rebar_long_size': '#7', 
            'estribo_size': '#4', 'num_bars_2': 3, 'num_bars_3': 5, 
            'fc': 300, 'fy': 4200
        }
    ]

    app = QApplication(sys.argv)
    main_window = ConfinamientoScreen(data_sections=SAMPLE_DATA)
    main_window.show()
    sys.exit(app.exec_())