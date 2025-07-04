import numpy as np
import matplotlib.pyplot as plt

def analyze_timing(flip_times, expected_hz=60.0):
    """
    Analyse les timestamps collectés de win.flip() et affiche les métriques & plots.

    :param flip_times: liste de timestamps de core.getTime() après chaque flip
    :param expected_hz: fréquence cible de l'écran
    """
    expected_ifi = 1.0 / expected_hz
    times = np.array(flip_times)
    rel_times = times - times[0]
    ifi = np.diff(times)
    frame_idx = np.arange(len(times))
    scheduled_times = frame_idx * expected_ifi
    onset_delay = rel_times - scheduled_times
    duration_delay = np.concatenate(([0], ifi - expected_ifi))

    # Affichage console
    print("\n--- Timing Analysis ---")
    print(f"IFI moyen     : {np.mean(ifi)*1000:.3f} ms")
    print(f"Jitter (std)  : {np.std(ifi - expected_ifi)*1000:.3f} ms")
    print(f"Fréquence     : {1.0/np.mean(ifi):.2f} Hz (attendu {expected_hz} Hz)")
    print(f"Frames sautées (>1.5×IFI): {np.sum(ifi > expected_ifi * 1.5)}")

    # Plot: Onset Delay
    plt.figure(figsize=(12, 4))
    plt.stem(frame_idx, onset_delay * 1000, linefmt='-', markerfmt='o', basefmt=' ')
    plt.title('Onset Delay (ms) par frame index')
    plt.xlabel('Index de frame')
    plt.ylabel('Onset Delay (ms)')
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    # Plot: Duration Delay
    plt.figure(figsize=(12, 4))
    plt.stem(frame_idx, duration_delay * 1000, linefmt='-', markerfmt='o', basefmt=' ')
    plt.title('Duration Delay (ms) par frame index')
    plt.xlabel('Index de frame')
    plt.ylabel('Duration Delay (ms)')
    plt.grid(True)
    plt.tight_layout()
    plt.show()