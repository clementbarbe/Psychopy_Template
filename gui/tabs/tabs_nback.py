from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                             QLabel, QSpinBox, QPushButton, QCheckBox)

class NBackTab(QWidget):
    def __init__(self, parent_menu):
        super().__init__()
        self.parent_menu = parent_menu
        self.init_ui()

    def init_ui(self):
        # Layout principal de l'onglet
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # --- GROUPE PARAMÈTRES ---
        params_group = QGroupBox("Paramètres NBack")
        params_layout = QVBoxLayout()
        
        # 1. Ligne Niveau N (Horizontal)
        n_layout = QHBoxLayout()
        n_layout.addWidget(QLabel("Niveau N :"))
        self.spin_n = QSpinBox()
        self.spin_n.setRange(1, 4)
        self.spin_n.setValue(2)
        n_layout.addWidget(self.spin_n)
        n_layout.addStretch() # C'est ceci qui empêche l'étirement sur toute la largeur
        params_layout.addLayout(n_layout)
        
        # 2. Ligne Essais (Horizontal)
        trials_layout = QHBoxLayout()
        trials_layout.addWidget(QLabel("Nombre d'essais :"))
        self.spin_trials = QSpinBox()
        self.spin_trials.setRange(1, 100)
        self.spin_trials.setValue(10)
        trials_layout.addWidget(self.spin_trials)
        trials_layout.addStretch() # Pousse vers la gauche
        params_layout.addLayout(trials_layout)

        # 4. Option Increment 
        increm_layout = QHBoxLayout()
        self.chk_increm = QCheckBox("Activer le mode incrémental")
        self.chk_increm.setChecked(False)
        increm_layout.addWidget(self.chk_increm)
        increm_layout.addStretch() # Compacte à gauche
        params_layout.addLayout(increm_layout)
        
        # Finalisation du groupe
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
        # 3. Bouton Lancer (Directement dans le vertical, sous les HBox)
        btn_run = QPushButton("Lancer NBack")
        btn_run.clicked.connect(self.run_task)
        params_layout.addWidget(btn_run)

        
        
        # Stretch final pour coller le tout en haut de la fenêtre
        layout.addStretch()

    def run_task(self):
        params = {
            'tache': 'NBack',
            'N': self.spin_n.value(),
            'n_trials': self.spin_trials.value(),
            'increm': self.chk_increm.isChecked()
        }
        self.parent_menu.run_experiment(params)