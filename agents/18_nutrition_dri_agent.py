"""
Nutrition DRI Agent (Agent 18)
File: agents/18_nutrition_dri_agent.py
Purpose: Taiwan HPA Dietary Reference Intakes data management and query
Commands: 查詢營養素標準 / 營養素運作原理 / 列出營養素 / 下載營養素標準
"""

import os
import json
import re
import requests
import urllib3
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(dotenv_path=r"C:\Users\user\claude AI_Agent\.env")

BASE_DIR = Path(r"C:\Users\user\claude AI_Agent")
DRI_DATA_PATH = BASE_DIR / "output" / "csv_data" / "nutrition_dri.json"
PDF_DIR = BASE_DIR / "output" / "nutrition_pdfs"

# 三餐攝取比例（早餐/午餐/晚餐）
MEAL_RATIO = {"早餐": 0.30, "午餐": 0.40, "晚餐": 0.30}

# Taiwan DRI 8th Edition (2022) built-in baseline
# Source: 衛生福利部國人膳食營養素參考攝取量第八版(2022)
# https://www.hpa.gov.tw/Pages/Detail.aspx?nodeid=4248&pid=12285
_BUILTIN_DRI = {
    "_meta": {
        "source": "衛生福利部國人膳食營養素參考攝取量第八版(2022)",
        "url": "https://www.hpa.gov.tw/Pages/Detail.aspx?nodeid=4248&pid=12285",
        "updated": "2022",
        "local_refresh": None,
    },
    "nutrients": {
        "熱量": {
            "unit": "kcal/天",
            "description": "維持身體基本功能與日常活動的能量來源",
            "mechanism": "由碳水化合物(4kcal/g)、蛋白質(4kcal/g)及脂肪(9kcal/g)提供，透過細胞有氧呼吸轉換為ATP，驅動所有生命活動。",
            "deficiency_warnings": [
                "長期疲勞、體力不支，難以完成日常活動",
                "體重持續下降，肌肉流失（身體分解肌肉供能）",
                "注意力不集中、情緒低落",
                "免疫力下降，易反覆生病",
                "女性月經不規則或停經（身體節能保護機制）",
                "兒童生長發育遲緩",
            ],
        },
        "蛋白質": {
            "unit": "公克/天",
            "description": "構成肌肉、器官、酵素、抗體等的基本建材，也參與荷爾蒙合成",
            "mechanism": "由20種胺基酸組成，透過核糖體合成各類蛋白質；參與細胞修復與再生、免疫抗體生成、酵素催化，也可在能量不足時分解供能。",
            "deficiency_warnings": [
                "肌肉萎縮、體力下降，握力明顯減弱",
                "水腫（尤其腹部、腳踝，因白蛋白不足）",
                "傷口癒合緩慢，術後復原延遲",
                "免疫力下降，感染頻率及嚴重度增加",
                "頭髮變細、大量脫落，指甲易斷裂",
                "皮膚乾燥、粗糙，失去彈性",
            ],
        },
        "鈣": {
            "unit": "毫克/天",
            "description": "骨骼和牙齒的主要礦物成分，也參與肌肉收縮、神經傳導及凝血",
            "mechanism": "99%儲存於骨骼和牙齒（磷灰石形式），1%在血液和細胞中；透過鈣通道調節肌肉收縮（含心肌），協助神經訊號傳遞，活化凝血因子。",
            "deficiency_warnings": [
                "骨質疏鬆症：骨密度下降，骨折風險增加（尤其脊椎、髖部）",
                "肌肉痙攣、腳抽筋（尤其夜間）",
                "手腳麻木、面部刺痛感（低血鈣症狀）",
                "牙齒鬆動、蛀牙頻繁",
                "心跳不規律（嚴重低血鈣危及生命）",
                "兒童佝僂病：骨骼彎曲、身高不足",
            ],
        },
        "鐵": {
            "unit": "毫克/天",
            "description": "血紅素和肌紅素的核心成分，負責攜帶和儲存氧氣",
            "mechanism": "以亞鐵離子形式構成血紅素，將肺部氧氣輸送至全身細胞；肌紅素儲存肌肉中的氧；也參與電子傳遞鏈（細胞色素）產生ATP。",
            "deficiency_warnings": [
                "缺鐵性貧血：面色蒼白、眼瞼結膜色淡",
                "持續疲勞、頭暈、活動後氣喘",
                "心跳加速（心臟代償性加速泵血）",
                "手腳冰冷（末梢血液循環差）",
                "指甲扁平或匙狀甲（指甲中間凹陷）",
                "注意力難以集中，嬰幼兒認知與運動發育受損",
                "免疫功能降低，易反覆感染",
            ],
        },
        "維生素A": {
            "unit": "微克視網醇當量/天",
            "description": "維持視力（尤其夜間）、皮膚及黏膜健康，調節免疫功能",
            "mechanism": "視網醛構成視紫質（感光蛋白），維持暗視力；視黃酸調控上皮細胞分化，維持皮膚和黏膜屏障；增強NK細胞和T細胞免疫反應。",
            "deficiency_warnings": [
                "夜盲症：在昏暗環境中看不清楚",
                "眼睛乾燥、眼白出現畢托斑（結膜角質化）",
                "嚴重缺乏導致角膜軟化、失明（全球兒童失明主因之一）",
                "皮膚乾燥、粗糙，毛囊性角化（毛孔呈雞皮疙瘩狀）",
                "黏膜防禦力下降，呼吸道及消化道感染增加",
                "兒童生長遲緩、骨骼發育不良",
            ],
        },
        "維生素D": {
            "unit": "微克/天",
            "description": "促進鈣磷吸收，維持骨骼健康，調節免疫和細胞增殖",
            "mechanism": "皮膚在紫外線下合成維生素D3，經肝腎活化為骨化三醇（1,25-(OH)₂D₃），促進腸道鈣磷吸收；調節超過200個基因的表現，包括免疫調節基因。",
            "deficiency_warnings": [
                "兒童佝僂病：骨骼軟化彎曲、前額突出",
                "成人骨軟化症：骨骼疼痛（腰背、骨盆、腿部）",
                "骨質疏鬆，骨折風險上升",
                "肌肉無力、容易跌倒（老年人特別需注意）",
                "免疫力下降，自體免疫疾病風險增加",
                "憂鬱傾向、季節性情緒障礙",
                "睡眠品質差，疲勞感增加",
            ],
        },
        "維生素C": {
            "unit": "毫克/天",
            "description": "強力水溶性抗氧化劑，膠原蛋白合成必需，促進免疫功能",
            "mechanism": "作為輔因子參與脯胺酸/賴胺酸羥化反應（膠原蛋白合成）；清除自由基（抗氧化）；促進非血基質鐵（植物性鐵）吸收；參與兒茶酚胺和L-肉鹼合成。",
            "deficiency_warnings": [
                "壞血病（嚴重缺乏）：牙齦出血、牙齒鬆動脫落",
                "皮下出血點、瘀青（毛細血管脆弱）",
                "傷口癒合延遲，舊傷疤重新裂開",
                "關節疼痛、腫脹",
                "持續疲勞、倦怠感",
                "免疫力下降，感冒頻率增加",
                "皮膚粗糙乾燥，容易出現細紋",
            ],
        },
        "維生素B1": {
            "unit": "毫克/天",
            "description": "碳水化合物代謝的關鍵輔酶，維持神經和心肌功能",
            "mechanism": "以TPP（焦磷酸硫胺素）形式作為丙酮酸脫羧酶和α-酮戊二酸脫氫酶輔酶，參與葡萄糖有氧氧化；維持神經細胞膜的離子通道功能。",
            "deficiency_warnings": [
                "濕性腳氣病：下肢水腫、心跳加速、呼吸困難（心臟衰竭）",
                "乾性腳氣病：下肢麻木、肌肉無力、步態不穩",
                "韋尼克腦病變（酗酒者）：眼球運動異常、共濟失調、意識混亂",
                "食慾不振、噁心、消化不良",
                "注意力不集中、記憶力下降",
                "精緻碳水化合物攝取多者（白米、甜食）特別需補充",
            ],
        },
        "維生素B2": {
            "unit": "毫克/天",
            "description": "能量代謝輔酶，維持皮膚、眼睛和黏膜健康",
            "mechanism": "構成FAD和FMN輔因子，參與線粒體電子傳遞鏈（複合物I和II）；協助穀胱甘肽還原酶再生抗氧化劑；參與維生素B6和菸鹼素代謝。",
            "deficiency_warnings": [
                "口角炎：嘴角龜裂、破潰、疼痛",
                "舌頭發紅腫痛（草莓舌/地圖舌）",
                "脂溢性皮膚炎（鼻翼、眼瞼旁油脂堆積）",
                "眼睛畏光、充血、視力模糊",
                "喉嚨腫痛",
                "疲勞感、生產力下降",
            ],
        },
        "菸鹼素": {
            "unit": "毫克菸鹼素當量/天",
            "description": "能量代謝和DNA修復的核心輔酶，超過400種酵素需要它",
            "mechanism": "構成NAD⁺和NADP⁺，是細胞氧化還原反應的電子載體；NAD⁺也是Sir蛋白（抗老化蛋白）和PARP（DNA修復酶）的底物，調節基因穩定性。",
            "deficiency_warnings": [
                "糙皮病「3D症候群」：皮膚炎(Dermatitis)、腹瀉(Diarrhea)、失智(Dementia)",
                "光敏性皮膚炎：日曬後皮膚發紅、起水泡，對稱分布於手背和頸部",
                "腹痛、腹瀉、噁心",
                "頭痛、焦慮、憂鬱、幻覺（嚴重時）",
                "口腔潰瘍、舌頭發炎",
                "以玉米為主食的族群特別需注意",
            ],
        },
        "維生素B6": {
            "unit": "毫克/天",
            "description": "胺基酸代謝核心輔酶，參與神經傳導物質和血紅素合成",
            "mechanism": "以磷酸吡哆醛(PLP)形式參與超過100種酵素反應：轉胺反應（胺基酸互轉）、去羧反應（合成血清素、多巴胺、GABA、組胺）、血紅素前驅物合成。",
            "deficiency_warnings": [
                "皮膚炎、口腔潰瘍",
                "周圍神經炎：手腳麻木、刺痛、燒灼感",
                "微細胞性貧血（血紅素合成受阻）",
                "情緒波動、焦慮、睡眠障礙（血清素不足）",
                "免疫功能下降",
                "嬰兒痙攣發作（嚴重缺乏）",
                "長期服用異煙肼（抗結核藥）者特別需補充",
            ],
        },
        "葉酸": {
            "unit": "微克/天",
            "description": "DNA和RNA合成的必需輔酶，細胞分裂不可或缺，預防神經管缺陷",
            "mechanism": "作為一碳基團轉移輔酶（THFA形式），參與嘌呤和嘧啶核苷酸合成；甲基化同半胱胺酸為甲硫胺酸；維持DNA甲基化模式（表觀遺傳調控）。",
            "deficiency_warnings": [
                "巨球性貧血：紅血球體積增大、數量減少，疲勞、頭暈、心悸",
                "孕早期缺乏→胎兒神經管缺陷（脊柱裂、無腦兒）",
                "口腔潰瘍、舌頭發炎",
                "同半胱胺酸升高（動脈粥狀硬化和心血管疾病風險增加）",
                "情緒憂鬱、記憶力下降",
                "孕婦、計畫懷孕者和老年人最需注意",
            ],
        },
        "維生素B12": {
            "unit": "微克/天",
            "description": "維護髓鞘（神經絕緣層），協助葉酸循環和DNA合成",
            "mechanism": "作為甲硫胺酸合成酶輔酶（同半胱胺酸→甲硫胺酸），再生活性葉酸；作為甲基丙二醯輔酶A變位酶輔酶，代謝奇數鏈脂肪酸；維護神經髓鞘結構。",
            "deficiency_warnings": [
                "巨球性貧血（與葉酸缺乏症狀相似但機制不同）",
                "亞急性脊髓聯合變性：手腳麻木→步態不穩→下肢癱瘓（不可逆）",
                "記憶力衰退、失智風險增加（尤其老年人）",
                "情緒憂鬱",
                "同半胱胺酸升高（心血管風險）",
                "純素食者、老年人（胃壁細胞退化）、長期服Metformin者特別需注意",
            ],
        },
        "鎂": {
            "unit": "毫克/天",
            "description": "300多種酵素反應的輔因子，維持肌肉、神經和骨骼健康",
            "mechanism": "ATP必須與鎂結合才能被細胞利用（Mg-ATP複合物）；參與DNA/RNA合成、蛋白質合成；調節鈣離子通道（肌肉放鬆）；影響NMDA受體（神經調節）；維持骨骼礦化。",
            "deficiency_warnings": [
                "肌肉痙攣、抽筋（尤其夜間腳抽筋）",
                "焦慮、易怒、無法放鬆",
                "睡眠障礙、難以入睡",
                "心律不整（心悸）",
                "骨質疏鬆（與鈣磷代謝相關）",
                "血糖調節異常，胰島素阻抗增加（2型糖尿病風險）",
                "偏頭痛、頭痛",
                "慢性疲勞感",
            ],
        },
        "鋅": {
            "unit": "毫克/天",
            "description": "免疫功能、傷口癒合、味覺嗅覺維持，超過300種酵素的組成成分",
            "mechanism": "作為超氧化物歧化酶（抗氧化）、胸腺素（免疫調節）、DNA聚合酶等酵素的結構或催化成分；參與T細胞增殖、NK細胞活化；調節睪酮等荷爾蒙分泌。",
            "deficiency_warnings": [
                "免疫力下降，易反覆感染（尤其呼吸道和消化道）",
                "傷口癒合遲緩",
                "味覺減退（食之無味）、嗅覺下降",
                "皮膚炎、痤瘡加重",
                "落髮、毛髮稀疏",
                "男性：精子數量減少，生殖功能障礙",
                "兒童：生長遲緩、身材矮小",
                "夜視力下降（鋅協助視黃醇結合蛋白運輸維生素A）",
            ],
        },
        "膳食纖維": {
            "unit": "公克/天",
            "description": "促進腸道健康、調控血糖和血脂，餵養腸道益生菌",
            "mechanism": "可溶性纖維（果膠、β-葡聚醣）：降低膽固醇、延緩糖分吸收；不可溶性纖維（纖維素、木質素）：增加糞便體積、促進蠕動；發酵後產生短鏈脂肪酸（滋養腸道細胞）。",
            "deficiency_warnings": [
                "便秘、排便不規律",
                "大腸癌風險增加（糞便在腸道停留時間過長）",
                "血糖波動大、飯後血糖飆升",
                "總膽固醇和LDL（壞膽固醇）升高",
                "腸道菌相失衡，影響免疫功能和情緒（腸腦軸）",
                "體重管理困難（飽腹感下降）",
            ],
        },
        "水": {
            "unit": "毫升/天",
            "description": "生命最基本的物質，所有生化反應的媒介，體溫調節的核心",
            "mechanism": "作為所有生化反應的溶劑；透過汗液蒸發調節體溫；潤滑關節（滑液成分）；攜帶廢物經腎臟排出；維持細胞體積和滲透壓平衡。",
            "deficiency_warnings": [
                "輕度脫水（體重1-2%）：口渴、尿液深黃、輕微頭痛、疲勞",
                "中度脫水（3-5%）：注意力和運動表現明顯下降、皮膚彈性差、頭暈",
                "重度脫水（>6%）：心跳加速、血壓下降、意識混亂（危及生命）",
                "慢性輕度脫水：腎結石風險增加、慢性便秘",
                "皮膚加速老化、皺紋加深",
                "口臭（唾液分泌減少）",
            ],
        },
    },
    "age_groups": {
        "1-3歲": {
            "M": {"熱量": 1150, "蛋白質": 20, "鈣": 500, "鐵": 10, "維生素A": 400, "維生素D": 10, "維生素C": 40, "維生素B1": 0.6, "維生素B2": 0.7, "菸鹼素": 9, "維生素B6": 0.5, "葉酸": 170, "維生素B12": 0.9, "鎂": 80, "鋅": 5, "膳食纖維": 15, "水": 1000},
            "F": {"熱量": 1050, "蛋白質": 20, "鈣": 500, "鐵": 10, "維生素A": 400, "維生素D": 10, "維生素C": 40, "維生素B1": 0.6, "維生素B2": 0.7, "菸鹼素": 9, "維生素B6": 0.5, "葉酸": 170, "維生素B12": 0.9, "鎂": 80, "鋅": 5, "膳食纖維": 15, "水": 1000},
        },
        "4-6歲": {
            "M": {"熱量": 1550, "蛋白質": 30, "鈣": 600, "鐵": 10, "維生素A": 400, "維生素D": 10, "維生素C": 50, "維生素B1": 0.8, "維生素B2": 0.9, "菸鹼素": 11, "維生素B6": 0.6, "葉酸": 200, "維生素B12": 1.2, "鎂": 120, "鋅": 6, "膳食纖維": 18, "水": 1300},
            "F": {"熱量": 1400, "蛋白質": 30, "鈣": 600, "鐵": 10, "維生素A": 400, "維生素D": 10, "維生素C": 50, "維生素B1": 0.8, "維生素B2": 0.9, "菸鹼素": 11, "維生素B6": 0.6, "葉酸": 200, "維生素B12": 1.2, "鎂": 120, "鋅": 6, "膳食纖維": 18, "水": 1300},
        },
        "7-9歲": {
            "M": {"熱量": 1800, "蛋白質": 40, "鈣": 800, "鐵": 10, "維生素A": 500, "維生素D": 10, "維生素C": 60, "維生素B1": 1.0, "維生素B2": 1.1, "菸鹼素": 14, "維生素B6": 0.8, "葉酸": 250, "維生素B12": 1.8, "鎂": 170, "鋅": 8, "膳食纖維": 22, "水": 1600},
            "F": {"熱量": 1650, "蛋白質": 40, "鈣": 800, "鐵": 10, "維生素A": 500, "維生素D": 10, "維生素C": 60, "維生素B1": 0.9, "維生素B2": 1.0, "菸鹼素": 13, "維生素B6": 0.8, "葉酸": 250, "維生素B12": 1.8, "鎂": 160, "鋅": 7, "膳食纖維": 22, "水": 1600},
        },
        "10-12歲": {
            "M": {"熱量": 2050, "蛋白質": 50, "鈣": 1000, "鐵": 15, "維生素A": 600, "維生素D": 10, "維生素C": 80, "維生素B1": 1.1, "維生素B2": 1.3, "菸鹼素": 15, "維生素B6": 1.1, "葉酸": 300, "維生素B12": 2.0, "鎂": 230, "鋅": 10, "膳食纖維": 25, "水": 1800},
            "F": {"熱量": 1950, "蛋白質": 50, "鈣": 1000, "鐵": 15, "維生素A": 600, "維生素D": 10, "維生素C": 80, "維生素B1": 1.0, "維生素B2": 1.2, "菸鹼素": 14, "維生素B6": 1.1, "葉酸": 300, "維生素B12": 2.0, "鎂": 220, "鋅": 9, "膳食纖維": 25, "水": 1800},
        },
        "13-15歲": {
            "M": {"熱量": 2400, "蛋白質": 60, "鈣": 1200, "鐵": 15, "維生素A": 700, "維生素D": 10, "維生素C": 90, "維生素B1": 1.3, "維生素B2": 1.5, "菸鹼素": 18, "維生素B6": 1.3, "葉酸": 400, "維生素B12": 2.4, "鎂": 320, "鋅": 13, "膳食纖維": 28, "水": 2100},
            "F": {"熱量": 2050, "蛋白質": 55, "鈣": 1200, "鐵": 15, "維生素A": 700, "維生素D": 10, "維生素C": 90, "維生素B1": 1.1, "維生素B2": 1.3, "菸鹼素": 15, "維生素B6": 1.3, "葉酸": 400, "維生素B12": 2.4, "鎂": 300, "鋅": 11, "膳食纖維": 28, "水": 2000},
        },
        "16-18歲": {
            "M": {"熱量": 2500, "蛋白質": 70, "鈣": 1200, "鐵": 15, "維生素A": 700, "維生素D": 10, "維生素C": 100, "維生素B1": 1.4, "維生素B2": 1.6, "菸鹼素": 19, "維生素B6": 1.5, "葉酸": 400, "維生素B12": 2.4, "鎂": 380, "鋅": 14, "膳食纖維": 30, "水": 2200},
            "F": {"熱量": 2050, "蛋白質": 60, "鈣": 1200, "鐵": 15, "維生素A": 700, "維生素D": 10, "維生素C": 100, "維生素B1": 1.1, "維生素B2": 1.3, "菸鹼素": 15, "維生素B6": 1.3, "葉酸": 400, "維生素B12": 2.4, "鎂": 330, "鋅": 12, "膳食纖維": 27, "水": 2000},
        },
        "19-30歲": {
            "M": {"熱量": 2400, "蛋白質": 60, "鈣": 1000, "鐵": 10, "維生素A": 600, "維生素D": 10, "維生素C": 100, "維生素B1": 1.2, "維生素B2": 1.3, "菸鹼素": 16, "維生素B6": 1.5, "葉酸": 400, "維生素B12": 2.4, "鎂": 380, "鋅": 12, "膳食纖維": 30, "水": 2400},
            "F": {"熱量": 2000, "蛋白質": 50, "鈣": 1000, "鐵": 15, "維生素A": 500, "維生素D": 10, "維生素C": 100, "維生素B1": 0.9, "維生素B2": 1.0, "菸鹼素": 14, "維生素B6": 1.5, "葉酸": 400, "維生素B12": 2.4, "鎂": 320, "鋅": 12, "膳食纖維": 25, "水": 2000},
        },
        "31-50歲": {
            "M": {"熱量": 2400, "蛋白質": 60, "鈣": 1000, "鐵": 10, "維生素A": 600, "維生素D": 10, "維生素C": 100, "維生素B1": 1.2, "維生素B2": 1.3, "菸鹼素": 16, "維生素B6": 1.5, "葉酸": 400, "維生素B12": 2.4, "鎂": 380, "鋅": 12, "膳食纖維": 30, "水": 2400},
            "F": {"熱量": 1900, "蛋白質": 50, "鈣": 1000, "鐵": 15, "維生素A": 500, "維生素D": 10, "維生素C": 100, "維生素B1": 0.9, "維生素B2": 1.0, "菸鹼素": 14, "維生素B6": 1.5, "葉酸": 400, "維生素B12": 2.4, "鎂": 320, "鋅": 12, "膳食纖維": 25, "水": 2000},
        },
        "51-70歲": {
            "M": {"熱量": 2150, "蛋白質": 60, "鈣": 1000, "鐵": 10, "維生素A": 600, "維生素D": 15, "維生素C": 100, "維生素B1": 1.2, "維生素B2": 1.3, "菸鹼素": 16, "維生素B6": 1.6, "葉酸": 400, "維生素B12": 2.4, "鎂": 360, "鋅": 12, "膳食纖維": 27, "水": 2300},
            "F": {"熱量": 1800, "蛋白質": 50, "鈣": 1000, "鐵": 10, "維生素A": 500, "維生素D": 15, "維生素C": 100, "維生素B1": 0.9, "維生素B2": 1.0, "菸鹼素": 14, "維生素B6": 1.6, "葉酸": 400, "維生素B12": 2.4, "鎂": 310, "鋅": 12, "膳食纖維": 22, "水": 1900},
        },
        "71歲以上": {
            "M": {"熱量": 1950, "蛋白質": 60, "鈣": 1000, "鐵": 10, "維生素A": 600, "維生素D": 15, "維生素C": 100, "維生素B1": 1.2, "維生素B2": 1.3, "菸鹼素": 16, "維生素B6": 1.6, "葉酸": 400, "維生素B12": 2.4, "鎂": 350, "鋅": 12, "膳食纖維": 25, "水": 2300},
            "F": {"熱量": 1650, "蛋白質": 50, "鈣": 1000, "鐵": 10, "維生素A": 500, "維生素D": 15, "維生素C": 100, "維生素B1": 0.9, "維生素B2": 1.0, "菸鹼素": 14, "維生素B6": 1.6, "葉酸": 400, "維生素B12": 2.4, "鎂": 300, "鋅": 12, "膳食纖維": 20, "水": 1800},
        },
        "孕婦（第三孕期）": {
            "F": {"熱量": 2300, "蛋白質": 70, "鈣": 1000, "鐵": 45, "維生素A": 700, "維生素D": 10, "維生素C": 110, "維生素B1": 1.1, "維生素B2": 1.2, "菸鹼素": 16, "維生素B6": 1.9, "葉酸": 600, "維生素B12": 2.6, "鎂": 360, "鋅": 15, "膳食纖維": 28, "水": 2300},
        },
        "哺乳婦": {
            "F": {"熱量": 2600, "蛋白質": 65, "鈣": 1000, "鐵": 45, "維生素A": 1000, "維生素D": 10, "維生素C": 145, "維生素B1": 1.3, "維生素B2": 1.4, "菸鹼素": 17, "維生素B6": 2.0, "葉酸": 500, "維生素B12": 2.8, "鎂": 350, "鋅": 17, "膳食纖維": 28, "水": 2700},
        },
    },
}


