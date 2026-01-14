"""
Flanker Task (fMRI / Behavioral)
-------------------------------
Tâche de type Flanker, compatible IRM.

Auteur : [Clément BARBE / CENIR]
"""

import os
import csv
import random
import logging
import sys
from datetime import datetime

from psychopy import visual, event, core
from utils.utils import should_quit
from utils.hardware_manager import setup_hardware


class Flanker:
    """
    Implémentation rigoureuse d'une tâche Flanker.
    """

    # ======================================================================
    # INITIALISATION
    # ======================================================================

    def __init__(self, win, nom, enregistrer, screenid=1,
                 n_trials=10, stim_dur=1.0, isi=1.0,
                 data_dir='data/flanker'):

        self.win = win
        self.nom = nom
        self.enregistrer = enregistrer
        self.screenid = screenid

        self.n_trials = int(n_trials)
        self.stim_dur = float(stim_dur)
        self.isi = float(isi)

        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

        self._setup_logger()

        # ------------------------------------------------------------------
        # CLOCKS
        # ------------------------------------------------------------------
        self.task_clock = None   # démarre au trigger (T0 IRM)
        self.trial_clock = core.Clock()

        # ------------------------------------------------------------------
        # STIMULI
        # ------------------------------------------------------------------
        self.text_stim = visual.TextStim(
            self.win,
            height=0.08,
            color='white',
            wrapWidth=1.5
        )

        self.fixation = visual.TextStim(
            self.win,
            text='+',
            height=0.12,
            color='white'
        )

        # ------------------------------------------------------------------
        # KEYS
        # ------------------------------------------------------------------
        self.keys = {
            'left': 'left',
            'right': 'right',
            'trigger': 't',
            'quit': 'escape'
        }

        # ------------------------------------------------------------------
        # DATA
        # ------------------------------------------------------------------
        self.start_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.records = []
        self.current_trial = None

    # ======================================================================
    # LOGGER
    # ======================================================================

    def _setup_logger(self):
        self.logger = logging.getLogger('FlankerTask')
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '[%(asctime)s] %(levelname)-8s : %(message)s',
                datefmt='%H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    # ======================================================================
    # LOGGING STRUCTURÉ
    # ======================================================================

    def log_event(self, event_type, **kwargs):
        t = self.task_clock.getTime() if self.task_clock else 0.0
        entry = {
            'participant': self.nom,
            'trial': self.current_trial,
            'time_s': round(t, 5),
            'event_type': event_type
        }
        entry.update(kwargs)
        self.records.append(entry)

    # ======================================================================
    # PHASES
    # ======================================================================

    def show_instructions(self):
        self.logger.info("Affichage des instructions")
        self.text_stim.text = (
            "Tâche Flanker\n\n"
            "Indiquez la direction de la flèche CENTRALE.\n\n"
            "← : touche LEFT\n"
            "→ : touche RIGHT\n\n"
            "Appuyez sur une touche pour commencer."
        )
        self.text_stim.draw()
        self.win.flip()

        event.waitKeys(keyList=['space', 'return', self.keys['quit']])
        if event.getKeys(keyList=[self.keys['quit']]):
            should_quit(self.win, quit=True)

    def wait_for_trigger(self):
        self.logger.info("Attente du trigger scanner")
        self.text_stim.text = f"En attente du trigger ('{self.keys['trigger']}')"
        self.text_stim.draw()
        self.win.flip()

        keys = event.waitKeys(keyList=[self.keys['trigger'], self.keys['quit']])
        if keys[0] == self.keys['quit']:
            should_quit(self.win, quit=True)

        self.task_clock = core.Clock()
        self.log_event('trigger_received')
        self.logger.info("Trigger reçu – T0 démarré")

    # ======================================================================
    # TRIAL GENERATION
    # ======================================================================

    @staticmethod
    def generate_trial():
        directions = ['left', 'right']
        target = random.choice(directions)
        congruent = random.choice([True, False])

        if congruent:
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

        return stim, target, congruent

    # ======================================================================
    # TRIAL EXECUTION
    # ======================================================================

    def run_trial(self, trial_idx):
        self.current_trial = trial_idx
        stim, target, congruent = self.generate_trial()

        # ---------------- FIXATION ----------------
        self.fixation.draw()
        self.win.flip()
        core.wait(0.5)

        # ---------------- STIMULUS ----------------
        self.text_stim.text = stim
        self.text_stim.draw()
        self.win.flip()

        self.trial_clock.reset()
        self.log_event(
            'stim_onset',
            stimulus=stim,
            target=target,
            congruent=congruent
        )

        event.clearEvents()
        response, rt = None, None

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
            core.wait(0.001)

        self.win.flip()
        accurate = (response == target)

        self.log_event(
            'response',
            response=response if response else 'none',
            rt=rt,
            accurate=accurate
        )

        self.logger.info(
            f"Trial {trial_idx:02d} | {stim} | "
            f"Congruent={congruent} | Resp={response} | "
            f"Acc={accurate} | RT={rt}"
        )

        core.wait(self.isi)

    # ======================================================================
    # RUN
    # ======================================================================

    def run(self):
        try:
            self.show_instructions()
            self.wait_for_trigger()

            for t in range(1, self.n_trials + 1):
                should_quit(self.win)
                self.run_trial(t)

        finally:
            self.save_results()

        return

    # ======================================================================
    # SAVE
    # ======================================================================

    def save_results(self):
        if not self.enregistrer or not self.records:
            return

        fname = f"{self.nom}_Flanker_{self.start_timestamp}.csv"
        path = os.path.join(self.data_dir, fname)

        keys = set()
        for r in self.records:
            keys.update(r.keys())

        fieldnames = sorted(keys)

        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.records)

        self.logger.info(f"Données sauvegardées : {path}")
