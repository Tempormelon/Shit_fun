import pandas as pd
import numpy as np
import re
import os


def clean_data():
    print("🧹 正在清洗数据（严格模式：区分空值与0）...")

    # 1. 读取 CSV
    try:
        # keep_default_na=False 可能会把 'NA' 读成字符串，建议还是用默认，手动判断
        df = pd.read_csv("sheet1.csv", header=None, encoding='gbk', nrows=18)
    except UnicodeDecodeError:
        df = pd.read_csv("sheet1.csv", header=None, encoding='gb18030', nrows=18)
    except FileNotFoundError:
        print("❌ 错误：找不到 sheet1.csv 文件！")
        return

    # 2. 提取日期行
    raw_dates = df.iloc[1, 1:].values
    MEMBERS = ["甲鱼", "气温", "牛子", "一哥", "毛毛", "老司", "JK"]
    cleaned_rows = []

    # 3. 扫描表格
    for idx, name in df.iloc[:, 0].items():
        clean_name = str(name).strip()

        if clean_name in MEMBERS:
            print(f"  -> 处理: {clean_name}")

            count_row = df.iloc[idx, 1:].values
            try:
                comment_row = df.iloc[idx + 1, 1:].values
            except IndexError:
                comment_row = [np.nan] * len(count_row)

            # 4. 遍历日期
            for i, date_val in enumerate(raw_dates):
                # 如果表头日期本身就是空的，直接跳过
                if pd.isna(date_val) or str(date_val).strip() == "":
                    continue

                # --- 日期格式化 (保持不变) ---
                raw_date_str = str(date_val).strip()
                if "月" in raw_date_str and "日" in raw_date_str:
                    match = re.findall(r'\d+', raw_date_str)
                    if len(match) >= 2:
                        month = int(match[0])
                        day = int(match[1])
                        year = 2025 if month >= 10 else 2026
                        final_date = f"{year}-{month:02d}-{day:02d}"
                    else:
                        final_date = raw_date_str
                else:
                    final_date = raw_date_str.split(" ")[0]

                # =========================================
                # 🔥 核心逻辑修改：严格区分 空值 和 0
                # =========================================

                # 获取原始单元格的值
                if i < len(count_row):
                    raw_val = count_row[i]
                else:
                    raw_val = np.nan

                # 1. 判定是否为“空” (没参加)
                # pd.isna 处理 NaN, None; strip() 处理纯空格字符串
                if pd.isna(raw_val) or str(raw_val).strip() == "":
                    continue  # 直接跳过循环，不录入这条数据！

                # 2. 既然不为空，那就处理数值 (包括 0)
                try:
                    # 尝试转为数字
                    final_count = int(float(raw_val))
                except (ValueError, TypeError):
                    # 如果填的是文字（比如“请假”），也跳过
                    continue

                # =========================================

                # 获取备注
                final_comment = ""
                if i < len(comment_row):
                    c_val = comment_row[i]
                    if pd.notna(c_val):
                        c_str = str(c_val).strip()
                        if c_str.lower() != "nan" and c_str != "":
                            final_comment = c_str

                # 只要走到了这里，说明 raw_val 不是空的，是数字(包含0)
                # 所以直接存！
                cleaned_rows.append({
                    "日期": final_date,
                    "姓名": clean_name,
                    "次数": final_count,
                    "备注": final_comment
                })

    # 5. 保存
    if cleaned_rows:
        new_df = pd.DataFrame(cleaned_rows)
        new_df['日期'] = pd.to_datetime(new_df['日期'])
        new_df = new_df.sort_values(by=["日期", "姓名"], ascending=[False, True])

        new_df.to_csv("shit_database.csv", index=False, encoding='utf-8-sig')
        print(f"✅ 清洗完成！保留了 {len(new_df)} 条有效数据。")
        print("   (规则：单元格为空则跳过，单元格为0则保留)")
    else:
        print("❌ 警告：没有提取到数据。")


if __name__ == "__main__":
    if os.path.exists("shit_database.csv"):
        try:
            os.remove("shit_database.csv")
        except:
            pass
    clean_data()