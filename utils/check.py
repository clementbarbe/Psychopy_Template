import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import glob

# ============================================================================
# CHARGER LES DONNÉES
# ============================================================================
# Remplacez par le chemin de votre fichier CSV
data_files = glob.glob('data/temporal_judgement/*.csv')
if not data_files:
    print("❌ Aucun fichier CSV trouvé dans data/temporal_judgement/")
    exit(1)

# Charger le dernier fichier généré
csv_path = max(data_files, key=lambda f: Path(f).stat().st_mtime)
print(f"📂 Chargement : {csv_path}")
df = pd.read_csv(csv_path)

# Afficher les premières lignes et des infos de base
print(f"\n✓ {len(df)} essais chargés")
print(df.head())

# ============================================================================
# VÉRIFIER LES DÉLAIS OBSERVÉS vs DEMANDÉS
# ============================================================================
df['observed_delay_ms'] = (df['outcome_time_s'] - df['action_time_s']) * 1000
df['delay_error_ms'] = df['observed_delay_ms'] - df['requested_delay_ms']
df['delay_error_percent'] = (df['delay_error_ms'] / df['requested_delay_ms']) * 100

print("\n" + "="*60)
print("VÉRIFICATION DES DÉLAIS")
print("="*60)
for delay in sorted(df['requested_delay_ms'].unique()):
    subset = df[df['requested_delay_ms'] == delay]
    observed_mean = subset['observed_delay_ms'].mean()
    observed_std = subset['observed_delay_ms'].std()
    error_mean = subset['delay_error_ms'].mean()
    print(f"\nDélai demandé: {delay} ms")
    print(f"  Observé: {observed_mean:.2f} ± {observed_std:.2f} ms")
    print(f"  Erreur: {error_mean:.2f} ms ({subset['delay_error_percent'].mean():.2f}%)")

# ============================================================================
# FIGURE 1 : TIMELINE COMPLÈTE
# ============================================================================
fig, ax = plt.subplots(figsize=(14, 8))

colors = {'active': '#00CC00', 'passive': '#FF4444'}

for idx, row in df.iterrows():
    trial_n = row['trial']
    cond = row['condition']
    color = colors[cond]
    
    # Ligne horizontale pour cet essai
    ax.hlines(trial_n, row['trial_onset_s'], row['outcome_time_s'] + 0.5, 
              color=color, alpha=0.3, linewidth=3)
    
    # Point action
    if pd.notna(row['action_time_s']):
        ax.scatter(row['action_time_s'], trial_n, color=color, s=100, 
                  marker='o', edgecolor='white', linewidth=1.5, zorder=3, label='Action' if idx == 0 else '')
    
    # Point résultat (ampoule)
    ax.scatter(row['outcome_time_s'], trial_n, color=color, s=150, 
              marker='*', edgecolor='white', linewidth=1.5, zorder=3, label='Outcome' if idx == 0 else '')

# Styling
ax.set_ylabel('Essai #', fontsize=12, fontweight='bold')
ax.set_xlabel('Temps (s)', fontsize=12, fontweight='bold')
ax.set_title('Timeline complète de la tâche\n(○ = Action | ★ = Ampoule allumée)', 
            fontsize=14, fontweight='bold', pad=20)
ax.grid(True, alpha=0.3, axis='x')
ax.set_ylim(-1, len(df) + 1)

# Légende
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor='#00CC00', alpha=0.3, label='Condition ACTIVE'),
                   Patch(facecolor='#FF4444', alpha=0.3, label='Condition PASSIVE')]
ax.legend(handles=legend_elements, loc='upper right', fontsize=11)

plt.tight_layout()
plt.savefig('temporal_judgement_timeline.png', dpi=150, bbox_inches='tight')
print("\n✓ Sauvegardé : temporal_judgement_timeline.png")
plt.show()

# ============================================================================
# FIGURE 2 : ERREUR DE DÉLAI PAR ESSAI
# ============================================================================
fig, ax = plt.subplots(figsize=(14, 6))

for cond in ['active', 'passive']:
    subset = df[df['condition'] == cond]
    color = colors[cond]
    ax.scatter(subset['trial'], subset['delay_error_ms'], 
              color=color, s=80, alpha=0.7, label=f'{cond.upper()}', edgecolor='black', linewidth=0.5)

ax.axhline(y=0, color='black', linestyle='--', linewidth=2, alpha=0.7, label='Pas d\'erreur')
ax.fill_between(ax.get_xlim(), -50, 50, alpha=0.1, color='green', label='±50 ms (acceptable)')
ax.set_xlabel('Numéro d\'essai', fontsize=12, fontweight='bold')
ax.set_ylabel('Erreur de délai (ms observé - ms demandé)', fontsize=12, fontweight='bold')
ax.set_title('Précision des délais de stimulation', fontsize=14, fontweight='bold', pad=20)
ax.grid(True, alpha=0.3)
ax.legend(fontsize=11)

