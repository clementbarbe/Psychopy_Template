from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
                             QSpinBox, QDoubleSpinBox, QPushButton)
from PyQt6.QtCore import Qt

class StroopTab(QWidget):
    def __init__(self, parent_menu):
        super().__init__()
        self.parent_menu = parent_menu
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        params_group = QGroupBox("Paramètres Stroop")
        params_layout = QVBoxLayout()
        
        trials_layout = QHBoxLayout()
        trials_layout.addWidget(QLabel("Nombre d'essais :"))
        self.spin_trials = QSpinBox()
        self.spin_trials.setRange(1, 500)
        self.spin_trials.setValue(30)
        trials_layout.addWidget(self.spin_trials)
        
        dur_layout = QHBoxLayout()
        dur_layout.addWidget(QLabel("Durée stimulus (s) :"))
        self.spin_dur = QDoubleSpinBox()
        self.spin_dur.setRange(0.1, 5.0)
        self.spin_dur.setValue(1.5)
        dur_layout.addWidget(self.spin_dur)

        dur_layout.addWidget(QLabel("ISI (s) :"))
        self.spin_isi = QDoubleSpinBox()
        self.spin_isi.setRange(0.1, 5.0)
        self.spin_isi.setValue(1.0)
        dur_layout.addWidget(self.spin_isi)
        
        params_layout.addLayout(trials_layout)
        params_layout.addLayout(dur_layout)
        params_group.setLayout(params_layout)
        
        btn_run = QPushButton("Lancer Stroop")
        btn_run.clicked.connect(self.run_task)
        
        layout.addWidget(params_group)
        layout.addStretch()
        layout.addWidget(btn_run, alignment=Qt.AlignmentFlag.AlignRight)

    def run_task(self):
        params = {
            'tache': 'Stroop',
            'n_trials': self.spin_trials.value(),
            'stim_dur': self.spin_dur.value(),
            'isi': self.spin_isi.value()
        }
        self.parent_menu.run_experiment(params)