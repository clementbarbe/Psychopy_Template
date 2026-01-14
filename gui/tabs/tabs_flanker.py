from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                             QLabel, QSpinBox, QPushButton)
from PyQt6.QtCore import Qt

class FlankerTab(QWidget):
    def __init__(self, parent_menu):
        super().__init__()
        self.parent_menu = parent_menu
        self.init_ui()

    def init_ui(self):
        # Layout principal de l'onglet
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # --- GROUPE PARAMÈTRES ---
        params_group = QGroupBox("Paramètres Flanker")
        params_layout = QVBoxLayout()
        
        # Ligne Nombre d'essais (Horizontal)
        trials_layout = QHBoxLayout()
        trials_layout.addWidget(QLabel("Nombre d'essais :"))
        self.spin_trials = QSpinBox()
        self.spin_trials.setRange(1, 100)
        self.spin_trials.setValue(20)
        
        trials_layout.addWidget(self.spin_trials)
        trials_layout.addStretch() # Pousse le spinbox vers la gauche
        
        params_layout.addLayout(trials_layout)
        
        # Bouton Lancer (Placé juste en dessous dans le layout vertical du groupe)
        btn_run = QPushButton("Lancer Flanker")
        btn_run.clicked.connect(self.run_task)
        params_layout.addWidget(btn_run)
        
        params_group.setLayout(params_layout)
        
        # Ajout du groupe au layout principal
        layout.addWidget(params_group)
        
        # Stretch pour caler le groupe en haut de l'onglet
        layout.addStretch()

    def run_task(self):
        params = {
            'tache': 'Flanker',
            'n_trials': self.spin_trials.value(),
        }
        self.parent_menu.run_experiment(params)