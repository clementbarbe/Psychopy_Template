from psychopy import parallel, core

# --- CLASSE FICTIVE (DÉSACTIVÉE PAR PARAMÈTRE) ---
# Implémente la même interface que ParPort mais sans aucune opération I/O ni impression.
class DummyParPort:
    def __init__(self, *args, **kwargs):
        pass 

    def send_trigger(self, code, duration=0.01):
        pass 

    def reset(self):
        pass

# --- CLASSE PRINCIPALE (CONNEXION PHYSIQUE) ---
class ParPort:
    def __init__(self, address=0x378):
        """
        Initialise le port parallèle.
        """
        self.address = address
        self.port = None
        self.dummy_mode = False

        try:
            parallel.setPortAddress(address)
            self.port = parallel.ParallelPort(address)
            self.port.setData(0)
        except Exception as e:
            # Conserve uniquement le message d'avertissement en cas d'échec
            # Cela permet de savoir pourquoi la case est grisée dans le menu
            print(f"ATTENTION : Port parallèle non trouvé à {hex(address)}. Mode simulation activé.")
            self.dummy_mode = True

    def send_trigger(self, code, duration=0.01):
        """
        Envoie un trigger (code) et remet à 0 après duration secondes.
        """
        if self.dummy_mode:
            return

        try:
            self.port.setData(int(code))
            core.wait(duration)
            self.port.setData(0)
        except Exception as e:
            print(f"Erreur envoi trigger {code}: {e}")

    def reset(self):
        """Force la remise à zéro des pins"""
        if not self.dummy_mode and self.port:
            self.port.setData(0)