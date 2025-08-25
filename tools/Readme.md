# CNR_tools

## 环境安装

```python
#创建独立环境
conda create -n cnr python=3.8
pip install requests
pip install opencv-python -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install pdf2image -i https://pypi.tuna.tsinghua.edu.cn/simple
conda install poppler
python -m pip install matplotlib -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install zipfile37 -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install -r tools/ocr_block/newrequirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 接口

### Iupac_ocr

```python
# box返回的内容为文字框
# txt返回的是所有文字拼接在一起的结果
client = ChemDTClient()
box,txt = client.iupac_ocr("图片地址")
```

### Pdf2img

```python
# pages返回的是转换成功的图片的路径
# 图片存储路径无需提前创建，会自动创建
client = ChemDTClient()
pages = client.pdf2img("pdf路径"，"图片存储路径")
```

### Iupac fixer

```python
# 返回的是一个字典，包含修正过的iupac以及对应的smile
# 如果没有修正成功，smile为空字符
client = ChemDTClient()
client.iupac_fixer("iupac文字")
```

### Rectange_box

```python
#boxs: iupac_ocr 返回的boxs
import matplotlib.pyplot as plt
img = client.rectange_box(boxs,"图片地址")
plt.imshow(img)
plt.show()
```