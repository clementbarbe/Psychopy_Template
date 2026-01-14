from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
                             QSpinBox, QDoubleSpinBox, QPushButton)
from PyQt6.QtCore import Qt

class DoorRewardTab(QWidget):
    def __init__(self, parent_menu):
        super().__init__()
        self.parent_menu = parent_menu
        self.init_ui()

    def init_ui(self):
        # Layout principal de l'onglet
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # --- GROUPE PARAMÈTRES ---
        params_group = QGroupBox("Paramètres Tâche DoorReward")
        params_layout = QVBoxLayout()
        
        # 1. Nombre d'essais
        trials_layout = QHBoxLayout()
        trials_layout.addWidget(QLabel("Nombre d'essais :"))
        self.spin_trials = QSpinBox()
        self.spin_trials.setRange(1, 200)
        self.spin_trials.setValue(50)
        trials_layout.addWidget(self.spin_trials)
        trials_layout.addStretch() # Pousse vers la gauche
        params_layout.addLayout(trials_layout)
        
        # 2. Probabilité de gain
        prob_layout = QHBoxLayout()
        prob_layout.addWidget(QLabel("Probabilité de gain (0.0 - 1.0) :"))
        self.spin_prob = QDoubleSpinBox()
        self.spin_prob.setRange(0.0, 1.0)
        self.spin_prob.setSingleStep(0.1)
        self.spin_prob.setValue(0.6)
        prob_layout.addWidget(self.spin_prob)
        prob_layout.addStretch() # Pousse vers la gauche
        params_layout.addLayout(prob_layout)

        # 3. Bouton Lancer (Placé dans le layout vertical du groupe)
        btn_run = QPushButton("Lancer DoorReward")
        btn_run.clicked.connect(self.run_task)
        params_layout.addWidget(btn_run)

        params_group.setLayout(params_layout)
        
        # Ajout du groupe au layout principal
        layout.addWidget(params_group)
        
        # Stretch final pour caler le tout en haut
        layout.addStretch()

    def run_task(self):
        params = {
            'tache': 'DoorReward',
            'n_trials': self.spin_trials.value(),
            'reward_prob': self.spin_prob.value(),

        }
        self.parent_menu.run_experiment(params)