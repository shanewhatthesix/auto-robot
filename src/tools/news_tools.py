import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import json # 导入json模块
import os # 导入os模块
from functools import lru_cache # 新增导入

weather_url_mcp = 'http://t.weather.sojson.com/api/weather/city/' # 恢复为原始URL
session_mcp = requests.Session() # 新增：MCP文件中的session

@lru_cache(maxsize=32)
def _get_weather_from_api(city_code: str = "101240101") -> str:
    """获取天气信息(带5分钟缓存) - 从MCP文件复制"""
    try:
        response = session_mcp.get( # 使用新的session_mcp
            weather_url_mcp + city_code, # 使用新的weather_url_mcp
            timeout=(5, 10)  # 连接5秒，读取10秒
        )
        print(f"API 请求 URL: {response.url}")
        print(f"API 响应状态码: {response.status_code}")
        data = response.json()
        # print(f"API 响应内容: {json.dumps(data, ensure_ascii=False, indent=2)}")

        if data.get('status') != 200:
            return f"天气数据获取失败。API 返回状态: {data.get('status')}, 消息: {data.get('message', '无')}. 请检查API是否可用或城市代码是否正确。"
    except json.JSONDecodeError as e:
        return f"获取天气信息时出错: API返回内容不是有效的JSON格式。错误: {str(e)}"
    except requests.exceptions.RequestException as e:
        return f"获取天气信息时出错: 网络请求失败。错误: {str(e)}"
    except Exception as e:
        return f"获取天气信息时出错: 未知错误。错误: {str(e)}"
    
    city_info = data.get('cityInfo', {})
    forecast = data.get('data', {}).get('forecast', [{}])[0]
    
    return (
        f"城市: {city_info.get('parent', '')} {city_info.get('city', '')}\n"
        f"日期: {data.get('time', '')} {forecast.get('week', '')}\n"
        f"温度: {forecast.get('high', '')}~{forecast.get('low', '')}\n"
        f"天气: {forecast.get('type', '')}"
    )

@dataclass
class NewsItem:
    title: str
    url: str
    source: str
    time: str = ""

