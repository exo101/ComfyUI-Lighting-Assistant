import os
import sys
import requests
import base64
import json
from typing import Dict, List, Tuple, Optional

script_directory = os.path.dirname(os.path.abspath(__file__))
images_directory = os.path.join(script_directory, "images")

DEFAULT_LLAMACPP_URL = "http://localhost:8082"

DEFAULT_LIGHTING_ANALYSIS_PROMPT = """你是一位专业的摄影打光分析师。请分析这张图片的打光方式和整体氛围感，并生成适合 Stable Diffusion 使用的纯中文打光关键词。

请按以下格式输出，**分析内容要精炼，只保留关键信息，去除废话描写**：

## 打光分析

### 1. 主光方向
[精炼描述，如：轮廓光和背光，勾勒角色边缘]

### 2. 光线质量
[精炼描述，如：混合光效，边缘锐利，强烈光泽感]

### 3. 光影效果
[精炼描述，如：强烈明暗对比，体积光效果]

### 4. 光线颜色
[精炼描述，如：暖色与冷色交织，金黄色与白色/淡青色]

### 5. 特殊光效
[精炼描述，如：丁达尔效应，光晕和辉光效果]

### 6. 氛围感
[精炼描述，如：神圣、庄严、梦幻]

## 打光关键词（Prompt）

请生成适合 Stable Diffusion 使用的纯中文打光关键词，用逗号分隔，格式如下：

```
正面光，轮廓光，硬光，体积光，暖光，冷光，丁达尔光，光晕，梦幻光，神秘光
```

关键词应包含：
- 光源方向：如 "正面光，侧面光，逆光，侧逆光，轮廓光，伦勃朗光"
- 光线质量：如 "硬光，柔光，聚光，锐利高光"
- 光影效果：如 "体积光，戏剧阴影，高对比"
- 光线颜色：如 "暖光，冷光，金黄光，霓虹光"
- 特殊效果：如 "丁达尔光，光晕，辉光，魔法光"
- 氛围感：如 "梦幻光，神秘光，神圣光，电影光"

请确保关键词简洁、专业、适合 AI 绘画使用，使用纯中文关键词。"""

DEFAULT_IMAGE_DESCRIPTION_PROMPT = """你是一位专业的图片描述专家。请详细描述这张图片的内容，生成适合 Stable Diffusion 使用的纯中文提示词。

请按以下格式输出：

## 图片描述

### 主体内容
[描述图片中的主要人物、物体或场景]

### 环境背景
[描述背景环境、地点、时间]

### 构图视角
[描述拍摄角度、构图方式]

### 风格质感
[描述艺术风格、画面质感]

## 提示词（Prompt）

请生成适合 Stable Diffusion 使用的纯中文提示词，用逗号分隔，格式如下：

```
一位穿着华丽金色铠甲的女性战士，站在神圣的祭坛前，发光的魔法光环，丁达尔光效，电影级画质，8k分辨率
```

提示词应包含：
- 主体描述：人物特征、服装、动作、表情
- 环境元素：背景、建筑、自然景观
- 风格标签：艺术风格、画质描述、渲染引擎
- 氛围情感：整体氛围、情绪表达

请确保提示词详细、丰富、适合 AI 绘画使用，使用纯中文。"""

