from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QTabWidget, QLineEdit, QCheckBox, QPushButton, QLabel,
                            QSpinBox, QDoubleSpinBox, QGroupBox, QMessageBox, QComboBox)
from PyQt6.QtCore import Qt
from utils.utils import is_valid_name
from utils.logger import get_logger
import sys


try:
    from hardware.parport import ParPort
    HARDWARE_LIB_AVAILABLE = True
except ImportError:
    HARDWARE_LIB_AVAILABLE = False
    print("Warning: hardware.parport introuvable, mode simulation forcé.")

class ExperimentMenu(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Configuration Expérimentale")
        self.setFixedSize(1200, 650) # Légèrement agrandi pour la nouvelle option
        
        # --- TEST DU MATÉRIEL DÈS LE LANCEMENT ---
        self.hardware_present = False
        self.check_hardware_availability()

        self.config = {
            'nom': '',
            'enregistrer': True,
            'fullscr': True,
            'screenid': 1,
            'monitor' : 'temp_monitor',
            'colorspace' : 'rgb',
            'parport_actif': False # Valeur par défaut
        }
        self.initUI()

    def check_hardware_availability(self):
        """Tente d'ouvrir le port pour voir s'il existe physiquement."""
        if not HARDWARE_LIB_AVAILABLE:
            self.hardware_present = False
            return

        try:
            # On tente une connexion (adresse standard 0x378)
            test_port = ParPort(address=0x378)
            
            if test_port.dummy_mode:
                self.hardware_present = False
                print("[MENU] Port parallèle NON détecté (Mode Dummy activé par la classe).")
            else:
                self.hardware_present = True
                print("[MENU] Port parallèle détecté avec succès.")
                
            # Pas besoin de fermer explicitement ici car ParPort gère ça ou reste dispo
            # mais si votre classe ParPort garde la ressource, le script principal
            # la réinitialisera, ce qui est généralement toléré par PsychoPy.
            
        except Exception as e:
            print(f"[MENU] Erreur lors du test matériel: {e}")
            self.hardware_present = False


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
        self.screenid.setRange(1, len(QApplication.screens()) )
        self.screenid.setValue(2)
        
        lbl_mode = QLabel("Mode touches:")
        self.combo_mode = QComboBox()
        self.combo_mode.addItem("PC")
        self.combo_mode.addItem("fmri")
        self.combo_mode.setCurrentText("fmri")

        self.chk_parport = QCheckBox("Triggers (LPT)")

        if self.hardware_present:
            # Si le matériel est là, on coche par défaut mais l'utilisateur peut décocher
            self.chk_parport.setChecked(True)
            self.chk_parport.setEnabled(True)
            self.chk_parport.setToolTip("Port parallèle")
            self.chk_parport.setStyleSheet("color: green; font-weight: bold;")
        else:
            # Si pas de matériel, on désactive et on décoche
            self.chk_parport.setChecked(False)
            self.chk_parport.setEnabled(False)
            self.chk_parport.setText("Port parallèle")
            self.chk_parport.setToolTip("Aucun port parallèle trouvé (0x378) ou driver manquant.")
            self.chk_parport.setStyleSheet("color: gray;")
        
        layout.addWidget(lbl_name)
        layout.addWidget(self.txt_name)
        layout.addWidget(self.chk_save)
        layout.addWidget(lbl_screen)
        layout.addWidget(self.screenid)
        layout.addWidget(lbl_mode)
        layout.addWidget(self.combo_mode)

        lbl_sep = QLabel("|")
        lbl_sep.setStyleSheet("color: gray;")
        layout.addWidget(lbl_sep)
        layout.addWidget(self.chk_parport)

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

        # ========== RUN TRAINING ==========
        run_training_group = QGroupBox("Training Run")
        run_training_layout = QVBoxLayout()

        # --- Ajout du choix du nombre d’essais ---
        training_trials_layout = QHBoxLayout()
        training_trials_layout.addWidget(QLabel("Essais Training :"))
        self.run_training_trials_spinbox = QSpinBox()
        self.run_training_trials_spinbox.setMinimum(1)
        self.run_training_trials_spinbox.setMaximum(200)
        self.run_training_trials_spinbox.setValue(12)  # valeur par défaut
        training_trials_layout.addWidget(self.run_training_trials_spinbox)
        training_trials_layout.addStretch()
        run_training_layout.addLayout(training_trials_layout)

        # --- Bouton Lancer Training ---
        btn_run_training = QPushButton("Lancer Training")
        btn_run_training.clicked.connect(lambda: self.run_temporal_judgement(
            run_type='training',
            n_trials_base=self.run_training_trials_spinbox.value(),
            run_number='00'
        ))
        run_training_layout.addWidget(btn_run_training)

        run_training_group.setLayout(run_training_layout)
        layout.addWidget(run_training_group)

        # ========== RUN BASE ==========
        run_base_group = QGroupBox("Run Base")
        run_base_layout = QVBoxLayout()

        # --- Essais pour la Base ---
        trials_base_layout = QHBoxLayout()
        trials_base_layout.addWidget(QLabel("Essais Base :"))
        self.run_base_n_base_spinbox = QSpinBox()
        self.run_base_n_base_spinbox.setMinimum(1)
        self.run_base_n_base_spinbox.setMaximum(120)
        self.run_base_n_base_spinbox.setValue(72)  # valeur par défaut pour Base
        trials_base_layout.addWidget(self.run_base_n_base_spinbox)
        trials_base_layout.addStretch()
        run_base_layout.addLayout(trials_base_layout)

        # --- Essais pour le Block ---
        trials_block_layout = QHBoxLayout()
        trials_block_layout.addWidget(QLabel("Essais Block :"))
        self.run_base_n_block_spinbox = QSpinBox()
        self.run_base_n_block_spinbox.setMinimum(1)
        self.run_base_n_block_spinbox.setMaximum(120)
        self.run_base_n_block_spinbox.setValue(24)
        trials_block_layout.addWidget(self.run_base_n_block_spinbox)
        trials_block_layout.addStretch()
        run_base_layout.addLayout(trials_block_layout)

        # --- Bouton Lancer Base ---
        btn_run_base = QPushButton("Lancer Run Base")
        btn_run_base.clicked.connect(lambda: self.run_temporal_judgement(
            run_type='base',
            n_trials_base=self.run_base_n_base_spinbox.value(),
            n_trials_block=self.run_base_n_block_spinbox.value(),
            run_number='00'
        ))
        run_base_layout.addWidget(btn_run_base)

        run_base_group.setLayout(run_base_layout)
        layout.addWidget(run_base_group)

        # ========== RUN PERSONNALISÉ ==========
        run_custom_group = QGroupBox("Run Personnalisé")
        run_custom_layout = QVBoxLayout()

        trials_layout = QHBoxLayout()
        trials_layout.addWidget(QLabel("Nombre d'essais :"))
        self.run_custom_trials_spinbox = QSpinBox()
        self.run_custom_trials_spinbox.setMinimum(1)
        self.run_custom_trials_spinbox.setMaximum(500)
        self.run_custom_trials_spinbox.setValue(24)
        trials_layout.addWidget(self.run_custom_trials_spinbox)
        trials_layout.addStretch()
        run_custom_layout.addLayout(trials_layout)

        run_num_layout = QHBoxLayout()
        run_num_layout.addWidget(QLabel("Numéro de Run :"))
        self.run_custom_number_spinbox = QSpinBox()
        self.run_custom_number_spinbox.setMinimum(1)
        self.run_custom_number_spinbox.setMaximum(99)
        self.run_custom_number_spinbox.setValue(1)
        run_num_layout.addWidget(self.run_custom_number_spinbox)
        run_num_layout.addStretch()
        run_custom_layout.addLayout(run_num_layout)

        btn_run_custom = QPushButton("Lancer Run Personnalisé")
        btn_run_custom.clicked.connect(lambda: self.run_temporal_judgement(
            run_type='custom',
            n_trials_block=self.run_custom_trials_spinbox.value(),
            run_number=str(self.run_custom_number_spinbox.value()).zfill(2)
        ))
        run_custom_layout.addWidget(btn_run_custom)

        run_custom_group.setLayout(run_custom_layout)
        layout.addWidget(run_custom_group)

        layout.addStretch()

    def validate_config(self):
        logger = get_logger()
        self.config['nom'] = self.txt_name.text().strip()
        self.config['enregistrer'] = self.chk_save.isChecked()
        self.config['screenid'] = self.screenid.value() - 1
        self.config['mode'] = self.combo_mode.currentText()
        self.config['parport_actif'] = self.chk_parport.isChecked()
        
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

    def run_temporal_judgement(
        self,
        run_type='base',
        n_trials_base=72,
        n_trials_block=24,
        n_trials_training=12,
        run_number='00'
        ):
        logger = get_logger()
        if not self.validate_config():
            return

        # ----- Log -----
        logger.log(
            f"Lancement Temporal Judgement : {run_type.upper()} "
        )

        # ----- Configuration -----
        self.config.update({
            'tache': 'TemporalJudgement',
            'run_type': run_type,
            'session': run_number,
            'isi': (1500, 2500),
            'delays_ms': [200, 300, 400, 550, 700, 800],
            'response_options': [200, 300, 400, 550, 700, 800, 1000, 1200],
            'n_trials_base': n_trials_base,
            'n_trials_block': n_trials_block,
            'n_trials_training': n_trials_training,
        })

        # ----- Fermeture -----
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