class NutritionDRIAgent:
    def __init__(self):
        DRI_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        PDF_DIR.mkdir(parents=True, exist_ok=True)
        self._data = self._load_data()

    # ── Data management ─────────────────────────────────────────────────

    def _load_data(self) -> dict:
        if DRI_DATA_PATH.exists():
            try:
                with open(DRI_DATA_PATH, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return _BUILTIN_DRI

    def _save_data(self):
        with open(DRI_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    # ── Age group matching ───────────────────────────────────────────────

    def _match_age_group(self, age: int, gender: str) -> tuple[str, dict]:
        """Return (age_group_key, nutrient_dict) for given age and gender."""
        groups = self._data.get("age_groups", {})
        gender_key = "M" if gender.upper() in ("M", "男", "男性") else "F"

        boundaries = [
            (3, "1-3歲"), (6, "4-6歲"), (9, "7-9歲"), (12, "10-12歲"),
            (15, "13-15歲"), (18, "16-18歲"), (30, "19-30歲"),
            (50, "31-50歲"), (70, "51-70歲"), (999, "71歲以上"),
        ]
        matched_group = "19-30歲"
        for upper, label in boundaries:
            if age <= upper:
                matched_group = label
                break

        group_data = groups.get(matched_group, {})
        nutrients = group_data.get(gender_key, group_data.get("M", group_data.get("F", {})))
        return matched_group, nutrients

    # ── Public query methods ─────────────────────────────────────────────

    def get_dri(self, gender: str, age: int) -> dict:
        """Return full DRI dict for given gender/age."""
        _, nutrients = self._match_age_group(age, gender)
        return nutrients

    def get_meal_dri(self, gender: str, age: int, meal: str) -> dict:
        """Return per-meal DRI based on MEAL_RATIO distribution."""
        nutrients = self.get_dri(gender, age)
        ratio = MEAL_RATIO.get(meal, 1.0 / 3)
        return {k: round(v * ratio, 1) for k, v in nutrients.items()}

    def get_nutrient_info(self, nutrient_name: str) -> dict | None:
        """Return mechanism/warnings for a nutrient (fuzzy match)."""
        nutrients = self._data.get("nutrients", {})
        # Exact match first
        if nutrient_name in nutrients:
            return nutrients[nutrient_name]
        # Partial match
        for key, val in nutrients.items():
            if nutrient_name in key or key in nutrient_name:
                return {**val, "_matched_name": key}
        return None

    def list_nutrients(self) -> list[str]:
        return list(self._data.get("nutrients", {}).keys())

    # ── HPA download (optional refresh) ─────────────────────────────────

    def download_hpa_data(self) -> str:
        """Try to download PDF list from HPA page and save locally."""
        try:
            hpa_url = "https://www.hpa.gov.tw/Pages/Detail.aspx?nodeid=4248&pid=12285"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            try:
                resp = requests.get(hpa_url, headers=headers, timeout=20)
                resp.raise_for_status()
                verify = True
            except requests.exceptions.SSLError:
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                resp = requests.get(hpa_url, headers=headers, timeout=20, verify=False)
                resp.raise_for_status()
                verify = False

            # Find PDF links. HPA currently uses GetFile.ashx URLs where the PDF
            # filename appears in the anchor text/title instead of the href itself.
            pdf_links = re.findall(r'href="([^"]+\.pdf)"', resp.text, re.IGNORECASE)
            pdf_links += re.findall(r"href='([^']+\.pdf)'", resp.text, re.IGNORECASE)
            pdf_links += re.findall(
                r'<a[^>]+href="([^"]*GetFile\.ashx[^"]*)"[^>]*>[^<]*\.pdf',
                resp.text,
                re.IGNORECASE,
            )
            pdf_links += re.findall(
                r"<a[^>]+href='([^']*GetFile\.ashx[^']*)'[^>]*>[^<]*\.pdf",
                resp.text,
                re.IGNORECASE,
            )
            pdf_links = list(dict.fromkeys(pdf_links))

            if not pdf_links:
                return "⚠️ 未找到 PDF 連結，HPA 頁面結構可能已變更。\n目前使用內建第八版(2022)資料。"

            base_url = "https://www.hpa.gov.tw"
            saved = []
            for link in pdf_links:
                full_url = link if link.startswith("http") else base_url + link
                filename = Path(link).name or f"dri_{len(saved)+1}.pdf"
                if not filename.lower().endswith(".pdf"):
                    filename = f"dri_{len(saved)+1}.pdf"
                dest = PDF_DIR / filename
                if not dest.exists():
                    pdf_resp = requests.get(full_url, headers=headers, timeout=30, verify=verify)
                    if pdf_resp.status_code == 200:
                        dest.write_bytes(pdf_resp.content)
                        saved.append(filename)

            self._data["_meta"]["local_refresh"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            self._save_data()

            if saved:
                return f"✅ 已下載 {len(saved)} 個 PDF 至 {PDF_DIR}\n{chr(10).join(saved)}\n\n注意：PDF 內容需手動或 AI 解析後更新。"
            else:
                return "ℹ️ PDF 已是最新版本，無需重新下載。"

        except Exception as e:
            return f"⚠️ 下載失敗：{e}\n目前使用內建第八版(2022)資料。"

    # ── Command handler ──────────────────────────────────────────────────

    def handle_command(self, cmd: str) -> str:
        cmd = cmd.strip()

        if cmd in ("下載營養素標準", "更新營養素標準"):
            return self.download_hpa_data()

        if cmd in ("列出營養素", "所有營養素"):
            names = self.list_nutrients()
            return "📋 支援查詢的營養素：\n" + "、".join(names)

        if cmd.startswith("營養素運作原理"):
            name = cmd.replace("營養素運作原理", "").strip()
            if not name:
                return "請指定營養素名稱，例如：\n小幫手 營養素運作原理 鈣"
            info = self.get_nutrient_info(name)
            if not info:
                return f"⚠️ 找不到「{name}」的資料。\n可用：" + "、".join(self.list_nutrients())
            matched = info.get("_matched_name", name)
            lines = [
                f"🔬 {matched} 的運作原理",
                f"說明：{info.get('description', '')}",
                "",
                f"機制：{info.get('mechanism', '')}",
            ]
            warnings = info.get("deficiency_warnings", [])
            if warnings:
                lines += ["", "⚠️ 長期缺乏警訊："]
                for w in warnings:
                    lines.append(f"  • {w}")
            return "\n".join(lines)

        if cmd.startswith("查詢營養素標準"):
            rest = cmd.replace("查詢營養素標準", "").strip()
            gender, age, meal = self._parse_profile(rest)
            if age is None:
                return (
                    "請提供性別和年齡，例如：\n"
                    "小幫手 查詢營養素標準 男 30\n"
                    "小幫手 查詢營養素標準 女 25 午餐"
                )
            group, nutrients = self._match_age_group(age, gender)
            gender_label = "男" if gender.upper() == "M" else "女"

            if meal and meal in MEAL_RATIO:
                ratio = MEAL_RATIO[meal]
                lines = [
                    f"🥗 {gender_label}性 {age} 歲 {meal} 攝取參考量",
                    f"（全日 × {int(ratio*100)}%，依據 {group} 組）",
                    "─────────────────────",
                ]
                for n, v in nutrients.items():
                    unit = self._data.get("nutrients", {}).get(n, {}).get("unit", "")
                    lines.append(f"  {n}：{round(v * ratio, 1)} {unit}")
            else:
                lines = [
                    f"📊 {gender_label}性 {age} 歲 每日參考攝取量",
                    f"（年齡組別：{group}）",
                    f"資料來源：{self._data.get('_meta', {}).get('source', '')}",
                    "─────────────────────",
                ]
                for n, v in nutrients.items():
                    unit = self._data.get("nutrients", {}).get(n, {}).get("unit", "")
                    lines.append(f"  {n}：{v} {unit}")

            return "\n".join(lines)

        return ""

    def _parse_profile(self, text: str):
        """Parse '男 30 午餐' → ('M', 30, '午餐')"""
        gender = None
        age = None
        meal = None

        parts = text.split()
        for p in parts:
            if p in ("男", "男性", "M", "m"):
                gender = "M"
            elif p in ("女", "女性", "F", "f"):
                gender = "F"
            elif re.match(r"^\d{1,3}$", p):
                age = int(p)
            elif p in MEAL_RATIO:
                meal = p

        if gender is None:
            gender = "M"
        return gender, age, meal


if __name__ == "__main__":
    agent = NutritionDRIAgent()
    print(agent.handle_command("查詢營養素標準 女 30 午餐"))
    print()
    print(agent.handle_command("營養素運作原理 鈣"))
    print()
    print(agent.handle_command("列出營養素"))
