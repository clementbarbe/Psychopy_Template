import os
import sys
import random
import gc

# Import relatif
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from psychopy import visual, event, core
from utils.base_task import BaseTask
from utils.utils import should_quit


class Flanker(BaseTask):
    """
    Flanker Task - Rapid Event-Related fMRI
    - Timing absolu (anti-drift)
    - ISI Jittered (distribution exponentielle tronquée)
    - Stimulus : 500ms (Standard visibilité confortable)
    - Fenêtre de réponse : 1.5s (Standard pour éviter les 'misses')
    """

    def __init__(self, win, nom, session='01', enregistrer=True,
                 mode='fmri', n_trials=80, stim_dur=0.5, response_window=1.5,
                 isi_min=1.0, isi_max=5.0, isi_mean=2.5,
                 parport_actif=True, eyetracker_actif=False, **kwargs):

        super().__init__(
            win=win,
            nom=nom,
            session=session,
            task_name="Flanker",
            folder_name="flanker",
            eyetracker_actif=eyetracker_actif,
            parport_actif=(mode == 'fmri' and parport_actif),
            enregistrer=enregistrer,
            et_prefix="FLK"
        )

        # ------------------------
        # Paramètres (Standards fMRI)
        # ------------------------
        self.n_trials = n_trials
        self.stim_dur = stim_dur            # 500ms (Standard littérature)
        self.resp_window = response_window  # 1.5s
        self.isi_params = (isi_min, isi_max, isi_mean)

        # Codes TTL
        self.codes = {
            'start_exp': 255,
            'stim_congruent': 11,
            'stim_incongruent': 12,
            'resp_left': 1,
            'resp_right': 2,
            'fixation': 5
        }

        # Stimuli - Design standard arrows
        self.stim_text = visual.TextStim(
            self.win, text='', color='white', height=0.15, font='Arial', bold=True
        )

        # Touches
        if mode == 'fmri':
            self.keys = {'left': 'b', 'right': 'y'} 
        else:
            self.keys = {'left': 'left', 'right': 'right'}
        
        self.quit_key = 'escape'

        # Données
        self.trials_design = []
        self.global_records = []

    # ======================================================================
    # DESIGN & TIMING
    # ======================================================================

    def generate_design(self):
        """Génère les essais et les ISIs (Jitter)."""
        # 1. Génération ISIs (Distribution exponentielle tronquée pour efficacité BOLD)
        isi_min, isi_max, isi_mean = self.isi_params
        lam = 1.0 / isi_mean
        isis = []
        while len(isis) < self.n_trials:
            sample = random.expovariate(lam)
            if isi_min <= sample <= isi_max:
                isis.append(round(sample, 3))

        # 2. Génération Conditions (50% Congruent / 50% Incongruent)
        conds = ['congruent'] * (self.n_trials // 2) + ['incongruent'] * (self.n_trials // 2)
        random.shuffle(conds)

        # 3. Construction des stimuli
        symbol = {'left': '<', 'right': '>'}
        for i in range(self.n_trials):
            target = random.choice(['left', 'right'])
            if conds[i] == 'congruent':
                flank = target
            else:
                flank = 'right' if target == 'left' else 'left'
            
            # Format standard: << < << ou << > <<
            stim_str = f"{symbol[flank]}{symbol[flank]} {symbol[target]} {symbol[flank]}{symbol[flank]}"
            
            self.trials_design.append({
                'stimulus': stim_str,
                'target': target,
                'condition': conds[i],
                'isi': isis[i]
            })

    def _wait_until(self, t_goal, relax=0.001):
        while self.task_clock.getTime() < t_goal:
            dt = t_goal - self.task_clock.getTime()
            core.wait(min(relax, dt))

    # ======================================================================
    # RUN TRIAL
    # ======================================================================

    def run_trial(self, trial_idx, trial_data, onset_goal):
        """Un essai de Flanker avec timing absolu et fenêtre fixe."""
        should_quit(self.win)
        gc.disable()
        event.clearEvents(eventType='keyboard')

        trig_stim = self.codes[f"stim_{trial_data['condition']}"]

        # 1) Attente de l'onset précis (V-Sync aware)
        self._wait_until(onset_goal - 0.012) 

        # 2) STIM ONSET (500ms)
        self.stim_text.text = trial_data['stimulus']
        self.stim_text.draw()
        self.win.callOnFlip(self.ParPort.send_trigger, trig_stim)
        self.win.flip()
        
        onset_time = self.task_clock.getTime()
        drift_ms = (onset_time - onset_goal) * 1000.0

        # Timing de l'essai
        t_stim_off = onset_time + self.stim_dur
        t_resp_end = onset_time + self.resp_window
        # Ancrage du prochain essai : Onset actuel + Fenêtre de réponse fixe + Jitter
        next_onset_anchor = onset_goal + self.resp_window + trial_data['isi']

        resp_key = None
        rt = None

        # 3) Boucle de réponse et d'affichage
        # On maintient la boucle jusqu'à t_resp_end quoi qu'il arrive
        while self.task_clock.getTime() < t_resp_end:
            now = self.task_clock.getTime()
            
            if now < t_stim_off:
                self.stim_text.draw()
            else:
                self.fixation.draw()
            
            self.win.flip()

            if resp_key is None:
                keys = event.getKeys(
                    keyList=[self.keys['left'], self.keys['right'], self.quit_key],
                    timeStamped=self.task_clock
                )
                if keys:
                    k, t = keys[0]
                    if k == self.quit_key: should_quit(self.win, quit=True)
                    resp_key = k
                    rt = t - onset_time
                    self.ParPort.send_trigger(self.codes[f"resp_{'left' if k == self.keys['left'] else 'right'}"])

        # 4) Log & Score
        correct_key = self.keys[trial_data['target']]
        acc = 1 if resp_key == correct_key else 0
        status = "HIT" if acc == 1 else ("MISS" if resp_key is None else "WRONG")

        self.logger.log(f"T{trial_idx+1:02d} | {trial_data['condition'][:5].upper()} | {status} | RT:{rt if rt else 0:.3f} | Drift:{drift_ms:.1f}ms")

        # 5) Record
        self.global_records.append({
            'trial_idx': trial_idx + 1,
            'condition': trial_data['condition'],
            'target': trial_data['target'],
            'onset_goal': onset_goal,
            'onset_time': onset_time,
            'drift_ms': drift_ms,
            'rt': rt,
            'acc': acc,
            'isi_jitter': trial_data['isi']
        })
        
        gc.enable()
        return next_onset_anchor

    # ======================================================================
    # MAIN RUN
    # ======================================================================

    def run(self):
        try:
            self.generate_design()
            self.show_instructions(
                "TÂCHE FLANKER\n\n"
                "Répondez à la flèche du CENTRE\n"
                "le plus vite possible.\n\n"
                "Ignorez les flèches sur les côtés.\n"
                "Appuyez pour commencer."
            )
            self.wait_for_trigger()

            # Baseline initiale (12s pour stabiliser le signal T1)
            self.show_resting_state(5.0)

            next_onset = self.task_clock.getTime() + 0.5

            for i, trial_data in enumerate(self.trials_design):
                next_onset = self.run_trial(i, trial_data, next_onset)

            # Baseline finale (15s pour capturer la HRF du dernier essai)
            self.show_resting_state(5.0)

        finally:
            self.save_data(self.global_records)