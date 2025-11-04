from psychopy import visual, core, hardware
from gui.menu import Menu
from utils.task_factory import create_task
from utils.logger import get_logger


def run_task(config):
    """Exécute une tâche basée sur la configuration, avec logging temporel avancé"""
    logger = get_logger()
    logger.log("Création de la fenêtre PsychoPy...")
    win = visual.Window(
        size=config['window_size'],
        fullscr=config['fullscr'],
        color='black',
        units='norm',
        screen=config['screenid'],
    )
    logger.ok("Fenêtre PsychoPy créée ({}x{}, fullscr={}, écran={})".format(
        *config['window_size'], config['fullscr'], config['screenid']
    ))

    logger.log("Création de la tâche '{}'...".format(config['tache']))
    task = create_task(config, win)
    if not task:
        logger.err("Échec de création de la tâche '{}'".format(config['tache']))
        win.close()
        return None

    logger.ok("Tâche '{}' prête".format(config['tache']))
    results = None
    try:
        logger.log("Démarrage de l'exécution de la tâche...")
        results = task.run()
        logger.ok("Tâche '{}' terminée avec succès".format(config['tache']))
    except Exception as e:
        logger.err("Erreur pendant l'exécution de la tâche : {}".format(e))
        raise
    finally:
        if hasattr(task, 'save_results') and config.get('enregistrer', True):
            logger.log("Sauvegarde des résultats...")
            try:
                task.save_results()
                logger.ok("Résultats sauvegardés")
            except Exception as e:
                logger.err("Échec sauvegarde résultats : {}".format(e))

        logger.log("Fermeture de la fenêtre...")
        win.close()
        logger.ok("Fenêtre fermée")

    return results


def main():
    logger = get_logger()
    logger.padding = 30
    logger.ok("Démarrage de l'application PsychoPy")

    while True:
        logger.log("Affichage du menu de configuration...")
        menu = Menu()
        config = menu.show()
        
        if not config:
            logger.warn("Configuration annulée par l'utilisateur")
            break

        logger.ok("Configuration validée : participant='{}', tâche='{}'".format(
            config['nom'], config['tache']
        ))
        
        try:
            run_task(config)
            logger.ok("Session terminée pour '{}'".format(config['nom']))
        except Exception as e:
            logger.err("Erreur fatale dans run_task : {}".format(e))

        # Optionnel : demander si on continue
        # (ou boucle infinie si tu veux relancer directement)

    logger.ok("Application terminée proprement")

if __name__ == '__main__':
    main()