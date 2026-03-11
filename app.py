from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import base64
import os
import json

app = Flask(__name__)
CORS(app)  # 允许跨域，前端直接调用

# 从环境变量读取API密钥（安全）
client = OpenAI(
    api_key=os.environ.get("ERNIE_API_KEY", "your-api-key-here"),
    base_url="https://aistudio.baidu.com/llm/lmapi/v3"
)


@app.route('/')
def home():
    return "手写笔记助手API服务运行中..."


@app.route('/api/analyze', methods=['POST'])
def analyze_note():
    try:
        data = request.json
        image_base64 = data.get('image')
        prompt_type = data.get('type', 'general')  # 分析类型
        custom_prompt = data.get('prompt', '')

        # 根据类型选择系统提示词
        prompts = {
            'general': '请分析这张手写笔记图片，提取所有文字内容，整理成结构化的笔记格式。',
            'exam': '这是关于期末考试的笔记，请帮我整理考试题型、重点范围和复习建议。',
            'math': '这是数学笔记，请解析其中的公式和解题步骤，用LaTeX格式输出数学表达式。',
            'english': '这是英语笔记，请整理词汇、语法点和例句。',
            'structure': '请分析笔记的知识结构，生成思维导图大纲（Markdown列表格式）。'
        }

        system_prompt = prompts.get(prompt_type, prompts['general'])
        if custom_prompt:
            system_prompt = custom_prompt

        # 调用ERNIE-VL模型
        completion = client.chat.completions.create(
            model="ernie-4.5-vl-28b-a3b-thinking",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": system_prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                        }
                    ]
                }
            ],
            stream=False
        )

        response = completion.choices[0].message

        return jsonify({
            'success': True,
            'content': response.content,
            'reasoning': getattr(response, 'reasoning_content', ''),
            'type': prompt_type
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/export', methods=['POST'])
def export_note():
    """导出Markdown格式"""
    data = request.json
    content = data.get('content', '')
    title = data.get('title', '笔记导出')

    markdown = f"""# {title}

{content}

---
*由手写笔记助手生成 - 使用ERNIE-4.5-VL模型*
"""
    return jsonify({'markdown': markdown})


if __name__ == '__main__':
    app.run(debug=True, port=5000)