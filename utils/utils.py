import re
from psychopy import event, core

def is_valid_name(name: str) -> bool:
    name = name.strip()
    pattern = r"^[\w\s\-']+$"
    return bool(re.match(pattern, name, re.UNICODE))

is_valid_number_map = {
    'int': lambda v, min, max: _check_int(v, min, max),
    'float': lambda v, min, max: _check_float(v, min, max)
}

def _check_int(val, min=None, max=None):
    try:
        i = int(val)
    except:
        return False
    return (min is None or i >= min) and (max is None or i <= max)

def _check_float(val, min=None, max=None):
    try:
        f = float(val)
    except:
        return False
    return (min is None or f >= min) and (max is None or f <= max)

def is_valid_number(val, type='int', min=None, max=None):
    return is_valid_number_map[type](val, min, max)

def should_quit(win=None, quit=False):
    """
    Vérifie si on doit quitter.
    - Si quit=True est passé en argument : on quitte immédiatement (forcé).
    - Sinon : on vérifie si l'utilisateur a appuyé sur 'escape' ou 'q'.
    """
    # Si l'ordre de quitter n'est pas explicite, on vérifie le clavier
    if not quit:
        keys = event.getKeys(keyList=['escape', 'q'])
        if keys:
            quit = True

    # Si on doit quitter (soit forcé, soit détecté ci-dessus)
    if quit:
        if win:
            try:
                win.close()
            except:
                pass # Évite une erreur si la fenêtre est déjà fermée
        core.quit() # Lève SystemExit (attrapé par le 'finally' du main)
        return True
    
    return False