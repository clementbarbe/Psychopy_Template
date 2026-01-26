import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def qc_temporaljudgement(csv_path):
    """
    Dashboard QC Final pour Temporal Judgement.
    6 Figures : Précision, ISI, Jitter technique, Distrib. Réponses, Corrélation (R²), Taux de complétion.
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

    # --- 1. RECONSTRUCTION DES DONNÉES (Basé sur ton CSV) ---
    
    # Target & Condition
    df_trials = df[df['event_type'] == 'trial_start'][['phase', 'trial', 'condition', 'delay_target_ms']].copy()

    # Timing Ampoule (bulb_lit)
    df_bulb = df[df['event_type'] == 'bulb_lit'][['phase', 'trial', 'error_ms', 'time_s']].rename(columns={'time_s': 't_bulb'})

    # Timing Prompt de réponse (response_prompt_shown)
    df_prompt = df[df['event_type'] == 'response_prompt_shown'][['phase', 'trial', 'time_s']].rename(columns={'time_s': 't_prompt'})

    # Réponses (response_given)
    df_resp = df[df['event_type'] == 'response_given'][['phase', 'trial', 'response_ms']].copy()

    # ISI (trial_end)
    df_isi = df[df['event_type'] == 'trial_end'][['isi_duration']].copy()

    # Fusion
    df_full = pd.merge(df_trials, df_bulb, on=['phase', 'trial'], how='left')
    df_full = pd.merge(df_full, df_prompt, on=['phase', 'trial'], how='left')
    df_full = pd.merge(df_full, df_resp, on=['phase', 'trial'], how='left')

    # Calcul Jitter : Temps entre l'allumage et l'apparition de l'échelle (en ms)
    df_full['jitter_ms'] = (df_full['t_prompt'] - df_full['t_bulb']) * 1000

    # Statut
    df_full['status'] = np.where(df_full['response_ms'].notna(), 'Répondu', 'Manqué')

    # --- 2. CONFIGURATION GRAPHIQUE ---
    plt.style.use('ggplot')
    fig, axes = plt.subplots(2, 3, figsize=(18, 11))
    fig.suptitle(f"QC Report: {os.path.basename(csv_path)}", fontsize=16, fontweight='bold')
    
    colors = {'active': '#2ca02c', 'passive': '#d62728'} 

    # FIG 1: PRÉCISION GLOBALE
    ax = axes[0, 0]
    sns.histplot(df_full['error_ms'].dropna(), kde=True, ax=ax, color='steelblue')
    ax.set_title(f"1. Précision Technique (Cible - Réel)\nMean: {df_full['error_ms'].mean():.2f}ms")
    ax.set_xlabel("Erreur (ms)")
    ax.axvline(0, color='black', ls='--')

    # FIG 2: DISTRIBUTION ISI
    ax = axes[0, 1]
    if not df_isi.empty:
        sns.histplot(df_isi['isi_duration'].dropna(), kde=True, ax=ax, color='purple')
        ax.set_title(f"2. Distribution ISI\nRange: [{df_isi['isi_duration'].min():.1f}s - {df_isi['isi_duration'].max():.1f}s]")
        ax.set_xlabel("Secondes")

    # FIG 3: DISTRIBUTION DU JITTER
    ax = axes[0, 2]
    jitter_vals = df_full['jitter_ms'].dropna()
    if not jitter_vals.empty:
        sns.histplot(jitter_vals, kde=True, ax=ax, color='chocolate')
        ax.set_title(f"3. Jitter (Stimulus -> Prompt)\nMoyenne: {jitter_vals.mean():.1f}ms")
        ax.set_xlabel("Délai (ms)")

    # FIG 4: DISTRIBUTION DES RÉPONSES
    ax = axes[1, 0]
    sns.countplot(x='response_ms', data=df_full.dropna(subset=['response_ms']), hue='condition', palette=colors, ax=ax)
    ax.set_title("4. Distribution des Réponses (ms)")
    ax.set_xlabel("Réponse choisie (ms)")

    # FIG 5: CORRÉLATION (R² par condition)
    ax = axes[1, 1]
    df_corr = df_full.dropna(subset=['response_ms', 'delay_target_ms'])
    for cond, color in colors.items():
        sub = df_corr[df_corr['condition'] == cond]
        if len(sub) > 1:
            r = sub['delay_target_ms'].corr(sub['response_ms'])
            r2 = r**2 if not np.isnan(r) else 0
            sns.regplot(x='delay_target_ms', y='response_ms', data=sub, ax=ax, 
                        scatter_kws={'alpha':0.5}, color=color, label=f"{cond} ($R^2$={r2:.2f})")
    ax.plot([100, 800], [100, 800], 'k--', alpha=0.3)
    ax.set_title("5. Corrélation Target vs Réponse")
    ax.set_xlabel("Target (ms)")
    ax.set_ylabel("Réponse (ms)")
    ax.legend()

    # FIG 6: RÉPARTITION RÉPONSES + CHIFFRE
    ax = axes[1, 2]
    sns.countplot(x='status', hue='condition', data=df_full, palette=colors, ax=ax)
    total = len(df_full)
    ok = len(df_full[df_full['status'] == 'Répondu'])
    ax.text(0.5, 0.85, f"{ok} / {total}", transform=ax.transAxes, ha='center', fontsize=32, fontweight='bold', color='#222')
    ax.text(0.5, 0.75, "ESSAIS RÉPONDUS", transform=ax.transAxes, ha='center', fontsize=12)
    ax.set_title("6. Taux de Réponse Global")
    ax.set_xlabel("")

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    png_name = os.path.basename(csv_path).replace('.csv', '_QC.png')
    save_path = os.path.join(qc_dir, png_name)
    plt.savefig(save_path, dpi=100)
    plt.close()
    
    print(f"QC Réussi : {save_path}")