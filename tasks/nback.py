from psychopy import visual, event, core
import random, csv, os
from datetime import datetime
from utils.utils import should_quit


class NBack:
    def __init__(self, win, nom, enregistrer, N=2, n_trials=30,
                 isi=1.5, stim_dur=0.5, screenid=1, data_dir='data/nback'):
        self.win = win
        self.nom = nom
        self.screenid = screenid
        self.enregistrer = enregistrer
        self.N = N
        self.n_trials = n_trials
        self.isi = isi
        self.stim_dur = stim_dur
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.letters = []
        self.results = []
        self.text_stim = visual.TextStim(self.win, color='white', wrapWidth=1.5, height=0.07)
        self.fixation = visual.TextStim(self.win, text='+', color='white', height=0.2)
        self.stim = visual.TextStim(self.win, text='', color='white', height=0.3)
        self.trial_clock = core.Clock()

    def show_instructions(self):
        instructions = (
            f"Tâche N-Back {self.N}\n\n"
            "Une série de lettres va s'afficher une à une.\n"
            f"Votre tâche est de détecter si la lettre présentée est la même que celle "
            f"présentée {self.N} positions avant.\n\n"
            "Appuyez sur la barre espace chaque fois qu'il y a une correspondance.\n"
            "Appuyez sur 'n' s'il n'y a pas de correspondance.\n\n"
            "Appuyez sur une touche pour commencer."
        )
        self.text_stim.text = instructions
        self.text_stim.draw()
        self.win.flip()
        event.waitKeys()

    def wait_for_trigger(self, trigger_key='t'):
        """Affiche un message et attend le trigger scanner."""
        self.text_stim.text = (
            f"En attente du trigger scanner ('{trigger_key}')\n"
            "Appuyez sur 'escape' pour quitter."
        )
        self.text_stim.draw()
        self.win.flip()
        keys = event.waitKeys(keyList=[trigger_key, 'escape'])
        if 'escape' in keys:
            should_quit(self.win, quit=True)

    def generate_sequence(self):
        alpha = list('ABCDEHIKLMOPRST')
        seq = []
        
        for i in range(self.n_trials):
            if i >= self.N and random.random() < 0.3:
                seq.append(seq[i - self.N])
            else:
                new_letter = random.choice(alpha)
                max_attempts = 20
                attempts = 0
                while i >= self.N and new_letter == seq[i - self.N] and attempts < max_attempts:
                    new_letter = random.choice(alpha)
                    attempts += 1
                seq.append(new_letter)
                
        self.letters = seq

    def run(self):
        self.show_instructions()
        self.wait_for_trigger(trigger_key='t')
        self.generate_sequence()

        for idx, letter in enumerate(self.letters):
            should_quit(self.win)
            event.clearEvents()

            # Fixation
            self.fixation.draw()
            self.win.flip()
            core.wait(self.isi)

            # Stimulus
            self.stim.text = letter
            self.stim.draw()
            self.win.flip()
            self.trial_clock.reset()

            resp = 'no'
            rt = None
            responded = False
            response_window = self.stim_dur 

            while self.trial_clock.getTime() < response_window:
                keys = event.getKeys(keyList=['space', 'n', 'escape'], timeStamped=self.trial_clock)
                if keys and not responded:
                    key, press_time = keys[0]
                    if key == 'escape':
                        should_quit(self.win, quit=True)
                    elif key in ['space', 'n']:
                        resp = 'yes' if key == 'space' else 'no'
                        rt = round(press_time, 5)
                        responded = True
                core.wait(0.001)

            is_target = (idx >= self.N and letter == self.letters[idx - self.N])
            accurate = (resp == 'yes' and is_target) or (resp == 'no' and not is_target)

            trial_result = {
                'trial': idx + 1,
                'letter': letter,
                'letter_Nback': self.letters[idx - self.N] if idx >= self.N else 'N/A',
                'is_target': is_target,
                'response': resp,
                'accurate': accurate,
                'RT': rt
            }
            self.results.append(trial_result)

            # 🔎 DEBUG temps réel (comme Flanker)
            print(f" Essai {idx+1:2d} | Lettre: {letter} | "
                  f"N-back: {trial_result['letter_Nback']} | "
                  f"Cible: {is_target} | "
                  f"Réponse: {resp} | "
                  f"Correct: {accurate} | "
                  f"RT: {rt if rt is not None else 'N/A'}", flush=True)

            elapsed = self.trial_clock.getTime()
            remaining_isi = self.isi - max(elapsed, self.stim_dur)
            if remaining_isi > 0:
                core.wait(remaining_isi)

        self.print_results_summary()
        if self.enregistrer:
            self.save_results()
        return self.results

    def print_results_summary(self):
        print("\n--- Résultats de la tâche N-Back ---")
        total_correct = sum(1 for r in self.results if r['accurate'])
        total_trials = len(self.results)
        percent_correct = total_correct / total_trials * 100 if total_trials else 0
        print(f"Réponses correctes : {total_correct} / {total_trials} ({percent_correct:.1f}%)\n")

        print("Détail par essai :")
        for r in self.results:
            print(f"Essai {r['trial']:2d} | Lettre: {r['letter']} | "
                  f"N-back: {r['letter_Nback']} | "
                  f"Cible: {r['is_target']} | "
                  f"Réponse: {r['response']} | "
                  f"Correct: {r['accurate']} | "
                  f"RT: {r['RT'] if r['RT'] is not None else 'N/A'}")

    def save_results(self):
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        fname = f"{self.nom}_N{self.N}_{ts}.csv"
        path = os.path.join(self.data_dir, fname)
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'participant', 'date', 'N', 'trial',
                'letter', 'letter_Nback', 'is_target',
                'response', 'accurate', 'RT'
            ])
            writer.writeheader()
            for row in self.results:
                writer.writerow({
                    'participant': self.nom,
                    'date': ts,
                    'N': self.N,
                    'trial': row['trial'],
                    'letter': row['letter'],
                    'letter_Nback': row['letter_Nback'],
                    'is_target': row['is_target'],
                    'response': row['response'],
                    'accurate': row['accurate'],
                    'RT': row['RT']
                })
        print(f"Données sauvegardées : {path}")
