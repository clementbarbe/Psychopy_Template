from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QTabWidget, QLineEdit, QCheckBox, QPushButton, QLabel,
                            QSpinBox, QDoubleSpinBox, QGroupBox)
from PyQt6.QtCore import Qt
from utils.utils import is_valid_name
import sys


class ExperimentMenu(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Configuration Expérimentale")
        self.setFixedSize(800, 600)
        
        self.config = {
            'nom': '',
            'enregistrer': True,
            'window_size': (1500, 1500),
            'fullscr': False
        }
        
        self.initUI()
        
    def initUI(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        
        # Partie supérieure - Configuration générale (toujours visible)
        self.create_general_section(main_layout)
        
        # Partie centrale - Onglets des tâches avec boutons Run
        self.create_task_tabs(main_layout)
        
    def create_general_section(self, parent_layout):
        group = QGroupBox("Configuration Générale")
        layout = QHBoxLayout()
        
        # Nom participant
        lbl_name = QLabel("Nom du participant:")
        self.txt_name = QLineEdit()
        self.txt_name.setFixedWidth(200)
        
        # Options générales
        self.chk_save = QCheckBox("Enregistrer les données")
        self.chk_save.setChecked(True)
        
        layout.addWidget(lbl_name)
        layout.addWidget(self.txt_name)
        layout.addWidget(self.chk_save)
        layout.addStretch()
        
        group.setLayout(layout)
        parent_layout.addWidget(group)
    
    def create_task_tabs(self, parent_layout):
        """Crée les onglets avec leurs propres boutons Run"""
        self.tabs = QTabWidget()
        
        # Onglet NBack
        self.nback_tab = QWidget()
        self.init_nback_tab()
        self.tabs.addTab(self.nback_tab, "NBack")
        
        # Onglet DigitSpan
        self.digit_tab = QWidget()
        self.init_digitspan_tab()
        self.tabs.addTab(self.digit_tab, "DigitSpan")
        
        # Onglet Flanker
        self.flanker_tab = QWidget()
        self.init_flanker_tab()
        self.tabs.addTab(self.flanker_tab, "Flanker")
        
        parent_layout.addWidget(self.tabs)
    
    def init_nback_tab(self):
        layout = QVBoxLayout()
        self.nback_tab.setLayout(layout)

        params_group = QGroupBox("Paramètres NBack")
        params_layout = QVBoxLayout()

        # Niveau N
        n_layout = QVBoxLayout()
        lbl_n = QLabel("Niveau N:")
        self.spin_n = QSpinBox()
        self.spin_n.setRange(1, 4)
        self.spin_n.setValue(2)
        n_layout.addWidget(lbl_n)
        n_layout.addWidget(self.spin_n)

        # Nombre essais
        trials_layout = QVBoxLayout()
        lbl_trials = QLabel("Nombre d'essais:")
        self.spin_nback_trials = QSpinBox()
        self.spin_nback_trials.setRange(1, 100)
        self.spin_nback_trials.setValue(15)
        trials_layout.addWidget(lbl_trials)
        trials_layout.addWidget(self.spin_nback_trials)

        # Durées
        dur_layout = QVBoxLayout()
        lbl_isi = QLabel("ISI (s):")
        self.spin_nback_isi = QDoubleSpinBox()
        self.spin_nback_isi.setSingleStep(0.1)
        self.spin_nback_isi.setValue(2.0)

        lbl_dur = QLabel("Durée stimulus (s):")
        self.spin_nback_dur = QDoubleSpinBox()
        self.spin_nback_dur.setSingleStep(0.01)
        self.spin_nback_dur.setValue(0.76)

        dur_layout.addWidget(lbl_isi)
        dur_layout.addWidget(self.spin_nback_isi)
        dur_layout.addWidget(lbl_dur)
        dur_layout.addWidget(self.spin_nback_dur)

        params_layout.addLayout(n_layout)
        params_layout.addLayout(trials_layout)
        params_layout.addLayout(dur_layout)
        params_group.setLayout(params_layout)

        btn_run = QPushButton("Lancer NBack")
        btn_run.clicked.connect(self.run_nback)

        layout.addWidget(params_group)
        layout.addStretch()
        layout.addWidget(btn_run, alignment=Qt.AlignmentFlag.AlignRight)

    
    def init_digitspan_tab(self):
        # Utilisez un QVBoxLayout principal pour l'onglet
        layout = QVBoxLayout()
        self.digit_tab.setLayout(layout)

        # Paramètres DigitSpan
        params_group = QGroupBox("Paramètres DigitSpan")
        params_layout = QVBoxLayout()  # Layout vertical pour les paramètres

        # Longueur empan
        span_layout = QVBoxLayout()  # Utilisez QVBoxLayout pour chaque sous-section
        lbl_span = QLabel("Longueur empan:")
        self.spin_span = QSpinBox()
        self.spin_span.setRange(1, 10)
        self.spin_span.setValue(5)
        span_layout.addWidget(lbl_span)
        span_layout.addWidget(self.spin_span)

        # Nombre essais
        trials_layout = QVBoxLayout()  # Utilisez QVBoxLayout pour chaque sous-section
        lbl_trials = QLabel("Nombre d'essais:")
        self.spin_digit_trials = QSpinBox()
        self.spin_digit_trials.setRange(1, 20)
        self.spin_digit_trials.setValue(3)
        trials_layout.addWidget(lbl_trials)
        trials_layout.addWidget(self.spin_digit_trials)

        # Durées
        dur_layout = QVBoxLayout()  # Utilisez QVBoxLayout pour chaque sous-section
        lbl_digit_dur = QLabel("Durée chiffre (s):")
        self.spin_digit_dur = QDoubleSpinBox()
        self.spin_digit_dur.setValue(0.8)

        lbl_digit_isi = QLabel("ISI (s):")
        self.spin_digit_isi = QDoubleSpinBox()
        self.spin_digit_isi.setValue(0.5)

        dur_layout.addWidget(lbl_digit_dur)
        dur_layout.addWidget(self.spin_digit_dur)
        dur_layout.addWidget(lbl_digit_isi)
        dur_layout.addWidget(self.spin_digit_isi)

        # Ajoutez les sous-layouts au layout principal des paramètres
        params_layout.addLayout(span_layout)
        params_layout.addLayout(trials_layout)
        params_layout.addLayout(dur_layout)
        params_group.setLayout(params_layout)

        # Bouton Run pour DigitSpan
        btn_run = QPushButton("Lancer DigitSpan")
        btn_run.clicked.connect(self.run_digitspan)

        # Ajoutez les widgets au layout principal de l'onglet
        layout.addWidget(params_group)
        layout.addStretch()
        layout.addWidget(btn_run, alignment=Qt.AlignmentFlag.AlignRight)
    
    def init_flanker_tab(self):
        layout = QVBoxLayout()
        self.flanker_tab.setLayout(layout)

        params_group = QGroupBox("Paramètres Flanker")
        params_layout = QVBoxLayout()

        # Nombre essais
        trials_layout = QVBoxLayout()
        lbl_trials = QLabel("Nombre d'essais:")
        self.spin_flanker_trials = QSpinBox()
        self.spin_flanker_trials.setRange(1, 100)
        self.spin_flanker_trials.setValue(20)
        trials_layout.addWidget(lbl_trials)
        trials_layout.addWidget(self.spin_flanker_trials)

        # Durées
        dur_layout = QVBoxLayout()
        lbl_flanker_dur = QLabel("Durée stimulus (s):")
        self.spin_flanker_dur = QDoubleSpinBox()
        self.spin_flanker_dur.setValue(1.0)

        lbl_flanker_isi = QLabel("ISI (s):")
        self.spin_flanker_isi = QDoubleSpinBox()
        self.spin_flanker_isi.setValue(1.0)

        dur_layout.addWidget(lbl_flanker_dur)
        dur_layout.addWidget(self.spin_flanker_dur)
        dur_layout.addWidget(lbl_flanker_isi)
        dur_layout.addWidget(self.spin_flanker_isi)

        params_layout.addLayout(trials_layout)
        params_layout.addLayout(dur_layout)
        params_group.setLayout(params_layout)

        btn_run = QPushButton("Lancer Flanker")
        btn_run.clicked.connect(self.run_flanker)

        layout.addWidget(params_group)
        layout.addStretch()
        layout.addWidget(btn_run, alignment=Qt.AlignmentFlag.AlignRight)

    
    def validate_config(self):
        """Valide la configuration générale"""
        self.config['nom'] = self.txt_name.text().strip()
        self.config['enregistrer'] = self.chk_save.isChecked()
        
        if not is_valid_name(self.config['nom']):
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erreur", "Nom invalide")
            return False
        return True
    
    def run_nback(self):
        if not self.validate_config():
            return
            
        self.config.update({
            'tache': 'NBack',
            'N': self.spin_n.value(),
            'n_trials': self.spin_nback_trials.value(),
            'isi': self.spin_nback_isi.value(),
            'stim_dur': self.spin_nback_dur.value()
        })
        self.launch_experiment()
    
    def run_digitspan(self):
        if not self.validate_config():
            return
            
        self.config.update({
            'tache': 'DigitSpan',
            'span_length': self.spin_span.value(),
            'n_trials': self.spin_digit_trials.value(),
            'digit_dur': self.spin_digit_dur.value(),
            'isi': self.spin_digit_isi.value()
        })
        self.launch_experiment()
    
    def run_flanker(self):
        if not self.validate_config():
            return
            
        self.config.update({
            'tache': 'Flanker',
            'n_trials': self.spin_flanker_trials.value(),
            'stim_dur': self.spin_flanker_dur.value(),
            'isi': self.spin_flanker_isi.value()
        })
        self.launch_experiment()
    
    def launch_experiment(self):
        """Ferme la fenêtre et retourne la configuration"""
        self.close()
        QApplication.exit(0)
    
    def get_config(self):
        return self.config

def show_qt_menu():
    app = QApplication(sys.argv)
    menu = ExperimentMenu()
    menu.show()
    app.exec()
    return menu.get_config()

# Version compatible avec votre code existant
class Menu:
    def show(self):
        config = show_qt_menu()
        return config if config['nom'] else None