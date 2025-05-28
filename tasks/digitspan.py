from psychopy import visual, event, core
import random, csv, os
from datetime import datetime
from utils.utils import should_quit


class DigitSpan:
    def __init__(self, win, nom, enregistrer, span_length=5,
                 n_trials=3, digit_dur=0.8, isi=0.5, data_dir='data/digitspan'):
        self.win = win
        self.nom = nom
        self.enregistrer = enregistrer
        self.span_length = span_length
        self.n_trials = n_trials
        self.digit_dur = digit_dur
        self.isi = isi
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

        self.results = []
        self.text_stim = visual.TextStim(self.win, color='white', height=0.1)
        self.instruction_stim = visual.TextStim(self.win, color='white', height=0.07, wrapWidth=1.5)

    def show_instructions(self):
        instructions = (
            f"Tâche Digit Span\n\n"
            "Une séquence de chiffres va s'afficher un par un.\n"
            f"Votre tâche est de mémoriser la séquence puis de la taper correctement.\n\n"
            "Appuyez sur une touche pour commencer."
        )
        self.instruction_stim.text = instructions
        self.instruction_stim.draw()
        self.win.flip()
        event.waitKeys()

    def generate_sequence(self):
        return [str(random.randint(0, 9)) for _ in range(self.span_length)]

    def get_response(self):
        response = ''
        self.text_stim.text = ''
        self.text_stim.draw()
        self.win.flip()

        while True:
            keys = event.getKeys()
            for key in keys:
                if key == 'escape':
                    should_quit(self.win)
                elif key in ['return', 'num_enter']:
                    return response
                elif key == 'backspace':
                    response = response[:-1]
                elif key in ['0','1','2','3','4','5','6','7','8','9']:
                    response += key
                elif key in ['num_0','num_1','num_2','num_3','num_4',
                            'num_5','num_6','num_7','num_8','num_9']:
                    response += key[-1]

                self.text_stim.text = response
                self.text_stim.draw()
                self.win.flip()


    def run(self):
        self.show_instructions()

        for trial in range(self.n_trials):
            should_quit(self.win)

            seq = self.generate_sequence()

            # Affichage séquentiel
            for digit in seq:
                self.text_stim.text = digit
                self.text_stim.draw()
                self.win.flip()
                core.wait(self.digit_dur)

                # ISI
                self.text_stim.text = ''
                self.text_stim.draw()
                self.win.flip()
                core.wait(self.isi)

            # Demander la réponse
            self.text_stim.text = "Tapez la séquence, puis Entrée"
            self.text_stim.draw()
            self.win.flip()
            core.wait(1)
            response = self.get_response()

            # Confirmation visuelle de la réponse après saisie
            self.text_stim.text = f"Votre réponse : {response}"
            self.text_stim.draw()
            self.win.flip()
            core.wait(1.5)  # Pause pour laisser le temps de voir


            accurate = (response == ''.join(seq))

            self.results.append({
                'trial': trial + 1,
                'sequence': ''.join(seq),
                'response': response,
                'accurate': accurate,
                'length': len(response)
            })

        self.print_results_summary()
        return self.results

    def print_results_summary(self):
        print("\n--- Résultats de la tâche Digit Span ---")
        n_correct = sum(r['accurate'] for r in self.results)
        n_trials = len(self.results)
        print(f"Réponses correctes : {n_correct} / {n_trials} ({100*n_correct/n_trials:.1f}%)")
        print("\nDétail par essai :")
        for r in self.results:
            print(f"Essai {r['trial']:2d} | Séquence: {r['sequence']} | "
                  f"Réponse: {r['response']} | Correct: {r['accurate']}")

    def save_results(self):
        if not self.enregistrer:
            return
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        fname = f"{self.nom}_DigitSpan_{ts}.csv"
        path = os.path.join(self.data_dir, fname)
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'participant', 'date', 'trial', 'sequence', 'response', 'accurate', 'length'
            ])
            writer.writeheader()
            for row in self.results:
                writer.writerow({**row, 'participant': self.nom, 'date': ts})
        print(f"Données sauvegardées : {path}")
