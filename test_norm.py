import pandas as pd
import re

def _limpar_valor_excel(valor):
    if pd.isna(valor): return ""
    v = str(valor).strip()
    if v.endswith('.0'): v = v[:-2]
    return v

def old_normalize(numero):
    if pd.isna(numero): return None
    numero_str = str(numero).strip()
    numero_limpo = re.sub(r"[^\d]", "", numero_str)
    return numero_limpo

def new_normalize(numero):
    v = _limpar_valor_excel(numero)
    numero_limpo = re.sub(r"[^\d]", "", v)
    return numero_limpo

test_val = 5581991234567.0
print(f"Original: {test_val}")
print(f"Old: {old_normalize(test_val)}")
print(f"New: {new_normalize(test_val)}")

test_sci = 5.581991234567e12
print(f"Sci: {test_sci}")
print(f"Old: {old_normalize(test_sci)}")
print(f"New: {new_normalize(test_sci)}")
