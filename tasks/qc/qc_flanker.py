import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def qc_flanker(csv_path):
    """
    Dashboard QC Final - Version Flanker Task (optimisé pour timing absolu)
    1. Taux de Réponse Correcte par Condition (Congruent/Incongruent)
    2. Distribution des Temps de Réaction (RT) par Condition
    3. Drift Temporel (Précision des Onsets)
    4. Distribution des ISI/Jitter
    5. Taux d'Erreur par Condition
    6. Résumé des Statuts de Réponse (HIT/MISS/WRONG)
    """
    if not os.path.exists(csv_path):
        print(f"QC Error: Fichier non trouvé {csv_path}")
        return

    print(f"--- Lancement du QC sur {os.path.basename(csv_path)} ---")

    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"QC Error: Impossible de lire le CSV. {e}")
        return

    # Dossier QC
    csv_dir = os.path.dirname(csv_path)
    qc_dir = os.path.join(csv_dir, 'qc')
    os.makedirs(qc_dir, exist_ok=True)

    # --- 1. NETTOYAGE & PRÉPARATION ---
    required_cols = ['condition', 'rt', 'acc', 'onset_goal', 'onset_time', 'isi_jitter']
    for col in required_cols:
        if col not in df.columns:
            print(f"QC Warning: Colonne manquante: {col}")
            return

    # Calcul du drift temporel
    df['drift_ms'] = (df['onset_time'] - df['onset_goal']) * 1000

    # --- 2. MÉTRIQUES ---
    # Taux de réponse correcte par condition
    response_summary = df.groupby('condition')['acc'].agg(['mean', 'count'])

    # --- 3. GRAPHIQUES ---
    plt.style.use('ggplot')
    fig, axes = plt.subplots(2, 3, figsize=(18, 11))
    fig.suptitle(f"QC Report: {os.path.basename(csv_path)}", fontsize=16, fontweight='bold')

    colors = {'congruent': '#2ca02c', 'incongruent': '#d62728'}

    # FIG 1: TAUX DE RÉPONSE CORRECTE PAR CONDITION
    ax = axes[0, 0]
    sns.barplot(x=response_summary.index, y='mean', data=response_summary.reset_index(),
                hue=response_summary.index, palette=colors, legend=False, ax=ax)
    ax.set_title("1. Taux de Réponse Correcte par Condition")
    ax.set_ylabel("Taux de Réponse Correcte")
    ax.set_xlabel("Condition")

    # FIG 2: DISTRIBUTION DES TEMPS DE RÉACTION (RT)
    ax = axes[0, 1]
    sns.boxplot(x='condition', y='rt', data=df[df['rt'].notna()],
                hue='condition', palette=colors, legend=False, ax=ax)
    ax.set_title("2. Distribution des RT (s)")
    ax.set_ylabel("Temps de Réaction (s)")

    # FIG 3: DRIFT TEMPOREL (PRÉCISION DES ONSETS)
    ax = axes[0, 2]
    sns.histplot(df['drift_ms'].dropna(), kde=True, ax=ax, color='purple')
    ax.set_title(f"3. Drift Temporel (ms)\nMoyenne: {df['drift_ms'].mean():.1f}ms")
    ax.set_xlabel("Drift (ms)")
    ax.axvline(0, color='black', ls='--')

    # FIG 4: DISTRIBUTION DES ISI/JITTER
    ax = axes[1, 0]
    sns.histplot(df['isi_jitter'].dropna(), kde=True, ax=ax, color='teal')
    ax.set_title(f"4. Distribution ISI/Jitter\nMoyenne: {df['isi_jitter'].mean():.2f}s")
    ax.set_xlabel("ISI (s)")

    # FIG 5: TAUX D'ERREUR PAR CONDITION
    ax = axes[1, 1]
    error_rates = df[df['acc'] == 0].groupby('condition').size() / df.groupby('condition').size()
    error_rates = error_rates.reset_index(name='error_rate')
    sns.barplot(x='condition', y='error_rate', data=error_rates,
                hue='condition', palette=colors, legend=False, ax=ax)
    ax.set_title("5. Taux d'Erreur par Condition")
    ax.set_ylabel("Taux d'Erreur")

    # FIG 6: RÉSUMÉ DES STATUTS DE RÉPONSE
    ax = axes[1, 2]
    df['status'] = df.apply(lambda x: "HIT" if x['acc'] == 1 else ("MISS" if pd.isna(x['rt']) else "WRONG"), axis=1)
    status_counts = df['status'].value_counts().reset_index()
    status_counts.columns = ['status', 'count']
    sns.barplot(x='status', y='count', data=status_counts, ax=ax, palette='viridis', hue='status', legend=False)
    ax.set_title("6. Résumé des Statuts de Réponse")
    ax.set_xlabel("Statut")
    ax.set_ylabel("Nombre d'Essais")

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    png_name = os.path.basename(csv_path).replace('.csv', '_QC.png')
    save_path = os.path.join(qc_dir, png_name)
    plt.savefig(save_path, dpi=100)
    plt.close()

    print(f"QC Réussi : {save_path}")
