# main.py
import sys
import signal 
from PyQt6.QtWidgets import QApplication
from gui.menu import ExperimentMenu
from utils.logger import get_logger


signal.signal(signal.SIGINT, signal.SIG_DFL)

def show_menu_and_get_config(app, last_config=None):
    """
    Instantiates and displays the PyQt Experiment Menu.
    Blocks execution until the user validates a configuration or closes the window.
    
    Returns:
        dict: Configuration dictionary if validated.
        None: If the user closed the window (Exit).
    """
    menu = ExperimentMenu(last_config)
    menu.show()
    
    # Start Qt Event Loop. Execution halts here until menu.close() is called.
    app.exec()
    
    # Retrieve configuration state before destroying the object
    config = menu.get_config()
    
    # Clean up UI resources immediately
    menu.deleteLater()
    app.processEvents() 
    
    return config

def run_task_logic(config):
    """
    Logique PsychoPy sécurisée pour permettre le retour au menu.
    """
    logger = get_logger()
    
    # Imports différés (inchangés)
    from psychopy import visual, core, logging
    from utils.task_factory import create_task 
    
    logging.console.setLevel(logging.ERROR)
    
    # Création fenêtre
    win = visual.Window(
        fullscr=config['fullscr'],
        color='black',
        units='norm',
        screen=config['screenid'],
        checkTiming=False 
    )

    task = create_task(config, win)
    
    if not task:
        logger.err(f"Factory Error: Could not create task '{config.get('tache')}'")
        win.close()
        return

    try:
        win.flip()
        core.wait(0.5) 

        # --- Lancement de la tâche ---
       
        task.run()
        
        # --- Sauvegarde ---
        if config.get('enregistrer', True):
            if hasattr(task, 'save_results'):
                task.save_results()
            elif hasattr(task, 'save_data'):
                task.save_data()
                
    except Exception as e:
        logger.err(f"Runtime Error during task execution: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # --- CRUCIAL : On ferme juste la fenêtre ---
   
        win.close()

def main():
    """
    Application Entry Point.
    Manages the lifecycle loop: Menu -> Task -> Menu.
    """
    logger = get_logger()
    
    # Initialize the centralized Qt Application
    app = QApplication(sys.argv)
   
    last_config = None

    while True:
        # 1. Configuration Phase (PyQt)
        config = show_menu_and_get_config(app, last_config)

        # Exit Condition: User closed the menu window directly
        if not config:
            logger.log("User requested exit via Menu.")
            break 
        
        # 2. Execution Phase (PsychoPy)
        try:
            logger.log(f"Launching task: {config.get('tache', 'Unknown')}...")
            
            run_task_logic(config)
            
            # Cache config for the next iteration (convenience for the user)
            last_config = config
            
        except Exception as e:
            logger.err(f"Fatal error in main loop: {e}")
            # We continue the loop to allow the user to retry or fix settings
            pass

    # --- GRACEFUL SHUTDOWN ---
    logger.log("Application shutdown.")
    app.quit() 
    sys.exit(0)

if __name__ == '__main__':
    main()