# 早安微信模板消息

每天早上，为你送上一条专属的微信早安消息。只用 Python 标准库，无需安装依赖，要求 Python 3.8+。

## 功能

- **星期问候**：每天一句不同的早安开场白，周一到周日各不相同
- **今日天气**：城市、天气和当天温度区间，一眼看清
- **恋爱天数**：记录相爱的每一天，并提示距离下一个整百天还有多久
- **纪念日提醒**：每月纪念日和整百天会有专属祝福
- **贴心提醒**：根据天气自动提示，下雨带伞、降温加衣、高温防晒、大雾慢行

## 调试

**1. 本地预览（不发送，不需要密钥）**

```powershell
python morning.py --dry-run
```

只打印消息内容，不会调用微信接口。如果终端中文乱码，先执行 `$env:PYTHONIOENCODING="utf-8"`。

**2. 只发给自己**

把 `.env` 里的 `TARGET_OPENIDS` 改成你自己的 openid，然后运行：

```powershell
python morning.py
```

成功会输出 `成功: ... 'errcode': 0`。

**3. 正式发送**

确认效果后，清空 `TARGET_OPENIDS` 再运行，即发送给所有关注者。

## 配置

### 环境变量（`.env`）

在脚本同目录的 `.env` 文件中填写，脚本启动时会自动读取：

| 变量 | 说明 |
| --- | --- |
| `WECHAT_APP_ID` | 公众号 AppID |
| `WECHAT_APP_SECRET` | 公众号 AppSecret |
| `WECHAT_TEMPLATE_ID` | 审核通过的模板消息 ID |
| `TARGET_OPENIDS` | 接收人 openid，多个用英文逗号分隔；留空表示发送给所有关注者 |

`.env` 含有密钥，已加入 `.gitignore`，请勿提交或外传。

### 个性化设置（`morning.py` 顶部）

| 常量 | 说明 |
| --- | --- |
| `CITY` | 消息里显示的城市名 |
| `LAT`、`LON` | 查询天气使用的坐标 |
| `START` | 恋爱开始日期 |
| `GREETINGS` | 周一到周日的开场白，可直接修改 |

### 模板字段

微信模板需包含 `first`、`keyword1` ~ `keyword6`，对应内容如下：

| 字段 | 内容 |
| --- | --- |
| `first` | 星期问候 |
| `keyword1` | 日期和星期 |
| `keyword2` | 城市 |
| `keyword3` | 天气 |
| `keyword4` | 温度区间 |
| `keyword5` | 恋爱天数 / 纪念日 |
| `keyword6` | 天气贴心提醒 |
