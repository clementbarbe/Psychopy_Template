"""
Flanker Task – Event-related fMRI (3T / 7T compatible)

Author : Clément BARBE / CENIR
Reviewed & optimized for fMRI by senior task engineer

Design:
- Event-related
- Jittered ISI (exponential, truncated)
- Optimized for BOLD GLM efficiency
"""

import os
import csv
import random
import logging
import sys
from datetime import datetime

import numpy as np
from psychopy import visual, event, core

from utils.utils import should_quit


# ======================================================================
# UTILS
# ======================================================================

def generate_jittered_isi(n_trials, isi_min=2.0, isi_max=14.0, isi_mean=6.0):
    """
    Generate truncated exponential ISIs for event-related fMRI.

    This distribution improves HRF deconvolution efficiency
    and reduces regressor collinearity.
    """
    lam = 1.0 / isi_mean
    isis = []

    for _ in range(n_trials):
        while True:
            sample = random.expovariate(lam)
            if isi_min <= sample <= isi_max:
                isis.append(round(sample, 3))
                break
    return isis


def generate_trials(n_trials):
    """
    Generate a balanced list of Flanker trials.
    """
    assert n_trials % 2 == 0, "n_trials must be even"

    conditions = ['congruent'] * (n_trials // 2) + \
                 ['incongruent'] * (n_trials // 2)
    random.shuffle(conditions)

    trials = []
    for cond in conditions:
        target = random.choice(['left', 'right'])
        if cond == 'congruent':
            flankers = [target, target]
        else:
            flankers = ['left' if target == 'right' else 'right'] * 2

        symbol = {'left': '<', 'right': '>'}
        stim = (
            symbol[flankers[0]] +
            symbol[flankers[1]] +
            symbol[target] +
            symbol[flankers[0]] +
            symbol[flankers[1]]
        )

        trials.append({
            'stimulus': stim,
            'target': target,
            'congruent': cond == 'congruent'
        })

    return trials


# ======================================================================
# TASK CLASS
# ======================================================================

class Flanker:
        
    def __init__(self, win, nom, enregistrer, screenid=1, n_trials=40, stim_dur=1.0, fixation_dur=0.5, data_dir='data/flanker', parport_actif=False, eyetracker_actif=False, mode='PC', session='01'):

        self.win = win
        self.participant = nom
        self.save_data = enregistrer

        self.n_trials = int(n_trials)
        self.stim_dur = float(stim_dur)
        self.fixation_dur = float(fixation_dur)

        os.makedirs(data_dir, exist_ok=True)
        self.data_dir = data_dir

        self._setup_logger()

        # Timing
        self.task_clock = None
        self.trial_clock = core.Clock()

        # Stimuli
        self.text = visual.TextStim(
            win, height=0.08, color='white', wrapWidth=1.5
        )
        self.fixation = visual.TextStim(
            win, text='+', height=0.12, color='white'
        )

        # Keys
        self.keys = {
            'left': 'left',
            'right': 'right',
            'trigger': 't',
            'quit': 'escape'
        }

        # Design
        self.trials = generate_trials(self.n_trials)
        self.isis = generate_jittered_isi(self.n_trials)

        # Data
        self.records = []
        self.current_trial = None
        self.start_time = datetime.now().strftime('%Y%m%d_%H%M%S')

    # ==================================================================

    def _setup_logger(self):
        self.logger = logging.getLogger('FlankerFMRI')
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '[%(asctime)s] %(levelname)s : %(message)s',
                datefmt='%H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    # ==================================================================

    def log_event(self, event_type, **kwargs):
        t = self.task_clock.getTime() if self.task_clock else 0.0
        entry = {
            'participant': self.participant,
            'trial': self.current_trial,
            'time_s': round(t, 5),
            'event': event_type
        }
        entry.update(kwargs)
        self.records.append(entry)

    # ==================================================================
    # TASK FLOW
    # ==================================================================

    def show_instructions(self):
        self.text.text = (
            "Tâche Flanker\n\n"
            "Indiquez la direction de la flèche CENTRALE.\n\n"
            "← : flèche gauche\n"
            "→ : flèche droite\n\n"
            "Essayez de répondre le plus rapidement\n"
            "et le plus précisément possible.\n\n"
            "Appuyez sur ESPACE pour commencer."
        )
        self.text.draw()
        self.win.flip()

        event.waitKeys(keyList=['space', self.keys['quit']])
        if event.getKeys([self.keys['quit']]):
            should_quit(self.win, quit=True)

    # ==================================================================

    def wait_for_trigger(self):
        self.text.text = "En attente du trigger scanner ('t')"
        self.text.draw()
        self.win.flip()

        event.waitKeys(keyList=[self.keys['trigger'], self.keys['quit']])
        if event.getKeys([self.keys['quit']]):
            should_quit(self.win, quit=True)

        self.task_clock = core.Clock()
        self.log_event('trigger')

    # ==================================================================

    def run_trial(self, idx):
        self.current_trial = idx + 1
        trial = self.trials[idx]
        isi = self.isis[idx]

        # Fixation pre-stimulus
        self.fixation.draw()
        self.win.flip()
        core.wait(self.fixation_dur)

        # Stimulus
        self.text.text = trial['stimulus']
        self.text.draw()
        self.win.flip()

        self.trial_clock.reset()
        self.log_event(
            'stim_onset',
            stimulus=trial['stimulus'],
            target=trial['target'],
            congruent=trial['congruent']
        )

        response, rt = None, None
        event.clearEvents()

        while self.trial_clock.getTime() < self.stim_dur:
            keys = event.getKeys(
                keyList=[self.keys['left'], self.keys['right'], self.keys['quit']],
                timeStamped=self.trial_clock
            )
            if keys:
                key, t = keys[0]
                if key == self.keys['quit']:
                    should_quit(self.win, quit=True)
                response = key
                rt = round(t, 5)
                break

        self.win.flip()

        accurate = response == trial['target']
        self.log_event(
            'response',
            response=response if response else 'none',
            rt=rt,
            accurate=accurate
        )

        # ISI (baseline)
        self.fixation.draw()
        self.win.flip()
        core.wait(isi)

    # ==================================================================

    def run(self):
        try:
            self.show_instructions()
            self.wait_for_trigger()

            for i in range(self.n_trials):
                should_quit(self.win)
                self.run_trial(i)

        finally:
            self.save()

    # ==================================================================

    def save(self):
        if not self.save_data or not self.records:
            return

        fname = f"{self.participant}_Flanker_{self.start_time}.csv"
        path = os.path.join(self.data_dir, fname)

        fieldnames = sorted({k for r in self.records for k in r})

        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames)
            writer.writeheader()
            writer.writerows(self.records)

        self.logger.info(f"Data saved to {path}")