class NewsTools:
    """
    新闻和天气查询工具集。
    """
    def __init__(self):
        self.baidu_news_url = 'https://news.baidu.com/'
        self.xinlang_news_url = 'https://news.sina.com.cn/'
        self.Tencent_news_url = 'http://news.qq.com/'
        self.NetEase_news_url = 'https://news.163.com/'
        self.sohu_news_url = 'https://news.sohu.com'
        # self.weather_url = 'http://www.weather.com.cn/data/cityinfo/' # 移除此行，不再使用
        self.news_items: List[NewsItem] = []
        self.city_codes: Dict[str, str] = self._load_city_codes() # 加载城市代码

    def _clear_news(self):
        """清空新闻列表"""
        self.news_items = []

    def _format_news(self, max_items: int = 10) -> str:
        """格式化新闻输出"""
        if not self.news_items:
            return "暂无新闻"
            
        output = "\n" + "="*50 + "\n"
        output += f"为您找到 {len(self.news_items)} 条新闻，显示前 {min(max_items, len(self.news_items))} 条：\n"
        output += "="*50 + "\n\n"
        
        for idx, item in enumerate(self.news_items[:max_items], 1):
            output += f"{idx}. {item.title}\n"
            output += f"   来源: {item.source}\n"
            if item.time:
                output += f"   时间: {item.time}\n"
            output += f"   链接: {item.url}\n"
            output += "-"*30 + "\n"
        
        return output

    def _baidu_news(self):
        try:
            response = requests.get(self.baidu_news_url, timeout=10)
            content = response.content
            soup = BeautifulSoup(content, 'html.parser')
            titles = soup.find_all('a', attrs={'target': '_blank'})
            for i in titles:
                if i.get_text().strip() and i.get("href").strip() is not None:
                    self.news_items.append(NewsItem(
                        title=i.get_text().strip(),
                        url=i.get('href').strip(),
                        source="百度新闻"
                    ))
        except Exception as e:
            print(f"获取百度新闻时出错: {str(e)}")

    def _xinlang_news(self):
        try:
            response = requests.get(self.xinlang_news_url, timeout=10)
            content = response.content
            soup = BeautifulSoup(content, 'html.parser')
            titles = soup.find_all('a', attrs={'target': '_blank'})
            for i in titles:
                if i.get_text().strip() and i.get("href").strip() is not None:
                    self.news_items.append(NewsItem(
                        title=i.get_text().strip(),
                        url=i.get('href').strip(),
                        source="新浪新闻"
                    ))
        except Exception as e:
            print(f"获取新浪新闻时出错: {str(e)}")

    def _NetEase_news(self):
        try:
            response = requests.get(self.NetEase_news_url, timeout=10)
            content = response.content
            soup = BeautifulSoup(content, 'html.parser')
            div = soup.find(name="div", attrs={"class": "newsdata_wrap"})
            if div:
                div = div.find("li", class_="newsdata_item", attrs={'ne-role':'tab-body'})
            if div is not None:
                a_tags = div.find_all("a")
                for i in a_tags:
                    if i.get_text().strip() and i.get('href').strip() is not None:
                        self.news_items.append(NewsItem(
                            title=i.get_text().strip(),
                            url=i.get('href').strip(),
                            source="网易新闻"
                        ))
        except Exception as e:
            print(f"获取网易新闻时出错: {str(e)}")

    def _sohu_news(self):
        try:
            response = requests.get(self.sohu_news_url, timeout=10)
            content = response.content
            soup = BeautifulSoup(content, 'html.parser')
            div = soup.find(id="block4")

            if div is not None:
                a_tags = div.find_all("a")
                for i in a_tags:
                    if i.get_text().strip() and i.get('href').strip() is not None:
                        self.news_items.append(NewsItem(
                            title=i.get_text().strip(),
                            url=self.sohu_news_url + i.get('href').strip(),
                            source="搜狐新闻"
                        ))
        except Exception as e:
            print(f"获取搜狐新闻时出错: {str(e)}")

    def get_latest_news(self, max_items: int = 10) -> str:
        """
        获取最新新闻。
        :param max_items: 最多显示的新闻条数，默认为10。
        :return: 格式化的新闻字符串。
        """
        self._clear_news()
        self._baidu_news()
        self._xinlang_news()
        self._NetEase_news()
        self._sohu_news()
        return self._format_news(max_items)

    def _load_city_codes(self) -> Dict[str, str]:
        """
        从data/weather.json加载城市代码映射。
        """
        file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'weather.json') # 修正路径
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"错误: 未找到城市代码文件 {file_path}")
            return {}
        except json.JSONDecodeError:
            print(f"错误: 城市代码文件 {file_path} 格式不正确")
            return {}

    def get_city_weather(self, city_name_or_code: str = "重庆") -> str:
        """
        获取指定城市的天气信息。
        可以通过城市名称（如“北京”）或城市代码（如“101010100”）查询。
        :param city_name_or_code: 城市名称或城市代码，默认为“重庆”。
        :return: 格式化的天气信息字符串。
        """
        print(f"get_city_weather 接收到 city_name_or_code: '{city_name_or_code}'")
        actual_city_code = self.city_codes.get(city_name_or_code, city_name_or_code)
        print(f"解析后的城市代码 actual_city_code: '{actual_city_code}'")
        
        # 检查是否是有效的城市代码（纯数字）
        if not actual_city_code.isdigit():
            return f"无法识别的城市名称或代码: {city_name_or_code}。请提供有效的城市名称或城市代码。"

        # 调用从MCP文件复制过来的天气获取函数
        return _get_weather_from_api(actual_city_code)

if __name__ == '__main__':
    news_tool = NewsTools()
    print("--- 最新新闻 ---")
    print(news_tool.get_latest_news(max_items=5))
    print("\n--- 重庆天气 ---")
    print(news_tool.get_city_weather("101040100"))
    print("\n--- 北京天气 ---")
    print(news_tool.get_city_weather("101010100"))