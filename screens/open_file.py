import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSpacerItem, QSizePolicy, QFileDialog,
    QTableWidget, QTableWidgetItem, QScrollArea, QFrame
    
)
from PyQt5.QtGui import QFont, QPixmap 
from PyQt5.QtCore import Qt, QSize, QT_VERSION_STR, PYQT_VERSION_STR

from core import create_column_table

class OpenFileWindow(QWidget):
    """
    A new window that appears when 'Start New Game' is clicked.
    It contains a button to open a QFileDialog for .edb files,
    a button to process the file, and a button to go back to the main menu.
    """
    def __init__(self, main_menu_ref, parent=None): # Added main_menu_ref
        super().__init__(parent)
        self.main_menu_ref = main_menu_ref # Store reference to main menu
        self.selected_file_path = None # To store the path of the selected .edb file

        self.setWindowTitle("Extraccion de Datos ETABS")
        self.setMinimumSize(450, 250) # Adjusted minimum size
        self.setGeometry(200, 200, 450, 250) # x, y, width, height

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)

        self.info_label = QLabel("Seleccione una opcion.", self)
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setWordWrap(True)

        self.btn_select_file = QPushButton("Select .edb File", self)
        self.btn_select_file.clicked.connect(self.open_file_dialog)
        
        # Style the select file button
        self.btn_select_file.setStyleSheet(f"""
            QPushButton {{
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 16px;
                font-weight: bold;
                color: #FFFFFF;
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                  stop:0 #00AEC4, stop:1 #00868B); /* Teal */
                border: 2px solid #006063;
                padding: 10px 20px;
                border-radius: 6px;
                min-width: 150px;
                outline: none;
            }}
            QPushButton:hover {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                  stop:0 #00868B, stop:1 #00AEC4);
                border: 2px solid #00868B;
            }}
            QPushButton:pressed {{
                background-color: #006063;
                border: 2px solid #006063;
            }}
        """)

        self.selected_file_label = QLabel("No selecciono ningun archivo.", self)
        self.selected_file_label.setAlignment(Qt.AlignCenter)
        self.selected_file_label.setStyleSheet("font-style: italic; color: #7f8c8d;")

        # --- New Buttons ---
        self.btn_process_file = QPushButton("Aceptar", self)
        self.btn_process_file.clicked.connect(self.process_selected_file)
        self.btn_process_file.setEnabled(False) # Initially disabled

        self.btn_back_to_menu = QPushButton("Volver al Menu Principal", self)
        self.btn_back_to_menu.clicked.connect(self.go_back_to_main_menu)

        # Styling for new buttons
        button_style_sheet_process = f"""
            QPushButton {{
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                font-weight: bold;
                color: #FFFFFF;
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                  stop:0 #00AEC4, stop:1 #00868B); /* Teal for process */
                border: 2px solid #006063;
                padding: 8px 15px;
                border-radius: 6px;
                outline: none;
            }}
            QPushButton:hover {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                  stop:0 #00868B, stop:1 #00AEC4);
                border: 2px solid #00868B;
            }}
            QPushButton:pressed {{
                background-color: #006063;
            }}
            QPushButton:disabled {{
                background-color: #bdc3c7;
                border-color: #7f8c8d;
                color: #7f8c8d;
            }}
        """
        button_style_sheet_back = f"""
            QPushButton {{
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                color: #2c3e50; /* Dark text for back button */
                background-color: #ecf0f1; /* Light gray */
                border: 1px solid #bdc3c7; /* Subtler border */
                padding: 8px 15px;
                border-radius: 6px;
                outline: none;
            }}
            QPushButton:hover {{
                background-color: #d5d9db;
                border-color: #95a5a6;
            }}
            QPushButton:pressed {{
                background-color: #bdc3c7;
            }}
        """
        self.btn_process_file.setStyleSheet(button_style_sheet_process)
        self.btn_back_to_menu.setStyleSheet(button_style_sheet_back)

        # Layout for the bottom buttons
        bottom_button_layout = QHBoxLayout()
        bottom_button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        bottom_button_layout.addWidget(self.btn_back_to_menu)
        bottom_button_layout.addWidget(self.btn_process_file)
        bottom_button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))


        self.layout.addWidget(self.info_label)
        self.layout.addWidget(self.btn_select_file, 0, Qt.AlignHCenter)
        self.layout.addWidget(self.selected_file_label)
        self.layout.addStretch(1) # Add stretchable space
        self.layout.addLayout(bottom_button_layout) # Add the new button layout

        # Fallback background color if no specific styling is inherited
        self.setStyleSheet("QWidget { background-color: #f0f3f4; } " + self.styleSheet()) # Ensure QWidget is targeted

    def open_file_dialog(self):
        """
        Opens a QFileDialog to select files with the .edb extension.
        """
        options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog # Uncomment if native dialog causes issues
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Archivo EDB",  # Dialog Title
            "",                 # Default directory (empty means current or last used)
            "EDB Files (*.edb);;All Files (*)",  # File filter
            options=options
        )

        if file_name:
            print(f"Selected file: {file_name}")
            self.selected_file_path = file_name # Store the full path
            self.selected_file_label.setText(f"Selected: {file_name.split('/')[-1]}")
            self.selected_file_label.setStyleSheet("color: #2c3e50; font-weight: bold;") # Darker text for selected file
            self.btn_process_file.setEnabled(True) # Enable process button
        else:
            print("File selection cancelled.")
            self.selected_file_path = None # Reset path
            self.selected_file_label.setText("File selection cancelled.")
            self.selected_file_label.setStyleSheet("font-style: italic; color: #c0392b;") # Reddish for cancelled
            self.btn_process_file.setEnabled(False) # Disable process button

    def process_selected_file(self):
        """
        Placeholder function to process the selected .edb file.
        This function will be implemented later.
        """
        if self.selected_file_path:
            print(f"Processing file: {self.selected_file_path}")
            # TODO: Implement file processing logic here
            self.info_label.setText(f"Processing: {self.selected_file_path.split('/')[-1]}...")
            # For now, just show a message
            # Call function to open etabs and extract the column data
            create_column_table.get_model_data(self.selected_file_path)
            
            
        else:
            print("No file selected to process.")
            self.info_label.setText("No file selected. Please select an .edb file first.")

    def go_back_to_main_menu(self):
        """Hides this window and shows the main menu."""
        self.hide()
        if self.main_menu_ref:
            self.main_menu_ref.show()

    def closeEvent(self, event):
        """Handle the case where this window is closed directly."""
        if self.main_menu_ref:
            # Option 1: Show main menu if this window is closed (unless app is exiting)
            # self.main_menu_ref.show()
            # Option 2: Or, if this window closing means exiting this part of the flow,
            # the main menu's visibility is handled by its own logic or app exit.
            # For now, we assume closing this window means returning to the main menu's control.
            # If the main menu is not visible and this is closed, it might be good to show it.
            if not self.main_menu_ref.isVisible():
                 self.main_menu_ref.show() # Show main menu if it was hidden
        super().closeEvent(event)

