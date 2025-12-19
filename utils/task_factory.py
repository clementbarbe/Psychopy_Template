from tasks.nback import NBack
from tasks.digitspan import DigitSpan
from tasks.flanker import Flanker
from tasks.stroop import Stroop
from tasks.visualmemory import VisualMemory
from tasks.temporaljudgement import TemporalJudgement
from tasks.doorreward import DoorReward

def create_task(config, win):
    base_kwargs = {
        'win': win,
        'nom': config['nom'],
        'enregistrer': config['enregistrer'],
        'screenid': config['screenid'],
        #'parport_actif': config['parport_actif']
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
    
    if task_config == 'VisualMemory':
        return VisualMemory(
            **base_kwargs,  
            
        )   
    
    if task_config == 'TemporalJudgement':
        return TemporalJudgement(
            **base_kwargs,
            n_trials_base=config['n_trials_base'],
            n_trials_block=config['n_trials_block'],
            n_trials_training=config['n_trials_training'],
            session=config['session'],
            mode=config['mode'],
            run_type=config['run_type']            
        )
    
    elif task_config == 'DoorReward':
        return DoorReward(
            **base_kwargs,
            session=config['session'],             # Ajouté pour le logging
            n_trials=config['n_trials'],           # Vient du spin_reward_trials
            reward_probability=config['reward_prob'], # Vient du spin_reward_prob
            mode=config['mode']
        )
    else:
        print("Tâche inconnue.")
        return None
