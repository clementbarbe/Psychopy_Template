from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QTabWidget, QLineEdit, QCheckBox, QLabel,
                            QSpinBox, QGroupBox, QMessageBox, QComboBox)
from utils.utils import is_valid_name
from utils.logger import get_logger
import sys

# Import Direct des fichiers de tabs (avec le prefixe gui.)
from gui.tabs.tabs_nback import NBackTab
from gui.tabs.tabs_digitspan import DigitSpanTab
from gui.tabs.tabs_flanker import FlankerTab
from gui.tabs.tabs_stroop import StroopTab
from gui.tabs.tabs_visual_memory import VisualMemoryTab
from gui.tabs.tabs_temporal_judgement import TemporalJudgementTab
from gui.tabs.tabs_doorreward import DoorRewardTab

logger = get_logger()

class ExperimentMenu(QMainWindow):
    def __init__(self, last_config=None):
        super().__init__()
        self.setWindowTitle("Configuration Expérimentale")
        self.setFixedSize(1200, 650)
        
        self.hardware_present = False 
        self.eyelink_present = False  
        self.final_config = None

        self.check_hardware_availability()

        # 1. Configuration par défaut
        self.default_config = {
            'nom': '', 
            'session': '01', 
            'enregistrer': True, 
            'fullscr': True,
            'screenid': 1, 
            'monitor' : 'temp_monitor', 
            'colorspace' : 'rgb',
            'parport_actif': False, 
            'eyetracker_actif':False,
            'mode': 'fmri'
        }

        # 2. Si on relance le menu (last_config existe), on met à jour les valeurs
        if last_config:
            self.default_config.update(last_config)
            # Logique intelligente : on essaie d'augmenter la session de 1
            try:
                current_sess = int(self.default_config['session'])
                self.default_config['session'] = f"{current_sess + 1:02d}"
            except ValueError:
                pass # Si la session n'est pas un nombre, on ne touche à rien

        self.initUI()

    def closeEvent(self, event):
        """
        Déclenché quand on clique sur la croix de la fenêtre.
        """
        # Si final_config n'est pas rempli (donc on n'a pas lancé de tâche),
        # on s'assure qu'il est None
        if self.final_config is None:
            logger.log("Menu fermé par l'utilisateur (Croix).")
        
        # On laisse la fermeture se faire
        event.accept()
        
    def check_hardware_availability(self):
        # --- CHECK PORT PARALLÈLE ---
        try:
            from hardware.parport import ParPort
            test_port = ParPort(address=0x378)
            if test_port.dummy_mode:
                self.hardware_present = False
                logger.log("LPT: Mode Simulation (Dummy) détecté.")
            else:
                self.hardware_present = True
                logger.ok("LPT: Port parallèle détecté.")
        except ImportError:
            self.hardware_present = False
            logger.warn("LPT: Module introuvable -> Mode Simulation.")
        except Exception as e:
            self.hardware_present = False
            logger.warn(f"LPT: Erreur init -> {e}")

        # --- CHECK EYELINK ---
        try:
            import pylink
            self.eyelink_present = True
            logger.ok("EyeLink: Librairie Pylink détectée.")
        except ImportError:
            self.eyelink_present = False
            logger.warn("EyeLink: Librairie Pylink introuvable.")
        except Exception as e:
            self.eyelink_present = False
            logger.warn(f"EyeLink: Erreur -> {e}")

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

        lbl_name = QLabel("ID Participant:")
        self.txt_name = QLineEdit()
        self.txt_name.setFixedWidth(150)
        # On remplit avec la valeur de la config (vide ou ancien nom)
        self.txt_name.setText(self.default_config.get('nom', ''))
        
        lbl_sess = QLabel("Session:")
        self.spin_session = QSpinBox()
        self.spin_session.setRange(1, 20)
        self.spin_session.setFixedWidth(60)
        # On remplit avec la session calculée
        try:
            self.spin_session.setValue(int(self.default_config.get('session', 1)))
        except:
            self.spin_session.setValue(1)

        lbl_screen = QLabel("Écran:")
        self.screenid = QSpinBox()
        self.screenid.setRange(1, len(QApplication.screens()))
        self.screenid.setFixedWidth(60)
        # Attention : default_config stocke l'index 0 (0,1...), le spinbox affiche 1,2...
        saved_screen = self.default_config.get('screenid', 1)
        self.screenid.setValue(saved_screen + 1)
        
        lbl_mode = QLabel("Mode:")
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["fmri", "PC"])
        self.combo_mode.setCurrentText(self.default_config.get('mode', 'fmri'))

        self.chk_save = QCheckBox("Enregistrer")
        self.chk_save.setChecked(self.default_config.get('enregistrer', True))

        # --- HARDWARE CHECKBOXES ---
        self.chk_parport = QCheckBox("Triggers (LPT)")
        # On active si le hardware est là ET que la config le demande (ou par défaut)
        should_check_lpt = self.hardware_present and self.default_config.get('parport_actif', False)
        
        if self.hardware_present:
            self.chk_parport.setChecked(should_check_lpt)
            self.chk_parport.setEnabled(True)
            self.chk_parport.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.chk_parport.setChecked(False)
            self.chk_parport.setEnabled(False)
            self.chk_parport.setStyleSheet("color: gray;")

        self.chk_eyetracker = QCheckBox("EyeLink")
        should_check_eye = self.eyelink_present and self.default_config.get('eyetracker_actif', False)

        if self.eyelink_present:
            self.chk_eyetracker.setChecked(should_check_eye) 
            self.chk_eyetracker.setEnabled(True)
            self.chk_eyetracker.setStyleSheet("color: blue; font-weight: bold;")
        else:
            self.chk_eyetracker.setChecked(False)
            self.chk_eyetracker.setEnabled(False)
            self.chk_eyetracker.setStyleSheet("color: gray;")
            self.chk_eyetracker.setToolTip("Librairie 'pylink' manquante")
        
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

        lbl_sep = QLabel("|")
        lbl_sep.setStyleSheet("color: gray;")
        layout.addWidget(lbl_sep)
        layout.addWidget(self.chk_eyetracker)

        layout.addStretch()
        group.setLayout(layout)
        parent_layout.addWidget(group)

    def create_task_tabs(self, parent_layout):
        self.tabs = QTabWidget()

        # On passe 'self' (le menu) aux onglets
        self.tabs.addTab(NBackTab(self), "NBack")
        self.tabs.addTab(DigitSpanTab(self), "DigitSpan")
        self.tabs.addTab(FlankerTab(self), "Flanker")
        self.tabs.addTab(StroopTab(self), "Stroop")
        self.tabs.addTab(VisualMemoryTab(self), "Visual Memory")
        self.tabs.addTab(TemporalJudgementTab(self), "Temporal Judgement")
        self.tabs.addTab(DoorRewardTab(self), "Door Reward")

        parent_layout.addWidget(self.tabs)

    def validate_config(self):
        """Valide la config générale et retourne le dictionnaire ou None"""
        nom = self.txt_name.text().strip()
        if not is_valid_name(nom):
            QMessageBox.warning(self, "Erreur", "Nom invalide")
            logger.warn("Validation échouée : nom participant invalide")
            return None
        
        config = self.default_config.copy()
        config.update({
            'nom': nom,
            'session': f"{self.spin_session.value():02d}",
            'enregistrer': self.chk_save.isChecked(),
            'screenid': self.screenid.value() - 1,
            'mode': self.combo_mode.currentText(),
            'parport_actif': self.chk_parport.isChecked(),
            'eyetracker_actif': self.chk_eyetracker.isChecked()
        })
        
        logger.ok(f"Config validée : {config['nom']} (Session {config['session']})")
        return config

    def run_experiment(self, task_params):
        """Méthode appelée par les onglets. Fusionne config générale et config tâche"""
        general_config = self.validate_config()
        if not general_config:
            return

        # Fusion
        self.final_config = {**general_config, **task_params}
        self.close()
        QApplication.instance().quit()

    def get_config(self):
        return self.final_config

# --- Note: Cette fonction 'show_qt_menu' n'est probablement plus utilisée telle quelle
# si ton main.py instancie directement ExperimentMenu, mais on la laisse pour compatibilité.
def show_qt_menu(last_config=None):
    logger.log("Ouverture Menu QT")
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    menu = ExperimentMenu(last_config)
    menu.show()
    app.exec()
    return menu.get_config()