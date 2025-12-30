from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QLabel, 
                             QDoubleSpinBox, QPushButton)
from PyQt6.QtCore import Qt

class VisualMemoryTab(QWidget):
    def __init__(self, parent_menu):
        super().__init__()
        self.parent_menu = parent_menu
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        params_group = QGroupBox("Paramètres Visual Memory")
        params_layout = QVBoxLayout()
        
        dur_layout = QVBoxLayout()
        dur_layout.addWidget(QLabel("Durée stimulus (s):"))
        self.spin_dur = QDoubleSpinBox()
        self.spin_dur.setValue(1.0)
        dur_layout.addWidget(QLabel("ISI (s):"))
        self.spin_isi = QDoubleSpinBox()
        self.spin_isi.setValue(0.5)
        
        dur_layout.addWidget(self.spin_dur)
        dur_layout.addWidget(self.spin_isi)
        params_layout.addLayout(dur_layout)
        params_group.setLayout(params_layout)
        
        btn_run = QPushButton("Lancer Visual Memory")
        btn_run.clicked.connect(self.run_task)
        
        layout.addWidget(params_group)
        layout.addStretch()
        layout.addWidget(btn_run, alignment=Qt.AlignmentFlag.AlignRight)

    def run_task(self):
        params = {
            'tache': 'VisualMemory',
            'stim_dur': self.spin_dur.value(),
            'isi': self.spin_isi.value()
        }
        self.parent_menu.run_experiment(params)