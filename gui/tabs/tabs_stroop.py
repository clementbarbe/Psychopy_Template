from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
                             QSpinBox, QPushButton, QCheckBox)
from PyQt6.QtCore import Qt

class StroopTab(QWidget):
    def __init__(self, parent_menu):
        super().__init__()
        self.parent_menu = parent_menu
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # --- GROUPE PARAMÈTRES ---
        params_group = QGroupBox("Paramètres Stroop")
        params_layout = QVBoxLayout()

        # 1. Nombre d'essais (Horizontal + Stretch)
        trials_layout = QHBoxLayout()
        trials_layout.addWidget(QLabel("Nombre d'essais :"))
        self.spin_trials = QSpinBox()
        self.spin_trials.setRange(1, 500)
        self.spin_trials.setValue(30)
        trials_layout.addWidget(self.spin_trials)
        trials_layout.addStretch() # Compacte à gauche
        params_layout.addLayout(trials_layout)

        # 2. Nombre de choix (Horizontal + Stretch)
        choices_layout = QHBoxLayout()
        choices_layout.addWidget(QLabel("Nombre de choix :"))
        self.spin_choices = QSpinBox()
        self.spin_choices.setRange(2, 4)
        self.spin_choices.setValue(3)
        choices_layout.addWidget(self.spin_choices)
        choices_layout.addStretch() # Compacte à gauche
        params_layout.addLayout(choices_layout)

        # 3. Option Go / No-Go (Horizontal + Stretch)
        # On le met aussi dans un HBox pour éviter que la zone cliquable ne prenne toute la largeur
        gonogo_layout = QHBoxLayout()
        self.chk_gonogo = QCheckBox("Activer le mode Go / No-Go")
        self.chk_gonogo.setChecked(False)
        gonogo_layout.addWidget(self.chk_gonogo)
        gonogo_layout.addStretch() # Compacte à gauche
        params_layout.addLayout(gonogo_layout)
        
        # 4. Bouton Lancer (Directement dans le vertical, sous les options)
        btn_run = QPushButton("Lancer Stroop")
        btn_run.clicked.connect(self.run_task)
        params_layout.addWidget(btn_run)
        
        params_group.setLayout(params_layout)
        
        # Ajout du groupe au layout principal et Stretch final pour tout pousser vers le haut
        layout.addWidget(params_group)
        layout.addStretch()

    def run_task(self):
        params = {
            'tache': 'Stroop',
            'n_trials': self.spin_trials.value(),
            'n_choices': self.spin_choices.value(),
            'go_nogo': self.chk_gonogo.isChecked()
        }
        self.parent_menu.run_experiment(params)