plt.tight_layout()
plt.savefig('temporal_judgement_delay_error.png', dpi=150, bbox_inches='tight')
print("✓ Sauvegardé : temporal_judgement_delay_error.png")
plt.show()

# ============================================================================
# FIGURE 3 : DÉLAI OBSERVÉ vs DÉLAI DEMANDÉ (BOX PLOT)
# ============================================================================
fig, ax = plt.subplots(figsize=(10, 7))

delays = sorted(df['requested_delay_ms'].unique())
data_by_delay = [df[df['requested_delay_ms'] == d]['observed_delay_ms'].values for d in delays]

bp = ax.boxplot(data_by_delay, labels=[f'{d} ms' for d in delays], patch_artist=True)

# Colorer les box plots
for patch, delay in zip(bp['boxes'], delays):
    patch.set_facecolor('#3498db')
    patch.set_alpha(0.7)

# Ajouter la ligne "parfait" y=x
for i, delay in enumerate(delays, 1):
    ax.hlines(delay, i - 0.3, i + 0.3, color='red', linestyle='--', linewidth=2, label='Théorique' if i == 1 else '')

ax.set_ylabel('Délai observé (ms)', fontsize=12, fontweight='bold')
ax.set_xlabel('Délai demandé (ms)', fontsize=12, fontweight='bold')
ax.set_title('Distribution des délais observés vs demandés', fontsize=14, fontweight='bold', pad=20)
ax.grid(True, alpha=0.3, axis='y')
ax.legend(fontsize=11)

plt.tight_layout()
plt.savefig('temporal_judgement_boxplot.png', dpi=150, bbox_inches='tight')
print("✓ Sauvegardé : temporal_judgement_boxplot.png")
plt.show()

# ============================================================================
# FIGURE 4 : RT (REACTION TIME) ET CONDITION
# ============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# RT par condition
for cond in ['active', 'passive']:
    subset = df[df['condition'] == cond]
    color = colors[cond]
    ax1.scatter(subset['trial'], subset['RT_s'] * 1000, 
               color=color, s=80, alpha=0.7, label=cond.upper(), edgecolor='black', linewidth=0.5)

ax1.set_xlabel('Numéro d\'essai', fontsize=12, fontweight='bold')
ax1.set_ylabel('Reaction Time (ms)', fontsize=12, fontweight='bold')
ax1.set_title('Temps de réponse par essai', fontsize=13, fontweight='bold')
ax1.grid(True, alpha=0.3)
ax1.legend(fontsize=11)

# Comparaison RT par condition
rt_active = df[df['condition'] == 'active']['RT_s'].dropna() * 1000
rt_passive = df[df['condition'] == 'passive']['RT_s'].dropna() * 1000

bp = ax2.boxplot([rt_active, rt_passive], labels=['ACTIVE', 'PASSIVE'], patch_artist=True)
for patch, color_key in zip(bp['boxes'], ['active', 'passive']):
    patch.set_facecolor(colors[color_key])
    patch.set_alpha(0.7)

ax2.set_ylabel('Reaction Time (ms)', fontsize=12, fontweight='bold')
ax2.set_title('RT par condition', fontsize=13, fontweight='bold')
ax2.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('temporal_judgement_RT.png', dpi=150, bbox_inches='tight')
print("✓ Sauvegardé : temporal_judgement_RT.png")
plt.show()

# ============================================================================
# RÉSUMÉ FINAL
# ============================================================================
print("\n" + "="*60)
print("RÉSUMÉ POUR L'ANALYSE BOLD")
print("="*60)
print(f"\n✓ Total d'essais: {len(df)}")
print(f"✓ Conditions: {df['condition'].unique()}")
print(f"✓ Délais testés: {sorted(df['requested_delay_ms'].unique())} ms")
print(f"\n✓ Durée totale de la tâche: {df['outcome_time_s'].max():.2f} s ({df['outcome_time_s'].max()/60:.2f} min)")
print(f"✓ Erreur moyenne: {df['delay_error_ms'].mean():.2f} ms")
print(f"✓ Erreur std: {df['delay_error_ms'].std():.2f} ms")

# Vérifier les essais problématiques
problematic = df[df['delay_error_ms'].abs() > 100]
if len(problematic) > 0:
    print(f"\n⚠ {len(problematic)} essai(s) avec erreur > 100 ms !")
    print(problematic[['trial', 'condition', 'requested_delay_ms', 'delay_error_ms']])
else:
    print(f"\n✓ Tous les essais respectent une erreur < 100 ms")