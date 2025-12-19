from psychopy import visual, event, core, gui
import logging
import random, csv, os
import sys
import time

# On utilise tes modules customs
from utils.hardware_manager import setup_hardware
from utils.utils import should_quit
from utils.logger import get_logger  # <--- On prend le VRAI logger stylé

# =============================================================================
# CLASSE DE TÂCHE
# =============================================================================

class DoorReward:
    def __init__(self, win, nom, session, n_trials, reward_probability, mode, enregistrer=True, eyetracker_actif=False, parport_actif=False, **kwargs):
        self.win = win
        self.nom = nom
        self.session = session
        self.n_trials = n_trials
        self.reward_prob = reward_probability
        self.mode = mode
        self.enregistrer = enregistrer
        self.eyetracker_actif = eyetracker_actif
        self.parport_actif = parport_actif

        # Gestion des chemins
        self.root_dir = os.path.dirname(os.path.abspath(__file__))
        if os.path.basename(self.root_dir) == 'tasks':
            self.root_dir = os.path.dirname(self.root_dir)
            
        self.data_dir = os.path.join(self.root_dir, 'data')
        if not os.path.exists(self.data_dir): os.makedirs(self.data_dir)
        
        self.global_records = []
        self.total_gain = 0
        self.start_timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.is_data_saved = False
        self.current_trial_idx = 0
        
        # --- LOGGER ---
        self.logger = get_logger() # On récupère l'instance singleton
        
        # --- HARDWARE ---
        self.ParPort, self.EyeTracker = setup_hardware(self.parport_actif, self.eyetracker_actif, win)
        
        # Init EyeTracker (Nom fichier: DR + 3 lettres + session -> DR_CLE01)
        self.EyeTracker.initialize(file_name=f"DR_{nom[:3]}{session}")
        
        self.codes = {
            'start_exp': 10, 'rest_start': 20, 'rest_end': 21,
            'doors_onset': 30, 'choice_made': 40, 'door_open': 50,
            'feedback_win': 60, 'feedback_neutral': 61, 'timeout': 99
        }
        if mode == "fmri":
            self.keys = {'choices': ['b', 'y', 'g'], 'trigger': 't', 'quit': 'escape'}
        else :
            self.keys = {'choices': ['a', 'z', 'e'], 'trigger': 't', 'quit': 'escape'}
        
        self.task_clock = None 
        self._setup_visuals()

    def _setup_visuals(self):
        self.img_closed_path = os.path.join(self.root_dir, 'image', 'porte_ferme.png')
        self.img_open_path = os.path.join(self.root_dir, 'image', 'porte_ouverte.png')

        self.door_positions = [(-0.5, 0), (0, 0), (0.5, 0)]
        self.doors_closed_stim = [] 
        self.doors_open_stim = []   
        
        for pos in self.door_positions:
            stim_closed = visual.ImageStim(self.win, image=self.img_closed_path, pos=pos, size=(0.3, 0.6), interpolate=True)
            self.doors_closed_stim.append(stim_closed)
            stim_open = visual.ImageStim(self.win, image=self.img_open_path, pos=pos, size=(0.3, 0.6), interpolate=True)
            self.doors_open_stim.append(stim_open)

        self.feedback_stim = visual.TextStim(self.win, text="", height=0.15, bold=True)
        self.score_stim = visual.TextStim(self.win, text="Total: 0 €", pos=(0, -0.6), height=0.06)
        self.fixation = visual.TextStim(self.win, text='+', color='white', height=0.12)
        self.text_instr = visual.TextStim(self.win, text="", color='white', height=0.06, wrapWidth=1.5)

    def log_step(self, event_type, **kwargs):
        self.is_data_saved = False
        current_time = self.task_clock.getTime() if self.task_clock else 0.0
        
        # On envoie aussi un message dans le fichier EDF (EyeLink) pour marquer l'event
        self.EyeTracker.send_message(f"TRIAL {self.current_trial_idx} {event_type}")
        
        entry = {
            'participant': self.nom,
            'session': self.session,
            'trial': self.current_trial_idx,
            'time_s': round(current_time, 5),
            'event_type': event_type,
            'total_gain': self.total_gain
        }
        entry.update(kwargs)
        self.global_records.append(entry)

    def check_for_ttl(self):
        if self.task_clock:
            keys = event.getKeys(keyList=[self.keys['trigger']], timeStamped=self.task_clock)
            for k, t in keys:
                self.log_step('ttl_pulse', real_time=t)

    # =========================================================================
    # TASK PHASES
    # =========================================================================

    def show_instructions(self):
        instr = (
            "Tâche de Récompense\n\n"
            "3 portes vont apparaître.\n"
            "Choisissez-en une pour trouver le trésor.\n\n"
            f"Touches : {self.keys['choices']}\n\n"
            "En attente du Trigger..."
        )
        self.text_instr.text = instr
        self.text_instr.draw()
        self.win.flip()
        
        self.logger.log("Waiting for trigger...")
        event.waitKeys(keyList=[self.keys['trigger']])
        
        self.task_clock = core.Clock() 
        self.ParPort.send_trigger(self.codes['start_exp'])
        self.log_step('experiment_start')
        
        self.EyeTracker.start_recording()
        self.EyeTracker.send_message("START_EXP")
        self.logger.ok("Experiment Started")

    def show_resting_state(self, duration_s):
        self.ParPort.send_trigger(self.codes['rest_start'])
        self.log_step('rest_start')
        timer = core.CountdownTimer(duration_s)
        while timer.getTime() > 0:
            self.fixation.draw()
            self.win.flip()
            self.check_for_ttl()
            if event.getKeys(keyList=[self.keys['quit']]): should_quit(self.win, quit=True)
            core.wait(0.1)
        self.ParPort.send_trigger(self.codes['rest_end'])
        self.log_step('rest_end')

    def run_trial(self, trial_num):
        self.current_trial_idx = trial_num
        
        # --- 1. PORTES FERMEES ---
        for d in self.doors_closed_stim:
            d.opacity = 1
            d.draw()
        self.score_stim.draw()
        self.win.flip()
        
        onset_time = self.task_clock.getTime()
        self.ParPort.send_trigger(self.codes['doors_onset'])
        self.log_step('stim_onset_doors')

        # --- 2. CHOIX ---
        event.clearEvents()
        keys = event.waitKeys(maxWait=4.0, keyList=self.keys['choices'] + [self.keys['quit']], timeStamped=self.task_clock)
        
        if not keys:
            self.ParPort.send_trigger(self.codes['timeout'])
            self.log_step('timeout')
            self.feedback_stim.text = "Trop lent !"
            self.feedback_stim.color = 'red'
            self.feedback_stim.pos = (0, 0)
            self.feedback_stim.draw()
            self.win.flip()
            self.logger.warn(f"Trial {trial_num} Timeout")
            core.wait(1.0)
            return

        key_pressed, rt_abs = keys[0]
        rt = rt_abs - onset_time
        if key_pressed == self.keys['quit']: should_quit(self.win, quit=True)
        
        choice_idx = self.keys['choices'].index(key_pressed)
        
        self.ParPort.send_trigger(self.codes['choice_made'])
        self.log_step('response_made', key=key_pressed, choice_idx=choice_idx, rt=rt)

        # --- 3. OUVERTURE ---
        for i in range(3):
            if i == choice_idx: self.doors_open_stim[i].draw()
            else: self.doors_closed_stim[i].draw()
        self.score_stim.draw()
        self.win.flip()
        self.ParPort.send_trigger(self.codes['door_open'])
        
        core.wait(random.uniform(1.0, 2.0))

        # --- 5. RESULTAT ---
        is_win = random.random() < self.reward_prob
        gain = 10 if is_win else 0
        if is_win:
            self.total_gain += gain
            msg, col, trig = "+ 10 €", 'lime', self.codes['feedback_win']
        else:
            msg, col, trig = "0 €", 'grey', self.codes['feedback_neutral']

        self.ParPort.send_trigger(trig)
        self.log_step('feedback_outcome', is_win=is_win, gain=gain)

        # Dessin Feedback
        for i in range(3):
            if i == choice_idx: self.doors_open_stim[i].draw()
            else: self.doors_closed_stim[i].draw()
        self.feedback_stim.text = msg
        self.feedback_stim.color = col
        self.feedback_stim.pos = (self.door_positions[choice_idx][0], 0) 
        self.feedback_stim.draw()
        self.score_stim.text = f"Total: {self.total_gain} €"
        self.score_stim.draw()
        self.win.flip()
        
        # --- CUSTOM LOGGING (LE VOILA) ---
        outcome_str = "WIN " if is_win else "LOSE"
        self.logger.log(
            f"Trial {trial_num:>2}/{self.n_trials:<2} | "
            f"Choice: Door {choice_idx+1} ({key_pressed.upper()}) | "
            f"RT: {rt:.3f}s | "
            f"Outcome: {outcome_str:<4} ({msg:>6}) | "
            f"Total: {self.total_gain:>3} €"
        )
        
        core.wait(1.5)

        # --- 6. ITI ---
        self.fixation.draw()
        self.win.flip()
        core.wait(random.uniform(1.0, 2.5))

    def save_results(self):
        if self.is_data_saved: return 

        output_dir = os.path.join(self.data_dir, "doorreward")
        os.makedirs(output_dir, exist_ok=True)

        fname = f"{self.nom}_Reward_Sess{self.session}_{self.start_timestamp}.csv"
        path = os.path.join(output_dir, fname)
        
        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                if self.global_records:
                    all_keys = set().union(*(r.keys() for r in self.global_records))
                    writer = csv.DictWriter(f, fieldnames=sorted(list(all_keys)))
                    writer.writeheader()
                    writer.writerows(self.global_records)
            
            self.is_data_saved = True
            # Log vert pour succès
            self.logger.ok(f"Sauvegarde réussie : {path}")
            
        except Exception as e:
            # Log rouge pour erreur
            self.logger.err(f"Erreur sauvegarde : {e}")

    def run(self):
        self.show_instructions()
        self.show_resting_state(2.0)
        for i in range(1, self.n_trials + 1):
            self.run_trial(i)
        self.show_resting_state(2.0)
        
        self.EyeTracker.stop_recording()
        self.EyeTracker.send_message("END_EXP")
        # On passe le dossier de sortie pour récupérer le EDF
        self.EyeTracker.close_and_transfer_data(os.path.join(self.data_dir, "doorreward"))
        
        self.save_results()
        
        end_txt = visual.TextStim(self.win, text=f"Fini !\nGains totaux : {self.total_gain} €", height=0.1)
        end_txt.draw()
        self.win.flip()
        core.wait(2.0)