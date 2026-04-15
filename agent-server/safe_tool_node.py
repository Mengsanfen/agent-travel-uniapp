import asyncio
import json
from typing import Any

from langchain_core.messages import ToolMessage


def _parse_json_if_possible(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _summarize_tool_output(tool_name: str, observation: Any) -> tuple[str, Any, str]:
    if isinstance(observation, Exception):
        message = f"Tool {tool_name} failed: {observation}"
        return message, str(observation), "error"

    artifact = observation
    parsed = _parse_json_if_possible(observation)

    if tool_name == "map_data" and isinstance(parsed, dict):
        route_type = parsed.get("type")
        day = str(parsed.get("day") or "").strip()
        day_prefix = f"{day}: " if day else ""
        if route_type == "route_polyline":
            points = len(parsed.get("points") or [])
            markers = len(parsed.get("marker") or [])
            return (
                f"{day_prefix}Route map generated. Points: {points}. Markers: {markers}.",
                artifact,
                "success",
            )
        if route_type == "route_error":
            error_message = parsed.get("message") or "Route map generation failed"
            return (
                f"{day_prefix}Route map failed: {error_message}",
                artifact,
                "error",
            )

    content = str(observation)
    if len(content) > 1200:
        content = content[:1200] + "...(truncated)"
    return content, artifact, "success"


async def safe_tool_node(state, tool_info):
    tools_by_name = tool_info["tools_by_name"]
    last_message = state["messages"][-1]
    task = []
    runnable_tool_calls = []
    tool_messages = []

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool = tools_by_name.get(tool_name)
        if tool is None:
            tool_messages.append(
                ToolMessage(
                    content=f"Tool {tool_name} is unavailable.",
                    tool_call_id=tool_call["id"],
                    name=tool_name,
                    artifact=f"Tool {tool_name} is unavailable",
                    status="error",
                )
            )
            continue

        runnable_tool_calls.append(tool_call)
        task.append(tool.ainvoke(tool_call["args"]))

    observations = await asyncio.gather(*task, return_exceptions=True)
    for observation, tool_call in zip(observations, runnable_tool_calls):
        tool_name = tool_call["name"]
        content, artifact, status = _summarize_tool_output(tool_name, observation)
        tool_messages.append(
            ToolMessage(
                content=content,
                tool_call_id=tool_call["id"],
                name=tool_name,
                artifact=artifact,
                status=status,
            )
        )

    return {"messages": tool_messages}
