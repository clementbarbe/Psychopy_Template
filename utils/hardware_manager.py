import sys
from utils.logger import get_logger

logger = get_logger()

# =============================================================================
# 1. FAIL-SAFE DUMMY CLASSES
# =============================================================================

class SafeDummyParPort:
    """
    Mock class for Parallel Port. 
    Used when hardware is disabled or drivers are missing.
    """
    def __init__(self): 
        pass

    def send_trigger(self, code, duration=0.03): 
        # Silent pass to avoid console spamming during high-frequency loops
        pass

    def reset(self): 
        pass

class SafeDummyEyeTracker:
    """
    Mock class for EyeTracker (Pylink).
    Mimics the API of the real EyeTracker to prevent AttributeErrors.
    """
    def __init__(self, sample_rate=1000, dummy_mode=True): 
        pass

    def initialize(self, file_name="TEST.EDF"): 
        logger.info(f"[Dummy ET] Virtual file defined: {file_name}")

    def send_message(self, msg): 
        pass 

    def start_recording(self): 
        logger.info("[Dummy ET] Start Recording (Simulation)")

    def stop_recording(self): 
        pass

    def close_and_transfer_data(self, local_folder="data"): 
        logger.info(f"[Dummy ET] Data transfer simulation to {local_folder}")

# =============================================================================
# 2. SECURE IMPORTS (Dependency Injection)
# =============================================================================

# --- Parallel Port Import ---
try:
    from hardware.parport import ParPort
    ParPortAvailable = True
except (ImportError, OSError) as e:
    logger.warn(f"Hardware: Parallel Port driver unavailable ({e}). Fallback to Dummy.")
    ParPort = SafeDummyParPort
    ParPortAvailable = False

# --- EyeTracker Import ---
try:
    # Handles missing 'libeyelink_core.so' or 'pylink' library
    from hardware.eyetracker import EyeTracker
    EyeTrackerAvailable = True
except (ImportError, OSError) as e:
    logger.warn(f"Hardware: EyeTracker driver unavailable ({e}). Fallback to Dummy.")
    EyeTracker = SafeDummyEyeTracker
    EyeTrackerAvailable = False


# =============================================================================
# 3. FACTORY FUNCTION
# =============================================================================
def setup_hardware(parport_actif=False, eyetracker_actif=False, window=None):
    """
    Initializes hardware based on configuration and availability.
    
    Returns:
        tuple: (lpt_instance, et_instance)
        Both are guaranteed to be objects (Real or Dummy), never None.
    """
    
    # --- 1. SETUP PARALLEL PORT ---
    lpt = None
    if parport_actif:
        if ParPortAvailable:
            try:
                lpt = ParPort(address=0x378)
                logger.ok("LPT: Parallel Port connected successfully.")
            except Exception as e:
                logger.err(f"LPT: Init failed ({e}). Reverting to Dummy.")
                lpt = SafeDummyParPort()
        else:
            logger.info("LPT: Active in config but drivers missing. Using Dummy.")
            lpt = SafeDummyParPort()
    else:
        # Intentionally disabled by user
        lpt = SafeDummyParPort()

    # --- 2. SETUP EYETRACKER ---
    et = None
    if eyetracker_actif:
        if EyeTrackerAvailable:
            try:
                # Instantiate Real EyeTracker
                et = EyeTracker(dummy_mode=False)
                
                # Check internal state (some wrappers have their own dummy flag)
                if not getattr(et, 'dummy_mode', False):
                    logger.ok("EyeTracker: Connected and Ready.")
                else:
                    logger.warn("EyeTracker: Driver loaded but device not found (Internal Dummy).")
            except Exception as e:
                logger.err(f"EyeTracker: Init failed ({e}). Reverting to Dummy.")
                et = SafeDummyEyeTracker()
        else:
            logger.info("EyeTracker: Active in config but drivers missing. Using Dummy.")
            et = SafeDummyEyeTracker()
    else:
        # Intentionally disabled by user
        et = SafeDummyEyeTracker()

    return lpt, et