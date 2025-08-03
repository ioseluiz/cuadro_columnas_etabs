import sys
import json
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QSpacerItem,
    QSizePolicy,
    QFileDialog,
    QTableWidget,
    QTableWidgetItem,
    QScrollArea,
    QFrame,
    QProgressDialog,
    QMessageBox
)
import comtypes.client
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt, QSize, QT_VERSION_STR, PYQT_VERSION_STR, QObject, pyqtSignal, QThread

from core import create_column_table, etabs
from core.etabs import UNITS_LENGTH_CM, UNITS_FORCE_KGF, UNITS_TEMP_C

# Import Screens
from screens.column_data import ColumnDataScreen
from screens.open_file import OpenFileWindow
from screens.info_stories import InfoStoriesScreen
from screens.info_gridlines_2 import InfoGridLinesScreen
from screens.section_designer_2 import SectionDesignerScreen
from screens.confinamiento_screen import ConfinementScreen

class Worker(QObject):
    # Signal cuando acabe el proceso
    finished = pyqtSignal()
    progress = pyqtSignal(str)
    crear_ventana_signal = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
       
    
    def run(self):
        comtypes.CoInitialize()
         # Obtener Modelo
        self.sap_model = etabs.obtener_sapmodel_etabs()
        
        comtypes.CoUninitialize()
        
         # Set units to kg-cm
        etabs.establecer_units_etabs(
            self.sap_model, UNITS_FORCE_KGF, UNITS_LENGTH_CM, UNITS_TEMP_C
        )
        
        data_cols_labels_story, gridlines_data = etabs.get_story_lable_col_name(self.sap_model)
        # Get stories with elevation
        stories_with_elevations = etabs.get_stories_with_elevations(self.sap_model)
        # Get defined rebars
        defined_rebars = etabs.get_defined_rebars(self.sap_model)
        # Get concrete sections
        rect_sections = etabs.get_rect_concrete_sections(self.sap_model)
        rectangular_sections = etabs.get_rectangular_concrete_sections(self.sap_model)
        sections = []
        rebars = []
        print("*****Rectangular Sections*****")
        print(rectangular_sections)
        for item in rectangular_sections:
            print(item['section'])
        for item in rect_sections:
            print(item["Nombre"])
            sections.append(item["Nombre"])
        for item in defined_rebars:
            rebars.append(item["Nombre"])
            
        # Emitir signal con info
        self.crear_ventana_signal.emit({
            'data_cols_labels_story': data_cols_labels_story,
            'stories_with_elevations': stories_with_elevations,
            'defined_rebars': defined_rebars,
            'rect_sections': rect_sections,
            'rectangular_sections': rectangular_sections,
            'sections': sections,
            'rebars': rebars,
            'sap_model': self.sap_model,
            'gridlines_data': gridlines_data
        })
        
        self.finished.emit()
        
class FileLoaderWorker(QObject):
    """
        Worker para cargar y procesar el archivo JSON en un hilo separado.
    """
    # Signal que se emite con los datos cargados cuando el proceso es exitoso.
    finished = pyqtSignal(dict)
    # Signal que se emite con un mensaje de error si algo falla.
    error = pyqtSignal(str)
    
    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        
    def run(self):
        """
            Logica de carga de archivo que se ejecuta en el hilo secundario.
        """
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                loaded_json = json.load(f)
                
            table_data = loaded_json.get('table_data', [])
            combo_options = loaded_json.get('combo_options', {})
            sections_list = combo_options.get('sections', [])
            rebars_list = combo_options.get('rebars', [])
            
            gridlines_data = loaded_json.get('gridlines_data', [])
            
            sections_properties = loaded_json.get("sections_properties", [])
            
            if not table_data:
                self.error.emit("El archivo no contiene datos de la tabla o tiene un formato incorrecto.")
                return
            
            # Prepara el diccionario de datos para emitir
            data_to_emit = {
                "table_data": table_data,
                "sections_list": sections_list,
                "rebars_list": rebars_list,
                "gridlines_data": gridlines_data,
                "sections_properties": sections_properties
            }
            self.finished.emit(data_to_emit)
            
        except json.JSONDecodeError:
            self.error.emit("Error de Formato: El archivo no es un JSON valido")
        except Exception as e:
            self.error.emit(f"No se pudo cargar el archivo.\nError: {e}")
        


