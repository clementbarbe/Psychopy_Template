from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QLabel, 
                             QSpinBox, QDoubleSpinBox, QPushButton)
from PyQt6.QtCore import Qt

class NBackTab(QWidget):
    def __init__(self, parent_menu):
        super().__init__()
        self.parent_menu = parent_menu
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        params_group = QGroupBox("Paramètres NBack")
        params_layout = QVBoxLayout()
        
        # Niveau N
        n_layout = QVBoxLayout()
        n_layout.addWidget(QLabel("Niveau N:"))
        self.spin_n = QSpinBox()
        self.spin_n.setRange(1, 4)
        self.spin_n.setValue(2)
        n_layout.addWidget(self.spin_n)
        
        # Essais
        trials_layout = QVBoxLayout()
        trials_layout.addWidget(QLabel("Nombre d'essais:"))
        self.spin_trials = QSpinBox()
        self.spin_trials.setRange(1, 100)
        self.spin_trials.setValue(10)
        trials_layout.addWidget(self.spin_trials)
        
        # Durées
        dur_layout = QVBoxLayout()
        dur_layout.addWidget(QLabel("ISI (s):"))
        self.spin_isi = QDoubleSpinBox()
        self.spin_isi.setSingleStep(0.1)
        self.spin_isi.setValue(0.5)
        
        dur_layout.addWidget(QLabel("Durée stimulus (s):"))
        self.spin_dur = QDoubleSpinBox()
        self.spin_dur.setSingleStep(0.01)
        self.spin_dur.setValue(1.5)
        
        dur_layout.addWidget(self.spin_isi)
        dur_layout.addWidget(self.spin_dur)
        
        params_layout.addLayout(n_layout)
        params_layout.addLayout(trials_layout)
        params_layout.addLayout(dur_layout)
        params_group.setLayout(params_layout)
        
        btn_run = QPushButton("Lancer NBack")
        btn_run.clicked.connect(self.run_task)
        
        layout.addWidget(params_group)
        layout.addStretch()
        layout.addWidget(btn_run, alignment=Qt.AlignmentFlag.AlignRight)

    def run_task(self):
        params = {
            'tache': 'NBack',
            'N': self.spin_n.value(),
            'n_trials': self.spin_trials.value(),
            'isi': self.spin_isi.value(),
            'stim_dur': self.spin_dur.value()
        }
        self.parent_menu.run_experiment(params)