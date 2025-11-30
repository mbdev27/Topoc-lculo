import pandas as pd
import io

def download_modelo_excel():
    df = pd.DataFrame({
        "EST": ["P1", "P1"],
        "PV": ["P2", "P3"],
        "Hz_PD": ["" , ""],
        "Hz_PI": ["" , ""],
        "Z_PD":  ["" , ""],
        "Z_PI":  ["" , ""],
        "DI_PD": ["" , ""],
        "DI_PI": ["" , ""]
    })

    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    return buffer
