import asyncio
import json
import os
import time
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

    def request_json_with_retry(url: str, params: dict[str, Any], retries: int = 3):
        last_error: Exception | None = None
        for attempt in range(retries):
            try:
                response = requests.get(url, params=params, timeout=15)
                response.raise_for_status()
                payload = response.json()
                if (
                    isinstance(payload, dict)
                    and str(payload.get("info", "")).upper() == "CUQPS_HAS_EXCEEDED_THE_LIMIT"
                    and attempt < retries - 1
                ):
                    time.sleep(0.5 * (attempt + 1))
                    continue
                return payload
            except (requests.RequestException, ValueError) as err:
                last_error = err
                if attempt < retries - 1:
                    time.sleep(0.5 * (attempt + 1))
                    continue
        raise last_error or RuntimeError("Unknown request error")

    def simplify_points(points: list[dict[str, float]], max_points: int = 800) -> list[dict[str, float]]:
        if len(points) <= max_points:
            return points
        if max_points < 2:
            return points[:1]
        sampled = [points[0]]
        span = len(points) - 1
        for i in range(1, max_points - 1):
            idx = round(i * span / (max_points - 1))
            sampled.append(points[idx])
        sampled.append(points[-1])
        return sampled

    def normalize_marker(marker: Any, index: int) -> dict[str, Any]:
        if not isinstance(marker, dict):
            return {
                "id": index + 1,
                "latitude": 0.0,
                "longitude": 0.0,
                "content": str(marker),
            }

        latitude = marker.get("latitude", marker.get("lat"))
        longitude = marker.get("longitude", marker.get("lon"))
        content = (
            marker.get("content")
            or marker.get("name")
            or marker.get("title")
            or marker.get("city")
            or f"Point {index + 1}"
        )
        marker_id = marker.get("id", index + 1)

        try:
            if latitude is None or longitude is None:
                geocoded = geocode_to_amap_location(str(content))
                lng, lat = geocoded.split(",")
                longitude = float(lng)
                latitude = float(lat)
            else:
                latitude = float(latitude)
                longitude = float(longitude)
        except Exception:
            latitude = 0.0
            longitude = 0.0

        return {
            "id": int(marker_id) if str(marker_id).isdigit() else index + 1,
            "latitude": latitude,
            "longitude": longitude,
            "content": str(content),
        }

    if not AMAP_WEB_SERVICE_KEY:
        return build_route_error("AMAP_WEB_SERVICE_KEY is not configured")

    def geocode_to_amap_location(location: str) -> str:
        geo_url = "https://restapi.amap.com/v3/geocode/geo"
        try:
            geo_data = request_json_with_retry(
                geo_url,
                {
                    "key": AMAP_WEB_SERVICE_KEY,
                    "address": location,
                },
            )
        except requests.RequestException as err:
            raise ValueError(f"Failed to geocode location: {location}, error: {err}") from err
        except ValueError as err:
            raise ValueError(f"Failed to parse geocode response for location: {location}") from err

        if not isinstance(geo_data, dict):
            raise ValueError(f"Invalid geocode response for location: {location}")

        if geo_data.get("status") not in ("1", 1):
            raise ValueError(
                geo_data.get("info")
                or geo_data.get("message")
                or f"Failed to geocode location: {location}"
            )

        geocodes = geo_data.get("geocodes", [])
        if not isinstance(geocodes, list) or len(geocodes) < 1:
            raise ValueError(f"No geocode result found for location: {location}")

        result_location = geocodes[0].get("location")
        if not result_location:
            raise ValueError(f"Geocode result has no coordinates for location: {location}")
        return str(result_location)

    def normalize_to_amap_location(location: str) -> str:
        parts = [item.strip() for item in location.split(",")]
        if len(parts) == 2:
            try:
                latitude, longitude = float(parts[0]), float(parts[1])
                return f"{longitude},{latitude}"
            except ValueError:
                pass
        return geocode_to_amap_location(location)

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
        data = request_json_with_retry(url, params)
    except requests.RequestException as err:
        print("route_request_error--------")
        print(err)
        print("route_request_error--------")
        return build_route_error(f"AMap route request failed: {err}")
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

    normalized_markers = [normalize_marker(marker, index) for index, marker in enumerate(markers or [])]
    normalized_markers = [
        marker for marker in normalized_markers
        if marker["latitude"] != 0.0 or marker["longitude"] != 0.0
    ]
    simplified_points = simplify_points(pl)

    return json.dumps(
        {"points": simplified_points, "type": "route_polyline", "day": day, "marker": normalized_markers},
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
