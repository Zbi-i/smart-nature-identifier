import torch
from torchvision import models, transforms
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import io
import json
import os
from dotenv import load_dotenv
import requests
import re
import base64
import traceback
import asyncio;
import edge_tts;
import cn2an
from ddgs import DDGS

app = Flask(__name__)
CORS(app)

# --- 1. ResNet-101 + GPU 配置 ---
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"检测到硬件加速: {device}")
model = models.resnet101(weights='DEFAULT').to(device)
model.eval()
preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])
with open('labels.json', 'r') as f:
    labels = json.load(f)
print("模型加载完毕。")

load_dotenv()
BAIDU_API_KEY = os.getenv("BAIDU_API_KEY")
BAIDU_SECRET_KEY = os.getenv("BAIDU_SECRET_KEY")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_API_URL = os.getenv("LLM_API_URL")

def get_baidu_token():
    url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={BAIDU_API_KEY}&client_secret={BAIDU_SECRET_KEY}"
    res = requests.post(url).json()
    return res.get("access_token")

def baidu_identify(image_bytes):
    print(">>> 本地识别度低，正在请求云端增强识别...")
    base64_img = base64.b64encode(image_bytes).decode('utf-8')
    token = get_baidu_token()
    url = f"https://aip.baidubce.com/rest/2.0/image-classify/v2/advanced_general?access_token={token}"
    res = requests.post(url, data={'image': base64_img}, headers={'Content-Type': 'application/x-www-form-urlencoded'}).json()
    if res.get('result'):
        top = res['result'][0]
        return top['keyword'], top['score'], "云端增强(百度AI)"
    return None, 0, "识别失败"

# --- 3. 识别接口 ---
@app.route('/api/identify', methods=['POST'])
def identify():
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': 'No image'}), 400
    file = request.files['image']
    img_bytes = file.read()
    try:
        img = Image.open(io.BytesIO(img_bytes)).convert('RGB')
        img_tensor = preprocess(img).unsqueeze(0).to(device)
        with torch.no_grad():
            outputs = model(img_tensor)
        probs = torch.nn.functional.softmax(outputs[0], dim=0)
        score, idx = torch.max(probs, 0)
        local_name = labels[idx.item()]
        local_score = score.item()
        if local_score < 0.60:
            cloud_name, cloud_score, source = baidu_identify(img_bytes)
            if cloud_name:
                return jsonify({'success': True, 'name': cloud_name, 'score': cloud_score, 'source': source})
        return jsonify({'success': True, 'name': local_name, 'score': local_score, 'source': "本地高精度模型(ResNet-101)"})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# --- 4. 升级版 “探索发现” 接口 (Pixabay 版) ---
@app.route('/api/recommendations', methods=['GET'])
def get_recommendations():
    try:
        # 1. 调用大模型获取名称 (保持之前的中英双语 Prompt)
        print("步骤1: 调用大模型获取推荐...")
        llm_prompt = {
            "model": "deepseek-v3-2-251201",
            "messages": [{
                "role": "user", 
                "content": "请随机生成3个动植物名称。按JSON返回：{\"recommendations\": [{\"cn\":\"\", \"en\":\"\"}, ...]}"
            }],
            "stream": False
        }
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {LLM_API_KEY}'}
        response = requests.post(LLM_API_URL, json=llm_prompt, headers=headers)
        
        content_str = response.json()['choices'][0]['message']['content']
        json_match = re.search(r'\{.*\}', content_str, re.DOTALL)
        if json_match: content_str = json_match.group(0)
        
        items = json.loads(content_str)['recommendations']
        print(f"获取名称成功: {items}")

        # 2. 调用 Pixabay 获取图片
        print("步骤2: 开始从 Pixabay 获取高质图片...")
        recommendations_with_images = []
        
        for item in items:
            cn_name = item['cn']
            en_name = item['en']
            
            try:
                # 🌟 调用 Pixabay API
                # q: 搜索关键词, image_type: 只要照片, safesearch: 开启安全搜索
                pix_url = f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q={en_name.replace(' ', '+')}&image_type=photo&safesearch=true&per_page=3"
                
                pix_res = requests.get(pix_url, timeout=5).json()
                
                if pix_res.get('hits') and len(pix_res['hits']) > 0:
                    # 取第一张最相关的图片，使用 webformatURL (尺寸适中)
                    img_url = pix_res['hits'][0]['webformatURL']
                    recommendations_with_images.append({'name': cn_name, 'imageUrl': img_url})
                    print(f"Pixabay 成功: {cn_name} -> {img_url}")
                else:
                    raise Exception("Pixabay no results")
                    
            except Exception as e:
                print(f"Pixabay 搜索 {cn_name} 失败: {e}，使用终极备用图")
                # 🌟 终极兜底：如果 API 坏了，直接给一个 Unsplash 的图片链接，让前端去重定向
                # 这个链接几乎 100% 能生成出图片
                fallback_url = f"https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?fit=crop&w=500&q=80"
                recommendations_with_images.append({'name': cn_name, 'imageUrl': fallback_url})
        
        return jsonify({'success': True, 'data': recommendations_with_images})

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': '推荐模块暂时维护中'}), 500

# --- 5. TTS 接口 ---
@app.route('/api/tts', methods=['POST'])
def tts_generate():
    data = request.json
    text = data.get('text', '')
    
    if not text:
        return jsonify({'success': False, 'message': 'No text'}), 400

    # -----------------------------------------------------------
    # 🌟 第一步：优先处理数字范围
    # -----------------------------------------------------------
    try:
        # 将 "2-5" 替换为 "2 到 5" (加空格有助于语音停顿和转换准确性)
        text = re.sub(r'(\d+)\s*[-~]\s*(\d+)', r'\1 到 \2', text)
    except Exception:
        pass

    # -----------------------------------------------------------
    # 🌟 第二步：清洗 Markdown 和 表情
    # -----------------------------------------------------------
    # 1. 移除 Markdown 符号 (*, #, >, `) - 不移除减号
    clean_text = re.sub(r'[*#>`]', '', text)
    
    # # 2. 移除 Emoji
    # 注意：这个正则表达式覆盖了大部分常见的 Emoji，但会替换掉数字暂不使用
    # emoji_pattern = re.compile(
    #     "["
    #     "\U00010000-\U0010ffff"
    #     "\u2600-\u27bf"
    #     "\u1f300-\u1f64f"c
    #     "\u1f680-\u1f6ff"
    #     "]+", flags=re.UNICODE)
    # clean_text = emoji_pattern.sub('', clean_text)
    
    # 3. 移除多余空白
    clean_text = clean_text.replace('\n', ' ').strip()

    # -----------------------------------------------------------
    # 🌟 第三步：数字转中文 (cn2an)
    # -----------------------------------------------------------
    try:
        clean_text = cn2an.transform(clean_text, "an2cn")
    except Exception as e:
        print(f"数字转换忽略: {e}")

    # -----------------------------------------------------------
    # 🌟 第四步：生成音频
    # -----------------------------------------------------------
    print(f"TTS文本: {clean_text[:60]}...") # 打印日志检查一下

    VOICE = "zh-CN-XiaoxiaoNeural"
    OUTPUT_FILE = "tts_output.mp3"

    async def _run_tts():
        communicate = edge_tts.Communicate(clean_text, VOICE)
        await communicate.save(OUTPUT_FILE)

    try:
        asyncio.run(_run_tts())
        with open(OUTPUT_FILE, "rb") as audio:
            audio_data = audio.read()
        return base64.b64encode(audio_data).decode('utf-8')
    except Exception as e:
        print(f"TTS Error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)