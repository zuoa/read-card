import json
import os
from urllib.parse import unquote

import requests
import io
from PIL import Image, ImageDraw, ImageFont
import textwrap

from flask.cli import load_dotenv
from openai import OpenAI

load_dotenv()

def llm_chat(prompt):
    llm_base_url = os.environ.get('LLM_BASE_URL', 'https://api.deepseek.com/v1')
    llm_model_name = os.environ.get('LLM_MODEL_NAME', 'deepseek-chat')
    llm_api_key = os.environ.get('LLM_API_KEY', '')

    messages = []
    messages.append({"role": "user", "content": prompt})

    data = {
        "model": llm_model_name,
        "messages": messages,
        "stream": False
    }
    print(data)
    try:
        client = OpenAI(
            base_url=llm_base_url,
            api_key=llm_api_key,
        )

        chat_completion = client.chat.completions.create(**data)
        return chat_completion.choices[0].message.content

    except Exception as e:
        print(e)

    return ''

def get_markdown_from_url(url):
    """
    调用 Jina Reader API 获取指定 URL 的 markdown 内容。
    """
    # url decode
    url_decoded = unquote(url)

    reader_url = f"https://r.jina.ai/{url}"
    headers = {
        'Accept': 'text/markdown',
    }

    if '://mp.weixin.qq.com/' in url_decoded.lower():
        headers = {
            'Accept': 'text/markdown',
            'Authorization': f'Bearer {os.environ.get("JINA_READER_API_KEY", "")}',
            "X-Engine": "cf-browser-rendering"
        }

    try:
        resp = requests.get(reader_url, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"Jina Reader 获取失败: {e}")
        return ''

def extract_core_sentences_from_markdown(markdown_text, quote_number=3):
    """
    调用 LLM 提炼3句核心语句，返回list[str]。
    """
    prompt = f"""
你是一个内容摘要助手。请从以下markdown内容中，提炼出{quote_number}句最能代表原文核心思想的语句，要求保留原文,不要精简、不要添加解释。

## 任务要求
### 内容提取与呈现 (Card Content Extraction & Presentation)
1.  **精准核心语句提取**：
    * a. **核心语句选择**：从提供的文章中，智能识别并提取**不多于{quote_number}句**最能代表核心观点的句子。优先选择简洁、有力的表达。
    * b. **原文保留**：**严格保留核心语句的原文**，不进行任何形式的改写或总结。

2.  **双语对照（如适用）**：
    * 若原文为英文，务必在每个英文核心语句下方提供**精炼、准确、自然的简体中文翻译**。
    * 若原文为中文，务必在每个中文核心语句下方提供**精炼、准确、自然的英文翻译**。
"""
    prompt+= """\n\n
## 响应格式
以json列表格式返回，包含以下字段：text、translation。text字段为提炼的核心语句列表，translation字段为对应的翻译。
参考格式：[{"text": "核心语句1", "translation": "对应翻译1"}, {"text": "核心语句2", "translation": "对应翻译2"}, {"text": "核心语句3", "translation": "对应翻译3"}]

## 以下为原文内容
"""
    prompt += f"""\n\n
```
{markdown_text}
```

现在请根据以上内容，提炼出{quote_number}句核心语句，并返回json格式的结果。
"""
    result = llm_chat(prompt)
    # 按行分割，去除空行
    return json.loads(result)

def draw_sentences_image(sentences, width=720):
    """
    按指定样式绘制3句核心语句图片，宽度720px，返回BytesIO对象。
    """
    # 字体设置（可根据实际路径调整）
    font_path = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"  # macOS常见字体
    font_title = ImageFont.truetype(font_path, 36)
    font_body = ImageFont.truetype(font_path, 28)
    font_quote = ImageFont.truetype(font_path, 24)
    margin = 40
    line_spacing = 12
    block_spacing = 36
    bg_color = (250, 250, 250)
    fg_color = (40, 40, 40)
    quote_color = (120, 120, 120)
    # 预处理文本，分段
    blocks = []
    for s in sentences:
        blocks.append({
            'main': s,
            'quote': None
        })
    # 计算高度
    dummy_img = Image.new('RGB', (width, 1000))
    draw = ImageDraw.Draw(dummy_img)
    total_height = margin
    for block in blocks:
        main_lines = textwrap.wrap(block['main'], width=28)
        h_main = len(main_lines) * (font_body.size + line_spacing)
        h_quote = 0
        if block['quote']:
            quote_lines = textwrap.wrap(block['quote'], width=32)
            h_quote = len(quote_lines) * (font_quote.size + 2)
        total_height += h_main + h_quote + block_spacing
    total_height += margin
    # 创建图片
    img = Image.new('RGB', (width, total_height), bg_color)
    draw = ImageDraw.Draw(img)
    y = margin
    for block in blocks:
        main_lines = textwrap.wrap(block['main'], width=28)
        for line in main_lines:
            draw.text((margin, y), line, font=font_body, fill=fg_color)
            y += font_body.size + line_spacing
        if block['quote']:
            quote_lines = textwrap.wrap(block['quote'], width=32)
            for line in quote_lines:
                draw.text((margin+20, y), line, font=font_quote, fill=quote_color)
                y += font_quote.size + 2
        y += block_spacing
    # 保存到 BytesIO
    output = io.BytesIO()
    img.save(output, format='PNG')
    output.seek(0)
    return output


