"""
BaseTask - Classe mère pour les tâches fMRI/Comportementales
------------------------------------------------------------
Gère l'initialisation commune, le hardware, les chemins et les
fonctions de timing standard (Trigger, Resting State).

Auteur : Clément BARBE / CENIR
Date : Janvier 2026
"""

import os
import sys
from datetime import datetime
from psychopy import visual, event, core
from utils.logger import get_logger
from utils.hardware_manager import setup_hardware
from utils.utils import should_quit

class BaseTask:
    def __init__(self, win, nom, session, task_name, folder_name, 
                 eyetracker_actif=False, parport_actif=False, 
                 enregistrer=True, et_prefix='TSK'):
        """
        Args:
            win: Fenêtre PsychoPy
            nom (str): ID Sujet
            session (str): ID Session
            task_name (str): Nom affiché (ex: "Door Reward")
            folder_name (str): Nom du dossier de data (ex: "doorreward")
            et_prefix (str): Préfixe 2-3 lettres pour le fichier Eyelink (ex: 'DR')
        """
        self.win = win
        self.nom = str(nom)
        self.session = str(session)
        self.task_name = task_name
        self.et_prefix = et_prefix
        
        # Hardware flags
        self.eyetracker_actif = eyetracker_actif
        self.parport_actif = parport_actif
        self.enregistrer = enregistrer

        # Logger
        self.logger = get_logger()
        
        # 1. Gestion des Chemins (Encapsulée)
        self._init_paths(folder_name)
        
        # 2. Hardware (Encapsulé)
        self._init_hardware()

        # 3. Stimuli communs (Instructions / Fixation)
        self._init_common_stimuli()

        # Horloge principale
        self.task_clock = core.Clock()
        self.codes = {} # À définir dans les classes enfants

    def _init_paths(self, folder_name):
        """Détecte la racine et crée le dossier de données."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Gestion du cas où le script est dans un sous-dossier 'tasks'
        if os.path.basename(base_dir) == 'tasks':
            self.root_dir = os.path.dirname(base_dir)
        else: # Cas où utils est importé depuis la racine
             # Attention : cette logique suppose que base_task.py est importé par le script principal
             # Si base_task est dans utils/, on doit remonter
             self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.data_dir = os.path.join(self.root_dir, 'data', folder_name)
        self.img_dir = os.path.join(self.root_dir, 'image')

        if self.enregistrer and not os.path.exists(self.data_dir):
            try:
                os.makedirs(self.data_dir)
                self.logger.log(f"Dossier créé : {self.data_dir}")
            except OSError as e:
                self.logger.err(f"Erreur création dossier data : {e}")

    def _init_hardware(self):
        """Initialise le port parallèle et l'eyetracker via le manager."""
        self.logger.log(f"Setup Hardware pour {self.task_name}...")
        
        try:
            # Appel au hardware_manager qui renvoie les instances
            self.ParPort, self.EyeTracker = setup_hardware(
                self.parport_actif, 
                self.eyetracker_actif, 
                self.win
            )
            
            # Configuration EyeTracker spécifique
            if self.eyetracker_actif:
                # Nom fichier EyeTracker (Max 8 chars : PRE + 3 lettres sujet + Session)
                # Ex: DR_ALE01 (DR = Prefix, ALE = Nom, 01 = Session)
                short_nom = self.nom[:3] if len(self.nom) >= 3 else self.nom
                et_filename = f"{self.et_prefix}_{short_nom}{self.session}"
                
                # Sécurité longueur nom de fichier (max 8 chars DOS)
                if len(et_filename) > 8:
                    et_filename = et_filename[:8]
                    self.logger.warn(f"Nom fichier ET tronqué à : {et_filename}")
                
                self.EyeTracker.initialize(file_name=et_filename)
                
        except Exception as e:
            self.logger.err(f"Hardware Init Error: {e}")
            raise e

    def _init_common_stimuli(self):
        """Prépare les stimuli textuels utilisés partout."""
        self.fixation = visual.TextStim(self.win, text='+', height=0.1, color='white')
        self.instr_stim = visual.TextStim(self.win, text='', height=0.06, color='white', wrapWidth=1.5)

    # --- MÉTHODES UTILISATEUR ENCAPSULÉES ---

    def show_instructions(self, text_override=None):
        """
        Affiche les instructions et attend une touche.
        """
        msg = text_override if text_override else f"Bienvenue dans la tâche : {self.task_name}\n\nAppuyez sur une touche pour voir les consignes spécifiques."
        
        self.instr_stim.text = msg
        self.instr_stim.draw()
        self.win.flip()
        
        # Petite pause pour éviter de passer l'écran trop vite si l'utilisateur martèle les touches
        core.wait(0.5) 
        event.waitKeys()

    def wait_for_trigger(self, trigger_key='t'):
        """
        Attente standardisée du trigger IRM.
        Reset l'horloge et envoie le code 'start_exp'.
        """
        self.instr_stim.text = "En attente du trigger IRM..."
        self.instr_stim.draw()
        self.win.flip()
        
        self.logger.log("Waiting for trigger...")
        
        # Attente bloquante
        event.waitKeys(keyList=[trigger_key])
        
        # Démarrage immédiat
        self.task_clock.reset() 
        
        # Envoi marker start si défini
        start_code = self.codes.get('start_exp', 255)
        self.ParPort.send_trigger(start_code)
        
        if self.eyetracker_actif:
            self.EyeTracker.start_recording()
            self.EyeTracker.send_message(f"START_{self.task_name.upper()}")

        self.logger.log(f"Trigger reçu. Start Code: {start_code}")

    def show_resting_state(self, duration_s=10.0, code_start_key='rest_start', code_end_key='rest_end'):
        """
        Affiche la croix de fixation pour une durée précise (Baseline).
        Gère les triggers de début et de fin de repos.
        """
        self.logger.log(f"Resting state: {duration_s}s")
        
        # Trigger Début Repos
        c_start = self.codes.get(code_start_key, 0)
        self.ParPort.send_trigger(c_start)
        if self.eyetracker_actif: self.EyeTracker.send_message("REST_START")

        # Affichage
        self.fixation.draw()
        self.win.flip()
        
        # Attente précise
        core.wait(duration_s)
        
        # Trigger Fin Repos (optionnel, parfois on enchaîne direct sur un essai)
        if code_end_key:
            c_end = self.codes.get(code_end_key, 0)
            self.ParPort.send_trigger(c_end)
            if self.eyetracker_actif: self.EyeTracker.send_message("REST_END")

    def save_data(self, data_list=None, filename_suffix=""):
        """
        Sauvegarde générique CSV.
        Si data_list est None, tente de sauvegarder self.global_records.
        """
        # 1. Gestion automatique de la liste de données
        if data_list is None:
            data_list = getattr(self, 'global_records', [])

        if not self.enregistrer or not data_list:
            self.logger.warn("Aucune donnée à sauvegarder (ou enregistrement désactivé).")
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        fname = f"{self.nom}_{self.task_name.replace(' ', '')}{filename_suffix}_{timestamp}.csv"
        path = os.path.join(self.data_dir, fname)
        
        try:
            import csv
            # On récupère toutes les clés possibles (au cas où certaines lignes n'ont pas toutes les colonnes)
            keys = set().union(*(d.keys() for d in data_list))
            
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=sorted(list(keys))) # Sorted pour l'ordre
                writer.writeheader()
                writer.writerows(data_list)
            self.logger.log(f"Data saved: {path}")
            
        except Exception as e:
            self.logger.err(f"CRITICAL SAVE ERROR: {e}")
            # Sauvegarde brute de secours
            with open(path + '.bak', 'w') as f:
                f.write(str(data_list))