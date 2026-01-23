"""
temporal_judgement.py
---------------------
Tâche de jugement temporel avec conditions Active/Passive.
Hérite de BaseTask pour une architecture cohérente.

Spécificités:
    - Modes d'exécution multiples (training / base / block)
    - Fenêtre de validation de crise (crisis window)

Auteur : Clément BARBE / CENIR
Date : Janvier 2026
"""

import random
import gc
from psychopy import visual, event, core
from utils.base_task import BaseTask
from utils.utils import should_quit


class TemporalJudgement(BaseTask):
    """
    Tâche de jugement de délai temporel entre une action et un stimulus visuel.
    
    Workflow:
        1. Participant appuie sur un bouton (Active) ou attend (Passive)
        2. Ampoule s'allume après un délai (200-700ms)
        3. Estimation du délai perçu (8 options : 100-800ms)
        4. Feedback optionnel (mode training)
    """

    def __init__(self, win, nom, session='01', mode='fmri', run_type='base',
                 n_trials_base=72, n_trials_block=24, n_trials_training=12,
                 delays_ms=(200, 300, 400, 500, 600, 700),
                 response_options=(100, 200, 300, 400, 500, 600, 700, 800),
                 stim_isi_range=(1500, 2500),
                 enregistrer=True, eyetracker_actif=False, parport_actif=True,
                 **kwargs):
        """
        Args:
            win: Fenêtre PsychoPy
            nom (str): ID Participant
            session (str): Numéro de session
            mode (str): 'fmri' ou 'behavioral' (mapping touches)
            run_type (str): 'training', 'base' (complet) ou 'block' (court)
            n_trials_base (int): Nombre d'essais en condition baseline
            n_trials_block (int): Nombre d'essais post-crise
            n_trials_training (int): Nombre d'essais d'entraînement
            delays_ms (tuple): Délais possibles entre action et stimulus (ms)
            response_options (tuple): Choix de réponse disponibles (ms)
            stim_isi_range (tuple): Range du délai inter-stimuli (ms)
            enregistrer (bool): Sauvegarder les données
            eyetracker_actif (bool): Activer EyeTracker
            parport_actif (bool): Activer Port Parallèle
        """
        
        # --- Appel au constructeur parent ---
        super().__init__(
            win=win,
            nom=nom,
            session=session,
            task_name="Temporal Judgement",
            folder_name="temporal_judgement",
            eyetracker_actif=eyetracker_actif,
            parport_actif=parport_actif,
            enregistrer=enregistrer,
            et_prefix='TJ'
        )

        # --- Paramètres Expérimentaux Spécifiques ---
        self.mode = mode.lower()
        self.run_type = run_type.lower()
        
        self.n_trials_base = n_trials_base
        self.n_trials_block = n_trials_block
        self.n_trials_training = n_trials_training
        
        self.delays_ms = list(delays_ms)
        self.response_values_ms = list(response_options)
        self.stim_isi_range = (stim_isi_range[0] / 1000.0, stim_isi_range[1] / 1000.0)

        # --- Variables de Session ---
        self.global_records = []  # ✅ AJOUT EXPLICITE
        self.current_trial_idx = 0
        self.current_phase = 'setup'

        # --- Détection Résolution (Pour scaling 4K) ---
        self._detect_display_scaling()

        # --- Configuration des Codes TTL ---
        self._define_ttl_codes()

        # --- Mapping des Touches ---
        self._setup_key_mapping()

        # --- Préchargement des Stimuli ---
        self._setup_task_stimuli()

        self.logger.ok(f"TemporalJudgement init | Mode: {self.run_type} | Trials: Base={self.n_trials_base}, Block={self.n_trials_block}")

    def _detect_display_scaling(self):
        """Détecte la résolution pour adapter l'épaisseur des traits (4K vs HD)."""
        if self.win.size[1] > 1200:
            self.pixel_scale = 2.0
            self.logger.log(f"Écran Haute Résolution détecté ({self.win.size}). Scale: x2.0")
        else:
            self.pixel_scale = 1.0
            self.logger.log(f"Écran Standard ({self.win.size}). Scale: x1.0")
        
        self.x_spacing_scale = 1.14  # Espacement horizontal des options de réponse

    def _define_ttl_codes(self):
        """Codes TTL spécifiques à Temporal Judgement."""
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

    def _setup_key_mapping(self):
        """Configure les touches selon le mode (fMRI vs Comportemental)."""
        if self.mode == 'fmri':
            self.key_action = 'b'
            self.keys_responses = ['d', 'n', 'z', 'e', 'b', 'y', 'g', 'r']
            self.key_trigger = 't'
        else:
            self.key_action = 'y'
            self.keys_responses = ['a', 'z', 'e', 'r', 'y', 'u', 'i', 'o']
            self.key_trigger = 't'
        
        self.keys_quit = ['escape', 'q']
        
        # Mapping touches -> valeurs temporelles
        self.response_key_to_ms = {
            key: ms for key, ms in zip(self.keys_responses, self.response_values_ms)
        }
        
        self.logger.log(f"Mapping touches ({self.mode}): Action={self.key_action}, Responses={self.keys_responses[:3]}...")

    def _setup_task_stimuli(self):
        """Charge tous les stimuli visuels spécifiques."""
        import os
        
        # --- Images des Ampoules ---
        bulb_size = (0.45 * 0.9, 0.9 * 0.9)
        bulb_pos = (0.0, 0.0)
        
        img_off = os.path.join(self.img_dir, 'bulbof.png')
        img_on = os.path.join(self.img_dir, 'bulbon.png')
        
        if os.path.exists(img_off) and os.path.exists(img_on):
            self.bulb_off_img = visual.ImageStim(
                self.win, image=img_off, size=bulb_size, pos=bulb_pos
            )
            self.bulb_on_img = visual.ImageStim(
                self.win, image=img_on, size=bulb_size, pos=bulb_pos
            )
        else:
            self.logger.warn("Images ampoules absentes, utilisation de cercles.")
            self.bulb_off_img = visual.Circle(self.win, radius=0.2, fillColor='grey')
            self.bulb_on_img = visual.Circle(self.win, radius=0.2, fillColor='yellow')

        # --- Barre de Condition (Vert=Active, Rouge=Passive) ---
        self.colored_bar = visual.Rect(
            win=self.win,
            width=0.15,
            height=0.04,
            pos=(0.0, -0.5)
        )

        # --- Textes de Réponse ---
        self.response_title = visual.TextStim(
            self.win,
            text="Combien de ms avez-vous perçu ?",
            color='white',
            height=0.05,
            pos=(0, 0.3)
        )
        
        self.response_options_text = visual.TextStim(
            self.win,
            text="1: 100 | 2: 200 | 3: 300 | 4: 400 | 5: 500 | 6: 600 | 7: 700 | 8: 800",
            color='white',
            height=0.05,
            pos=(0, 0.05)
        )
        
        self.response_instr = visual.TextStim(
            self.win,
            text="Répondez avec les 8 boutons",
            color='white',
            height=0.045,
            pos=(0, -0.2)
        )

        # --- Positions des Soulignements (Feedback visuel) ---
        base_positions = [-0.35, -0.255, -0.15, -0.05, 0.055, 0.16, 0.26, 0.36]
        self.underline_x_positions = [x * self.x_spacing_scale for x in base_positions]
        self.underline_y_line = -0.055

        self.logger.log("Stimuli Temporal Judgement chargés.")

    # =========================================================================
    # LOGGING SPÉCIFIQUE (Wrapper Amélioré)
    # =========================================================================

    def log_trial_event(self, event_type, **kwargs):
        """
        Enregistre un événement avec contexte de phase et de trial.
        
        Args:
            event_type (str): Type d'événement
            **kwargs: Données additionnelles
        """
        current_time = self.task_clock.getTime()
        
        if self.eyetracker_actif:
            self.EyeTracker.send_message(
                f"PHASE_{self.current_phase.upper()}_TRIAL_{self.current_trial_idx:03d}_{event_type.upper()}"
            )
        
        entry = {
            'participant': self.nom,
            'session': self.session,
            'phase': self.current_phase,
            'trial': self.current_trial_idx,
            'time_s': round(current_time, 5),
            'event_type': event_type
        }
        entry.update(kwargs)
        self.global_records.append(entry)

    # =========================================================================
    # CORE TASK LOGIC: TRIAL EXECUTION
    # =========================================================================

    def draw_lightbulb(self, base_color, bulb_on=False):
        """
        Affiche l'ampoule (ON/OFF) + la barre de condition.
        
        Args:
            base_color (str): Couleur de la barre (#00FF00=Active, #FF0000=Passive)
            bulb_on (bool): État de l'ampoule
        """
        self.colored_bar.fillColor = base_color
        self.colored_bar.lineColor = base_color
        self.colored_bar.draw()
        
        bulb = self.bulb_on_img if bulb_on else self.bulb_off_img
        bulb.draw()

    def run_trial(self, trial_index, total_trials, condition, delay_ms, feedback=False):
        """
        Exécute un essai complet avec timing sub-millisecondes (GC désactivé).
        
        Phases:
            1. Fixation
            2. Affichage ampoule éteinte + attente action
            3. Délai précis (200-700ms)
            4. Allumage ampoule
            5. Prompt de réponse (8 options)
            6. Feedback optionnel (training)
            7. ITI
        
        Args:
            trial_index (int): Numéro de l'essai
            total_trials (int): Total d'essais dans le bloc
            condition (str): 'active' ou 'passive'
            delay_ms (int): Délai cible en millisecondes
            feedback (bool): Afficher le feedback correct/incorrect
        
        Returns:
            bool: True si succès, False si interruption
        """
        should_quit(self.win)
        
        # =====================================================================
        # CRITICAL TIMING START: DISABLE GARBAGE COLLECTOR
        # =====================================================================
        gc.disable()

        self.current_trial_idx = trial_index
        base_color = '#00FF00' if condition == 'active' else '#FF0000'

        # --- Phase 1: Début de Trial ---
        self.log_trial_event('trial_start', condition=condition, delay_target_ms=delay_ms, feedback_mode=feedback)
        trigger_code = self.codes['trial_active'] if condition == 'active' else self.codes['trial_passive']
        
        # Fixation initiale
        self.fixation.draw()
        self.win.callOnFlip(self.ParPort.send_trigger, trigger_code)
        self.win.flip()
        core.wait(0.5)

        # --- Phase 2: Attente Action (Condition Active) ---
        self.draw_lightbulb(base_color=base_color, bulb_on=False)
        self.win.flip()
        
        event.clearEvents(eventType='keyboard')
        keys = []
        action_time = 0
        
        while not keys:
            keys = event.getKeys(
                keyList=[self.key_action] + self.keys_quit,
                timeStamped=self.task_clock
            )
            
            if keys:
                key_name, t_down = keys[0]
                if key_name in self.keys_quit:
                    should_quit(self.win, quit=True)
                action_time = t_down
                self.ParPort.send_trigger(self.codes['action_bulb'])
                break
            
            core.wait(0.0005)  # Polling ultra-rapide

        self.log_trial_event('action_performed', action_key=keys[0][0])

        # --- Phase 3: Délai Précis (Timing Critique) ---
        target_light_time = action_time + (delay_ms / 1000.0)
        
        # Calcul du frame tolerance
        frame_rate = self.win.getActualFrameRate(nIdentical=10, nMaxFrames=100, threshold=1)
        if frame_rate is None:
            frame_rate = 60.0
        
        frame_tolerance_s = (0.75 / frame_rate)
        
        # Attente active jusqu'à 1 frame avant le target
        while self.task_clock.getTime() < (target_light_time - frame_tolerance_s):
            core.wait(0.001)

        # --- Phase 4: Allumage de l'Ampoule (Synchronized Flip) ---
        self.draw_lightbulb(base_color=base_color, bulb_on=True)
        self.win.callOnFlip(self.ParPort.send_trigger, self.codes['bulb_on'])
        self.win.flip()
        
        bulb_on_time = self.task_clock.getTime()
        actual_delay = (bulb_on_time - action_time) * 1000
        error_ms = actual_delay - delay_ms
        
        self.log_trial_event('bulb_lit', actual_delay_ms=actual_delay, error_ms=error_ms)

        # Affichage ampoule allumée (durée variable)
        wait_duration = random.uniform(1.2, 1.8)
        core.wait(wait_duration)
        self.win.flip()

        # --- Phase 5: Prompt de Réponse ---
        t0_response = self.task_clock.getTime()
        self.log_trial_event('response_prompt_shown')
        self.ParPort.send_trigger(self.codes['response_prompt'])
        
        self.response_title.draw()
        self.response_options_text.draw()
        self.response_instr.draw()
        self.win.flip()

        event.clearEvents(eventType='keyboard')
        resp_keys = event.waitKeys(
            maxWait=5.0,
            keyList=self.keys_responses + self.keys_quit,
            timeStamped=self.task_clock
        )

        rt = None
        response_ms = None

        # --- Gestion de la Réponse ou Timeout ---
        if resp_keys:
            resp_key, timestamp_key = resp_keys[0]
            
            if resp_key in self.keys_quit:
                should_quit(self.win, quit=True)
            
            self.ParPort.send_trigger(self.codes['response_given'])
            
            rt = timestamp_key - t0_response
            response_ms = self.response_key_to_ms.get(resp_key)
            idx_user = self.keys_responses.index(resp_key)

            # --- Feedback Visuel (Training Mode) ---
            if feedback:
                is_correct = (response_ms == delay_ms)
                user_bar_color = 'green' if is_correct else 'yellow'
                msg_text = "Bonne réponse !" if is_correct else f"Réponse correcte : {delay_ms} ms"
                msg_color = 'green' if is_correct else 'red'
                
                # Redessiner les options
                self.response_title.draw()
                self.response_options_text.draw()
                
                # Soulignement du choix utilisateur
                current_line_width = 5 * self.pixel_scale
                user_line = visual.Line(
                    self.win,
                    start=(self.underline_x_positions[idx_user] - 0.04, self.underline_y_line),
                    end=(self.underline_x_positions[idx_user] + 0.04, self.underline_y_line),
                    lineColor=user_bar_color,
                    lineWidth=current_line_width
                )
                user_line.draw()
                
                # Si incorrect, montrer la bonne réponse
                if not is_correct:
                    try:
                        idx_correct = self.response_values_ms.index(delay_ms)
                        thick_line_width = 6 * self.pixel_scale
                        correct_line = visual.Line(
                            self.win,
                            start=(self.underline_x_positions[idx_correct] - 0.04, self.underline_y_line),
                            end=(self.underline_x_positions[idx_correct] + 0.04, self.underline_y_line),
                            lineColor='red',
                            lineWidth=thick_line_width
                        )
                        correct_line.draw()
                    except ValueError:
                        pass
                
                # Message textuel
                fb_text = visual.TextStim(
                    self.win, text=msg_text, color=msg_color, height=0.05, pos=(0, -0.2)
                )
                fb_text.draw()
                self.win.flip()
                core.wait(1.0)
            
            else:
                # Mode sans feedback : simple soulignement jaune
                underline = visual.Line(
                    self.win,
                    start=(self.underline_x_positions[idx_user] - 0.04, self.underline_y_line),
                    end=(self.underline_x_positions[idx_user] + 0.04, self.underline_y_line),
                    lineColor='yellow',
                    lineWidth=5 * self.pixel_scale
                )
                self.response_title.draw()
                self.response_options_text.draw()
                self.response_instr.draw()
                underline.draw()
                self.win.flip()
                core.wait(0.6)

            self.log_trial_event('response_given', response_key=resp_key, response_ms=response_ms, rt_s=rt)
            
            fb_str = f"| FB: {'Yes' if feedback else 'No':<3}"
            self.logger.log(
                f"Trial {trial_index:>2}/{total_trials:<2} | {condition.upper():<7} | "
                f"Target: {delay_ms:>3}ms | Answer: {str(response_ms):>4}ms | RT: {rt:.3f}s {fb_str}"
            )

        else:
            # --- TIMEOUT ---
            self.ParPort.send_trigger(self.codes['timeout'])
            self.log_trial_event('response_timeout')
            
            too_slow = visual.TextStim(
                self.win, text="Temps de réponse écoulé", color='red', height=0.1
            )
            too_slow.draw()
            self.win.flip()
            core.wait(0.8)
            
            self.logger.warn(
                f"Trial {trial_index:>2}/{total_trials:<2} | {condition.upper():<7} | "
                f"Target: {delay_ms:>3}ms | TIMEOUT"
            )

        # =====================================================================
        # CRITICAL TIMING END: RE-ENABLE GARBAGE COLLECTOR
        # =====================================================================
        gc.enable()
        gc.collect()  # Force collection maintenant pendant l'ITI

        # --- Phase 7: ITI (Inter-Trial Interval) ---
        isi = random.uniform(*self.stim_isi_range)
        self.fixation.draw()
        self.win.flip()
        core.wait(isi)
        
        self.log_trial_event('trial_end', isi_duration=isi)
        
        return True

    # =========================================================================
    # TRIAL GENERATION (Randomisation avec Contraintes)
    # =========================================================================

    def build_trials(self, n_trials, training=False):
        """
        Génère une liste de trials avec randomisation sous contraintes.
        
        Contraintes:
            - Max 3 répétitions consécutives de la même condition
            - Max 2 répétitions consécutives du même délai
        
        Args:
            n_trials (int): Nombre d'essais à générer
            training (bool): Mode training (Active uniquement)
        
        Returns:
            list: Liste de tuples (condition, delay_ms)
        """
        conditions = ['active'] if training else ['active', 'passive']
        
        # Toutes les combinaisons possibles
        unique_types = [(c, d) for c in conditions for d in self.delays_ms]
        
        # Répétition pour atteindre n_trials
        n_full_repeats = n_trials // len(unique_types)
        remainder = n_trials % len(unique_types)
        
        trials = unique_types * n_full_repeats
        if remainder > 0:
            trials.extend(random.sample(unique_types, remainder))
        
        random.shuffle(trials)
        
        # Si training, pas de contraintes strictes
        if training:
            return trials

        # --- Fonction de Détection de Conflit ---
        def is_conflict(trial_list, idx, candidate):
            cand_cond, cand_delay = candidate
            
            # Contrainte 1: Max 3 conditions identiques consécutives
            if idx >= 3:
                if (trial_list[idx-1][0] == trial_list[idx-2][0] == 
                    trial_list[idx-3][0] == cand_cond):
                    return True
            
            # Contrainte 2: Max 2 délais identiques consécutifs
            if idx >= 2:
                if trial_list[idx-1][1] == trial_list[idx-2][1] == cand_delay:
                    return True
            
            return False

        # --- Tentative de Résolution des Contraintes ---
        max_restarts = 10
        for attempt in range(max_restarts):
            try:
                current_trials = trials[:]
                random.shuffle(current_trials)
                
                for i in range(n_trials):
                    if is_conflict(current_trials, i, current_trials[i]):
                        # Cherche un swap valide
                        swapped = False
                        for j in range(i + 1, n_trials):
                            if not is_conflict(current_trials, i, current_trials[j]):
                                current_trials[i], current_trials[j] = current_trials[j], current_trials[i]
                                swapped = True
                                break
                        
                        if not swapped:
                            raise ValueError("Impossible de résoudre les contraintes")
                
                return current_trials
            
            except ValueError:
                continue
        
        self.logger.warn("Contraintes de randomisation non respectées, shuffle simple appliqué.")
        return trials

    # =========================================================================
    # BLOCK EXECUTION
    # =========================================================================

    def run_trial_block(self, n_trials, block_name, phase_tag, feedback):
        """
        Exécute un bloc complet d'essais.
        
        Args:
            n_trials (int): Nombre d'essais
            block_name (str): Nom du bloc (pour logs)
            phase_tag (str): Tag de phase (ex: 'training', 'base')
            feedback (bool): Afficher le feedback
        """
        self.current_phase = phase_tag
        self.log_trial_event('block_start', block_name=block_name, feedback_mode=feedback)
        self.logger.log(f"--- Bloc Start: {block_name} ({n_trials} essais) ---")
        
        trials = self.build_trials(n_trials, training=(phase_tag == 'training'))
        total_trials = len(trials)
        
        for i, (cond, delay) in enumerate(trials, start=1):
            self.run_trial(i, total_trials, cond, delay, feedback=feedback)
        
        self.log_trial_event('block_end', block_name=block_name)
        self.logger.log(f"--- Bloc End: {block_name} ---")

    # =========================================================================
    # CRISIS VALIDATION WINDOW (Spécifique à cette tâche)
    # =========================================================================

    def show_crisis_validation_window(self):
        """
        Fenêtre de validation de crise (spécifique au protocole).
        
        Workflow:
            1. Prompt démarrage crise
            2. Action simulée (2 appuis successifs)
            3. Validation du résultat (succès/échec)
            4. Si échec: Proposition de retry ou quit
        """
        self.current_phase = 'crisis_validation'
        self.current_trial_idx = None
        self.logger.log("=== Entering Crisis Validation Window ===")

        loop_crisis = True
        
        while loop_crisis:
            # --- 1. Prompt Démarrage ---
            msg_launch = visual.TextStim(
                self.win, text='Appuyez pour démarrer la crise', height=0.08
            )
            msg_launch.draw()
            self.win.flip()
            
            self.log_trial_event('crisis_prompt_start')
            self.ParPort.send_trigger(self.codes['crisis_prompt'])
            
            event.clearEvents()
            keys = event.waitKeys(keyList=self.keys_responses + self.keys_quit)
            
            if keys[0] in self.keys_quit:
                should_quit(self.win, quit=True)

            # --- 2. Simulation Action (2 appuis) ---
            self.log_trial_event('crisis_action_started', trigger_key=keys[0])
            self.ParPort.send_trigger(self.codes['crisis_start'])
            
            self.fixation.draw()
            self.win.flip()
            core.wait(0.5)
            
            event.clearEvents()
            keys = event.waitKeys(keyList=self.keys_responses + self.keys_quit)
            
            if keys[0] in self.keys_quit:
                should_quit(self.win, quit=True)
            
            self.ParPort.send_trigger(self.codes['crisis_end'])
            self.log_trial_event('crisis_action_ended', end_key=keys[0])

            # --- 3. Validation Résultat ---
            choice_text = visual.TextStim(
                self.win,
                text='[1-4] Crise réussie     [5-8] Crise échouée',
                height=0.08
            )
            choice_text.draw()
            self.win.flip()
            
            self.log_trial_event('crisis_validation_prompt')
            self.ParPort.send_trigger(self.codes['crisis_valid_prompt'])
            
            core.wait(0.2)
            event.clearEvents()
            keys = event.waitKeys(keyList=self.keys_responses + self.keys_quit)
            
            if keys[0] in self.keys_quit:
                should_quit(self.win, quit=True)
            
            key = keys[0]
            idx = self.keys_responses.index(key)
            success = True if idx < 4 else False
            result_label = 'SUCCESS' if success else 'FAILED'
            
            trigger_code = self.codes['crisis_res_success'] if success else self.codes['crisis_res_fail']
            self.ParPort.send_trigger(trigger_code)
            
            self.log_trial_event('crisis_result_chosen', result=result_label, key=key)
            self.logger.log(f"Crisis Outcome: {result_label}")

            # --- Feedback ---
            confirmation = visual.TextStim(
                self.win, text=f"Résultat : {result_label}", height=0.08
            )
            confirmation.draw()
            self.win.flip()
            core.wait(1.0)

            # --- 4. Retry si Échec ---
            if not success:
                retry_text = visual.TextStim(
                    self.win,
                    text='Recommencer ?\n[1-4] Oui   [5-8] Non (Quitter)',
                    height=0.06
                )
                retry_text.draw()
                self.win.flip()
                
                keys = event.waitKeys(keyList=self.keys_responses + self.keys_quit)
                idx_retry = self.keys_responses.index(keys[0])
                
                if idx_retry >= 4:
                    self.log_trial_event('crisis_retry_decision', choice='no_retry_quit')
                    self.ParPort.send_trigger(self.codes['crisis_retry_no'])
                    should_quit(self.win, quit=True)
                else:
                    self.log_trial_event('crisis_retry_decision', choice='retry')
                    self.ParPort.send_trigger(self.codes['crisis_retry_yes'])
                    self.logger.log("Crisis Retry Selected.")
            else:
                loop_crisis = False

        self.log_trial_event('crisis_phase_end')

    # =========================================================================
    # MAIN EXPERIMENTAL LOOP
    # =========================================================================

    def run(self):
        """
        Boucle principale de l'expérience.
        
        Modes d'exécution:
            - 'training': Entraînement seul (12 essais avec feedback)
            - 'base': Protocole complet (150s rest + 72 base + crisis + 24 block)
            - 'block': Protocole court (150s rest + crisis + 24 block)
        """
        finished_naturally = False
        
        try:
            # =================================================================
            # 1. INSTRUCTIONS
            # =================================================================
            if self.run_type == 'training':
                instructions = (
                    "ENTRAINEMENT - Tâche de Jugement Temporel\n\n"
                    "Vous allez voir une ampoule.\n"
                    "Condition ACTIVE (barre verte) : Appuyez sur le bouton pour l'allumer.\n"
                    "Condition PASSIVE (barre rouge) : Elle s'allumera automatiquement.\n\n"
                    "Après un délai, estimez le temps perçu (100 à 800ms).\n\n"
                    f"Nombre d'essais : {self.n_trials_training} (avec feedback)\n\n"
                    "Appuyez sur 't' (trigger) pour commencer..."
                )
            else:
                instructions = (
                    "Tâche de Jugement Temporel\n\n"
                    "Condition ACTIVE (barre verte) : Appuyez pour allumer l'ampoule.\n"
                    "Condition PASSIVE (barre rouge) : Attente passive.\n\n"
                    "Ensuite, évaluez le délai perçu (100 à 800ms).\n\n"
                    "Appuyez sur ESPACE pour continuer..."
                )
            
            self.show_instructions(instructions)

            # =================================================================
            # 2. ATTENTE TRIGGER IRM
            # =================================================================
            self.wait_for_trigger()

            # =================================================================
            # 3. EXECUTION SELON LE MODE
            # =================================================================
            if self.run_type == 'training':
                # --- Mode Entraînement ---
                self.logger.log(f"Lancement : TRAINING ({self.n_trials_training} essais)")
                self.show_resting_state(duration_s=10.0)
                self.run_trial_block(
                    self.n_trials_training,
                    block_name="TRAINING",
                    phase_tag='training',
                    feedback=True
                )
            
            elif self.run_type == 'base':
                # --- Mode Protocole Complet ---
                self.logger.log(f"Lancement : PROTOCOLE COMPLET (Base:{self.n_trials_base} / Block:{self.n_trials_block})")
                
                # Resting State Initial (150s pour stabilisation BOLD)
                self.show_resting_state(duration_s=150.0)
                
                # Bloc Baseline
                self.run_trial_block(
                    self.n_trials_base,
                    block_name="BASELINE",
                    phase_tag='base',
                    feedback=False
                )
                
                # Crisis Window
                self.show_crisis_validation_window()
                
                # Bloc Post-Crisis
                self.run_trial_block(
                    self.n_trials_block,
                    block_name="POST_CRISIS",
                    phase_tag='run_standard',
                    feedback=False
                )
            
            else:  # run_type == 'block'
                # --- Mode Bloc Court ---
                self.logger.log(f"Lancement : BLOC COURT ({self.n_trials_block} essais)")
                
                # Resting State Initial
                self.show_resting_state(duration_s=150.0)
                
                # Crisis Window
                self.show_crisis_validation_window()
                
                # Bloc Standard
                self.run_trial_block(
                    self.n_trials_block,
                    block_name="STANDARD_BLOCK",
                    phase_tag='run_standard',
                    feedback=False
                )

            finished_naturally = True
            self.logger.ok("Expérience terminée avec succès.")

        except (KeyboardInterrupt, SystemExit):
            self.logger.warn("Interruption manuelle détectée (Echap).")
        
        except Exception as e:
            self.logger.err(f"ERREUR CRITIQUE : {e}")
            import traceback
            traceback.print_exc()
            raise
        
        finally:
            # =================================================================
            # BLOC DE SECURITE (S'exécute TOUJOURS)
            # =================================================================
            self.logger.log("Nettoyage et sauvegarde...")
            
            # 1. Arrêt EyeTracker
            if self.eyetracker_actif:
                self.EyeTracker.stop_recording()
                self.EyeTracker.send_message("END_EXP")
                self.EyeTracker.close_and_transfer_data(self.data_dir)
            
            # 2. Sauvegarde des données (méthode héritée)
            self.save_data(
                data_list=self.global_records,
                filename_suffix=f"_{self.run_type}"
            )
            
            # 3. Écran de fin (si terminé naturellement)
            if finished_naturally:
                end_msg = "Fin de la session.\nMerci pour votre participation."
                self.show_instructions(end_msg)
                core.wait(3.0)
            
            self.logger.log("Fermeture de la tâche.")


# =============================================================================
# POINT D'ENTREE (Tests Autonomes)
# =============================================================================

if __name__ == "__main__":
    """Script de test autonome."""
    from psychopy import visual
    
    win = visual.Window(
        size=(1024, 768),
        fullscr=False,
        color='black',
        units='norm',
        allowGUI=True
    )
    
    task = TemporalJudgement(
        win=win,
        nom="TEST001",
        session="1",
        mode="behavioral",
        run_type="training",  # Test rapide
        n_trials_training=3,
        enregistrer=True,
        eyetracker_actif=False,
        parport_actif=False
    )
    
    try:
        task.run()
    finally:
        win.close()
        core.quit()