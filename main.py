from psychopy import visual, core
from gui.menu import Menu
from utils.task_factory import create_task
from utils.timing import analyze_timing


def run_task(config):
    """Exécute une tâche basée sur la configuration, avec logging temporel avancé"""
    # Crée la fenêtre PsychoPy
    win = visual.Window(
        size=config['window_size'],
        fullscr=config['fullscr'],
        color='black',
        units='norm'
    )

    # Logger des timestamps
    flip_times = []
    original_flip = win.flip
    def logged_flip(*args, **kwargs):
        ret = original_flip(*args, **kwargs)
        flip_times.append(core.getTime())
        return ret
    win.flip = logged_flip

    # Exécution de la tâche
    task = create_task(config, win)
    results = None
    if task:
        results = task.run()
        if hasattr(task, 'save_results'):
            task.save_results()

    win.close()

    # Analyse post-tâche
    if flip_times:
        analyze_timing(flip_times, expected_hz=config.get('expected_hz', 60.0))

    return results


def main():
    while True:
        menu = Menu()
        config = menu.show()
        if not config:
            print("Configuration annulée")
            break

        print("Configuration validée:", config)
        run_task(config)


if __name__ == '__main__':
    main()