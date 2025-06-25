import sys
from PyQt5.QtWidgets import (
    QApplication,
    
)
from PyQt5.QtGui import QFont, QPixmap 
from PyQt5.QtCore import Qt, QSize, QT_VERSION_STR, PYQT_VERSION_STR

from core import create_column_table

# Import Screens
from screens.main_menu import MainMenuScreen

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    print(f"Using Qt Version: {QT_VERSION_STR}")
    print(f"Using PyQt Version: {PYQT_VERSION_STR}")

    main_menu = MainMenuScreen()
    main_menu.show()
    sys.exit(app.exec_())
