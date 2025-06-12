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

def should_quit(win=None):
    """
    Vérifie si l'utilisateur a appuyé sur 'escape' ou 'q' pour quitter.
    Si oui, ferme la fenêtre PsychoPy (si fournie) et quitte proprement.
    """
    keys = event.getKeys(keyList=['escape', 'q'])
    if keys:
        if win:
            win.close()
        core.quit()
        return True
    return False