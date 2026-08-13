# youtube_user

> 🔥 YouTube influencer discovery tool - an efficiency tool for global brands and cross-border marketing teams.
>
> 💡 Features: ✅ filter influencers by keyword ✅ filter by country/region ✅ filter by subscriber range
>
> [⬇️Download Latest Release](https://github.com/mashukui/youtube_user/releases/) | [🎬Video Demo](https://www.bilibili.com/video/BV1suDUBuEoi/) | [🏠Homepage](https://mashukui.github.io/youtube_user/) | [💳Purchase Access](https://mgnb.pro/product/youtube_user)

<p align="center">
  <a href="README.md">简体中文 README</a> | <a href="README.en.md">English README</a>
</p>

# 1. Background

## 1.1 Why This Tool Was Built

![Collection target: YouTube influencers](https://files.mdnice.com/user/32110/9df21c30-9071-48b7-bbbe-165665742a07.png)

YouTube is one of the world's largest video social platforms, with massive daily active users and a diverse creator ecosystem across regions. Accurate collection of creator data helps brands understand creator activity, evaluate commercial potential, and improve outreach efficiency.

Based on this need, I independently developed the "YouTube Influencer Collection Software v2.0" using the Python technology stack.

Why v2.0? An earlier version used a browser automation framework. The current version has been upgraded to v2.0, which collects data through the official YouTube API.

## 1.2 Software Interface

Software interface:

![Software interface](https://files.mdnice.com/user/32110/b77dfa83-ac34-4ee6-b709-d5c108ae7c7b.png)

## 1.3 Result Preview

Collection result 1: due to the large number of fields, the result is shown in two screenshots.

![Result 1: first 10 fields](https://files.mdnice.com/user/32110/c43c1730-8782-422e-8eed-53feb73f1670.png)

![Result 2: remaining 12 fields](https://files.mdnice.com/user/32110/3af9e3c3-1db1-4329-9bdd-6498c9561876.png)

Clear result preview:

> https://docs.qq.com/sheet/DVEFhZlFKR1NXVEdN?tab=ht1erv

## 1.4 Notes

Please read the following before use:

1. Supports Windows and macOS. No Python environment is required.
2. The software collects data through the official YouTube API, reducing anti-crawling risk.
3. Supports filtering by brand keyword, country/region, and subscriber range.
4. During collection, each creator record is saved immediately to CSV instead of waiting until the whole task is complete. This reduces data loss caused by interruptions. The default interval is 1-2 seconds and can be customized.
5. Runtime logs are recorded for troubleshooting and review.
6. The creator CSV contains 22 core fields: search keyword, page, video title, video link, current video views, creator name, creator link, channel id, channel link, country, Telegram link, WhatsApp link, Twitter link, Facebook link, Instagram link, TikTok link, subscribers, video count, total views, registration date, email description, and email more.

# 2. Implementation

## 2.1 Architecture

The software is developed in Python. Core modules include:

```python
tkinter: GUI interface
requests: crawler requests
threading: multi-threaded collection
json: response parsing
csv: CSV export
logging: runtime logging
```

The following sections describe the main implementation logic.

## 2.2 Software Interface

The GUI is built with tkinter.

```python
# Create main window
root = tk.Tk()
root.title('YouTube Influencer Collection Software v2.0 | Mage Python')
# Set window size
root.minsize(width=900, height=650)
# Window icon
root.iconbitmap('mage.ico')
```

## 2.3 Crawler Logic

`YouTubeApiClient`: wrapper around YouTube Data API v3

```python
Search videos -> search_videos() # Search by keyword and return video list
Get channels -> get_channels() # Batch-fetch channel details such as subscribers
Get videos -> get_videos() # Batch-fetch video details such as views
Get regions -> get_regions() # Get global country code mapping
```

`YouTubeSpider`: core crawler logic

The collection process has two phases:

```text
Phase 1: API phase
├── Search videos by keyword, 50 videos per page
├── Extract channel IDs and deduplicate
├── Batch-call API to fetch channel basics, such as subscribers, country, registration date
└── Filter by subscriber range and country/region
    ↓
Phase 2: optional web enrichment
└── Visit channel About pages
    ├── Extract emails with regular expressions
    ├── Extract social links such as Telegram/WhatsApp/Twitter
    └── Supplement contact information unavailable through the API
```

## 2.4 Logging

`Log_week`: logging module

Logs are written both to the software interface and local files for persistence.

```python
def get_logger(self):
    self.logger = logging.getLogger(__name__)
    # Log format
    formatter = '[%(asctime)s-%(filename)s][%(funcName)s-%(lineno)d]--%(message)s'
    # Log level
    self.logger.setLevel(logging.DEBUG)
    log_formatter = logging.Formatter(formatter, datefmt='%Y-%m-%d %H:%M:%S')
    # Info log filename
    info_file_name = time.strftime("%Y-%m-%d") + '.log'
    # Save logs to a specific directory
    case_dir = r'./logs/'
    if not self.logger.handlers:
        # Console logs
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

# 3. Quick Start

## 3.1 Configure API Key

As mentioned above, v2.0 collects data through the official YouTube API. Before running the software, configure your own API key.

How to enable the API: [Step-by-step guide to enabling YouTube Data API v3](https://mp.weixin.qq.com/s/cFQ8GM3EK5B448qLWytsBw)

After obtaining the key, put it into `config_pub.json` in the current directory:

![Configure personal API key](https://files.mdnice.com/user/32110/3d586b34-a113-4f15-b7ab-89af7935acc2.png)

This config file contains two parameters. The second parameter is the API key. The first parameter, `wait_sec`, controls the request interval. The default is 1 second and can be adjusted as needed.

## 3.2 Start Collection

After configuring the key, you can start collecting data. Make sure your network is available.

In the software interface, fill in the filtering conditions you need:

![Filtering conditions](https://files.mdnice.com/user/32110/b0040825-58ac-4dda-91ad-b5d92d5a4961.png)

Click the start button, and the software will automatically collect creator data in batches.

## 3.3 Input Suggestions

**1. Search Keyword**

Use industry terms, brand names, competitor names, or keyword combinations to find creators publishing content in a specific field.

Suggestions:

| Scenario | Keyword Strategy | Effect |
| --- | --- | --- |
| Precise creator targeting | Use brand names or competitor names directly | Find creators publishing in that field |
| Broad collection | Use broad terms such as "beauty" or "gaming" | Larger collection volume, but creator types may be mixed |
| Trend tracking | Use current trending topics | Quickly find recently active creators |
| Multi-keyword combination | "beauty tutorial \| skincare review" | Collect creators across multiple directions in one run |

---

**2. Country/Region**

Chinese and English names are supported. If unsure, refer to the included standard country list `country.json`.

Suggestions:

| Scenario | Country Strategy | Purpose |
| --- | --- | --- |
| Global brand expansion | Select target markets such as the US, UK, or Australia | Reach local creators precisely |
| Cross-cultural content | Select Japan, Korea, or Southeast Asian countries | Find local creators interested in Chinese brands |
| Avoiding heavy competition | Select less saturated markets such as France, Germany, or Brazil | Find opportunities in smaller markets |
| Batch collection | Leave it empty with no country restriction | Collect broadly without missing creators |

---

**3. Subscriber Range**

Use subscriber ranges to target creators by scale and improve outreach efficiency.

Suggestions:

| Subscriber Range | Use Case | Creator Characteristics |
| --- | --- | --- |
| 0-10K | Beginners / micro creators | Low cost and cooperative, but data may be unstable |
| 10K-100K | Mid-tier creators | Best cost-performance ratio, early commercial awareness |
| 100K-500K | Early top-tier creators | More influence, moderate pricing |
| 500K-5M | Top KOLs | Strong influence, high pricing, lower flexibility |
| 5M+ | Super creators | Usually suitable for luxury or major brands |

**In short, how do you use the filters well?**

Keywords decide what kind of content creators you want to find. Country decides which market you want to target. Subscriber range decides what creator scale you want. Use the three filters together to accurately identify targets and save time and cost.

# 4. Demo Video

Full software demo: [YouTube influencer collection software demo](https://www.bilibili.com/video/BV1suDUBuEoi/)

# 5. Pricing

## 5.1 License Key Plans

Pricing:

```python
Day pass: valid for 1 day, 9.9 CNY. Suitable for trials or temporary needs.
Monthly pass: valid for 1 month, 149 CNY. Suitable for short-term collection needs.
Quarterly pass: valid for 3 months, 399 CNY. Suitable for medium-term collection needs.
Yearly pass: valid for 1 year, 799 CNY. Suitable for long-term use.
```

Purchase page: https://mgnb.pro/product/youtube_user

## 5.2 One Device, One License

To prevent unauthorized resale, the software uses a one-device-one-license mechanism. One license key can only be used on one computer.

## 5.3 Multiple Instances

Only one software instance is allowed on one computer. Multiple concurrent instances are not supported.

## 5.4 Maintenance

The software is independently developed and maintained by the author, with long-term updates.

# 6. Get the Software

Reply `爬油管博主` in the WeChat official account `老男孩的平凡之路` to get the latest software package. [Download directly here](https://github.com/mashukui/youtube_user/releases)

<img width="573" height="196" alt="二维码-公众号放底部v4" src="https://github.com/user-attachments/assets/19cd7f46-dc67-4b65-a176-f5000dfaed1b" />
