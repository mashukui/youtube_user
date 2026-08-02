import time
from urllib.parse import urlencode
from urllib.parse import unquote, parse_qs, urlparse
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError
import csv
import re
import datetime
import os
import html
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import logging
from logging.handlers import TimedRotatingFileHandler
import threading
import webbrowser
import json
from json import JSONDecodeError
import pymysql
import subprocess
import platform
import queue
import unicodedata

QUERY_PLACEHOLDER = '必填。多关键词以 | 分隔'
COUNTRY_PLACEHOLDER = '可不填。多国家以 | 分隔'


class Log_week():
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


class YouTubeApiClient:
	"""YouTube Data API v3 客户端

	负责：
	1. API Key 管理与自动轮换（额度用尽/无效时切换下一个Key）
	2. HTTP请求与重试机制
	3. 封装 search/videos/channels/i18nRegions 等端点
	"""

	BASE_URL = "https://www.googleapis.com/youtube/v3"

	def __init__(self, api_keys, logger=None, ui_log_func=None, key_index_change_func=None, timeout=20, max_retries=3, request_interval_sec=0):
		self.api_keys = [str(api_key).strip() for api_key in api_keys if str(api_key).strip()]
		if not self.api_keys:
			raise ValueError("YouTube API Key不能为空")
		self.api_key_index = 0
		self._unavailable_key_indexes = set()
		self.logger = logger
		self.ui_log_func = ui_log_func
		self.key_index_change_func = key_index_change_func
		self.timeout = timeout
		self.max_retries = max_retries
		self.request_interval_sec = max(float(request_interval_sec), 0.0)
		self._last_request_ts = 0.0

	@property
	def api_key(self):
		return self.api_keys[self.api_key_index]

	def _show_message(self, message):
		if self.logger:
			self.logger.warning(message)
		if self.ui_log_func:
			try:
				self.ui_log_func(message)
			except Exception:
				pass

	def _is_quota_exceeded(self, status_code, body):
		"""检测403配额超限错误"""
		if status_code != 403:
			return False
		try:
			data = json.loads(body)
		except Exception:
			return "quotaExceeded" in body or "youtube.quota" in body
		error_data = data.get("error", {})
		errors = error_data.get("errors", [])
		for item in errors:
			if item.get("reason") == "quotaExceeded" or item.get("domain") == "youtube.quota":
				return True
		return error_data.get("reason") == "quotaExceeded" or "quotaExceeded" in str(error_data)

	def _is_api_key_invalid(self, status_code, body):
		"""检测400无效API Key错误"""
		if status_code != 400:
			return False
		try:
			data = json.loads(body)
		except Exception:
			return "API_KEY_INVALID" in body or "API key not valid" in body
		error_data = data.get("error", {})
		if error_data.get("status") == "INVALID_ARGUMENT":
			message = str(error_data.get("message", ""))
			if "API key not valid" in message:
				return True
		for item in error_data.get("errors", []):
			message = str(item.get("message", ""))
			if "API key not valid" in message:
				return True
		for item in error_data.get("details", []):
			if item.get("reason") == "API_KEY_INVALID":
				return True
			message = str(item.get("message", ""))
			if "API key not valid" in message:
				return True
		return "API_KEY_INVALID" in str(error_data)

	def _switch_to_next_api_key(self, unavailable_reason):
		"""切换到下一个可用的API Key"""
		current_index = self.api_key_index
		self._unavailable_key_indexes.add(current_index)
		for offset in range(1, len(self.api_keys) + 1):
			next_index = (current_index + offset) % len(self.api_keys)
			if next_index not in self._unavailable_key_indexes:
				self.api_key_index = next_index
				if self.key_index_change_func:
					try:
						self.key_index_change_func(next_index + 1)
					except Exception:
						pass
				self._show_message(
					f"YouTube API Key第{current_index + 1}个{unavailable_reason}，自动切换到第{next_index + 1}个Key继续请求。"
				)
				return True
		self._show_message("所有YouTube API Key均不可用，请检查config_pub.json中的Key是否有效或新增可用Key后重试。")
		return False

	def _request(self, endpoint, params):
		"""[专有代码已移除] 核心HTTP请求方法
		"""
		# [专有代码已移除] HTTP请求 + 重试 + Key轮换逻辑
		raise NotImplementedError("核心请求逻辑需要专有实现")

	def search_videos(self, keyword, page_token=None, max_results=50, region_code=None):
		"""搜索视频（调用 search 端点）"""
		params = {
			"part": "snippet",
			"q": keyword,
			"type": "video",
			"maxResults": max_results,
			"safeSearch": "none",
		}
		if region_code:
			params["regionCode"] = region_code
		if page_token:
			params["pageToken"] = page_token
		return self._request("search", params)

	def get_channels(self, channel_ids):
		"""批量获取频道信息（调用 channels 端点）"""
		if not channel_ids:
			return {}
		data = self._request("channels", {
			"part": "snippet,statistics,brandingSettings",
			"id": ",".join(channel_ids),
			"maxResults": 50,
		})
		return {item.get("id"): item for item in data.get("items", [])}

	def get_videos(self, video_ids):
		"""批量获取视频信息（调用 videos 端点）"""
		if not video_ids:
			return {}
		data = self._request("videos", {
			"part": "snippet,statistics",
			"id": ",".join(video_ids),
			"maxResults": 50,
		})
		return {item.get("id"): item for item in data.get("items", [])}

	def get_regions(self, hl):
		"""获取支持的国家/地区列表（调用 i18nRegions 端点）"""
		data = self._request("i18nRegions", {"part": "snippet", "hl": hl})
		return {item.get("id"): item.get("snippet", {}).get("name", "") for item in data.get("items", [])}


