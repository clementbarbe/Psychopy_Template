import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def qc_stroop(csv_path):
    """
    Dashboard QC Final - Version Stroop Task
    1. Taux de Réponse par Condition (Go/No-Go, Congruent/Incongruent)
    2. Distribution des Temps de Réaction (RT) par Condition
    3. Taux d'Erreur par Condition
    4. Distribution des ISI/Jitter
    5. Corrélation RT vs Congruence (si applicable)
    6. Résumé des Triggers/Événements
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
    # On s'assure que les colonnes attendues existent
    required_cols = ['trial_type', 'congruent', 'rt', 'accuracy', 'status', 'trigger_stim', 'trigger_resp']
    for col in required_cols:
        if col not in df.columns:
            print(f"QC Warning: Colonne manquante: {col}")
            return

    # --- 2. MÉTRIQUES ---
    # Taux de réponse par condition
    df['congruent_str'] = df['congruent'].map({True: 'Congruent', False: 'Incongruent'})
    response_summary = df.groupby(['trial_type', 'congruent_str'])['accuracy'].agg(['mean', 'count'])

    # --- 3. GRAPHIQUES ---
    plt.style.use('ggplot')
    fig, axes = plt.subplots(2, 3, figsize=(18, 11))
    fig.suptitle(f"QC Report: {os.path.basename(csv_path)}", fontsize=16, fontweight='bold')

    colors = {'GO': '#2ca02c', 'NOGO': '#d62728', 'Congruent': '#1f77b4', 'Incongruent': '#ff7f0e'}

    # FIG 1: TAUX DE RÉPONSE PAR CONDITION
    ax = axes[0, 0]
    sns.barplot(x=response_summary.index.get_level_values(0),
                y='mean',
                hue=response_summary.index.get_level_values(1),
                data=response_summary.reset_index(),
                palette=colors,
                ax=ax)
    ax.set_title("1. Taux de Réponse Correcte par Condition")
    ax.set_ylabel("Taux de Réponse Correcte")
    ax.set_xlabel("Type d'Essai")

    # FIG 2: DISTRIBUTION DES TEMPS DE RÉACTION (RT)
    ax = axes[0, 1]
    sns.boxplot(x='congruent_str', y='rt', hue='trial_type', data=df[df['rt'].notna()], palette=colors, ax=ax)
    ax.set_title("2. Distribution des RT (s)")
    ax.set_ylabel("Temps de Réaction (s)")

    # FIG 3: TAUX D'ERREUR PAR CONDITION
    ax = axes[0, 2]
    error_rates = df[df['accuracy'] == 0].groupby(['trial_type', 'congruent_str']).size() / df.groupby(['trial_type', 'congruent_str']).size()
    error_rates = error_rates.reset_index(name='error_rate')
    sns.barplot(x='trial_type', y='error_rate', hue='congruent_str', data=error_rates, palette=colors, ax=ax)
    ax.set_title("3. Taux d'Erreur par Condition")
    ax.set_ylabel("Taux d'Erreur")

    # FIG 4: DISTRIBUTION DES ISI/JITTER
    ax = axes[1, 0]
    # Supposons que l'ISI est calculé comme la différence entre les onsets (à adapter selon ton CSV)
    if 'onset_time' in df.columns:
        df['isi'] = df['onset_time'].diff().dropna()
        sns.histplot(df['isi'].dropna(), kde=True, ax=ax, color='purple')
        ax.set_title(f"4. Distribution ISI\nMoyenne: {df['isi'].mean():.2f}s")
        ax.set_xlabel("ISI (s)")

    # FIG 5: CORRÉLATION RT vs CONGRUENCE (si applicable)
    ax = axes[1, 1]
    df_corr = df[df['rt'].notna()].copy()
    df_corr['congruent_int'] = df_corr['congruent'].astype(int)
    sns.regplot(x='congruent_int', y='rt', data=df_corr, ax=ax, color='darkorange')
    ax.set_title("5. Corrélation RT vs Congruence")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(['Incongruent', 'Congruent'])

    # FIG 6: RÉSUMÉ DES TRIGGERS/ÉVÉNEMENTS
    ax = axes[1, 2]
    trigger_counts = df['trigger_stim'].value_counts().reset_index()
    trigger_counts.columns = ['trigger', 'count']
    sns.barplot(x='trigger', y='count', data=trigger_counts, ax=ax, color='teal')
    ax.set_title("6. Nombre d'Essais par Trigger (Stim)")
    ax.set_xlabel("Code Trigger")
    ax.set_ylabel("Nombre d'Essais")

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    png_name = os.path.basename(csv_path).replace('.csv', '_QC.png')
    save_path = os.path.join(qc_dir, png_name)
    plt.savefig(save_path, dpi=100)
    plt.close()

    print(f"QC Réussi : {save_path}")