LIGHT_DIRECTIONS = {
    "正面光": {
        "keywords": "正面光，平光",
        "description": "光源在相机正后方，直接照射主体，阴影最少，适合展现细节但缺乏立体感"
    },
    "侧面光": {
        "keywords": "侧面光，侧向打光",
        "description": "光源在主体侧面，产生明显的明暗分界，增强立体感和质感"
    },
    "侧逆光": {
        "keywords": "侧逆光，轮廓光",
        "description": "光源在主体侧后方，勾勒出主体轮廓边缘，分离主体与背景"
    },
    "正逆光": {
        "keywords": "逆光，剪影光",
        "description": "光源在主体正后方，形成剪影或轮廓光效果"
    },
    "顶光": {
        "keywords": "顶光，蝴蝶光",
        "description": "光源从正上方照射，在眼窝和下巴下方产生阴影"
    },
    "底光": {
        "keywords": "底光",
        "description": "光源从下方照射，常用于恐怖或神秘场景"
    },
    "伦勃朗光": {
        "keywords": "伦勃朗光，三角光",
        "description": "经典人像布光，在阴影侧脸颊形成三角形光斑"
    },
    "蝴蝶光": {
        "keywords": "蝴蝶光",
        "description": "顶光变体，在鼻子下方形成蝴蝶形阴影"
    },
    "分割光": {
        "keywords": "分割光",
        "description": "光源在侧面90度，将脸部分成明暗两半"
    },
    "环形光": {
        "keywords": "环形光",
        "description": "侧光变体，在鼻子阴影侧形成小环状阴影"
    }
}

LIGHT_QUALITY = {
    "硬光": {
        "keywords": "硬光，锐利阴影",
        "description": "直射光，阴影边缘清晰锐利，对比强烈"
    },
    "柔光": {
        "keywords": "柔光，柔和光照",
        "description": "经过漫射的光，阴影边缘柔和模糊"
    },
    "漫射光": {
        "keywords": "漫射光，阴天光",
        "description": "经过大面积漫射的光，几乎没有阴影"
    },
    "聚光": {
        "keywords": "聚光，聚光灯",
        "description": "集中照射的光束，强调特定区域"
    }
}

LIGHT_COLOR = {
    "暖光": {
        "keywords": "暖光，金色光",
        "description": "偏黄/橙色的光，营造温暖氛围"
    },
    "冷光": {
        "keywords": "冷光，蓝色调",
        "description": "偏蓝/青色的光，营造冷静氛围"
    },
    "中性光": {
        "keywords": "中性光，白色光",
        "description": "接近白色的平衡光"
    },
    "黄金时刻": {
        "keywords": "黄金时刻，日落光",
        "description": "日落前后的温暖光线"
    },
    "蓝色时刻": {
        "keywords": "蓝色时刻，暮光",
        "description": "日落后天空的蓝色光线"
    },
    "霓虹光": {
        "keywords": "霓虹光，赛博朋克光",
        "description": "霓虹灯的多彩光线"
    },
    "烛光": {
        "keywords": "烛光",
        "description": "烛火的温暖摇曳光线"
    },
    "月光": {
        "keywords": "月光，银白月光",
        "description": "月亮的冷色光线"
    }
}

SPECIAL_EFFECTS = {
    "丁达尔光": {
        "keywords": "丁达尔光，光束",
        "description": "光线穿过介质形成的光束效果"
    },
    "光晕": {
        "keywords": "光晕，镜头光晕",
        "description": "强光进入镜头产生的光晕效果"
    },
    "体积光": {
        "keywords": "体积光，雾气光",
        "description": "在雾气或灰尘中可见的光束"
    },
    "轮廓光": {
        "keywords": "轮廓光，边缘光",
        "description": "勾勒主体轮廓的光线"
    },
    "电影光": {
        "keywords": "电影光",
        "description": "电影级别的专业布光"
    },
    "舞台光": {
        "keywords": "舞台光，聚光灯",
        "description": "舞台表演用的聚光效果"
    }
}

ATMOSPHERE = {
    "神秘": {
        "keywords": "神秘光，忧郁光，诡异光，神秘氛围",
        "description": "神秘的氛围"
    },
    "浪漫": {
        "keywords": "浪漫光，梦幻柔光，温馨光，甜蜜氛围",
        "description": "浪漫温馨"
    },
    "恐怖": {
        "keywords": "恐怖光照，阴森光，诡异光，恐怖氛围",
        "description": "恐怖阴森"
    },
    "科幻": {
        "keywords": "科幻光照，未来光，科技光，未来感",
        "description": "科幻未来感"
    },
    "复古": {
        "keywords": "复古光，老电影感，怀旧光，经典光效",
        "description": "复古怀旧"
    },
    "梦幻": {
        "keywords": "梦幻光，仙境光，童话光，魔法光，飘渺光",
        "description": "梦幻仙境"
    }
}

