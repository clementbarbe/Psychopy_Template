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
            'window_size': (2000, 2000),
            'fullscr': True,
            'screenid': 1
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
        
        # Choix de l'écran
        lbl_screen = QLabel("Écran:")
        self.screenid = QSpinBox()
        self.screenid.setRange(0, QApplication.screens().__len__() - 1)  # index en fonction du nb d'écrans
        self.screenid.setValue(1)  # par défaut le premier écran

        


        layout.addWidget(lbl_name)
        layout.addWidget(self.txt_name)
        layout.addWidget(self.chk_save)
        layout.addWidget(lbl_screen)
        layout.addWidget(self.screenid)
        
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

        # Onglet Stroop
        self.stroop_tab = QWidget()
        self.init_stroop_tab()
        self.tabs.addTab(self.stroop_tab, "Stroop")

        # Onglet Visual Memory
        self.visualmemory_tab = QWidget()
        self.init_visualmemory_tab()
        self.tabs.addTab(self.visualmemory_tab, "Visual Memory")

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
        self.spin_nback_trials.setValue(10)
        trials_layout.addWidget(lbl_trials)
        trials_layout.addWidget(self.spin_nback_trials)

        # Durées
        dur_layout = QVBoxLayout()
        lbl_isi = QLabel("ISI (s):")
        self.spin_nback_isi = QDoubleSpinBox()
        self.spin_nback_isi.setSingleStep(0.1)
        self.spin_nback_isi.setValue(0.5)

        lbl_dur = QLabel("Durée stimulus (s):")
        self.spin_nback_dur = QDoubleSpinBox()
        self.spin_nback_dur.setSingleStep(0.01)
        self.spin_nback_dur.setValue(1.5)

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

    def init_stroop_tab(self):
        # Création de l'onglet Stroop
        layout = QVBoxLayout()
        self.stroop_tab = QWidget()
        self.stroop_tab.setLayout(layout)

        # — Groupe Paramètres Stroop —
        params_group = QGroupBox("Paramètres Stroop")
        params_layout = QVBoxLayout()

        # Nombre d'essais Stroop
        trials_layout = QHBoxLayout()
        lbl_trials = QLabel("Nombre d'essais :")
        self.spin_stroop_trials = QSpinBox()
        self.spin_stroop_trials.setRange(1, 500)      # jusqu'à 500 essais si besoin
        self.spin_stroop_trials.setValue(30)        # valeur par défaut
        trials_layout.addWidget(lbl_trials)
        trials_layout.addWidget(self.spin_stroop_trials)

        # Durée du stimulus Stroop
        dur_layout = QHBoxLayout()
        lbl_dur = QLabel("Durée stimulus (s) :")
        self.spin_stroop_dur = QDoubleSpinBox()
        self.spin_stroop_dur.setRange(0.1, 5.0)      # entre 100 ms et 5 s
        self.spin_stroop_dur.setSingleStep(0.1)
        self.spin_stroop_dur.setDecimals(2)
        self.spin_stroop_dur.setValue(1.5)           # valeur par défaut
        dur_layout.addWidget(lbl_dur)
        dur_layout.addWidget(self.spin_stroop_dur)

        # ISI Stroop
        lbl_isi = QLabel("ISI (s) :")
        self.spin_stroop_isi = QDoubleSpinBox()
        self.spin_stroop_isi.setRange(0.1, 5.0)
        self.spin_stroop_isi.setSingleStep(0.1)
        self.spin_stroop_isi.setDecimals(2)
        self.spin_stroop_isi.setValue(1.0)
        dur_layout.addWidget(lbl_isi)
        dur_layout.addWidget(self.spin_stroop_isi)

        # Assemblage des paramètres
        params_layout.addLayout(trials_layout)
        params_layout.addLayout(dur_layout)
        params_group.setLayout(params_layout)

        # — Bouton de lancement —
        btn_run = QPushButton("Lancer Stroop")
        btn_run.clicked.connect(self.run_stroop)

        # Ajout dans le layout principal
        layout.addWidget(params_group)
        layout.addStretch()  # pousse le bouton en bas
        layout.addWidget(btn_run, alignment=Qt.AlignmentFlag.AlignRight)

        # Retourne l'onglet pour que tu puisses l'ajouter à ton QTabWidget
        return self.stroop_tab
    
    def init_visualmemory_tab(self):
        layout = QVBoxLayout()
        self.visualmemory_tab.setLayout(layout)

        params_group = QGroupBox("Paramètres Visual Memory")
        params_layout = QVBoxLayout()

        # Durées
        dur_layout = QVBoxLayout()
        lbl_visual_dur = QLabel("Durée stimulus (s):")
        self.spin_visual_dur = QDoubleSpinBox()
        self.spin_visual_dur.setValue(1.0)

        lbl_visual_isi = QLabel("ISI (s):")
        self.spin_visual_isi = QDoubleSpinBox()
        self.spin_visual_isi.setValue(0.5)

        dur_layout.addWidget(lbl_visual_dur)
        dur_layout.addWidget(self.spin_visual_dur)
        dur_layout.addWidget(lbl_visual_isi)
        dur_layout.addWidget(self.spin_visual_isi)

        params_layout.addLayout(dur_layout)
        params_group.setLayout(params_layout)

        btn_run = QPushButton("Lancer Visual Memory")
        btn_run.clicked.connect(self.run_visualmemory)

        layout.addWidget(params_group)
        layout.addStretch()
        layout.addWidget(btn_run, alignment=Qt.AlignmentFlag.AlignRight)

    def validate_config(self):
        """Valide la configuration générale"""
        self.config['nom'] = self.txt_name.text().strip()
        self.config['enregistrer'] = self.chk_save.isChecked()
        self.config['screenid'] = self.screenid.value()

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
        self.close()
        QApplication.quit()

    def run_digitspan(self):
        if not self.validate_config():
            return

        self.config.update({
            'tache': 'DigitSpan',
            'digit_dur': self.spin_digit_dur.value(),
            'isi': self.spin_digit_isi.value()
        })
        self.close()
        QApplication.quit()

    def run_flanker(self):
        if not self.validate_config():
            return

        self.config.update({
            'tache': 'Flanker',
            'n_trials': self.spin_flanker_trials.value(),
            'stim_dur': self.spin_flanker_dur.value(),
            'isi': self.spin_flanker_isi.value()
        })
        self.close()
        QApplication.quit()

    def run_stroop(self):
        if not self.validate_config():
            return

        self.config.update({
            'tache': 'Stroop',
            'n_trials': self.spin_stroop_trials.value(),
            'stim_dur': self.spin_stroop_dur.value(),
            'isi': self.spin_stroop_isi.value()
        })
        self.close()
        QApplication.quit()

    def run_visualmemory(self):
        if not self.validate_config():
            return

        self.config.update({
            'tache': 'VisualMemory',
            'stim_dur': self.spin_visual_dur.value(),
            'isi': self.spin_visual_isi.value()
        })
        self.close()
        QApplication.quit()


    def get_config(self):
        return self.config

def show_qt_menu():
    app = QApplication(sys.argv)
    menu = ExperimentMenu()
    menu.show()
    app.exec()
    return menu.get_config()

class Menu:
    def show(self):
        config = show_qt_menu()
        return config if config['nom'] else None