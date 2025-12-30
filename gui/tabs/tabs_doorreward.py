from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
                             QSpinBox, QDoubleSpinBox, QPushButton)
from PyQt6.QtCore import Qt

class DoorRewardTab(QWidget):
    def __init__(self, parent_menu):
        super().__init__()
        self.parent_menu = parent_menu
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        params_group = QGroupBox("Paramètres Tâche Portes (Reward)")
        params_layout = QVBoxLayout()
        
        trials_layout = QHBoxLayout()
        trials_layout.addWidget(QLabel("Nombre d'essais :"))
        self.spin_trials = QSpinBox()
        self.spin_trials.setRange(1, 200)
        self.spin_trials.setValue(50)
        trials_layout.addWidget(self.spin_trials)
        
        prob_layout = QHBoxLayout()
        prob_layout.addWidget(QLabel("Probabilité de gain (0.0 - 1.0) :"))
        self.spin_prob = QDoubleSpinBox()
        self.spin_prob.setRange(0.0, 1.0)
        self.spin_prob.setSingleStep(0.1)
        self.spin_prob.setValue(0.6)
        prob_layout.addWidget(self.spin_prob)

        isi_layout = QHBoxLayout()
        isi_layout.addWidget(QLabel("ISI Moyen (s) :"))
        self.spin_isi = QDoubleSpinBox()
        self.spin_isi.setRange(0.1, 10.0)
        self.spin_isi.setValue(2.0)
        isi_layout.addWidget(self.spin_isi)
        
        params_layout.addLayout(trials_layout)
        params_layout.addLayout(prob_layout)
        params_layout.addLayout(isi_layout)
        params_group.setLayout(params_layout)

        btn_run = QPushButton("Lancer Tâche Portes")
        btn_run.clicked.connect(self.run_task)
        
        layout.addWidget(params_group)
        layout.addStretch()
        layout.addWidget(btn_run, alignment=Qt.AlignmentFlag.AlignRight)

    def run_task(self):
        params = {
            'tache': 'DoorReward',
            'n_trials': self.spin_trials.value(),
            'reward_prob': self.spin_prob.value(),
            'isi': self.spin_isi.value()
        }
        self.parent_menu.run_experiment(params)