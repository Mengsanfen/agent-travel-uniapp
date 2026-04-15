import asyncio

from langchain_core.messages import ToolMessage


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
                    content=f"工具 {tool_name} 当前不可用，请直接回答用户并说明相关实时能力暂时不可用。",
                    tool_call_id=tool_call["id"],
                    name=tool_name,
                )
            )
            continue

        runnable_tool_calls.append(tool_call)
        task.append(tool.ainvoke(tool_call["args"]))

    observations = await asyncio.gather(*task, return_exceptions=True)
    for observation, tool_call in zip(observations, runnable_tool_calls):
        tool_name = tool_call["name"]
        content = (
            f"工具 {tool_name} 调用失败: {observation}"
            if isinstance(observation, Exception)
            else observation
        )
        tool_messages.append(
            ToolMessage(
                content=content,
                tool_call_id=tool_call["id"],
                name=tool_name,
            )
        )

    return {"messages": tool_messages}
