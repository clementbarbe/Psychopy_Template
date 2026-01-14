"""
N-Back Task (fMRI / Behavioral) 
-------------------------------------------------------
Ce script exécute une tâche de mémoire de travail (N-Back) sous PsychoPy.

  - Timing "Non-Slip" pour éviter la dérive temporelle cumulative.
  - Séparation stricte de la phase Stimulus et de la phase ISI.
  - Modularity N-Level robuste.
  - Optimisation des appels de garbage collection.

Auteur : [BARBE Clément / CENIR]
Date : Janvier 2026
"""

import logging
import random
import csv
import os
import sys
import gc
from datetime import datetime
from psychopy import visual, event, core
from utils.utils import should_quit

# --- Hardware Simulation ---
try:
    from hardware.parport import ParPort, DummyParPort
except ImportError:
    class DummyParPort:
        def send_trigger(self, code): pass
    ParPort = DummyParPort

class NBack:
    """
    Contrôleur principal de la tâche N-Back.
    Mise à jour : Logs temps réel + Fix Sauvegarde CSV.
    """

    def __init__(self, win, nom, session='01', enregistrer=True, 
                 N=2, n_trials=30, target_ratio=0.3,
                 stim_dur=0.5, isi=1.5, data_dir='data/nback',
                 port_address=0x378, parport_actif=True, screenid=1, **kwargs):
        
        self._setup_logger()
        self.win = win
        self.nom = nom
        self.session = session
        self.enregistrer = enregistrer
        
        self.N = int(N)
        self.n_trials = int(n_trials)
        self.target_ratio = float(target_ratio)
        self.stim_dur = float(stim_dur)
        self.isi = float(isi)
        
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.start_timestamp = datetime.now().strftime('%Y%m%d_%H%M')

        # Hardware setup
        self.parport_actif = parport_actif
        if parport_actif:
            try:
                from hardware.parport import ParPort
                self.ParPort = ParPort()
            except:
                self.ParPort = DummyParPort()
        else:
            self.ParPort = DummyParPort()
            
        self.codes = {'start_exp': 255, 'stim_target': 10, 'stim_nontarget': 20, 'response': 128, 'end_exp': 250}
        
        # Stimuli
        self.stim_text = visual.TextStim(self.win, text='', color='white', height=0.25, font='Arial')
        self.fixation = visual.TextStim(self.win, text='+', color='white', height=0.1)
        self.instr_text = visual.TextStim(self.win, text='', color='white', height=0.06, wrapWidth=1.8)
        
        self.global_records = []
        self.sequence = []
        self.task_clock = core.Clock()
        self.keys = {'target': 'space', 'trigger': 't', 'quit': 'escape'}

    def _setup_logger(self):
        self.logger = logging.getLogger('NBackTask')
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            # Format simplifié pour la console pour éviter d'être trop verbeux avec le timestamp à chaque ligne
            handler.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(handler)

    def log_step(self, event_type, **kwargs):
        t = self.task_clock.getTime()
        entry = {'participant': self.nom, 'session': self.session, 'N_level': self.N, 'time_s': round(t, 5), 'event_type': event_type}
        entry.update(kwargs)
        self.global_records.append(entry)

    def generate_sequence(self):
        # ... (Identique à la version précédente) ...
        possible_letters = list("BCDFGHJKLMNPQRSTVXZ")
        seq = []
        is_target = []
        for i in range(self.N):
            char = random.choice(possible_letters)
            if i > 0 and char == seq[-1]: char = random.choice([l for l in possible_letters if l != seq[-1]])
            seq.append(char)
            is_target.append(False)
        
        remaining = self.n_trials - self.N
        n_targets = int(remaining * self.target_ratio)
        conditions = [True] * n_targets + [False] * (remaining - n_targets)
        random.shuffle(conditions)

        for is_t in conditions:
            target_letter = seq[-self.N]
            if is_t:
                seq.append(target_letter)
                is_target.append(True)
            else:
                pool = [l for l in possible_letters if l != target_letter]
                seq.append(random.choice(pool))
                is_target.append(False)
        self.sequence = list(zip(seq, is_target))
        # On remet le log standard avec timestamp juste pour l'init
        print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Séquence générée (N={self.N}, Trials={len(self.sequence)})")

    def run_trial(self, trial_idx, letter, is_target, trial_start_global_time):
        should_quit(self.win)
        gc.disable()

        trig = self.codes['stim_target'] if is_target else self.codes['stim_nontarget']
        self.stim_text.text = letter
        
        t_stim_end = trial_start_global_time + self.stim_dur
        t_trial_end = trial_start_global_time + self.stim_dur + self.isi

        # 1. Attente précise du début théorique (Spin-lock)
        while self.task_clock.getTime() < trial_start_global_time: 
            pass

        # 2. FLIP SYNCHRONISÉ
        self.win.callOnFlip(self.ParPort.send_trigger, trig)
        self.stim_text.draw()
        self.win.flip() 
        
        # --- FIX CRITIQUE ---
        # On capture le temps MAINTENANT selon l'horloge de la tâche (relatif au Reset)
        # au lieu de prendre le timestamp absolu de win.flip()
        onset_real = self.task_clock.getTime() 
        
        # Le delay est maintenant la différence entre le temps réel mesuré et le temps théorique
        delay_ms = (onset_real - trial_start_global_time) * 1000

        self.log_step('stimulus_onset', trial=trial_idx, letter=letter, is_target=is_target, delay_ms=delay_ms)

        response_data = {'key': None, 'rt': None, 'acc': None, 'sdt': None}
        
        # Phase Stimulus
        while self.task_clock.getTime() < t_stim_end:
            # Optimisation: on vérifie les touches SEULEMENT si pas encore répondu
            if response_data['key'] is None:
                # timeStamped=self.task_clock assure que 't' est compatible avec 'onset_real'
                keys = event.getKeys(keyList=[self.keys['target'], self.keys['quit']], timeStamped=self.task_clock)
                if keys: self._process_response(keys[0], onset_real, is_target, response_data)
        
        # Phase ISI (Croix)
        self.fixation.draw()
        self.win.flip()
        
        while self.task_clock.getTime() < t_trial_end:
            if response_data['key'] is None:
                keys = event.getKeys(keyList=[self.keys['target'], self.keys['quit']], timeStamped=self.task_clock)
                if keys: self._process_response(keys[0], onset_real, is_target, response_data)
            core.wait(0.001)

        # Fin de l'essai : Traitement de la non-réponse
        if response_data['key'] is None:
            acc = 0 if is_target else 1
            sdt = "MISS" if is_target else "CR"
            self.log_step('response_none', trial=trial_idx, sdt=sdt, accuracy=acc)
            
            rt_display = 0.0
            fb_str = "MISS" if is_target else "OK"
            col_fb = "\033[91m" if is_target else "\033[92m" 
        else:
            rt_display = response_data['rt']
            sdt = response_data['sdt']
            is_correct = response_data['acc'] == 1
            fb_str = sdt
            col_fb = "\033[92m" if is_correct else "\033[91m"

        gc.enable()
        
        # LOGGER CORRIGÉ
        cond_str = "TARGET" if is_target else "______"
        reset_col = "\033[0m"
        
        # Le delay devrait maintenant être entre 0.0ms et 16.0ms (durée d'une frame à 60Hz)
        log_msg = (f"Trial {trial_idx:>2}/{self.n_trials:<2} | "
                   f"Condition: {cond_str:<7} | "
                   f"Delay: {delay_ms:>5.1f}ms | "
                   f"RT: {rt_display:.3f}s {col_fb}{fb_str:<4}{reset_col}")
        
        self.logger.info(log_msg)

    def _process_response(self, key_tuple, onset_time, is_target, data):
        k, t = key_tuple
        if k == self.keys['quit']: should_quit(self.win, quit=True)
        
        self.ParPort.send_trigger(self.codes['response'])
        rt = t - onset_time
        
        acc = 1 if is_target else 0
        sdt = "HIT" if is_target else "FA" # False Alarm
        
        data['key'] = k
        data['rt'] = rt
        data['acc'] = acc
        data['sdt'] = sdt
        
        self.log_step('response_given', key=k, rt=rt, sdt=sdt, accuracy=acc)

    def show_instructions(self):
        self.instr_text.text = (f"Tâche {self.N}-BACK\n\nAppuyez si la lettre est identique\nà {self.N} étapes avant.\n\nAppuyez pour commencer.")
        self.instr_text.draw()
        self.win.flip()
        event.waitKeys()

    def wait_for_trigger(self):
        self.instr_text.text = f"Attente Trigger IRM ('{self.keys['trigger']}')"
        self.instr_text.draw()
        self.win.flip()
        event.waitKeys(keyList=[self.keys['trigger']])
        self.task_clock.reset()
        self.ParPort.send_trigger(self.codes['start_exp'])
        self.log_step('experiment_start')

    def save_data(self):
        """
        CORRECTION DU BUG DICTWRITER
        """
        if self.enregistrer and self.global_records:
            fname = f"nback_{self.nom}_S{self.session}_{self.start_timestamp}.csv"
            path = os.path.join(self.data_dir, fname)
            try:
                # 1. On récupère TOUTES les clés uniques présentes dans l'historique
                all_keys = set()
                for rec in self.global_records:
                    all_keys.update(rec.keys())
                
                # 2. On trie pour avoir les colonnes importantes au début
                priority_cols = ['participant', 'session', 'N_level', 'trial', 'event_type', 'time_s', 'letter', 'is_target', 'rt', 'sdt', 'accuracy']
                fieldnames = [k for k in priority_cols if k in all_keys] + [k for k in all_keys if k not in priority_cols]

                with open(path, 'w', newline='') as f:
                    w = csv.DictWriter(f, fieldnames=fieldnames)
                    w.writeheader()
                    w.writerows(self.global_records)
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] SUCCESS: Données sauvegardées dans {path}")

            except Exception as e:
                print(f"ERROR CRITIQUE SAVE: {e}")
                # Backup de secours en raw
                with open(path + ".bak", "w") as f:
                    f.write(str(self.global_records))

    def run(self):
        try:
            self.generate_sequence()
            self.show_instructions()
            self.wait_for_trigger()
            
            self.fixation.draw()
            self.win.flip()
            
            # Start avec 2s de pré-rest
            next_trial_time = 2.0 
            while self.task_clock.getTime() < next_trial_time: core.wait(0.001)
            
            for i, (l, t) in enumerate(self.sequence):
                self.run_trial(i+1, l, t, next_trial_time)
                next_trial_time += (self.stim_dur + self.isi)
                
            self.fixation.draw()
            self.win.flip()
            core.wait(2.0)
            
        finally:
            self.save_data()