LIGHTING_PREVIEW_IMAGES = {
    "正面光": "正面光.png",
    "侧面光": "侧面光.png",
    "侧逆光": "侧逆光.png",
    "正逆光": "正逆光.png",
    "顶光": "顶光.png",
    "底光": "底光.png",
    "伦勃朗光": "伦勃朗光.png",
    "蝴蝶光": "蝴蝶光.png",
    "分割光": "分割光.png",
    "环形光": "轮毂光.png",
    "硬光": "硬光.png",
    "柔光": "柔光.png",
    "漫射光": "漫反射光.png",
    "聚光": "聚光.png",
    "暖光": "暖光.png",
    "冷光": "冷光.png",
    "中性光": "中性光.png",
    "黄金时刻": "黄金时刻.png",
    "蓝色时刻": "蓝色时刻.png",
    "霓虹光": "霓虹光.png",
    "烛光": "烛光.png",
    "月光": "月光.png",
    "丁达尔光": "丁达尔光.png",
    "光晕": "光晕.png",
    "体积光": "体积光.png",
    "轮廓光": "侧逆光.png",
    "电影光": "电影光照.png",
    "舞台光": "舞台光.png",
    "神秘": "神秘.png",
    "浪漫": "浪漫.png",
    "恐怖": "恐怖.png",
    "科幻": "科技.png",
    "复古": "复古.png",
    "梦幻": "梦幻.png",
}

def encode_image_to_base64(image_path: str) -> Optional[str]:
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        return None

def analyze_lighting_with_llamacpp(
    image_path: str,
    prompt: str,
    model: str = "local-model",
    llamacpp_host: str = DEFAULT_LLAMACPP_URL,
    timeout: int = 120
) -> Dict:
    try:
        image_base64 = encode_image_to_base64(image_path)
        if not image_base64:
            return {"success": False, "analysis": "图片编码失败", "keywords": ""}

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]
            }
        ]

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "temperature": 0.7,
            "max_tokens": 2000
        }

        response = requests.post(
            f"{llamacpp_host.rstrip('/')}/v1/chat/completions",
            json=payload,
            timeout=timeout
        )
        response.raise_for_status()

        result = response.json()

        if "choices" in result and len(result["choices"]) > 0:
            analysis_text = result["choices"][0]["message"]["content"]
            return {
                "success": True,
                "analysis": analysis_text,
                "model": model,
                "image_path": image_path
            }
        else:
            return {
                "success": False,
                "analysis": "响应格式异常",
                "keywords": ""
            }

    except requests.exceptions.ConnectionError as e:
        return {"success": False, "analysis": f"无法连接到 llama.cpp 服务\n请检查服务是否启动，地址是否正确: {llamacpp_host}", "keywords": ""}
    except requests.exceptions.Timeout:
        return {"success": False, "analysis": f"请求超时（{timeout}秒）", "keywords": ""}
    except Exception as e:
        return {"success": False, "analysis": f"分析出错：{str(e)}", "keywords": ""}

def get_llamacpp_models(llamacpp_host: str = DEFAULT_LLAMACPP_URL) -> List[str]:
    try:
        models_url = f"{llamacpp_host.rstrip('/')}/v1/models"
        response = requests.get(models_url, timeout=10)
        response.raise_for_status()

        data = response.json()
        models = []

        if "models" in data and isinstance(data["models"], list):
            for m in data["models"]:
                if isinstance(m, dict):
                    if "id" in m:
                        models.append(m["id"])
                    elif "name" in m:
                        models.append(m["name"])
                elif isinstance(m, str):
                    models.append(m)

        if "data" in data and isinstance(data["data"], list):
            for m in data["data"]:
                if isinstance(m, dict):
                    if "id" in m:
                        models.append(m["id"])
                    elif "name" in m:
                        models.append(m["name"])

        return list(set(models)) if models else []
    except Exception:
        return []

