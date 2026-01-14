"""
Stroop Task (fMRI / Behavioral)
-------------------------------------------
Ce script exécute une tâche de Stroop Task sous PsychoPy.
Elle possède aussi une option Go / No Go et des paramètres modulaires.

Auteur : [Clément BARBE/ CENIR]
Date de mise en prod : Décembre 2025
"""

import logging
import random
import csv
import os
import sys
import gc
from datetime import datetime

# --- PsychoPy Imports ---
from psychopy import visual, event, core

# --- Local Imports (Mock) ---
try:
    from utils.utils import should_quit
    from hardware.parport import ParPort, DummyParPort
except ImportError:
    def should_quit(win, quit=False):
        if event.getKeys(['escape']):
            if quit: core.quit()
            return True
        return False
    class ParPort:
        def __init__(self, addr): pass
        def send_trigger(self, code): pass
    class DummyParPort(ParPort): pass

class Stroop:
    def __init__(self, win, nom, session='01', enregistrer=True, screenid=1, mode='fmri',
                 n_trials=80,
                 n_choices=4,  
                 go_nogo=False, # <--- NOUVEAU PARAMÈTRE
                 stim_dur=2.0,
                 isi_range=(1500, 2500),
                 data_dir='data/stroop_task',
                 port_address=0x378,
                 parport_actif=True): 
        
        # 1. INITIALISATION
        self._setup_logger()
        self.win = win
        self.frame_rate = win.getActualFrameRate() or 60.0
        self.start_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Scale resolution
        self.text_scale = 1.5 if self.win.size[1] > 1200 else 1.0

        # 2. PARAMÈTRES
        self.nom = nom
        self.session = session
        self.enregistrer = enregistrer
        self.mode = mode
        
        # Validation
        if n_choices not in [2, 3, 4]:
            raise ValueError("n_choices doit être 2, 3 ou 4.")
        self.n_choices = n_choices
        
        # Mode Go/No-Go
        self.go_nogo = go_nogo
        
        self.n_trials = n_trials
        self.stim_dur = stim_dur
        self.isi_range = (isi_range[0]/1000.0, isi_range[1]/1000.0)
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

        self.logger.info(f"Config: {self.n_choices} Choix | Go/No-Go: {self.go_nogo}")

        # -- MASTER CONFIGURATION --
        self.MASTER_CONFIG = [
            {'word': 'ROUGE',  'ink': 'red',    'hex': '#FF0000', 'key_fmri': '1', 'key_behav': 'r'},
            {'word': 'VERT',   'ink': 'green',  'hex': '#00FF00', 'key_fmri': '2', 'key_behav': 'v'},
            {'word': 'BLEU',   'ink': 'blue',   'hex': '#0088FF', 'key_fmri': '3', 'key_behav': 'b'},
            {'word': 'JAUNE',  'ink': 'yellow', 'hex': '#FFFF00', 'key_fmri': '4', 'key_behav': 'j'}
        ]
        
        # Active Config = Les cibles (Go)
        self.active_config = self.MASTER_CONFIG[:self.n_choices]
        
        # Set des couleurs cibles pour vérification rapide O(1)
        self.target_inks = set(item['ink'] for item in self.active_config)
        
        # Colors hex lookup (besoin de tout le monde si Go/NoGo)
        self.colors_hex = {item['ink']: item['hex'] for item in self.MASTER_CONFIG}
        
        # 3. MATÉRIEL
        if self.mode != 'fmri': parport_actif = False

        if parport_actif:
            try: self.ParPort = ParPort(port_address)
            except: self.ParPort = DummyParPort()
        else:
            self.ParPort = DummyParPort()
            
        self.codes = {
            'start_exp': 255, 'rest_start': 200, 'rest_end': 201, 
            'stim_congruent': 10, 'stim_incongruent': 11,
            'resp_correct': 100,      # Hit
            'resp_error': 101,        # Wrong Color (Go trial)
            'resp_miss': 102,         # Miss (Go trial)
            'resp_false_alarm': 103,  # Error (No-Go trial)
            'resp_correct_rej': 104,  # Correct (No-Go trial)
            'fixation': 5
        }

        self.global_records = [] 
        self.current_phase = 'setup'
        self._setup_keys()
        
        # 4. STIMULI
        self.stroop_stim = visual.TextStim(self.win, text='', height=0.15 * self.text_scale, bold=True)
        self.fixation = visual.TextStim(self.win, text='+', color='white', height=0.12 * self.text_scale)
        self.instr_stim = visual.TextStim(self.win, text='', color='white', height=0.05 * self.text_scale, wrapWidth=1.6)
        self.task_clock = None 

    def _setup_logger(self):
        self.logger = logging.getLogger('Stroop')
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter('[%(asctime)s] %(levelname)-8s : %(message)s', datefmt='%H:%M:%S')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _setup_keys(self):
        self.key_mapping = {}
        # On mappe uniquement les touches des choix actifs (Cibles)
        for item in self.active_config:
            ink = item['ink']
            key = item['key_fmri'] if self.mode == 'fmri' else item['key_behav']
            self.key_mapping[key] = ink
                
        self.trigger_key = 't'
        self.quit_key = 'escape'
        self.response_keys = list(self.key_mapping.keys())

    def log_step(self, event_type, trial=None, **kwargs):
        current_time = self.task_clock.getTime() if self.task_clock else 0.0
        entry = {
            'participant': self.nom,
            'session': self.session,
            'n_choices': self.n_choices,
            'go_nogo': self.go_nogo,
            'phase': self.current_phase,
            'trial': trial,
            'time_s': round(current_time, 5),
            'event_type': event_type
        }
        entry.update(kwargs)
        self.global_records.append(entry)

    def check_ttl(self):
        if self.task_clock and self.mode == 'fmri':
            keys = event.getKeys(keyList=[self.trigger_key], timeStamped=True)
            for k, t in keys:
                self.log_step('ttl_pulse', real_time=t)

    # =========================================================================
    # TRIAL LOGIC
    # =========================================================================

    def run_trial(self, trial_idx, word, ink, congruent, trial_type):
        """
        trial_type: 'GO' ou 'NOGO'
        """
        should_quit(self.win)
        gc.disable() 
        
        self.stroop_stim.text = word
        self.stroop_stim.color = self.colors_hex[ink]
        
        # Trigger stimulus
        trigger_code = self.codes['stim_congruent'] if congruent else self.codes['stim_incongruent']
        self.log_step('trial_start', trial=trial_idx, word=word, ink=ink, 
                      congruent=congruent, trial_type=trial_type)

        # Fixation
        self.fixation.draw()
        self.win.flip()

        # Stimulus Onset
        self.stroop_stim.draw()
        self.win.callOnFlip(self.ParPort.send_trigger, trigger_code)
        
        event.clearEvents(eventType='keyboard') 
        onset_time = self.win.flip()
        self.log_step('stim_onset', onset_time=onset_time)

        # Response Collection
        # Note: En Go/No-Go, on attend potentiellement que le temps s'écoule sans réponse.
        keys = event.waitKeys(maxWait=self.stim_dur, keyList=self.response_keys + [self.quit_key], timeStamped=True)
        
        resp_key = None
        rt = None
        
        if keys:
            k, t = keys[0]
            if k == self.quit_key: should_quit(self.win, quit=True)
            resp_key = k
            rt = t - onset_time
            # Feedback visuel immédiat
            self.fixation.draw()
            self.win.flip()
        else:
            # Timeout (Pas de réponse)
            self.fixation.draw()
            self.win.flip()

        # --- SCORING COMPLEXE ---
        acc = 0
        status = "UNKNOWN"
        trig_out = 0

        if trial_type == 'GO':
            if resp_key:
                user_color = self.key_mapping.get(resp_key)
                if user_color == ink:
                    acc = 1
                    status = "HIT"
                    trig_out = self.codes['resp_correct']
                else:
                    acc = 0
                    status = "ERROR_WRONG_KEY"
                    trig_out = self.codes['resp_error']
            else:
                acc = 0
                status = "MISS"
                trig_out = self.codes['resp_miss']

        elif trial_type == 'NOGO':
            if resp_key:
                # L'utilisateur a appuyé alors qu'il ne fallait pas
                acc = 0
                status = "FALSE_ALARM"
                trig_out = self.codes['resp_false_alarm']
            else:
                # L'utilisateur s'est abstenu correctement
                acc = 1
                status = "CORRECT_REJECTION"
                trig_out = self.codes['resp_correct_rej']

        # Envoi Trigger Réponse
        self.ParPort.send_trigger(trig_out)

        self.log_step('response', key=resp_key, rt=rt, accuracy=acc, status=status, trigger_sent=trig_out)
        self.logger.info(f"T{trial_idx}: {trial_type} | {word}/{ink} | {status}")

        gc.enable()
        gc.collect()

        # ISI
        isi = random.uniform(*self.isi_range)
        self.fixation.draw()
        self.win.callOnFlip(self.ParPort.send_trigger, self.codes['fixation'])
        self.win.flip()
        
        start_isi = self.task_clock.getTime()
        while (self.task_clock.getTime() - start_isi) < isi:
            self.check_ttl()
            if event.getKeys(keyList=[self.quit_key]): should_quit(self.win, quit=True)
            core.wait(0.02)

    def build_trials(self):
        """
        Construction intelligente des essais selon le mode.
        """
        trials = []
        
        # Source des mots et couleurs
        # Si Go/NoGo : On puise dans TOUT (MASTER)
        # Sinon : On puise seulement dans ACTIVE
        source_config = self.MASTER_CONFIG if self.go_nogo else self.active_config
        
        words_pool = [x['word'] for x in source_config]
        colors_pool = [x['ink'] for x in source_config]
        
        # Mapping Mot -> Encre théorique pour congruence
        fr_to_eng = {item['word']: item['ink'] for item in self.MASTER_CONFIG}

        base_trials = []
        
        for w in words_pool:
            for ink in colors_pool:
                is_congruent = (fr_to_eng[w] == ink)
                
                # Détermination du type d'essai
                # C'est un GO si la couleur de l'encre est dans nos cibles actives
                is_go = (ink in self.target_inks)
                trial_type = 'GO' if is_go else 'NOGO'
                
                base_trials.append({
                    'word': w, 
                    'ink': ink, 
                    'congruent': is_congruent,
                    'trial_type': trial_type
                })
        
        full_trials = base_trials * (self.n_trials // len(base_trials) + 1)
        full_trials = full_trials[:self.n_trials]
        random.shuffle(full_trials)
        
        # Log stats
        n_go = len([t for t in full_trials if t['trial_type'] == 'GO'])
        n_nogo = len(full_trials) - n_go
        self.logger.info(f"Génération: {len(full_trials)} essais. GO: {n_go}, NOGO: {n_nogo}")
        
        return full_trials

    # =========================================================================
    # INSTRUCTIONS & RUN (Reste inchangé sauf instructions)
    # =========================================================================

    def show_instructions(self):
        self.current_phase = 'instructions'
        
        # Récupération des noms des couleurs CIBLES
        cibles_txt = " / ".join([i['word'] for i in self.active_config])
        
        if self.go_nogo:
            consigne_speciale = (
                f"ATTENTION - TÂCHE GO / NO-GO\n\n"
                f"Répondez UNIQUEMENT si l'encre est :\n"
                f"--> {cibles_txt} <--\n\n"
                f"Si l'encre est une autre couleur :\n"
                f"NE FAITES RIEN (N'appuyez pas)."
            )
        else:
            consigne_speciale = (
                f"Couleurs possibles :\n{cibles_txt}"
            )

        msg = (
            "TACHE DE STROOP\n\n"
            "Indiquez la couleur de L'ENCRE\n"
            "(Ne lisez pas le mot).\n\n"
            f"{consigne_speciale}\n\n"
            "Répondez vite et précisément.\n"
            "Appuyez sur une touche pour commencer."
        )
        self.instr_stim.text = msg
        self.instr_stim.draw()
        self.win.flip()
        
        valid_instr_keys = ['space', 'return'] + self.response_keys + [self.quit_key]
        keys = event.waitKeys(keyList=valid_instr_keys)
        if self.quit_key in keys: should_quit(self.win, quit=True)

    def save_results(self):
        if not self.enregistrer or not self.global_records: return
        fname = f"Stroop_{'GNG' if self.go_nogo else 'STD'}_{self.n_choices}Choice_{self.nom}_{self.session}_{self.start_timestamp}.csv"
        path = os.path.join(self.data_dir, fname)
        cols = ['time_s', 'participant', 'session', 'n_choices', 'go_nogo', 'phase', 'trial', 
                'event_type', 'trial_type', 'word', 'ink', 'congruent', 'rt', 'accuracy', 'status', 'trigger_sent']
        all_keys = set().union(*(d.keys() for d in self.global_records))
        cols += [c for c in all_keys if c not in cols]
        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=cols)
                writer.writeheader()
                writer.writerows(self.global_records)
            self.logger.info(f"Données sauvegardées : {path}")
        except Exception as e:
            self.logger.error(f"Erreur Sauvegarde : {e}")

    def run(self):
        # Code d'exécution standard (similaire à v2.0)
        try:
            self.show_instructions() 
            if self.mode == 'fmri':
                self.current_phase = 'waiting_trigger'
                self.instr_stim.text = "En attente du trigger scanner ('t')"
                self.instr_stim.draw()
                self.win.flip()
                keys = event.waitKeys(keyList=[self.trigger_key, self.quit_key])
                if self.quit_key in keys: should_quit(self.win, quit=True)
                self.ParPort.send_trigger(self.codes['start_exp'])
                self.task_clock = core.Clock() 
            else:
                self.task_clock = core.Clock()

            self.current_phase = 'resting_start'
            self.ParPort.send_trigger(self.codes['rest_start'])
            self.fixation.draw()
            self.win.flip()
            core.wait(10.0) # Simplifié pour la lisibilité
            
            self.current_phase = 'task_run'
            trial_list = self.build_trials()
            
            for i, t in enumerate(trial_list, 1):
                self.run_trial(i, t['word'], t['ink'], t['congruent'], t['trial_type'])
            
            self.current_phase = 'resting_end'
            self.ParPort.send_trigger(self.codes['rest_end'])
            self.fixation.draw()
            self.win.flip()
            core.wait(10.0)
            
        except (SystemExit, KeyboardInterrupt): self.logger.info("Arrêt manuel.")
        except Exception as e: 
            self.logger.critical(f"Erreur : {e}")
            raise e
        finally:
            self.save_results()
            try: self.win.close()
            except: pass
