# youtube_user
> _马哥原创：用python开发的油管博主达人采集软件，支持根据搜索关键词、国家、粉丝数范围等条件，爬取博主链接、邮箱等信息。_

# 一、背景分析
## 1.1 开发背景

![爬取目标: 油管博主](https://s2.51cto.com/images/blog/202412/08095449_6754fc69f07c821166.png?x-oss-process=image/watermark,size_14,text_QDUxQ1RP5Y2a5a6i,color_FFFFFF,t_100,g_se,x_10,y_10,shadow_20,type_ZmFuZ3poZW5naGVpdGk=)

As everyone knows，YouTube（以下简称油管）是全世界最大的视频社交平台，拥有上亿的用户群体和海量日活用户。尤其是平台上来自各个国家地区的达人博主，蕴含着巨大的商业价值。通过收集油管的用户数据，客户可以更深入地了解达人博主的最新动向和商业价值，从而更有效地助力业务合作。
因此，我用python开发了一个爬虫采集工具，叫"爬油管博主软件"，如下。
## 1.2 软件界面
软件界面，如下：（目前已升级至v1.7版）<img width="900" height="678" alt="v1 7" src="https://github.com/user-attachments/assets/be718647-0e22-49c7-bce4-67147be5a1b3" />


## 1.3 结果展示
爬取结果1：（字段太多，可能看不清）
![爬取结果抽查](https://s2.51cto.com/images/blog/202412/08095450_6754fc6a39d8685286.png?x-oss-process=image/watermark,size_14,text_QDUxQ1RP5Y2a5a6i,color_FFFFFF,t_100,g_se,x_10,y_10,shadow_20,type_ZmFuZ3poZW5naGVpdGk=)

爬取结果2：（清晰版）
> https://docs.qq.com/sheet/DVEFhZlFKR1NXVEdN?tab=ht1er

## 1.4 演示视频
软件运行演示：[【软件演示】youtube博主采集工具，可爬取上万条，含邮箱！](https://www.bilibili.com/video/BV14ASTYZEFt/)

## 1.5 软件说明
几点重要说明，请详读了解：
1. Windows用户可直接双击打开exe使用，无需Python运行环境，非常方便！
2. 软件通过模拟浏览器爬取，能有效规避对端反爬
3. 支持筛选：国家地区(多)和粉丝数范围
4. 支持多个的设置项有：搜索关键词、国家地区
5. 爬取过程中，每爬一条，存一次csv。并非爬完最后一次性保存，防止因异常中断导致丢失前面的数据（每条间隔1~2s）
6. 爬取过程中，有log文件详细记录运行过程，方便回溯
7. 爬取过程中，博主筛选同时进行。并非全部博主爬完再一次性筛选，所以效率较高！ 
8. 博主csv含16个核心字段：搜索关键词,视频标题,视频链接,当前视频播放数,博主名称,博主链接,国家,telegram链接,whatsapp链接,twitter链接,facebook链接,instagram链接,粉丝数,视频总数,总观看次数,邮箱
# 二、主要技术
软件全部模块采用python语言开发，主要分工如下：
```python
tkinter：GUI软件界面  
selenium：爬虫请求  
json：解析响应数据  
csv：保存csv结果、数据清洗  
logging：日志记录
```
下面介绍python主要实现逻辑。

## 2.1 软件界面
软件主体界面采用tkinter开发，tkinter是Python的标准图形用户界面（GUI）工具包，允许创建窗口、对话框、按钮等桌面应用程序的组件。tkinter内置于Python中，因此无需额外安装任何库即可使用它。

部分代码实现：
```python
# 创建主窗口
root = tk.Tk()
root.title('YouTube博主采集软件v1.0')
# 设置窗口大小
root.minsize(width=900, height=650)
# 搜索关键词
tk.Label(root, text='搜索关键词:').place(x=30, y=130)
query = tk.StringVar()
query.set('')
entry = tk.Entry(root, bg='#ffffff', width=80, textvariable=query)
entry.place(x=110, y=130, anchor='nw')  # 摆放位置
tk.Label(root, justify='left', fg='red', text='多关键词以|分隔').place(x=650, y=130)
```


## 2.2 爬虫
爬虫采用selenium模拟浏览器操作发送请求。

初始化浏览器部分：
```python
# 初始化浏览器
chrome_driver = './chromedriver.exe'  # 浏览器驱动
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
browser = webdriver.Chrome(executable_path=chrome_driver, options=chrome_options)
wait = WebDriverWait(browser, 10)
self.tk_show('\n开始爬取关键词[{}]，浏览器初始化中，请等待..\n'.format(keyword))
# 开始爬取
js = 'window.open("https://www.youtube.com/results?search_query={}");'.format(quote(keyword))
browser.execute_script(js)
```

解析博主所在国家代码：
```python
# 国家
try:
	country = browser.find_element(By.XPATH,
								   '//*[@icon="privacy_public"]/../../td[2]').text
except:
	country = ''
if country_list != ['']:  # 国家不是空
	if country not in country_list and country not in country_list2:
		self.tk_show('国家地区是[{}], 不满足指定国家地区:{}, 跳过!'.format(country, country_list))
		browser.close()
		browser.switch_to.window(handles[-2])
		continue
```

# 三、功能介绍
## 3.1 配置chromedriver
开始采集前，先安装最新版Chrome浏览器，再配置对应版本的chromedriver驱动:
> chromedriver下载说明：https://docs.qq.com/doc/DVFZNdk91eGV0cVRH
## 3.2 采集软件
配置好chromedriver后，打开youtube_user.exe软件，登录用户：

![软件登录界面](https://s2.51cto.com/images/blog/202412/08095449_6754fc69ec11e94556.png?x-oss-process=image/watermark,size_14,text_QDUxQ1RP5Y2a5a6i,color_FFFFFF,t_100,g_se,x_10,y_10,shadow_20,type_ZmFuZ3poZW5naGVpdGk=)

并在主界面填写爬取条件：
![设置爬取条件](https://s2.51cto.com/images/blog/202412/08095450_6754fc6a0ac0140488.png?x-oss-process=image/watermark,size_14,text_QDUxQ1RP5Y2a5a6i,color_FFFFFF,t_100,g_se,x_10,y_10,shadow_20,type_ZmFuZ3poZW5naGVpdGk=)

点击开始执行按钮进行采集。

# 四、付费说明
## 4.1 卡密说明
付费如下：
```python
日卡：使用期限1天，29元。日卡仅能购买一次。适合试用等临时需求
月卡：使用期限1个月，149元。月卡可多次购买。适合短期采集需求
季卡：使用期限3个月，399元。季卡可多次购买。适合中期采集需求
年卡：使用期限1年，799元。年卡可多次购买。适合长期采集需求
```
付费方式：<img width="1528" height="918" alt="收款码v2" src="https://github.com/user-attachments/assets/ec8e8a5f-9d0c-4edd-8498-324c571cb2c3" />

付费后，加我v（493882434）自动掉落登录卡密。

## 4.2 一机一码
软件采用一机一码机制，一个卡密只能在一台电脑运行、不可多电脑运行。
## 4.3 软件多开
一台电脑仅允许运行一个软件，不支持软件多开。

## 4.4 软件维护
软件由本人独立原创开发，长期维护更新，提供稳定运行​。

# 五、软件首发
"**爬油管博主软件**"首发于公众号"**老男孩的平凡之路**"，欢迎交流！
![二维码-公众号放底部](https://github.com/user-attachments/assets/b98aa9f5-aff2-450f-995d-b5df0172da08)

