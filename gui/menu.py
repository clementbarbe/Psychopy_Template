from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QTabWidget, QLineEdit, QCheckBox, QPushButton, QLabel,
                            QSpinBox, QDoubleSpinBox, QGroupBox, QMessageBox, QComboBox)
from PyQt6.QtCore import Qt
from utils.utils import is_valid_name
from utils.logger import get_logger
import sys

logger = get_logger()

class ExperimentMenu(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Configuration Expérimentale")
        self.setFixedSize(1200, 650)
        
        self.hardware_present = False
        self.check_hardware_availability()

        self.config = {
            'nom': '',
            'session': '01',
            'enregistrer': True,
            'fullscr': True,
            'screenid': 1,
            'monitor' : 'temp_monitor',
            'colorspace' : 'rgb',
            'parport_actif': False
        }
        self.initUI()
        

    def check_hardware_availability(self):
        """
        Tente d'importer la librairie et d'ouvrir le port.
        Gère l'absence de librairie ou l'échec de connexion en interne.
        """
        try:
            # Import local : si ça échoue ici, on passe direct dans le except ImportError
            from hardware.parport import ParPort
            
            # Tentative de connexion
            test_port = ParPort(address=0x378)
            
            if test_port.dummy_mode:
                self.hardware_present = False
                # On log juste en info, car ParPort a déjà fait son print d'avertissement
                logger.log("Mode Simulation (Dummy) détecté.")
            else:
                self.hardware_present = True
                logger.ok("Port parallèle détecté avec succès.")
                
        except ImportError:
            # Cas où le fichier hardware/parport.py n'existe pas ou dépendances manquantes
            self.hardware_present = False
            logger.warn("Module 'hardware.parport' introuvable : Mode Simulation forcé.")
            
        except Exception as e:
            # Cas où la lib existe mais crashe à l'init (autre que le dummy mode)
            self.hardware_present = False
            logger.warn(f"Erreur init matériel : {e}")

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

        # Nom
        lbl_name = QLabel("ID Participant:")
        self.txt_name = QLineEdit()
        self.txt_name.setFixedWidth(150)
        
        # Session
        lbl_sess = QLabel("Session:")
        self.spin_session = QSpinBox()
        self.spin_session.setRange(1, 20)
        self.spin_session.setValue(1)
        self.spin_session.setFixedWidth(60)

        # Ecran
        lbl_screen = QLabel("Écran:")
        self.screenid = QSpinBox()
        self.screenid.setRange(1, len(QApplication.screens()))
        self.screenid.setValue(2)
        self.screenid.setFixedWidth(60)
        
        # Mode
        lbl_mode = QLabel("Mode:")
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["fmri", "PC"])
        self.combo_mode.setCurrentText("fmri")

        # Options
        self.chk_save = QCheckBox("Save Data")
        self.chk_save.setChecked(True)

        self.chk_parport = QCheckBox("Triggers (LPT)")
        if self.hardware_present:
            self.chk_parport.setChecked(True)
            self.chk_parport.setEnabled(True)
            self.chk_parport.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.chk_parport.setChecked(False)
            self.chk_parport.setEnabled(False)
            self.chk_parport.setStyleSheet("color: gray;")
        
        # Ajout au layout
        layout.addWidget(lbl_name)
        layout.addWidget(self.txt_name)
        layout.addWidget(lbl_sess)
        layout.addWidget(self.spin_session)
        layout.addWidget(lbl_screen)
        layout.addWidget(self.screenid)
        layout.addWidget(lbl_mode)
        layout.addWidget(self.combo_mode)
        layout.addWidget(self.chk_save)
        
        lbl_sep = QLabel("|")
        lbl_sep.setStyleSheet("color: gray;")
        layout.addWidget(lbl_sep)
        layout.addWidget(self.chk_parport)

        layout.addStretch()
        group.setLayout(layout)
        parent_layout.addWidget(group)

    def create_task_tabs(self, parent_layout):
        self.tabs = QTabWidget()

        self.nback_tab = QWidget()
        self.init_nback_tab()
        self.tabs.addTab(self.nback_tab, "NBack")

        self.digit_tab = QWidget()
        self.init_digitspan_tab()
        self.tabs.addTab(self.digit_tab, "DigitSpan")

        self.flanker_tab = QWidget()
        self.init_flanker_tab()
        self.tabs.addTab(self.flanker_tab, "Flanker")

        self.stroop_tab = QWidget()
        self.init_stroop_tab()
        self.tabs.addTab(self.stroop_tab, "Stroop")

        self.visualmemory_tab = QWidget()
        self.init_visualmemory_tab()
        self.tabs.addTab(self.visualmemory_tab, "Visual Memory")

        self.temporaljudgement_tab = QWidget()
        self.init_temporaljudgement_tab()
        self.tabs.addTab(self.temporaljudgement_tab, "Temporal Judgement")

        self.reward_tab = QWidget()
        self.init_reward_tab()
        self.tabs.addTab(self.reward_tab, "Door Reward")

        parent_layout.addWidget(self.tabs)

    # --- TABS INIT METHODS ---

    def init_nback_tab(self):
        layout = QVBoxLayout()
        self.nback_tab.setLayout(layout)
        params_group = QGroupBox("Paramètres NBack")
        params_layout = QVBoxLayout()
        
        n_layout = QVBoxLayout()
        lbl_n = QLabel("Niveau N:")
        self.spin_n = QSpinBox()
        self.spin_n.setRange(1, 4)
        self.spin_n.setValue(2)
        n_layout.addWidget(lbl_n)
        n_layout.addWidget(self.spin_n)
        
        trials_layout = QVBoxLayout()
        lbl_trials = QLabel("Nombre d'essais:")
        self.spin_nback_trials = QSpinBox()
        self.spin_nback_trials.setRange(1, 100)
        self.spin_nback_trials.setValue(10)
        trials_layout.addWidget(lbl_trials)
        trials_layout.addWidget(self.spin_nback_trials)
        
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
        self.spin_stroop_dur.setValue(1.5) 
        dur_layout.addWidget(lbl_dur) 
        dur_layout.addWidget(self.spin_stroop_dur) 

        lbl_isi = QLabel("ISI (s) :") 
        self.spin_stroop_isi = QDoubleSpinBox() 
        self.spin_stroop_isi.setRange(0.1, 5.0) 
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

        # TRAINING
        run_training_group = QGroupBox("Training")
        run_training_layout = QVBoxLayout()
        training_trials_layout = QHBoxLayout()
        training_trials_layout.addWidget(QLabel("Essais Training :"))
        self.run_training_trials_spinbox = QSpinBox()
        self.run_training_trials_spinbox.setRange(1, 200)
        self.run_training_trials_spinbox.setValue(12)
        training_trials_layout.addWidget(self.run_training_trials_spinbox)
        training_trials_layout.addStretch()
        run_training_layout.addLayout(training_trials_layout)

        btn_run_training = QPushButton("Lancer Training")
        btn_run_training.clicked.connect(lambda: self.run_temporal_judgement(
            run_type='training',
            n_trials_base=self.run_training_trials_spinbox.value(),
            run_number='00' 
        ))
        run_training_layout.addWidget(btn_run_training)
        run_training_group.setLayout(run_training_layout)
        layout.addWidget(run_training_group)

        # BASE
        run_base_group = QGroupBox("Run Base")
        run_base_layout = QVBoxLayout()
        trials_base_layout = QHBoxLayout()
        trials_base_layout.addWidget(QLabel("Essais Base :"))
        self.run_base_n_base_spinbox = QSpinBox()
        self.run_base_n_base_spinbox.setRange(1, 120)
        self.run_base_n_base_spinbox.setValue(72)
        trials_base_layout.addWidget(self.run_base_n_base_spinbox)
        trials_base_layout.addStretch()
        run_base_layout.addLayout(trials_base_layout)

        trials_block_layout = QHBoxLayout()
        trials_block_layout.addWidget(QLabel("Essais Block :"))
        self.run_base_n_block_spinbox = QSpinBox()
        self.run_base_n_block_spinbox.setRange(1, 120)
        self.run_base_n_block_spinbox.setValue(24)
        trials_block_layout.addWidget(self.run_base_n_block_spinbox)
        trials_block_layout.addStretch()
        run_base_layout.addLayout(trials_block_layout)

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

        # CUSTOM
        run_custom_group = QGroupBox("Run Personnalisé")
        run_custom_layout = QVBoxLayout()
        trials_layout = QHBoxLayout()
        trials_layout.addWidget(QLabel("Essais :"))
        self.run_custom_trials_spinbox = QSpinBox()
        self.run_custom_trials_spinbox.setRange(1, 500)
        self.run_custom_trials_spinbox.setValue(24)
        trials_layout.addWidget(self.run_custom_trials_spinbox)
        trials_layout.addStretch()
        run_custom_layout.addLayout(trials_layout)

        run_num_layout = QHBoxLayout()
        run_num_layout.addWidget(QLabel("Index Run (Block) :"))
        self.run_custom_number_spinbox = QSpinBox()
        self.run_custom_number_spinbox.setRange(1, 99)
        self.run_custom_number_spinbox.setValue(1)
        run_num_layout.addWidget(self.run_custom_number_spinbox)
        run_num_layout.addStretch()
        run_custom_layout.addLayout(run_num_layout)

        btn_run_custom = QPushButton("Lancer Custom")
        btn_run_custom.clicked.connect(lambda: self.run_temporal_judgement(
            run_type='custom',
            n_trials_block=self.run_custom_trials_spinbox.value(),
            run_number=str(self.run_custom_number_spinbox.value()).zfill(2)
        ))
        run_custom_layout.addWidget(btn_run_custom)
        run_custom_group.setLayout(run_custom_layout)
        layout.addWidget(run_custom_group)
        layout.addStretch()

    def init_reward_tab(self): 
        layout = QVBoxLayout() 
        self.reward_tab.setLayout(layout) 
        params_group = QGroupBox("Paramètres Tâche Portes (Reward)") 
        params_layout = QVBoxLayout() 
        
        trials_layout = QHBoxLayout() 
        lbl_trials = QLabel("Nombre d'essais :") 
        self.spin_reward_trials = QSpinBox() 
        self.spin_reward_trials.setRange(1, 200) 
        self.spin_reward_trials.setValue(50) 
        trials_layout.addWidget(lbl_trials) 
        trials_layout.addWidget(self.spin_reward_trials) 
        
        prob_layout = QHBoxLayout() 
        lbl_prob = QLabel("Probabilité de gain (0.0 - 1.0) :") 
        self.spin_reward_prob = QDoubleSpinBox() 
        self.spin_reward_prob.setRange(0.0, 1.0) 
        self.spin_reward_prob.setSingleStep(0.1) 
        self.spin_reward_prob.setValue(0.6) 
        prob_layout.addWidget(lbl_prob) 
        prob_layout.addWidget(self.spin_reward_prob) 

        isi_layout = QHBoxLayout() 
        lbl_isi = QLabel("ISI Moyen (s) :") 
        self.spin_reward_isi = QDoubleSpinBox() 
        self.spin_reward_isi.setRange(0.1, 10.0) 
        self.spin_reward_isi.setValue(2.0) 
        isi_layout.addWidget(lbl_isi) 
        isi_layout.addWidget(self.spin_reward_isi) 
        
        params_layout.addLayout(trials_layout) 
        params_layout.addLayout(prob_layout) 
        params_layout.addLayout(isi_layout) 
        params_group.setLayout(params_layout) 

        btn_run = QPushButton("Lancer Tâche Portes") 
        btn_run.clicked.connect(self.run_reward) 
        layout.addWidget(params_group) 
        layout.addStretch() 
        layout.addWidget(btn_run, alignment=Qt.AlignmentFlag.AlignRight) 

    # --- VALIDATION & RUN ---

    def validate_config(self):
        self.config['nom'] = self.txt_name.text().strip()
        self.config['session'] = f"{self.spin_session.value():02d}"
        self.config['enregistrer'] = self.chk_save.isChecked()
        self.config['screenid'] = self.screenid.value() - 1
        self.config['mode'] = self.combo_mode.currentText()
        self.config['parport_actif'] = self.chk_parport.isChecked()
        
        if not is_valid_name(self.config['nom']):
            QMessageBox.warning(self, "Erreur", "Nom invalide")
            logger.warn("Validation échouée : nom participant invalide")
            return False
        logger.ok(f"Config validée : {self.config['nom']} (Session {self.config['session']})")
        return True

    def run_nback(self):
        if not self.validate_config(): return
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
        if not self.validate_config(): return
        self.config.update({
            'tache': 'DigitSpan',
            'digit_dur': self.spin_digit_dur.value(),
            'isi': self.spin_digit_isi.value()
        })
        self.close()
        QApplication.quit()

    def run_flanker(self):
        if not self.validate_config(): return
        self.config.update({
            'tache': 'Flanker',
            'n_trials': self.spin_flanker_trials.value(),
            'stim_dur': self.spin_flanker_dur.value(),
            'isi': self.spin_flanker_isi.value()
        })
        self.close()
        QApplication.quit()

    def run_stroop(self):
        if not self.validate_config(): return
        self.config.update({
            'tache': 'Stroop',
            'n_trials': self.spin_stroop_trials.value(),
            'stim_dur': self.spin_stroop_dur.value(),
            'isi': self.spin_stroop_isi.value()
        })
        self.close()
        QApplication.quit()

    def run_visualmemory(self):
        if not self.validate_config(): return
        self.config.update({
            'tache': 'VisualMemory',
            'stim_dur': self.spin_visual_dur.value(),
            'isi': self.spin_visual_isi.value()
        })
        self.close()
        QApplication.quit()

    def run_temporal_judgement(self, run_type='base', n_trials_base=72, n_trials_block=24, n_trials_training=12, run_number='00'):
        if not self.validate_config(): return
        self.config.update({
            'tache': 'TemporalJudgement',
            'run_type': run_type,
            'run_id': run_number,
            'isi': (1500, 2500),
            'delays_ms': [200, 300, 400, 550, 700, 800],
            'response_options': [200, 300, 400, 550, 700, 800, 1000, 1200],
            'n_trials_base': n_trials_base,
            'n_trials_block': n_trials_block,
            'n_trials_training': n_trials_training,
        })
        self.close()
        QApplication.quit()

    def run_reward(self):
        if not self.validate_config(): return
        self.config.update({
            'tache': 'DoorReward',
            'n_trials': self.spin_reward_trials.value(),
            'reward_prob': self.spin_reward_prob.value(),
            'isi': self.spin_reward_isi.value()
        })
        self.close()
        QApplication.quit()

    def get_config(self):
        return self.config

def show_qt_menu():
    logger.log("Ouverture Menu QT")
    app = QApplication(sys.argv)
    menu = ExperimentMenu()
    menu.show()
    app.exec()
    return menu.get_config()

class Menu:
    def show(self):
        config = show_qt_menu()
        return config if config['nom'] else None