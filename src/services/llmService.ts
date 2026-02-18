// src/services/llmService.ts
const LLM_API_KEY = import.meta.env.VITE_LLM_API_KEY;
const LLM_API_URL = import.meta.env.VITE_LLM_API_URL;

/**
 * 流式获取科普信息
 * @param keyword - 需要查询的关键词
 * @param onDelta - 接收到每个数据块时的回调函数
 * @param onFinish - 流结束时的回调
 * @param onError - 发生错误时的回调
 */
export async function fetchStreamWiki(
  keyword: string,
  isModelResult: boolean, // 🌟 新增参数：标记是否为本地模型返回的标签
  onDelta: (text: string) => void,
  onFinish: () => void,
  onError: (error: any) => void,
  signal?: AbortSignal // 🌟 新增参数：接收中断信号
) {
  let prompt = ``;

  if (isModelResult) {
    // 针对本地模型识别结果 (如 "Chow Chow")
    prompt = `我通过AI识别到了一个物体，英文标签是 "${keyword}"。请帮我：
    1. 给出它的中文学名。
    2. 详细介绍分类、特征和习性。
    内容在300字以内，使用Markdown，确保第一行是“# [中文名]”。`;
  } else {
    // 针对探索发现的点击 (如 "树袋熊")
    prompt = `请为“${keyword}”写一段科普介绍。
    注意：请直接使用“${keyword}”作为标题。
    包含分类、形态特征、生活习性和主要价值。
    300字以内，Markdown格式，确保第一行是“# ${keyword}”。`;
  }
  try {
    const response = await fetch(LLM_API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${LLM_API_KEY}` },
      signal: signal, // 将信号传给 fetch，这样调用 signal.abort() 时请求就会断开
      body: JSON.stringify({
        model: "deepseek-v3-2-251201",
        messages: [
          { role: "system", content: "你是一个专业的生物百科专家。" },
          { role: "user", content: prompt }
        ],
        stream: true
      })
    });

    if (!response.ok || !response.body) {
      throw new Error(`API 请求失败，状态码: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        onFinish();
        break;
      }

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const jsonStr = line.slice(6).trim();
          if (jsonStr === '[DONE]') {
            onFinish();
            return;
          }
          try {
            const data = JSON.parse(jsonStr);
            const content = data.choices[0]?.delta?.content || '';
            if (content) {
              onDelta(content);
            }
          } catch (e) { /* 忽略解析错误 */ }
        }
      }
    }
  } catch (error: any) {
    if (error.name === 'AbortError') {
      console.log('用户中断了上一条生成任务');
    } else {
      onError(error);
    }
  }
}
