from psychopy import visual, event, core
import random, csv, os
from datetime import datetime
from utils.utils import should_quit

class DigitSpan:
    def __init__(self, win, nom, enregistrer, screenid = 1, digit_dur=0.8, isi=0.5, data_dir='data/digitspan'):
        self.win = win
        self.nom = nom
        self.enregistrer = enregistrer
        self.screenid = screenid
        self.digit_dur = digit_dur
        self.isi = isi
        self.data_dir = data_dir
        self.lives = 3
        os.makedirs(self.data_dir, exist_ok=True)
        self.results = []

        # Stimuli principaux
        self.text_stim = visual.TextStim(self.win, color='white', height=0.08, pos=(0, 0.3))
        self.lives_stim = visual.TextStim(self.win, color='red', height=0.08, pos=(0, 0.9))
        self.instruction_stim = visual.TextStim(self.win, color='white', height=0.07)

        # Souris
        self.mouse = event.Mouse(win=self.win)

        # Boutons
        self.digit_buttons = []
        self.button_size = (0.1, 0.15)
        number_size = 0.06
        letter_size = 0.035
        button_spacing = 0.15
        start_pos = -(4 * button_spacing) / 2

        # Chiffres 0-4 (ligne haute)
        for i in range(5):
            btn = visual.ButtonStim(
                self.win, text=str(i), pos=(start_pos + i * button_spacing, 0.0),
                letterHeight=number_size, size=self.button_size, font='Arial',
                color='white', fillColor='darkgrey', borderColor='white'
            )
            self.digit_buttons.append(btn)

        # Chiffres 5-9 (ligne basse)
        for i in range(5, 10):
            btn = visual.ButtonStim(
                self.win, text=str(i), pos=(start_pos + (i - 5) * button_spacing, -0.2),
                letterHeight=number_size, size=self.button_size, font='Arial',
                color='white', fillColor='darkgrey', borderColor='white'
            )
            self.digit_buttons.append(btn)

        # Boutons Entrée et Effacer
        self.enter_button = visual.ButtonStim(
            self.win, text="Entrée", pos=(button_spacing * 2, -0.4),
            letterHeight=letter_size, size=self.button_size, font='Arial',
            color='white', fillColor='darkgrey', borderColor='white'
        )
        self.backspace_button = visual.ButtonStim(
            self.win, text="Effacer", pos=(-button_spacing * 2, -0.4),
            letterHeight=letter_size, size=self.button_size, font='Arial',
            color='white', fillColor='darkgrey', borderColor='white'
        )

    # ---------- Instructions ----------
    def show_instructions(self):
        instructions = (
            "Tâche Digit Span\n\n"
            "Une séquence de chiffres va s'afficher un par un.\n"
            "Votre tâche est de mémoriser la séquence puis de la saisir en cliquant sur les chiffres.\n"
            "Cliquez sur 'Entrée' pour valider, 'Effacer' pour corriger.\n"
            "Vous avez 3 vies. La tâche continue jusqu'à épuisement des vies.\n"
            "Appuyez sur une touche pour commencer."
        )
        self.instruction_stim.text = instructions
        self.instruction_stim.draw()
        self.win.flip()
        event.waitKeys()

    # ---------- Trigger scanner ----------
    def wait_for_trigger(self, trigger_key='t'):
        self.text_stim.text = f"En attente du trigger scanner ('{trigger_key}')\nAppuyez sur 'escape' pour quitter."
        self.text_stim.draw()
        self.win.flip()
        keys = event.waitKeys(keyList=[trigger_key, 'escape'])
        if 'escape' in keys:
            should_quit(self.win, quit=True)

    # ---------- Génération de séquence ----------
    def generate_sequence(self, length):
        return [str(random.randint(0, 9)) for _ in range(length)]

    # ---------- Affichage des vies ----------
    def draw_lives(self):
        self.lives_stim.text = "♥ " * self.lives
        self.lives_stim.draw()

    # ---------- Redessin de l’écran ----------
    def draw_all(self, response=''):
        self.text_stim.text = response if response else self.text_stim.text
        self.text_stim.draw()
        self.draw_lives()
        for btn in self.digit_buttons:
            btn.draw()
        self.enter_button.draw()
        self.backspace_button.draw()
        self.win.flip()

    # ---------- Saisie utilisateur ----------
    def get_response(self):
        response = ''
        self.mouse.clickReset()  # reset des clics au démarrage
        last_input_time = 0  # pour mémoriser le dernier input
        debounce = 0.2      # temps minimum (en secondes) entre deux inputs

        while True:
            self.draw_all(f"Saisie : {response}")
            now = core.getTime()

            # ----- Souris -----
            buttons, times = self.mouse.getPressed(getTime=True)
            if buttons[0] and (now - last_input_time > debounce):  # clic gauche + délai OK
                # Vérifier chiffres
                for i, btn in enumerate(self.digit_buttons):
                    if btn.contains(self.mouse):
                        response += str(i)
                        last_input_time = now
                        self.mouse.clickReset()
                        break
                # Vérifier entrée
                if self.enter_button.contains(self.mouse):
                    self.mouse.clickReset()
                    return response
                # Vérifier effacer
                if self.backspace_button.contains(self.mouse):
                    response = response[:-1]
                    last_input_time = now
                    self.mouse.clickReset()

            # ----- Clavier -----
            keys = event.getKeys()
            if keys and (now - last_input_time > debounce):  # délai OK
                for key in keys:
                    if key in ['escape', 'q']:
                        should_quit(self.win, quit=True)
                    elif key in ['return', 'num_enter']:
                        return response
                    elif key == 'backspace':
                        response = response[:-1]
                    elif key in '0123456789':
                        response += key
                last_input_time = now


    # ---------- Exécution d’un essai ----------
    def run_trial(self, length):
        seq = self.generate_sequence(length)
        # Affichage de la séquence
        for digit in seq:
            self.text_stim.text = digit
            self.draw_all()
            core.wait(self.digit_dur)
            self.text_stim.text = ''
            self.draw_all()
            core.wait(self.isi)

        # Pause courte avant saisie
        self.text_stim.text = "Cliquez sur les chiffres, puis 'Entrée'"
        self.draw_all()
        core.wait(0.8)

        response = self.get_response()
        if response is None:
            return None

        # ---------- Feedback global ----------
        accurate = (response == ''.join(seq))
        self.text_stim.color = 'green' if accurate else 'red'
        self.text_stim.text = f"Votre réponse : {response}"
        self.draw_all()
        core.wait(2)
        self.text_stim.color = 'white'  # remettre couleur par défaut pour essai suivant

        # Enregistrement du résultat
        self.results.append({
            'trial': len(self.results) + 1,
            'span': length,
            'sequence': ''.join(seq),
            'response': response,
            'accurate': accurate,
            'length': len(response)
        })
        print(f" Trial {self.results[-1]['trial']:2d} | Span: {length} | Séquence: {''.join(seq)} | "
            f"Réponse: {response} | Correct: {accurate} | Longueur: {len(response)}", flush=True)
        return accurate

    # ---------- Résumé des résultats ----------
    def print_results_summary(self):
        print("\n--- Résultats de la tâche Digit Span ---")
        n_correct = sum(r['accurate'] for r in self.results)
        n_trials = len(self.results)
        print(f"Réponses correctes : {n_correct} / {n_trials} ({100*n_correct/n_trials:.1f}%)" if n_trials > 0 else "Aucun essai")
        max_span = max([r['span'] for r in self.results if r['accurate']], default=0)
        print(f"Plus longue séquence correctement rappelée : {max_span}")
        print("\nDétail par essai :")
        for r in self.results:
            print(f"Essai {r['trial']:2d} | Span: {r['span']:2d} | Séquence: {r['sequence']} | "
                  f"Réponse: {r['response']} | Correct: {r['accurate']}")

    # ---------- Sauvegarde ----------
    def save_results(self):
        if not self.enregistrer:
            return
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        fname = f"{self.nom}DigitSpan{ts}.csv"
        path = os.path.join(self.data_dir, fname)
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'participant', 'date', 'trial', 'span', 'sequence', 'response', 'accurate', 'length'
            ])
            writer.writeheader()
            for row in self.results:
                writer.writerow({**row, 'participant': self.nom, 'date': ts})
        print(f"Données sauvegardées : {path}")

    # ---------- Exécution complète ----------
    def run(self):
        self.show_instructions()
        self.wait_for_trigger(trigger_key='t')
        current_span = 1
        while self.lives > 0:
            if should_quit(self.win):
                return None
            accurate = self.run_trial(current_span)
            if accurate is None:
                return None
            if accurate:
                current_span += 1
            else:
                self.lives -= 1
        self.print_results_summary()
        self.save_results()
        return self.results
