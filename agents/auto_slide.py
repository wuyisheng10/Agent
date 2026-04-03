import google.generativeai as genai
import os
import sys
import re
from pptx import Presentation
from pathlib import Path
from dotenv import load_dotenv

# 載入環境變數
load_dotenv(dotenv_path=r"C:\Users\user\claude AI_Agent\.env")

# 1. 設定你的 API Key
# 優先讀取環境變數，若無則可在此填入預設值
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    # 如果使用者沒有設定環境變數，這裡可以填入預設 key (但不建議)
    # api_key = "你的_API_KEY"
    print("錯誤: 未設定 GOOGLE_API_KEY 或 GEMINI_API_KEY 環境變數。")
    sys.exit(1)

genai.configure(api_key=api_key)

def process_media_to_slides(file_path):
    file_path = Path(file_path)
    if not file_path.exists():
        print(f"錯誤: 找不到檔案 {file_path}")
        return

    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # 2. 上傳影片/錄音
    print(f"正在分析檔案: {file_path}...")
    try:
        media_file = genai.upload_file(path=str(file_path))
        # 註：GenAI 可能需要一點時間處理上傳後的檔案，但在 flash 模式下通常很快
    except Exception as e:
        print(f"上傳失敗: {e}")
        return
    
    # 3. 讓 Gemini 生成投影片內容
    prompt = """
    請分析這段影片/錄音，並將重點整理成 5 頁投影片。
    每頁請提供：標題(Title) 和 3 個內文要點(Bullet Points)。
    請直接以繁體中文回答。
    輸出的格式請嚴格遵守：
    第 X 頁：[標題]
    - 要點 1
    - 要點 2
    - 要點 3
    """
    
    try:
        response = model.generate_content([prompt, media_file])
        content = response.text
    except Exception as e:
        print(f"生成內容失敗: {e}")
        return
    
    # 4. 建立實體投影片檔案
    prs = Presentation()
    
    # 解析邏輯：按「第 X 頁」拆分
    pages = re.split(r"第\s*[0-9一二三四五六七八九十]+\s*頁[:：]", content)
    
    slide_count = 0
    for page in pages:
        page = page.strip()
        if not page:
            continue
            
        lines = [line.strip() for line in page.split('\n') if line.strip()]
        if not lines:
            continue
            
        # 第一行通常是標題
        title_text = lines[0].replace("[", "").replace("]", "")
        bullet_points = [l for l in lines[1:] if l.startswith('-') or l.startswith('•') or re.match(r'^\d+\.', l)]
        
        # 如果沒抓到 bullet points，就用剩餘的所有行
        if not bullet_points and len(lines) > 1:
            bullet_points = lines[1:]

        slide = prs.slides.add_slide(prs.slide_layouts[1]) # 使用「標題與內容」版面
        slide.shapes.title.text = title_text
        
        # 填入內文
        if slide.placeholders[1].has_text_frame:
            tf = slide.placeholders[1].text_frame
            tf.clear() # 清除預設文字
            for bp in bullet_points:
                p = tf.add_paragraph()
                p.text = bp.lstrip('- •').strip()
                p.level = 0
        
        slide_count += 1

    # 如果解析失敗，至少產生一個包含完整內容的投影片
    if slide_count == 0:
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        slide.shapes.title.text = "重點摘要"
        slide.placeholders[1].text = content

    # 5. 存檔到相同資料夾
    output_name = file_path.with_name(file_path.stem + "_重點簡報.pptx")
    try:
        prs.save(str(output_name))
        print(f"完成！投影片已存至: {output_name}")
    except Exception as e:
        print(f"存檔失敗: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        process_media_to_slides(sys.argv[1])
    else:
        print("請提供檔案路徑作為參數。")
