"""
Flanker Task – Rapid Event-related fMRI (3T / 7T compatible)

Author : Clément BARBE / CENIR

- Stimulus duration reduced to 200ms (standard to prevent saccades).
- Response window extended to 1.5s (stimulus disappears but recording continues).
- ISI distribution tightened (Rapid Event-Related design).
"""

import os
import csv
import random
import logging
import sys
from datetime import datetime

import numpy as np
from psychopy import visual, event, core

# Mocking utils for standalone functionality if utils package is missing
try:
    from utils.utils import should_quit
except ImportError:
    def should_quit(win, quit=False):
        if quit:
            win.close()
            core.quit()

# ======================================================================
# UTILS
# ======================================================================

def generate_jittered_isi(n_trials, isi_min=1.5, isi_max=6.0, isi_mean=3.5):
    """
    Generate truncated exponential ISIs for Rapid Event-related fMRI.
    
    Updated parameters for 'Fast' design:
    - Min: 1.5s (allows BOLD to start decreasing)
    - Mean: 3.5s (optimum for rapid design efficiency)
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
    # Ensure even number for balanced design
    if n_trials % 2 != 0:
        n_trials += 1
        
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

        # Standard Flanker symbology
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
        
    def __init__(self, win, nom, enregistrer, screenid=1, n_trials=40, 
                 stim_dur=0.5,       # REDUCED: 200ms is lit. standard
                 response_max=1.5,   # NEW: Total time allowed to respond
                 data_dir='data/flanker', 
                 parport_actif=False, eyetracker_actif=False, 
                 mode='PC', session='01'):

        self.win = win
        self.participant = nom
        self.save_data = enregistrer

        self.n_trials = int(n_trials)
        self.stim_dur = float(stim_dur)        # Duration of arrows on screen
        self.response_max = float(response_max) # Duration of recording window

        os.makedirs(data_dir, exist_ok=True)
        self.data_dir = data_dir

        self._setup_logger()

        # Timing
        self.task_clock = None
        self.trial_clock = core.Clock()

        # Stimuli
        # Increased height slightly for better visibility at 200ms
        self.text = visual.TextStim(
            win, height=0.10, color='white', wrapWidth=1.5, font='Arial'
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
            'onset_s': round(t, 5),
            'event': event_type
        }
        entry.update(kwargs)
        self.records.append(entry)

    # ==================================================================
    # TASK FLOW
    # ==================================================================

    def show_instructions(self):
        self.text.text = (
            "Tâche Flanker (Rapide)\n\n"
            "Une série de flèches va apparaître très brièvement.\n"
            "Indiquez la direction de la flèche CENTRALE.\n\n"
            "← : flèche gauche\n"
            "→ : flèche droite\n\n"
            "Répondez même si les flèches ont disparu.\n"
            "Soyez le plus RAPIDE possible.\n\n"
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

        # 1. ISI (Jittered Fixation)
        # In rapid designs, the ISI acts as the baseline fixation
        self.fixation.draw()
        self.win.flip()
        core.wait(isi)

        # 2. Stimulus Onset (Short duration: 200ms)
        self.text.text = trial['stimulus']
        self.text.draw()
        
        # Sync to screen flip for precise timing
        onset_time = self.win.flip() 
        self.trial_clock.reset()
        
        self.log_event(
            'stim_onset',
            stimulus=trial['stimulus'],
            target=trial['target'],
            congruent=trial['congruent']
        )

        response = None
        rt = None
        event.clearEvents()
        
        # Loop for the duration of the response window (e.g., 1.5s)
        # Note: We do NOT break the loop on response to keep fMRI timing fixed
        while self.trial_clock.getTime() < self.response_max:
            t = self.trial_clock.getTime()
            
            # Switch from Stimulus to Fixation after stim_dur (e.g., 0.2s)
            if t >= self.stim_dur:
                self.fixation.draw()
            else:
                self.text.draw()
            
            self.win.flip()

            # Check for response if we haven't got one yet
            if response is None:
                keys = event.getKeys(
                    keyList=[self.keys['left'], self.keys['right'], self.keys['quit']],
                    timeStamped=self.trial_clock
                )
                if keys:
                    key, key_t = keys[0]
                    if key == self.keys['quit']:
                        should_quit(self.win, quit=True)
                    response = key
                    rt = round(key_t, 5) # RT relative to stim onset
                    
                    # Optional: Visual feedback of response? 
                    # Usually avoided in strict fMRI to avoid visual confounds.

        # Log response at the end of the trial window
        accurate = (response == trial['target']) if response else None
        self.log_event(
            'response',
            response=response if response else 'miss',
            rt=rt if rt else 0,
            accurate=accurate
        )

    # ==================================================================

    def run(self):
        try:
            self.show_instructions()
            self.wait_for_trigger()

            for i in range(self.n_trials):
                should_quit(self.win)
                self.run_trial(i)
                
            # Final buffer to capture BOLD of last trial
            self.fixation.draw()
            self.win.flip()
            core.wait(5.0)

        finally:
            self.save()

    # ==================================================================

    def save(self):
        if not self.save_data or not self.records:
            return

        fname = f"{self.participant}_FlankerFast_{self.start_time}.csv"
        path = os.path.join(self.data_dir, fname)

        fieldnames = sorted({k for r in self.records for k in r})

        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames)
            writer.writeheader()
            writer.writerows(self.records)

        self.logger.info(f"Data saved to {path}")