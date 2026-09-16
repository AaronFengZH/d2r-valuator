import numpy as np
from PIL import Image
from rapidocr_onnxruntime import RapidOCR

# 初始化本地离线 OCR 模型
engine = RapidOCR()

def preprocess_and_ocr(pil_img: Image.Image):
    # 0. 统一转为 RGB 格式（剥离透明通道，避免通道数报错）
    img_rgb = pil_img.convert('RGB')

    # 1. 2.5 倍超采样放大 (平移 Canvas 2.5x 逻辑)
    w, h = img_rgb.size
    scale = 2.5
    img_scaled = img_rgb.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)

    # 2. 灰度并二值化 (gray > 38 变黑底，其余变白字)
    gray = img_scaled.convert('L')
    table = [0 if i > 38 else 255 for i in range(256)]
    bw_img = gray.point(table, 'L').convert('RGB')  # 转回三通道适配 OCR 输入

    # 3. 转换为 numpy 数组送入 RapidOCR 推理
    img_np = np.array(bw_img)
    result, _ = engine(img_np)

    if not result:
        return []

    # 提取识别出的文本行
    return [line[1].strip() for line in result if line[1].strip()]