import re

def evaluate_amulet(lines: list[str]) -> dict:
    data = {
        'skills': 0, 'fcr': 0, 'str': 0, 'dex': 0,
        'life': 0, 'mana': 0, 'reg_mana': 0,
        'all_res': 0, 'lr': 0, 'fr': 0, 'cr': 0, 'pr': 0,
        'is_craft': False
    }

    def get_nums(text):
        return [int(n) for n in re.findall(r'\d+', text)]

    raw_res = {'cr': 0, 'lr': 0, 'fr': 0, 'pr': 0}

    for line in lines:
        if re.search(r'需要等級|需要等级|level|lvl', line, re.I):
            continue
        nums = get_nums(line)
        if not nums:
            continue

        # 1. 技能匹配 (兼容法师/法師/全系技能)
        if re.search(r'技能|法師|法师|ASN|SOR|PAL|BAR|NEC|DRU|AMA', line, re.I):
            for n in nums:
                if n in [1, 2]:
                    data['skills'] = max(data['skills'], n)
            continue

        # 2. 施法速度 FCR
        if re.search(r'FCR|快速施法|施法速度|更快速施法', line, re.I):
            data['fcr'] = nums[0]
            continue

        # 3. 法力回复 / 恢復 (同时支持繁简，必须优先拦截以防覆盖基础法力)
        if re.search(r'法力回复|法力恢復|恢復速度|回复速度|Reg Mana', line, re.I):
            data['reg_mana'] = nums[0]
            data['is_craft'] = True
            continue

        # 4. 基础法力 (严格熔断：若已存在较大法力值，避免被小数字误覆盖)
        if re.search(r'法力|Mana', line, re.I):
            for n in nums:
                if n > data['mana']:
                    data['mana'] = n
            continue

        # 5. 生命与属性
        if re.search(r'生命|Life', line, re.I):
            data['life'] = nums[0]
            continue
        if re.search(r'STR', line, re.I) or (re.search(r'力量', line) and not re.search(r'法力', line)):
            data['str'] = nums[0]
            continue
        if re.search(r'DEX|敏捷|敏', line, re.I):
            data['dex'] = nums[0]
            continue

        # 6. 抗性
        if re.search(r'All Res|所有抗性|全抗|RES', line, re.I):
            data['all_res'] = nums[0]
            continue
        if re.search(r'CR|冰霜|冰冷|抗寒|抗冰', line, re.I):
            raw_res['cr'] = nums[0]
        elif re.search(r'LR|閃電|闪电|抗電|抗电', line, re.I):
            raw_res['lr'] = nums[0]
        elif re.search(r'FR|火焰|抗火', line, re.I):
            raw_res['fr'] = nums[0]
        elif re.search(r'PR|毒素|抗毒', line, re.I):
            raw_res['pr'] = nums[0]

    # 手工项链标志判定
    if data['fcr'] > 10 or data['reg_mana'] > 0:
        data['is_craft'] = True

    # 四抗自动剥离合并
    if min(raw_res.values()) > 0:
        inferred_all_res = min(raw_res.values())
        data['all_res'] = max(data['all_res'], inferred_all_res)
        data['cr'] = raw_res['cr'] - inferred_all_res
        data['lr'] = raw_res['lr'] - inferred_all_res
        data['fr'] = raw_res['fr'] - inferred_all_res
        data['pr'] = raw_res['pr'] - inferred_all_res
    else:
        for k in raw_res:
            data[k] = raw_res[k]

    # --- 评分模型计算 ---
    pts = 0.0

    # 技能点数
    if data['skills'] >= 2:
        pts += 1.0
    elif data['skills'] == 1:
        pts += 0.35

    # 施法 FCR
    if data['fcr'] >= 19:
        pts += 1.0
    elif data['fcr'] >= 17:
        pts += 0.90
    elif data['fcr'] >= 15:
        pts += 0.75
    elif data['fcr'] >= 10:
        pts += 0.50

    # 属性点
    pts += min(data['str'], 30) / 30.0
    pts += min(data['dex'], 20) / 20.0
    pts += min(data['life'], 60) / 60.0
    # 法力折算 (手工项链法力上限可超 100，满 90 即可折算 1.0 分)
    pts += min(data['mana'], 90) / 90.0

    # 抗性
    pts += min(data['all_res'], 20) / 20.0
    pts += (min(data['lr'], 40) / 40.0) * 0.75
    pts += (min(data['fr'], 40) / 40.0) * 0.75
    pts += (min(data['cr'], 40) / 40.0) * 0.5
    pts += (min(data['pr'], 40) / 40.0) * 0.4

    # 核心基石溢价：+2技能 与 17+FCR 形成流派突破档位
    has_synergy = False
    if data['skills'] >= 2 and data['fcr'] >= 17:
        pts += 1.20
        has_synergy = True
    elif data['skills'] >= 2 and data['fcr'] >= 10:
        pts += 0.50

    total = round(pts, 2)

    # 档位判定
    if total >= 4.8:
        tier = "【海景毕业 / 天价竞价】"
        color = "#ff4d4f"
        rec = "天花板属性！+2技能+突破档位FCR+极品高变属性，估值数枚 30#/31#(Jah/Ber)+！"
    elif total >= 4.2:
        tier = "【极品流通大货】"
        color = "#faad14"
        rec = "顶配通用大货，核心属性极其扎实，交易区硬通货，估值约 28#(Lo) ~ 30#(Jah)。"
    elif total >= 3.4:
        tier = "【实用自用件】"
        color = "#52c41a"
        rec = "成型构筑通吃，优质过渡硬通货，估值约 24#(Ist) ~ 26#(Vex)。"
    else:
        tier = "【过渡 / 卖店】"
        color = "#888888"
        rec = "缺少核心技能或施法档位，自用过渡或找铁匠换 35,000 金币。"

    if has_synergy:
        rec = "⚡已激活【2技能+突破档FCR】核心基石溢价！" + rec

    return {
        "score": total,
        "tier": tier,
        "color": color,
        "rec": rec,
        "data": data
    }