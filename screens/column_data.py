import sys
from pathlib import Path
from collections import defaultdict # Modificacion
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSpacerItem, QSizePolicy, QFileDialog,
    QTableWidget, QTableWidgetItem, QScrollArea, QFrame, QComboBox,
    QTextEdit, QMessageBox, QInputDialog, QLineEdit
    
)
from PyQt5.QtGui import QFont, QPixmap 
from PyQt5.QtCore import Qt, QSize, QT_VERSION_STR, PYQT_VERSION_STR

import pandas as pd

from core import create_column_table, export_excel, etabs

from screens.identify_column import IdentificarColumnasScreen
from screens.info_gridlines_2 import InfoGridLinesScreen # modificacion

from dxf_drawer.drawing import Drawing
from dxf_drawer.detail import Detail
from dxf_drawer.column import RectangularColumn


class ColumnDataScreen(QWidget):
    """
    Pantalla para mostrar y gestionar datos de columnas después de conectar con ETABS.
    Inspirada en la imagen proporcionada.
    """
    def __init__(self, main_menu_ref,stories_window_ref, gridlines_window_ref, section_designer_window_ref,confinement_screen_ref,sap_model_object=None, parent=None, column_data=None, rect_sections=None, rebars=None):
        super().__init__(parent)
        self.main_menu_ref = main_menu_ref
        self.stories_window_ref = stories_window_ref
        self.gridlines_window_ref = gridlines_window_ref
        # Almacenamos los datos de gridlines originales para usarlos despues
        self._raw_gridlines_data = self._extract_unique_gridlines(column_data)
        self.section_designer_window_ref = section_designer_window_ref
        self.confinement_screen_ref = confinement_screen_ref
        self.sap_model = sap_model_object
        
        self.identificar_columnas_screen = None
        self.data_columns_for_render = None
        
        self.setWindowTitle("Detalle y Gestión de Columnas - ETABS")
        self.setGeometry(50, 50, 1300, 750) # Size based on complexity
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10,10,10,10)
        self.main_layout.setSpacing(10)
        
        # -- Seccion de Botones Superiores
        top_button_layout = QHBoxLayout()
        top_button_layout.setSpacing(5) # Menor espaciado para botones de accion
        
        self.btn_modificar_columnas = QPushButton("1. Reasignar Columnas")
        self.btn_exportar_excel = QPushButton("Exportar a Excel")
        self.btn_exportar_planos = QPushButton("Exportar DXF")
        self.btn_actualizar_modelo = QPushButton("Actualizar el Modelo")
       
        
        # top_button_layout.addWidget(self.btn_modificar_columnas)
        top_button_layout.addWidget(self.btn_exportar_excel)
        top_button_layout.addWidget(self.btn_exportar_planos)
        top_button_layout.addWidget(self.btn_actualizar_modelo)
        
        
        self.main_layout.addLayout(top_button_layout)
        
        # -- Seccion de Botones de Informacion del Modelo
        info_button_layout = QHBoxLayout()
        info_button_layout.setSpacing(5)
        
        self.btn_info_stories = QPushButton("Stories")
        self.btn_grid_lines = QPushButton("Grid lines")
        self.btn_section_editor = QPushButton("Section Editor")
        self.btn_renombrar_detalle = QPushButton("Renombrar Detalle")
        self.btn_confinement_calculator = QPushButton("Calculos de Confinamiento")
        
        info_button_layout.addWidget(self.btn_info_stories)
        info_button_layout.addWidget(self.btn_grid_lines)
        info_button_layout.addWidget(self.btn_section_editor)
        info_button_layout.addWidget(self.btn_renombrar_detalle)
        info_button_layout.addWidget(self.btn_confinement_calculator)
        
        self.main_layout.addLayout(info_button_layout, stretch=1)
        
        # Seccion de Botones para Seleccionar ubicacion de los archivos generados
        file_button_layout = QVBoxLayout()

        lbl_folder = QLabel("Seleccionar el folder donde se van a generar los archivos:")
        file_button_layout.addWidget(lbl_folder)
        folder_button_layout = QHBoxLayout()
        self.btn_folder_selection = QPushButton("Seleccionar")
        
        self.btn_folder_selection.clicked.connect(self.select_folder)
        
        self.txt_folder_selection = QTextEdit()
        self.txt_folder_selection.setFixedHeight(40)
        folder_button_layout.addWidget(self.btn_folder_selection)
        folder_button_layout.addWidget(self.txt_folder_selection)
        
        
        file_button_layout.addLayout(folder_button_layout)
        
        self.main_layout.addLayout(file_button_layout)
        
        # Seccion de Filtros ---
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)
        
        self.filter_gridline_input = QLineEdit()
        self.filter_gridline_input.setPlaceholderText("Filtrar por GridLine...")
        self.filter_gridline_input.textChanged.connect(self.filter_table)
        
        self.filter_detalle_input = QLineEdit()
        self.filter_detalle_input.setPlaceholderText("Filtrar por Detalle No...")
        self.filter_detalle_input.textChanged.connect(self.filter_table)
        
        self.filter_section_input = QLineEdit()
        self.filter_section_input.setPlaceholderText("Filtrar por Section...")
        self.filter_section_input.textChanged.connect(self.filter_table)
        
        self.filter_group_input = QLineEdit()
        self.filter_group_input.setPlaceholderText("Filtrar por Group...")
        self.filter_group_input.textChanged.connect(self.filter_table)
        
        filter_layout.addWidget(QLabel("Filtros:"))
        filter_layout.addWidget(self.filter_gridline_input)
        filter_layout.addWidget(self.filter_detalle_input)
        filter_layout.addWidget(self.filter_section_input)
        filter_layout.addWidget(self.filter_group_input)

        self.main_layout.addLayout(filter_layout)
        
        # -- Area de Tabs para Datos de Columnas
        self.tabs_layout = QHBoxLayout()
        
        # Placeholder para Rectangular
        group_rectangular_layout = QVBoxLayout()
        lbl_rectangular_armado = QLabel("[Rectangular] Armado transversal")
        lbl_rectangular_resultados = QLabel("[Rectangular] Resultados")
        self.table_rectangular_armado = QTableWidget(len(column_data), 25) # Filas, Columnas de ejemplo
        self.table_rectangular_armado.setHorizontalHeaderLabels(["Story","GridLine","Frame_id","Start Z", "End Z" ,"Label","Sección", "depth","width",
                                                                 "Material", "Long. R2 Bars", "Long. R3 Bars","Rebar",
                                                                 "Mat. Est.","Rebar. Est.","Cover","Detalle No.","bxh","As",
                                                                 "fc","Rebar Estribo", "nivel start", "nivel end","start_end_level","Group"])
        
        print(column_data[0].keys())
        print(column_data[0])
        
        
        # Configure QTable
        for col_idx, col in enumerate(column_data):
            
            # Col 0: Piso
            item_piso = QTableWidgetItem(col['story'])
            self.table_rectangular_armado.setItem(col_idx, 0, item_piso)
            
            # Col 1: GridLine
            item_gridline = QTableWidgetItem(str(col['GridLine']))
            self.table_rectangular_armado.setItem(col_idx, 1, item_gridline)
            
            # Col 2: Frame id
            item_frame_id = QTableWidgetItem(col['col_id'])
            self.table_rectangular_armado.setItem(col_idx, 2, item_frame_id)
            
            # Col 3: z start
            item_frame_id = QTableWidgetItem(str(col['z_start']))
            self.table_rectangular_armado.setItem(col_idx, 3, item_frame_id)
            
            # Col 4: Frame id
            item_frame_id = QTableWidgetItem(str(col['z_end']))
            self.table_rectangular_armado.setItem(col_idx, 4, item_frame_id)
            
            # Col 5: Label
            item_label = QTableWidgetItem(col['label'])
            self.table_rectangular_armado.setItem(col_idx, 5, item_label)
            
            # Col 6: Section
            combo_section = QComboBox()
            combo_section.addItems(rect_sections)
            
            if col['section'] in rect_sections:
                combo_section.setCurrentText(col['section'])
            else:
                print(f"Advertencia: El valor inicial '{col['section']}' para la fila {col_idx}")
                print(f"No se encuentra en las opciones del ComboBox")
                
            # item_section = QTableWidgetItem(col['section'])
            self.table_rectangular_armado.setCellWidget(col_idx, 6, combo_section)
            
            # Optional: Conectar signal para saber cuando cambia la seleccion
            # Usamos lambda para pasar la fila y el combobox a la funcion
            
            
            # Col 7: depthssss
            item_depth = QTableWidgetItem(str(col['depth']))
            self.table_rectangular_armado.setItem(col_idx, 7, item_depth)
            
            # Col 8: width
            item_width = QTableWidgetItem(str(col['width']))
            self.table_rectangular_armado.setItem(col_idx, 8, item_width)
            
            # Col 9: Material
            item_material = QTableWidgetItem(col['material'])
            self.table_rectangular_armado.setItem(col_idx, 9, item_material)
            
            # Col 10: Long. R2 Bars
            item_r2_bars = QTableWidgetItem(str(col['r2_bars']))
            self.table_rectangular_armado.setItem(col_idx, 10, item_r2_bars)
            
            # Col 11: Long. R3 Bars
            item_r3_bars = QTableWidgetItem(str(col['r3_bars']))
            self.table_rectangular_armado.setItem(col_idx, 11, item_r3_bars)
            
            # Col 12: Rebar #
            combo_rebar = QComboBox()
            combo_rebar.addItems(rebars)
            if col['Rebar'] in rebars:
            #     indice = rebars.index(col['Rebar'])
                combo_rebar.setCurrentText(col['Rebar'])
            else:
                print(f"Advertencia: El valor inicial '{col['Rebar']}' para la fila {col_idx}")
                print(f"No se encuentra en las opciones del ComboBox")
            self.table_rectangular_armado.setCellWidget(col_idx, 12, combo_rebar)
            # item_rebar = QTableWidgetItem(col['Rebar'])
            # self.table_rectangular_armado.setItem(col_idx, 12, combo_rebar)
            
            # Col 13: Mat. Est
            item_mat_est = QTableWidgetItem(col['Mat. Estribo'])
            self.table_rectangular_armado.setItem(col_idx, 13, item_mat_est)
            
            # Col 14: Rebar Est.
            combo_rebar_est = QComboBox()
            combo_rebar_est.addItems(rebars)
            if col['Est. Rebar'] in rebars:
                combo_rebar_est.setCurrentText(col['Est. Rebar'])
            else:
                print(f"Advertencia: El valor inicial '{col['Est. Rebar']}' para la fila {col_idx}")
                print(f"No se encuentra en las opciones del ComboBox")
            self.table_rectangular_armado.setCellWidget(col_idx, 14, combo_rebar_est)
            
            # Col 15: Cover
            item_cover = QTableWidgetItem(str(col['cover']))
            self.table_rectangular_armado.setItem(col_idx, 15,item_cover)
            
            # Col 16: Detalle #
            item_detalle = QTableWidgetItem(col['detail'])
            self.table_rectangular_armado.setItem(col_idx, 16,item_detalle)
            
            # Col 17: Detalle #
            item_detalle = QTableWidgetItem(col['bxh'])
            self.table_rectangular_armado.setItem(col_idx, 17,item_detalle)
            
            # Col 18: Detalle #
            item_detalle = QTableWidgetItem(col['As'])
            self.table_rectangular_armado.setItem(col_idx, 18,item_detalle)
            
            # Col 19: Detalle #
            item_detalle = QTableWidgetItem(str(col['fc']))
            self.table_rectangular_armado.setItem(col_idx, 19,item_detalle)
            
            # Col 20: Estribo Barra #
            item_est_rebar = QTableWidgetItem(col['Est. Rebar'])
            self.table_rectangular_armado.setItem(col_idx, 20,item_est_rebar)
            
            # Col 21: Start Level
            item_start_level = QTableWidgetItem(col['nivel_start'])
            self.table_rectangular_armado.setItem(col_idx, 21, item_start_level)
            
            # Col 22
            item_end_level = QTableWidgetItem(col['nivel_end'])
            self.table_rectangular_armado.setItem(col_idx, 22, item_end_level)
            
             # Col 23: start end level
            item_end_level = QTableWidgetItem(col['start_end_level'])
            self.table_rectangular_armado.setItem(col_idx, 23,item_end_level)
            
            # Col 24: Column Group
            item_col_group = QTableWidgetItem()
            self.table_rectangular_armado.setItem(col_idx, 24, item_col_group)
            
            
        self.table_rectangular_armado.resizeColumnsToContents()
        # self.table_rectangular_armado.resizeRowToContents()
        
        group_column_index = 24
        self.table_rectangular_armado.setColumnWidth(group_column_index, 250) # Establece un ancho de 150 píxeles (ajusta este valor si es necesario)
        
        
        # Pasamos la referencia de la tabla a la ventana de gridlines para que el diálogo de grupos pueda acceder a ella.
        if self.gridlines_window_ref:
            self.gridlines_window_ref.set_main_column_table(self.table_rectangular_armado)
        
        
        # self.table_rectangular_resultados = QTableWidget(5, 4)
        # self.table_rectangular_resultados.setHorizontalHeaderLabels(["CONF...", "ID Ramas vert.", "CONF...", "ID Ramas horiz."])
        
        group_rectangular_layout.addWidget(lbl_rectangular_armado)
        group_rectangular_layout.addWidget(self.table_rectangular_armado)
        group_rectangular_layout.addWidget(lbl_rectangular_resultados)
        # group_rectangular_layout.addWidget(self.table_rectangular_resultados)
    

        self.tabs_layout.addLayout(group_rectangular_layout)
        # self.tabs_layout.addLayout(group_circular_layout)

        # Para hacer scrollable el contenido principal si excede el tamaño
        scroll_content_widget = QWidget()
        scroll_content_widget.setLayout(self.tabs_layout)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_content_widget)
        scroll_area.setFrameShape(QFrame.NoFrame) # Sin borde para el área de scroll

        self.main_layout.addWidget(scroll_area, stretch=10) # Añadir el área de scroll al layout principal
        
        # -- Boton de Volver
        bottom_layout = QHBoxLayout()
        self.btn_back_to_menu = QPushButton("Volver al Menú Principal")
        self.btn_back_to_menu.clicked.connect(self.go_back_to_main_menu)
        bottom_layout.addStretch(1)
        bottom_layout.addWidget(self.btn_back_to_menu)
        bottom_layout.addStretch(1)

        self.main_layout.addLayout(bottom_layout)
        
         # Conectar acciones (placeholders por ahora)
        self.btn_modificar_columnas.clicked.connect(self.load_column_data_action)
        self.btn_exportar_excel.clicked.connect(self.exportar_excel_action)
        self.btn_exportar_planos.clicked.connect(self.exportar_planos_action)
        self.btn_info_stories.clicked.connect(self.show_info_stories)
        self.btn_grid_lines.clicked.connect(self.show_info_gridlines)
        self.btn_section_editor.clicked.connect(self.show_section_designer)
        self.btn_renombrar_detalle.clicked.connect(self.renombrar_detalle_action)
        self.btn_confinement_calculator.clicked.connect(self.show_confinement_screen)
        

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
        
        
        self.btn_modificar_columnas.setStyleSheet(action_button_style)
        self.btn_exportar_excel.setStyleSheet(action_button_style)
        self.btn_exportar_planos.setStyleSheet(action_button_style)
        self.btn_actualizar_modelo.setStyleSheet(action_button_style)
        self.btn_info_stories.setStyleSheet(action_button_style)
        self.btn_grid_lines.setStyleSheet(action_button_style)
        self.btn_section_editor.setStyleSheet(action_button_style)
        self.btn_renombrar_detalle.setStyleSheet(action_button_style)
        self.btn_confinement_calculator.setStyleSheet(action_button_style)
        
        

        # Estilo para el botón de volver (más grande y centrado)
        self.btn_back_to_menu.setStyleSheet("""
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
        
    def filter_table(self):
        """
        Filtra las filas de la tabla basandose en el texto QLineEdit de filtro.
        """
        gridline_filter = self.filter_gridline_input.text().lower()
        detalle_filter = self.filter_detalle_input.text().lower()
        section_filter = self.filter_section_input.text().lower()
        group_filter = self.filter_group_input.text().lower()
        
        for row in range(self.table_rectangular_armado.rowCount()):
            gridline_item = self.table_rectangular_armado.item(row, 1)
            detalle_item = self.table_rectangular_armado.item(row, 16)
            section_widget = self.table_rectangular_armado.cellWidget(row, 6) # Es un QComboBox
            group_item = self.table_rectangular_armado.item(row, 24)
           
            # Obtener texto de los items y widgets
            gridline_text = gridline_item.text().lower() if gridline_item else ""
            detalle_text = detalle_item.text().lower() if detalle_item else ""
            section_text = section_widget.currentText().lower() if isinstance(section_widget, QComboBox) else ""
            group_text = group_item.text().lower() if group_item else ""
           
            # Comprobar si la fila debe ser visible
            gridline_match = not gridline_filter or gridline_text == gridline_filter
            detalle_match = not detalle_filter or detalle_text == detalle_filter
            section_match = not section_filter or section_text in section_filter
            group_match = not group_filter or group_text == group_filter

            # La fila es visible solo si coincide con todos los filtros
            if gridline_match and detalle_match and section_match and group_match:
                self.table_rectangular_armado.setRowHidden(row, False)
            else:
                self.table_rectangular_armado.setRowHidden(row, True)
   
    def load_column_data_action(self):
        # Se crea una nueva instancia cada vez o se muestra una existente
        
        if self.identificar_columnas_screen is None or not self.identificar_columnas_screen.isVisible():
            self.identificar_columnas_screen = IdentificarColumnasScreen(self, stories=["N-100", "N-200"])
            self.identificar_columnas_screen.show()
        else:
            self.identificar_columnas_screen.activateWindow() # Traer al frente si ya está abierta
            
    def exportar_excel_action(self):
        print("Click Exportar a Excel")
                
        
        column_list_dict = []
        stories_list_dict = []
        gridlines_list_dict = []
        num_filas = self.table_rectangular_armado.rowCount()
        num_columnas = self.table_rectangular_armado.columnCount()
        
        # Obtener los headers de la tabla
        table_headers = []
        for col in range(num_columnas):
            header_item = self.table_rectangular_armado.horizontalHeaderItem(col)
            if header_item is not None and header_item.text():
                table_headers.append(header_item.text())
            # else:
            
            #     # Usar un nombre generico
            #     header_item.append(f"Columna_{col+1}")
                
        print(table_headers)
        for fila in range(num_filas):
            diccionario_fila = {}
            for columna in range(num_columnas):
                if columna in [6, 12,14]:
                    widget_combo = self.table_rectangular_armado.cellWidget(fila, columna)
                    if isinstance(widget_combo, QComboBox):
                        texto_combo = widget_combo.currentText()
                        if texto_combo is not None:
                            clave = table_headers[columna]
                            diccionario_fila[clave] = texto_combo
                        else:
                            clave=table_headers[columna]
                            diccionario_fila[clave] = None
                else:
                    item = self.table_rectangular_armado.item(fila, columna)
                    if item is not None and item.text() is not None:
                        clave = table_headers[columna]
                        diccionario_fila[clave] = item.text()
                    else:
                        clave = table_headers[columna]
                        diccionario_fila[clave] = None
                    
            # Solo agregar el diccionario si no esta completamente vacio
            if any(diccionario_fila.values()):
                column_list_dict.append(diccionario_fila)
            elif not diccionario_fila:
                column_list_dict.append(diccionario_fila)
                
        # Obtener stories
        ## Leer stories desde la ventana info_stories
        num_filas_stories = self.stories_window_ref.table_stories_info.rowCount()
        num_cols_stories = self.stories_window_ref.table_stories_info.columnCount()
        ### Headers de la Tabla Stories Info
        stories_headers = []
        for col in range(num_cols_stories):
            header_item = self.stories_window_ref.table_stories_info.horizontalHeaderItem(col)
            if header_item is not None and header_item.text():
                stories_headers.append(header_item.text())
                
        ## Data de la Tabla Stories
        for fila in range(num_filas_stories):
            diccionario_fila = {}
            for columna in range(num_cols_stories):
                item = self.stories_window_ref.table_stories_info.item(fila,columna)
                if item is not None and item.text() is not None:
                    clave = stories_headers[columna]
                    diccionario_fila[clave] = item.text()
                    
                else:
                    clave = stories_headers[columna]
                    diccionario_fila[clave] = None
                    
            # Solo agregar el diccionario si no esta completamente vacio
            if any(diccionario_fila.values()):
                stories_list_dict.append(diccionario_fila)
            elif not diccionario_fila:
                stories_list_dict.append(diccionario_fila)
                
        ## Data de la Tabla GridLines
        num_filas_gridlines = self.gridlines_window_ref.table.rowCount()
        num_cols_gridlines = self.gridlines_window_ref.table.columnCount()
        print(num_filas_gridlines, num_cols_gridlines)
        
        gridlines_headers = []
        for col in range(num_cols_gridlines):
            header_item = self.gridlines_window_ref.table.horizontalHeaderItem(col)
            if header_item is not None and header_item.text():
                gridlines_headers.append(header_item.text())
                
        for fila in range(num_filas_gridlines):
            diccionario_fila = {}
            for columna in range(num_cols_gridlines):
                item = self.gridlines_window_ref.table.item(fila,columna)
                if item is not None and item.text() is not None:
                    clave = gridlines_headers[columna]
                    diccionario_fila[clave] = item.text()
                else:
                    clave = gridlines_headers[columna]
                    diccionario_fila[clave] = None
                    
            # Solo agregar el diccionario si no esta completamente vacio
            if any(diccionario_fila.values()):
                gridlines_list_dict.append(diccionario_fila)
            elif not diccionario_fila:
                gridlines_list_dict.append(diccionario_fila)
                
                
        # -- DEBUG
        print(column_list_dict)
        print(stories_list_dict)
        print(gridlines_list_dict)
        
        # Obtener el folder donde se van a guardar los archivos
        folder_path = self.txt_folder_selection.toPlainText()
        full_filename = str(Path(folder_path) / "cuadro_columnas.xlsx")
        
        # Revisar que column records tenga todo lo necesario para exportar a excel
        # cols_records = column_list_dict
        if folder_path:
            export_excel.generate_excel_table(folder_path, stories_list_dict, gridlines_list_dict, column_list_dict)
            QMessageBox.information(self, "Proceso Completado",f"Archivo {full_filename} creado de forma exitosa.")
        else:
            print("Seleccione un folder en donde guardar los archivos.")#stories_data, grid_lines, column_records
        
    def realizar_renombrado(self, mapa_valores):
        print(f"Recibiendo datos para renombrar: {mapa_valores}")
        if not mapa_valores:
            return
        
        # Iterar sobre todas las celdas de la tabla
        for fila in range(self.table_rectangular_armado.rowCount()):
            item = self.table_rectangular_armado.item(fila, 1)
            # Verificar que la celda no este vacia
            if item and item.text():
                texto_celda = item.text()
                # Si el texto de la celda esta en nuestro mapa, lo reemplazamos
                if texto_celda in mapa_valores:
                    nuevo_valor = mapa_valores[texto_celda]
                    item.setText(nuevo_valor)
                    print(f"Cambiado '{texto_celda}' por '{nuevo_valor}' en ({fila}, 1)")
                    
                    
    def _update_group_column_in_table(self, groups):
        """
        Actualiza la columna 'Group' en la tabla principal (self.table_rectangular_armado)
        basándose en el diccionario de grupos proporcionado.

        Args:
            groups (dict): Un diccionario donde las llaves son los nombres de los grupos
                           y los valores son listas de los GridLine IDs que pertenecen a él.
        """
        table = self.table_rectangular_armado
        if not table:
            return

        # Índices de las columnas relevantes (basado en el código existente)
        GRIDLINE_COL_IDX = 1
        GROUP_COL_IDX = 24

        # 1. Crear un mapa inverso para una búsqueda eficiente: {grid_id: group_name}
        grid_to_group_map = {}
        for group_name, grid_ids in groups.items():
            for grid_id in grid_ids:
                grid_to_group_map[grid_id] = group_name

        # 2. Recorrer la tabla y actualizar la columna "Group"
        for row in range(table.rowCount()):
            gridline_item = table.item(row, GRIDLINE_COL_IDX)
            if not gridline_item:
                continue
            
            gridline_id = gridline_item.text()
            
            # Determinar el nombre del grupo para el GridLine actual
            group_name = grid_to_group_map.get(gridline_id, "") # Devuelve "" si no está en un grupo

            # Obtener o crear el item en la columna de grupo
            group_item = table.item(row, GROUP_COL_IDX)
            if not group_item:
                group_item = QTableWidgetItem(group_name)
                table.setItem(row, GROUP_COL_IDX, group_item)
            else:
                group_item.setText(group_name)

        print("Columna 'Group' en la tabla principal ha sido actualizada.")
                        
           
                    
         
    def exportar_planos_action(self):
        folder_path = self.txt_folder_selection.toPlainText()
        filename = 'detalles_columnas.dxf'
        full_filename = str(Path(folder_path) / filename)
        
        # Lectura de la informacion de la tabla de las columnas
        num_filas = self.table_rectangular_armado.rowCount()
        num_columnas = self.table_rectangular_armado.columnCount()
        
        column_list_dict = []
        
        # Obtener los headers de la tabla
        table_headers = []
        for col in range(num_columnas):
            header_item = self.table_rectangular_armado.horizontalHeaderItem(col)
            if header_item is not None and header_item.text():
                table_headers.append(header_item.text())
                
        print(table_headers)
        print(len(table_headers))
        for fila in range(num_filas):
            diccionario_fila = {}
            for columna in range(num_columnas):
                if columna in [6, 12,14]:
                    widget_combo = self.table_rectangular_armado.cellWidget(fila, columna)
                    if isinstance(widget_combo, QComboBox):
                        texto_combo = widget_combo.currentText()
                        if texto_combo is not None:
                            clave = table_headers[columna]
                            diccionario_fila[clave] = texto_combo
                        else:
                            clave=table_headers[columna]
                            diccionario_fila[clave] = None
                else:
                    item = self.table_rectangular_armado.item(fila, columna)
                    if item is not None and item.text() is not None:
                        clave = table_headers[columna]
                        diccionario_fila[clave] = item.text()
                    else:
                        clave = table_headers[columna]
                        diccionario_fila[clave] = None
                    
            # Solo agregar el diccionario si no esta completamente vacio
            if any(diccionario_fila.values()):
                column_list_dict.append(diccionario_fila)
            elif not diccionario_fila:
                column_list_dict.append(diccionario_fila)
        
        df_columns = pd.DataFrame(column_list_dict)
        
        lista_detalles = df_columns.drop_duplicates(subset=['Detalle No.'])
        lista_detalles_dict = lista_detalles.to_dict(orient='records')
        
        # Create list of columns
        detalles = []
        start_point = (100,100)
        width_detail = 4000
        height_detail = 4000
        counter = 0
        for section in lista_detalles_dict:
            detalle = section['Detalle No.']
            origin_point = (start_point[0], start_point[1] - (height_detail*counter))
            width = min(int(float(section['depth'])), int(float(section['width']))) * 10 # Convert to mm
            height = max(int(float(section['depth'])), int(float(section['width']))) * 10 # Convert to mm
            fc = int(float(section['fc'])) # kg/cm2
            
            r3 = int(section['Long. R2 Bars'])
            r2 = int(section['Long. R3 Bars'])
            
            long_bars = 2*r2 + 2*(r3 - 2)
            cover = float(section['Cover']) * 10 # Convert to mm
            rebar = section['Rebar']
            rebar_est = section['Rebar. Est.']
            actual_column = RectangularColumn(
                    width=width,
                    height=height,
                    fc=str(fc),
                    number_of_bars=long_bars,
                    rebar_type=rebar,
                    r2_bars=r2,
                    r3_bars=r3,
                    stirrup_type=rebar_est,
                    cover=cover
                    
                )
            detail = Detail(
                name=detalle,
                origin=origin_point,
                width=width_detail,
                height=height_detail
            )
            detail.set_column(actual_column)
            detail.set_origin_for_col(actual_column.width, actual_column.height)
            detalles.append(detail)
            
            counter += 1
            
        
        drawing = Drawing(
            filename=full_filename,
            list_details=detalles
        )
        drawing.create_dxf()
        QMessageBox.information(self, "Proceso Completado",f"Archivo {full_filename} creado de forma exitosa.")
            
        
            
        
        
        # Call dxf drawer
        # dxf_drawing = Drawing()
        
    
    def show_info_stories(self):
        self.stories_window_ref.show()
        
    def _extract_unique_gridlines(self, column_data):
        """Extrae información única de GridLines (ID, x, y) de los datos de columnas."""
        if not column_data:
            return []
        
        df = pd.DataFrame(column_data)
        if 'GridLine' not in df.columns or 'pos_x' not in df.columns or 'pos_y' not in df.columns:
            return []
            
        unique_gridlines = df[['GridLine', 'pos_x', 'pos_y']].drop_duplicates().to_dict('records')
        
        # Convertir a la tupla (id, x, y) que espera InfoGridLinesScreen
        return [(str(g['GridLine']), g['pos_x'], g['pos_y']) for g in unique_gridlines]
    
    def _group_identical_gridlines_from_table(self):
        """
        Analiza la tabla de datos de columnas y agrupa los GridLines que tienen
        contenido idéntico a través de todos los niveles.
        """
        table = self.table_rectangular_armado
        if table.rowCount() == 0:
            return {}

        # Mapea ID de GridLine a una lista de sus valores en la tabla
        gridline_content = defaultdict(list)
        
        # Columnas a comparar para determinar si los GridLines son idénticos
        # Se excluyen Story, Frame_id, y coordenadas Z que varían por nivel.
        # Se incluye el Detalle No. y el Grupo.
        columns_to_check = [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 24]
        
        # 1. Crear una "firma" para cada GridLine basada en su contenido
        gridlines = sorted(list(set(table.item(row, 1).text() for row in range(table.rowCount()))))

        signatures = {}
        for grid_id in gridlines:
            content = []
            for row in range(table.rowCount()):
                if table.item(row, 1).text() == grid_id:
                    row_content = []
                    for col_idx in columns_to_check:
                        widget = table.cellWidget(row, col_idx)
                        if isinstance(widget, QComboBox):
                            row_content.append(widget.currentText())
                        else:
                            item = table.item(row, col_idx)
                            row_content.append(item.text() if item else "")
                    content.append(tuple(row_content))
            signatures[grid_id] = tuple(content)

        # 2. Agrupar los GridLines que tienen la misma firma
        grouped_by_signature = defaultdict(list)
        for grid_id, signature in signatures.items():
            grouped_by_signature[signature].append(grid_id)

        # 3. Formatear el resultado final
        final_groups = {}
        group_counter = 1
        for signature, grid_ids in grouped_by_signature.items():
            if len(grid_ids) > 1: # Solo nos interesan los grupos con más de un miembro
                group_name = f"Grupo {group_counter}"
                final_groups[group_name] = sorted(grid_ids)
                group_counter += 1
        
        return final_groups
    
    
        
    def show_info_gridlines(self):
        """
        Gestiona la creación y visualización de la ventana de información de GridLines,
        incluyendo la agrupación y actualización de la tabla principal.
        """
        # Si la ventana no existe o fue cerrada, se crea una nueva.
        if self.gridlines_window_ref is None or not self.gridlines_window_ref.isVisible():
            # 1. Agrupar los GridLines usando la función existente
            print("Agrupando GridLines idénticos desde la tabla...")
            preloaded_groups = self._group_identical_gridlines_from_table()
            print(f"Grupos encontrados: {preloaded_groups}")

            # 2. Actualizar la columna "Group" en la tabla de datos principal (NUEVO PASO)
            self._update_group_column_in_table(preloaded_groups)

            # 3. Instanciar la ventana de InfoGridLines, pasando los datos y los grupos
            self.gridlines_window_ref = InfoGridLinesScreen(
                gridlines_data=self._raw_gridlines_data,
                groups=preloaded_groups
            )
            
            # 4. Conectar la señal para renombrar y pasar la referencia de la tabla
            self.gridlines_window_ref.datos_para_renombrar.connect(self.realizar_renombrado)
            self.gridlines_window_ref.set_main_column_table(self.table_rectangular_armado)
        
        # 5. Mostrar la ventana
        self.gridlines_window_ref.show()
        self.gridlines_window_ref.activateWindow() # Traer al frente
        
    def show_confinement_screen(self):
        """Muestra la pantalla de cálculo de confinamiento."""
        if self.confinement_screen_ref:
            self.confinement_screen_ref.show()

    def show_section_designer(self):
        self.section_designer_window_ref.show()
        
    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Seleccionar un folder", "")
        
        if folder_path:
            self.txt_folder_selection.setText(folder_path)
        else:
            print("Seleccion de Folder cancelada.")


    def go_back_to_main_menu(self):
        """Oculta esta pantalla y muestra el menú principal."""
        self.hide()
        if self.main_menu_ref:
            self.main_menu_ref.show()
            self.main_menu_ref.sap_model_connected = None # Limpiar referencia en el menú principal
            
    def renombrar_detalle_action(self):
        selected_items = self.table_rectangular_armado.currentItem()
        if not selected_items:
            QMessageBox.warning(self, "Seleccion Requerida", "Por favor seleccione una fila en la columna Detalle No.")
            return
        
        
        selected_row = selected_items.row()
        detalle_item = self.table_rectangular_armado.item(selected_row, 16)
        
        if not detalle_item:
            return
        
        old_detalle_name = detalle_item.text()
        new_detalle_name, ok = QInputDialog.getText(self, "Renombrar Detalle", f"Renombrar '{old_detalle_name}' a: ", text=old_detalle_name)
        
        if ok and new_detalle_name and new_detalle_name != old_detalle_name:
            # Bucle para renombrar en todas las filas que hacen match
            for row in range(self.table_rectangular_armado.rowCount()):
                item = self.table_rectangular_armado.item(row,16)
                if item and item.text() == old_detalle_name:
                    item.setText(new_detalle_name)
                    
            QMessageBox.information(self, "Exito", f"El detalle '{old_detalle_name}' ha sido renombrado a: '{new_detalle_name}.'")

    def closeEvent(self, event):
        """Maneja el cierre de la ventana."""
        self.go_back_to_main_menu() # Asegura que el menú principal se muestre
        super().closeEvent(event)
      