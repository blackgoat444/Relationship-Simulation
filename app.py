# -*- coding: utf-8 -*-
import streamlit as st
import dashscope
from dashscope import Generation

# ===== 1. API Key =====
dashscope.api_key = st.secrets["DASHSCOPE_API_KEY"]

# ===== 2. 页面基础设置 =====
st.set_page_config(
    page_title="AI关系模拟器",
    page_icon="💬",
    layout="centered"
)

st.title("AI关系模拟器")
st.caption("选择角色、调整性格，然后输入你想说的话，看看对方会如何回应。")

# 调试用：验证页面中文本身没问题
st.write("中文页面测试：你好")

# ===== 3. 工具函数：把数值转成自然语言 =====
def level_text(value, low_text, mid_text, high_text):
    if value <= 3:
        return low_text
    elif value <= 7:
        return mid_text
    else:
        return high_text

# ===== 4. 角色选择 =====
role = st.selectbox(
    "选择对话对象",
    ["老师", "领导", "同学", "朋友", "恋人", "亲戚", "父母"]
)

# ===== 5. 性格参数 =====
st.subheader("调整人物性格")

intimacy = st.slider("亲密度", 0, 10, 5)
emotion = st.slider("情绪稳定性", 0, 10, 5)
style = st.slider("表达风格（越高越委婉）", 0, 10, 5)
control = st.slider("控制欲", 0, 10, 5)
support = st.slider("支持度", 0, 10, 5)

traits = {
    "亲密度": level_text(intimacy, "较低", "中等", "较高"),
    "情绪稳定性": level_text(emotion, "容易情绪化", "一般", "较稳定"),
    "表达风格": level_text(style, "直接", "正常", "委婉"),
    "控制欲": level_text(control, "较弱", "中等", "较强"),
    "支持度": level_text(support, "较低", "一般", "较高"),
}

# ===== 6. 初始化会话状态 =====
if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_role" not in st.session_state:
    st.session_state.last_role = role

if "last_traits" not in st.session_state:
    st.session_state.last_traits = traits.copy()

# 角色或性格变化时，清空对话，避免串戏
if st.session_state.last_role != role or st.session_state.last_traits != traits:
    st.session_state.messages = []
    st.session_state.last_role = role
    st.session_state.last_traits = traits.copy()

# ===== 7. 构造系统提示词（先用简化版，便于排查编码问题） =====
def build_system_prompt(role_name, traits_dict):
    return f"""
你现在扮演{role_name}。

性格如下：
亲密度：{traits_dict["亲密度"]}
情绪稳定性：{traits_dict["情绪稳定性"]}
表达风格：{traits_dict["表达风格"]}
控制欲：{traits_dict["控制欲"]}
支持度：{traits_dict["支持度"]}

请保持角色一致，用自然、简短、中文口语化的方式回复。
不要说自己是AI，不要解释设定。
回复控制在1到3句话。
"""

# ===== 8. 调用大模型 =====
def get_ai_reply(user_text, role_name, traits_dict, history):
    system_prompt = build_system_prompt(role_name, traits_dict)

    messages = [{"role": "system", "content": str(system_prompt)}]
    messages.extend(history)
    messages.append({"role": "user", "content": str(user_text)})

    print("===== 调用前检查 =====")
    print("user_text repr:", repr(user_text))
    print("system_prompt repr:", repr(system_prompt))
    print("messages repr:", repr(messages))

    try:
        response = Generation.call(
            model="qwen-turbo",
            messages=messages,
            result_format="message"
        )

        print("===== API返回 =====")
        print("status_code:", getattr(response, "status_code", None))
        print("response repr:", repr(response))

        if response.status_code == 200 and response.output:
            print("===== 开始读取 output =====")
            print("response.output repr:", repr(response.output))
            print("response.output.choices repr:", repr(response.output.choices))

            reply = response.output.choices[0].message.content
            print("reply repr:", repr(reply))

            return str(reply).strip()
        else:
            print("===== 调用失败对象 =====")
            print(repr(response))
            return "模型调用失败，请稍后重试"

    except Exception as e:
        print("===== 捕获到异常 =====")
        print("异常类型:", type(e))
        print("异常详情 repr:", repr(e))
        return "调用失败，请稍后重试"

# ===== 9. 展示当前角色摘要 =====
with st.expander("当前人物设定", expanded=False):
    st.write(f"**角色：** {role}")
    for k, v in traits.items():
        st.write(f"- {k}：{v}")

# ===== 10. 对话展示 =====
st.subheader("对话区")

for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message("assistant"):
            st.write(msg["content"])

# ===== 11. 用户输入 =====
user_input = st.chat_input("输入你想说的话...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": str(user_input)})

    history_for_model = st.session_state.messages[:-1]

    reply = get_ai_reply(user_input, role, traits, history_for_model)

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()

# ===== 12. 操作按钮 =====
col1, col2 = st.columns(2)

with col1:
    if st.button("撤回上一轮"):
        if len(st.session_state.messages) >= 2:
            st.session_state.messages = st.session_state.messages[:-2]
            st.rerun()

with col2:
    if st.button("清空对话"):
        st.session_state.messages = []
        st.rerun()
