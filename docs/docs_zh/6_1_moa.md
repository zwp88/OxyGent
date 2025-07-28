# 如何快速复制多个智能体？

如果您需要生成多个相同的智能体，您可以使用`team_size`参数快速复制智能体。

```
    oxy.ReActAgent(
        name="time_agent",
        desc="A tool for time query",
        tools=["time"],
        llm_model="default_llm",
        team_size=2,
    ),
```

`team_size`目前仅能复制较为简单的智能体，之后我们会支持更完备的智能体复制。