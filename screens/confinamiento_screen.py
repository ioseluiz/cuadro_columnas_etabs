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
        self.setGeometry(200, 200, 1800, 600)  # Aumentamos el ancho para las nuevas columnas

        # Layout principal
        main_layout = QVBoxLayout()
        
        # Tabla
        self.table = QTableWidget()
        main_layout.addWidget(self.table)
        
        # Botón de Recalcular
        self.recalculate_button = QPushButton("Recalcular")
        self.recalculate_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 8px 15px;
                border: none;
                max-width: 120px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        self.recalculate_button.setCursor(Qt.PointingHandCursor)
        self.recalculate_button.clicked.connect(self.recalculate_table)
        
        # Layout para el botón para poder centrarlo
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.recalculate_button)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        self.populate_table()

    def calculate_confinement(self, current_data, rebar_size_est, rebar_size_long):
        """
        Realiza los cálculos de confinamiento basados en los datos de la sección.
        Esta es una implementación de las fórmulas de la hoja de cálculo.
        """
        try:
            h = float(current_data.get("H (cm)", 0))
            b = float(current_data.get("L (cm)", 0))
            fc_psi = float(current_data.get("f'c (psi)", 0))
            rec = float(current_data.get("rec(cm)", 0))
            n_b_bc1 = int(current_data.get("N_b bc1", 1))
            n_b_bc2 = int(current_data.get("N_b bc2", 1))
            fy = 4200  # Acero de refuerzo (kg/cm2)

            # Conversión de números de barra a diámetros (pulgadas a cm)
            rebar_diameters = {
                2: 0.635, 3: 0.953, 4: 1.27, 5: 1.588, 6: 1.905, 
                7: 2.223, 8: 2.54, 9: 2.858, 10: 3.175, 11: 3.493, 
                12: 3.81, 14: 4.445, 16: 5.08, 18: 5.715
            }
            
            # Calcular diámetros
            d_est = rebar_diameters.get(rebar_size_est, 0)
            d_long = rebar_diameters.get(rebar_size_long, 0)
            
            # Calcular áreas (π * d²/4)
            import math
            a_est = math.pi * (d_est**2) / 4
            a_long = math.pi * (d_long**2) / 4

            # Calculos intermedios
            bc1 = b - 2 * rec
            bc2 = h - 2 * rec
            ach = bc1 * bc2 if bc1 > 0 and bc2 > 0 else 0
            ag = b * h

            # Cálculo de X1 y X2
            x1 = 0
            x2 = 0
            if n_b_bc1 > 1 and bc1 > 0:
                x1 = (bc1 - d_est - d_long) / (n_b_bc1 - 1)
            if n_b_bc2 > 1 and bc2 > 0:
                x2 = (bc2 - d_est - d_long) / (n_b_bc2 - 1)

            # Cuantía volumétrica de confinamiento (ACI 318)
            fc_kgcm2 = fc_psi * 0.070307
            
            ash_sbc = 0
            if ach > 0:
                ash_sbc_1 = 0.3 * (ag / ach - 1) * (fc_kgcm2 / fy)
                ash_sbc_2 = 0.09 * (fc_kgcm2 / fy)
                ash_sbc = max(ash_sbc_1, ash_sbc_2)

            # --- Nuevos Cálculos ---
            hx = max(x1, x2)
            a_cm = h / 4
            b_cm = 6 * d_long if fy <= 4200 else 0
            c_cm = "Placeholder C"  # Placeholder para la fórmula de (c)
            d_cm = "Placeholder D"  # Placeholder para la fórmula de (d)

            return {
                "D_est (cm)": f"#{rebar_size_est} ({d_est:.3f})",
                "D_long (cm)": f"#{rebar_size_long} ({d_long:.3f})",
                "A_est (cm2)": a_est,
                "A_long (cm2)": a_long,
                "fy (kg/cm2)": fy,
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
            return {}

    def populate_table(self):
        """
        Llena la tabla con los resultados de los cálculos.
        """
        # Definir qué columnas son editables y cuáles son calculadas
        self.input_headers = [
            "Pu(kg)", 
            "H (cm)", 
            "N_b bc2",
            "L (cm)", 
            "N_b bc1",
            "rec(cm)", 
            "f'c (psi)"
        ]
        self.calculated_headers = [
            "D_est (cm)", 
            "D_long (cm)",
            "A_est (cm2)",
            "A_long (cm2)",
            "fy (kg/cm2)", 
            "bc1 (cm)", 
            "bc2 (cm)", 
            "X1 (cm)",
            "X2 (cm)",
            "Ach (cm2)", 
            "Ash/Sbc (req)",
            "hx",
            "(a) (cm)",
            "(b) (cm)",
            "(c) (cm)",
            "(d) (cm)",
        ]
        
        headers = ["Sección", "Ver Section Designer"] + self.input_headers + self.calculated_headers
        self.header_map = {header: i for i, header in enumerate(headers)}

        self.table.setColumnCount(len(headers))
        self.table.setRowCount(len(self.initial_section_data_list))
        self.table.setHorizontalHeaderLabels(headers)

        for row, section_data in enumerate(self.initial_section_data_list):
            initial_data = {
                "Sección": section_data.get("name", f"Sección {row+1}"),
                "Pu(kg)": section_data.get("pu", 3000 + row * 500),
                "H (cm)": section_data.get("h", 60),
                "N_b bc2": section_data.get("n_b_bc2", 4),
                "L (cm)": section_data.get("b", 125),
                "N_b bc1": section_data.get("n_b_bc1", 6),
                "rec(cm)": section_data.get("rec", 4.0),
                "f'c (psi)": section_data.get("f'c", 8500),
            }

            rebar_size_est = section_data.get("estribo", 4)
            rebar_size_long = section_data.get("rebar_size", 8)

            calculated_data = self.calculate_confinement(initial_data, rebar_size_est, rebar_size_long)
            full_data_row = {**initial_data, **calculated_data}

            for header, value in full_data_row.items():
                col_index = self.header_map.get(header)
                if col_index is not None:
                    item = QTableWidgetItem(str(value))
                    if header not in self.input_headers and header != "Sección":
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.table.setItem(row, col_index, item)

            self.add_designer_button(row, self.header_map["Ver Section Designer"])

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)

    def add_designer_button(self, row, col):
        """Añade el botón 'Ver' a la celda especificada."""
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
        """Lee los datos de todas las filas, los recalcula y actualiza la tabla."""
        for row in range(self.table.rowCount()):
            current_data = {}
            for header in self.input_headers:
                col_index = self.header_map[header]
                item = self.table.item(row, col_index)
                if item:
                    current_data[header] = item.text()
            
            section_data = self.initial_section_data_list[row]
            rebar_size_est = section_data.get("estribo", 4)
            rebar_size_long = section_data.get("rebar_size", 8)
            
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
        """
        Esta función se ejecutará al hacer clic en el botón "Ver Section Designer".
        """
        section_name = self.table.item(row, self.header_map["Sección"]).text()
        print(f"Abriendo Section Designer para: {section_name} (Fila {row})")

