import os
import sys


from omegaconf import OmegaConf
from pathlib import Path
import sqlite3
from tqdm import tqdm
import pandas as pd
from rdkit import Chem

root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(root_dir))


class Csv2DB():
    def __init__(self, db_path, data_dir, batch_size):
        self.db_path = db_path
        self.dir = Path(data_dir)
        self.batch_size = batch_size

        self.init_db()


    def init_db(self):
        con = sqlite3.connect(self.db_path)
        cursor = con.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS target_mols ( target text, patent_id text, page_id text, iupac text, smiles text );")
        con.close()

    def insert_patent_data(self):
        all_csv = list(self.dir.glob("*.csv"))
        with sqlite3.connect(self.db_path) as con:
            cursor = con.cursor()
            all_tuples = []
            for csv_file in tqdm(all_csv, total=len(all_csv)):
                all_tuples.extend(self.read_csv(csv_file))

            print("total number of tuples: ", len(all_tuples))

            for i in range(0, len(all_tuples), self.batch_size):
                cursor.executemany(
                    "insert into target_mols values (?, ?, ?, ?, ?)", all_tuples[i:i+self.batch_size]
                ) 
                
        
    def read_csv(self, csv_file):
        df = pd.read_csv(csv_file)

        all_tuples = []

        def func(row):
            for iu, s in zip(eval(row["iupac_list"]), eval(row["smiles"])):
                if len(s.strip()) == 0:
                    continue 
                try: 
                    mol = Chem.MolFromSmiles(s.strip())
                    if mol:
                        all_tuples.append((row["target"], row["patent_id"], row["image_path"], iu.strip(), s.strip()))
                except:
                    pass 
        df.apply(func = func, axis = 1)
    
        return all_tuples


    def select(self, num):
        res = []
        
        with sqlite3.connect(self.db_path) as con:
            cursor = con.cursor()
            res = cursor.execute("SELECT * FROM target_mols LIMIT {};".format(num))

        return res

    def count_total_moelcules(self):
        query = "SELECT COUNT(*) FROM target_mols;"
        return self.execute(query).fetchone()[0]

    def execute(self, query):
        with sqlite3.connect(self.db_path) as con:
            cursor = con.cursor()
            res = cursor.execute(
                query)
        return res
        
        
if __name__ == "__main__":
    ## inference
    cfg = OmegaConf.load(os.path.join(root_dir, "conf.yaml"))
    client = Csv2DB(cfg.db.db_path, cfg.patents.dir, cfg.db.batch_size)
    client.insert_patent_data()

    print("total molecules in database: ", client.count_total_moelcules())
    res = client.select(10)

    df = pd.DataFrame(data = res, columns=["target", "patent", "page", "iupac", "smiles"])
    df["page"] = df["page"].apply(lambda x: x.split(".")[0])
    print(df)

    
    

    

        
        