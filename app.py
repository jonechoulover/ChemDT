import os
import sys
import pandas as pd
import numpy as np

from omegaconf import OmegaConf
from rdkit import Chem
from rdkit.ML.Descriptors import MoleculeDescriptors


import mols2grid
import streamlit as st
import streamlit.components.v1 as components
import streamlit as st


root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(root_dir))

from ChemicalNameRecognition.to_db import Csv2DB

cfg = OmegaConf.load(os.path.join(root_dir, "conf.yaml"))

DB_CLIENT = Csv2DB(cfg.db.db_path, cfg.patents.dir, cfg.db.batch_size)

MIN_MOL_WEIGHT = cfg.visualization.min_mol_weight
LIMIT = cfg.visualization.max_molecules

DES_LIST = ['MolWt', 'NumHAcceptors',
            'NumHDonors', 'MolLogP', 'NumRotatableBonds']


def space(num_lines=1):
    """Adds empty lines to the Streamlit app."""
    for _ in range(num_lines):
        st.write("")


@st.cache(allow_output_mutation=True)
def init_dataset(num):
    res = DB_CLIENT.select(num)
    df = pd.DataFrame(data=res, columns=["target", "patent", "page", "iupac", "smiles"])
    df["page"] = df["page"].apply(lambda x: x.split(".")[0])

    return df


def query_dataset(selected):
    query_str = "SELECT * FROM target_mols WHERE target=\'{}\' OR patent_id=\'{}\'  LIMIT {}".format(
        selected, selected, LIMIT)

    # print(query_str)

    res = DB_CLIENT.execute(query_str)
    df = pd.DataFrame(data=res, columns=["target", "patent", "page", "iupac", "smiles"])
    df["page"] = df["page"].apply(lambda x: x.split(".")[0])

    return df


def calc_descriptors(smiles_string, des_list):
    """Given a smiles string (ex. C1CCCCC1), calculate and return the molecular weight"""
    mol = Chem.MolFromSmiles(smiles_string)

    calculator = MoleculeDescriptors.MolecularDescriptorCalculator(des_list)
    res = calculator.CalcDescriptors(mol)

    return [round(_, 3 ) for _ in res]


# style 
st.set_page_config(layout='wide')


# app
st.title('Welcome to ChemDTD!')
st.markdown(
    "ChemDTD is a compound database built on ChemDT framework which can detect IUPAC mentions of chemicals in scanned printed text images and convert them into structures. ChemDT is a deep learning based recognition framework and developed by the algorithm team of [HILAB](http://www.healthinformaticslab.org). If you have any question, please contact [Qiong Zhou](mailto:jonechoulover@gmail.com)")


space(2)

## Search

st.subheader("Search target or patent in database")
selected = st.text_input(label="", value="").strip()

space(2)


## Molecules Tables


# Copy the dataset so any changes are not applied to the original cached version
df = init_dataset(LIMIT)

if selected:
   df = query_dataset(selected)


df[DES_LIST] = np.array([list(_) for _ in df.apply(lambda x: calc_descriptors(
    x["smiles"], DES_LIST), axis=1).values])
df = df.astype({'NumHAcceptors': np.int32, 'NumHDonors': np.int32,
          'NumRotatableBonds': np.int32})
df = df[df["MolWt"] > MIN_MOL_WEIGHT]


if not df.empty:

    col1, col2, col3 = st.columns([2, 1, 5])
    
    weight_cutoff = col1.slider(
        label="Show molecules that weigh below:",
        min_value=100,
        max_value=1000,
        value=300,
        step=10,
    )

    ha_cutoff = col1.slider(
        label="Show number of hydrogen bond acceptors below:",
        min_value=0,
        max_value=10,
        value=5,
        step=1,
    )

    hd_cutoff = col1.slider(
        label="Show number of hydrogen bond donors below:",
        min_value=0,
        max_value=5,
        value=3,
        step=1,
    )

    logp_cutoff = col1.slider(
        label="Show wildman-crippen LogP value below:",
        min_value=-2,
        max_value=5,
        value=2,
        step=1,
    )

    rb_cutoff = col1.slider(
        label="Show number of rotatable bondss below:",
        min_value=0,
        max_value=10,
        value=5,
        step=1,
    )

    df_result = df[(df["MolWt"] < weight_cutoff) & (
        df['NumHAcceptors'] < ha_cutoff) & (df['NumHDonors'] < hd_cutoff) & (df['MolLogP'] < logp_cutoff) & (df['NumRotatableBonds'] < rb_cutoff)]
    col3.dataframe(df_result, width = 800, height = 500)

    space(2)
    
    st.subheader("Structure View")
    
    raw_html = mols2grid.display(
        df_result, smiles_col="SMILES", rename={"smiles": "SMILES"}, template="pages")._repr_html_()


    components.html(raw_html, width=900, height=900, scrolling=True)
