import pandas as pd
import io

# Create a sample dataframe
df = pd.DataFrame({'telefone': ['5581991234567', '81991234567'], 'imei': ['123456789012345', '123456789012345']})

# Save to bytes
output = io.BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    df.to_excel(writer, index=False)
xlsx_data = output.getvalue()

# Mock the streamlit file object
class MockFile(io.BytesIO):
    def __init__(self, data, name):
        super().__init__(data)
        self.name = name

file = MockFile(xlsx_data, "test.xlsx")

# Simulation of detecting header
def detectar_cabecalho(file, filename, max_linhas=15):
    try:
        file.seek(0)
        for i in range(max_linhas):
            file.seek(0)
            if filename.endswith(".csv"):
                df = pd.read_csv(file, header=i, nrows=5, encoding="utf-8", sep=None, engine='python')
            else:
                df = pd.read_excel(file, header=i, nrows=5)
            if df.shape[1] >= 2 and sum("Unnamed" in str(c) for c in df.columns) < df.shape[1] // 2:
                print(f"Detected header at row {i}")
                return i
        return 0
    except Exception as e:
        print(f"Error in detectar_cabecalho: {e}")
        return 0

header_row = detectar_cabecalho(file, "test.xlsx")
file.seek(0)
try:
    df_read = pd.read_excel(file, header=header_row, dtype=str)
    print("Columns read:", df_read.columns.tolist())
    print("First row:", df_read.iloc[0].to_dict())
except Exception as e:
    print(f"Error reading excel: {e}")
