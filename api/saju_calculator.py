# api/saju_calculator.py

import datetime

GAN = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
JI = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]

def calculate_saju(year, month, day, hour, minute):
    """
    사용자의 생년월일, 시, 분 정보를 포함하여 사주팔자를 계산하고,
    그 결과를 딕셔너리 형태로 반환합니다.
    """
    try:
        target_date = datetime.date(year, month, day)
    except ValueError:
        return {"error": "유효하지 않은 날짜입니다."}

    # --- 일주(日柱) 계산 ---
    start_date = datetime.date(1900, 1, 31)
    total_days = (target_date - start_date).days
    day_gan_idx = (6 + total_days) % 10
    day_ji_idx = (0 + total_days) % 12
    day_pillar_str = GAN[day_gan_idx] + JI[day_ji_idx]

    # --- 년주(年柱) 계산 ---
    saju_year = year if (month, day) >= (2, 4) else year - 1
    year_offset = saju_year - 1864
    year_gan_idx = year_offset % 10
    year_ji_idx = year_offset % 12
    year_pillar_str = GAN[year_gan_idx] + JI[year_ji_idx]

    # --- 월주(月柱) 계산 ---
    month_ji_map = {1: "축", 2: "인", 3: "묘", 4: "진", 5: "사", 6: "오", 7: "미", 8: "신", 9: "유", 10: "술", 11: "해", 12: "자"}
    month_ji_str = month_ji_map.get(month)
    year_gan_str = GAN[year_gan_idx]
    month_gan_start_map = {"갑기": "병", "을경": "무", "병신": "경", "정임": "임", "무계": "갑"}
    month_gan_start_char = ""
    for key, start_gan in month_gan_start_map.items():
        if year_gan_str in key: month_gan_start_char = start_gan
    month_gan_start_idx = GAN.index(month_gan_start_char)
    month_gan_idx = (month_gan_start_idx + (JI.index(month_ji_str) - JI.index("인") + 12) % 12) % 10
    month_pillar_str = GAN[month_gan_idx] + month_ji_str

    # --- 시주(時柱) 계산 (minute 활용) ---
    day_gan_for_hour_calc = GAN[day_gan_idx]
    if hour == 23 and minute >= 30:
        next_day_total_days = total_days + 1
        next_day_gan_idx = (6 + next_day_total_days) % 10
        day_gan_for_hour_calc = GAN[next_day_gan_idx]

    hour_ji_map = {
        (23, 0): "자", (1, 2): "축", (3, 4): "인", (5, 6): "묘", (7, 8): "진", (9, 10): "사",
        (11, 12): "오", (13, 14): "미", (15, 16): "신", (17, 18): "유", (19, 20): "술", (21, 22): "해"
    }
    hour_ji_str = ""
    for time_range, ji in hour_ji_map.items():
        if hour == 23 or hour == 0: hour_ji_str = "자"; break
        if time_range[0] <= hour <= time_range[1]: hour_ji_str = ji; break

    hour_gan_start_map = {"갑기": "갑", "을경": "병", "병신": "무", "정임": "경", "무계": "임"}
    hour_gan_start_char = ""
    for key, start_gan in hour_gan_start_map.items():
        if day_gan_for_hour_calc in key:
            hour_gan_start_char = start_gan
            break
    hour_gan_start_idx = GAN.index(hour_gan_start_char)
    hour_gan_idx = (hour_gan_start_idx + JI.index(hour_ji_str)) % 10
    hour_pillar_str = GAN[hour_gan_idx] + hour_ji_str

    # --- 최종 결과 반환 ---
    result = {
        "year_pillar": year_pillar_str, "month_pillar": month_pillar_str,
        "day_pillar": day_pillar_str, "hour_pillar": hour_pillar_str,
        "details": {
            "year": {"gan": GAN[year_gan_idx], "ji": JI[year_ji_idx]},
            "month": {"gan": GAN[month_gan_idx], "ji": month_ji_str},
            "day": {"gan": GAN[day_gan_idx], "ji": JI[day_ji_idx]},
            "hour": {"gan": GAN[hour_gan_idx], "ji": hour_ji_str},
        }
    }
    return result