from psychopy import visual, event, core, sound
import random, csv, os
from datetime import datetime
from utils.utils import should_quit
import subprocess

class AuditoryOddball:
    def __init__(self, win, nom, enregistrer=True,
                 p_deviant=0.2, n_trials=10,
                 isi=1.0, stim_dur=0.1,
                 data_dir='data/oddball',
                 sound_dir='utils/sound'):
        
        self.win = win
        self.nom = nom
        self.enregistrer = enregistrer
        self.p_deviant = p_deviant
        self.n_trials = n_trials
        self.isi = isi
        self.stim_dur = stim_dur
        self.data_dir = data_dir
        self.sound_dir = sound_dir

        self.results = []
        self.sequence = []
        self.fixation = visual.TextStim(self.win, text='+', color='white', height=0.2)
        self.text_stim = visual.TextStim(self.win, color='white', wrapWidth=1.5, height=0.07)
        self.trial_clock = core.Clock()
    
    def play_wav(self, filename):
        path = os.path.join(self.sound_dir, filename)
        subprocess.run(['aplay', '-q', path], check=True)

    def show_instructions(self):
        instructions = (
            f"Tâche Auditory Oddball\n\n"
            f"Vous entendrez une série de sons.\n"
            f"La plupart des sons (standards) ont une fréquence de 500 Hz.\n"
            f"Dans environ {int(self.p_deviant * 100)}% des cas, un son déviant de 550 Hz sera joué.\n"
            "Appuyez sur la barre espace dès que vous entendez un son déviant.\n\n"
            "Appuyez sur une touche pour commencer."
        )
        self.text_stim.text = instructions
        self.text_stim.draw()
        self.win.flip()
        event.waitKeys()

    def wait_for_trigger(self, trigger_key='t'):
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
        # Boolean list: True for deviant, False for standard
        self.sequence = [random.random() < self.p_deviant for _ in range(self.n_trials)]

    def run(self):
        self.show_instructions()
        self.wait_for_trigger('t')
        self.generate_sequence()

        for idx, is_deviant in enumerate(self.sequence):
            should_quit(self.win)
            event.clearEvents()

            self.fixation.draw()
            self.win.flip()
            core.wait(self.isi)

            self.trial_clock.reset()
            if is_deviant:
                self.play_wav('deviant.wav')
            else:
                self.play_wav('standard.wav')

            resp = 'no'
            rt = None
            responded = False
            while self.trial_clock.getTime() < self.stim_dur + 0.5:
                keys = event.getKeys(keyList=['space', 'escape'], timeStamped=self.trial_clock)
                if keys and not responded:
                    key, press_time = keys[0]
                    if key == 'escape':
                        should_quit(self.win, quit=True)
                    elif key == 'space':
                        resp = 'yes'
                        rt = round(press_time, 5)
                        responded = True
                core.wait(0.001)

            accurate = (resp == 'yes' and is_deviant) or (resp == 'no' and not is_deviant)
            self.results.append({
                'trial': idx + 1,
                'is_deviant': is_deviant,
                'response': resp,
                'accurate': accurate,
                'RT': rt
            })

        self.print_results_summary()
        if self.enregistrer:
            self.save_results()
        return self.results


    def print_results_summary(self):
        total = len(self.results)
        correct = sum(r['accurate'] for r in self.results)
        pct = correct/total*100 if total else 0
        print(f"\n--- Résultats Oddball ---\nCorrect: {correct}/{total} ({pct:.1f}%)")

    def save_results(self):
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        fname = f"{self.nom}_Oddball_{ts}.csv"
        path = os.path.join(self.data_dir, fname)
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['participant','date','trial','is_deviant','response','accurate','RT'])
            writer.writeheader()
            for row in self.results:
                writer.writerow({**row, 'participant': self.nom, 'date': ts})
        print(f"Données sauvegardées : {path}")

if __name__ == '__main__':
    from psychopy import logging
    logging.console.setLevel(logging.CRITICAL)
    win = visual.Window(fullscr=True, color='black')
    task = AuditoryOddball(win, nom='P01', enregistrer=True)
    task.run()
    win.close()
    core.quit()
