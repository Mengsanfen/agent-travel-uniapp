import os

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent

load_dotenv()

# 读取环境变量
API_KEY = os.getenv("API_KEY")
APPCODE = os.getenv("APPCODE")
AMAP_WEB_SERVICE_KEY = os.getenv("AMAP_WEB_SERVICE_KEY", "")

client = MultiServerMCPClient(
    {
        # 联网搜索
        "web_search": {
            "url": "https://dashscope.aliyuncs.com/api/v1/mcps/WebSearch/mcp",
            "headers": {"Authorization": f"Bearer {API_KEY}"},
            "transport": "streamable_http"
        },
        # 高德地图
        "amap_maps": {
            "url": f"https://mcp.amap.com/mcp?key={AMAP_WEB_SERVICE_KEY}",
            "transport": "streamable_http"
        },
        # 12306
        "china_railway": {
            "url": "https://dashscope.aliyuncs.com/api/v1/mcps/china-railway/sse",
            "headers": {"Authorization": f"Bearer {API_KEY}"},
            "transport": "sse"
        },
        # 搜索图片
        "geng-search-image": {
            "url": "https://ai.weiniai.cn/search-image",
            "transport": "streamable_http",
            "headers": {"Authorization": f"Bearer {APPCODE}"},
        },
    }
)