def extract_keywords_from_analysis(analysis_text: str) -> str:
    try:
        if "```" in analysis_text:
            parts = analysis_text.split("```")
            for i, part in enumerate(parts):
                if i % 2 == 1:
                    lines = part.strip().split('\n')
                    if lines[0] in ['python', 'text', 'plaintext', '']:
                        keywords = '\n'.join(lines[1:])
                    else:
                        keywords = part.strip()
                    return keywords.strip()

        extracted_keywords = []
        analysis_text_lower = analysis_text.lower()

        for name, data in LIGHT_DIRECTIONS.items():
            if name in analysis_text:
                extracted_keywords.extend(data["keywords"].split("，"))

        for name, data in LIGHT_QUALITY.items():
            if name in analysis_text:
                extracted_keywords.extend(data["keywords"].split("，"))

        for name, data in LIGHT_COLOR.items():
            if name in analysis_text or (name == "暖光" and ("暖色" in analysis_text or "金黄" in analysis_text)) or (name == "冷光" and ("冷色" in analysis_text or "淡青" in analysis_text)):
                extracted_keywords.extend(data["keywords"].split("，"))

        for name, data in SPECIAL_EFFECTS.items():
            if name in analysis_text:
                extracted_keywords.extend(data["keywords"].split("，"))

        for name, data in ATMOSPHERE.items():
            if name in analysis_text or (name == "梦幻" and ("神圣" in analysis_text or "庄严" in analysis_text)):
                extracted_keywords.extend(data["keywords"].split("，"))

        if "轮廓光" in analysis_text:
            extracted_keywords.append("轮廓光")
        if "rim light" in analysis_text_lower or "边缘光" in analysis_text:
            extracted_keywords.append("轮廓光")
        if "体积光" in analysis_text:
            extracted_keywords.append("体积光")
        if "丁达尔" in analysis_text:
            extracted_keywords.append("丁达尔光")
        if "光晕" in analysis_text:
            extracted_keywords.append("光晕")
        if "辉光" in analysis_text or "glow" in analysis_text_lower:
            extracted_keywords.append("光晕")
        if "魔法" in analysis_text:
            extracted_keywords.append("魔法光")
        if "神圣" in analysis_text:
            extracted_keywords.append("神秘光")

        extracted_keywords = list(set(extracted_keywords))

        if extracted_keywords:
            return "，".join(extracted_keywords)

        if "关键词" in analysis_text or "Keywords" in analysis_text.lower():
            lines = analysis_text.split('\n')
            for line in lines:
                if "关键词" in line or "Keywords" in line.lower() or "prompt" in line.lower():
                    idx = lines.index(line)
                    if idx + 1 < len(lines):
                        return lines[idx + 1].strip()
                    elif ':' in line:
                        return line.split(':', 1)[1].strip()

        return analysis_text
    except Exception:
        return analysis_text

def generate_lighting_keywords(
    directions: List[str],
    qualities: List[str],
    colors: List[str],
    effects: List[str],
    atmospheres: List[str],
    custom_keywords: str = ""
) -> Tuple[str, str]:
    all_keywords = []
    descriptions = []

    for d in directions:
        if d in LIGHT_DIRECTIONS:
            all_keywords.append(LIGHT_DIRECTIONS[d]["keywords"])
            descriptions.append(f"**{d}**: {LIGHT_DIRECTIONS[d]['description']}")

    for q in qualities:
        if q in LIGHT_QUALITY:
            all_keywords.append(LIGHT_QUALITY[q]["keywords"])
            descriptions.append(f"**{q}**: {LIGHT_QUALITY[q]['description']}")

    for c in colors:
        if c in LIGHT_COLOR:
            all_keywords.append(LIGHT_COLOR[c]["keywords"])
            descriptions.append(f"**{c}**: {LIGHT_COLOR[c]['description']}")

    for e in effects:
        if e in SPECIAL_EFFECTS:
            all_keywords.append(SPECIAL_EFFECTS[e]["keywords"])
            descriptions.append(f"**{e}**: {SPECIAL_EFFECTS[e]['description']}")

    for a in atmospheres:
        if a in ATMOSPHERE:
            all_keywords.append(ATMOSPHERE[a]["keywords"])
            descriptions.append(f"**{a}**: {ATMOSPHERE[a]['description']}")

    if custom_keywords.strip():
        all_keywords.append(custom_keywords.strip())

    keywords_str = "，".join(all_keywords)
    description_str = "\n\n".join(descriptions) if descriptions else "未选择任何打光选项"

    return keywords_str, description_str

