from psychopy import visual, event, core
import random
import csv
import os
from datetime import datetime
from utils.utils import should_quit

class Stroop:
    def __init__(self, win, nom, enregistrer=True, n_trials=30,
                 stim_dur=1.5, isi=1.0, data_dir='data/stroop_two_keys'):
        self.win = win
        self.nom = nom
        self.enregistrer = enregistrer
        self.n_trials = n_trials
        self.stim_dur = stim_dur
        self.isi = isi
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

        # Préparation des stimuli
        self.colors = ['red', 'green', 'blue', 'yellow']
        self.words = ['ROUGE', 'VERT', 'BLEU', 'JAUNE']
        # Mapping touche: couleur
        self.key_mapping = {'r': 'red', 'b': 'blue'}

        self.results = []
        self.text_stim = visual.TextStim(self.win, height=0.1, color='white')
        self.trial_clock = core.Clock()

    def show_instructions(self):
        instructions = (
            "Tâche Stroop\n\n"
            "Vous verrez un mot désignant une couleur écrit dans une couleur d'encre.\n"
            "Votre tâche est d'indiquer la couleur de l'encre en utilisant les touches suivantes :\n"
            "Touche 'R' pour la couleur ROUGE\n"
            "Touche 'B' pour la couleur BLEUE\n"
            "Ne répondez pas pour les autres couleurs.\n"
            "Appuyez sur n'importe quelle touche pour commencer."
        )
        self.text_stim.text = instructions
        self.text_stim.color = 'white'
        self.text_stim.wrapWidth = 1.2
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

    def generate_trial(self):
        word = random.choice(self.words)
        ink_color = random.choice(self.colors)
        congruent = (word.lower() == self.color_to_word(ink_color))
        return word, ink_color, congruent

    def color_to_word(self, color):
        return {
            'red': 'rouge',
            'green': 'vert',
            'blue': 'bleu',
            'yellow': 'jaune'
        }.get(color, '')

    def run(self):
        self.show_instructions()
        random.seed()

        # Attente du trigger scanner avant de démarrer la tâche
        self.wait_for_trigger(trigger_key='t')

        for trial in range(1, self.n_trials + 1):
            should_quit(self.win)

            word, ink_color, congruent = self.generate_trial()

            # Afficher le stimulus
            self.text_stim.text = word
            self.text_stim.color = ink_color
            self.text_stim.draw()
            self.win.flip()

            self.trial_clock.reset()
            resp = None
            rt = None

            while self.trial_clock.getTime() < self.stim_dur:
                keys = event.getKeys(keyList=list(self.key_mapping.keys()) + ['escape'],
                                     timeStamped=self.trial_clock)
                if keys:
                    key, ts = keys[0]
                    if key == 'escape':
                        should_quit(self.win)
                    resp = key
                    rt = round(ts, 4)
                    break
                core.wait(0.005)

            # Clear screen
            self.win.flip()
            core.wait(self.isi)

            accurate = self.check_response(resp, ink_color)

            trial_result = {
                'trial': trial,
                'word': word,
                'ink_color': ink_color,
                'congruent': congruent,
                'response_key': resp if resp else 'none',
                'response_color': self.key_mapping.get(resp, 'none'),
                'accurate': accurate,
                'RT': rt
            }
            self.results.append(trial_result)

            # 🔎 DEBUG temps réel (comme Flanker et NBack)
            print(f" Essai {trial:2d} | Mot: {word} | "
                  f"Couleur: {ink_color} | "
                  f"Congruent: {congruent} | "
                  f"Réponse: {trial_result['response_color']} | "
                  f"Correct: {accurate} | "
                  f"RT: {rt if rt else 'N/A'}", flush=True)

        self.print_results_summary()
        return self.results

    def check_response(self, resp, ink_color):
        if ink_color in self.key_mapping.values():
            if resp:
                resp_color = self.key_mapping.get(resp)
                return resp_color == ink_color
            else:
                return False
        else:
            return resp is None

    def print_results_summary(self):
        n_correct = sum(r['accurate'] for r in self.results)
        n_trials = len(self.results)
        print(f"\n--- Résultats de la tâche Stroop ---")
        print(f"Corrects : {n_correct} / {n_trials} ({100 * n_correct / n_trials:.1f}%)")
        mean_rt = (sum(r['RT'] for r in self.results if r['RT'] is not None) /
                   sum(r['RT'] is not None for r in self.results)) if any(r['RT'] is not None for r in self.results) else 0
        print(f"RT moyen (sur réponses) : {mean_rt:.3f} s")
        print("\nDétail par essai :")
        for r in self.results:
            print(f"Essai {r['trial']:2d} | Mot: {r['word']} | Couleur: {r['ink_color']} | "
                  f"Congruent: {r['congruent']} | Réponse: {r['response_color']} | "
                  f"Correct: {r['accurate']} | RT: {r['RT'] if r['RT'] else 'N/A'}")

    def save_results(self):
        if not self.enregistrer:
            return
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        fname = f"{self.nom}_StroopTwoKeys_{ts}.csv"
        path = os.path.join(self.data_dir, fname)
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'participant', 'date', 'trial', 'word', 'ink_color',
                'congruent', 'response_key', 'response_color', 'accurate', 'RT'
            ])
            writer.writeheader()
            for row in self.results:
                writer.writerow({**row,
                                 'participant': self.nom,
                                 'date': ts})
        print(f"Données sauvegardées : {path}")