class MainMenuScreen(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Menu Principal")
        self.setGeometry(100, 100, 800, 600)  # x, y, width, height
        self.new_game_window = None  # Attribute to hold the new game window instance
        self.column_data_screen = None  # Atributo para la nueva pantalla
        self.sap_model_connected = None  # Para almacenar el objeto SapModel
        self.info_stories_screen = None # Window with Stories Data
        self.info_gridlines_screen = None # Window with GridLines Data
        self.section_designer_screen = None # Window with Section Data
        self.confinement_screen = None

        # --- Central Widget and Layout ---
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        # Main vertical layout for the central widget
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(50, 50, 50, 50)
        self.main_layout.setSpacing(20)
  
        # --- Background Image Placeholder ---
        self.background_image_path = "path/to/your/background_image.jpg"

        # --- Title Label ---
        self.title_label = QLabel("ETABS - Cuadro de Columnas", self)
        self.title_label.setAlignment(Qt.AlignCenter)

        # --- Menu Buttons ---
        # self.btn_start_game = QPushButton("Crear cuadro de cols")
        # self.btn_connect_etabs = QPushButton("Conectar con archivo de ETABS abierto")
        self.btn_identify_columns = QPushButton("Conectar a Archivo ETABS")
        # Boton para cargar datos
        self.btn_load_data_from_file = QPushButton("Cargar Datos desde Archivo")
        
        self.btn_exit = QPushButton("Salir del Programa")

        # Set object names for specific styling
        # self.btn_start_game.setObjectName("StdButton")
        # self.btn_connect_etabs.setObjectName("StdButton")
        self.btn_identify_columns.setObjectName("StdButton")
        self.btn_load_data_from_file.setObjectName("StdButton")
        self.btn_exit.setObjectName("ExitButton")

        # --- Layout Management ---
        self.main_layout.addWidget(self.title_label, 0, Qt.AlignTop | Qt.AlignHCenter)
        self.main_layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )

        button_layout = QVBoxLayout()
        button_layout.setSpacing(15)
        button_layout.addWidget(self.btn_identify_columns)
        button_layout.addWidget(self.btn_load_data_from_file)
        
        # button_layout.addWidget(self.btn_start_game)
        # button_layout.addWidget(self.btn_connect_etabs)
        button_layout.addWidget(self.btn_exit)

        self.main_layout.addLayout(button_layout)
        self.main_layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )

        # --- Connect Signals to Slots (Button Actions) ---
        # self.btn_start_game.clicked.connect(self.start_game)
        # self.btn_connect_etabs.clicked.connect(self.connect_to_etabs_instance)
        self.btn_identify_columns.clicked.connect(self.identificar_columnas)
        self.btn_load_data_from_file.clicked.connect(self.cargar_datos_desde_archivo)
        self.btn_exit.clicked.connect(self.exit_application)

        # --- Apply Stylesheet ---
        self.apply_styles()
        
    def cargar_datos_desde_archivo(self):
        """
        Abre un archivo JSON estructurado, extrae los datos de la tabla y las
        opciones de los ComboBox, y carga todo en la pantalla ColumnDataScreen.
        """
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Cargar Datos de Columnas", "",
                                                  "JSON Files (*.json);;All Files (*)", options=options)

        if not fileName:
            self.show_message("Carga de archivo cancelada.")
            return
        
        # Crear y mostrar el dialogo de progreso
        self.progress_dialog = QProgressDialog("Cargando datos desde archivo...", None, 0, 0, self)
        self.progress_dialog.setWindowTitle("Procesando Archivo")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.show()
        
        QApplication.processEvents()
        
        # Configurar el Thread y el Worker
        self.thread = QThread()
        self.file_worker = FileLoaderWorker(fileName)
        self.file_worker.moveToThread(self.thread)
        
        # Conectar signals y slots
        self.thread.started.connect(self.file_worker.run)
        self.file_worker.finished.connect(self.on_file_load_finished)
        self.file_worker.error.connect(self.on_file_load_error)
        
        # Conexiones para limpiar
        self.file_worker.finished.connect(self.thread.quit)
        self.file_worker.error.connect(self.thread.quit)
        self.thread.finished.connect(self.progress_dialog.close)
        self.thread.finished.connect(self.thread.deleteLater)
        self.file_worker.finished.connect(self.file_worker.deleteLater)
        self.file_worker.error.connect(self.file_worker.deleteLater)
        
        # Iniciar el proceso
        self.thread.start()

    def on_file_load_finished(self, data):
        """
            Slot que se ejecuta cuando el FileLoaderWorker termina exitosamente.
            Crea y muestra la pantalla de datos de columnas.
        """
        if self.column_data_screen:
            self.column_data_screen.close()
            
        # Extraemos los datos de los gridlines del diccionario recibido del worker
        gridlines_list = data.get("gridlines_data", [])
        table_data = data.get("table_data", [])
        sections_list = data.get("sections_list", [])
        rebars_list = data.get("rebars_list", [])
        sections_properties = data.get("sections_properties", [])
        
        # Crear y esconder InfoStoriesScreen (asumimos que no hay datos de stories en el JSON por ahora)
        if not self.info_stories_screen:
            # Puedes pasar una lista vacía o manejar esto según tu lógica
            self.info_stories_screen = InfoStoriesScreen([])
            self.info_stories_screen.hide()

        # Crear SectionDesignerScreen con los datos de las secciones del archivo
        if not self.section_designer_screen:
            self.section_designer_screen = SectionDesignerScreen(sections_data=sections_properties)
        
        # Preparar datos para ConfinementScreen a partir de las propiedades cargadas
        section_data_for_confinement = []
        for section in sections_properties:
            section_data_for_confinement.append({
                "name": section.get("section"),
                "b": section.get("b"),
                "h": section.get("h"),
                "f'c": section.get("fc"),
                "rebar_size": section.get("rebar_size"),
                "estribo": section.get("stirrup_size"),
                "pu": None, # O un valor por defecto
                "rec": section.get("cover"),
                "n_b_bc2": section.get("num_bars_2"), # Barras  de long. en dir 2
                "n_b_bc1": section.get("num_bars_3"), # Barras de long. en dir 3
                "num_est_2": section.get("num_crossties_2"),
                "num_est_3": section.get("num_crossties_3"),
            })

        # Crear y esconder ConfinementScreen
        if not self.confinement_screen:
            self.confinement_screen = ConfinementScreen(section_data_for_confinement, section_designer_window_ref=self.section_designer_screen)
            self.confinement_screen.hide()
            
        self.column_data_screen = ColumnDataScreen(
            main_menu_ref=self,
            stories_window_ref=self.info_stories_screen,
            gridlines_window_ref=None,
            section_designer_window_ref=self.section_designer_screen,
            confinement_screen_ref=self.confinement_screen,
            sap_model_object=None,
            column_data=table_data,
            rect_sections=sections_list,
            rebars=rebars_list,
            gridlines_data=gridlines_list
        )
        
        self.column_data_screen.show()
        self.hide()
        
    def on_file_load_error(self, message):
        """
            Slot que se ejecuta si el FileLoaderWorker encuentra un error.
        """
        self.progress_dialog.close() # Asegurarse de que el diálogo de progreso se cierre
        QMessageBox.critical(self, "Error de Carga", message)
    
    def apply_styles(self):
        """Applies QSS styles to the main menu using the new color palette."""
        pixmap = QPixmap(self.background_image_path)
        qss_compatible_path = self.background_image_path.replace("\\", "/")

        color_teal_base = "#00868B"
        color_teal_light = "#00AEC4"
        color_teal_dark = "#006063"

        color_red_base = "#E40E2D"
        color_red_light = "#F71F3F"
        color_red_dark = "#B80B24"

        color_blue_base = "#0147BA"
        color_text_light = "#FFFFFF"
        color_title_shadow = "#00235C"

        final_background_style = ""
        if not pixmap.isNull():
            final_background_style = f"""
                background-image: url({qss_compatible_path});
                background-repeat: no-repeat;
                background-position: center;
                background-attachment: fixed;
                background-size: cover; 
            """
        else:
            print(
                f"Warning: Background image not found at '{self.background_image_path}'. Using fallback color: {color_blue_base}."
            )
            final_background_style = f"background-color: {color_blue_base};"

        self.setStyleSheet(f"""
            QMainWindow {{
                {final_background_style}
            }}
            QWidget#MainMenuScreenCentralWidget {{
                /* background-color: transparent; */ 
            }}
            QLabel#TitleLabel {{
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 48px;
                font-weight: bold;
                color: {color_text_light}; 
                padding: 20px;
                text-shadow: 2px 2px 4px {color_title_shadow};
            }}
            QPushButton#StdButton {{
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 18px;
                font-weight: bold;
                color: {color_text_light};
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                  stop:0 {color_teal_light}, stop:1 {color_teal_base});
                border: 2px solid {color_teal_dark};
                padding: 12px 25px;
                border-radius: 8px;
                min-width: 200px;
                outline: none;
            }}
            QPushButton#StdButton:hover {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                  stop:0 {color_teal_base}, stop:1 {color_teal_light}); 
                border: 2px solid {color_teal_base};
            }}
            QPushButton#StdButton:pressed {{
                background-color: {color_teal_dark}; 
                border: 2px solid {color_teal_dark};
            }}
            QPushButton#ExitButton {{
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 18px;
                font-weight: bold;
                color: {color_text_light};
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                  stop:0 {color_red_light}, stop:1 {color_red_base});
                border: 2px solid {color_red_dark};
                padding: 12px 25px;
                border-radius: 8px;
                min-width: 200px;
                outline: none;
            }}
            QPushButton#ExitButton:hover {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                  stop:0 {color_red_base}, stop:1 {color_red_light}); 
                border: 2px solid {color_red_base};
            }}
            QPushButton#ExitButton:pressed {{
                background-color: {color_red_dark};
                border: 2px solid {color_red_dark};
            }}
        """)
        self.central_widget.setObjectName("MainMenuScreenCentralWidget")
        self.title_label.setObjectName("TitleLabel")

    def start_game(self):
        """Hides the main menu and shows the OpenFileWindow."""
        print("Action: Start New Game clicked!")
        if not self.new_game_window:  # Create window only if it doesn't exist
            self.new_game_window = OpenFileWindow(
                main_menu_ref=self
            )  # Pass self (main menu)

        self.new_game_window.show()
        self.hide()  # Hide the main menu

    def load_game(self):
        print("Action: Crear cuadro de columnas!")
        self.show_message("Cargando Cuadro de Columnas ...")  # Placeholder

    def open_options(self):
        print("Action: Options clicked!")
        self.show_message("Opening Options...")  # Placeholder

    def connect_to_etabs_instance(self):
        print("Action: Conectar con archivo de ETABS abierto clicked!")
        self.show_message("Intentando conectar con ETABS...")
        success, message, sap_model = (
            create_column_table.connect_to_active_etabs_instance()
        )
        if success and sap_model:
            self.sap_model_connected = sap_model
            self.show_message(message)

            # Get model Column data
            model_data = create_column_table.get_open_model_data(sap_model)
            column_data = model_data["cols_data"]
            rect_sections = model_data["rect_sections"]
            rebars = model_data["rebars_defined"]

            # Crear y mostrar la ColumnDataScreen
            if not self.column_data_screen:
                self.column_data_screen = ColumnDataScreen(
                    main_menu_ref=self,
                    sap_model_object=self.sap_model_connected,
                    column_data=column_data,
                    rect_sections=rect_sections,
                    rebars=rebars,
                )
            else:
                # Si ya existe, actualiza la referencia al sap_model por si acaso
                self.column_data_screen.sap_model = self.sap_model_connected
                # Aquí podrías llamar a una función en column_data_screen para refrescar datos si es necesario
                # self.column_data_screen.refresh_display_with_new_model()

            self.column_data_screen.show()
            self.hide()  # Ocultar el menú principal

            # create_column_table.get_open_model_data(sap_model)

        elif success and not sap_model:
            # ETABS conectado pero sin modelo abierto
            self.show_message(
                message
                + " Se requiere un modelo abierto para ver los datos de columnas."
            )
            self.sap_model_connected = None
        else:
            self.show_message(message)  # Muestra el mensaje de error
            self.sap_model_connected = None

    def identificar_columnas(self):
        print("Action: Identificar Columnas")
        # Deshabilitamos el botón para no iniciar el proceso dos veces
        self.btn_identify_columns.setEnabled(False)
        
        # --- Configuración del Diálogo de Progreso ---
        self.progress_dialog = QProgressDialog("Procesando, por favor espere...", None, 0, 0, self)
        self.progress_dialog.setWindowTitle("Proceso en Curso")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.show()
        
       
        
        # --- Configuración del Hilo y el Trabajador ---
        self.thread = QThread()
        self.trabajador = Worker()
        
        # Mover el trabajador al hilo
        self.trabajador.moveToThread(self.thread)
        
        # --- Conexión de Señales y Slots ---
        # 1. Cuando el hilo inicie, ejecuta el método run() del trabajador.
        self.thread.started.connect(self.trabajador.run)
        
        # 2. Cuando el trabajador termine, cierra el diálogo y el hilo.
        self.trabajador.finished.connect(self.thread.quit)
        self.trabajador.finished.connect(self.progress_dialog.close)
        
        # 3. Limpiar los objetos después de que el hilo haya terminado.
        self.trabajador.finished.connect(self.trabajador.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        
        # 4. Volver a habilitar el botón cuando el hilo termine.
        self.thread.finished.connect(lambda: self.btn_identify_columns.setEnabled(True))
        
        self.thread.finished.connect(self.on_worker_finished)
        # self.thread.finished.connect(lambda: self.etiqueta.setText("¡Proceso completado!"))
        
        # Opcional: Actualizar el texto del diálogo con el progreso
        self.trabajador.progress.connect(self.progress_dialog.setLabelText)
        
        self.trabajador.crear_ventana_signal.connect(self.pasar_info_para_ventanas)
        
        # --- Iniciar el Hilo ---
        self.thread.start()
        
    #  -- Nuevo: Slot para manejar el final del worker --
    def on_worker_finished(self):
        if not hasattr(self.trabajador, 'sap_model') or not self.trabajador.sap_model:
            QMessageBox.critical(self, "Error de Conexion", 
                                 "No se pudo conectar a una instancia de ETABS con un modelo abierto.\n",
                                 "Por favor, asegurese de que ETABS este en ejecucion y tenga un modelo cargado.")
            
        
    def pasar_info_para_ventanas(self, datos):
        sap_model = datos['sap_model']
        data_cols_labels_story = datos['data_cols_labels_story']
        sections = datos['sections']
        rect_sections = datos['rect_sections']
        rebars = datos['rebars']
        stories_with_elevations = datos['stories_with_elevations']
        gridlines_data = datos['gridlines_data']
        rectangular_sections = datos['rectangular_sections']
        
        
         # Crear y esconder InfoStoriesScreen
        if not self.info_stories_screen:
            self.info_stories_screen = InfoStoriesScreen(stories_with_elevations)
            self.info_stories_screen.hide()
            
        if not self.section_designer_screen:
            self.section_designer_screen = SectionDesignerScreen(sections_data=rectangular_sections)
            
        # Preparar datos para ConfinementScreen
        section_data_list = []
        for section in rectangular_sections:
            section_data_list.append(
                {
                    "name": section.get("section"),
                    "b": section.get("b"),
                    "h": section.get("h"),
                    "f'c": section.get("fc"),
                    "rebar_size": section.get("rebar_size"),
                    "estribo": section.get("stirrup_size"),
                    "pu": None,
                    "rec": section.get("cover"),
                    "n_b_bc2": section.get("num_bars_2"),
                    "n_b_bc1": section.get("num_bars_3"),
                }
            )
            
        # Crear y esconder ConfinementScreen
        if not self.confinement_screen:
            self.confinement_screen = ConfinementScreen(section_data_list, section_designer_window_ref=self.section_designer_screen)
            self.confinement_screen.hide()
            
            # self.info_gridlines_screen.hide()
        # Crear y mostrar ColumnDataScreen
        if not self.column_data_screen:
            self.column_data_screen = ColumnDataScreen(
                main_menu_ref=self,
                stories_window_ref= self.info_stories_screen,
                gridlines_window_ref= None, # modificacion
                section_designer_window_ref=self.section_designer_screen,
                confinement_screen_ref=self.confinement_screen,
                sap_model_object=sap_model,
                column_data=data_cols_labels_story,
                rect_sections=sections,
                rebars=rebars,
            )
            # self.info_gridlines_screen.datos_para_renombrar.connect(self.column_data_screen.realizar_renombrado)
        else:
            # Si ya existe, actualiza la referencia al sap_model por si acaso
            self.column_data_screen.sap_model = self.sap_model_connected
            # Aquí podrías llamar a una función en column_data_screen para refrescar datos si es necesario
            # self.column_data_screen.refresh_display_with_new_model()

        self.column_data_screen.show()
        self.hide()  # Ocultar el menú principal

    def exit_application(self):
        print("Action: Salir del Programa clicked!")
        # Before quitting, ensure child windows are also closed if necessary
        if self.new_game_window and self.new_game_window.isVisible():
            self.new_game_window.close()
        QApplication.instance().quit()

    def show_message(self, message):
        """Helper to show a temporary message label (used for Load Game/Options)."""
        existing_labels = self.central_widget.findChildren(QLabel, "temp_message_label")
        for label in existing_labels:
            label.deleteLater()

        msg_label = QLabel(message, self.central_widget)
        msg_label.setObjectName("temp_message_label")
        msg_label.setAlignment(Qt.AlignCenter)

        defined_color_text_light = getattr(self, "color_text_light", "#FFFFFF")

        msg_label.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(0, 0, 0, 0.75);
                color: {defined_color_text_light}; 
                font-size: 16px;
                padding: 10px 15px;
                border-radius: 5px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
        """)

        msg_label.adjustSize()
        msg_label.move(
            int((self.central_widget.width() - msg_label.width()) / 2),
            int(self.central_widget.height() - msg_label.height() - 20),
        )
        msg_label.show()
        msg_label.raise_()
        # from PyQt5.QtCore import QTimer # Uncomment for auto-hide
        # QTimer.singleShot(3000, msg_label.deleteLater) # Uncomment for auto-hide

    # Sobrescribir closeEvent para cerrar también ColumnDataScreen si está abierta
    def closeEvent(self, event):
        if self.new_game_window:
            self.new_game_window.close()
        if self.column_data_screen:  # Añadido
            self.column_data_screen.close()
        super().closeEvent(event)
