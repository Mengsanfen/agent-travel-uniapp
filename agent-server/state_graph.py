import asyncio
import json
import os
from typing import Any

import requests
from dotenv import load_dotenv
from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import BaseMessage, SystemMessage, ToolMessage
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool
from langgraph.graph import add_messages, StateGraph, START, END

from tools import client
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_openai.chat_models import ChatOpenAI
from typing_extensions import TypedDict, Annotated
from fastapi import WebSocket, Request
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres.aio import AsyncPostgresStore
from functools import partial
from langchain.tools import tool
from safe_tool_node import safe_tool_node

load_dotenv()

# 读取环境变量
API_KEY = os.getenv("API_KEY")
QQ_MAP_KEY = os.getenv("QQ_MAP_KEY")
AMAP_WEB_SERVICE_KEY = os.getenv("AMAP_WEB_SERVICE_KEY")
MODEL = os.getenv("MODEL")

# 模型参数传递
# tongyi = ChatTongyi(
#     model='qwen3-max',
#     api_key=API_KEY,
#     streaming=True
# )

tongyi = ChatOpenAI(
    model=MODEL,
    api_key=API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# 获取经纬度接口专用
tongyi_position = ChatTongyi(
    model=MODEL,
    api_key=API_KEY
)


# tongyi = ChatOpenAI(
#     model="qwen-plus",
#     api_key=API_KEY,
#     base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
#     streaming=True
# )
# Define map route data
@tool
def map_data(
        from_location: str,
        to_location: str,
        day: str,
        markers: list[Any],
        waypoints: str | list[Any] | None = None,
):
    """Generate route polyline data for the frontend map."""
    print("tool call -> map_data")
    print("from_location:", from_location)
    print("to_location:", to_location)
    print("day:", day)
    print("markers:", markers)
    print("waypoints:", waypoints)
    print("------------------")

    def build_route_error(message: str, status: int | None = None):
        return json.dumps(
            {
                "points": [],
                "type": "route_error",
                "day": day,
                "marker": markers or [],
                "message": message,
                "status": status,
            },
            ensure_ascii=False,
        )

    if not AMAP_WEB_SERVICE_KEY:
        return build_route_error("AMAP_WEB_SERVICE_KEY is not configured")

    def normalize_to_amap_location(location: str) -> str:
        parts = [item.strip() for item in location.split(",")]
        if len(parts) != 2:
            raise ValueError(f"Invalid coordinate format: {location}")
        latitude, longitude = float(parts[0]), float(parts[1])
        return f"{longitude},{latitude}"

    def normalize_waypoints(value: str | list[Any] | None) -> str | None:
        if value is None or value == "":
            return None
        if isinstance(value, list):
            raw_items = [str(item).strip() for item in value if str(item).strip()]
        else:
            raw_items = [item.strip() for item in str(value).split(";") if item.strip()]
        if not raw_items:
            return None
        return ";".join(normalize_to_amap_location(item) for item in raw_items)

    try:
        origin = normalize_to_amap_location(from_location)
        destination = normalize_to_amap_location(to_location)
        amap_waypoints = normalize_waypoints(waypoints)
    except ValueError as err:
        return build_route_error(str(err))

    url = "https://restapi.amap.com/v5/direction/driving"
    params = {
        "origin": origin,
        "destination": destination,
        "key": AMAP_WEB_SERVICE_KEY,
        "show_fields": "polyline",
    }
    if amap_waypoints:
        params["waypoints"] = amap_waypoints

    try:
        res = requests.get(url, params=params, timeout=15)
        res.raise_for_status()
    except requests.RequestException as err:
        print("route_request_error--------")
        print(err)
        print("route_request_error--------")
        return build_route_error(f"AMap route request failed: {err}")

    try:
        data = res.json()
    except ValueError as err:
        print("route_json_error--------")
        print(err)
        print("route_json_error--------")
        return build_route_error("AMap route response is not valid JSON")

    print("data--------")
    print(data)
    print("data--------")

    if not isinstance(data, dict):
        return build_route_error("AMap route response has an invalid structure")

    status = data.get("status")
    if status not in ("1", 1):
        return build_route_error(
            data.get("info") or data.get("message") or "AMap route planning failed",
            int(status) if str(status).isdigit() else None,
        )

    route = data.get("route")
    if not isinstance(route, dict):
        return build_route_error("AMap route response did not include route data", int(status) if str(status).isdigit() else None)

    paths = route.get("paths", [])
    print("paths--------")
    print(paths)
    print("paths--------")
    if not isinstance(paths, list) or len(paths) < 1:
        return build_route_error("No route path was returned", int(status) if str(status).isdigit() else None)

    steps = paths[0].get("steps", [])
    print("steps--------")
    print(steps)
    print("steps--------")
    if not isinstance(steps, list) or len(steps) < 1:
        return build_route_error("No route steps were returned", int(status) if str(status).isdigit() else None)

    pl = []
    seen_points = set()
    for step in steps:
        polyline = step.get("polyline")
        if not polyline:
            continue
        for point in str(polyline).split(";"):
            lng_lat = [item.strip() for item in point.split(",")]
            if len(lng_lat) != 2:
                continue
            longitude, latitude = float(lng_lat[0]), float(lng_lat[1])
            point_key = (latitude, longitude)
            if point_key in seen_points:
                continue
            seen_points.add(point_key)
            pl.append({"latitude": latitude, "longitude": longitude})

    if len(pl) < 2:
        return build_route_error("Route polyline data is incomplete", int(status) if str(status).isdigit() else None)

    return json.dumps(
        {"points": pl, "type": "route_polyline", "day": day, "marker": markers},
        ensure_ascii=False,
    )
# 工具类型
class ToolInfo(TypedDict):
    tools_by_name: dict[str, BaseTool]
    llm_with_tools: Runnable[LanguageModelInput, BaseMessage]
    all_tools: list[BaseTool]


# 定义状态
class MessagesState(TypedDict):
    # 对话的数据类型：用户消息+模型回复+工具+提示词
    messages: Annotated[list[BaseMessage], add_messages]


# 定义模型节点
async def llm_call(state: MessagesState, prompt: str, tool_info: ToolInfo):
    """LLM decides whether to call a tool or not"""
    llm_with_tools = tool_info["llm_with_tools"]
    messages = [
                   SystemMessage(
                       content=prompt
                   )
               ] + state["messages"]

    response = await llm_with_tools.ainvoke(messages)
    return {'messages': [response]}


# 定义工具节点
async def tool_node(state: MessagesState, tool_info: ToolInfo):
    """Performs the tool call"""

    tools_by_name = tool_info["tools_by_name"]
    # 取对话里的最后一条
    last_message = state["messages"][-1]
    task = [
        tools_by_name[tool_call["name"]].ainvoke(tool_call['args']) for tool_call in last_message.tool_calls
    ]
    # 并发执行所有工具
    observations = await asyncio.gather(*task)
    tool_messages = [
        ToolMessage(content=observation, tool_call_id=tool_call["id"])
        for observation, tool_call in zip(observations, last_message.tool_calls)
    ]
    return {'messages': tool_messages}


# 定义结束逻辑
def should_continue(state: MessagesState):
    """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""

    messages = state["messages"]
    last_message = messages[-1]

    # If the LLM makes a tool call, then perform an action
    if last_message.tool_calls:
        return "tool_node"

    # Otherwise, we stop (reply to the user)
    return END


# 构建并编译agent，构建执行顺序
def build_state_graph(checkpointer: AsyncPostgresSaver, store: AsyncPostgresStore, prompt: str,
                      tool_info: ToolInfo):
    # Build workflow
    agent_builder = StateGraph(MessagesState)  # type: ignore
    # Add nodes
    agent_builder.add_node("llm_call", partial(llm_call, prompt=prompt, tool_info=tool_info))  # type: ignore
    agent_builder.add_node("tool_node", partial(safe_tool_node, tool_info=tool_info))  # type: ignore
    # Add edges to connect nodes
    agent_builder.add_edge(START, "llm_call")
    agent_builder.add_edge(START, "llm_call")
    agent_builder.add_conditional_edges(
        "llm_call",
        should_continue,
        ["tool_node", END]
    )

    agent_builder.add_edge("tool_node", "llm_call")

    # Compile the agent
    agent = agent_builder.compile(checkpointer=checkpointer,
                                  store=store,
                                  )
    return agent


# 获取全局缓存的工具数据(websocket专用)
def get_tool_list_ws(websocket: WebSocket) -> ToolInfo:
    tool_info = getattr(websocket.app.state, 'tool_cache', None)
    if tool_info is None:
        raise RuntimeError('工具数据未找到')
    return tool_info


# 获取全局缓存的工具数据(http专用)
def get_tool_list_http(request: Request) -> ToolInfo:
    tool_info = getattr(request.app.state, 'tool_cache', None)
    if tool_info is None:
        raise RuntimeError('工具数据未找到')
    return tool_info
