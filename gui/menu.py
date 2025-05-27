from psychopy import gui
from utils.utils import is_valid_name

class Menu:
    def show(self):
        info = {
            'Nom du participant': '',
            'Enregistrer les données ?': ['Non', 'Oui'],
            'Tâche': ['NBack', 'DigitSpan', 'Flanker']
        }

        dlg = gui.DlgFromDict(dictionary=info, title='Configuration générale', order=['Nom du participant', 'Enregistrer les données ?', 'Tâche'])

        if not dlg.OK:
            return None

        nom = info['Nom du participant'].strip()
        enregistrer = info['Enregistrer les données ?']
        tache = info['Tâche']

        if not is_valid_name(nom):
            print("Nom invalide.")
            return None

        config = {
            'nom': nom,
            'enregistrer': (enregistrer == 'Oui'),
            'tache': tache,
            'window_size': (1500, 1500),
            'fullscr': False
        }

        # Paramètres spécifiques
        if tache == 'NBack':
            config.update({'N': 2, 'n_trials': 30, 'isi': 1.5, 'stim_dur': 0.5})
        elif tache == 'DigitSpan':
            config.update({'span_length': 5, 'n_trials': 10, 'digit_dur': 0.8, 'isi': 0.5})
        elif tache == 'Flanker':
            config.update({'n_trials': 20, 'stim_dur': 1, 'isi': 1.0})

        return config
