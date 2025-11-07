from psychopy import visual, event, core
import random, csv, os
from datetime import datetime
from utils.utils import should_quit
import warnings
from psychopy import logging
logging.console.setLevel(logging.ERROR)



class TemporalJudgement:
    def __init__(self, win, nom, session='01', enregistrer=True, screenid=1,
                 n_trials=60, delays_ms=(200, 400, 600),
                 response_options=(1, 200, 400, 600, 800),  # ← 1 = "très court", etc.
                 stim_isi_range=(1.5, 2.5),
                 data_dir='data/temporal_judgement'):
        self.win = win
        self.nom = nom
        self.session = session
        self.enregistrer = enregistrer
        self.screenid = screenid
        self.n_trials = n_trials
        self.delays_ms = list(delays_ms)
        self.response_options = list(response_options)
        self.stim_isi_range = stim_isi_range
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

        # === TOUCHES CORRIGÉES ===
        self.keys = {
            'action': 'space',
            'responses': ['a', 'z', 'e', 'r', 't'],  # ← 1 à 5 (main gauche)
            'trigger': 't',
            'quit': 'escape'
        }

        # === STIMULI  ===
        self.text_stim = visual.TextStim(self.win, color='white', height=0.05, wrapWidth=1.5)
        self.fixation = visual.TextStim(self.win, text='+', color='white', height=0.12)

        self.results = []
        self.global_clock = core.Clock()

    # -------------------------------------------------------------------------
    def show_instructions(self):
        instructions = (
            "Tâche de jugement temporel\n\n"
            "Condition ACTIVE : base verte → appuyez sur ESPACE pour allumer l’ampoule.\n"
            "Condition PASSIVE : base rouge → restez immobile, l’expérimentateur bougera votre doigt.\n\n"
            "L’ampoule s’allumera après un délai de 200 / 400 / 600 ms.\n\n"
            "Après l’allumage, évaluez le délai perçu :\n"
            "1 → 1 ms | 2 → 200 ms | 3 → 400 ms | 4 → 600 ms | 5 → 800 ms\n\n"
            "Répondez avec la main gauche (touches 1 à 5).\n"
            "Appuyez sur une touche pour commencer."
        )
        self.text_stim.text = instructions
        self.text_stim.draw()
        self.win.flip()
        event.waitKeys(keyList=['space', 'return', 'num_enter', self.keys['quit']])
        if event.getKeys(keyList=[self.keys['quit']]):
            should_quit(self.win, quit=True)

    # -------------------------------------------------------------------------
    def wait_for_trigger(self):
        self.text_stim.text = f"En attente du trigger scanner ('{self.keys['trigger']}')"
        self.text_stim.draw()
        self.win.flip()
        keys = event.waitKeys(keyList=[self.keys['trigger'], self.keys['quit']])
        if keys and keys[0][0] == self.keys['quit']:
            should_quit(self.win, quit=True)

    # -------------------------------------------------------------------------
    def draw_lightbulb(self, base_color='white', bulb_on=False, size=0.35):
        """Dessine l'ampoule avec ou sans lumière."""
        bulb_color = 'yellow' if bulb_on else 'grey'
        bulb = visual.Circle(self.win, radius=size/2, fillColor=bulb_color,
                             lineColor='white', pos=(0.0, 0.15))
        base = visual.Rect(self.win, width=size*0.4, height=size*0.18,
                           fillColor=base_color, lineColor='white', pos=(0.0, -0.05))
        bulb.draw()
        base.draw()

    # -------------------------------------------------------------------------
    def run_trial(self, trial_index, condition, delay_ms):
        should_quit(self.win)
        base_color = '#00FF00' if condition == 'active' else '#FF0000'

        # Fixation
        self.fixation.draw()
        self.win.flip()
        core.wait(0.5)

        # Ampoule éteinte
        self.draw_lightbulb(base_color, bulb_on=False)
        self.win.flip()
        trial_onset = self.global_clock.getTime()

        # -----------------------
        # PHASE D’ACTION
        # -----------------------
        action_time = None
        
        waiting_clock = core.Clock()
        event.clearEvents(eventType='keyboard')
        while True:
            keys = event.getKeys(keyList=[self.keys['action'], self.keys['quit']],
                                    timeStamped=waiting_clock)
            if keys:
                key, ts = keys[0]
                if key == self.keys['quit']:
                    should_quit(self.win)
                action_time = trial_onset + ts
                break
            core.wait(0.001)
        

        # -----------------------
        # DÉLAI ACTION → RÉSULTAT
        # -----------------------
        core.wait(delay_ms / 1000.0)

        # -----------------------
        # ALLUMAGE DE L’AMPOULE
        # -----------------------
        self.draw_lightbulb(base_color, bulb_on=True)
        self.win.flip()
        outcome_time = self.global_clock.getTime()
        core.wait(1.0)

        # -----------------------
        # PHASE DE RÉPONSE
        # -----------------------
        # === AFFICHAGE FIXE (ne bouge jamais) ===
        title = visual.TextStim(self.win, text="Combien de ms avez-vous perçu ?", color='white', height=0.05, pos=(0, 0.25))
        options = visual.TextStim(self.win, text="    1: 1    |    2: 200   |    3: 400     |    4: 600   |    5: 800    ", color='white', height=0.05, pos=(0, 0))
        instr = visual.TextStim(self.win, text="Répondez avec la main gauche (touches 1–5)", color='white', height=0.05, pos=(0, -0.25))

        # Afficher une fois
        title.draw()
        options.draw()
        instr.draw()
        self.win.flip()

        # Attente réponse
        resp_clock = core.Clock()
        keys = event.waitKeys(
            maxWait=4.0,
            keyList=self.keys['responses'] + [self.keys['quit']],
            timeStamped=resp_clock
        )

        response_key = 'none'
        response_choice_ms = None
        rt = None

        if keys:
            key, ts = keys[0]
            if key == self.keys['quit']:
                should_quit(self.win)
            else:
                try:
                    idx = self.keys['responses'].index(key)
                    response_choice_ms = self.response_options[idx]
                    response_key = key
                    rt = ts

                    # === REDESSINER TOUT + AJOUTER UN SOULIGNEMENT ===
                    title.draw()
                    options.draw()
                    instr.draw()

                    # Positions des 5 options (ajustées pour correspondre au texte)
                    x_pos = [-0.33, -0.18 , -0.02  , 0.155, 0.315]
                    y_line = -0.06  # Position du soulignement

                    # Souligner uniquement la réponse choisie
                    underline = visual.Line(
                        self.win,
                        start=(x_pos[idx] - 0.045, y_line),
                        end=(x_pos[idx] + 0.045, y_line),
                        lineColor='white',
                        lineWidth=3
                    )
                    underline.draw()

                    self.win.flip()
                    core.wait(0.6)  # Voir le soulignement

                except ValueError:
                    response_key = 'invalid'
        else:
            response_key = 'timeout'

        # ISI aléatoire
        core.wait(random.uniform(*self.stim_isi_range))

        return {
            'trial': trial_index,
            'condition': condition,
            'requested_delay_ms': delay_ms,
            'action_time_s': round(action_time, 4) if action_time else None,
            'outcome_time_s': round(outcome_time, 4),
            'response_key': response_key,
            'response_choice_ms': response_choice_ms,
            'RT_s': round(rt, 4) if rt else None,
            'trial_onset_s': round(trial_onset, 4)
        }

    # -------------------------------------------------------------------------
    def run(self):
        self.show_instructions()
        self.wait_for_trigger()
        conditions = ['active', 'passive']
        trials = [(c, d) for c in conditions for d in self.delays_ms for _ in range(10)]
        random.shuffle(trials)
        self.global_clock.reset()
        print("=== Début de la tâche ===")
        for i, (cond, delay) in enumerate(trials, start=1):
            result = self.run_trial(i, cond, delay)
            self.results.append(result)
            print(f"Essai {i:02d} | {cond:7s} | {delay:3d} ms | "
                  f"Réponse: {result['response_choice_ms']} ms | RT: {result['RT_s']} s")
        print("=== Fin de la tâche ===")
        self.save_results()
        self.show_end_screen()

    # -------------------------------------------------------------------------
    def save_results(self):
        if not self.enregistrer:
            return
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        fname = f"{self.nom}_TemporalJudgement_{self.session}_{ts}.csv"
        path = os.path.join(self.data_dir, fname)
        fieldnames = [
            'participant', 'session', 'trial', 'condition', 'requested_delay_ms',
            'action_time_s', 'outcome_time_s', 'response_key',
            'response_choice_ms', 'RT_s', 'trial_onset_s'
        ]
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in self.results:
                row = {**r, 'participant': self.nom, 'session': self.session}
                writer.writerow(row)
        print(f"Données sauvegardées : {path}")

    # -------------------------------------------------------------------------
    def show_end_screen(self):
        self.text_stim.text = "Fin de la session.\nMerci de votre participation."
        self.text_stim.draw()
        self.win.flip()
        event.waitKeys(keyList=['space', 'return', 'escape'])
        self.win.close()
        core.quit()