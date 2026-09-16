import customtkinter as ctk
from PIL import Image, ImageGrab
from ocr_engine import preprocess_and_ocr
from rules.ring import evaluate_ring
from rules.amulet import evaluate_amulet

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class D2RValuatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("D2R 装备估价器")
        self.geometry("480x860")
        self.attributes("-topmost", True)

        # 1. 顶部标题与品类指示牌
        self.lbl_title = ctk.CTkLabel(
            self, text="⚔️ D2R 装备估价系统", 
            font=("Microsoft YaHei", 18, "bold"), text_color="#c7b377"
        )
        self.lbl_title.pack(pady=(14, 2))

        self.lbl_status = ctk.CTkLabel(
            self, text="识别品类：等待截图输入...", 
            font=("Microsoft YaHei", 12, "bold"), text_color="#888888"
        )
        self.lbl_status.pack(pady=4)

        # 2. 预览区
        self.preview_label = ctk.CTkLabel(
            self, text="[ 截取装备后直接按 Ctrl + V 粘贴 ]",
            fg_color="#121212", corner_radius=6, height=120
        )
        self.preview_label.pack(fill="x", padx=20, pady=6)

        # 3. 评分看板
        self.card = ctk.CTkFrame(self, fg_color="#161616", border_color="#5a4a2b", border_width=1)
        self.card.pack(fill="x", padx=20, pady=8)

        self.lbl_score = ctk.CTkLabel(
            self.card, text="0.00 / 6.0 点", 
            font=("Microsoft YaHei", 32, "bold"), text_color="#e5c158"
        )
        self.lbl_score.pack(pady=(10, 2))

        self.lbl_tier = ctk.CTkLabel(
            self.card, text="【等待截图输入】", 
            font=("Microsoft YaHei", 14, "bold"), text_color="#888888"
        )
        self.lbl_tier.pack(pady=2)

        self.lbl_rec = ctk.CTkLabel(
            self.card, text="全品类自动分流 · 繁简双模 · 智能熔断", 
            font=("Microsoft YaHei", 11), text_color="#aaaaaa", wraplength=400
        )
        self.lbl_rec.pack(pady=(2, 10))

        # 4. 详细解析文本展示
        self.txt_output = ctk.CTkTextbox(self, height=360, font=("Consolas", 12))
        self.txt_output.pack(fill="both", expand=True, padx=20, pady=(4, 16))
        self.txt_output.insert("0.0", "解析结果将显示在这里...")

        self.bind("<Control-v>", lambda event: self.handle_paste())

    def handle_paste(self):
        img = ImageGrab.grabclipboard()
        if not isinstance(img, Image.Image):
            self.lbl_status.configure(text="⚠️ 剪贴板里没有图片，请先截图！", text_color="#ff4d4f")
            return

        self.lbl_status.configure(text="正在分析词缀并打分...", text_color="#e5c158")
        self.update()

        preview_img = img.copy()
        preview_img.thumbnail((440, 120))
        ctk_img = ctk.CTkImage(light_image=preview_img, dark_image=preview_img, size=preview_img.size)
        self.preview_label.configure(image=ctk_img, text="")

        lines = preprocess_and_ocr(img)
        if not lines:
            self.lbl_status.configure(text="⚠️ 未能识别到文字，请重新截图", text_color="#ff4d4f")
            return

        full_text = " ".join(lines)

        # 优化品类路由逻辑：
        # 1. 优先排除护身符(Charms)
        # 2. 命中 护符 / 项链 / Amulet 均判定为 项链
        if "护身符" not in full_text and any(k in full_text for k in ["护符", "项链", "項鍊", "Amulet"]):
            category_name = "手工/黄金项链 (Amulet)"
            result = evaluate_amulet(lines)
        elif any(k in full_text for k in ["戒指", "Ring"]):
            category_name = "黄金戒指 (Ring)"
            result = evaluate_ring(lines)
        else:
            # 兜底判定
            category_name = "未知品类 (默认戒指模式)"
            result = evaluate_ring(lines)

        self.lbl_status.configure(text=f"识别品类：{category_name}", text_color="#52c41a")

        self.lbl_score.configure(text=f"{result['score']} / 6.0 点")
        self.lbl_tier.configure(text=result['tier'], text_color=result['color'])
        self.lbl_rec.configure(text=result['rec'])

        active_affixes = [f"{k.upper()}: {v}" for k, v in result['data'].items() if v > 0]
        summary_text = "【解析出的有效词缀】:\n" + ("  " + ", ".join(active_affixes) if active_affixes else "  无匹配词缀")
        summary_text += "\n\n" + "="*40 + "\n【OCR 原始识别文本】:\n" + "\n".join(lines)

        self.txt_output.delete("0.0", "end")
        self.txt_output.insert("0.0", summary_text)

if __name__ == "__main__":
    app = D2RValuatorApp()
    app.mainloop()