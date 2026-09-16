import re

def evaluate_ring(lines: list[str]) -> dict:
    data = {
        'fcr': 0, 'str': 0, 'dex': 0, 'life': 0, 'mana': 0,
        'all_res': 0, 'lr': 0, 'fr': 0, 'cr': 0, 'pr': 0,
        'ar': 0, 'll': 0, 'lm': 0
    }

    def get_nums(text):
        return [int(n) for n in re.findall(r'\d+', text)]

    # 逐行状态机数值提取与误判熔断
    for line in lines:
        if re.search(r'需要等級|需要等级|level|lvl', line, re.I):
            continue
        nums = get_nums(line)
        if not nums:
            continue

        # 1. 快速施法 FCR
        if re.search(r'FCR|快速施法|施法速度|更快速施法', line, re.I):
            data['fcr'] = nums[0]
            continue

        # 2. 法力相关 (根据数值范围智能分流)
        if re.search(r'法力|Mana|LM|IM|1M|LN', line, re.I):
            for n in nums:
                if 15 <= n <= 90:
                    data['mana'] = n
                elif 1 <= n <= 6:
                    data['lm'] = n
            continue

        # 3. 生命相关 (根据数值范围智能分流)
        if re.search(r'生命|Life|LL|IL|11|LI', line, re.I):
            for n in nums:
                if 10 <= n <= 40:
                    data['life'] = n
                elif 1 <= n <= 8:
                    data['ll'] = n
            continue

        # 4. 力量
        if re.search(r'STR', line, re.I) or (re.search(r'力量', line) and not re.search(r'法力', line)):
            data['str'] = nums[0]
            continue

        # 5. 敏捷
        if re.search(r'DEX|敏捷|敏', line, re.I):
            data['dex'] = nums[0]
            continue

        # 6. 准确率 / 命中
        if re.search(r'AR|準確|准确|命中', line, re.I):
            data['ar'] = nums[0]
            continue

        # 7. 全抗
        if re.search(r'All Res|所有抗性|全抗', line, re.I):
            data['all_res'] = nums[0]
            continue

        # 8. 单抗
        if re.search(r'LR|閃電|闪电|抗電|抗电', line, re.I):
            data['lr'] = nums[0]
        elif re.search(r'FR|火焰|抗火', line, re.I):
            data['fr'] = nums[0]
        elif re.search(r'CR|冰霜|冰冷|抗寒|抗冰', line, re.I):
            data['cr'] = nums[0]
        elif re.search(r'PR|毒素|抗毒', line, re.I):
            data['pr'] = nums[0]

    # 红叶 6 点制算分
    pts = 0.0
    if data['fcr'] >= 10: pts += 1.0
    pts += min(data['str'], 20) / 20.0
    pts += min(data['dex'], 15) / 15.0
    pts += min(data['life'], 40) / 40.0
    pts += min(data['mana'], 90) / 90.0
    pts += min(data['all_res'], 11) / 11.0

    pts += (min(data['lr'], 30) / 30.0) * 1.0
    pts += (min(data['fr'], 30) / 30.0) * 1.0
    pts += (min(data['cr'], 30) / 30.0) * 0.8
    pts += (min(data['pr'], 30) / 30.0) * 0.5

    pts += min(data['ar'], 120) / 120.0
    pts += min(data['ll'], 8) / 8.0
    pts += min(data['lm'], 6) / 6.0

    total = round(pts, 2)

    tier = "【过渡 / 卖店】"
    color = "#888888"
    rec = "词缀分散或未达及格线，自用过渡或找铁匠换 35,000 金币。"

    if total >= 4.8:
        tier = "【海景神装 / 竞价级】"
        color = "#ff4d4f"
        rec = "理论极限属性！建议锁死，挂交易大平台竞价（估值多枚 30#/31#）。"
    elif total >= 4.2:
        tier = "【高端硬通货】"
        color = "#faad14"
        rec = "核心属性极其强力，建议交易区出货，市场估值约 27#(Ohm) ~ 28#(Lo)+。"
    elif total >= 3.5:
        tier = "【中端实用件】"
        color = "#52c41a"
        rec = "主力构筑通吃，交易区硬通货，市场估值约 22# ~ 26#(Vex)。"

    return {
        "score": total,
        "tier": tier,
        "color": color,
        "rec": rec,
        "data": data
    }