class LightingKeywordGenerator:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": {
                "光源方向": (["无"] + list(LIGHT_DIRECTIONS.keys()), {"default": "无"}),
                "光线质量": (["无"] + list(LIGHT_QUALITY.keys()), {"default": "无"}),
                "光线颜色": (["无"] + list(LIGHT_COLOR.keys()), {"default": "无"}),
                "特殊光效": (["无"] + list(SPECIAL_EFFECTS.keys()), {"default": "无"}),
                "氛围风格": (["无"] + list(ATMOSPHERE.keys()), {"default": "无"}),
                "自定义关键词": ("STRING", {"default": "", "multiline": True}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("打光关键词", "详细说明")
    FUNCTION = "generate"
    CATEGORY = "Lighting Assistant"
    DESCRIPTION = "根据选择的打光参数生成专业的打光关键词"

    def generate(self, 光源方向="无", 光线质量="无", 光线颜色="无", 特殊光效="无", 氛围风格="无", 自定义关键词=""):
        directions = [光源方向] if 光源方向 != "无" else []
        qualities = [光线质量] if 光线质量 != "无" else []
        colors = [光线颜色] if 光线颜色 != "无" else []
        effects = [特殊光效] if 特殊光效 != "无" else []
        atmospheres = [氛围风格] if 氛围风格 != "无" else []

        keywords, description = generate_lighting_keywords(
            directions, qualities, colors, effects, atmospheres, 自定义关键词
        )

        return (keywords, description)

class LightingImageAnalyzer:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "llamacpp_url": ("STRING", {"default": DEFAULT_LLAMACPP_URL}),
                "model": ("STRING", {"default": "local-model"}),
            },
            "optional": {
                "自定义提示词": ("STRING", {"default": "", "multiline": True}),
                "timeout": ("INT", {"default": 120, "min": 30, "max": 600}),
                "测试模式": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("分析结果", "提取的关键词", "状态")
    FUNCTION = "analyze"
    CATEGORY = "Lighting Assistant"
    DESCRIPTION = "使用 llama.cpp 视觉模型分析图片的打光方式"

    def analyze(self, image, llamacpp_url=DEFAULT_LLAMACPP_URL, model="local-model", 自定义提示词="", timeout=120, 测试模式=False):
        import tempfile
        import cv2
        import numpy as np

        if 测试模式:
            test_analysis = """## 打光分析

### 1. 主光方向
这张图片采用了经典的伦勃朗光布光方式，主光源位于人物右前方约45度角位置。

### 2. 光线质量
光线为柔和的柔光，经过柔光箱漫射，阴影边缘柔和自然。

### 3. 光影效果
人物左侧脸颊形成了标志性的三角形光斑，右侧有明显的阴影区域，形成强烈的立体感。

### 4. 光线颜色
整体光线偏暖色，带有金色调，营造温暖浪漫的氛围。

### 5. 特殊光效
有轻微的轮廓光效果，勾勒出人物的发丝边缘。

### 6. 氛围感
整体氛围浪漫温馨，适合人像摄影。

## 打光关键词（Prompt）

```
伦勃朗光，侧面光，柔和光照，暖光，金色光，轮廓光，电影光，浪漫氛围
```"""
            test_keywords = "伦勃朗光，侧面光，柔和光照，暖光，金色光，轮廓光，电影光，浪漫氛围"
            return (test_analysis, test_keywords, "测试模式 - 分析完成")

        if image is None:
            return ("", "", "请提供图片")

        arr = (image.squeeze(0).cpu().numpy() * 255).astype(np.uint8)
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        cv2.imwrite(temp_file.name, cv2.cvtColor(arr, cv2.COLOR_RGB2BGR))
        image_path = temp_file.name

        prompt = 自定义提示词 if 自定义提示词.strip() else DEFAULT_LIGHTING_ANALYSIS_PROMPT

        result = analyze_lighting_with_llamacpp(image_path, prompt, model, llamacpp_url, timeout)

        if result.get("success"):
            analysis = result["analysis"]
            keywords = extract_keywords_from_analysis(analysis)
            return (analysis, keywords, "分析完成")
        else:
            error_msg = result.get("analysis", "分析失败")
            return (error_msg, "", error_msg)

class LightingModelList:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "llamacpp_url": ("STRING", {"default": DEFAULT_LLAMACPP_URL}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("模型列表",)
    FUNCTION = "get_models"
    CATEGORY = "Lighting Assistant"
    DESCRIPTION = "获取 llama.cpp 服务中加载的模型列表"

    def get_models(self, llamacpp_url=DEFAULT_LLAMACPP_URL):
        models = get_llamacpp_models(llamacpp_url)
        return (", ".join(models) if models else "未检测到模型",)


class ImageDescriber:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            },
            "optional": {
                "llamacpp_url": ("STRING", {"default": DEFAULT_LLAMACPP_URL}),
                "model": ("STRING", {"default": "local-model"}),
                "自定义提示词": ("STRING", {"default": "", "multiline": True}),
                "timeout": ("INT", {"default": 120, "min": 10, "max": 600}),
                "测试模式": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("描述结果", "提取的提示词", "状态")
    FUNCTION = "describe"
    CATEGORY = "Lighting Assistant"
    DESCRIPTION = "分析图片内容，生成详细描述和提示词"

    def describe(self, image, llamacpp_url=DEFAULT_LLAMACPP_URL, model="local-model", 自定义提示词="", timeout=120, 测试模式=True):
        try:
            import cv2
            import numpy as np
            import tempfile

            if 测试模式:
                test_description = """## 图片描述

### 主体内容
一位穿着华丽金色铠甲的女性战士，长发飘逸，站在神圣的祭坛前，双手举起释放魔法能量

### 环境背景
宏伟的古代神庙内部，高耸的穹顶，神秘的符文，发光的魔法阵

### 构图视角
仰视角度，展现角色的威严与神圣感，居中构图

### 风格质感
奇幻风格，史诗感，电影级渲染，细腻的光影，8k分辨率

## 提示词（Prompt）
```
一位穿着华丽金色铠甲的女性战士，长发飘逸，站在神圣的祭坛前，双手举起释放魔法能量，宏伟的古代神庙内部，高耸的穹顶，神秘的符文，发光的魔法阵，仰视角度，居中构图，奇幻风格，史诗感，电影级渲染，细腻的光影，8k分辨率
```"""
                test_prompt = "一位穿着华丽金色铠甲的女性战士，长发飘逸，站在神圣的祭坛前，双手举起释放魔法能量，宏伟的古代神庙内部，高耸的穹顶，神秘的符文，发光的魔法阵，仰视角度，居中构图，奇幻风格，史诗感，电影级渲染，细腻的光影，8k分辨率"
                return (test_description, test_prompt, "测试模式")

            arr = (image.squeeze(0).cpu().numpy() * 255).astype(np.uint8)
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            cv2.imwrite(temp_file.name, cv2.cvtColor(arr, cv2.COLOR_RGB2BGR))
            image_path = temp_file.name

            prompt = 自定义提示词 if 自定义提示词.strip() else DEFAULT_IMAGE_DESCRIPTION_PROMPT

            result = analyze_lighting_with_llamacpp(image_path, prompt, model, llamacpp_url, timeout)

            if result.get("success"):
                description = result["analysis"]
                prompt_text = extract_keywords_from_analysis(description)
                return (description, prompt_text, "描述完成")
            else:
                error_msg = result.get("analysis", "描述失败")
                return (error_msg, "", error_msg)

        except Exception as e:
            return (f"描述出错：{str(e)}", "", "错误")

class LightingPreview:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": {
                "光源方向": (["无"] + list(LIGHT_DIRECTIONS.keys()), {"default": "无"}),
                "光线质量": (["无"] + list(LIGHT_QUALITY.keys()), {"default": "无"}),
                "光线颜色": (["无"] + list(LIGHT_COLOR.keys()), {"default": "无"}),
                "特殊光效": (["无"] + list(SPECIAL_EFFECTS.keys()), {"default": "无"}),
                "氛围风格": (["无"] + list(ATMOSPHERE.keys()), {"default": "无"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("图片路径",)
    FUNCTION = "preview"
    CATEGORY = "Lighting Assistant"
    DESCRIPTION = "预览打光效果示意图"
    OUTPUT_NODE = True

    def preview(self, 光源方向="无", 光线质量="无", 光线颜色="无", 特殊光效="无", 氛围风格="无"):
        try:
            import cv2
            import numpy as np

            preview_key = None
            if 特殊光效 != "无" and 特殊光效 in LIGHTING_PREVIEW_IMAGES:
                preview_key = 特殊光效
            elif 光源方向 != "无" and 光源方向 in LIGHTING_PREVIEW_IMAGES:
                preview_key = 光源方向
            elif 氛围风格 != "无" and 氛围风格 in LIGHTING_PREVIEW_IMAGES:
                preview_key = 氛围风格
            elif 光线颜色 != "无" and 光线颜色 in LIGHTING_PREVIEW_IMAGES:
                preview_key = 光线颜色
            elif 光线质量 != "无" and 光线质量 in LIGHTING_PREVIEW_IMAGES:
                preview_key = 光线质量

            if preview_key and preview_key in LIGHTING_PREVIEW_IMAGES:
                image_filename = LIGHTING_PREVIEW_IMAGES[preview_key]
                image_path = os.path.join(images_directory, image_filename)
                
                if os.path.exists(image_path):
                    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
                    if img is not None and len(img.shape) == 3:
                        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        img = img.astype(np.float32) / 255.0
                        img = np.expand_dims(img, axis=0)
                        return {"ui": {"images": [img]}, "result": (image_path,)}

            default_img = np.zeros((256, 256, 3), dtype=np.float32)
            return {"ui": {"images": [default_img]}, "result": ("",)}
        except Exception as e:
            import traceback
            print(f"LightingPreview error: {e}")
            traceback.print_exc()
            import numpy as np
            default_img = np.zeros((256, 256, 3), dtype=np.float32)
            return {"ui": {"images": [default_img]}, "result": ("",)}

class TextDisplay:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"default": "", "multiline": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "display"
    CATEGORY = "Lighting Assistant"
    DESCRIPTION = "显示文本内容"
    OUTPUT_NODE = True

    def display(self, text):
        return {"ui": {"text": (text,)}, "result": (text,)}

NODE_CLASS_MAPPINGS = {
    "LightingKeywordGenerator": LightingKeywordGenerator,
    "LightingImageAnalyzer": LightingImageAnalyzer,
    "LightingModelList": LightingModelList,
    "ImageDescriber": ImageDescriber,
    "TextDisplay": TextDisplay,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LightingKeywordGenerator": "打光关键词生成器",
    "LightingImageAnalyzer": "图片打光分析器",
    "LightingModelList": "获取模型列表",
    "ImageDescriber": "图片描述器",
    "TextDisplay": "文本显示",
}