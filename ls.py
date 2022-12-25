import pandas 


df = pandas.read_csv('seller_info.csv')
df = df[df.ogrn == str(322774600670287)]
print(df)

