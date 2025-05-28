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

    def show_instructions(self):
        instructions = (
            f"Tâche N-Back {self.N}\n\n"
            "Une série de lettres va s'afficher une à une.\n"
            f"Votre tâche est de détecter si la lettre présentée est la même que celle "
            f"présentée {self.N} positions avant.\n\n"
            "Appuyez sur la barre espace chaque fois qu'il y a une correspondance.\n\n"
            "Appuyez sur une touche pour commencer."
        )
        self.text_stim.text = instructions
        self.text_stim.draw()
        self.win.flip()
        event.waitKeys(keyList=None)

    def generate_sequence(self):
        alpha = list('ABCDEHIKLMOPRST')  # 15 lettres uniquement
        seq = []
        for i in range(self.n_trials):
            if i >= self.N and random.random() < 0.3:
                # 30% de chances que ce soit un target (répétition N-back)
                seq.append(seq[i - self.N])
            else:
                l = random.choice(alpha)
                # éviter répétition involontaire N-back
                while i >= self.N and l == seq[i - self.N]:
                    l = random.choice(alpha)
                seq.append(l)
        self.letters = seq

    def run(self):
        self.show_instructions()
        self.generate_sequence()

        fixation = visual.TextStim(self.win, text='+', color='white', height=0.2)
        stim = visual.TextStim(self.win, text='', color='white', height=0.3)

        for idx, letter in enumerate(self.letters):
            should_quit(self.win)

            # Fixation
            fixation.draw()
            self.win.flip()
            core.wait(0.5)

            # Affichage stimulus
            stim.text = letter
            stim.draw()
            self.win.flip()
            t_on = core.getTime()

            # Attente réponse en boucle pendant stim_dur
            resp = 'none'
            rt = None
            responded = False
            while (core.getTime() - t_on) < self.stim_dur and not responded:
                keys = event.getKeys(keyList=['space', 'n'], timeStamped=True)
                if keys:
                    key, ts = keys[0]
                    resp = 'yes' if key == 'space' else 'no'
                    rt = round(ts - t_on, 5)
                    responded = True
                core.wait(0.01)  # Petite pause pour ne pas saturer le CPU

            is_target = (idx >= self.N and letter == self.letters[idx - self.N])
            accurate = (resp == 'yes' and is_target) or ((resp == 'no' or resp == 'none') and not is_target)


            self.results.append({
                'trial': idx + 1,
                'letter': letter,
                'letter_Nback': self.letters[idx - self.N] if idx >= self.N else '',
                'is_target': is_target,
                'response': resp,
                'accurate': accurate,
                'RT': rt
            })

            # Pause ISI (inter-stimulus interval) moins le temps écoulé
            elapsed = core.getTime() - t_on
            core.wait(max(0, self.isi - elapsed))

        self.print_results_summary()
        return self.results


    def print_results_summary(self):
        print("\n--- Résultats de la tâche N-Back ---")
        n_correct = sum(r['accurate'] for r in self.results)
        n_trials = len(self.results)
        print(f"Réponses correctes : {n_correct} / {n_trials} ({100*n_correct/n_trials:.1f}%)\n")

        print("Détail par essai :")
        for r in self.results:
            print(f"Essai {r['trial']:2d} | Lettre: {r['letter']} | "
                  f"Cible: {r['is_target']} | Réponse: {r['response']:>4} | "
                  f"Correct: {r['accurate']} | RT: {r['RT'] if r['RT'] is not None else 'N/A'}")

    def save_results(self):
        if not self.enregistrer:
            return
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
                writer.writerow({**row, 'participant': self.nom, 'date': ts, 'N': self.N})
        print(f"Données sauvegardées : {path}")