class YouTubeSpider:
	"""YouTube博主采集模块

	负责：
	1. 根据关键词搜索视频 → 提取博主频道信息
	2. 按国家、粉丝数等条件筛选
	3. 提取联系方式（邮箱、社媒链接等）
	4. 可选Phase2：访问频道About页补全联系方式
	5. 结果写入CSV
	"""

	def __init__(self, query, country2, fans_num_min, fans_num_max, max_page, txt_msglist, logger, enable_phase2=False):
		self.query = query
		self.country2 = country2
		self.fans_num_min = fans_num_min
		self.fans_num_max = fans_num_max
		self.max_page = max_page
		self.enable_phase2 = bool(enable_phase2)
		self.result_file = 'ytb博主_{}.csv'.format(datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
		self.txt_msglist = txt_msglist
		self.logger = logger
		self.describe = []
		self._public_config_cache = None
		self._public_config_error = None
		self.wait_sec = 2.0
		self._phase2_last_request_ts = 0.0
		self.current_api_key_index = None
		self.init()

	def init(self):
		"""初始化CSV文件，写入表头"""
		with open(self.result_file, 'a+', newline='', encoding='utf_8_sig') as f:
			writer = csv.writer(f)
			writer.writerow(
				['搜索关键词', '页码', '视频标题', '视频链接', '当前视频播放数', '博主名称', '博主链接', '频道id', '频道链接', '国家', 'telegram链接',
				 'whatsapp链接', 'twitter链接', 'facebook链接', 'instagram链接', 'tiktok链接', '粉丝数', '视频总数', '总观看次数',
				 '注册日期', '邮箱_说明', '邮箱_更多'])

	def tk_show(self, context):
		"""线程安全的日志输出到Tkinter Text控件"""
		message = str(context)
		if self.current_api_key_index:
			if message.startswith('\n'):
				message = '\n[key{}]{}'.format(self.current_api_key_index, message[1:])
			else:
				message = '[key{}]{}'.format(self.current_api_key_index, message)
		self.logger.info(message)
		log_queue = getattr(self.txt_msglist, "_log_queue", None)
		if log_queue is not None:
			log_queue.put(message)
			return
		self.txt_msglist.delete('1.0', 'end')
		self.describe.append(message)
		self.txt_msglist.insert('insert', '\n'.join(self.describe))
		self.txt_msglist.see("end")

	def _load_public_config(self):
		"""读取公开配置文件 config_pub.json"""
		if self._public_config_cache is not None:
			return self._public_config_cache
		config_file = 'config_pub.json'
		try:
			with open(config_file, 'r', encoding='utf-8') as file:
				self._public_config_cache = json.load(file)
				self._public_config_error = None
		except JSONDecodeError as e:
			self._public_config_error = e
			self.logger.warning("config_pub.json格式错误: %s", str(e))
			self._public_config_cache = {}
		except Exception as e:
			self._public_config_error = e
			self.logger.warning("读取config_pub.json失败: %s", str(e))
			self._public_config_cache = {}
		return self._public_config_cache

	def get_public_config_error_message(self):
		"""获取配置文件错误的人类可读描述"""
		error = self._public_config_error
		if not error:
			return ""
		if isinstance(error, JSONDecodeError):
			return (
				f"config_pub.json 格式错误：第{error.lineno}行附近有问题。\n\n"
				"常见错误：\n"
				"1、最后一个Key后面多写了英文逗号。\n"
				"2、Key没用英文双引号包起来。\n"
				"3、使用了中文逗号或中文引号。\n"
				"4、没用的行还没删除。\n\n"
				"正确示例：\n"
				'{\n'
				'  "wait_sec": 1,\n'
				'  "youtube_api_keys": [\n'
				'    "你的第1个key",\n'
				'    "你的第2个key",\n'
				'    "你的第3个key"\n'
				'  ]\n'
				'}'
			)
		return f"读取 config_pub.json 失败：{error}"

	def get_api_keys(self):
		"""从 config_pub.json 读取 YouTube API Key 列表"""
		text = self._load_public_config()
		if self._public_config_error:
			return []
		values = text.get("youtube_api_keys", [])
		if not isinstance(values, list):
			self.logger.warning("config_pub.json 的 youtube_api_keys 必须是数组")
			return []
		api_keys = [str(value).strip() for value in values if str(value).strip()]
		if api_keys:
			return api_keys
		self.logger.warning("config_pub.json 缺少 youtube_api_keys 字段或数组为空")
		return []

	def get_wait_sec(self):
		"""从 config_pub.json 读取请求间隔"""
		text = self._load_public_config()
		raw_value = text.get("wait_sec", 2)
		if raw_value in ("", None):
			return 2.0
		try:
			return float(raw_value)
		except Exception:
			return 2.0

	def set_current_api_key_index(self, key_index):
		self.current_api_key_index = key_index

	def _alert_wait_sec_invalid(self, wait_sec):
		def _show_popup():
			try:
				messagebox.showerror("配置错误", f'config_pub.json 的 wait_sec={wait_sec}，最小值为 1 秒，请修改后重试。')
			except Exception as e:
				self.logger.warning("wait_sec弹窗失败: %s", str(e))
		try:
			self.txt_msglist.after(0, _show_popup)
		except Exception:
			_show_popup()

	def _safe_int(self, value):
		try:
			return int(str(value).strip())
		except Exception:
			return 0

	def _safe_float(self, value, default=0.0):
		try:
			return float(str(value).strip())
		except Exception:
			return default

	def _normalize_country_key(self, value):
		"""统一国家名称格式（用于匹配）"""
		text = unicodedata.normalize("NFKC", str(value or ""))
		for ch in ("\ufeff", "\u200b", "\u200c", "\u200d"):
			text = text.replace(ch, "")
		text = text.replace("\u3000", " ")
		return " ".join(text.strip().lower().split())

	def _country_alias_code(self, name):
		"""中文别名 → ISO国家代码的硬编码映射"""
		alias = {
			"中国": "CN",
			"中华人民共和国": "CN",
			"中国大陆": "CN",
			"大陆中国": "CN",
			"china": "CN",
			"mainland china": "CN",
			"美国": "US",
			"美利坚合众国": "US",
			"united states": "US",
			"日本": "JP",
			"japan": "JP",
			"英国": "GB",
			"英格兰": "GB",
			"united kingdom": "GB",
			"india": "IN",
			"印度": "IN",
			"australia": "AU",
			"澳大利亚": "AU",
		}
		return alias.get(self._normalize_country_key(name))

	def _extract_email(self, text):
		"""从文本中提取邮箱地址（去重）"""
		email_list = re.findall(r"[A-Za-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+", text or "", flags=re.I)
		seen = set()
		unique_emails = []
		for email in email_list:
			key = email.strip().lower()
			if key and key not in seen:
				seen.add(key)
				unique_emails.append(email.strip())
		return " ".join(unique_emails)

	def _normalize_contact_url(self, url):
		"""清洗联系人URL（处理YouTube重定向包装）"""
		if not url:
			return ""
		clean_url = str(url).strip().rstrip('.,);]}>\'"')
		try:
			parsed = urlparse(clean_url)
			host = parsed.netloc.lower()
			if "youtube.com" in host and parsed.path.startswith("/redirect"):
				query_dict = parse_qs(parsed.query)
				target = ""
				if query_dict.get("q"):
					target = query_dict["q"][0]
				elif query_dict.get("url"):
					target = query_dict["url"][0]
				if target:
					target = unquote(unquote(target))
					return target.strip().rstrip('.,);]}>\'"')
		except Exception:
			return clean_url
		return clean_url

	def _extract_contacts(self, text):
		"""从文本中提取社媒链接（Telegram/WhatsApp/Twitter/Facebook/Instagram/TikTok）"""
		telegram_url = "该博主未设置Telegram信息"
		whatsapp_url = "该博主未设置WhatsApp信息"
		twitter_url = "该博主未设置Twitter信息"
		facebook_url = "该博主未设置Facebook信息"
		instagram_url = "该博主未设置Instagram信息"
		tiktok_url = "该博主未设置Tiktok信息"
		urls = re.findall(r'https?://[^\s<>"\']+', text or "")
		for url in urls:
			url = self._normalize_contact_url(url)
			url_l = url.lower()
			if "t.me/" in url_l and telegram_url.startswith("该博主未设置"):
				telegram_url = url
			if ("wa.link" in url_l or "wa.me/" in url_l or "whatsapp.com" in url_l) and whatsapp_url.startswith("该博主未设置"):
				whatsapp_url = url
			if ("twitter.com" in url_l or "x.com/" in url_l) and twitter_url.startswith("该博主未设置"):
				twitter_url = url
			if "facebook.com" in url_l and facebook_url.startswith("该博主未设置"):
				facebook_url = url
			if "instagram.com" in url_l and instagram_url.startswith("该博主未设置"):
				instagram_url = url
			if "tiktok.com" in url_l and tiktok_url.startswith("该博主未设置"):
				tiktok_url = url
		return telegram_url, whatsapp_url, twitter_url, facebook_url, instagram_url, tiktok_url

	def _phase2_fetch_about(self, channel_url):
		"""[专有代码已移除] 访问频道About页补全联系方式

		原实现：
		1. 根据 wait_sec 控制请求间隔
		2. 构造 HTTP GET 请求访问 {channel_url}/about?hl=zh-CN
		3. 设置 User-Agent 模拟浏览器
		4. 解析HTML：
		   - 检测「查看电子邮件地址」按钮 → email_more_tag = "Yes"/"No"
		   - 提取邮箱地址
		   - 提取社媒链接
		5. 返回 dict：email_more_tag, email_str, telegram/WhatsApp/Twitter/Facebook/Instagram/TikTok链接
		"""
		# [专有代码已移除] HTTP请求 + HTML解析 + 联系方式提取
		return {
			"email_more_tag": "Unknown(API限制)",
			"email_str": "",
			"telegram_url": "该博主未设置Telegram信息",
			"whatsapp_url": "该博主未设置WhatsApp信息",
			"twitter_url": "该博主未设置Twitter信息",
			"facebook_url": "该博主未设置Facebook信息",
			"instagram_url": "该博主未设置Instagram信息",
			"tiktok_url": "该博主未设置Tiktok信息",
		}

	def _normalize_publish_date(self, value):
		if not value:
			return ""
		return str(value).replace("T", " ")[:10]

	def _build_channel_url(self, channel_id, channel_snippet):
		"""根据 customUrl 或 channelId 构建频道链接"""
		custom_url = str(channel_snippet.get("customUrl", "")).strip()
		if custom_url:
			custom_url = custom_url.replace("https://www.youtube.com/", "").replace("http://www.youtube.com/", "").strip("/")
			if custom_url.startswith("@") or custom_url.startswith("c/") or custom_url.startswith("user/"):
				return f"https://www.youtube.com/{custom_url}"
			if re.fullmatch(r"[A-Za-z0-9._-]+", custom_url):
				return f"https://www.youtube.com/@{custom_url}"
		return f"https://www.youtube.com/channel/{channel_id}"

	def _notify_finish(self):
		"""采集完成弹窗提醒（带提示音）"""
		def _show_popup():
			try:
				if platform.system() == "Windows":
					try:
						import winsound
						winsound.MessageBeep(winsound.MB_ICONASTERISK)
					except Exception:
						pass
				else:
					try:
						self.txt_msglist.bell()
					except Exception:
						pass
					print('\a', end='', flush=True)
			except Exception:
				pass
			try:
				messagebox.showinfo("采集完成", f"全部关键词采集完毕！\n查看结果文件：{self.result_file}")
			except Exception as e:
				self.logger.warning("弹窗提醒失败: %s", str(e))

		def _wait_logs_then_popup():
			log_queue = getattr(self.txt_msglist, "_log_queue", None)
			if log_queue is not None and not log_queue.empty():
				self.txt_msglist.after(80, _wait_logs_then_popup)
				return
			self.txt_msglist.after(60, _show_popup)

		try:
			self.txt_msglist.after(0, _wait_logs_then_popup)
		except Exception:
			_show_popup()

	def _split_chunks(self, values, chunk_size=50):
		"""将列表按 chunk_size 切分（API每次最多50个ID）"""
		for idx in range(0, len(values), chunk_size):
			yield values[idx:idx + chunk_size]

	def _load_country_dict(self):
		"""读取本地国家映射文件 country.json"""
		try:
			country_path = 'country.json'
			with open(country_path, 'r', encoding='utf8') as file:
				return json.load(file)
		except Exception as e:
			self.tk_show(f'读取国家配置失败:{e}')
			return {}

	def _build_country_maps(self, client):
		"""构建国家名称↔代码的双向映射表"""
		country_dict = self._load_country_dict()
		region_zh = client.get_regions("zh-CN")
		region_en = client.get_regions("en-US")
		name_to_code = {}
		code_to_name = {}
		code_to_en_name = {}
		en_to_code = {}
		for code, name in region_en.items():
			code_to_name[code] = region_zh.get(code) or name or code
			code_to_en_name[code] = name or ""
			if name:
				normalized = self._normalize_country_key(name)
				name_to_code[normalized] = code
				en_to_code[normalized] = code
		for code, name in region_zh.items():
			if name:
				name_to_code[self._normalize_country_key(name)] = code
		for zh_name, en_name in country_dict.items():
			zh_key = self._normalize_country_key(zh_name)
			en_key = self._normalize_country_key(en_name)
			if en_key in en_to_code:
				code = en_to_code[en_key]
				name_to_code[zh_key] = code
				name_to_code[en_key] = code
				code_to_name[code] = zh_name
		return name_to_code, code_to_name, code_to_en_name

	def _parse_country_filter_codes(self, country_list, name_to_code, valid_region_codes=None):
		"""将用户输入的国家名称/代码转换为标准ISO代码集合"""
		country_codes = set()
		for country_name in country_list:
			name = country_name.strip()
			if not name:
				continue
			if re.fullmatch(r"[A-Za-z]{2}", name):
				code = name.upper()
				if valid_region_codes and code not in valid_region_codes:
					mapped_code = name_to_code.get(self._normalize_country_key(name))
					if mapped_code:
						code = mapped_code
					else:
						self.tk_show(f'\n输入国家代码有误:{name}，请填写有效的2位国家代码。')
						return None
				country_codes.add(code)
				continue
			code = name_to_code.get(self._normalize_country_key(name))
			if not code:
				code = self._country_alias_code(name)
			if not code:
				self.tk_show(f'\n输入国家名有误:{name}，请填写标准国家名（中英文均可），可参考《country.json》')
				return None
			country_codes.add(code)
		return country_codes

	def spider(self):
		"""[专有代码已移除] 主采集流程

		原实现核心流程：
		1. 校验 config_pub.json 配置（API Keys、wait_sec）
		2. 创建 YouTubeApiClient 实例
		3. 解析关键词列表（以 | 分隔）和国家过滤条件
		4. 构建国家名称↔代码映射表（调用 i18nRegions API + 本地 country.json）
		5. 对每个关键词循环：
		   a. 调用 search_videos API 搜索视频（每页50条，支持翻页 nextPageToken）
		   b. 从搜索结果提取 channelId 列表（去重）
		   c. 调用 get_channels API 批量获取频道详情（snippet + statistics + brandingSettings）
		   d. 按国家筛选：
		      - 若单个国家：通过 regionCode 参数预筛选
		      - 若多个国家：API不支持多regionCode，在结果中二次筛选
		   e. 按粉丝数范围筛选（fans_min ~ fans_max）
		   f. 调用 get_videos API 获取视频统计信息
		   g. 已存在的 channel_id 去重
		   h. 提取联系方式：
		      - Phase1：从 brandingSettings.channel.description 和 snippet.description 提取
		      - Phase2（可选）：访问频道 /about 页面补全联系方式
		   i. 实时写入CSV（22列）
		6. 翻页循环直到 nextPageToken 为空或达到 max_page 限制
		7. 采集完成弹窗提醒
		"""
		self.tk_show('\n[专有代码已移除] 核心采集逻辑需要专有实现')
		self.tk_show('\n程序开始采集，请确保已在config_pub.json配置好了youtube_api_keys')


class MyThread(threading.Thread):
	def __init__(self, func, *args):
		super().__init__()
		self.func = func
		self.args = args
		self.setDaemon(True)
		self.start()  # 在这里开始

	def run(self):
		self.func(*self.args)


def open_url(event):
	webbrowser.open("https://mp.weixin.qq.com/s/cFQ8GM3EK5B448qLWytsBw", new=0)


def open_url2(event):
	webbrowser.open("https://docs.qq.com/sheet/DVGpQQnhmWGdqdmR1", new=0)


def open_sugg():
	webbrowser.open("https://docs.qq.com/sheet/DVGxzT0VVSkVzSW1u?tab=1idvfa", new=0)


def task(query, txt_msglist, phase2_var):
	"""从UI控件提取参数，启动 YouTubeSpider 采集"""
	# 获取：搜索关键词
	q = query.get()
	q = str(q).strip()
	if q == QUERY_PLACEHOLDER:
		q = ''
	print('q:', q)
	# 获取：国家
	country2 = country.get()
	country2 = str(country2).strip()
	if country2 == COUNTRY_PLACEHOLDER:
		country2 = ''
	print('country2:', country2)
	# 获取：粉丝数量
	fans_num_min = entry_fans_num_min.get()
	fans_num_min = str(fans_num_min).strip()
	print('fans_num_min:\n', fans_num_min)
	fans_num_max = entry_fans_num_max.get()
	fans_num_max = str(fans_num_max).strip()
	print('fans_num_max:\n', fans_num_max)
	# 获取前几页
	max_page = entry_max_page.get()
	max_page = str(max_page).strip()
	print('max_page:\n', max_page)
	phase2_mode = str(phase2_var.get()).strip()
	enable_phase2 = phase2_mode == '开启'
	print('enable_phase2:\n', enable_phase2)
	log = Log_week()
	logger = log.get_logger()
	YouTubeSpider(q, country2, fans_num_min, fans_num_max, max_page, txt_msglist, logger, enable_phase2=enable_phase2).spider()


def show_about():
	messagebox.showinfo("About",
						'v1.0: 基础版本发布\nv1.1: 允许国家为空\nv1.2: 修复中途异常\nv1.3: 字段新增channel_id&新增意见收集入口\nv1.4: 新增去重\nv1.5: 修复异常（抱歉此页面不存在，试试搜索其他内容）&新增邮箱按钮提示\nv1.6: 新增mac端\nv1.7: 新增前几页\nv1.8: 修复"频道图标未检测到"\nv2.0: 改为YouTube Data API v3模式（Phase 1）\nv2.1: 支持配置多个key&自动轮换\n\n最新版本获取：\n公众号 "老男孩的平凡之路" 回复：爬油管博主')


def show_agreement():
	messagebox.showinfo("使用协议",
						"""欢迎使用本软件！在使用前，请仔细阅读以下使用协议：

授权与许可：本软件仅授权用户用于合法的个人或商业用途。禁止使用本软件进行任何违法活动，包括但不限于未经授权的数据采集、侵犯知识产权和侵犯隐私权等。
责任限制：本软件开发者不对用户因使用本软件而导致的任何直接或间接损失负责。用户在使用过程中应遵守相关法律法规，并自行承担因使用本软件而产生的风险和责任。
数据隐私：本软件不会收集、存储或分享用户的个人数据。用户采集的数据应严格遵守数据保护法律和目标网站的使用政策。
更新与维护：我们有权随时对本软件进行更新和维护，用户应及时下载并安装更新，以确保软件的正常使用。
协议修改：我们保留随时修改本使用协议的权利，修改后的协议将在发布后立即生效。用户继续使用本软件即表示接受新的协议条款。

作为软件使用者，您默认接受以上协议条款。感谢理解与支持。如有疑问，请联系作者。"""
						)


def create_spider_root():
	global entry, country, entry_fans_num_min, entry_fans_num_max, entry_max_page, phase2_enabled_var
	# 创建日志目录
	work_path = os.getcwd()
	if not os.path.exists(work_path + "/logs"):
		os.makedirs(work_path + "/logs")
	# 创建主窗口
	root = tk.Tk()
	root.title('油管红人采集软件v2.1 | 马哥python说 | 公众号:老男孩的平凡之路')
	# 设置窗口大小
	root.minsize(width=900, height=650)
	# 左上角图标
	root.iconbitmap('mage.ico')
	# 菜单
	menu_bar = tk.Menu(root)
	file_menu = tk.Menu(menu_bar, tearoff=0)
	file_menu.add_command(label="About", command=show_about)
	file_menu.add_command(label="使用协议", command=show_agreement)
	file_menu.add_command(label="意见收集", command=open_sugg)
	menu_bar.add_cascade(label="File", menu=file_menu)
	root.config(menu=menu_bar)

	# 输出框
	output_frame1 = ttk.LabelFrame(root, text="", padding="1")
	output_frame1.place(x=25, y=260, width=820, height=310, anchor='nw')  # 摆放位置

	# 运行日志
	tk.Label(root, justify='left', text='运行日志:').place(x=30, y=275)
	show_list_Frame = tk.Frame(width=800, height=260)  # 创建<消息列表分区>
	show_list_Frame.pack_propagate(0)
	show_list_Frame.place(x=30, y=300, anchor='nw')  # 摆放位置

	# 滚动条
	scroll = tk.Scrollbar(show_list_Frame)
	# 放到Y轴竖直方向
	scroll.pack(side=tk.RIGHT, fill=tk.Y)

	# 输入采集进度
	txt_msglist = tk.Text(show_list_Frame, width=700, height=500)
	txt_msglist.config(yscrollcommand=scroll.set)  # 配置滚动条
	txt_msglist.pack()
	txt_msglist._log_queue = queue.Queue()
	txt_msglist._log_lines = []

	def flush_ui_logs():
		updated = False
		while True:
			try:
				message = txt_msglist._log_queue.get_nowait()
				txt_msglist._log_lines.append(message)
				updated = True
			except queue.Empty:
				break
		if updated:
			txt_msglist.delete('1.0', 'end')
			txt_msglist.insert('end', '\n'.join(txt_msglist._log_lines))
			txt_msglist.see("end")
		root.after(80, flush_ui_logs)

	root.after(80, flush_ui_logs)

	# 提示信息
	hint1 = tk.Label(root, justify='left', font=('微软', 10), fg='red',
					 text='说明：\n1、开启可访问YouTube的网络\n2、在当前目录《config_pub.json》中配置youtube_api_keys，点击【这里】查看开通方法')
	hint1.place(x=30, y=10)
	hint1.bind("<Button-1>", open_url)

	# 输入框
	input_frame1 = ttk.LabelFrame(root, text="", padding="1")
	input_frame1.place(x=25, y=70, width=820, height=195, anchor='nw')  # 摆放位置

	# 搜索关键词
	tk.Label(root, text='搜索关键词:').place(x=30, y=100)
	query = tk.StringVar()
	query.set(QUERY_PLACEHOLDER)
	entry = tk.Entry(root, bg='#ffffff', width=79, textvariable=query)
	entry.place(x=110, y=100, anchor='nw')  # 摆放位置
	entry.config(fg='grey')

	# 国家或地区
	tk.Label(root, text='国家或地区:').place(x=30, y=130)
	country = tk.StringVar()
	country.set(COUNTRY_PLACEHOLDER)
	entry_country = tk.Entry(root, bg='#ffffff', width=79, textvariable=country)
	entry_country.place(x=110, y=130, anchor='nw')  # 摆放位置
	entry_country.config(fg='grey')

	def bind_placeholder(entry_widget, placeholder_text):
		def on_focus_in(event):
			if entry_widget.get().strip() == placeholder_text:
				entry_widget.delete(0, tk.END)
				entry_widget.config(fg='black')

		def on_focus_out(event):
			if not entry_widget.get().strip():
				entry_widget.delete(0, tk.END)
				entry_widget.insert(0, placeholder_text)
				entry_widget.config(fg='grey')

		entry_widget.bind("<FocusIn>", on_focus_in)
		entry_widget.bind("<FocusOut>", on_focus_out)

	bind_placeholder(entry, QUERY_PLACEHOLDER)
	bind_placeholder(entry_country, COUNTRY_PLACEHOLDER)

	# 粉丝数范围
	tk.Label(root, justify='left', text='粉丝数范围:').place(x=30, y=160)
	entry_fans_num_min = tk.Spinbox(root, from_=0, to=99999999, increment=1, width=10, font=('微软', 15))
	entry_fans_num_min.place(x=110, y=160)
	tk.Label(root, justify='left', text='~').place(x=240, y=160)
	entry_fans_num_max = tk.Spinbox(root, from_=0, to=99999999, increment=1, width=10, font=('微软', 15))
	entry_fans_num_max.place(x=255, y=160)
	tk.Label(root, justify='left', fg='red', text='如无需筛选，保留两个0').place(x=390, y=160)

	# 补抓模式
	tk.Label(root, text='补抓模式:').place(x=42, y=195)
	phase2_enabled_var = tk.StringVar(value='不开启')
	phase2_dropdown = ttk.Combobox(root, textvariable=phase2_enabled_var, values=('不开启', '开启'), width=8, state='readonly')
	phase2_dropdown.place(x=110, y=195)
	phase2_hint = tk.Label(root, justify='left', fg='red',
						   text='不开启:只调API | 开启:先调API，再访问频道About页，补全社媒链接和邮箱_更多(Yes/No)，会变慢')
	phase2_hint.place(x=210, y=195)

	# 前几页
	tk.Label(root, justify='left', text='前几页:').place(x=52, y=225)
	entry_max_page = tk.Spinbox(root, from_=-1, to=9999, increment=1, width=7, font=('微软', 15))
	entry_max_page.place(x=110, y=225)
	hint3 = tk.Label(root, justify='left', fg='red', text='每个关键词采集前几页视频，每页50条数据，-1代表无限制')
	hint3.place(x=210, y=225)

	# 执行按钮
	fill_button = tk.Button(root, bg='white', text='开始执行', width=10, height=1,
							command=lambda: MyThread(task, query, txt_msglist, phase2_enabled_var))
	fill_button.place(x=270, y=590, anchor='nw')  # 摆放位置

	quit_button = tk.Button(root, text='退出程序', width=10, height=1, command=root.quit)
	quit_button.place(x=460, y=590, anchor='nw')

	# 免责声明
	claim = tk.Label(root,
					 text='免责声明: 禁止使用该软件从事任何违法活动，否则由此产生的一切法律后果由软件使用者自行承担，与软件开发作者无关！',
					 font=('微软', 10), fg='red')
	claim.place(x=50, y=570)

	# 版权信息
	copyright = tk.Label(root, text='@马哥python说 All rights reserved.', font=('仿宋', 10), fg='grey')
	copyright.place(x=290, y=625)

	# 循环消息
	root.mainloop()


def get_cpu_info():
	"""[专有代码已移除] 获取硬件信息作为设备唯一标识
	"""
	# [专有代码已移除] 硬件指纹采集
	info = ''
	return info


def get_config():
	"""[专有代码已移除] 读取私有配置文件 config.json
	"""
	# [专有代码已移除] 数据库连接配置读取
	return "", ""


def check_user(v_name, v_passwd):
	"""[专有代码已移除] 远程许可证验证
	"""
	# [专有代码已移除] 数据库连接 + 许可证查询 + 设备绑定验证
	return 0, "开源版本"


def create_login_root():
	# 创建主窗口
	root_login = tk.Tk()
	root_login.title('油管红人采集软件v2.1')
	# 设置窗口大小
	root_login.minsize(width=400, height=300)
	# 左上角图标
	root_login.iconbitmap('mage.ico')
	# 菜单
	menu_bar = tk.Menu(root_login)
	file_menu = tk.Menu(menu_bar, tearoff=0)
	file_menu.add_command(label="关于软件", command=show_about)
	file_menu.add_command(label="使用协议", command=show_agreement)
	file_menu.add_command(label="意见收集", command=open_sugg)
	menu_bar.add_cascade(label="File", menu=file_menu)
	root_login.config(menu=menu_bar)
	# 标题标签
	label_title = ttk.Label(root_login, text="用户登录", font=("Helvetica", 20, "bold"), background="#f0f4f7")
	label_title.pack(pady=20)
	# 控件
	# 用户名标签和输入框
	frame_username = ttk.Frame(root_login)
	frame_username.pack(pady=10)
	label_username = ttk.Label(frame_username, text="账号:", font=("Helvetica", 12), width=10)
	label_username.pack(side="left", padx=5)
	entry_username = ttk.Entry(frame_username, font=("Helvetica", 12), width=20)
	entry_username.pack(side="right")
	# 密码标签和输入框
	frame_password = ttk.Frame(root_login)
	frame_password.pack(pady=10)
	label_password = ttk.Label(frame_password, text="密码:", font=("Helvetica", 12), width=10)
	label_password.pack(side="left", padx=5)
	entry_password = ttk.Entry(frame_password, font=("Helvetica", 12), width=20, show="*")
	entry_password.pack(side="right")
	# 读取上次登录用户（开源版本跳过远程验证）
	if os.path.exists('./userinfo.txt'):
		try:
			with open('./userinfo.txt', 'r') as f:
				userinfos = f.readlines()
				last_username = str(userinfos[0]).strip()
				last_password = str(userinfos[1]).strip()
				entry_username.insert(0, last_username)
				entry_password.insert(0, last_password)
		except:
			pass

	def login():
		"""[专有代码已移除] 原实现通过 check_user() 连接远程数据库验证许可证"""
		# 开源版本：直接跳过登录进入主界面
		username = entry_username.get()
		print('username:', username)
		password = entry_password.get()
		print('password:', password)
		# [专有代码已移除] 远程许可证验证
		messagebox.showinfo('登录成功', '开源版本无需验证，直接进入主界面')
		root_login.destroy()
		create_spider_root()

	# 按钮框架
	frame_buttons = ttk.Frame(root_login)
	frame_buttons.pack(pady=20)
	# 登录按钮
	btn_login = ttk.Button(frame_buttons, text="登录", command=login, width=10)
	btn_login.grid(row=0, column=0, padx=10)
	# 退出按钮
	btn_quit = ttk.Button(frame_buttons, text="退出", command=root_login.quit, width=10)
	btn_quit.grid(row=0, column=1, padx=10)
	# 新用户注册按钮
	btn_register = tk.Button(frame_buttons, text="新用户注册", font=("Helvetica", 9), fg='blue', bd=0, cursor='hand2',
							 command=lambda: webbrowser.open("https://mgnb.pro/product/youtube_user", new=0))
	btn_register.grid(row=1, column=0, columnspan=2, pady=8)

	# 版权信息
	copyright = tk.Label(root_login, text='@马哥python说 All rights reserved.', font=('仿宋', 10), fg='grey')
	copyright.place(x=80, y=275)

	# 循环消息
	root_login.mainloop()


if __name__ == "__main__":
	# 开启主程序
	create_login_root()
