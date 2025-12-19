from psychopy import visual, event, core, gui
import logging
import random, csv, os
import sys
import time

# =============================================================================
# UTILS & HARDWARE FALLBACK
# =============================================================================
try:
    from utils.utils import should_quit, get_logger
    from hardware.parport import ParPort, DummyParPort
except ImportError:
    def should_quit(win, quit=False):
        if quit:
            win.close()
            core.quit()

    def get_logger():
        l = logging.getLogger('RewardTask')
        if not l.handlers:
            l.setLevel(logging.INFO)
            h = logging.StreamHandler(sys.stdout)
            h.setFormatter(logging.Formatter('[%(asctime)s] %(message)s'))
            l.addHandler(h)
        return l
            
    class DummyParPort:
        def send_trigger(self, code):
            print(f"[TRIGGER] {code}")
            
    class ParPort(DummyParPort):
        def __init__(self, address=None, mode='dummy'): pass

# =============================================================================
# CLASSE DE TÂCHE
# =============================================================================

class DoorReward:
    def __init__(self, win, nom, session, n_trials, reward_probability, mode, enregistrer=True, **kwargs):
        self.win = win
        self.nom = nom
        self.session = session
        self.n_trials = n_trials
        self.reward_prob = reward_probability
        self.mode = mode
        self.enregistrer = enregistrer
        
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
        
        self.logger = get_logger()
        self.ParPort = ParPort(mode=mode) 
        
        self.codes = {
            'start_exp': 10, 'rest_start': 20, 'rest_end': 21,
            'doors_onset': 30, 'choice_made': 40, 'door_open': 50,
            'feedback_win': 60, 'feedback_neutral': 61, 'timeout': 99
        }
        if mode == "fmri":
            self.keys = {
                'choices': ['b', 'y', 'g'],
                'trigger': 't',
                'quit': 'escape'
            }
            
        else :
            self.keys = {
                'choices': ['a', 'z', 'e'],
                'trigger': 't',
                'quit': 'escape'
            }
        
        self.task_clock = None 
        self._setup_visuals()

    def _setup_visuals(self):
        # Chemins
        self.img_closed_path = os.path.join(self.root_dir, 'image', 'porte_ferme.png')
        self.img_open_path = os.path.join(self.root_dir, 'image', 'porte_ouverte.png')

        self.door_positions = [(-0.5, 0), (0, 0), (0.5, 0)]
        self.doors_closed_stim = [] 
        self.doors_open_stim = []   
        
        for pos in self.door_positions:
            # Porte FERMÉE
            stim_closed = visual.ImageStim(
                self.win, image=self.img_closed_path, 
                pos=pos, size=(0.3, 0.6), interpolate=True
            )
            self.doors_closed_stim.append(stim_closed)
            
            # Porte OUVERTE
            stim_open = visual.ImageStim(
                self.win, image=self.img_open_path, 
                pos=pos, size=(0.3, 0.6), interpolate=True
            )
            self.doors_open_stim.append(stim_open)

        # Textes
        self.feedback_stim = visual.TextStim(self.win, text="", height=0.15, bold=True)
        self.score_stim = visual.TextStim(self.win, text="Total: 0 €", pos=(0, -0.6), height=0.06)
        self.fixation = visual.TextStim(self.win, text='+', color='white', height=0.12)
        self.text_instr = visual.TextStim(self.win, text="", color='white', height=0.06, wrapWidth=1.5)

    def log_step(self, event_type, **kwargs):
        self.is_data_saved = False
        current_time = self.task_clock.getTime() if self.task_clock else 0.0
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
        
        event.waitKeys(keyList=[self.keys['trigger']])
        self.task_clock = core.Clock() 
        self.ParPort.send_trigger(self.codes['start_exp'])
        self.log_step('experiment_start')

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
        
        # --- 1. AFFICHAGE PORTES FERMÉES ---
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
            core.wait(1.0)
            return

        key_pressed, rt_abs = keys[0]
        rt = rt_abs - onset_time
        if key_pressed == self.keys['quit']: should_quit(self.win, quit=True)
        
        choice_idx = self.keys['choices'].index(key_pressed)
        
        self.ParPort.send_trigger(self.codes['choice_made'])
        self.log_step('response_made', key=key_pressed, choice_idx=choice_idx, rt=rt)

        # --- 3. OUVERTURE IMMÉDIATE (SANS TEXTE) ---
        # On redessine tout de suite : la porte choisie ouverte, les autres fermées
        for i in range(3):
            if i == choice_idx:
                self.doors_open_stim[i].draw() # Porte ouverte
            else:
                self.doors_closed_stim[i].draw() # Portes fermées
        
        self.score_stim.draw()
        self.win.flip()
        
        # On envoie un trigger pour dire "la porte s'est ouverte"
        self.ParPort.send_trigger(self.codes['door_open'])
        
        # --- 4. PETIT DÉLAI (Délai avant l'apparition du chiffre) ---
        # C'est ici que ça "attend" avec la porte ouverte mais sans le chiffre
        delay_before_text = random.uniform(1.0, 2.0) 
        core.wait(delay_before_text)

        # --- 5. RÉSULTAT (GAIN) ---
        is_win = random.random() < self.reward_prob
        
        if is_win:
            gain = 10 
            self.total_gain += gain
            msg = "+ 10 €"
            col = 'lime'
            trig = self.codes['feedback_win']
        else:
            gain = 0
            msg = "0 €"
            col = 'grey'
            trig = self.codes['feedback_neutral']

        self.ParPort.send_trigger(trig)
        self.log_step('feedback_outcome', is_win=is_win, gain=gain)

        # On redessine la scène (Porte ouverte) + LE TEXTE maintenant
        for i in range(3):
            if i == choice_idx:
                self.doors_open_stim[i].draw()
            else:
                self.doors_closed_stim[i].draw()
            
        self.feedback_stim.text = msg
        self.feedback_stim.color = col
        self.feedback_stim.pos = (self.door_positions[choice_idx][0], 0) 
        self.feedback_stim.draw()
        
        self.score_stim.text = f"Total: {self.total_gain} €"
        self.score_stim.draw()
        
        self.win.flip()
        
        # Temps de lecture du résultat
        core.wait(1.5)

        # --- 6. ITI ---
        self.fixation.draw()
        self.win.flip()
        iti = random.uniform(1.0, 2.5)
        core.wait(iti)

    def save_results(self):
        if self.is_data_saved: return 

        output_dir = os.path.join(self.data_dir, "doorreward")
        
        os.makedirs(output_dir, exist_ok=True)

        fname = f"{self.nom}_Reward_Sess{self.session}_{self.start_timestamp}.csv"
        path = os.path.join(output_dir, fname)
        
        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                if self.global_records:
                    all_keys = set()
                    for r in self.global_records:
                        all_keys.update(r.keys())

                    fieldnames = sorted(list(all_keys))
                    
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(self.global_records)
            
            self.is_data_saved = True
            print(f"Sauvegarde réussie : {path}")
            
        except Exception as e:
            print(f"Erreur sauvegarde : {e}")

    def run(self):
        self.show_instructions()
        self.show_resting_state(2.0)
        for i in range(1, self.n_trials + 1):
            self.run_trial(i)
        self.show_resting_state(2.0)
        self.save_results()
        
        end_txt = visual.TextStim(self.win, text=f"Fini !\nGains totaux : {self.total_gain} €", height=0.1)
        end_txt.draw()
        self.win.flip()
        core.wait(2.0)

