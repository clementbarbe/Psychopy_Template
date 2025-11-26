# Template de Stimulation IRM – Interface PyQt6 (PsychoPy 2025.1.1)

Ce projet constitue un **template de préparation et de configuration de sessions de stimulation pour l'IRM**, conçu pour être utilisé avec **PsychoPy 2025.1.1**.  
Il fournit une interface PyQt6 permettant de sélectionner et paramétrer rapidement différentes tâches cognitives avant leur exécution.

## Fonctionnalités principales

- Configuration générale :
  - Nom du participant
  - Numéro d’écran / mode plein écran
  - Mode d'entrée (PC ou fMRI)
  - Option d’enregistrement des données  
- Interface claire avec onglets pour chaque tâche :
  - **NBack**
  - **DigitSpan**
  - **Flanker**
  - **Stroop**
  - **Visual Memory**
  - **Temporal Judgement**  
- Chaque tâche propose des paramètres ajustables (durées, ISI, nombre d’essais, etc.).
- Le menu renvoie une configuration complète à PsychoPy pour lancer la tâche.

## Installation

Installer PyQt6 :

```bash
pip install PyQt6