# if __name__ == '__main__':
#     app = QApplication(sys.argv)
    
#     mock_section_data_list = [
#         {"name": "C-60x125-26N8-CO8.5-EN4/7", "b": 125.0, "h": 60.0, "f'c": 8500, "rebar_size": 8, "estribo": 4, "pu": 3000, "rec": 4.0, "n_b_bc2": 4, "n_b_bc1": 6},
#         {"name": "C-70x140-30N10-CO9.0-EN5/8", "b": 140.0, "h": 70.0, "f'c": 9000, "rebar_size": 10, "estribo": 5, "pu": 3500, "rec": 4.5, "n_b_bc2": 5, "n_b_bc1": 7},
#         {"name": "C-50x100-20N6-CO7.5-EN3/6", "b": 100.0, "h": 50.0, "f'c": 7500, "rebar_size": 6, "estribo": 3, "pu": 2500, "rec": 3.5, "n_b_bc2": 3, "n_b_bc1": 5},
#         {"name": "C-80x160-36N12-CO10.0-EN6/9", "b": 160.0, "h": 80.0, "f'c": 10000, "rebar_size": 12, "estribo": 6, "pu": 4000, "rec": 5.0, "n_b_bc2": 6, "n_b_bc1": 8},
#         {"name": "C-65x130-28N9-CO8.8-EN4.5/7.5", "b": 130.0, "h": 65.0, "f'c": 8800, "rebar_size": 9, "estribo": 4.5, "pu": 3200, "rec": 4.2, "n_b_bc2": 4, "n_b_bc1": 6}
#     ]
    
#     screen = ConfinementScreen(mock_section_data_list)
#     screen.show()
#     sys.exit(app.exec_())