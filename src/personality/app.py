
import pandas as pd
import time
import re
from google import genai
import sys
import os
from google.genai import types

sys.stdout.reconfigure(encoding='utf-8')

#Khởi tạo client 
client = genai.Client(api_key="AIzaSyCy1sWo_5_wUDV2tdKWz9jC4GZ2u_B2Fok") 

def analyze_bigfive_01(review_text):
    review_text = str(review_text).strip()
    if not review_text or review_text == 'nan':
        return [0.5]*5

    prompt = f"""
Đóng vai chuyên gia tâm lý, phân tích chỉ số Big Five (OCEAN) qua văn bản.
Thang điểm: 0.00 (Thấp) - 1.00 (Cao). 0.50 là trung lập.

Quy tắc chấm nhanh:
- O (Cởi mở): Khen thiết kế lạ/mùi mới/thú vị (>0.70); Chỉ nói về công dụng (0.50); Ngại thay đổi (<0.30).
- C (Tận tâm): Soi kỹ thành phần/đóng gói/giao hàng (>0.70); Cẩu thả/sao cũng được (<0.30).
- E (Hướng ngoại): Dùng nhiều từ cảm thán/vui vẻ/hào hứng (>0.70); Ngắn gọn/trầm lắng (<0.40).
- A (Dễ chịu): Khen shop/vị tha cho lỗi nhỏ (>0.80); Chửi bới/gắt gỏng/cạnh tranh (<0.20).
- N (Nhạy cảm): Lo lắng hàng giả/than phiền căng thẳng (>0.70); Điềm tĩnh/ổn định (<0.30).

Yêu cầu: Chỉ xuất duy nhất 5 số thực (O,C,E,A,N), cách nhau bởi dấu phẩy, làm tròn 2 chữ số thập phân. Không giải thích.
Chiến lược: Ưu tiên các giá trị thể hiện rõ tính cách (0.10-0.30 hoặc 0.70-0.90), hạn chế tối đa số 0.50.

Ví dụ: "Mùi nhẹ, thành phần thú vị, thích thử đồ mới": 0.84, 0.66, 0.53, 0.72, 0.37

Review: "{review_text}"
Kết quả:
 """

    
    for attempt in range(5):
        try:
            response = client.models.generate_content(
                model="gemini-flash-latest",
                contents=prompt,
                config=types.GenerateContentConfig(
                    safety_settings=[
                        types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                        types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                        types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                        types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
                    ],
                    temperature=0.1 # Giữ số ổn định
                )
            )

            raw = response.text.strip()
            print(f"AI phản hồi: {raw}")
            numbers = re.findall(r'\d*\.?\d+', raw)
            numbers = [float(x) for x in numbers if x != ""]

            if len(numbers) >= 5:
                # Chỉ lấy 5 số đầu và kẹp trong khoảng 0-1
                final_nums = [min(max(x, 0.0), 1.0) for x in numbers[:5]]
                return final_nums
            
            return [0.5]*5

        except Exception as e:
            if "429" in str(e):
                print(f"Hết hạn mức (429), đang nghỉ 60 giây rồi thử lại lần {attempt+1}...")
                time.sleep(30) # Nghỉ lâu hơn nếu bị lỗi Quota
            else:
                print(f"Lỗi khác: {e}")
                break 
    return [0.5]*5

# ================== MAIN ==================
BATCH_SIZE = 5
input_file = "D:/KLTN1/KLTN/data/data_review_273.csv"
output_file = "D:/KLTN1/KLTN/data/data_review_273_with_bigfive.csv"

try:
    df = pd.read_csv(input_file)
    df = df.dropna(subset=['text']).reset_index(drop=True)

    #Xác định đã xử lý tới đâu
    if os.path.exists(output_file):
        df_done = pd.read_csv(output_file)
        start_index = len(df_done)
        print(f"Resume từ dòng: {start_index}")
    else:
        start_index = 0
        # tạo file mới với header
        df.head(0).assign(O="", C="", E="", A="", N="") \
          .to_csv(output_file, index=False, encoding='utf-8-sig')
        print("Tạo file mới") 

    # Chạy từ vị trí chưa làm
    for start in range(start_index, len(df), BATCH_SIZE):
        end = start + BATCH_SIZE
        batch = df.iloc[start:end]

        print(f"\nBatch {start} → {end}")

        scores_list = []

        for idx, row in batch.iterrows():
            text = row.get('text', "")
            print(f"   → Dòng {idx}")

            try:
                scores = analyze_bigfive_01(text)
            except Exception as e:
                print(f" Lỗi: {e}")
                scores = ["", "", "", "", ""]

            scores_list.append(scores)
            time.sleep(5)

        df_scores = pd.DataFrame(scores_list, columns=['O','C','E','A','N'])
        batch = batch.reset_index(drop=True)
        df_scores = df_scores.reset_index(drop=True)

        df_out = pd.concat([batch, df_scores], axis=1)

        # append tiếp
        df_out.to_csv(output_file, mode='a', header=False, index=False, encoding='utf-8-sig')

        print(f"Đã lưu batch {start} → {end}")

    print("\nHoàn thành!")

except FileNotFoundError:
    print("❌ Không tìm thấy file data.csv")