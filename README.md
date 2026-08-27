# youtube_user
> 🔥 YouTube红人采集神器 - 出海品牌必备效率提升工具
> 
> 💡 功能支持：✅根据关键词筛选红人 ✅根据国家地区筛选红人 ✅根据粉丝数范围筛选红人
> 
> [⬇️下载最新版](https://github.com/mashukui/youtube_user/releases/) | [🎬使用演示](https://www.bilibili.com/video/BV1suDUBuEoi/) | [🏠产品主页](https://mashukui.github.io/youtube_user/) | [💳开通使用](https://mgnb.pro/product/youtube_user)

<p align="center">
<a href="README.md">简体中文 README</a> | <a href="README.en.md">English README</a>
</p>

# 一、背景分析
## 1.1 开发背景

![采集目标-油管红人](https://files.mdnice.com/user/32110/9df21c30-9071-48b7-bbbe-165665742a07.png)

YouTube 作为全球头部视频社交平台，汇聚上亿日活用户及多元地区红人生态，具备极高商业价值。精准采集平台用户数据，有助于深入洞察红人创作动态及商业潜力，推动高效业务合作。基于此需求，我独立开发了“油管博主采集软件v2.0”，基于 Python 技术栈实现全自动化数据采集。

为什么版本号是2.0？因为之前发布过模拟浏览器框架的初始版本，现已升级为调用官方API实现的2.0版本。

## 1.2 软件界面
软件运行界面：
![软件运行界面](https://files.mdnice.com/user/32110/b77dfa83-ac34-4ee6-b709-d5c108ae7c7b.png)

 
## 1.3 结果展示
爬取结果1：（字段实在太多了，我分成2张图展示） 
![结果一：前10字段](https://files.mdnice.com/user/32110/c43c1730-8782-422e-8eed-53feb73f1670.png)

 
![结果二：后12字段](https://files.mdnice.com/user/32110/3af9e3c3-1db1-4329-9bdd-6498c9561876.png)

 
爬取结果2：（清晰版）
> https://docs.qq.com/sheet/DVEFhZlFKR1NXVEdN?tab=ht1erv

## 1.4 软件说明
几点重要说明，请详读了解：

1. 支持Windows/Mac双端运行，无需配置Python环境，打开即用！
2. 软件通过调用油管官方api接口实现，无反爬风险
3. 支持筛选：品牌关键词 / 国家地区 / 粉丝数范围
4. 爬取过程中，每爬一条，存一次csv。并非爬完最后一次性保存，防止因异常中断导致丢失前面的数据（每条间隔1~2s，可自定义设置）
5. 爬取过程中，有log文件详细记录运行过程，方便回溯
6. 博主csv含22个核心字段：搜索关键词,页码,视频标题,视频链接,当前视频播放数,博主名称,博主链接,频道id,频道链接,国家,telegram链接,whatsapp链接,twitter链接,facebook链接,instagram链接,tiktok链接,粉丝数,视频总数,总观看次数,注册日期,邮箱_说明,邮箱_更多

# 二、代码实现
## 2.1 整体架构
完整模块采用python语言开发，主要分工如下：
```python
tkinter：GUI软件界面  
requests：爬虫请求  
threading：多线程采集
json：解析响应数据  
csv：导出csv结果
logging：日志记录
```
下面介绍python主要实现逻辑。
## 2.2 软件界面
软件主体界面采用tkinter开发，快速构建前端界面。

gui界面：
```python
# 创建主窗口
root = tk.Tk()
root.title('油管红人采集软件v2.0 | 马哥python说')
# 设置窗口大小
root.minsize(width=900, height=650)
# 左上角图标
root.iconbitmap('mage.ico')
```
## 2.2 爬虫采集

YouTubeApiClient类：YouTube Data API v3 封装
```python
搜索视频 → search_videos() # 搜索关键词，返回视频列表
获取频道 → get_channels() # 批量获取频道详情（粉丝数等）
获取视频 → get_videos() # 批量获取视频详情（播放量等）
获取地区 → get_regions() # 获取全球国家代码映射
```

YouTubeSpider类：爬虫核心逻辑

分两个阶段采集：
```python
Phase 1（API阶段）
├── 关键词搜索视频（每页50条）
├── 提取频道ID，去重
├── 批量调API获取频道基础信息（粉丝数/国家/注册时间）
└── 过滤：粉丝数范围、国家地区
    ↓
Phase 2（网页补抓，可选）
└── 访问频道 About 页面
├── 正则提取邮箱
├── 正则提取社媒链接（Telegram/WhatsApp/Twitter等）
└── 补充 API 无法获取的联系信息
```

## 2.3 日志记录
Log_week类：日志模块

日志同时写入软件界面和本地文件，持久存储。
```python
def get_logger(self):
	self.logger = logging.getLogger(__name__)
	# 日志格式
	formatter = '[%(asctime)s-%(filename)s][%(funcName)s-%(lineno)d]--%(message)s'
	# 日志级别
	self.logger.setLevel(logging.DEBUG)
	log_formatter = logging.Formatter(formatter, datefmt='%Y-%m-%d %H:%M:%S')
	# info日志文件名
	info_file_name = time.strftime("%Y-%m-%d") + '.log'
	# 将其保存到特定目录
	case_dir = r'./logs/'
	if not self.logger.handlers:
		# 控制台日志
		sh = logging.StreamHandler()
		info_handler = TimedRotatingFileHandler(filename=case_dir + info_file_name,
												when='MIDNIGHT',
												interval=1,
												backupCount=7,
												encoding='utf-8')
		self.logger.addHandler(sh)
		sh.setFormatter(log_formatter)
		self.logger.addHandler(info_handler)
		info_handler.setFormatter(log_formatter)
	return self.logger
```

# 三、快速开始
## 3.1 配置API key
如前言所说，软件已升级为全新的2.0版本-调用YouTube官方api采集接口数据，软件运行前，需配置好个人申请的API key。

开通方法：[手把手教你开通YouTube官方API接口(youtube data api v3)](https://mp.weixin.qq.com/s/cFQ8GM3EK5B448qLWytsBw)

key开通之后，把它填到当前目录的《config_pub.json》中，如下：
![配置个人API key](https://files.mdnice.com/user/32110/3d586b34-a113-4f15-b7ab-89af7935acc2.png)

 
顺便说一句，这个配置文件有2个参数，第2个参数是配置key，不多说了。
第1个参数，wait_sec，接口请求间隔，默认1s，可以根据需求自己调整。
## 3.2 启动采集
key配置好后，就可以采集了（记得打开网络，你懂得）
软件界面上，填入你关心的条件：
![筛选条件](https://files.mdnice.com/user/32110/b0040825-58ac-4dda-91ad-b5d92d5a4961.png)

 
点击开始执行按钮，软件就自动批量采集了。
## 3.3 填写建议
**1、搜索关键词**

行业名、品牌名、竞品词、多词组合--找到在该领域发内容的博主

填写建议：

| 场景 | 关键词策略 | 效果 |
|------|----------|------|
| 精准定位博主 | 直接用**品牌名/竞品词** | 找到在该领域发内容的博主 |
| 泛采集 | 用**泛词**如 "beauty", "gaming" | 采集量大但博主的类型杂 |
| 蹭热点 | 用**当下热门话题** | 短时间内找到最新活跃博主 |
| 多词组合 | "beauty tutorial \| skincare review" | 一次采多个方向的博主 |
____
**2、国家/地区**

填写支持中文/英文，如不确定，内附标准国家名称表《country.json》供参考。

填写建议：

| 场景 | 国家策略 | 作用 |
|------|---------|------|
| 品牌出海 | 选**目标市场国家**（美国/英国/澳洲）| 精准对接本地博主 |
| 跨文化内容 | 选**日韩/东南亚** | 找对中国品牌感兴趣的本地博主 |
| 规避竞争 | 选**小语种国家**（法国/德国/巴西）| 红海中的蓝海 |
| 批量采集 | **留空**（不限制国家）| 最大范围采集，不漏任何博主 |
____ 
**3、粉丝数范围**

通过粉丝数范围，精准定位博主量级，快速达成链接合作。

填写建议：
| 粉丝区间 | 适用场景 | 博主特点 |
|---------|---------|---------|
| **0~1万** | 素人/刚起步 | 价格低、配合度高，但数据不稳定 |
| **1万~10万** | 腰部博主 | 性价比最高，商业化意识初成 |
| **10万~50万** | 头部初阶 | 有一定影响力，报价适中 |
| **50万~500万** | KOL顶流 | 影响力大，但报价高、配合度低 |
| **500万+** | 超级博主 | 顶奢品牌专属，普通人基本用不起 |

____
**一句话总结，怎么用好筛选条件?**

关键词决定找什么内容的博主，国家决定找哪个市场的博主，粉丝数决定找什么级别的博主。三个条件配合使用，才能精准锁定目标，节省时间和成本。
# 四、演示视频
软件使用过程完整演示视频：[【爬虫演示】油管红人采集软件](https://www.bilibili.com/video/BV1suDUBuEoi/)

# 四、付费说明
## 4.1 卡密说明
费用如下：
```python
日卡：使用期限1天，19元。适合试用等临时需求
月卡：使用期限1个月，149元。适合短期采集需求
季卡：使用期限3个月，349元。适合中期采集需求
年卡：使用期限1年，799元。适合长期采集需求
```
开通入口：https://mgnb.pro/product/youtube_user

## 4.2 一机一码
为防止软件被恶意转卖，采用一机一码机制，一个卡密只能在一台电脑运行、不可多电脑运行。

## 4.3 软件多开
一台电脑仅允许运行一个软件，不支持软件多开。

## 4.4 软件维护
软件由本人独立原创开发，长期维护更新，提供稳定运行。

# 五、软件获取
公众号"**老男孩的平凡之路**"，后台回复"**爬油管博主**"获取最新版软件安装包。[点这里直接下载](https://github.com/mashukui/youtube_user/releases)

<img width="573" height="196" alt="二维码-公众号放底部v4" src="https://github.com/user-attachments/assets/2ecd3416-446b-47b2-8378-3887a248b4a7" />
