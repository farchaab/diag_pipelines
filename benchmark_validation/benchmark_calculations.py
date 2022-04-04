# -*- coding: UTF-8 -*-
"""
Author : benchmark_calculations <petros.liakopoulos@chuv.ch>
Date   : 2022-03-28
Purpose: benchmark new predictions to ref data
"""

import argparse
import pandas as pd
import os
from typing import NamedTuple
import pdfkit
from string import Template





class Args(NamedTuple):
    """ Command-line arguments """
    pipeline_TSV: str
    out: str

# --------------------------------------------------
def get_args() -> Args:
    """ Get command-line arguments """

    parser = argparse.ArgumentParser(
        description='Compare tsv of new pipeline to reference data and older pipeline',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('pipeline_tsv',
                        metavar='tsv file',
                        help='The output TSV file of the reference pipeline')

    # parser.add_argument('-p',
    #                     '--pre',
    #                     metavar='tsv file',
    #                     type=str,
    #                     help='The output TSV file of previous pipeline to compare to',
    #                     default='diag_pipelines_2.6.0/combined_detail_NR_2.6.tsv')

    parser.add_argument('-o',
                        '--out',
                        metavar='dir',
                        help="output directory",
                        type=str,
                        default='')



    args = parser.parse_args()

    if not os.path.isfile(args.pipeline_tsv):
        parser.error("File does not exist")

    if args.out != "":
        if not os.path.exists(args.out):
            parser.error("Output path does not exist")





    return Args(args.pipeline_tsv, args.out)

def main() -> None:
    """ Make a jazz noise here """
    args = get_args()
    ref_table = "reference_table.tsv"
    diag_2_6 = phenotype_microarray_spec_sens(ref_table, "diag_pipelines_2.6.0/combined_detail_NR_2.6.tsv")
    diag_2_7 = phenotype_microarray_spec_sens(ref_table, "diag_pipelines_2.7.0/combined_detail_NR_2.7.tsv")
    new_pipeline = phenotype_microarray_spec_sens(ref_table, args.pipeline_TSV)

    Template_string = """<!DOCTYPE html>
    <html>
    <head>
    <style>
    table, th, td {
      border: 1px solid black;
    }

    table {
      width: 100%;
    }
    </style>
    </head>
    <body>
    <h1><strong>Pipeline benchmark report</strong></h1>
       <br></br>
       <br>This report was generated by the 'benchmark_calculations.py' script.
       <br>A summary table of the raw data is available under the name 'reference_table.tsv'
       <br>For further information on the data and how percentages were calculated, take a look at the README file
       <br>The sensitivity and specificity were calculated using the data from the following paper: 
       <br>https://www.sciencedirect.com/science/article/pii/S1198743X15600660?via%3Dihub
       </p>
       <br></br>
    <h2>Phenotype(MIC) Sensitivity and Specificity</h2>

    <table>
      <tr>
        <th>Diag Pipelines 2.6.0</th>
        <th>Diag Pipelines 2.7.0</th>
        <th>New Pipeline</th>
      </tr>
      <tr>
        <td>Sensitivity: $sens1 %</td>
        <td>Sensitivity: $sens2 %</td>
        <td>Sensitivity: $sens3 %</td>
      </tr>
      <tr>
        <td>Specificity: $spec1 %</td>
        <td>Specificity: $spec2 %</td>
        <td>Specificity: $spec3 %</td>
      </tr>
    </table>

    <h2>Microarray Sensitivity</h2>

    <table>
      <tr>
        <th>Diag Pipelines 2.6.0</th>
        <th>Diag Pipelines 2.7.0</th>
        <th>New Pipeline</th>
      </tr>
      <tr>
        <td>Sensitivity: $sensma1 %</td>
        <td>Sensitivity: $sensma2 %</td>
        <td>Sensitivity: $sensma3 %</td>
      </tr>
    </table>
    
    
    </body>
    </html>
     """

    HTML_TEMPLATE1 = """
    <html>
    <head>
    <style>
      h2 {
        text-align: center;
        font-family: Helvetica, Arial, sans-serif;
      }
      table { 
        margin-left: auto;
        margin-right: auto;
      }
      table, th, td {
        border: 1px solid black;
        border-collapse: collapse;
      }
      th, td {
        padding: 5px;
        text-align: center;
        font-family: Helvetica, Arial, sans-serif;
        font-size: 90%;
      }
      table tbody tr:hover {
        background-color: #dddddd;
      }
      .wide {
        width: 90%; 
      }
    </style>
    </head>
    <body>
    """

    HTML_TEMPLATE2 = """
    </body>
    </html>
    """

    formatted_html = Template(Template_string).substitute(sens1=diag_2_6[0], sens2 = diag_2_7[0], sens3 = new_pipeline[0], spec1= diag_2_6[1], spec2=diag_2_7[1],
                                                          spec3 = new_pipeline[1], sensma1 = diag_2_6[2], sensma2 = diag_2_7[2], sensma3 = new_pipeline[2])

    pdfkit.from_string(formatted_html, output_path="pipeline_benchmark_summary.pdf")


    table = create_sum_table("diag_pipelines_2.6.0/combined_detail_NR_2.6.tsv", args.pipeline_TSV)



    to_html_pretty(table, HTML_TEMPLATE1, HTML_TEMPLATE2, "pipeline_comparison.html", 'Gene prediction differences in pipelines report')




# --------------------------------------------------

def phenotype_microarray_spec_sens(ref, table) -> tuple:
    """compare table to reference"""
    carbapenem_genes = ("OXA", "VIM", "NDM", "CTX", "SHV", "KPC", "ACT", "ADC", "CMH", "VEB", "PAL")
    df = pd.read_csv(table, sep='\t', header=0) #read tsv with pipeline predictions
    ref = pd.read_csv(ref, sep='\t', header=0) #read reference table with microarray and phenotype data
    samples = tuple(ref["Strain_ID"])
    pheno_tp, pheno_fp, pheno_fn, pheno_tn= 0, 0, 0, 0
    micro_tp= 0

    for sample in samples:
        phenotype = ref[ref['Strain_ID'] == sample].iloc[0,12]
        microarray = ref[ref['Strain_ID'] == sample].iloc[0,3].split(", ")
        subset_df = df[df["Sample"] == sample]
        carba_genes_found = 0
        #check carbapenemase genes detected
        for gene in carbapenem_genes:
            if any(gene in pred for pred in list(subset_df["Best_hit"])):
                carba_genes_found += 1
        if carba_genes_found != 0 and phenotype == "POS":
            pheno_tp += 1
        elif carba_genes_found == 0 and phenotype == "NEG":
            pheno_tn += 1
        elif carba_genes_found != 0 and phenotype == "NEG":
            pheno_fp += 1
        else:
            pheno_fn += 1
        #check if all gene fams detected by micrarray are present
        for gene_fam in microarray:
            if any(gene_fam in pred for pred in list(subset_df["Best_hit"])):
                micro_tp += 1

    return (round((pheno_tp/(pheno_tp+pheno_fn))*100), round((pheno_tn/(pheno_tn+pheno_fp))*100), round((micro_tp/33)*100))

# --------------------------------------------------

def create_sum_table(table1 , table2):
    """creates the main summary table"""
    df1 = pd.read_csv(table1, sep='\t', header=0) #read the two csv tables
    df2 = pd.read_csv(table2, sep='\t', header=0)
    sample_names = sorted([x for x in list(set(list(df1.iloc[:, 0])))]) #extract sample names and rank by alphabetical order
    preds_ref, preds_new = [], [] #lists for storing the differences in predictions for the two pipelines
    for sample in sample_names:
        subset_df1 = df1.loc[df1["Sample"] == sample]#subsetting the two df by the name of the sample
        subset_df2 = df2.loc[df2["Sample"] == sample]
        predicted_in_ref = list(set(list(subset_df1["Best_hit"])) - set(list(subset_df2["Best_hit"])))#extracting what genes were predicted in ref pipeline vs new
        predicted_in_new = list(set(list(subset_df2["Best_hit"])) - set(list(subset_df1["Best_hit"])))#extracting what genes were predicted in new pipeline vs ref
        lst_pred_ref, lst_pred_new, formated_preds_ref, formated_preds_new= [], [], [], []

        if predicted_in_ref != []:
            for pred in predicted_in_ref: #for each predicted gene, go back to the subsetted df and extract perc id and coverage
                lst_pred_ref.append([pred, subset_df1[subset_df1['Best_hit'] == pred].iloc[0,15], subset_df1[subset_df1['Best_hit'] == pred].iloc[0,16], subset_df1[subset_df1['Best_hit'] == pred].iloc[0,9]])
            for listit in lst_pred_ref: #format each list with gene name, perc id and coverage into one string
                formated_preds_ref.append(f"{listit[0]} (id: {listit[1]}, cov: {listit[2]}, depth: {listit[3]})")
        else:
            formated_preds_ref.append("-")

        if predicted_in_new != []:
            for pred2 in predicted_in_new:#same as above for new pipeline
                lst_pred_new.append([pred2, subset_df2[subset_df2['Best_hit'] == pred2].iloc[0,15], subset_df2[subset_df2['Best_hit'] == pred2].iloc[0,16], subset_df2[subset_df2['Best_hit'] == pred2].iloc[0,9]])
            for listit in lst_pred_new:
                formated_preds_new.append(f"{listit[0]} (id: {listit[1]}, cov: {listit[2]}, depth: {listit[3]})")
        else:
            formated_preds_new.append("-")


        preds_ref.append(formated_preds_ref)
        preds_new.append(formated_preds_new)


    col2 = []
    col3 = []
    for i in range(0, len(sample_names)):
        if preds_ref[i] == preds_new[i]: #if both predictions are the same add check marks
            col2.append("✓")
            col3.append("✓")
        else:
            col2.append(preds_ref[i])
            col3.append(preds_new[i])
    summary_table = pd.DataFrame(
        {"Sample Name": sample_names,
         "Prediction in reference pipeline": col2,
         "Prediction in updated pipeline": col3
         })
    summary_table["Prediction in reference pipeline"] = summary_table["Prediction in reference pipeline"].apply(lambda x: ', '.join(map(str, x))) #format lists within columns
    summary_table["Prediction in updated pipeline"] = summary_table["Prediction in updated pipeline"].apply(lambda x: ', '.join(map(str, x)))

    return summary_table

def to_html_pretty(df, templ1, templ2, filename, title=''):
    '''
    Write an entire dataframe to an HTML file
    with nice formatting.
    Thanks to @stackoverflowuser2010 for the
    pretty printer see https://stackoverflow.com/a/47723330/362951
    '''
    ht = ''
    if title != '':
        ht += '<h2> %s </h2>\n' % title
    ht += df.to_html()

    with open(filename, 'w') as f:
         f.write(templ1 + ht + templ2)


# --------------------------------------------------
if __name__ == '__main__':
    main()