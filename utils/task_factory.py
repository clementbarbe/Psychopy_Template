from tasks.nback import NBack
from tasks.digitspan import DigitSpan
from tasks.flanker import Flanker
from tasks.stroop import Stroop
from tasks.oddball import AuditoryOddball

def create_task(config, win):
    base_kwargs = {
        'win': win,
        'nom': config['nom'],
        'enregistrer': config['enregistrer']
    }

    task_config = config['tache']

    if task_config == 'NBack':
        return NBack(
            **base_kwargs,
            N=config['N'],
            n_trials=config['n_trials'],
            isi=config['isi'],
            stim_dur=config['stim_dur']
        )
    elif task_config == 'DigitSpan':
        return DigitSpan(
            **base_kwargs,
            span_length=config['span_length'],
            n_trials=config['n_trials'],
            digit_dur=config['digit_dur'],
            isi=config['isi']
        )
    elif task_config == 'Flanker':
        return Flanker(
            **base_kwargs,
            n_trials=config['n_trials'],
            stim_dur=config['stim_dur'],
            isi=config['isi']
        )
    
    if task_config == 'Stroop':
        return Stroop(
            **base_kwargs,
            n_trials=config['n_trials'],
            isi=config['isi'],
            stim_dur=config['stim_dur']
        )   
    
    elif task_config == 'AuditoryOddball':
        return AuditoryOddball(
            **base_kwargs,
            p_deviant=config['p_deviant'],
            n_trials=config['n_trials'],
            isi=config['isi'],
            stim_dur=config['stim_dur']
        )

    else:
        print("Tâche inconnue.")
        return None
