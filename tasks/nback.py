from psychopy import visual, event, core
import random, csv, os
from datetime import datetime
from utils.utils import should_quit


class NBack:
    def __init__(self, win, nom, enregistrer, N=2, n_trials=30,
                 isi=1.5, stim_dur=0.5, data_dir='data/nback'):
        self.win = win
        self.nom = nom
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
        # Affiche les instructions à l'utilisateur
        self.show_instructions()

        # Attente du trigger scanner avant de démarrer la tâche
        self.wait_for_trigger(trigger_key='t')

        # Génère la séquence de lettres pour la tâche N-Back
        self.generate_sequence()

        # Parcourt chaque lettre dans la séquence générée
        for idx, letter in enumerate(self.letters):
            # Vérifie si l'utilisateur souhaite quitter l'expérience
            should_quit(self.win)

            # Efface les événements précédents pour éviter les interférences
            event.clearEvents()

            # Affiche le stimulus de fixation (un signe '+') pendant 0.5 secondes
            self.fixation.draw()
            self.win.flip()
            core.wait(self.isi)

            # Prépare le stimulus (la lettre) à afficher
            self.stim.text = letter
            self.stim.draw()
            self.win.flip()

            # Réinitialise le chronomètre pour mesurer le temps de réponse
            self.trial_clock.reset()

            # Initialise les variables pour la réponse et le temps de réaction
            resp = 'no'
            rt = None
            responded = False

            # Définit la fenêtre de temps pendant laquelle une réponse sera acceptée
            response_window = self.stim_dur 

            # Boucle pour capturer la réponse de l'utilisateur pendant la fenêtre de réponse
            while self.trial_clock.getTime() < response_window:
                # Récupère les touches pressées par l'utilisateur
                keys = event.getKeys(keyList=['space', 'n', 'escape'], timeStamped=self.trial_clock)

                # Vérifie si une touche a été pressée et si une réponse n'a pas encore été enregistrée
                if keys and not responded:
                    key, press_time = keys[0]
                    if key == 'escape':
                        # Si la touche 'escape' est pressée, quitte l'expérience
                        should_quit(self.win, quit=True)
                    elif key in ['space', 'n']:
                        # Enregistre la réponse ('yes' pour espace, 'no' pour 'n')
                        resp = 'yes' if key == 'space' else 'no'
                        # Enregistre le temps de réaction
                        rt = round(press_time, 5)
                        responded = True

                # Attend un court instant pour éviter de surcharger le processeur
                core.wait(0.001)

            # Détermine si la lettre actuelle est une cible (correspond à la lettre N positions avant)
            is_target = (idx >= self.N and letter == self.letters[idx - self.N])

            # Vérifie si la réponse de l'utilisateur est correcte
            accurate = (resp == 'yes' and is_target) or (resp == 'no' and not is_target)

            # Enregistre les résultats de l'essai actuel
            self.results.append({
                'trial': idx + 1,
                'letter': letter,
                'letter_Nback': self.letters[idx - self.N] if idx >= self.N else 'N/A',
                'is_target': is_target,
                'response': resp,
                'accurate': accurate,
                'RT': rt
            })

            # Calcule le temps restant dans l'intervalle inter-stimulus
            elapsed = self.trial_clock.getTime()
            remaining_isi = self.isi - max(elapsed, self.stim_dur)

            # Attend le temps restant pour respecter l'intervalle inter-stimulus
            if remaining_isi > 0:
                core.wait(remaining_isi)

        # Affiche un résumé des résultats à la fin de la tâche
        self.print_results_summary()

        # Sauvegarde les résultats si l'option est activée
        if self.enregistrer:
            self.save_results()

        # Retourne les résultats
        return self.results

    def print_results_summary(self):
        print("\n--- Résultats de la tâche N-Back ---")
        
        total_correct = sum(1 for r in self.results if r['accurate'])
        total_trials = len(self.results)
        percent_correct = total_correct / total_trials * 100 if total_trials else 0

        print(f"Réponses correctes : {total_correct} / {total_trials} ({percent_correct:.1f}%)\n")

        print("Détail par essai :")
        for r in self.results:
            trial_str = f"Essai {r['trial']:>2} | Lettre: {r['letter']} | "
            target_str = f"Cible: {str(r['is_target']):<5} | "
            resp_str = f"Réponse: {r['response']:<4} | "
            correct_str = f"Correct: {str(r['accurate']):<5} | "
            rt_str = f"RT: {r['RT'] if r['RT'] is not None else 'N/A'}"
            print(trial_str + target_str + resp_str + correct_str + rt_str)

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
