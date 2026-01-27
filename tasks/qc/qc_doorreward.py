import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def qc_doorreward(csv_path):
    """
    QC Door Reward Task (IRMf)

    Contrôles principaux :
    1. Taux de réponse / timeout
    2. Distribution des RT + dérive temporelle
    3. Stabilité des onsets (doors_onset)
    4. Distribution des jitters (pré-feedback, ITI)
    5. Répartition des choix (portes)
    6. Résumé des événements / triggers logiques
    """

    if not os.path.exists(csv_path):
        print(f"[QC] Fichier introuvable : {csv_path}")
        return

    print(f"[QC] Lancement QC DoorReward : {os.path.basename(csv_path)}")

    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"[QC] Erreur lecture CSV : {e}")
        return

    # ------------------------------------------------------------------
    # DOSSIERS
    # ------------------------------------------------------------------
    csv_dir = os.path.dirname(csv_path)
    qc_dir = os.path.join(csv_dir, "qc")
    os.makedirs(qc_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # SANITY CHECK COLONNES
    # ------------------------------------------------------------------
    required_cols = ['trial', 'time_s', 'event_type']
    for col in required_cols:
        if col not in df.columns:
            print(f"[QC] Colonne manquante : {col}")
            return

    # ------------------------------------------------------------------
    # RESTRUCTURATION PAR ESSAI
    # ------------------------------------------------------------------
    stim_df = df[df['event_type'] == 'stim_onset_doors']
    resp_df = df[df['event_type'] == 'response_made']
    timeout_df = df[df['event_type'] == 'timeout']
    iti_df = df[df['event_type'] == 'iti_end']

    n_trials = stim_df['trial'].nunique()

    # ------------------------------------------------------------------
    # MÉTRIQUES COMPORTEMENTALES
    # ------------------------------------------------------------------
    rt = resp_df['rt'].dropna()
    timeout_rate = len(timeout_df) / n_trials

    # dérive RT (fatigue / perte attention)
    resp_df_sorted = resp_df.sort_values('trial')
    rt_slope = np.polyfit(resp_df_sorted['trial'], resp_df_sorted['rt'], 1)[0]

    # ------------------------------------------------------------------
    # STABILITÉ TEMPORELLE
    # ------------------------------------------------------------------
    stim_times = stim_df.sort_values('trial')['time_s'].values
    isi = np.diff(stim_times)

    iti_durations = iti_df['iti_duration'].dropna()

    # ------------------------------------------------------------------
    # CHOIX
    # ------------------------------------------------------------------
    if 'choice_idx' in resp_df.columns:
        choice_counts = resp_df['choice_idx'].value_counts().sort_index()
    else:
        choice_counts = pd.Series(dtype=int)

    # ------------------------------------------------------------------
    # FIGURES
    # ------------------------------------------------------------------
    plt.style.use('ggplot')
    fig, axes = plt.subplots(2, 3, figsize=(18, 11))
    fig.suptitle(f"QC DoorReward — {os.path.basename(csv_path)}",
                 fontsize=16, fontweight='bold')

    # 1. Taux de réponse / timeout
    ax = axes[0, 0]
    ax.bar(['Réponses', 'Timeout'],
           [len(resp_df), len(timeout_df)],
           color=['green', 'red'])
    ax.set_title("1. Réponses vs Timeout")
    ax.text(1, len(timeout_df),
            f"{timeout_rate*100:.1f} %",
            ha='center', va='bottom')

    # 2. Distribution des RT
    ax = axes[0, 1]
    sns.histplot(rt, bins=20, kde=True, ax=ax)
    ax.set_title(f"2. RT (s)\nMean={rt.mean():.3f}s | SD={rt.std():.3f}s")
    ax.set_xlabel("Temps de Réaction (s)")

    # 3. Dérive temporelle RT
    ax = axes[0, 2]
    sns.regplot(x='trial', y='rt', data=resp_df_sorted, ax=ax)
    ax.set_title(f"3. Dérive RT (pente={rt_slope:.4f} s/trial)")
    ax.set_xlabel("Essai")
    ax.set_ylabel("RT (s)")

    # 4. ISI entre onsets portes
    ax = axes[1, 0]
    sns.histplot(isi, bins=20, kde=True, ax=ax)
    ax.set_title(f"4. ISI Doors Onset\nMean={isi.mean():.2f}s | SD={isi.std():.2f}s")
    ax.set_xlabel("ISI (s)")

    # 5. Distribution ITI
    ax = axes[1, 1]
    sns.histplot(iti_durations, bins=20, kde=True, ax=ax)
    ax.set_title(f"5. ITI\nMean={iti_durations.mean():.2f}s")
    ax.set_xlabel("ITI (s)")

    # 6. Répartition des choix
    ax = axes[1, 2]
    if not choice_counts.empty:
        ax.bar(['Gauche', 'Centre', 'Droite'], choice_counts.values)
        ax.set_title("6. Répartition des Choix")
        ax.set_ylabel("N essais")
    else:
        ax.text(0.5, 0.5, "Choix indisponibles",
                ha='center', va='center')
        ax.axis('off')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    png_name = os.path.basename(csv_path).replace('.csv', '_QC.png')
    save_path = os.path.join(qc_dir, png_name)
    plt.savefig(save_path, dpi=100)
    plt.close()

    # ------------------------------------------------------------------
    # RÉSUMÉ RAPIDE CONSOLE
    # ------------------------------------------------------------------
    print("------ QC RÉSUMÉ ------")
    print(f"Trials attendus      : {n_trials}")
    print(f"Taux timeout         : {timeout_rate*100:.1f} %")
    print(f"RT moyen             : {rt.mean():.3f} s")
    print(f"Dérive RT (s/trial)  : {rt_slope:.4f}")
    print(f"ISI moyen            : {isi.mean():.2f} s")
    print(f"ITI moyen            : {iti_durations.mean():.2f} s")
    print(f"[QC] Figure sauvegardée : {save_path}")
