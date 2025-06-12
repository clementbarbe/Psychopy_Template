# main.py
from psychopy import visual, core
from gui.menu import Menu
from utils.task_factory import create_task

def run_task(config):
    """Exécute une tâche basée sur la configuration"""
    win = visual.Window(
        size=config['window_size'],
        fullscr=config['fullscr'],
        color='black',
        units='norm'
    )

    task = create_task(config, win)
    if task:
        results = task.run()
        if hasattr(task, 'save_results'):
            task.save_results()

    win.close()

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
