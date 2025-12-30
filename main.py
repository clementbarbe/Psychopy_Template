# main.py
import sys
import signal # Nécessaire pour le Ctrl+C
from PyQt6.QtWidgets import QApplication

# --- MODIF 1 : Ne PAS importer psychopy ou task_factory ici ---
# On importe seulement les modules légers
from gui.menu import ExperimentMenu
from utils.logger import get_logger

# On laisse Python gérer le Ctrl+C par défaut (sinon Qt le bloque)
signal.signal(signal.SIGINT, signal.SIG_DFL)

def show_menu_and_get_config(app, last_config=None):
    """
    Affiche le menu. Si l'utilisateur clique sur la croix, retourne None.
    """
    menu = ExperimentMenu(last_config)
    menu.show()
    
    # Lance la boucle d'événement.
    # Elle s'arrêtera quand menu.close() sera appelé (via run ou croix)
    app.exec()
    
    # Récupère la config
    config = menu.get_config()
    
    # --- NETTOYAGE CRITIQUE POUR LINUX ---
    # On force la destruction du widget pour libérer les ressources graphiques
    # avant que PsychoPy ne tente de prendre la main.
    menu.deleteLater()
    app.processEvents() 
    # -------------------------------------
    
    return config

def run_task_logic(config):
    """
    Logique PsychoPy. 
    Les imports sont faits ICI pour éviter le conflit avec PyQt au démarrage.
    """
    logger = get_logger()
    
    # --- MODIF 2 : IMPORTS TARDIFS (LAZY IMPORTS) ---
    # On importe PsychoPy uniquement maintenant. 
    # Cela évite le 'Core Dumped' au lancement car Qt a fini son travail.
    from psychopy import visual, core, logging
    from utils.task_factory import create_task # Déplacé ici aussi
    
    # Config logging PsychoPy
    logging.console.setLevel(logging.ERROR)
    
    # Création fenêtre PsychoPy
    win = visual.Window(
        fullscr=config['fullscr'],
        color='black',
        units='norm',
        screen=config['screenid'],
        checkTiming=False 
    )

    task = create_task(config, win)
    
    if not task:
        logger.err(f"Échec de création de la tâche '{config.get('tache')}'")
        win.close()
        return

    try:
        # Petit temps pour s'assurer que le focus est pris
        win.flip()
        core.wait(0.5) 

        task.run()
        
        if config.get('enregistrer', True):
            if hasattr(task, 'save_results'):
                task.save_results()
            elif hasattr(task, 'save_data'):
                task.save_data()
                
    except Exception as e:
        logger.err(f"Erreur pendant l'exécution de la tâche : {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Fermeture propre de la fenêtre PsychoPy
        win.close()
        # On tente de libérer les ressources Pyglet/GLFW
        core.quit() 

def main():
    logger = get_logger()
    
    # Création de l'app QT
    app = QApplication(sys.argv)
    
    # --- MODIF 3 : On enlève le setQuitOnLastWindowClosed(False) ---
    # Si on le laisse, l'app ne veut jamais mourir. 
    # On veut gérer la boucle nous-mêmes.
    
    last_config = None

    while True:
        # 1. Affichage Menu
        # Si l'utilisateur clique sur la croix, config sera None
        config = show_menu_and_get_config(app, last_config)

        # Si croix ou annuler
        if not config:
            logger.log("Fermeture demandée par l'utilisateur (Menu).")
            break # Sort du While True
        
        # 2. Exécution Tâche
        try:
            logger.log(f"Lancement de {config['tache']}...")
            
            # On lance la tâche PsychoPy
            run_task_logic(config)
            
            # Sauvegarde pour la prochaine boucle
            last_config = config
            
        except Exception as e:
            logger.err(f"Erreur fatale dans run_task : {e}")
            pass

    # --- MODIF 4 : Sortie propre ---
    logger.log("Arrêt du programme.")
    app.quit() # Tue l'instance QT
    sys.exit(0) # Tue le processus Python

if __name__ == '__main__':
    main()