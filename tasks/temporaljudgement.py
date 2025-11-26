from psychopy import visual, event, core, logging
import random, csv, os
from datetime import datetime
from utils.utils import should_quit
import warnings

# --- Console Logging Configuration ---
# Suppress minor warnings to keep the console readable
logging.console.setLevel(logging.ERROR)

class TemporalJudgement:
    def __init__(self, win, nom, session='01', enregistrer=True, screenid=1, mode='fmri', run_type='base',
                 n_trials=60, delays_ms=(200, 300, 400, 500, 600, 700),
                 response_options=(100, 200, 300, 400, 500, 600, 700, 800),
                 stim_isi_range=(1500, 2500),
                 data_dir='data/temporal_judgement'):
        
        # --- Experiment Parameters ---
        self.win = win
        self.frame_rate = win.getActualFrameRate(nIdentical=10, nMaxFrames=100, threshold=1)
        self.nom = nom
        self.session = session
        self.enregistrer = enregistrer  # Save flag
        self.screenid = screenid
        self.run_type = run_type
        self.mode = mode
        self.n_trials = n_trials
        self.delays_ms = list(delays_ms)
        self.response_values_ms = list(response_options)
        self.stim_isi_range = (stim_isi_range[0]/1000 , stim_isi_range[1]/1000 )
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

        # --- Global Logging System ---
        # Stores every event (keypress, TTL, screen flip) sequentially
        self.global_records = [] 
        self.current_phase = 'setup'
        self.current_trial_idx = None 
        self.is_data_saved = False

        self._setup_keys()

        # --- Visual Stimuli Setup ---
        img_path = 'image'
        bulb_size = (0.45 * 0.9, 0.9 * 0.9)
        bulb_pos = (0.0, 0.0)
        
        # Load images with graceful fallback (shapes) if files are missing
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

        self.underline_x_positions = [-0.35, -0.245, -0.145, -0.06, 0.06, 0.145, 0.245, 0.35]
        self.underline_y_line = -0.055

        self.response_key_to_ms = {key: ms for key, ms in zip(self.keys['responses'], self.response_values_ms)}

        # Timing Clocks
        self.task_clock = None # Initialized upon receiving MRI trigger
        self.trigger_time = None

    # =========================================================================
    # LOGGING & EVENT HANDLING
    # =========================================================================
    
    def log_step(self, event_type, trial=None, **kwargs):
        """
        Appends a single event dictionary to global_records.
        Used for TTL pulses, keystrokes, and trial milestones.
        """
        self.is_data_saved = False
        
        # Calculate time relative to T0 (Trigger)
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
        
        # Merge extra data (RTs, specific keys, etc.)
        entry.update(kwargs)
        self.global_records.append(entry)

    def check_for_ttl(self):
        """ Polls for MRI trigger pulses ('t') in the background """
        if self.task_clock:
            keys = event.getKeys(keyList=[self.keys['trigger']], timeStamped=self.task_clock)
            for k, t in keys:
                self.log_step('ttl_pulse', key=k, real_time=t)

    def _setup_keys(self):
        """ Defines keymaps based on environment (fMRI vs Lab) """
        if self.mode == 'fmri':
            self.keys = {'action': 'b', 'responses': ['d', 'n', 'z', 'e', 'b', 'y', 'g', 'r'], 'trigger': 't', 'quit': 'escape'}
        else:
            self.keys = {'action': 'y', 'responses': ['a', 'z', 'e', 'r', 'y', 'u', 'i', 'o'], 'trigger': 't', 'quit': 'escape'}

    # =========================================================================
    # EXPERIMENT PHASES
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
        """ Waits for the first MRI trigger to start the main clock (T0) """
        self.current_phase = 'waiting_trigger'
        self.text_stim.text = f"En attente du trigger scanner ('{self.keys['trigger']}')"
        self.text_stim.draw()
        self.win.flip()
        
        keys = event.waitKeys(keyList=[self.keys['trigger'], self.keys['quit']], timeStamped=True)
        if keys and keys[0][0] == self.keys['quit']:
            should_quit(self.win, quit=True)
        
        # Initialize T0
        self.task_clock = core.Clock() 
        self.trigger_time = 0.0 
        self.log_step('trigger_received', info="T0 start")
        print(">>> Trigger received - Clock started")

    # --- RESTING STATE ---
    def show_resting_state(self, duration_s=150):
        self.current_phase = 'resting_state'
        self.current_trial_idx = None
        
        print(f"=== Resting State ({duration_s}s) ===")
        self.log_step('resting_state_start', duration_expected=duration_s)
        
        start_time = self.task_clock.getTime()
        while (self.task_clock.getTime() - start_time) < duration_s:
            self.fixation.draw()
            self.win.flip()
            
            # Continuous checks
            self.check_for_ttl()
            if event.getKeys(keyList=[self.keys['quit']]):
                should_quit(self.win, quit=True)
            core.wait(0.01)
        
        self.log_step('resting_state_end')

    # --- CRISIS SIMULATION & VALIDATION ---
    def show_crisis_validation_window(self):
        """ 
        Interactive loop: 
        1. Prompt start -> 2. Action/Crisis -> 3. Success/Fail Validation -> 4. Retry if needed 
        """
        self.current_phase = 'crisis_validation'
        self.current_trial_idx = None
        print("=== Crisis Validation Window ===")

        loop_crisis = True
        while loop_crisis:
            # 1. Launch Prompt
            msg_launch = visual.TextStim(self.win, text='Appuyer pour démarrer la crise', height=0.08)
            msg_launch.draw()
            self.win.flip()
            self.log_step('crisis_prompt_start')
            
            event.clearEvents()
            keys = []
            while not keys:
                self.check_for_ttl()
                keys = event.getKeys(keyList=self.keys['responses'] + [self.keys['quit']])
                if keys and keys[0] == self.keys['quit']: should_quit(self.win, quit=True)
                core.wait(0.01)

            # 2. Crisis Active
            self.log_step('crisis_action_started', trigger_key=keys[0])
            msg_feedback = visual.TextStim(self.win, text='Crise en cours...\nAppuyer quand terminée', height=0.08)
            msg_feedback.draw()
            self.win.flip()
            
            core.wait(0.5) # Debounce
            event.clearEvents()
            
            keys = []
            while not keys:
                self.check_for_ttl()
                keys = event.getKeys(keyList=self.keys['responses'] + [self.keys['quit']])
                if keys and keys[0] == self.keys['quit']: should_quit(self.win, quit=True)
                core.wait(0.01)
            
            self.log_step('crisis_action_ended', end_key=keys[0])

            # 3. Validation
            choice_text = visual.TextStim(self.win, text='[1-4] Crise RÉUSSIE     [5-8] Crise ÉCHOUÉE', height=0.08)
            choice_text.draw()
            self.win.flip()
            self.log_step('crisis_validation_prompt')
            
            core.wait(0.2)
            event.clearEvents()
            keys = event.waitKeys(keyList=self.keys['responses'] + [self.keys['quit']])
            if keys[0] == self.keys['quit']: should_quit(self.win, quit=True)
            
            key = keys[0]
            idx = self.keys['responses'].index(key)
            success = True if idx < 4 else False
            result_label = 'success' if success else 'failed'
            
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
                if idx_retry >= 4: # No Retry
                    loop_crisis = False
                    self.log_step('crisis_retry_decision', choice='no_retry')
                else:
                    self.log_step('crisis_retry_decision', choice='retry')
            else:
                loop_crisis = False

        self.log_step('crisis_phase_end')

    # =========================================================================
    # CORE TRIAL LOGIC
    # =========================================================================

    def draw_lightbulb(self, base_color, bulb_on=False):
        self.colored_bar.fillColor = base_color
        self.colored_bar.lineColor = base_color
        self.colored_bar.draw()
        bulb = self.bulb_on_img if bulb_on else self.bulb_off_img
        bulb.draw()

    def run_trial(self, trial_index, condition, delay_ms):
            should_quit(self.win)
            self.current_trial_idx = trial_index
            base_color = '#00FF00' if condition == 'active' else '#FF0000'

            # 1. Trial Start & Fixation
            self.log_step('trial_start', condition=condition, requested_delay_ms=delay_ms)

            self.fixation.draw()
            self.win.flip()
            self.check_for_ttl()
            core.wait(0.5)

            # Show Bulb OFF
            self.draw_lightbulb(base_color=base_color, bulb_on=False)
            self.win.flip()
            
            # 2. Wait for Action (Keypress)
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

            action_time = self.task_clock.getTime()
            self.log_step('action_performed', action_key=keys[0], rt_prep=action_time-wait_start)

            # 3. Precise Timing Logic
            # Calculate exact target time
            target_light_time = action_time + (delay_ms / 1000.0)
            
            # Prepare stimulus *before* the deadline
            self.draw_lightbulb(base_color=base_color, bulb_on=True)
            
            # Wait actively until just before the target frame (approx 3/4 * frame)
            frame_tolerance_s = 0.75 * (1/self.frame_rate)
            
            while self.task_clock.getTime() < (target_light_time - frame_tolerance_s):
                self.check_for_ttl()
                core.wait(0.001) 

            # Critical Flip: Syncs with vertical retrace to hit target_light_time
            self.win.flip()
            
            # Capture actual hardware flip time
            bulb_on_time = self.task_clock.getTime()
            actual_delay = (bulb_on_time - action_time) * 1000
            
            self.log_step('bulb_lit', actual_delay_ms=actual_delay, error_ms=actual_delay-delay_ms)
            
            core.wait(1.0)
            self.check_for_ttl()

            # 4. Response Collection
            self.log_step('response_prompt_shown')
            self.response_title.draw()
            self.response_options_text.draw()
            self.response_instr.draw()
            self.win.flip()

            event.clearEvents(eventType='keyboard')
            resp_keys = event.waitKeys(maxWait=5.0, keyList=self.keys['responses'] + [self.keys['quit']], timeStamped=self.task_clock)
            self.check_for_ttl()

            rt = None
            response_ms = None
            resp_key = None

            if resp_keys:
                resp_key, timestamp_key = resp_keys[0]
                if resp_key == self.keys['quit']: should_quit(self.win, quit=True)
                rt = timestamp_key - bulb_on_time
                response_ms = self.response_key_to_ms.get(resp_key)
                
                # Visual Feedback (Underline)
                idx = self.keys['responses'].index(resp_key)
                underline = visual.Line(self.win, start=(self.underline_x_positions[idx]-0.04, self.underline_y_line),
                                        end=(self.underline_x_positions[idx]+0.04, self.underline_y_line),
                                        lineColor='yellow', lineWidth=5)
                self.response_title.draw()
                self.response_options_text.draw()
                self.response_instr.draw()
                underline.draw()
                self.win.flip()
                core.wait(0.6)
                self.log_step('response_given', response_key=resp_key, response_choice_ms=response_ms, rt_s=rt)
                print(f"Trial {trial_index} | Delay: {delay_ms}ms | Answer: {response_ms}ms | RT: {rt:.4f}s")
            else:
                self.log_step('response_timeout')
                too_slow = visual.TextStim(self.win, text="Trop lent !", color='red', height=0.12)
                too_slow.draw()
                self.win.flip()
                core.wait(0.8)

            # 5. Inter-Stimulus Interval (ISI)
            isi = random.uniform(*self.stim_isi_range)
            self.check_for_ttl()
            core.wait(isi)
            
            self.log_step('trial_summary_data', condition=condition, delay_target=delay_ms, delay_actual=actual_delay, response_ms=response_ms, isi=isi)
            return True

    def build_trials(self, n_trials):
        conditions = ['active', 'passive']
        trials = []
        for _ in range(n_trials):
            trials.append((random.choice(conditions), random.choice(self.delays_ms)))
        return trials

    def run_trial_block(self, n_trials, block_name, phase_tag):
        self.current_phase = phase_tag 
        print(f"--- Start {block_name} ({phase_tag}) ---")
        self.log_step('block_start', block_name=block_name)
        
        trials = self.build_trials(n_trials)
        for i, (cond, delay) in enumerate(trials, start=1):
            self.run_trial(i, cond, delay)
            
        self.log_step('block_end', block_name=block_name)
        print(f"--- End {block_name} ---")

    # =========================================================================
    # DATA SAVING & CLEANUP
    # =========================================================================

    def save_results(self):
        """ Robust CSV saving handling dynamic fieldnames (heterogeneous events) """
        if not self.enregistrer: return
        if self.is_data_saved: return 

        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        fname = f"{self.nom}_GLOBAL_{self.session}_{ts}.csv"
        path = os.path.join(self.data_dir, fname)
        
        print(f"Saving data: {len(self.global_records)} records...")

        if not self.global_records:
            return

        # 1. Identify all unique keys across all records
        all_keys = set()
        for rec in self.global_records:
            all_keys.update(rec.keys())
        
        # 2. Order columns: Standard fields first, others alphabetical
        first_cols = ['time_s', 'phase', 'trial', 'event_type', 'participant', 'session']
        remaining_cols = sorted(list(all_keys - set(first_cols)))
        final_fieldnames = first_cols + remaining_cols
        
        # 3. Write File
        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=final_fieldnames)
                writer.writeheader()
                writer.writerows(self.global_records)
            
            self.is_data_saved = True
            print(f">> Saved successfully: {fname}")
            
        except Exception as e:
            print(f"CRITICAL SAVE ERROR: {e}")
            # Local Backup
            with open(f"BACKUP_{ts}.csv", 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=final_fieldnames)
                writer.writeheader()
                writer.writerows(self.global_records)

    def show_end_screen(self):
        self.text_stim.text = "Fin de la session.\nMerci."
        self.text_stim.draw()
        self.win.flip()
        core.wait(2.0)
        self.win.close()
        core.quit()

    def run(self):
        # Main Execution Sequence
        self.show_instructions()
        self.wait_for_trigger()
        
        self.show_resting_state(duration_s=60) 
        
        if self.run_type == 'base':
            self.run_trial_block(10, "BLOC 1", phase_tag='run_01')
            self.show_crisis_validation_window()
            self.run_trial_block(self.n_trials, "BLOC 2", phase_tag='run_02')
        else:
            self.show_crisis_validation_window()
            self.run_trial_block(self.n_trials, "BLOC UNIQUE", phase_tag='run_standard')
        
        self.save_results()
        self.show_end_screen()