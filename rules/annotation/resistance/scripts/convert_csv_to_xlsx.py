import pandas


writer = pandas.ExcelWriter(snakemake.output["xlsx"])
pandas.read_csv(snakemake.input["tsv"], sep=",").to_excel(writer, index=False, sheet_name=snakemake.wildcards["software"]+"_"+snakemake.wildcards["sample"])
writer.save()
