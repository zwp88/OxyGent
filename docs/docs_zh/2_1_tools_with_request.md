# 如何使用工具操作智能体？

在OxyGent中，智能体之间使用`oxy.OxyRequest`和`oxy.OxyResponse`交流，因此您可以在工具中传入相关对象来访问或操作智能体。

例如，您可以使用以下的工具让智能体输出自己的节点信息：

```python
# in request_tools.py
from oxygent.oxy import FunctionHub
from pydantic import Field
from oxygent.schemas import OxyRequest

request_tools = FunctionHub(name="request_tools")


@request_tools.tool(description="A tool that can access the request context.")
def advanced_tool(
    query: str = Field(description="The user query"),
    oxy_request: OxyRequest = Field(description="The request context"), # 关键参数
) -> str:
    trace_id = oxy_request.current_trace_id
    shared_data = oxy_request.shared_data
    caller = oxy_request.caller
    node_id = oxy_request.node_id

    result = {
        "message": f"Successfully accessed request context for query: '{query}'",
        "trace_id": trace_id,
        "node_id": node_id,
        "caller": caller,
        "shared_data": shared_data,
        "demo_status": "SUCCESS - OxyRequest parameter working correctly!",
    }

    return f"CONTEXT ACCESS DEMO RESULT:\n{result}"

```

然后使用合适的agent调用这个工具：

```python
oxy_space = [
    oxy.HttpLLM(
        name="default_llm",
        api_key=os.getenv("DEFAULT_LLM_API_KEY"),
        base_url=os.getenv("DEFAULT_LLM_BASE_URL"),
        model_name=os.getenv("DEFAULT_LLM_MODEL_NAME"),
        llm_params={"temperature": 0.01},
        semaphore=4,
    ),
    request_tools,
    oxy.ReActAgent(
        name="request_agent",
        desc="A tool that can access request context and demonstrate oxy_request functionality",
        tools=["advanced_tool"],
    ),
    oxy.ReActAgent(
        is_master=True,
        name="master_agent",
        sub_agents=["request_agent"],
    ),
]
```

`ReActAgent`就能输出自己所在节点的信息。