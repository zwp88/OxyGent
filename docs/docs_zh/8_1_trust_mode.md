# 如何获取智能体原始输出？

OxyGent提供了非常丰富的参数供您自定义智能体的工作模式，

如果您希望获取智能体的原始输出，只需将 trust_mode 设置为 True。启用信任模式后，智能体会直接返回工具的执行结果，而不是对其进行额外的处理或解析。

```python
    oxy.ReActAgent(
        name="trust_agent",
        desc="a time query agent with trust mode enabled",
        tools=["time"],
        llm_model="default_llm",
        trust_mode=True,  # enable trust mode
        is_master=True,
    ),
```

例如，启用信任模式时，返回的原始输出可能如下所示：

```
trust mode output: Tool [get_current_time] execution result: {
  "timezone": "Asia/Shanghai",
  "datetime": "2025-07-24T20:26:19+08:00",
  "is_dst": false
}
```

## 完整的可运行样例

以下是可运行的完整代码示例：

```python
import asyncio
from oxygent import MAS, oxy
from oxygent.utils.env_utils import get_env_var

oxy_space = [
    # LLM configuration
    oxy.HttpLLM(
        name="default_llm",
        api_key=get_env_var("DEFAULT_LLM_API_KEY"),
        base_url=get_env_var("DEFAULT_LLM_BASE_URL"),
        model_name=get_env_var("DEFAULT_LLM_MODEL_NAME"),
        llm_params={"temperature": 0.01},
        semaphore=4,
    ),
    # time tool
    oxy.StdioMCPClient(
        name="time",
        params={
            "command": "uvx",
            "args": ["mcp-server-time", "--local-timezone=Asia/Shanghai"],
        },
    ),
    # normal mode ReActAgent
    oxy.ReActAgent(
        name="normal_agent",
        desc="a time query agent with trust mode disabled",
        tools=["time"],
        llm_model="default_llm",
        trust_mode=False,  # disable trust mode
    ),
    # trust mode ReActAgent
    oxy.ReActAgent(
        name="trust_agent",
        desc="a time query agent with trust mode enabled",
        tools=["time"],
        llm_model="default_llm",
        trust_mode=True,  # enable trust mode
        is_master=True,
    ),
]


async def main():
    async with MAS(oxy_space=oxy_space) as mas:
        query = "What is the current time"

        print("=== normal mode test ===")
        normal_result = await mas.call("normal_agent", {"query": query})
        print(f"normal mode output: {normal_result}")

        print("\n=== trust mode test ===")
        trust_result = await mas.call("trust_agent", {"query": query})
        print(f"trust mode output: {trust_result}")


if __name__ == "__main__":
    asyncio.run(main())

```

[上一章：并行调用agent](./7_parallel.md)
[下一章：处理查询和提示词](./8_update_prompts.md)
[回到首页](./readme.md)