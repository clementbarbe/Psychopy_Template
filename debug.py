from utils.utils import is_valid_name

print(is_valid_name("jean"))     # True
print(is_valid_name("Jean123"))  # True
print(is_valid_name("jean-paul"))# True
print(is_valid_name("jean_paul"))# True
print(is_valid_name("jean paul"))# False (espace non autorisé)
print(is_valid_name("jean!"))    # False (caractère spécial non autorisé)
