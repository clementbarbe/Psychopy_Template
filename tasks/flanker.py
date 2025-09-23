from psychopy import visual, event, core
import random, csv, os
from datetime import datetime
from utils.utils import should_quit


class Flanker:
    def __init__(self, win, nom, enregistrer, screenid = 1, n_trials=10,
                 stim_dur=1, isi=1.0, data_dir='data/flanker'):
        self.win = win
        self.nom = nom
        self.enregistrer = enregistrer
        self;screenid = screenid
        self.n_trials = n_trials
        self.stim_dur = stim_dur
        self.isi = isi
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

        self.results = []
        self.text_stim = visual.TextStim(self.win, height=0.07, color='white')
        self.trial_clock = core.Clock()  # <- Ajout d'une clock pour mesurer le RT

    def show_instructions(self):
        instructions = (
            "Tâche Flanker\n\n"
            "Vous verrez une série de flèches.\n"
            "Indiquez la direction de la flèche centrale :\n"
            "Flèche gauche = touche 'left'\n"
            "Flèche droite = touche 'right'\n\n"
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

    def generate_trial(self):
        directions = ['left', 'right']
        target_dir = random.choice(directions)
        congruent = random.choice([True, False])
        flankers = [target_dir]*2 if congruent else ['left' if target_dir == 'right' else 'right']*2

        mapping = {'left': '<', 'right': '>'}
        stim_str = ''.join([mapping[flankers[0]], mapping[flankers[1]], mapping[target_dir],
                            mapping[flankers[0]], mapping[flankers[1]]])
        return stim_str, target_dir, congruent

    def run(self):
        self.show_instructions()

        # Attente du trigger scanner avant de démarrer la tâche
        self.wait_for_trigger(trigger_key='t')

        for trial in range(1, self.n_trials + 1):
            should_quit(self.win)

            stim_str, target_dir, congruent = self.generate_trial()

            # Affichage du stimulus
            self.text_stim.text = stim_str
            self.text_stim.draw()
            self.win.flip()

            # Démarrer l'enregistrement des réponses dès affichage
            self.trial_clock.reset()
            resp = None
            rt = None

            # Présenter stimulus pour un temps fixe, enregistrer la réponse pendant ce temps
            while self.trial_clock.getTime() < self.stim_dur:
                keys = event.getKeys(keyList=['left', 'right', 'escape'], timeStamped=self.trial_clock)
                if keys:
                    key, ts = keys[0]
                    if key == 'escape':
                        should_quit(self.win)
                    resp = key
                    rt = round(ts, 5)
                    break
                core.wait(0.005)  # plus fin pour un meilleur timing

            # Effacer l’écran
            self.win.flip()

            accurate = (resp == target_dir)

            trial_result = {
                'trial': trial,
                'stimulus': stim_str,
                'target_direction': target_dir,
                'congruent': congruent,
                'response': resp if resp is not None else 'none',
                'accurate': accurate,
                'RT': rt
            }

            self.results.append(trial_result)

            # 🔎 DEBUG temps réel : affichage direct après chaque essai
            print(f" Trial {trial:2d} | Stimulus: {stim_str} | "
                f"Congruent: {congruent} | Cible: {target_dir} | "
                f"Réponse: {resp if resp is not None else 'none'} | "
                f"Correct: {accurate} | RT: {rt if rt is not None else 'N/A'}", flush = True)

            # Pause inter-essai stricte
            core.wait(self.isi)


    def print_results_summary(self):
        print("\n--- Résultats de la tâche Flanker ---")
        n_correct = sum(r['accurate'] for r in self.results)
        n_trials = len(self.results)
        print(f"Réponses correctes : {n_correct} / {n_trials} ({100 * n_correct / n_trials:.1f}%)")
        print("\nDétail par essai :")
        for r in self.results:
            print(f"Essai {r['trial']:2d} | Stimulus: {r['stimulus']} | "
                  f"Congruent: {r['congruent']} | Cible: {r['target_direction']} | "
                  f"Réponse: {r['response']} | Correct: {r['accurate']} | RT: {r['RT'] if r['RT'] is not None else 'N/A'}")

    def save_results(self):
        if not self.enregistrer:
            return
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        fname = f"{self.nom}_Flanker_{ts}.csv"
        path = os.path.join(self.data_dir, fname)
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'participant', 'date', 'trial', 'stimulus', 'target_direction',
                'congruent', 'response', 'accurate', 'RT'
            ])
            writer.writeheader()
            for row in self.results:
                writer.writerow({**row, 'participant': self.nom, 'date': ts})
        print(f"Données sauvegardées : {path}")