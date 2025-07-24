import sys
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QPushButton,
    QHeaderView,
    QHBoxLayout,
)
from PyQt5.QtCore import Qt
import math

# Lista de propiedades de barras de refuerzo en centímetros
REBAR_PROPERTIES_CM = [
    {'type': '#2', 'diameter': 0.635, 'area': 0.32},
    {'type': '#3', 'diameter': 0.9525, 'area': 0.71},
    {'type': '#4', 'diameter': 1.27, 'area': 1.27},
    {'type': '#5', 'diameter': 1.5875, 'area': 1.98},
    {'type': '#6', 'diameter': 1.905, 'area': 2.85},
    {'type': '#7', 'diameter': 2.2225, 'area': 3.88},
    {'type': '#8', 'diameter': 2.54, 'area': 5.07},
    {'type': '#9', 'diameter': 2.865, 'area': 6.45},
    {'type': '#10', 'diameter': 3.226, 'area': 8.17},
    {'type': '#11', 'diameter': 3.581, 'area': 10.07},
    {'type': '#12', 'diameter': 3.81, 'area': 11.40},
    {'type': '#14', 'diameter': 4.445, 'area': 15.52},
    {'type': '#16', 'diameter': 5.08, 'area': 20.27},
    {'type': '#18', 'diameter': 5.715, 'area': 25.65},
]

