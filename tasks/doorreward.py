"""
Door Reward Task (fMRI / Behavioral)
------------------------------------
Tâche de prise de décision avec récompense (Portes).
Refactorisation basée sur le template 'TemporalJudgement'.

Auteur : [Votre Nom / Labo]
Date de refactorisation : Janvier 2026
"""

import random
import csv
import os
import sys
import time
from datetime import datetime

# --- PsychoPy Imports ---
from psychopy import visual, event, core

# --- Local Imports ---
from utils.hardware_manager import setup_hardware
from utils.utils import should_quit
from utils.logger import get_logger

class DoorReward:
    """
    Classe principale gérant la logique de l'expérience Door Reward.
    """

    def __init__(self, win, nom, session, n_trials, reward_probability, mode, 
                 enregistrer=True, eyetracker_actif=False, parport_actif=False, **kwargs):
        
        # --- Paramètres Généraux ---
        self.win = win
        self.nom = str(nom)
        self.session = str(session)
        self.n_trials = n_trials
        self.reward_prob = reward_probability
        self.mode = mode
        self.enregistrer = enregistrer
        self.eyetracker_actif = eyetracker_actif
        self.parport_actif = parport_actif

        # --- Gestion des Chemins ---
        # On remonte d'un niveau si on est dans 'tasks/' pour trouver la racine
        base_dir = os.path.dirname(os.path.abspath(__file__))
        if os.path.basename(base_dir) == 'tasks':
            self.root_dir = os.path.dirname(base_dir)
        else:
            self.root_dir = base_dir

        self.data_dir = os.path.join(self.root_dir, 'data', 'doorreward')
        self.img_dir = os.path.join(self.root_dir, 'image')
        
        if self.enregistrer and not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        # --- Variables de Session ---
        self.global_records = []
        self.total_gain = 0
        self.current_trial_idx = 0
        self.start_timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.task_clock = core.Clock()

        # --- Logger ---
        self.logger = get_logger()
        # Utilisation de .log() au lieu de .info()
        self.logger.log(f"Initialisation DoorReward : {self.nom} - Session {self.session}")

        # --- Codes TTL ---
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

        # --- Configuration des Touches ---
        # Format unifié pour FMRI et Comportemental
        if self.mode == "fmri":
            self.keys = {'choices': ['b', 'y', 'g'], 'trigger': 't', 'quit': ['escape', 'q']}
            self.choice_map = {'b': 0, 'y': 1, 'g': 2} # Mapping touche -> index porte
        else:
            self.keys = {'choices': ['a', 'z', 'e'], 'trigger': 't', 'quit': ['escape', 'q']}
            self.choice_map = {'a': 0, 'z': 1, 'e': 2}

        # --- Initialisation Hardware ---
        self._init_hardware()

        # --- Initialisation Visuels ---
        self._setup_visuals()

    def _init_hardware(self):
        """Initialise le port parallèle et l'eyetracker via le manager."""
        self.logger.log("Setup Hardware...")
        self.ParPort, self.EyeTracker = setup_hardware(self.parport_actif, self.eyetracker_actif, self.win)
        
        # Nom fichier EyeTracker (Max 8 chars : DR + 3 lettres sujet + Session)
        # Ex: DR_ALE01
        et_filename = f"DR_{self.nom[:3]}{self.session}"
        self.EyeTracker.initialize(file_name=et_filename)

    def _setup_visuals(self):
        """Préchargement des stimuli visuels."""
        # Chemins images
        img_closed = os.path.join(self.img_dir, 'porte_ferme.png')
        img_open = os.path.join(self.img_dir, 'porte_ouverte.png')

        # Positions : Gauche, Centre, Droite
        self.door_positions = [(-0.5, 0), (0, 0), (0.5, 0)]
        self.doors_closed_stim = [] 
        self.doors_open_stim = []   
        
        # Création des sprites (Images)
        for pos in self.door_positions:
            self.doors_closed_stim.append(
                visual.ImageStim(self.win, image=img_closed, pos=pos, size=(0.3, 0.6), interpolate=True)
            )
            self.doors_open_stim.append(
                visual.ImageStim(self.win, image=img_open, pos=pos, size=(0.3, 0.6), interpolate=True)
            )

        # Textes
        self.feedback_stim = visual.TextStim(self.win, text="", height=0.15, bold=True)
        self.score_stim = visual.TextStim(self.win, text="Total: 0 €", pos=(0, -0.6), height=0.08)
        self.fixation = visual.TextStim(self.win, text='+', color='white', height=0.15)
        self.text_instr = visual.TextStim(self.win, text="", color='white', height=0.08, wrapWidth=1.8)

    # =========================================================================
    # LOGGING & DATA
    # =========================================================================

    def log_step(self, event_type, **kwargs):
        """Enregistre une ligne de donnée et envoie un message ET."""
        current_time = self.task_clock.getTime()
        
        # Message EyeTracker
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

    def save_results(self):
        """Sauvegarde les données en CSV."""
        if not self.enregistrer or not self.global_records:
            return

        fname = f"{self.nom}_Reward_Sess{self.session}_{self.start_timestamp}.csv"
        path = os.path.join(self.data_dir, fname)
        
        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                # Récupération dynamique de toutes les clés
                all_keys = set().union(*(r.keys() for r in self.global_records))
                writer = csv.DictWriter(f, fieldnames=sorted(list(all_keys)))
                writer.writeheader()
                writer.writerows(self.global_records)
            # Utilisation de .ok() pour le succès
            self.logger.ok(f"Données sauvegardées : {path}")
        except Exception as e:
            # Utilisation de .err() pour l'erreur
            self.logger.err(f"Erreur sauvegarde CSV : {e}")

    # =========================================================================
    # UTILS & TIMING
    # =========================================================================

    def smart_wait(self, duration_s):
        """
        Attente active précise vérifiant les touches 'quit'.
        Retourne False si une demande d'arrêt a été faite.
        """
        timer = core.CountdownTimer(duration_s)
        while timer.getTime() > 0:
            # 1. Vérif touches
            keys = event.getKeys(keyList=self.keys['quit'])
            if keys:
                # Utilisation de .warn() pour le warning
                self.logger.warn("Abandon détecté (Echap).")
                should_quit(self.win)
                return False
            
            # 2. Vérif Trigger (TTL) pour logging passif
            ttl = event.getKeys(keyList=[self.keys['trigger']], timeStamped=self.task_clock)
            for k, t in ttl:
                self.log_step('ttl_pulse_unexpected', real_time=t)

            # 3. Pause minime pour CPU
            core.wait(0.001)
            
        return True

    def show_resting_state(self, duration_s=10):
        """Affiche la croix de fixation pour le repos."""
        self.fixation.draw()
        self.win.flip()
        
        self.ParPort.send_trigger(self.codes['rest_start'])
        self.log_step('rest_start', duration=duration_s)
        
        if not self.smart_wait(duration_s):
            return False

        self.ParPort.send_trigger(self.codes['rest_end'])
        self.log_step('rest_end')
        return True

    # =========================================================================
    # CORE TRIAL LOGIC
    # =========================================================================

    def run_trial(self, trial_num):
        """
        Exécute un essai unique.
        Retourne False si l'utilisateur a voulu quitter, True sinon.
        """
        self.current_trial_idx = trial_num
        
        # --- 1. PORTES FERMEES (Onset) ---
        for d in self.doors_closed_stim:
            d.opacity = 1
            d.draw()
        self.score_stim.draw()
        self.win.flip()
        
        onset_time = self.task_clock.getTime()
        self.ParPort.send_trigger(self.codes['doors_onset'])
        self.log_step('stim_onset_doors')

        # --- 2. REPONSE (Wait for Keys) ---
        event.clearEvents()
        wait_list = self.keys['choices'] + self.keys['quit']
        keys = event.waitKeys(maxWait=4.0, keyList=wait_list, timeStamped=self.task_clock)
        
        choice_idx = -1
        rt = 0
        
        if not keys:
            # --- TIMEOUT ---
            self.ParPort.send_trigger(self.codes['timeout'])
            self.log_step('timeout')
            
            self.feedback_stim.text = "Trop lent !"
            self.feedback_stim.color = 'red'
            self.feedback_stim.pos = (0, 0)
            self.feedback_stim.draw()
            self.win.flip()
            
            if not self.smart_wait(1.0): return False
            return True # On passe au suivant
        
        else:
            # --- REPONSE VALIDEE ---
            key_pressed, rt_abs = keys[0]
            rt = rt_abs - onset_time
            
            if key_pressed in self.keys['quit']:
                should_quit(self.win)
                return False

            # Conversion touche -> index (0, 1, 2)
            choice_idx = self.choice_map.get(key_pressed, -1)
            
            self.ParPort.send_trigger(self.codes['choice_made'])
            self.log_step('response_made', key=key_pressed, choice_idx=choice_idx, rt=rt)

        # --- 3. OUVERTURE PORTE (Selection) ---
        for i in range(3):
            if i == choice_idx:
                self.doors_open_stim[i].draw()
            else:
                self.doors_closed_stim[i].draw()
        self.score_stim.draw()
        self.win.flip()
        
        self.ParPort.send_trigger(self.codes['door_open'])
        
        # Délai pré-feedback (Jitter 1s - 2s)
        if not self.smart_wait(random.uniform(1.0, 2.0)): return False

        # --- 4. FEEDBACK (Calcul gain) ---
        is_win = random.random() < self.reward_prob
        gain = 10 if is_win else 0
        self.total_gain += gain
        
        msg = "+ 10 €" if is_win else "0 €"
        col = 'lime' if is_win else 'grey'
        trig = self.codes['feedback_win'] if is_win else self.codes['feedback_neutral']

        self.ParPort.send_trigger(trig)
        self.log_step('feedback_outcome', is_win=is_win, gain=gain)

        # Affichage Feedback
        for i in range(3):
            if i == choice_idx:
                self.doors_open_stim[i].draw()
            else:
                self.doors_closed_stim[i].draw()
                
        self.feedback_stim.text = msg
        self.feedback_stim.color = col
        # Position du texte sur la porte choisie
        self.feedback_stim.pos = (self.door_positions[choice_idx][0], 0) 
        self.feedback_stim.draw()
        
        self.score_stim.text = f"Total: {self.total_gain} €"
        self.score_stim.draw()
        self.win.flip()

        self.logger.log(f"Trial {trial_num} | Choice: {choice_idx} | Win: {is_win} | Gain: {gain}")

        # Délai Feedback (1.5s)
        if not self.smart_wait(1.5): return False

        # --- 5. ITI (Croix de fixation) ---
        self.fixation.draw()
        self.win.flip()
        
        # Jitter ITI (1s - 2.5s)
        if not self.smart_wait(random.uniform(1.0, 2.5)): return False

        return True

    # =========================================================================
    # MAIN LOOP
    # =========================================================================

    def run(self):
        """
        Boucle principale avec gestion robuste des erreurs (try/finally).
        """
        finished_naturally = False
        
        try:
            # 1. Instructions
            instr = (
                "Tâche de Récompense\n\n"
                "3 portes vont apparaître.\n"
                "Choisissez-en une pour trouver le trésor.\n\n"
                f"Touches : {self.keys['choices']}\n\n"
                "Appuyez sur 't' pour commencer..."
            )
            self.text_instr.text = instr
            self.text_instr.draw()
            self.win.flip()
            
            # 2. Attente Trigger
            self.logger.log("En attente du Trigger IRM...")
            # On lance l'ET avant le trigger pour être sûr d'avoir le début
            self.EyeTracker.start_recording()
            
            event.waitKeys(keyList=[self.keys['trigger']])
            
            # Reset Horloge & Marqueurs
            self.task_clock.reset()
            self.ParPort.send_trigger(self.codes['start_exp'])
            self.EyeTracker.send_message("START_EXP")
            self.log_step('experiment_start')
            
            self.logger.ok("Trigger reçu. Start !")

            # 3. Repos Initial (stabilisation signal BOLD)
            if not self.show_resting_state(duration_s=5.0):
                raise KeyboardInterrupt # Sortie propre si annulé

            # 4. Boucle d'essais
            for i in range(1, self.n_trials + 1):
                continue_exp = self.run_trial(i)
                if not continue_exp:
                    raise KeyboardInterrupt
            
            # 5. Repos Final
            self.show_resting_state(duration_s=5.0)
            
            finished_naturally = True

        except (KeyboardInterrupt, SystemExit):
            self.logger.warn("Interruption manuelle (Echap) ou fin prématurée.")
        
        except Exception as e:
            # Utilisation de .err() pour l'erreur critique
            self.logger.err(f"ERREUR CRITIQUE PENDANT LA TACHE : {e}")
            raise e # On relève l'erreur pour le debug, mais le finally s'exécutera
            
        finally:
            # --- BLOC DE SECURITE ---
            # S'exécute TOUJOURS, même en cas de crash
            self.logger.log("Fermeture et sauvegarde...")
            
            # 1. Arrêt EyeTracker
            self.EyeTracker.stop_recording()
            self.EyeTracker.send_message("END_EXP")
            self.EyeTracker.close_and_transfer_data(self.data_dir)
            
            # 2. Sauvegarde CSV
            self.save_results()
            
            # 3. Écran de fin (si fini naturellement)
            if finished_naturally:
                end_msg = f"Fin de l'expérience.\nGains totaux : {self.total_gain} €"
                self.text_instr.text = end_msg
                self.text_instr.draw()
                self.win.flip()
                core.wait(3.0)