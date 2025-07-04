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
        return [str(random.randint(0, 9)) for _ in range(self.span_length)]

    def get_response(self):
        response = ''
        self.text_stim.text = ''
        self.text_stim.draw()
        self.win.flip()
        event.clearEvents()  # vide le buffer des touches
        
        while True:
            keys = event.getKeys()
            for key in keys:
                if key in ['escape', 'q']:
                    should_quit()
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


    def run(self):
        self.show_instructions()

        # Attente du trigger scanner avant de démarrer la tâche
        self.wait_for_trigger(trigger_key='t')

        for trial in range(self.n_trials):
            if should_quit(self.win):
                return None  # Quitter si 'q' est pressé

            seq = self.generate_sequence()

            # Affichage séquentiel avec vérification continue
            for digit in seq:
                self.text_stim.text = digit
                self.text_stim.draw()
                self.win.flip()
                
                # Vérifier 'q' pendant l'affichage du chiffre
                start_time = core.getTime()
                while core.getTime() - start_time < self.digit_dur:
                    if should_quit(self.win):
                        return None
                    core.wait(0.01)  # Petite pause pour éviter de surcharger le CPU

            # ISI avec vérification
            self.text_stim.text = ''
            self.text_stim.draw()
            self.win.flip()
            
            start_time = core.getTime()
            while core.getTime() - start_time < self.isi:
                if should_quit(self.win):
                    return None
                core.wait(0.01)

            # Demander la réponse avec vérification
            self.text_stim.text = "Tapez la séquence, puis Entrée"
            self.text_stim.draw()
            self.win.flip()
            
            start_time = core.getTime()
            while core.getTime() - start_time < 1:  # Attente avant saisie
                if should_quit(self.win):
                    return None
                core.wait(0.01)
            
            response = self.get_response()  # Nouvelle méthode pour gérer 'q' pendant la saisie

            if response is None:  # Si 'q' a été pressé pendant la saisie
                return None

            # Confirmation visuelle avec vérification
            self.text_stim.text = f"Votre réponse : {response}"
            self.text_stim.draw()
            self.win.flip()
            
            start_time = core.getTime()
            while core.getTime() - start_time < 1.5:
                if should_quit(self.win):
                    return None
                core.wait(0.01)

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


