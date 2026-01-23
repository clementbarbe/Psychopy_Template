"""
door_reward.py
--------------
Tâche de prise de décision avec récompense (Portes).
Hérite de BaseTask pour bénéficier de l'infrastructure commune.

Architecture:
    - Séparation claire des responsabilités
    - Réutilisation maximale du code de base
    - Logique métier isolée
    - Gestion d'erreurs robuste

Auteur : Clément BARBE / CENIR
Date : Janvier 2026
"""

import random
from psychopy import visual, event, core
from utils.base_task import BaseTask

class DoorReward(BaseTask):
    """
    Tâche de choix entre 3 portes avec feedback de récompense.
    
    Workflow:
        1. Affichage simultané de 3 portes fermées
        2. Choix du participant (3 touches possibles)
        3. Ouverture de la porte choisie
        4. Feedback : Gain (10€) ou Neutre (0€)
        5. ITI variable
    """

    def __init__(self, win, nom, session, n_trials=40, reward_probability=0.5, 
                 mode="fmri", enregistrer=True, eyetracker_actif=False, 
                 parport_actif=False, **kwargs):
        """
        Args:
            win: Fenêtre PsychoPy
            nom (str): ID Participant
            session (str): Numéro de session
            n_trials (int): Nombre d'essais
            reward_probability (float): Probabilité de gain (0.0 - 1.0)
            mode (str): 'fmri' ou 'behavioral' (change le mapping des touches)
            enregistrer (bool): Sauvegarder les données
            eyetracker_actif (bool): Activer l'EyeTracker
            parport_actif (bool): Activer le port parallèle
        """
        
        # --- Appel au constructeur parent ---
        super().__init__(
            win=win, 
            nom=nom, 
            session=session, 
            task_name="Door Reward",
            folder_name="doorreward",
            eyetracker_actif=eyetracker_actif,
            parport_actif=parport_actif,
            enregistrer=enregistrer,
            et_prefix='DR'  # Préfixe pour l'EyeTracker
        )

        # --- Paramètres Spécifiques de la Tâche ---
        self.n_trials = n_trials
        self.reward_prob = reward_probability
        self.mode = mode.lower()
        self.total_gain = 0
        self.current_trial_idx = 0

        self.codes = {
            'start_exp': 10, 
            'rest_start': 20, 
            'rest_end': 21,
            'doors_onset': 30, 
            'choice_made': 40, 
            'door_open': 50,
            'feedback_win': 60, 
            'feedback_neutral': 61, 
            'timeout': 99
        }

        # --- Configuration du Mapping des Touches ---
        if self.mode == "fmri":
            self.keys_choices = ['b', 'y', 'g']
            self.choice_map = {'b': 0, 'y': 1, 'g': 2}  # Index des portes (G, C, D)
        else:
            self.keys_choices = ['a', 'z', 'e']
            self.choice_map = {'a': 0, 'z': 1, 'e': 2}
        
        self.keys_quit = ['escape', 'q']
        self.logger.log(f"Mapping touches ({self.mode}): {self.keys_choices}")

        # --- Préchargement des Stimuli Visuels ---
        self._setup_task_stimuli()

        self.logger.ok(f"DoorReward initialisée : {self.n_trials} essais, p(win)={self.reward_prob}")

        self.global_records = []



    def _setup_task_stimuli(self):
        """
        Charge et prépare tous les stimuli visuels spécifiques à la tâche.
        Utilise self.img_dir défini dans BaseTask.
        """
        import os
        
        # --- Chemins Images ---
        img_closed = os.path.join(self.img_dir, 'porte_ferme.png')
        img_open = os.path.join(self.img_dir, 'porte_ouverte.png')

        # --- Positions des 3 Portes (Gauche, Centre, Droite) ---
        self.door_positions = [(-0.5, 0), (0, 0), (0.5, 0)]
        
        # --- Création des Stimuli Portes ---
        self.doors_closed_stim = []
        self.doors_open_stim = []
        
        for pos in self.door_positions:
            # Portes Fermées
            self.doors_closed_stim.append(
                visual.ImageStim(
                    self.win, 
                    image=img_closed, 
                    pos=pos, 
                    size=(0.3, 0.6), 
                    interpolate=True
                )
            )
            # Portes Ouvertes
            self.doors_open_stim.append(
                visual.ImageStim(
                    self.win, 
                    image=img_open, 
                    pos=pos, 
                    size=(0.3, 0.6), 
                    interpolate=True
                )
            )

        # --- Textes Spécifiques ---
        self.feedback_stim = visual.TextStim(
            self.win, 
            text="", 
            height=0.15, 
            bold=True,
            font='Arial'
        )
        
        self.score_stim = visual.TextStim(
            self.win, 
            text="Total: 0 €", 
            pos=(0, -0.7), 
            height=0.08,
            color='white'
        )

        self.logger.log("Stimuli Door Reward chargés.")

    # =========================================================================
    # LOGGING & DATA MANAGEMENT (Méthodes Utilitaires)
    # =========================================================================

    def log_trial_event(self, event_type, **kwargs):
        """
        Enregistre un événement lié à un essai (wrapper amélioré).
        
        Args:
            event_type (str): Type d'événement (ex: 'stim_onset', 'response')
            **kwargs: Données additionnelles (RT, choix, gain, etc.)
        """
        current_time = self.task_clock.getTime()
        
        # Message EyeTracker avec contexte
        if self.eyetracker_actif:
            self.EyeTracker.send_message(
                f"TRIAL_{self.current_trial_idx:03d}_{event_type.upper()}"
            )
        
        # Enregistrement structuré
        entry = {
            'participant': self.nom,
            'session': self.session,
            'trial': self.current_trial_idx,
            'time_s': round(current_time, 5),
            'event_type': event_type,
            'total_gain': self.total_gain
        }
        entry.update(kwargs)  # Fusion avec données spécifiques
        
        self.global_records.append(entry)

    # =========================================================================
    # CORE TASK LOGIC (Logique Métier)
    # =========================================================================

    def run_trial(self, trial_num):
        """
        Exécute un essai complet de la Door Reward Task.
        
        Phases:
            1. Affichage des portes fermées (Onset)
            2. Attente de la réponse (Max 4s)
            3. Ouverture de la porte choisie
            4. Feedback (Gain ou Neutre)
            5. ITI (Fixation)
        
        Args:
            trial_num (int): Numéro de l'essai courant
        
        Returns:
            bool: True si l'essai s'est terminé normalement, False si interruption
        """
        self.current_trial_idx = trial_num
        
        # =====================================================================
        # PHASE 1 : AFFICHAGE DES PORTES FERMEES
        # =====================================================================
        for door in self.doors_closed_stim:
            door.opacity = 1
            door.draw()
        
        self.score_stim.draw()
        self.win.flip()
        
        onset_time = self.task_clock.getTime()
        self.ParPort.send_trigger(self.codes['doors_onset'])
        self.log_trial_event('stim_onset_doors')

        # =====================================================================
        # PHASE 2 : COLLECTE DE LA REPONSE
        # =====================================================================
        event.clearEvents()
        wait_keys = self.keys_choices + self.keys_quit
        
        keys = event.waitKeys(
            maxWait=4.0,  # Fenêtre de réponse de 4 secondes
            keyList=wait_keys,
            timeStamped=self.task_clock
        )
        
        # --- TIMEOUT (Aucune réponse) ---
        if not keys:
            self.ParPort.send_trigger(self.codes['timeout'])
            self.log_trial_event('timeout')
            
            self.feedback_stim.text = "Trop lent !"
            self.feedback_stim.color = 'red'
            self.feedback_stim.pos = (0, 0)
            self.feedback_stim.draw()
            self.win.flip()
            
            core.wait(1.5)
            self.logger.warn(f"Trial {trial_num}: Timeout")
            return True  # Passe à l'essai suivant
        
        # --- GESTION DE LA REPONSE ---
        key_pressed, rt_abs = keys[0]
        rt = rt_abs - onset_time
        
        # Vérif touche Quit
        if key_pressed in self.keys_quit:
            self.logger.warn("Interruption utilisateur (Echap)")
            from utils.utils import should_quit
            should_quit(self.win)
            return False
        
        # Conversion touche -> index porte (0=Gauche, 1=Centre, 2=Droite)
        choice_idx = self.choice_map.get(key_pressed, -1)
        
        if choice_idx == -1:
            self.logger.warn(f"Touche invalide: {key_pressed}")
            return True
        
        self.ParPort.send_trigger(self.codes['choice_made'])
        self.log_trial_event('response_made', key=key_pressed, choice_idx=choice_idx, rt=rt)

        # =====================================================================
        # PHASE 3 : OUVERTURE DE LA PORTE CHOISIE
        # =====================================================================
        for i in range(3):
            if i == choice_idx:
                self.doors_open_stim[i].draw()  # Porte choisie ouverte
            else:
                self.doors_closed_stim[i].draw()  # Autres fermées
        
        self.score_stim.draw()
        self.win.flip()
        
        self.ParPort.send_trigger(self.codes['door_open'])
        
        # Délai pré-feedback (Jitter 1-2s pour découplage temporel)
        core.wait(random.uniform(1.0, 2.0))

        # =====================================================================
        # PHASE 4 : FEEDBACK DE RECOMPENSE
        # =====================================================================
        # Détermination du gain (probabiliste)
        is_win = random.random() < self.reward_prob
        gain = 10 if is_win else 0
        self.total_gain += gain
        
        # Configuration visuelle du feedback
        msg = "+ 10 €" if is_win else "0 €"
        color = 'lime' if is_win else 'grey'
        trigger_code = self.codes['feedback_win'] if is_win else self.codes['feedback_neutral']

        self.ParPort.send_trigger(trigger_code)
        self.log_trial_event('feedback_outcome', is_win=is_win, gain=gain, choice=choice_idx)

        # Affichage du feedback sur la porte choisie
        for i in range(3):
            if i == choice_idx:
                self.doors_open_stim[i].draw()
            else:
                self.doors_closed_stim[i].draw()
        
        self.feedback_stim.text = msg
        self.feedback_stim.color = color
        self.feedback_stim.pos = (self.door_positions[choice_idx][0], 0.3)
        self.feedback_stim.draw()
        
        self.score_stim.text = f"Total: {self.total_gain} €"
        self.score_stim.draw()
        self.win.flip()

        self.logger.log(f"Trial {trial_num} | Choice: {choice_idx} | Win: {is_win} | RT: {rt:.3f}s")

        # Durée affichage feedback
        core.wait(1.5)

        # =====================================================================
        # PHASE 5 : ITI (Inter-Trial Interval)
        # =====================================================================
        self.fixation.draw()
        self.win.flip()
        
        # ITI variable (Jitter 1-2.5s)
        iti_duration = random.uniform(1.0, 2.5)
        core.wait(iti_duration)
        
        self.log_trial_event('iti_end', iti_duration=iti_duration)

        return True

    # =========================================================================
    # MAIN EXPERIMENTAL LOOP
    # =========================================================================

    def run(self):
        """
        Boucle principale de l'expérience avec gestion robuste des erreurs.
        
        Workflow:
            1. Instructions
            2. Attente trigger IRM
            3. Resting State initial
            4. Boucle d'essais
            5. Resting State final
            6. Fin et sauvegarde
        """
        finished_naturally = False
        
        try:
            # =================================================================
            # 1. INSTRUCTIONS
            # =================================================================
            instructions_text = (
                "Tâche de Récompense\n\n"
                "Trois portes vont apparaître à l'écran.\n"
                "Choisissez-en une pour trouver le trésor !\n\n"
                f"Touches : {' / '.join(self.keys_choices)}\n"
                "(Gauche / Centre / Droite)\n\n"
                "Appuyez sur une touche pour voir les consignes détaillées..."
            )
            
            self.show_instructions(instructions_text)
            
            # Instructions détaillées (2e écran)
            detailed_instr = (
                "CONSIGNES DETAILLEES\n\n"
                "• Chaque porte peut contenir un trésor de 10€ ou rien (0€).\n"
                "• Vous avez 4 secondes pour choisir une porte.\n"
                "• Si vous êtes trop lent, l'essai est perdu.\n"
                "• Essayez de maximiser vos gains !\n\n"
                f"Nombre d'essais : {self.n_trials}\n\n"
                "Appuyez sur 't' (trigger IRM) pour commencer..."
            )
            
            self.show_instructions(detailed_instr)

            # =================================================================
            # 2. ATTENTE TRIGGER IRM (Utilise la méthode de BaseTask)
            # =================================================================
            self.wait_for_trigger()

            # =================================================================
            # 3. RESTING STATE INITIAL (Stabilisation BOLD)
            # =================================================================
            self.show_resting_state(duration_s=5.0, 
                                   code_start_key='rest_start', 
                                   code_end_key='rest_end')

            # =================================================================
            # 4. BOUCLE D'ESSAIS
            # =================================================================
            for trial_num in range(1, self.n_trials + 1):
                continue_exp = self.run_trial(trial_num)
                
                if not continue_exp:
                    raise KeyboardInterrupt  # Interruption propre

            # =================================================================
            # 5. RESTING STATE FINAL
            # =================================================================
            self.show_resting_state(duration_s=5.0)
            
            # =================================================================
            # 6. ECRAN DE FIN
            # =================================================================
            end_message = (
                f"Fin de l'expérience !\n\n"
                f"Gains totaux : {self.total_gain} €\n\n"
                "Merci pour votre participation."
            )
            
            self.show_instructions(end_message)
            core.wait(3.0)
            
            finished_naturally = True
            self.logger.ok(f"Expérience terminée. Gains: {self.total_gain}€")

        except (KeyboardInterrupt, SystemExit):
            self.logger.warn("Interruption manuelle de l'expérience.")
        
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
            
            # 2. Sauvegarde des données (utilise la méthode de BaseTask)
            self.save_data(
                data_list=self.global_records,
                filename_suffix=""  # Pas de suffixe additionnel
            )
            
            # 3. Message final
            if finished_naturally:
                self.logger.ok("Expérience terminée avec succès.")
            else:
                self.logger.warn("Expérience terminée prématurément.")

