from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QTabWidget, QLineEdit, QCheckBox, QPushButton, QLabel,
                            QSpinBox, QDoubleSpinBox, QGroupBox, QMessageBox)
from PyQt6.QtCore import Qt
from utils.utils import is_valid_name
from utils.logger import get_logger
import sys


class ExperimentMenu(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Configuration Expérimentale")
        self.setFixedSize(800, 600)
        self.config = {
            'nom': '',
            'enregistrer': True,
            'fullscr': True,
            'screenid': 1,
            'monitor' : 'temp_monitor',
            'colorspace' : 'rgb'
        }
        self.initUI()

    def initUI(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.create_general_section(main_layout)
        self.create_task_tabs(main_layout)

    def create_general_section(self, parent_layout):
        group = QGroupBox("Configuration Générale")
        layout = QHBoxLayout()
        lbl_name = QLabel("Nom du participant:")
        self.txt_name = QLineEdit()
        self.txt_name.setFixedWidth(200)
        self.chk_save = QCheckBox("Enregistrer les données")
        self.chk_save.setChecked(True)
        lbl_screen = QLabel("Écran:")
        self.screenid = QSpinBox()
        self.screenid.setRange(0, len(QApplication.screens()) )
        self.screenid.setValue(1)  # Écran 2 (index 1)
        layout.addWidget(lbl_name)
        layout.addWidget(self.txt_name)
        layout.addWidget(self.chk_save)
        layout.addWidget(lbl_screen)
        layout.addWidget(self.screenid)
        layout.addStretch()
        group.setLayout(layout)
        parent_layout.addWidget(group)

    def create_task_tabs(self, parent_layout):
        self.tabs = QTabWidget()

        # NBack
        self.nback_tab = QWidget()
        self.init_nback_tab()
        self.tabs.addTab(self.nback_tab, "NBack")

        # DigitSpan
        self.digit_tab = QWidget()
        self.init_digitspan_tab()
        self.tabs.addTab(self.digit_tab, "DigitSpan")

        # Flanker
        self.flanker_tab = QWidget()
        self.init_flanker_tab()
        self.tabs.addTab(self.flanker_tab, "Flanker")

        # Stroop
        self.stroop_tab = QWidget()
        self.init_stroop_tab()
        self.tabs.addTab(self.stroop_tab, "Stroop")

        # Visual Memory
        self.visualmemory_tab = QWidget()
        self.init_visualmemory_tab()
        self.tabs.addTab(self.visualmemory_tab, "Visual Memory")

        # Temporal Judgement
        self.temporaljudgement_tab = QWidget()
        self.init_temporaljudgement_tab()
        self.tabs.addTab(self.temporaljudgement_tab, "Temporal Judgement")

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
        layout = QVBoxLayout()
        self.digit_tab.setLayout(layout)
        params_group = QGroupBox("Paramètres DigitSpan")
        params_layout = QVBoxLayout()
        dur_layout = QVBoxLayout()
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
        btn_run = QPushButton("Lancer DigitSpan")
        btn_run.clicked.connect(self.run_digitspan)
        layout.addWidget(params_group)
        layout.addStretch()
        layout.addWidget(btn_run, alignment=Qt.AlignmentFlag.AlignRight)

    def init_flanker_tab(self):
        layout = QVBoxLayout()
        self.flanker_tab.setLayout(layout)
        params_group = QGroupBox("Paramètres Flanker")
        params_layout = QVBoxLayout()
        trials_layout = QVBoxLayout()
        lbl_trials = QLabel("Nombre d'essais:")
        self.spin_flanker_trials = QSpinBox()
        self.spin_flanker_trials.setRange(1, 100)
        self.spin_flanker_trials.setValue(20)
        trials_layout.addWidget(lbl_trials)
        trials_layout.addWidget(self.spin_flanker_trials)
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
        layout = QVBoxLayout() 
        self.stroop_tab = QWidget() 
        self.stroop_tab.setLayout(layout) 

        params_group = QGroupBox("Paramètres Stroop") 
        params_layout = QVBoxLayout() 
        trials_layout = QHBoxLayout() 

        lbl_trials = QLabel("Nombre d'essais :") 
        self.spin_stroop_trials = QSpinBox() 
        self.spin_stroop_trials.setRange(1, 500) 
        self.spin_stroop_trials.setValue(30) 
        trials_layout.addWidget(lbl_trials) 
        trials_layout.addWidget(self.spin_stroop_trials) 
        dur_layout = QHBoxLayout() 

        lbl_dur = QLabel("Durée stimulus (s) :") 
        self.spin_stroop_dur = QDoubleSpinBox() 
        self.spin_stroop_dur.setRange(0.1, 5.0) 
        self.spin_stroop_dur.setSingleStep(0.1) 
        self.spin_stroop_dur.setDecimals(2) 
        self.spin_stroop_dur.setValue(1.5) 
        dur_layout.addWidget(lbl_dur) 
        dur_layout.addWidget(self.spin_stroop_dur) 

        lbl_isi = QLabel("ISI (s) :") 
        self.spin_stroop_isi = QDoubleSpinBox() 
        self.spin_stroop_isi.setRange(0.1, 5.0) 
        self.spin_stroop_isi.setSingleStep(0.1) 
        self.spin_stroop_isi.setDecimals(2) 
        self.spin_stroop_isi.setValue(1.0) 
        dur_layout.addWidget(lbl_isi) 
        dur_layout.addWidget(self.spin_stroop_isi) 
        params_layout.addLayout(trials_layout) 
        params_layout.addLayout(dur_layout) 
        params_group.setLayout(params_layout) 

        btn_run = QPushButton("Lancer Stroop") 
        btn_run.clicked.connect(self.run_stroop) 
        layout.addWidget(params_group) 
        layout.addStretch() 
        layout.addWidget(btn_run, alignment=Qt.AlignmentFlag.AlignRight) 

        return self.stroop_tab
    

    def init_visualmemory_tab(self):
        layout = QVBoxLayout()
        self.visualmemory_tab.setLayout(layout)
        params_group = QGroupBox("Paramètres Visual Memory")
        params_layout = QVBoxLayout()
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

    def init_temporaljudgement_tab(self):
        layout = QVBoxLayout()
        self.temporaljudgement_tab.setLayout(layout)

        params_group = QGroupBox("Paramètres Temporal Judgement")
        params_layout = QVBoxLayout()

        trials_layout = QHBoxLayout()
        lbl_trials = QLabel("Nombre d'essais :")
        self.spin_temporal_trials = QSpinBox()
        self.spin_temporal_trials.setRange(1, 500)
        self.spin_temporal_trials.setValue(30)
        trials_layout.addWidget(lbl_trials)
        trials_layout.addWidget(self.spin_temporal_trials)

        isi_layout = QHBoxLayout()
        lbl_isi = QLabel("ISI (s) :")
        self.spin_temporal_isi = QDoubleSpinBox()
        self.spin_temporal_isi.setRange(0.1, 5.0)
        self.spin_temporal_isi.setSingleStep(0.1)
        self.spin_temporal_isi.setDecimals(2)
        self.spin_temporal_isi.setValue(1.0)
        isi_layout.addWidget(lbl_isi)
        isi_layout.addWidget(self.spin_temporal_isi)

        delays_layout = QHBoxLayout()
        lbl_delays = QLabel("Délais (ms, séparés par virgule) :")
        self.line_temporal_delays = QLineEdit()
        self.line_temporal_delays.setText("200,400,600")
        delays_layout.addWidget(lbl_delays)
        delays_layout.addWidget(self.line_temporal_delays)

        params_layout.addLayout(trials_layout)
        params_layout.addLayout(isi_layout)
        params_layout.addLayout(delays_layout)
        params_group.setLayout(params_layout)

        btn_run = QPushButton("Lancer Temporal Judgement")
        btn_run.clicked.connect(self.run_temporal_judgement)

        layout.addWidget(params_group)
        layout.addStretch()
        layout.addWidget(btn_run, alignment=Qt.AlignmentFlag.AlignRight)      

    def validate_config(self):
        logger = get_logger()
        self.config['nom'] = self.txt_name.text().strip()
        self.config['enregistrer'] = self.chk_save.isChecked()
        self.config['screenid'] = self.screenid.value() - 1
        if not is_valid_name(self.config['nom']):
            QMessageBox.warning(self, "Erreur", "Nom invalide")
            logger.warn("Validation échouée : nom participant invalide")
            return False
        logger.ok("Configuration générale validée : '{}'".format(self.config['nom']))
        return True

    def run_nback(self):
        logger = get_logger()
        if not self.validate_config():
            return
        logger.log("Lancement NBack (N={}, essais={}, dur={}, ISI={})".format(
            self.spin_n.value(),
            self.spin_nback_trials.value(),
            self.spin_nback_dur.value(),
            self.spin_nback_isi.value()
        ))
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
        logger = get_logger()
        if not self.validate_config():
            return
        logger.log("Lancement DigitSpan (dur={}, ISI={})".format(
            self.spin_digit_dur.value(),
            self.spin_digit_isi.value()
        ))
        self.config.update({
            'tache': 'DigitSpan',
            'digit_dur': self.spin_digit_dur.value(),
            'isi': self.spin_digit_isi.value()
        })
        self.close()
        QApplication.quit()

    def run_flanker(self):
        logger = get_logger()
        if not self.validate_config():
            return
        logger.log("Lancement Flanker (essais={}, dur={}, ISI={})".format(
            self.spin_flanker_trials.value(),
            self.spin_flanker_dur.value(),
            self.spin_flanker_isi.value()
        ))
        self.config.update({
            'tache': 'Flanker',
            'n_trials': self.spin_flanker_trials.value(),
            'stim_dur': self.spin_flanker_dur.value(),
            'isi': self.spin_flanker_isi.value()
        })
        self.close()
        QApplication.quit()

    def run_stroop(self):
        logger = get_logger()
        if not self.validate_config():
            return
        logger.log("Lancement Stroop (essais={}, dur={}, ISI={})".format(
            self.spin_stroop_trials.value(),
            self.spin_stroop_dur.value(),
            self.spin_stroop_isi.value()
        ))
        self.config.update({
            'tache': 'Stroop',
            'n_trials': self.spin_stroop_trials.value(),
            'stim_dur': self.spin_stroop_dur.value(),
            'isi': self.spin_stroop_isi.value()
        })
        self.close()
        QApplication.quit()

    def run_visualmemory(self):
        logger = get_logger()
        if not self.validate_config():
            return
        logger.log("Lancement VisualMemory (dur={}, ISI={})".format(
            self.spin_visual_dur.value(),
            self.spin_visual_isi.value()
        ))
        self.config.update({
            'tache': 'VisualMemory',
            'stim_dur': self.spin_visual_dur.value(),
            'isi': self.spin_visual_isi.value()
        })
        self.close()
        QApplication.quit()

    def run_temporal_judgement(self):
        if not self.validate_config():
            return

        # Récupération des paramètres depuis l’interface
        n_trials = self.spin_temporal_trials.value()
        isi = self.spin_temporal_isi.value()
        delays_str = self.line_temporal_delays.text().strip()

        # Conversion des délais en liste d'entiers
        try:
            delays = [int(x.strip()) for x in delays_str.split(',') if x.strip()]
            if not delays:
                raise ValueError("Aucun délai valide fourni.")
        except Exception:
            print("⚠️ Erreur : la liste des délais doit contenir des valeurs entières séparées par des virgules (ex: 200,400,600).")
            return

        # Mise à jour de la configuration
        self.config.update({
            'tache': 'TemporalJudgement',
            'n_trials': n_trials,
            'isi': isi,
            'delays_ms': delays
        })

        print(f"Lancement Temporal Judgement : essais={n_trials}, ISI={isi}, délais={delays}")

        # Fermeture propre
        self.close()
        QApplication.quit()


    def get_config(self):
        return self.config

def show_qt_menu():
    logger = get_logger()
    logger.log("Ouverture du menu graphique (Qt)")
    app = QApplication(sys.argv)
    menu = ExperimentMenu()
    menu.show()
    app.exec()
    logger.log("Menu fermé")
    return menu.get_config()


class Menu:
    def show(self):
        config = show_qt_menu()
        return config if config['nom'] else None