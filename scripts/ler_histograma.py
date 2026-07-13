import pandas as pd

arquivo = r"C:\Users\jsantos250\OneDrive - Bureau Veritas\POP - Planejamento - Documentos\Automacoes\Comparativo_Cronograma\entrada\J0006\Histograma\Histograma J006.xlsx"

df = pd.read_excel(
    arquivo,
    header=None
)

for i in range(0, 148):
    print(i, "->", df.iloc[5, i])