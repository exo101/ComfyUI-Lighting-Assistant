# ComfyUI-Lighting-Assistant

基于 sd-webui-lighting-assistant 打光辅助插件移植的 ComfyUI 版本，提供专业的打光关键词生成和图片分析功能。

## 功能特性

### 1. 打光关键词生成器
快速生成适合 Stable Diffusion 使用的打光关键词，支持多种打光类型组合：
- **光源方向**：正面光、侧面光、侧逆光、正逆光、顶光、底光、伦勃朗光、蝴蝶光、分割光、环形光
- **光线质量**：硬光、柔光、漫射光、聚光
- **光线颜色**：暖光、冷光、中性光、黄金时刻、蓝色时刻、霓虹光、烛光、月光
- **特殊光效**：丁达尔光、光晕、体积光、轮廓光、电影光、舞台光
- **氛围风格**：神秘、浪漫、恐怖、科幻、复古、梦幻

### 2. 图片打光分析器
通过 llama.cpp 服务分析图片的打光方式，生成详细的打光分析报告和关键词：
- 主光方向分析
- 光线质量分析
- 光影效果分析
- 光线颜色分析
- 特殊光效分析
- 氛围感分析

### 3. 图片描述器
全面描述图片内容，生成适合 Stable Diffusion 使用的详细提示词：
- 主体内容描述
- 环境背景描述
- 构图视角描述
- 风格质感描述

### 4. 获取模型列表
查看 llama.cpp 服务中加载的模型列表，方便选择合适的分析模型。

## 安装方法

1. 将本文件夹复制到 ComfyUI 的 `custom_nodes` 目录下：
   ```
   ComfyUI/custom_nodes/ComfyUI-Lighting-Assistant/
   ```

2. 确保已安装必要依赖：
   ```bash
   pip install requests opencv-python numpy
   ```

3. 重启 ComfyUI，在节点菜单中找到 **Lighting Assistant** 分类。

## 使用方法

### 打光关键词生成器

1. 在节点菜单中选择 **Lighting Assistant** → **打光关键词生成器**
2. 选择所需的打光选项（每个类别都有"无"选项）
3. 点击执行，输出包含：
   - 打光关键词：适合 Stable Diffusion 使用的关键词
   - 详细说明：每个选项的详细描述

### 图片打光分析器

1. 加载一张图片（使用 LoadImage 节点）
2. 添加 **图片打光分析器** 节点，连接图片输入
3. 配置 llama.cpp 服务地址（默认：http://localhost:8082）
4. 选择模型名称（默认：local-model）
5. 点击执行，输出包含：
   - 分析结果：详细的打光分析报告
   - 提取的关键词：从分析中提取的打光关键词
   - 状态：运行状态

### 图片描述器

1. 加载一张图片（使用 LoadImage 节点）
2. 添加 **图片描述器** 节点，连接图片输入
3. 配置 llama.cpp 服务地址
4. 点击执行，输出包含：
   - 描述结果：详细的图片描述
   - 提取的提示词：适合 Stable Diffusion 的提示词
   - 状态：运行状态

### 测试模式

图片打光分析器和图片描述器支持测试模式（默认开启），无需连接 llama.cpp 服务即可查看示例输出。

## 工作流示例

插件包含两个工作流示例，位于 `workflows/` 目录：

### 1. keyword_generation_workflow.json
关键词生成工作流，包含打光关键词生成器和预览节点。

### 2. lighting_analysis_workflow.json
图片分析工作流，包含图片加载、打光分析和描述节点。

## 配置说明

### llama.cpp 服务配置

确保 llama.cpp 服务已启动并支持图像分析（需使用支持 vision 的模型）：

```bash
./server -m model.gguf --host 0.0.0.0 --port 8082
```

## 节点列表

| 节点名称 | 说明 |
|---------|------|
| 打光关键词生成器 | 生成打光关键词 |
| 图片打光分析器 | 分析图片打光方式 |
| 图片描述器 | 描述图片内容 |
| 获取模型列表 | 获取 llama.cpp 模型列表 |
| 文本显示 | 显示文本内容 |

## 兼容性

- ComfyUI v0.4+
- Python 3.10+
- llama.cpp 支持 vision 的模型


本插件基于 [sd-webui-lighting-assistant](https://github.com/ototadana/sd-webui-lighting-assistant) 项目的打光关键词数据。
视频教程使用
https://www.bilibili.com/video/BV18hj26xE6Q/?vd_source=343e49b703fb5b4137cd6c1987846f37#reply116799018374239

<img width="1284" height="1547" alt="qq群ai交流群" src="https://github.com/user-attachments/assets/dd483666-ae16-4a56-91a7-f6256422e8ee" />