class ConfinementScreen(QWidget):
    """
    Una nueva pantalla para mostrar los cálculos de confinamiento de columnas.
    """
    def __init__(self, section_data_list):
        """
        Inicializa la pantalla de cálculo de confinamiento.

        Args:
            section_data_list (list): Una lista con diccionarios de datos de secciones transversales.
        """
        super().__init__()
        self.initial_section_data_list = section_data_list
        self.setWindowTitle("Cálculo de Confinamiento")
        self.setGeometry(200, 200, 1800, 600)

        main_layout = QVBoxLayout()
        self.table = QTableWidget()
        main_layout.addWidget(self.table)
        
        self.recalculate_button = QPushButton("Recalcular")
        self.recalculate_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745; color: white; font-weight: bold;
                border-radius: 5px; padding: 8px 15px; border: none; max-width: 120px;
            }
            QPushButton:hover { background-color: #218838; }
            QPushButton:pressed { background-color: #1e7e34; }
        """)
        self.recalculate_button.setCursor(Qt.PointingHandCursor)
        self.recalculate_button.clicked.connect(self.recalculate_table)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.recalculate_button)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
        self.populate_table()

    def get_rebar_area(self, rebar_type_num):
        rebar_type_str = rebar_type_num
        for rebar in REBAR_PROPERTIES_CM:
            if rebar['type'] == rebar_type_str:
                return rebar['area']
        return 0

    def get_rebar_diameter(self, rebar_type_num):
        rebar_type_str = rebar_type_num
        for rebar in REBAR_PROPERTIES_CM:
            if rebar['type'] == rebar_type_str:
                return rebar['diameter']
        return 0

    def calculate_confinement(self, current_data, rebar_size_est, rebar_size_long):
        """
        Realiza los cálculos de confinamiento basados en los datos de la sección.
        """
        try:
            h = float(current_data.get("H (cm)", 0))
            b = float(current_data.get("L (cm)", 0))
            fc_psi = float(current_data.get("f'c (psi)", 0))
            rec = float(current_data.get("rec(cm)", 0))
            n_b_bc1 = int(current_data.get("N_b bc1", 1))
            n_b_bc2 = int(current_data.get("N_b bc2", 1))
            fy = float(current_data.get("fy (kg/cm2)", 4200)) # Se lee fy desde los datos actuales

            d_est = self.get_rebar_diameter(rebar_size_est)
            d_long = self.get_rebar_diameter(rebar_size_long)
            a_est = self.get_rebar_area(rebar_size_est)
            a_long = self.get_rebar_area(rebar_size_long)

            bc1 = b - 2 * rec
            bc2 = h - 2 * rec
            ach = bc1 * bc2 if bc1 > 0 and bc2 > 0 else 0
            ag = b * h

            x1 = (bc1 - d_est - d_long) / (n_b_bc1 - 1) if n_b_bc1 > 1 and bc1 > 0 else 0
            x2 = (bc2 - d_est - d_long) / (n_b_bc2 - 1) if n_b_bc2 > 1 and bc2 > 0 else 0

            fc_kgcm2 = fc_psi * 0.070307
            
            ash_sbc = 0
            if ach > 0 and fy > 0:
                ash_sbc_1 = 0.3 * (ag / ach - 1) * (fc_kgcm2 / fy)
                ash_sbc_2 = 0.09 * (fc_kgcm2 / fy)
                ash_sbc = max(ash_sbc_1, ash_sbc_2)

            hx = max(x1, x2)
            a_cm = h / 4
            b_cm = 6 * d_long if fy <= 4200 else 0
            c_cm = "Placeholder C"
            d_cm = "Placeholder D"

            # Se elimina 'fy' del diccionario de retorno, ya que es un dato de entrada
            return {
                "D_est (cm)": f"{rebar_size_est} ({d_est:.3f})",
                "D_long (cm)": f"{rebar_size_long} ({d_long:.3f})",
                "A_est (cm2)": a_est,
                "A_long (cm2)": a_long,
                "bc1 (cm)": bc1,
                "bc2 (cm)": bc2,
                "X1 (cm)": x1,
                "X2 (cm)": x2,
                "Ach (cm2)": ach,
                "Ash/Sbc (req)": ash_sbc,
                "hx": hx,
                "(a) (cm)": a_cm,
                "(b) (cm)": b_cm,
                "(c) (cm)": c_cm,
                "(d) (cm)": d_cm,
            }
        except (ValueError, TypeError) as e:
            print(f"Error en los datos de entrada para el cálculo: {e}")
            print(current_data)
            return {}

    def populate_table(self):
        """
        Llena la tabla con los resultados de los cálculos.
        """
        # Se mueve 'fy (kg/cm2)' a las cabeceras de entrada
        self.input_headers = [
            "Pu(kg)", "H (cm)", "N_b bc2", "L (cm)", 
            "N_b bc1", "rec(cm)", "f'c (psi)", "fy (kg/cm2)"
        ]
        # Se elimina 'fy (kg/cm2)' de las cabeceras calculadas
        self.calculated_headers = [
            "D_est (cm)", "D_long (cm)", "A_est (cm2)", "A_long (cm2)",
            "bc1 (cm)", "bc2 (cm)", "X1 (cm)", "X2 (cm)",
            "Ach (cm2)", "Ash/Sbc (req)", "hx", "(a) (cm)", "(b) (cm)",
            "(c) (cm)", "(d) (cm)",
        ]
        
        headers = ["Sección", "Ver Section Designer"] + self.input_headers + self.calculated_headers
        self.header_map = {header: i for i, header in enumerate(headers)}

        self.table.setColumnCount(len(headers))
        self.table.setRowCount(len(self.initial_section_data_list))
        self.table.setHorizontalHeaderLabels(headers)

        for row, section_data in enumerate(self.initial_section_data_list):
            
            pu_value = section_data.get("pu")
            if pu_value is None:
                pu_value = 3000
            
            # Se añade 'fy' a los datos iniciales leídos del constructor
            initial_data = {
                "Sección": section_data.get("name", f"Sección {row+1}"),
                "Pu(kg)": pu_value,
                "H (cm)": section_data.get("h", 60),
                "N_b bc2": section_data.get("n_b_bc2", 4),
                "L (cm)": section_data.get("b", 125),
                "N_b bc1": section_data.get("n_b_bc1", 6),
                "rec(cm)": section_data.get("rec", 4.0),
                "f'c (psi)": section_data.get("f'c", 8500),
                "fy (kg/cm2)": section_data.get("fy", 4200),
            }

            rebar_size_est = section_data.get("estribo", '#4')
            rebar_size_long = section_data.get("rebar_size", '#8')

            calculated_data = self.calculate_confinement(initial_data, rebar_size_est, rebar_size_long)
            full_data_row = {**initial_data, **calculated_data}

            for header, value in full_data_row.items():
                col_index = self.header_map.get(header)
                if col_index is not None:
                    formatted_value = f"{value:.4f}" if isinstance(value, float) else str(value)
                    item = QTableWidgetItem(formatted_value)
                    # La lógica para hacer las celdas editables/no editables funciona sin cambios
                    if header not in self.input_headers and header != "Sección":
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.table.setItem(row, col_index, item)

            self.add_designer_button(row, self.header_map["Ver Section Designer"])

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)

    def add_designer_button(self, row, col):
        btn_section_designer = QPushButton("Ver")
        btn_section_designer.setStyleSheet("""
            QPushButton {
                background-color: #007BFF; color: white; font-weight: bold;
                border-radius: 5px; padding: 5px 10px; border: none;
            }
            QPushButton:hover { background-color: #0056b3; }
            QPushButton:pressed { background-color: #004085; }
        """)
        btn_section_designer.setCursor(Qt.PointingHandCursor)
        btn_section_designer.clicked.connect(lambda checked, r=row: self.open_section_designer(r))
        
        container_widget = QWidget()
        layout = QHBoxLayout(container_widget)
        layout.addWidget(btn_section_designer)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setAlignment(Qt.AlignCenter)
        self.table.setCellWidget(row, col, container_widget)

    def recalculate_table(self):
        for row in range(self.table.rowCount()):
            current_data = {}
            for header in self.input_headers:
                col_index = self.header_map[header]
                item = self.table.item(row, col_index)
                if item:
                    current_data[header] = item.text()
            
            section_data = self.initial_section_data_list[row]
            rebar_size_est = section_data.get("estribo", '#4')
            rebar_size_long = section_data.get("rebar_size", '#8')
            
            calculated_data = self.calculate_confinement(current_data, rebar_size_est, rebar_size_long)

            for header, value in calculated_data.items():
                col_index = self.header_map[header]
                if header in self.calculated_headers:
                    formatted_value = f"{value:.4f}" if isinstance(value, float) else str(value)
                    item = self.table.item(row, col_index)
                    if item:
                        item.setText(formatted_value)
                    else:
                        self.table.setItem(row, col_index, QTableWidgetItem(formatted_value))
        print("Tabla recalculada.")

    def open_section_designer(self, row):
        section_name = self.table.item(row, self.header_map["Sección"]).text()
        print(f"Abriendo Section Designer para: {section_name} (Fila {row})")