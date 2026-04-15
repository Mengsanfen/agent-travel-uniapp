import os
from typing import Any

from dotenv import load_dotenv
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

API_KEY = os.getenv("API_KEY")
APPCODE = os.getenv("APPCODE")
AMAP_WEB_SERVICE_KEY = os.getenv("AMAP_WEB_SERVICE_KEY")

CONNECTIONS: dict[str, dict[str, Any]] = {
    "web_search": {
        "url": "https://dashscope.aliyuncs.com/api/v1/mcps/WebSearch/mcp",
        "headers": {"Authorization": f"Bearer {API_KEY}"},
        "transport": "streamable_http",
    },
    "china_railway": {
        "url": "https://dashscope.aliyuncs.com/api/v1/mcps/china-railway/sse",
        "headers": {"Authorization": f"Bearer {API_KEY}"},
        "transport": "sse",
    },
    "geng-search-image": {
        "url": "https://ai.weiniai.cn/search-image",
        "transport": "streamable_http",
        "headers": {"Authorization": f"Bearer {APPCODE}"},
    },
}

if AMAP_WEB_SERVICE_KEY:
    CONNECTIONS["amap_maps"] = {
        "url": f"https://mcp.amap.com/mcp?key={AMAP_WEB_SERVICE_KEY}",
        "transport": "streamable_http",
    }


async def get_available_tools() -> tuple[list[BaseTool], dict[str, str]]:
    all_tools: list[BaseTool] = []
    failed_servers: dict[str, str] = {}

    if not AMAP_WEB_SERVICE_KEY:
        failed_servers["amap_maps"] = (
            "AMAP_WEB_SERVICE_KEY is not set. "
            "Please configure the official AMap Web Service key in agent-server/.env."
        )

    for server_name, connection in CONNECTIONS.items():
        client = MultiServerMCPClient({server_name: connection})
        try:
            tools = await client.get_tools(server_name=server_name)
            all_tools.extend(tools)
        except Exception as err:
            failed_servers[server_name] = str(err)

    return all_tools, failed_servers
