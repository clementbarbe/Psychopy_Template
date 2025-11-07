from psychopy import visual, logging
from gui.menu import Menu
from utils.task_factory import create_task
from utils.logger import get_logger

# Supprime les warnings PsychoPy
logging.console.setLevel(logging.ERROR)


def run_task(config):
    """Exécute une tâche basée sur la configuration"""
    logger = get_logger()
    win = visual.Window(
        fullscr=config['fullscr'],
        color='black',
        units='norm',
        screen=config['screenid']
    )

    task = create_task(config, win)
    if not task:
        logger.err(f"Échec de création de la tâche '{config['tache']}'")
        win.close()
        return None

    try:
        results = task.run()
    except Exception as e:
        logger.err(f"Erreur pendant l'exécution de la tâche : {e}")
        raise
    finally:
        if hasattr(task, 'save_results') and config.get('enregistrer', True):
            try:
                task.save_results()
            except Exception as e:
                logger.err(f"Échec sauvegarde résultats : {e}")
        win.close()

    return results


def main():
    logger = get_logger()
    logger.padding = 30
    menu = Menu()

    while True:
        config = menu.show()
        if not config:
            break

        config.pop('monitor', None)
        config.pop('colorspace', None)

        try:
            run_task(config)
        except Exception as e:
            logger.err(f"Erreur fatale dans run_task : {e}")

if __name__ == '__main__':
    main()
