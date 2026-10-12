#!/usr/bin/env python3
"""每日早安微信模板消息。用法: python3 morning.py [--dry-run]"""
import json, os, sys, time
from datetime import datetime, date, timedelta, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

def load_env():
    """读取脚本同目录的 .env 文件(已存在的系统环境变量优先)。"""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(path):
        return
    for line in open(path, encoding="utf-8"):
        key, sep, value = line.strip().partition("=")
        if sep and not key.startswith("#"):
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


load_env()

# ---------- 配置(密钥走环境变量) ----------
APP_ID = os.getenv("WECHAT_APP_ID", "")
APP_SECRET = os.getenv("WECHAT_APP_SECRET", "")
TEMPLATE_ID = os.getenv("WECHAT_TEMPLATE_ID", "")
TARGET_OPENIDS = [x for x in os.getenv("TARGET_OPENIDS", "").split(",") if x]  # 为空=全部关注者

CITY = "淄博"
LAT, LON = 36.8070, 118.0560           # 张店区附近
START = date(2026, 4, 12)              # 恋爱开始日
TZ = timezone(timedelta(hours=8))

# ---------- 内容库(按日期轮换,可随意追加) ----------
GREETINGS = [  # 周一到周日
    "宝，周一啦，我们轻轻松松开个好头～",
    "宝，周二早安，今天也要元气满满～",
    "宝，周三早安，一周已经过半啦～",
    "宝，周四早安，再坚持一下，周末在招手～",
    "宝，周五早安，今天过完就自由啦～",
    "宝，周六早安，今天可以睡饱再慢慢起～",
    "宝，周日早安，今天适合做点让自己开心的事～",
]

# 天气码区间表: (码上限, 文案)
WEATHER_TEXT = [(0, "晴"), (2, "多云"), (3, "阴"), (48, "雾"), (57, "毛毛雨"),
                (67, "雨"), (77, "雪"), (82, "阵雨"), (86, "阵雪"), (99, "雷暴")]


def call(url, data=None, retries=3):
    """请求 JSON 接口,网络错误/5xx 自动重试。"""
    body = json.dumps(data, ensure_ascii=False).encode() if data else None
    for i in range(retries):
        try:
            req = Request(url, body, {"Content-Type": "application/json"})
            with urlopen(req, timeout=20) as resp:
                return json.load(resp)
        except Exception:
            if i == retries - 1:
                raise
            time.sleep(5 * (i + 1))


def care_tip(text, low, high):
    if "雨" in text or text == "雷暴":
        return "出门记得带伞，路滑慢慢走。"
    if "雪" in text:
        return "路面可能结冰，注意保暖防滑。"
    if text == "雾":
        return "雾大能见度低，路上慢一点。"
    if low <= 5:
        return "早晚很冷，记得穿厚外套。"
    if high - low >= 10:
        return "今天温差大，带件外套备着。"
    if high >= 30:
        return "天气炎热，多喝水注意防晒。"
    return "天气不错，记得吃早餐晒太阳。"


def get_weather():
    """返回 (天气, 温度区间, 贴心提醒);失败时返回兜底文案,不影响发送。"""
    try:
        query = urlencode({"latitude": LAT, "longitude": LON, "forecast_days": 1,
                           "timezone": "Asia/Shanghai",
                           "daily": "weather_code,temperature_2m_max,temperature_2m_min"})
        daily = call(f"https://api.open-meteo.com/v1/forecast?{query}")["daily"]
        code = daily["weather_code"][0]
        low, high = round(daily["temperature_2m_min"][0]), round(daily["temperature_2m_max"][0])
        text = next(t for limit, t in WEATHER_TEXT if code <= limit)
        return text, f"{low}℃ ~ {high}℃", care_tip(text, low, high)
    except Exception as e:
        print(f"天气获取失败,使用兜底文案: {e}", file=sys.stderr)
        return "多变", "--", "记得看看窗外的天气哦。"  # 天气获取失败的兜底


def love_text(today):
    days = (today - START).days + 1
    months = (today.year - START.year) * 12 + today.month - START.month
    if today.day == START.day and months > 0:
        return f"在一起第{months}个月，第{days}天"
    if days % 100 == 0:
        return f"相爱第{days}天，值得庆祝！"
    nxt = (days // 100 + 1) * 100
    return f"相爱第{days}天，距{nxt}天还有{nxt - days}天"


def build_message(openid, today, weather=None):
    weather, temp, tip = weather or get_weather()
    weekday = "一二三四五六日"[today.weekday()]
    field = lambda value, color: {"value": value, "color": color}
    return {
        "touser": openid,
        "template_id": TEMPLATE_ID,
        "data": {
            "first": field(GREETINGS[today.weekday()], "#FF6B8A"),
            "keyword1": field(f"{today:%Y年%m月%d日} 周{weekday}", "#5C6BC0"),
            "keyword2": field(CITY, "#26A69A"),
            "keyword3": field(weather, "#42A5F5"),
            "keyword4": field(temp, "#EF5350"),
            "keyword5": field(love_text(today), "#FF6B8A"),
            "keyword6": field(tip, "#7E57C2"),
        },
    }


def get_followers(token):
    openids, next_id = [], ""
    while True:
        data = call("https://api.weixin.qq.com/cgi-bin/user/get?"
                    + urlencode({"access_token": token, "next_openid": next_id}))
        if data.get("errcode"):
            raise RuntimeError(f"获取关注者失败: {data}")
        openids += data.get("data", {}).get("openid", [])
        next_id = data.get("next_openid")
        if not next_id:
            return openids


def main():
    today = datetime.now(TZ).date()

    if "--dry-run" in sys.argv:  # 预览:不调用微信接口
        print(json.dumps(build_message("DRY_RUN_OPENID", today), ensure_ascii=False, indent=2))
        return

    if not (APP_ID and APP_SECRET and TEMPLATE_ID):
        sys.exit("请先设置 WECHAT_APP_ID / WECHAT_APP_SECRET / WECHAT_TEMPLATE_ID")

    token = call("https://api.weixin.qq.com/cgi-bin/token?" + urlencode(
        {"grant_type": "client_credential", "appid": APP_ID, "secret": APP_SECRET}
    )).get("access_token")
    if not token:
        sys.exit("获取 access_token 失败,请检查 AppID/AppSecret 和服务器 IP 白名单")

    send_url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={token}"
    openids = TARGET_OPENIDS or get_followers(token)
    weather = get_weather()  # 天气只查一次,所有人共用
    failed = 0
    for openid in openids:
        result = call(send_url, build_message(openid, today, weather))
        ok = result.get("errcode") == 0
        failed += not ok
        print(("成功" if ok else "失败") + f": {openid} {result}")
        time.sleep(0.2)  # 避免请求过快
    print(f"发送完成: 共 {len(openids)},失败 {failed}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
