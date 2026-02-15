<template>
  <div class="voice-reader-wrapper">
    <el-button
      circle
      :type="isPlaying ? 'danger' : 'primary'"
      :icon="isPlaying ? VideoPause : Microphone"
      class="voice-btn"
      :class="{ 'is-pulsing': isPlaying }"
      @click="togglePlay"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue';
import { Microphone, VideoPause } from '@element-plus/icons-vue';
import axios from 'axios';

const props = defineProps<{
  text: string,
  isGenerating: boolean,
  backendUrl: string
}>();

// --- 状态管理 ---
const isPlaying = ref(false);
const processedIndex = ref(0);
const audioPlayer = new Audio();

// 队列与锁
const downloadQueue = ref<string[]>([]);
const playBuffer = ref<string[]>([]);
const isDownloading = ref(false);
const isAudioPlaying = ref(false);

// 🌟 核心修复：会话 ID，防止旧任务诈尸
let currentSessionId = 0;

// 1. 监听文字
watch(() => props.text, (newText) => {
  if (!isPlaying.value) return;

  const newPart = newText.slice(processedIndex.value);
  const delimiters = /[。！？\n]/;

  if (delimiters.test(newPart)) {
    const lastMarkIndex = Math.max(
      newPart.lastIndexOf('。'), newPart.lastIndexOf('！'),
      newPart.lastIndexOf('？'), newPart.lastIndexOf('\n')
    );

    const sentence = newPart.slice(0, lastMarkIndex + 1).trim();
    if (sentence.length > 1) {
      downloadQueue.value.push(sentence);
      processDownloadQueue();
    }
    processedIndex.value += lastMarkIndex + 1;
  }
});

// 监听结束
watch(() => props.isGenerating, (isGenerating) => {
  if (!isGenerating && isPlaying.value) {
    const finalPart = props.text.slice(processedIndex.value).trim();
    if (finalPart) {
      downloadQueue.value.push(finalPart);
      processDownloadQueue();
    }
  }
});

// 2. 下载线程 (带 Session 校验)
const processDownloadQueue = async () => {
  if (isDownloading.value || downloadQueue.value.length === 0) return;

  // 🌟 记录发起请求时的 Session ID
  const thisSessionId = currentSessionId;

  isDownloading.value = true;
  const textToDownload = downloadQueue.value.shift();

  try {
    const response = await axios.post(`${props.backendUrl}/api/tts`, { text: textToDownload });

    // 🌟 关键校验：下载回来后，检查当前 Session ID 变没变
    // 如果变了（说明用户点了停止或切了图片），直接丢弃，不放入播放列表
    if (thisSessionId !== currentSessionId || !isPlaying.value) {
      return;
    }

    const blob = base64ToBlob(response.data, 'audio/mp3');
    const blobUrl = URL.createObjectURL(blob);
    playBuffer.value.push(blobUrl);

    if (!isAudioPlaying.value) {
      startPlaybackThread();
    }
  } catch (e) {
    console.error("音频下载失败:", e);
  } finally {
    // 只有 ID 匹配时才继续递归，否则终止旧线程
    if (thisSessionId === currentSessionId) {
      isDownloading.value = false;
      processDownloadQueue();
    }
  }
};

// 3. 播放线程 (带 Session 校验)
const startPlaybackThread = () => {
  if (!isPlaying.value || playBuffer.value.length === 0) {
    isAudioPlaying.value = false;
    return;
  }

  isAudioPlaying.value = true;
  const nextUrl = playBuffer.value.shift();

  if (nextUrl) {
    audioPlayer.src = nextUrl;
    audioPlayer.play();
    audioPlayer.onended = () => {
      URL.revokeObjectURL(nextUrl);
      isAudioPlaying.value = false;
      if (isPlaying.value) startPlaybackThread();
    };
  }
};

const base64ToBlob = (base64: string, type: string) => {
  const binary = atob(base64);
  const array = [];
  for (let i = 0; i < binary.length; i++) array.push(binary.charCodeAt(i));
  return new Blob([new Uint8Array(array)], { type });
};

const togglePlay = () => isPlaying.value ? stop() : start();

const start = () => {
  stop(); // 先清理
  currentSessionId = Date.now(); // 🌟 生成新的 Session ID
  isPlaying.value = true;
  processedIndex.value = 0;

  // 处理已有文字
  if (props.text) {
    downloadQueue.value.push(...props.text.split(/[。！？\n]/).filter(s => s.length > 1));
    processedIndex.value = props.text.length;
    processDownloadQueue();
  }
};

const stop = () => {
  currentSessionId = 0; // 🌟 销毁 Session ID
  isPlaying.value = false;
  isAudioPlaying.value = false;
  isDownloading.value = false;
  audioPlayer.pause();
  audioPlayer.src = ''; // 清空播放器

  playBuffer.value.forEach(url => URL.revokeObjectURL(url));
  playBuffer.value = [];
  downloadQueue.value = [];
};

onUnmounted(() => stop());
defineExpose({ start, stop });
</script>

<style scoped lang="scss">
.voice-reader-wrapper {
  position: fixed;
  top: 30px;
  right: 30px;
  z-index: 1000;
}
.voice-btn {
  transition: all 0.3s ease;
  &.is-pulsing {
    animation: pulse-red 1.5s infinite;
    transform: scale(1.1);
  }
}
@keyframes pulse-red {
  0% { box-shadow: 0 0 0 0 rgba(245, 108, 108, 0.7); }
  70% { box-shadow: 0 0 0 10px rgba(245, 108, 108, 0); }
  100% { box-shadow: 0 0 0 0 rgba(245, 108, 108, 0); }
}
</style>
