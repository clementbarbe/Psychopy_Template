from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
                             QSpinBox, QPushButton, QLineEdit, QCheckBox) # <--- Ajout de QCheckBox
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
        
        # --- 1. Session ---
        sess_layout = QHBoxLayout()
        sess_layout.addWidget(QLabel("Session :"))
        self.txt_session = QLineEdit("01")
        sess_layout.addWidget(self.txt_session)
        params_layout.addLayout(sess_layout)

        # --- 2. Nombre d'essais ---
        trials_layout = QHBoxLayout()
        trials_layout.addWidget(QLabel("Nombre d'essais :"))
        self.spin_trials = QSpinBox()
        self.spin_trials.setRange(1, 500)
        self.spin_trials.setValue(30)
        trials_layout.addWidget(self.spin_trials)
        params_layout.addLayout(trials_layout)

        # --- 3. Nombre de choix ---
        choices_layout = QHBoxLayout()
        choices_layout.addWidget(QLabel("Nombre de choix :"))
        self.spin_choices = QSpinBox()
        self.spin_choices.setRange(2, 4)
        self.spin_choices.setValue(3)
        choices_layout.addWidget(self.spin_choices)
        params_layout.addLayout(choices_layout)

        # --- 4. Option Go / No-Go (NOUVEAU) ---
        # J'utilise une checkbox simple. Si cochée = True.
        self.chk_gonogo = QCheckBox("Activer le mode Go / No-Go")
        self.chk_gonogo.setChecked(False) # Par défaut désactivé
        params_layout.addWidget(self.chk_gonogo)
        
        params_group.setLayout(params_layout)
        
        btn_run = QPushButton("Lancer Stroop")
        btn_run.clicked.connect(self.run_task)
        
        layout.addWidget(params_group)
        layout.addStretch()
        layout.addWidget(btn_run, alignment=Qt.AlignmentFlag.AlignRight)

    def run_task(self):
        # On ajoute le paramètre go_nogo ici
        params = {
            'tache': 'Stroop',
            'session': self.txt_session.text(),
            'n_trials': self.spin_trials.value(),
            'n_choices': self.spin_choices.value(),
            'go_nogo': self.chk_gonogo.isChecked() # <--- Récupère True ou False
        }
        self.parent_menu.run_experiment(params)