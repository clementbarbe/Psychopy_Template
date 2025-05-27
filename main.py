from psychopy import visual, core
from gui.menu import Menu
from tasks.nback import NBack
from tasks.digitspan import DigitSpan
from tasks.flanker import Flanker


def main():
    config = Menu().show()
    if config is None:
        print("Configuration annulée.")
        return

    win = visual.Window(
        size=config['window_size'],
        fullscr=config['fullscr'],
        color='black',
        units='norm'
    )

    task_name = config['tache']

    # Arguments communs
    base_kwargs = {
        'win': win,
        'nom': config['nom'],
        'enregistrer': config['enregistrer']
    }

    if task_name == 'NBack':
        task = NBack(
            **base_kwargs,
            N=config['N'],
            n_trials=config['n_trials'],
            isi=config['isi'],
            stim_dur=config['stim_dur']
        )

    elif task_name == 'DigitSpan':
        task = DigitSpan(
            **base_kwargs,
            span_length=config['span_length'],
            n_trials=config['n_trials'],
            digit_dur=config['digit_dur'],
            isi=config['isi']
        )

    elif task_name == 'Flanker':
        task = Flanker(
            **base_kwargs,
            n_trials=config['n_trials'],
            stim_dur=config['stim_dur'],
            isi=config['isi']
        )

    else:
        print("Tâche inconnue.")
        return

    results = task.run()
    if hasattr(task, 'save_results'):
        task.save_results()

    # Rejouer ?
    menu_final = Menu()
    choix = menu_final.show()
    if choix:
        win.close()
        main()
    else:
        win.close()
        core.quit()


if __name__ == '__main__':
    main()
