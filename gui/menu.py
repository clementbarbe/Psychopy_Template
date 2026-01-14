from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QTabWidget, QLineEdit, QCheckBox, QLabel,
                            QSpinBox, QGroupBox, QMessageBox, QComboBox)
from utils.utils import is_valid_name
from utils.logger import get_logger
import sys

# Direct imports for task tabs (GUI modules)
from gui.tabs.tabs_nback import NBackTab
from gui.tabs.tabs_flanker import FlankerTab
from gui.tabs.tabs_stroop import StroopTab
from gui.tabs.tabs_temporal_judgement import TemporalJudgementTab
from gui.tabs.tabs_doorreward import DoorRewardTab

logger = get_logger()

class ExperimentMenu(QMainWindow):
    """
    Main entry point for the Experimental Setup.
    Handles participant metadata, hardware checks (EyeTracker/Parallel Port),
    and task selection via tabs.
    """
    def __init__(self, last_config=None):
        super().__init__()
        self.setWindowTitle("Configuration Expérimentale")
        self.setFixedSize(1200, 650)
        
        # Hardware state flags
        self.hardware_present = False 
        self.eyelink_present = False  
        self.final_config = None

        # Run hardware checks before UI init to set checkbox states
        self.check_hardware_availability()

        # 1. Initialize default configuration structure
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

        # 2. Update with previous configuration if available (Session persistence)
        if last_config:
            self.default_config.update(last_config)
            # Auto-increment session number logic
            try:
                current_sess = int(self.default_config['session'])
                self.default_config['session'] = f"{current_sess + 1:02d}"
            except ValueError:
                pass # Keep as is if session is not an integer

        self.initUI()

    def closeEvent(self, event):
        """
        Handle window closure. Logs if the user quits without starting a task.
        """
        if self.final_config is None:
            logger.log("Menu closed by user (Exit).")
        event.accept()
        
    def check_hardware_availability(self):
        """
        Probes for physical hardware to enable/disable UI options accordingly.
        """
        # --- PARALLEL PORT CHECK ---
        try:
            from hardware.parport import ParPort
            test_port = ParPort(address=0x378)
            if test_port.dummy_mode:
                self.hardware_present = False
                logger.warn("Parallel Port: Not Available")
            else:
                self.hardware_present = True
                logger.ok("Parallel Port: Hardware detected.")
        except ImportError:
            self.hardware_present = False
            logger.warn("Parallel Port: Module not found -> Simulation Mode.")
        except Exception as e:
            self.hardware_present = False
            logger.warn(f"Parallel Port: Init Error -> {e}")

        # --- EYELINK CHECK ---
        try:
            import pylink
            self.eyelink_present = True
            logger.ok("EyeLink: Pylink library detected.")
        except ImportError:
            self.eyelink_present = False
            logger.warn("EyeLink: Not Available")
        except Exception as e:
            self.eyelink_present = False
            logger.warn(f"EyeLink: Error -> {e}")

    def initUI(self):
        """Builds the main layout structure."""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        
        self.create_general_section(main_layout)
        self.create_task_tabs(main_layout)

    def create_general_section(self, parent_layout):
        """Creates the top section for global settings (Subject ID, Session, Hardware)."""
        group = QGroupBox("Configuration Générale")
        layout = QHBoxLayout()

        # -- Participant Data --
        lbl_name = QLabel("ID Participant:")
        self.txt_name = QLineEdit()
        self.txt_name.setFixedWidth(150)
        self.txt_name.setText(self.default_config.get('nom', ''))
        
        lbl_sess = QLabel("Session:")
        self.spin_session = QSpinBox()
        self.spin_session.setRange(1, 20)
        self.spin_session.setFixedWidth(60)
        try:
            self.spin_session.setValue(int(self.default_config.get('session', 1)))
        except:
            self.spin_session.setValue(1)

        # -- Display Settings --
        lbl_screen = QLabel("Écran:")
        self.screenid = QSpinBox()
        self.screenid.setRange(1, len(QApplication.screens()))
        self.screenid.setFixedWidth(60)
        # Convert internal index (0-based) to UI display (1-based)
        saved_screen = self.default_config.get('screenid', 1)
        self.screenid.setValue(saved_screen + 1)
        
        lbl_mode = QLabel("Mode:")
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["fmri", "PC"])
        self.combo_mode.setCurrentText(self.default_config.get('mode', 'fmri'))

        self.chk_save = QCheckBox("Enregistrer")
        self.chk_save.setChecked(self.default_config.get('enregistrer', True))

        # -- Hardware Checkboxes (Styling & Logic) --
        # Standardized styles for consistency
        ACTIVE_STYLE = "color: green; font-weight: bold;"
        INACTIVE_STYLE = "color: gray;"

        # 1. Parallel Port
        self.chk_parport = QCheckBox("Parallel Port")
        should_check_lpt = self.hardware_present and self.default_config.get('parport_actif', False)
        
        if self.hardware_present:
            self.chk_parport.setChecked(should_check_lpt)
            self.chk_parport.setEnabled(True)
            self.chk_parport.setStyleSheet(ACTIVE_STYLE)
        else:
            self.chk_parport.setChecked(False)
            self.chk_parport.setEnabled(False)
            self.chk_parport.setStyleSheet(INACTIVE_STYLE)

        # 2. EyeLink (EyeTracker)
        self.chk_eyetracker = QCheckBox("EyeLink")
        should_check_eye = self.eyelink_present and self.default_config.get('eyetracker_actif', False)

        if self.eyelink_present:
            self.chk_eyetracker.setChecked(should_check_eye) 
            self.chk_eyetracker.setEnabled(True)
            self.chk_eyetracker.setStyleSheet(ACTIVE_STYLE)
        else:
            self.chk_eyetracker.setChecked(False)
            self.chk_eyetracker.setEnabled(False)
            self.chk_eyetracker.setStyleSheet(INACTIVE_STYLE)
            self.chk_eyetracker.setToolTip("Librairie 'pylink' manquante")
        
        # -- Layout Assembly --
        layout.addWidget(lbl_name)
        layout.addWidget(self.txt_name)
        layout.addWidget(lbl_sess)
        layout.addWidget(self.spin_session)
        layout.addWidget(lbl_screen)
        layout.addWidget(self.screenid)
        layout.addWidget(lbl_mode)
        layout.addWidget(self.combo_mode)
        layout.addWidget(self.chk_save)
        
        # Separators
        for chk in [self.chk_parport, self.chk_eyetracker]:
            lbl_sep = QLabel("|")
            lbl_sep.setStyleSheet("color: gray;")
            layout.addWidget(lbl_sep)
            layout.addWidget(chk)

        layout.addStretch()
        group.setLayout(layout)
        parent_layout.addWidget(group)

    def create_task_tabs(self, parent_layout):
        """Initializes the tabs for each specific cognitive task."""
        self.tabs = QTabWidget()
        
        # Inject 'self' (the menu instance) into tabs to allow callback execution
        self.tabs.addTab(NBackTab(self), "NBack")
        self.tabs.addTab(FlankerTab(self), "Flanker")
        self.tabs.addTab(StroopTab(self), "Stroop")
        self.tabs.addTab(TemporalJudgementTab(self), "Temporal Judgement")
        self.tabs.addTab(DoorRewardTab(self), "Door Reward")

        parent_layout.addWidget(self.tabs)

    def validate_config(self):
        """
        Validates User Inputs (Name, Session) and aggregates General Config.
        Returns: Dict if valid, None otherwise.
        """
        nom = self.txt_name.text().strip()
        if not is_valid_name(nom):
            QMessageBox.warning(self, "Erreur", "Nom invalide")
            logger.warn("Validation failed: Invalid participant name.")
            return None
        
        config = self.default_config.copy()
        config.update({
            'nom': nom,
            'session': f"{self.spin_session.value():02d}",
            'enregistrer': self.chk_save.isChecked(),
            'screenid': self.screenid.value() - 1, # Back to 0-based index
            'mode': self.combo_mode.currentText(),
            'parport_actif': self.chk_parport.isChecked(),
            'eyetracker_actif': self.chk_eyetracker.isChecked()
        })
        
        logger.ok(f"Config validated: {config['nom']} (Session {config['session']})")
        return config

    def run_experiment(self, task_params):
        """
        Merges General Config with Task Specific Params and exits the Menu 
        to start the experiment loop.
        """
        general_config = self.validate_config()
        if not general_config:
            return

        # Merge configs
        self.final_config = {**general_config, **task_params}
        self.close()
        QApplication.instance().quit()

    def get_config(self):
        return self.final_config

def show_qt_menu(last_config=None):
    """Entry point helper to launch the PyQt Application independently."""
    logger.log("Opening QT Menu")
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    menu = ExperimentMenu(last_config)
    menu.show()
    app.exec()
    return menu.get_config()