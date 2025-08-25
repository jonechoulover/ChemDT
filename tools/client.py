import os
import sys
import cv2
import json
import base64
import zipfile
import requests
import numpy as np
import ocr_block.tools.infer.utility as utility
__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.append(__dir__)

from typing import List, Dict
from ocr_block.tools.infer.predict_system import main


def im2base64(img_array):
    """ convert image(numpy array) to base64 string
    """
    _, buffer = cv2.imencode('.png', img_array)
    return base64.b64encode(buffer.tobytes()).decode()

def cv2_to_base64(image):
    """ convert image(numpy array) to base64 string
    """
    return base64.b64encode(image).decode('utf8')

class ChemDTClient(object): 
    """ The client of ChemDT service 
    """
    def __init__(self) -> None:

        # make sure the server is running before you run this client
    
        self.headers = {"Content-type": "application/json"}
        self.iupac_api = "http://127.0.0.1:5533/v1/iupac_det"
        self.iupac_fixer_api = "http://127.0.0.1:5533/iupac_fixer"
        self.iupac_ner_api = "http://127.0.0.1:5533/iupac_ner"
        self.pdf_api = "http://127.0.0.1:3114/process/images2"

    def iupac_det(self, img_path:str):
        """
        img_path: the path of image
        """
        with requests.Session() as s:
            r = s.post(self.iupac_api,
                    files={
                        'file_upload': open(img_path, 'rb')
                    },
                    json={
                        "ocr_type": "paddle"
                    }).json()
        return r

    def iupac_ner(self, iupac_text:str):
        """
        iupac_text: the text of OCR result. This function will be called after iupac_ocr
        """
        with requests.Session() as s:
            r = s.post(self.iupac_ner_api,
                    json={
                        "iupac_text": iupac_text
                    }).json()
        return r

    def iupac_fixer(self, iupac_text:str):
        """
        iupac_text: the text of NER result. This function will be called after iupac_ner
        """
        with requests.Session() as s:
            r = s.post(self.iupac_fixer_api,
                    json={
                        "iupac_text": iupac_text
                    }).json()
        return r
    
    def conver_outcomt(self, ocr_result):
        content = ocr_result[0].split("\t")[1]
        content = json.loads(content)
        return content
        
    def iupac_ocr(self, image_path:str):
        """
        image_path: the path of image which need to be ocr 
        """
        args = utility.parse_args()
        args.image_dir = image_path
        ocr_result = main(args)
        res = self.conver_outcomt(ocr_result)
        boxs, rec_res = [], []
        for _ in res:
            boxs.append(np.array(_["points"]))
            text = _["transcription"]
            conf = "None"
            rec_res.append((text, conf))
        return boxs, rec_res
    
    def pdf2img(self, pdf_path:str, save_dir:str):
        """
        pdf_path: the path of pdf file
        save_dir: the path of save dir
        """
        name = os.path.basename(pdf_path).split(".")[0]
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        zip_dir = os.path.join(save_dir,"zip_"+name)
        if not os.path.exists(zip_dir):
            os.makedirs(zip_dir)
        img_dir = os.path.join(save_dir,"img_"+name)
        if not os.path.exists(img_dir):
            os.makedirs(img_dir)
        
        with requests.Session() as s:
            res = s.post(self.pdf_api, files={"file": open(pdf_path, "rb")})

        with open(os.path.join(zip_dir,name+".zip"), "wb") as f:
            f.write(res.content)
        with zipfile.ZipFile(os.path.join(zip_dir,name+".zip")) as zf:
            zf.extractall(img_dir)
        pages = [os.path.join(img_dir,name,page) for page in os.listdir(os.path.join(img_dir,os.listdir(img_dir)[0]))]
        pages.sort(key=lambda x : int(os.path.basename(x).split("_")[-1].split(".")[0]))
        return pages
    
    def rectange_box(self, boxs:List, img_path:str):
        img = cv2.imread(img_path)
        for box in boxs:
            box = box.tolist()
            xmin = box[0][0]
            ymin = box[0][1]
            xmax = box[2][0]
            ymax = box[2][1]
            cv2.rectangle(img,(xmin,ymin),(xmax,ymax),(0,255,0),5)
        return img

    def run_pipline(self, pdf_path, save_dir = '../pdf_images'):
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        pages = self.pdf2img(pdf_path, save_dir)
    
        for origin_img_path in pages:
            #iupac detection
            iupac_det_res = self.iupac_det(origin_img_path)["iupac_result"]
            if len(iupac_det_res) > 0:
                for iupac_det in iupac_det_res:
                    #iupac ocr
                    save_png_path = '../inference_results/1.png'
                    save_png_np = np.array(json.loads(iupac_det["iupac_image"]))
                    cv2.imwrite(save_png_path, save_png_np)
                    ocr_box,ocr_res = self.iupac_ocr(save_png_path)
                    
                    if len(ocr_res) > 0:
                        conc_ocr_text = ""
                        for ocr_text,ocr_conf in ocr_res:
                            conc_ocr_text += ocr_text

                        print(conc_ocr_text,'*'*80)
                        #iupac ner
                        iupac_ners = self.iupac_ner(conc_ocr_text)["inpac_ner"]
                        print("iupac_ners is {}".format(iupac_ners))
                            
                        #iupac fixer
                        if len(iupac_ners) > 0:
                            for iupac_ner in iupac_ners:
                                iupac_fixer_res = self.iupac_fixer(iupac_ner)["checked_iupac"]
                                print("iupac fixer is {}".format(iupac_fixer_res))
                    os.remove(save_png_path)
        
        


if __name__ == '__main__':
    client = ChemDTClient()
    pdf_path = '../test_data/p2.pdf'
    save_dir = '../pdf_images'
    client.run_pipline(pdf_path, save_dir = save_dir)
    
    