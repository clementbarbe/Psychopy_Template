from psychopy import visual, event, core, logging
import random, csv, os
from datetime import datetime
from utils.utils import should_quit
from hardware.parport import ParPort, DummyParPort

logging.console.setLevel(logging.ERROR)

class TemporalJudgement:
    def __init__(self, win, nom, session='01', enregistrer=True, screenid=1, mode='fmri', run_type='base',
                 n_trials_base=72, n_trials_block=24, n_trials_training=12, delays_ms=(200, 300, 400, 500, 600, 700),
                 response_options=(100, 200, 300, 400, 500, 600, 700, 800),
                 stim_isi_range=(1500, 2500),
                 data_dir='data/temporal_judgement',
                 port_address=0x378,
                 parport_actif=True): 
        
        # --- Experiment Parameters ---
        self.win = win
        self.frame_rate = win.getActualFrameRate(nIdentical=10, nMaxFrames=100, threshold=1)
        self.start_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        self.nom = nom
        self.session = session
        self.enregistrer = enregistrer
        self.screenid = screenid
        self.run_type = run_type
        self.mode = mode
        self.n_trials_base = n_trials_base
        self.n_trials_block = n_trials_block
        self.n_trials_training = n_trials_training
        self.delays_ms = list(delays_ms)
        self.response_values_ms = list(response_options)
        self.stim_isi_range = (stim_isi_range[0]/1000 , stim_isi_range[1]/1000 )
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

        if parport_actif:
            try:
                self.ParPort = ParPort(port_address)
                print(f"Tentative connexion Port Parallèle {hex(port_address)}...")
            except Exception as e:
                print(f"Échec réel : {e}")
                self.ParPort = DummyParPort()
        else:
            print("Mode simulation (Dummy) activé par configuration.")
            self.ParPort = DummyParPort()
            
        # --- DEFINITION DES CODES TRIGGERS ---
        self.codes = {
            'start_exp': 255,      
            'rest_start': 200,     
            'rest_end': 201,       

            'trial_active': 110,   
            'trial_passive': 111,  
            'action_bulb': 120,    
            'bulb_on': 130,        
            'response_prompt': 135,
            'response_given': 140, 
            'timeout': 199,        
            
            'crisis_prompt': 150,  
            'crisis_start': 151,
            'crisis_end': 152,
            'crisis_valid_prompt': 153,
            'crisis_res_success': 154,
            'crisis_res_fail': 155,
            'crisis_retry_yes': 156,
            'crisis_retry_no': 157
        }

        # --- Global Logging System ---
        self.global_records = [] 
        self.current_phase = 'setup'
        self.current_trial_idx = None 
        self.is_data_saved = False

        self._setup_keys()

        # --- Visual Stimuli Setup (INCHANGÉ) ---
        img_path = 'image'
        bulb_size = (0.45 * 0.9, 0.9 * 0.9)
        bulb_pos = (0.0, 0.0)
        
        if os.path.exists(os.path.join(img_path, 'bulbof.png')):
            self.bulb_off_img = visual.ImageStim(self.win, image=os.path.join(img_path, 'bulbof.png'), size=bulb_size, pos=bulb_pos)
            self.bulb_on_img = visual.ImageStim(self.win, image=os.path.join(img_path, 'bulbon.png'), size=bulb_size, pos=bulb_pos)
        else:
            self.bulb_off_img = visual.Circle(self.win, radius=0.2, fillColor='grey')
            self.bulb_on_img = visual.Circle(self.win, radius=0.2, fillColor='yellow')

        self.colored_bar = visual.Rect(win=self.win, width=0.15, height=0.04, pos=(0.0, -0.5))
        self.text_stim = visual.TextStim(self.win, color='white', height=0.05, wrapWidth=1.5)
        self.fixation = visual.TextStim(self.win, text='+', color='white', height=0.12)

        # Response screen elements
        self.response_title = visual.TextStim(self.win, text="Combien de ms avez-vous perçu ?", color='white', height=0.05, pos=(0, 0.3))
        self.response_options_text = visual.TextStim(self.win, text="1: 100 | 2: 200 | 3: 300 | 4: 400 | 5: 500 | 6: 600 | 7: 700 | 8: 800", color='white', height=0.05, pos=(0, 0.05))
        self.response_instr = visual.TextStim(self.win, text="Répondez avec les 8 boutons", color='white', height=0.045, pos=(0, -0.2))

        self.underline_x_positions = [-0.35, -0.255, -0.15, -0.05, 0.055, 0.16, 0.26, 0.36]
        self.underline_y_line = -0.055

        self.response_key_to_ms = {key: ms for key, ms in zip(self.keys['responses'], self.response_values_ms)}

        # Timing Clocks
        self.task_clock = None 
        self.trigger_time = None

    # =========================================================================
    # LOGGING & EVENT HANDLING (INCHANGÉ)
    # =========================================================================
    
    def log_step(self, event_type, trial=None, **kwargs):
        self.is_data_saved = False
        current_time = self.task_clock.getTime() if self.task_clock else 0.0
        t_idx = trial if trial is not None else self.current_trial_idx

        entry = {
            'participant': self.nom,
            'session': self.session,
            'phase': self.current_phase,
            'trial': t_idx,
            'time_s': round(current_time, 5),
            'event_type': event_type
        }
        entry.update(kwargs)
        self.global_records.append(entry)

    def check_for_ttl(self):
        if self.task_clock:
            keys = event.getKeys(keyList=[self.keys['trigger']], timeStamped=self.task_clock)
            for k, t in keys:
                self.log_step('ttl_pulse', key=k, real_time=t)

    def _setup_keys(self):
        if self.mode == 'fmri':
            self.keys = {'action': 'b', 'responses': ['d', 'n', 'z', 'e', 'b', 'y', 'g', 'r'], 'trigger': 't', 'quit': 'escape'}
        else:
            self.keys = {'action': 'y', 'responses': ['a', 'z', 'e', 'r', 'y', 'u', 'i', 'o'], 'trigger': 't', 'quit': 'escape'}

    # =========================================================================
    # EXPERIMENT PHASES (TRIGGERS INCHANGÉS)
    # =========================================================================

    def show_instructions(self):
        self.current_phase = 'instructions'
        instructions = (
            "Tâche de jugement temporel\n\n"
            "Condition ACTIVE : barre verte\nCondition PASSIVE : barre rouge\n\n"
            "Appuyez sur ESPACE pour allumer l'ampoule.\nL'ampoule s'allumera après un délai aléatoire.\n\n"
            "Ensuite, évaluez le délai perçu (100 à 800ms).\n"
            "Appuyez sur une touche pour commencer."
        )
        self.text_stim.text = instructions
        self.text_stim.draw()
        self.win.flip()
        
        event.waitKeys(keyList=['space', 'return', 'num_enter', self.keys['quit']])
        if event.getKeys(keyList=[self.keys['quit']]):
            should_quit(self.win, quit=True)

    def wait_for_trigger(self):
        self.current_phase = 'waiting_trigger'
        self.text_stim.text = f"En attente du trigger scanner ('{self.keys['trigger']}')"
        self.text_stim.draw()
        self.win.flip()
        
        keys = event.waitKeys(keyList=[self.keys['trigger'], self.keys['quit']], timeStamped=True)
        if keys and keys[0][0] == self.keys['quit']:
            should_quit(self.win, quit=True)
        
        self.task_clock = core.Clock() 
        self.trigger_time = 0.0 
        self.log_step('trigger_received', info="T0 start")
        print("- Trigger reçu - ")
        
        # TRIGGER T=0
        self.ParPort.send_trigger(self.codes['start_exp'])

    # --- RESTING STATE (TRIGGERS INCHANGÉS) ---
    def show_resting_state(self, duration_s):
        self.current_phase = 'resting_state'
        self.current_trial_idx = None
        
        print(f"=== Resting State ({duration_s}s) ===")
        self.log_step('resting_state_start', duration_expected=duration_s)
        
        # TRIGGER: Début Resting
        self.ParPort.send_trigger(self.codes['rest_start'])
        
        start_time = self.task_clock.getTime()
        last_print_time = 0
        
        while (self.task_clock.getTime() - start_time) < duration_s:
            self.fixation.draw()
            self.win.flip()
            
            elapsed = self.task_clock.getTime() - start_time
            
            if elapsed - last_print_time >= 15:
                print(f"Resting State : {int(elapsed)}s / {duration_s}s")
                last_print_time = elapsed

            self.check_for_ttl()
            if event.getKeys(keyList=[self.keys['quit']]):
                should_quit(self.win, quit=True)
            core.wait(0.01)

        print(f"Resting State :{duration_s}s / {duration_s}s")
        
        # TRIGGER: Fin Resting
        self.ParPort.send_trigger(self.codes['rest_end'])
        self.log_step('resting_state_end')

    # --- CRISIS SIMULATION & VALIDATION (TRIGGERS INCHANGÉS) ---
    def show_crisis_validation_window(self):
        self.current_phase = 'crisis_validation'
        self.current_trial_idx = None
        print("=== Fenêtre de Validation de Crise ===")

        loop_crisis = True
        while loop_crisis:
            # 1. Launch Prompt
            msg_launch = visual.TextStim(self.win, text='Appuyer pour démarrer la crise', height=0.08)
            msg_launch.draw()
            self.win.flip()
            self.log_step('crisis_prompt_start')
            
            # TRIGGER : Affichage du prompt crise
            self.ParPort.send_trigger(self.codes['crisis_prompt'])
            
            event.clearEvents()
            keys = []
            while not keys:
                self.check_for_ttl()
                keys = event.getKeys(keyList=self.keys['responses'] + [self.keys['quit']])
                if keys and keys[0] == self.keys['quit']: should_quit(self.win, quit=True)
                core.wait(0.01)

            # 2. Crisis Active
            self.log_step('crisis_action_started', trigger_key=keys[0])
            
            # TRIGGER : Début de l'action Crise
            self.ParPort.send_trigger(self.codes['crisis_start'])
            
            self.fixation.draw()
            self.win.flip()
            
            core.wait(0.5) 
            event.clearEvents()
            
            keys = []
            while not keys:
                self.check_for_ttl()
                keys = event.getKeys(keyList=self.keys['responses'] + [self.keys['quit']])
                if keys and keys[0] == self.keys['quit']: should_quit(self.win, quit=True)
                core.wait(0.01)
            
            # TRIGGER : Fin de l'action Crise
            self.ParPort.send_trigger(self.codes['crisis_end'])
            self.log_step('crisis_action_ended', end_key=keys[0])

            # 3. Validation
            choice_text = visual.TextStim(self.win, text='[1-4] Crise réussie     [5-8] Crise échouée', height=0.08)
            choice_text.draw()
            self.win.flip()
            self.log_step('crisis_validation_prompt')
            
            # TRIGGER : Demande de validation
            self.ParPort.send_trigger(self.codes['crisis_valid_prompt'])
            
            core.wait(0.2)
            event.clearEvents()
            keys = event.waitKeys(keyList=self.keys['responses'] + [self.keys['quit']])
            if keys[0] == self.keys['quit']: should_quit(self.win, quit=True)
            
            key = keys[0]
            idx = self.keys['responses'].index(key)
            success = True if idx < 4 else False
            result_label = 'success' if success else 'failed'
            
            # TRIGGER : Résultat choisi
            if success:
                self.ParPort.send_trigger(self.codes['crisis_res_success'])
            else:
                self.ParPort.send_trigger(self.codes['crisis_res_fail'])
            
            self.log_step('crisis_result_chosen', result=result_label, key=key)

            # Feedback
            confirmation = visual.TextStim(self.win, text=f"Résultat : {result_label.upper()}", height=0.08)
            confirmation.draw()
            self.win.flip()
            core.wait(1.0)

            # 4. Retry Logic
            if not success:
                retry_text = visual.TextStim(self.win, text='Recommencer ?\n[1-4] Oui   [5-8] Non', height=0.06)
                retry_text.draw()
                self.win.flip()
                
                keys = event.waitKeys(keyList=self.keys['responses'] + [self.keys['quit']])
                idx_retry = self.keys['responses'].index(keys[0])
                
                if idx_retry >= 4:  # NON
                    self.log_step('crisis_retry_decision', choice='no_retry_quit')
                    self.ParPort.send_trigger(self.codes['crisis_retry_no'])
                    should_quit(self.win, quit=True)
                else: # OUI
                    self.log_step('crisis_retry_decision', choice='retry')
                    self.ParPort.send_trigger(self.codes['crisis_retry_yes'])
            else:
                loop_crisis = False

        self.log_step('crisis_phase_end')

    # =========================================================================
    # CORE TRIAL LOGIC (TRIGGERS INCHANGÉS)
    # =========================================================================

    def draw_lightbulb(self, base_color, bulb_on=False):
        self.colored_bar.fillColor = base_color
        self.colored_bar.lineColor = base_color
        self.colored_bar.draw()
        bulb = self.bulb_on_img if bulb_on else self.bulb_off_img
        bulb.draw()

    def run_trial(self, trial_index, total_trials, condition, delay_ms, feedback=False):
        """
        Unified trial function.
        """
        should_quit(self.win)
        self.current_trial_idx = trial_index
        base_color = '#00FF00' if condition == 'active' else '#FF0000'

        # --- 1. Trial Start ---
        log_event = 'trial_start_feedback' if feedback else 'trial_start'
        self.log_step(log_event, condition=condition, requested_delay_ms=delay_ms)
        
        # TRIGGER : Début Essai
        t_code = self.codes['trial_active'] if condition == 'active' else self.codes['trial_passive']
        self.ParPort.send_trigger(t_code)

        self.fixation.draw()
        self.win.flip()
        self.check_for_ttl()
        core.wait(0.5)

        # Show Bulb OFF
        self.draw_lightbulb(base_color=base_color, bulb_on=False)
        self.win.flip()
        
        # --- 2. Wait for Action (Keypress) ---
        event.clearEvents(eventType='keyboard')
        keys = []
        wait_start = self.task_clock.getTime()
        while not keys:
            self.check_for_ttl()
            keys = event.getKeys(keyList=[self.keys['action'], self.keys['quit']])
            if keys:
                if keys[0] == self.keys['quit']: should_quit(self.win, quit=True)
                break
            core.wait(0.001)

        # TRIGGER : Appui bouton "Allumer"
        self.ParPort.send_trigger(self.codes['action_bulb'])

        action_time = self.task_clock.getTime()
        self.log_step('action_performed', action_key=keys[0], rt_prep=action_time-wait_start)

        # --- 3. Precise Timing Logic ---
        target_light_time = action_time + (delay_ms / 1000.0)
        
        self.draw_lightbulb(base_color=base_color, bulb_on=True)
        
        frame_tolerance_s = (0.75*1/self.frame_rate)
        while self.task_clock.getTime() < (target_light_time - frame_tolerance_s):
            core.wait(0.001) 

        self.win.flip() # Bulb ON
        
        # TRIGGER : Ampoule s'allume
        self.ParPort.send_trigger(self.codes['bulb_on'])
        
        bulb_on_time = self.task_clock.getTime()
        actual_delay = (bulb_on_time - action_time) * 1000
        self.log_step('bulb_lit', actual_delay_ms=actual_delay, error_ms=actual_delay-delay_ms)
        
        # Random wait before response prompt
        wait_duration = random.uniform(1.2, 1.8)
        core.wait(wait_duration)
        self.win.flip()

        # --- 4. Response Collection ---
        t0_response = self.task_clock.getTime()
        self.log_step('response_prompt_shown')
        
        # TRIGGER : Affichage question
        self.ParPort.send_trigger(self.codes['response_prompt'])
        
        self.response_title.draw()
        self.response_options_text.draw()
        self.response_instr.draw()
        self.win.flip()

        event.clearEvents(eventType='keyboard')
        resp_keys = event.waitKeys(maxWait=5.0, keyList=self.keys['responses'] + [self.keys['quit']], timeStamped=self.task_clock)
        self.check_for_ttl()

        rt = None
        response_ms = None
        
        if resp_keys:
            resp_key, timestamp_key = resp_keys[0]
            if resp_key == self.keys['quit']: should_quit(self.win, quit=True)
            
            # TRIGGER : Réponse donnée
            self.ParPort.send_trigger(self.codes['response_given'])

            rt = timestamp_key - t0_response
            response_ms = self.response_key_to_ms.get(resp_key)
            
            idx_user = self.keys['responses'].index(resp_key)
            
            # --- FEEDBACK LOGIC ---
            if feedback:
                is_correct = (response_ms == delay_ms)
                user_bar_color = 'green' if is_correct else 'yellow'
                msg_text = "Bonne réponse !" if is_correct else f"La bonne réponse était : {delay_ms}"
                msg_color = 'green' if is_correct else 'red'
                
                self.response_title.draw()
                self.response_options_text.draw()
                
                user_line = visual.Line(self.win, 
                                        start=(self.underline_x_positions[idx_user]-0.04, self.underline_y_line),
                                        end=(self.underline_x_positions[idx_user]+0.04, self.underline_y_line),
                                        lineColor=user_bar_color, lineWidth=5)
                user_line.draw()
                
                if not is_correct:
                    try:
                        idx_correct = self.response_values_ms.index(delay_ms)
                        correct_line = visual.Line(self.win, 
                                                start=(self.underline_x_positions[idx_correct]-0.04, self.underline_y_line),
                                                end=(self.underline_x_positions[idx_correct]+0.04, self.underline_y_line),
                                                lineColor='red', lineWidth=6)
                        correct_line.draw()
                    except ValueError: pass

                fb_text = visual.TextStim(self.win, text=msg_text, color=msg_color, height=0.05, pos=(0, -0.2))
                fb_text.draw()
                
                self.win.flip()
                core.wait(1.5) 
                
            else:
                # --- STANDARD (NO FEEDBACK) ---
                underline = visual.Line(self.win, 
                                        start=(self.underline_x_positions[idx_user]-0.04, self.underline_y_line),
                                        end=(self.underline_x_positions[idx_user]+0.04, self.underline_y_line),
                                        lineColor='yellow', lineWidth=5)
                self.response_title.draw()
                self.response_options_text.draw()
                self.response_instr.draw()
                underline.draw()
                self.win.flip()
                core.wait(0.6)

            self.log_step('response_given', response_key=resp_key, response_choice_ms=response_ms, rt_s=rt, feedback_mode=feedback)
            
            # --- CUSTOM PRINT FORMAT ---
            fb_info = f" | FB: {feedback}" if feedback else ""
            print(f"Trial {trial_index}/{total_trials} | Condition: {condition} | Delay: {delay_ms} | Answer: {response_ms}{fb_info}")

        else:
            # TRIGGER : Timeout
            self.ParPort.send_trigger(self.codes['timeout'])
            
            print(f"Trial {trial_index}/{total_trials} | Condition: {condition} | Delay: {delay_ms} | Response timeout")
            self.log_step('response_timeout')
            too_slow = visual.TextStim(self.win, text="Temps de réponse écoulé", color='red', height=0.1)
            too_slow.draw()
            self.win.flip()
            core.wait(0.8)

        # --- 5. ISI ---
        isi = random.uniform(*self.stim_isi_range)
        self.check_for_ttl()
        core.wait(isi)
        
        self.log_step('trial_summary', condition=condition, delay_target=delay_ms, delay_actual=actual_delay, response_ms=response_ms)
        return True

    def build_trials(self, n_trials, training):
        if training:
            conditions = ['active']
        else:
            conditions = ['active', 'passive']

        unique_types = [(c, d) for c in conditions for d in self.delays_ms]

        n_full_repeats = n_trials // len(unique_types)
        remainder = n_trials % len(unique_types)
        trials = unique_types * n_full_repeats
        if remainder > 0:
            trials.extend(random.sample(unique_types, remainder))
        random.shuffle(trials)

        if training:
            return trials

        # --- Constraint Enforcement (Swap Method) ---
        def is_conflict(trial_list, idx, candidate_trial):
            cand_cond, cand_delay = candidate_trial
            if idx >= 3:
                if trial_list[idx-1][0] == trial_list[idx-2][0] == trial_list[idx-3][0] == cand_cond:
                    return True
            if idx >= 2:
                if trial_list[idx-1][1] == trial_list[idx-2][1] == cand_delay:
                    return True
            return False

        max_restarts = 10
        for attempt in range(max_restarts):
            try:
                current_trials = trials[:]
                random.shuffle(current_trials)
                for i in range(n_trials):
                    if is_conflict(current_trials, i, current_trials[i]):
                        swapped = False
                        for j in range(i + 1, n_trials):
                            if not is_conflict(current_trials, i, current_trials[j]):
                                current_trials[i], current_trials[j] = current_trials[j], current_trials[i]
                                swapped = True
                                break
                        if not swapped:
                            raise ValueError("Constraint conflict")
                return current_trials
            except ValueError:
                continue
        
        return trials

    def run_trial_block(self, n_trials, block_name, phase_tag, feedback):
        self.current_phase = phase_tag 
        self.log_step('block_start', block_name=block_name, feedback_mode=feedback)
        
        trials = self.build_trials(n_trials, feedback)
        total_trials_in_block = len(trials)
        
        for i, (cond, delay) in enumerate(trials, start=1):
            self.run_trial(i, total_trials_in_block, cond, delay, feedback=feedback)
            
        self.log_step('block_end', block_name=block_name)

    # =========================================================================
    # DATA SAVING & CLEANUP (INCHANGÉ)
    # =========================================================================

    def save_results(self):
        if not self.enregistrer: return
        if self.is_data_saved: return 

        fname = f"{self.nom}_session_{self.session}_start_{self.start_timestamp}.csv"
        path = os.path.join(self.data_dir, fname)
        
        print(f"Sauvegarde des données : {len(self.global_records)} lignes")

        if not self.global_records:
            return

        all_keys = set()
        for rec in self.global_records:
            all_keys.update(rec.keys())
        
        first_cols = ['time_s', 'phase', 'trial', 'event_type', 'participant', 'session']
        remaining_cols = sorted(list(all_keys - set(first_cols)))
        final_fieldnames = first_cols + remaining_cols
        
        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=final_fieldnames)
                writer.writeheader()
                writer.writerows(self.global_records)
            
            self.is_data_saved = True
            print(f"- Sauvegarde réussie : {fname}")
            
        except Exception as e:
            print(f"ERREUR CRITIQUE SAUVEGARDE : {e}")
            with open(f"BACKUP_{self.start_timestamp}.csv", 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=final_fieldnames)
                writer.writeheader()
                writer.writerows(self.global_records)

    def show_end_screen(self):
        self.text_stim.text = "Fin de la session.\nMerci."
        self.text_stim.draw()
        self.win.flip()
        core.wait(15)
        self.win.close()
        core.quit()

    def run(self):
        """
        Main execution logic.
        """
        if self.run_type == 'training':
            print(f"Démarrage de l'ENTRAÎNEMENT ({self.n_trials_training} essais)")
            self.wait_for_trigger()
            self.show_resting_state(duration_s=10)
            self.show_instructions() 
            self.run_trial_block(self.n_trials_training, block_name="TRAINING", phase_tag='training', feedback=True)
        else:
            self.show_instructions()
            self.wait_for_trigger()
            if self.run_type == 'base':
                print(f"Démarrage de la BASE avec {self.n_trials_base} essais de type base et {self.n_trials_block} de type bloc")
                self.show_resting_state(duration_s=150) 
                self.run_trial_block(self.n_trials_base, "BASE", phase_tag='base', feedback=False)
                self.show_crisis_validation_window()
                self.run_trial_block(self.n_trials_block, "BLOCK", phase_tag='run_standard', feedback=False)
            else:
                print(f"Démarrage du BLOC avec {self.n_trials_block} essais")
                self.show_resting_state(duration_s=150) 
                self.show_crisis_validation_window()
                self.run_trial_block(self.n_trials_block, "BLOCK", phase_tag='run_standard', feedback=False)
        
        self.save_results()
        self.show_end_screen()