import os
import sys
import random
import gc

# Import relatif si exécuté depuis tasks/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from psychopy import visual, event, core
from utils.base_task import BaseTask
from utils.utils import should_quit


class NBack(BaseTask):
    """
    N-Back Task (fMRI / Behavioral)
    - Hérite de BaseTask (trigger, resting state, save_data, hardware)
    - Timing fMRI précis avec planning ABSOLU
    - Correction du drift : ISI variable pour absorber les retards d'affichage
    """

    def __init__(self, win, nom, session='01', enregistrer=True,
                 mode='fmri', N=2, n_trials=30, target_ratio=0.3,
                 stim_dur=0.5, isi=1.5,
                 parport_actif=True, eyetracker_actif=False, **kwargs):

        super().__init__(
            win=win,
            nom=nom,
            session=session,
            task_name=f"NBack_{int(N)}",
            folder_name="nback",
            eyetracker_actif=eyetracker_actif,
            parport_actif=(mode == 'fmri' and parport_actif),
            enregistrer=enregistrer,
            et_prefix="NBK"
        )

        # ------------------------
        # Paramètres
        # ------------------------
        self.mode = mode
        self.N = N
        self.n_trials = n_trials
        self.target_ratio = target_ratio
        self.stim_dur = stim_dur
        self.isi = isi


        # ------------------------
        # Codes TTL
        # ------------------------
        self.codes = {
            'start_exp': 255,
            'rest_start': 200,
            'rest_end': 201,
            'stim_target': 10,
            'stim_nontarget': 20,
            'resp': 128,
            'fixation': 5
        }

        # ------------------------
        # Stimuli
        # ------------------------
        self.stim_text = visual.TextStim(
            self.win, text='', color='white',
            height=0.25, font='Arial'
        )

        # ------------------------
        # Touches
        # ------------------------
        if self.mode == 'fmri':
            self.response_keys = ['b', 'y', 'g', 'r']
        else:
            self.response_keys = ['space', 'return', 'a', 'z']

        self.quit_key = 'escape'

        # ------------------------
        # Données
        # ------------------------
        self.sequence = []
        self.global_records = []

    # ======================================================================
    # TIMING UTIL
    # ======================================================================

    def _wait_until(self, t_goal, relax=0.002):
        """
        Attente jusqu'à t_goal.
        """
        while True:
            now = self.task_clock.getTime()
            dt = t_goal - now
            if dt <= 0:
                return
            core.wait(min(relax, dt))

    # ======================================================================
    # SEQUENCE
    # ======================================================================

    def generate_sequence(self):
        """Génère une séquence N-back avec ratio de cibles."""
        letters = list("BCDFGHJKLMNPQRSTVXZ")

        seq = []
        flags = []

        # N premiers essais: non-cibles
        for i in range(self.N):
            ch = random.choice(letters)
            if i > 0 and ch == seq[-1]:
                ch = random.choice([x for x in letters if x != seq[-1]])
            seq.append(ch)
            flags.append(False)

        remaining = self.n_trials - self.N
        n_targets = int(round(remaining * self.target_ratio))

        conditions = [True] * n_targets + [False] * (remaining - n_targets)
        random.shuffle(conditions)

        for is_t in conditions:
            target_letter = seq[-self.N]
            if is_t:
                seq.append(target_letter)
                flags.append(True)
            else:
                pool = [x for x in letters if x != target_letter]
                seq.append(random.choice(pool))
                flags.append(False)

        self.sequence = list(zip(seq, flags))
        self.logger.log(
            f"Séquence générée: N={self.N} | trials={len(self.sequence)} | "
            f"targets={sum(flags)} (planned~{n_targets})"
        )

    # ======================================================================
    # TRIAL
    # ======================================================================

    def run_trial(self, trial_idx, letter, is_target, onset_goal):
        """
        Essai planifié.
        CORRECTION DRIFT: L'ISI compense le retard éventuel du Stimulus.
        """

        should_quit(self.win)
        gc.disable()
        event.clearEvents(eventType='keyboard')

        trig_stim = self.codes['stim_target'] if is_target else self.codes['stim_nontarget']

        # 1) Attente de l'onset planifié
        # Astuce: on vise ~1 frame (10-15ms) AVANT le but pour laisser win.flip()
        # se synchroniser sur le VSync exact correspondant à onset_goal.
        frame_tolerance = 0.012  # 12ms
        self._wait_until(onset_goal - frame_tolerance)

        # 2) STIM ONSET
        self.stim_text.text = letter
        self.stim_text.draw()

        self.win.callOnFlip(self.ParPort.send_trigger, trig_stim)
        if self.eyetracker_actif:
            self.win.callOnFlip(self.EyeTracker.send_message,
                                f"TRIAL_{trial_idx}_TARGET_{int(is_target)}")

        # Le flip va attendre le prochain VSync (qui devrait être très proche de onset_goal)
        self.win.flip()
        
        onset_time = self.task_clock.getTime()
        drift_ms = (onset_time - onset_goal) * 1000.0

        # --- CORRECTION TIMING ---
        # On veut que le Stimulus reste affiché stim_dur (visuel constant)
        t_stim_end = onset_time + self.stim_dur
        
        # MAIS on veut que l'essai total finisse à l'heure PLANIFIÉE (Absolue)
        # On ne se base PAS sur onset_time pour la fin de l'essai, sinon on décale tout.
        t_trial_end_absolute = onset_goal + self.stim_dur + self.isi

        resp_key = None
        rt = None

        # 3) Réponse pendant stimulus
        while self.task_clock.getTime() < t_stim_end and resp_key is None:
            keys = event.getKeys(
                keyList=self.response_keys + [self.quit_key],
                timeStamped=self.task_clock
            )
            if keys:
                k, t = keys[0]
                if k == self.quit_key:
                    should_quit(self.win, quit=True)
                resp_key = k
                rt = t - onset_time

        # 4) Fixation / ISI + réponse
        self.fixation.draw()
        self.win.callOnFlip(self.ParPort.send_trigger, self.codes['fixation'])
        self.win.flip()

        # On attend jusqu'au temps ABSOLU de fin
        while self.task_clock.getTime() < t_trial_end_absolute and resp_key is None:
            keys = event.getKeys(
                keyList=self.response_keys + [self.quit_key],
                timeStamped=self.task_clock
            )
            if keys:
                k, t = keys[0]
                if k == self.quit_key:
                    should_quit(self.win, quit=True)
                resp_key = k
                rt = t - onset_time
        
        # Si on a déjà répondu, il faut quand même attendre la fin du temps absolu
        # pour ne pas lancer l'essai suivant trop tôt (ce qui casserait la grille fMRI)
        if resp_key is not None:
             self._wait_until(t_trial_end_absolute)

        # 5) Scoring
        if resp_key is None:
            acc = 0 if is_target else 1
            status = "MISS" if is_target else "CR"
            trig_resp = 0
        else:
            acc = 1 if is_target else 0
            status = "HIT" if is_target else "FA"
            trig_resp = self.codes['resp']
            self.ParPort.send_trigger(trig_resp)
            if self.eyetracker_actif:
                self.EyeTracker.send_message(f"RESP_{status}")

        rt_str = f"{rt:.3f}s" if rt is not None else "---"
        
        # Log avec une alerte visuelle si le drift dépasse 1 frame (16ms)
        drift_marker = "!!!" if abs(drift_ms) > 17 else "   "
        self.logger.log(
            f"T{trial_idx:02d} | {letter} | {'TARGET' if is_target else 'NONTARGET'} | "
            f"{status} | RT:{rt_str} | Drift:{drift_ms:5.1f}ms {drift_marker}"
        )

        # 6) Record
        self.global_records.append({
            'participant': self.nom,
            'session': self.session,
            'trial_number': trial_idx,
            'N_level': self.N,
            'letter': letter,
            'is_target': is_target,
            'onset_goal': onset_goal,
            'onset_time': onset_time,
            'drift_ms': drift_ms,
            'stim_dur': self.stim_dur,
            'isi_planned': self.isi,
            'isi_actual': t_trial_end_absolute - t_stim_end, # Durée réelle de l'ISI
            'response_key': resp_key,
            'rt': rt,
            'accuracy': acc,
            'status': status,
            'trigger_stim': trig_stim,
            'trigger_resp': trig_resp
        })

        gc.enable()

    # ======================================================================
    # INSTRUCTIONS / RUN
    # ======================================================================

    def get_instruction_text(self):
        return (f"TÂCHE {self.N}-BACK\n\n"
                f"Appuyez si la lettre est IDENTIQUE\n"
                f"à celle vue il y a {self.N} lettres.\n\n"
                f"Sinon, ne faites rien.\n\n"
                f"Appuyez pour commencer.")

    def run(self):
        try:
            self.generate_sequence()
            self.show_instructions(self.get_instruction_text())
            self.wait_for_trigger()
            self.show_resting_state(duration_s=10.0, code_start_key='rest_start', code_end_key='rest_end')

            # Ancrage temporel
            start_anchor = self.task_clock.getTime() + 0.5
            trial_len = self.stim_dur + self.isi

            self.fixation.draw()
            self.win.flip()

            for i, (letter, is_target) in enumerate(self.sequence, 1):
                # Calcul purement mathématique de l'heure de début
                onset_goal = start_anchor + (i - 1) * trial_len
                self.run_trial(i, letter, is_target, onset_goal)

            self.show_resting_state(duration_s=10.0, code_start_key='rest_start', code_end_key='rest_end')

        except (KeyboardInterrupt, SystemExit):
            self.logger.warn("Arrêt manuel par l'utilisateur.")
        except Exception as e:
            self.logger.err(f"Erreur critique NBack: {e}")
            raise
        finally:
            self.save_data(self.global_records)