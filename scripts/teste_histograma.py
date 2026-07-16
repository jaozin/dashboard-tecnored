import pandas as pd

arquivo = r"C:\Users\jsantos250\OneDrive - Bureau Veritas\POP - Planejamento - Documentos\Automacoes\Comparativo_Cronograma\entrada\J0006\Histograma\Histograma J0006.xlsx"

df = pd.read_excel(
    arquivo,
    header=None
)

recurso_atual = None

for linha in range(6, 34):

    recurso = df.iloc[linha, 1]

    if pd.notna(recurso):
        recurso_atual = str(recurso)

    tipo = str(
        df.iloc[linha, 2]
    ).replace(".", "")

    if tipo not in ["Prev", "Real"]:
        continue

    print(
        recurso_atual,
        "-",
        tipo
    )