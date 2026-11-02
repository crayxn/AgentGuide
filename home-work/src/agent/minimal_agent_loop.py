import json
import os
from pyexpat.errors import messages

from openai import OpenAI
from dotenv import load_dotenv
from openai.resources.skills import content

load_dotenv(dotenv_path="../../../.env", override=True)

# tools
def get_weather(city:str) -> str:
    return f"{city}天气晴朗"

# register
tools_pool = {
    "get_weather": {
        "func": get_weather,
        "review": True
    }
}

tools = [
    {
        "type":"function",
        "function": {
            "name":"get_weather",
            "description": "获取某城市的天气",
            "parameters": {
                "type":"object",
                "properties":{
                    "city":{
                        "type":"string",
                        "description":"城市名称",
                    }
                },
                "required":["city"]
            },
        },
        "need_review": True
    }
]

# history
history = [{
    "role":"system",
    "content":"你是个人助手"
}]

llm = OpenAI(
    base_url="https://open.bigmodel.cn/api/coding/paas/v4",
    api_key="14dcf717b4824877b875b7b43b3f8a24.gyPVXDMqWu2FqlOj", #os.getenv("LLM_API_KEY")
)

history.append({
    "role":"user",
    "content":"珠海天气如何"
})
################
# loop
max_steps = 3
task = "珠海天气如何"
system_prompt = "你的一个人工助手"
state = {
    "task": "",
    "steps": [], #执行过程
    "artifacts": {},
    "final": False,
    "content": None
}

# 需要支持多 llm 类型
def llm_req(task, state, tools):
    result = {
        "tool_calls": [],
        "content": ""
    }
    # 暂时只支持 openai风格
    # 处理上下文
    messages = [{
        "role":"system",
        "content": system_prompt
    },{
        "role":"user",
        "content": task
    }]
    for step in state["steps"]:
        messages.append({
            "role":"tool",
            "content": json.dumps(step)
        })

    completion = llm.chat.completions.create(
        model=os.getenv("LLM_MODEL") or "glm-5.3-flash",
        messages=messages,
        tools=tools,
    )

    message = completion.choices[0].message
    if message.tool_calls:
        for tool_call in message.tool_calls:
            result["tool_calls"].append({
                "function":tool_call.function.name,
                "args": json.loads(tool_call.function.arguments)
            })

    return result

for step_id in range(max_steps):
    result = llm_req(task, state, tools)
    if len(result["tool_calls"]) == 0:
        state["final"] = True
        state["content"] = result["content"]
        break
    else:
        # 遍历请求
        for tool_call in result["tool_calls"]:
            tool_result = {
                "ok": False,
                "error": "Unknow error",
                "message": "",
                "data": None
            }
            print(tool_call)
            if tool_call["function"] not in tools_pool:
                tool_result["error"] = "Unknow Tool"

            tool = tools_pool[tool_call["function"]]
            # # 询问用户
            # if tool.review and not ask_human(tool):
            #     break
            try:
                tool_result["data"] = tool["function"](**tool_call.args)
                tool_result["ok"] = True
            except Exception as e:
                tool_result["error"] = str(e)

            state["steps"].append({
                **tool_call,
                **tool_result,
            })

if not state["final"]:
    state["content"] = "over max steps"

print(json.dumps(state))