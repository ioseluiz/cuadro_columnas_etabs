from PyQt5.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout,QTableWidget, QTableWidgetItem,
    QScrollArea, QFrame,QLabel
)


class InfoStoriesScreen(QWidget):
    def __init__(self, stories ,parent=None):
        super().__init__(parent)
        self.setWindowTitle("Stories Data")
        self.resize(500, 350)
         
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10,10,10,10)
        self.main_layout.setSpacing(10)
        
        self.title_label = QLabel("Stories Info")
        self.main_layout.addWidget(self.title_label)
        

        self.table_stories_info = QTableWidget(len(stories),2) # Modify with len of stories list
        self.table_stories_info.setHorizontalHeaderLabels(["Name", "Elevation"])
        
        # Configure QTable
        
        for story_idx, story in enumerate(stories):
            # Col 0: Story Name
            item_name = QTableWidgetItem(story['nombre'])
            self.table_stories_info.setItem(story_idx, 0, item_name)
            
            # Col 1: Elevation
            item_elevation = QTableWidgetItem(str(story['elevacion']))
            self.table_stories_info.setItem(story_idx, 1, item_elevation)
            
        self.table_stories_info.resizeColumnsToContents()
            
        
        self.main_layout.addWidget(self.table_stories_info)
            
        # Para hacer scrollable el contenido principal si excede el tamaño
        # scroll_content_widget = QWidget()
        # scroll_content_widget.setLayout(self.tabs_layout)
        # scroll_area = QScrollArea()
        # scroll_area.setWidgetResizable(True)
        # scroll_area.setWidget(scroll_content_widget)
        # scroll_area.setFrameShape(QFrame.NoFrame) # Sin borde para el área de scroll
        
        