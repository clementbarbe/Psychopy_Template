import sys
# On importe la fonction pour récupérer ton instance de Logger
from utils.logger import get_logger

# On récupère l'instance du logger
logger = get_logger()

# =============================================================================
# 1. DÉFINITION DES CLASSES DE SECOURS (DUMMIES)
# =============================================================================

class SafeDummyParPort:
    def __init__(self): 
        pass

    def send_trigger(self, code, duration=0.03): 
        # On utilise log (blanc/défaut) pour ne pas spammer de warnings
        pass

    def reset(self): 
        pass

class SafeDummyEyeTracker:
    def __init__(self, sample_rate=1000, dummy_mode=True): 
        # Warn ici pour rappeler que c'est un faux EyeTracker au démarrage
        logger.warn("[Dummy ET] Initialisé (Mode Simulation)")

    def initialize(self, file_name="TEST.EDF"): 
        logger.log(f"[Dummy ET] Fichier virtuel défini : {file_name}")

    def send_message(self, msg): 
        pass 

    def start_recording(self): 
        logger.log("[Dummy ET] Start Recording")

    def stop_recording(self): 
        pass

    def close_and_transfer_data(self, local_folder="data"): 
        pass

# =============================================================================
# 2. IMPORTS SÉCURISÉS
# =============================================================================

# --- A. Import Port Parallèle ---
try:
    from hardware.parport import ParPort, DummyParPort
except (ImportError, OSError) as e:
    logger.warn(f">> Hardware Warning: Port Parallèle non disponible ({e}). Utilisation du Dummy.")
    ParPort = SafeDummyParPort
    DummyParPort = SafeDummyParPort

# --- B. Import EyeTracker ---
try:
    # C'est ici que l'erreur "libeyelink_core.so" arrive sur ton PC portable
    from hardware.eyetracker import EyeTracker
except (ImportError, OSError) as e:
    logger.warn(f">> Hardware Warning: EyeTracker (Pylink) non disponible ({e}). Utilisation du Dummy.")
    EyeTracker = SafeDummyEyeTracker


# =============================================================================
# 3. FONCTION DE CONFIGURATION
# =============================================================================
def setup_hardware(parport_actif=False, eyetracker_actif=False, window=None):
    """
    Configure le matériel. Si les librairies manquent, renvoie silencieusement
    les versions Dummy définies ci-dessus.
    """
    
    # --- 1. PORT PARALLÈLE ---
    if parport_actif:
        try:
            lpt = ParPort(address=0x378)
            logger.ok("Port Parallèle connecté.")
        except Exception as e:
            logger.err(f"Erreur init ParPort: {e}")
            lpt = SafeDummyParPort()
    else:
        lpt = SafeDummyParPort()

    # --- 2. EYETRACKER ---
    if eyetracker_actif:
        try:
            # Tente de charger le vrai, ou le SafeDummy si l'import a échoué plus haut
            et = EyeTracker(dummy_mode=False)
            
            # Vérification supplémentaire : si c'est le vrai EyeTracker, est-il connecté ?
            if not getattr(et, 'dummy_mode', False):
                logger.ok("EyeTracker connecté.")
            else:
                # C'est le vrai module mais il a échoué la connexion IP
                pass 
                
        except Exception as e:
            logger.err(f"Erreur init EyeTracker: {e}")
            et = SafeDummyEyeTracker()
    else:
        et = SafeDummyEyeTracker() # Force le dummy

    return lpt, et