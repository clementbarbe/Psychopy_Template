from psychopy import visual, event, core
import random, csv, os
from datetime import datetime

class VisualMemory:
    def __init__(self, win, nom, enregistrer=True, data_dir="data/visualmemory"):
        self.win = win
        self.nom = nom
        self.enregistrer = enregistrer
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

        # paramètres
        self.lives = 3
        self.level = 3      # taille de la grille (N x N)
        self.streak = 0     # compteur de réussites consécutives
        self.flash_time = 1.0
        self.wait_time = 0.5
        self.extra_targets = 0


        # stimuli textuels
        self.instruction_stim = visual.TextStim(self.win, color='white', height=0.07, wrapWidth=1.2)
        self.lives_stim = visual.TextStim(self.win, color='red', height=0.08, pos=(0, 0.9))

        # souris
        self.mouse = event.Mouse(win=self.win)

        # bouton "Valider"
        self.validate_button = visual.ButtonStim(
            self.win, text="Valider", pos=(0, -0.8),
            letterHeight=0.05, size=(0.25, 0.12),
            color="white", fillColor="darkgrey", borderColor="white"
        )

        # résultats
        self.results = []

    # ---------- Instructions ----------
    def show_instructions(self):
        text = (
            "Tâche Visual Memory\n\n"
            "Une grille de cases va apparaître.\n"
            "Certaines cases vont s'allumer brièvement.\n"
            "Cliquez sur les cases pour les sélectionner/désélectionner.\n"
            "Appuyez sur le bouton 'Valider' pour confirmer votre choix.\n"
            "Vous avez 3 vies. La difficulté augmente après 3 réussites consécutives.\n\n"
            "Appuyez sur une touche pour commencer."
        )
        self.instruction_stim.text = text
        self.instruction_stim.draw()
        self.win.flip()
        event.waitKeys()

    # ---------- Affichage des vies ----------
    def draw_lives(self):
        self.lives_stim.text = "♥ " * self.lives
        self.lives_stim.draw()

    # ---------- Génération de la grille ----------
    def generate_grid(self, n, grid_frac=0.5):

        grid = []

        # taille fenêtre en pixels
        win_w, win_h = self.win.size
        extent_px = int(min(win_w, win_h) * float(grid_frac))  # taille totale de la grille en px

        # taille d'une cellule en pixels (on garde un petit margin pour l'espacement)
        cell_px = extent_px / n
        pad_px = cell_px * 0.1             # padding intérieur (10% -> case remplit 90% du cell)
        rect_px = cell_px - pad_px         # taille effective du rect (largeur==hauteur -> carré)

        # coordonnées de départ (coin supérieur gauche en repère centré)
        # on calcule les centres des cellules : start correspond au centre de la cellule (0,0) décalé
        start_x = - (cell_px * (n - 1)) / 2.0
        start_y = + (cell_px * (n - 1)) / 2.0  # on parcourt i de haut en bas => start_y positif

        for i in range(n):
            row = []
            for j in range(n):
                # centre de la cellule j (x) et i (y) en pixels, relatif au centre de la fenêtre
                cx = start_x + j * cell_px
                cy = start_y - i * cell_px  # minus parce que i augmente vers le bas

                rect = visual.Rect(
                    self.win,
                    width=rect_px, height=rect_px,   # même valeur => parfait carré (en pixels)
                    units='pix',                     # IMPORTANT : travailler en pixels
                    pos=(cx, cy),
                    fillColor="darkgrey",
                    lineColor="white"
                )
                row.append(rect)
            grid.append(row)

        return grid


    # ---------- Sélection aléatoire des cibles ----------
    def select_targets(self, grid, n_targets):
        N = len(grid)
        all_pos = [(i, j) for i in range(N) for j in range(N)]
        return random.sample(all_pos, n_targets)

    # ---------- Afficher la grille ----------
    def draw_grid(self, grid):
        for row in grid:
            for rect in row:
                rect.draw()

    # ---------- Essai ----------
    def run_trial(self):
        n = self.level
        grid = self.generate_grid(n)

        n_targets = max(3, n) + self.extra_targets
        targets = self.select_targets(grid, n_targets)

        # --- phase d’illumination ---
        for (i, j) in targets:
            grid[i][j].fillColor = "yellow"
        self.draw_grid(grid)
        self.draw_lives()
        self.win.flip()
        core.wait(self.flash_time)

        # retour normal
        for (i, j) in targets:
            grid[i][j].fillColor = "darkgrey"

        self.draw_grid(grid)
        self.draw_lives()
        self.win.flip()
        core.wait(self.wait_time)

        # --- phase de réponse ---
        response = []
        self.mouse.clickReset()

        while True:
            self.draw_grid(grid)
            self.draw_lives()
            self.validate_button.draw()
            self.win.flip()

            if self.mouse.getPressed()[0]:
                if self.validate_button.contains(self.mouse):
                    self.mouse.clickReset()
                    break  # validation

                for i in range(n):
                    for j in range(n):
                        if grid[i][j].contains(self.mouse):
                            if (i, j) in response:
                                response.remove((i, j))
                                grid[i][j].fillColor = "darkgrey"  # désélection
                            else:
                                response.append((i, j))
                                grid[i][j].fillColor = "blue"  # sélection
                            core.wait(0.1)  # petit délai pour éviter multi-clicsq
                self.mouse.clickReset()

            keys = event.getKeys()
            if "escape" in keys:
                core.quit()

        # --- vérifier la réponse ---
        correct = set(response) == set(targets)

        for (i, j) in targets:
            grid[i][j].fillColor = "green" if correct else "red"
        self.draw_grid(grid)
        self.draw_lives()
        self.win.flip()
        core.wait(1.5)

        self.results.append({
            "trial": len(self.results) + 1,
            "grid_size": n,
            "n_targets": n_targets,
            "targets": targets,
            "response": response,
            "correct": correct
        })

        return correct

    # ---------- Sauvegarde ----------
    def save_results(self):
        if not self.enregistrer:
            return
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"{self.nom}_VisualMemory_{ts}.csv"
        path = os.path.join(self.data_dir, fname)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "participant", "date", "trial", "grid_size", "n_targets", "targets", "response", "correct"
            ])
            writer.writeheader()
            for row in self.results:
                writer.writerow({
                    **row,
                    "participant": self.nom,
                    "date": ts
                })
        print(f"Données sauvegardées : {path}")

    # ---------- Exécution complète ----------
    def run(self):
        self.show_instructions()
        while self.lives > 0:
            correct = self.run_trial()
            if correct:
                self.streak += 1
                if self.streak == 3:  # après 3 succès consécutifs
                    self.level += 1
                    self.streak = 0
                    # tous les 2 niveaux → ajouter une cible
                    if (self.level) % 2 == 0:
                        self.extra_targets += 1

            else:
                self.lives -= 1
                self.streak = 0
        self.save_results()
        return self.results