# 如何修改记忆节点？

OxyGent支持读取记忆及重新执行功能。您可以在`chat_with_agent`方法中指定要访问的节点，您可以修改节点内容并从被修改的节点开始重新运行系统。

```python
async def main():
    async with MAS(oxy_space=oxy_space) as mas:
        # 第一次运行
        payload = {
            "query": "Get what time it is in America/New_York and save in `log.txt` under `./local_file`",
        }
        # 第二次运行
        payload = {
            "query": "Get what time it is in America/New_York and save in `log.txt` under `./local_file`",  
            "from_trace_id": "",
            "reference_trace_id": "CVu84yL8jbk3UwT6",  #修改为真实的trace编号
            "restart_node_id": "gn7YBoKeTxr439ps", #修改为真实的节点编号
            "restart_node_output": """{ 
                "timezone": "America/New_York",
                "datetime": "2024-07-21T05:32:43-04:00",
                "is_dst": true
            }""", #要修改的输出
        }
        oxy_response = await mas.chat_with_agent(payload=payload)
        from_trace_id = oxy_response.oxy_request.current_trace_id
        print("LLM: ", oxy_response.output, from_trace_id)
```

重新运行之后，系统的输出将会是您设定的`2024-07-21T05:32:43-04:00`。

您也可以在可视化界面进行详细调试和重新运行。
