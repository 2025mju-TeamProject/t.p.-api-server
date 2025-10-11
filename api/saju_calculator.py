import datetime

# 10천간(天干)과 12지지(地支) 정의
GAN = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
JI = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]


def calculate_saju(year, month, day, hour):
    """
    사용자의 생년월일시 정보를 받아 사주팔자(네 기둥)를 계산하고,
    그 결과를 딕셔너리 형태로 반환합니다.

    NOTE: 월주와 년주는 절기를 기준으로 해야 정확하지만,
          이 코드는 학습 목적으로 근사치를 사용하여 계산합니다.
    """

    # 1. 일주(日柱) 계산 (사주팔자의 기준점)
    # 1900년 1월 31일이 경자(庚子)일인 것을 기준으로 총 일수를 계산하여 60으로 나눈 나머지로 계산
    try:
        start_date = datetime.date(1900, 1, 31)
        target_date = datetime.date(year, month, day)
        # 1900년 1월 31일의 간지 인덱스는 경(6), 자(0)
        total_days = (target_date - start_date).days

        day_gan_idx = (6 + total_days) % 10
        day_ji_idx = (0 + total_days) % 12
        day_pillar_str = GAN[day_gan_idx] + JI[day_ji_idx]
    except ValueError:
        return {"error": "유효하지 않은 날짜입니다."}

    # 2. 년주(年柱) 계산
    # 절기 '입춘'(보통 2월 4일)을 기준으로 한 해가 바뀌므로, 그 이전은 전년도로 계산
    saju_year = year if (month, day) >= (2, 4) else year - 1

    # 1864년(갑자년)을 기준으로 계산 (주기: 60년)
    year_offset = saju_year - 1864
    year_gan_idx = year_offset % 10
    year_ji_idx = year_offset % 12
    year_pillar_str = GAN[year_gan_idx] + JI[year_ji_idx]

    # 3. 월주(月柱) 계산
    # 각 월은 절기를 기준으로 시작됨 (여기서는 양력 월을 그대로 사용)
    # 월지(月支)는 인(寅)월부터 시작하며 고정되어 있음 (인묘진사오미신유술해자축)
    month_ji_map = {
        1: "축", 2: "인", 3: "묘", 4: "진", 5: "사", 6: "오",
        7: "미", 8: "신", 9: "유", 10: "술", 11: "해", 12: "자"
    }
    month_ji_str = month_ji_map.get(month, "알수없음")  # 월별 지지

    # 월간(月干)은 년간(年干)에 따라 결정됨 (갑기년->병인월, 을경년->무인월...)
    year_gan_str = GAN[year_gan_idx]
    month_gan_start_map = {"갑기": "병", "을경": "무", "병신": "경", "정임": "임", "무계": "갑"}

    month_gan_start_char = ""
    for key, start_gan in month_gan_start_map.items():
        if year_gan_str in key:
            month_gan_start_char = start_gan
            break

    # 인월(寅月)의 천간부터 순서대로 계산
    month_gan_start_idx = GAN.index(month_gan_start_char)
    month_ji_start_idx = JI.index("인")
    current_month_ji_idx = JI.index(month_ji_str)

    month_gan_idx = (month_gan_start_idx + (current_month_ji_idx - month_ji_start_idx + 12) % 12) % 10
    month_pillar_str = GAN[month_gan_idx] + month_ji_str

    # 4. 시주(時柱) 계산
    # 시간대별 지지(地支)는 고정됨
    hour_ji_map = {
        (23, 0): "자", (1, 2): "축", (3, 4): "인", (5, 6): "묘",
        (7, 8): "진", (9, 10): "사", (11, 12): "오", (13, 14): "미",
        (15, 16): "신", (17, 18): "유", (19, 20): "술", (21, 22): "해"
    }

    hour_ji_str = ""
    for time_range, ji in hour_ji_map.items():
        # 23시는 자시이므로 특별 처리
        if hour == 23:
            hour_ji_str = "자"
            break
        if time_range[0] <= hour <= time_range[1]:
            hour_ji_str = ji
            break

    # 시간의 천간(干)은 일간(日干)에 따라 결정됨 (갑기일->갑자시, 을경일->병자시...)
    day_gan_str = GAN[day_gan_idx]
    hour_gan_start_map = {"갑기": "갑", "을경": "병", "병신": "무", "정임": "경", "무계": "임"}

    hour_gan_start_char = ""
    for key, start_gan in hour_gan_start_map.items():
        if day_gan_str in key:
            hour_gan_start_char = start_gan
            break

    hour_gan_start_idx = GAN.index(hour_gan_start_char)
    hour_ji_start_idx = JI.index("자")  # 자시부터 시작
    current_hour_ji_idx = JI.index(hour_ji_str)

    hour_gan_idx = (hour_gan_start_idx + (current_hour_ji_idx - hour_ji_start_idx + 12) % 12) % 10
    hour_pillar_str = GAN[hour_gan_idx] + hour_ji_str

    # 계산된 결과를 딕셔너리 형태로 최종 반환
    result = {
        "year_pillar": year_pillar_str,
        "month_pillar": month_pillar_str,
        "day_pillar": day_pillar_str,
        "hour_pillar": hour_pillar_str,
        "details": {
            "year": {"gan": GAN[year_gan_idx], "ji": JI[year_ji_idx]},
            "month": {"gan": GAN[month_gan_idx], "ji": month_ji_str},
            "day": {"gan": GAN[day_gan_idx], "ji": JI[day_ji_idx]},
            "hour": {"gan": GAN[hour_gan_idx], "ji": hour_ji_str},
        }
    }
    return result


# --- 이 파일 자체를 테스트하기 위한 실행 코드 ---
if __name__ == '__main__':
    # 예시: 1995년 3월 15일 오전 9시 30분에 태어난 사람
    saju_result = calculate_saju(1995, 3, 15, 9)

    # 결과가 잘 나오는지 확인하기 위해 print
    import json

    print(json.dumps(saju_result, indent=4, ensure_ascii=False))