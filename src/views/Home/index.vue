<template>
  <div class="app-wrapper">
    <!-- 动态背景 -->
    <div class="ambient-bg">
      <div class="blob blob-1"></div>
      <div class="blob blob-2"></div>
      <div class="blob blob-3"></div>
    </div>

    <el-container class="main-layout">
      <!-- 导航栏 -->
      <el-header class="nav-header">
        <div class="brand">
          <el-icon :size="28" color="#42b983"><Menu /></el-icon>
          <span class="brand-text">万物生色 <small></small></span>
        </div>
      </el-header>

      <!-- 主内容区 -->
      <el-main class="main-content">
        <el-row justify="center">
          <el-col :xs="24" :sm="22" :md="20" :lg="18" :xl="16">

            <!-- 1. 探索发现组件 -->
             <ExploreSection
              @explore-item-click="handleExploreClick"
            />

            <!-- 2. 上传识别卡片 -->
            <UploadCard
              :img-url="imgUrl"
              :is-processing="isProcessing"
              :has-file="!!selectedFile"
              @update:file="handleFileUpdate"
              @update:imgUrl="url => imgUrl = url"
              @start-identify="uploadAndIdentify"
            />

            <!-- 3. 结果展示卡片 -->
            <transition name="el-zoom-in-top">
              <ResultCard
                  ref="resultCardRef"
                  :visible="!!resultName || !!identificationError"
                  :result-name="resultName"
                  :result-source="resultSource"
                  :result-score="resultScore"
                  :stream-text="streamText"
                  :loading-l-l-m="loadingLLM"
                  :error-msg="identificationError"
                  :backend-url="backendUrl"
                  @retry="triggerInput"
                />
            </transition>

          </el-col>
        </el-row>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue';
import { api } from '@/services/api'; // 引入 API 服务
import {  Menu,  } from '@element-plus/icons-vue';
import { fetchStreamWiki } from '@/services/llmService';
import ExploreSection from '@/components/ExploreSection/index.vue';
import UploadCard from '@/components/UploadCard/index.vue';
import ResultCard from '@/components/ResultCard/index.vue';
// 环境变量
const backendUrl = api.getBackendUrl();
// --- 状态 ---
const fileInput = ref<HTMLInputElement | null>(null);
const imgUrl = ref('');
const selectedFile = ref<File | null>(null);
const isProcessing = ref(false);
const loadingLLM = ref(false);
const resultName = ref('');
const resultCategory = ref('');
const resultScore = ref<number | null>(null);
const resultSource = ref('');
const streamText = ref('');
const identificationError = ref(''); // 🌟 新增：存储识别失败的幽默提示
const resultCardRef = ref<InstanceType<typeof ResultCard> | null>(null);
let llmAbortController: AbortController | null = null;

const handleExploreClick = async (item: { name: string, imageUrl: string }) => {
   // 🌟 核心修复：立即停止正在播放的语音
  resultCardRef.value?.stopVoice();
  // 1. 更新 UI 状态
  selectedFile.value = null;

  // 重置其他状态
  imgUrl.value = item.imageUrl;
  resultName.value = `正在查询 ${item.name}...`;
  resultCategory.value = '探索发现';
  resultSource.value = 'AI 推荐';
  resultScore.value = null;
  identificationError.value = '';
  streamText.value = '';


  await callLlmService(item.name, false);

  await nextTick();
  const resultCard = document.getElementById('result-card');
  if (resultCard) {
    resultCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
};

const triggerInput = () => fileInput.value?.click();

const handleFileUpdate = (file: File) => {
  selectedFile.value = file;
  resultName.value = ''; // 重置结果
  // ... 滚动逻辑
  nextTick(() => {
      // 稍微给图片渲染留一点点余地 (100ms)
      setTimeout(() => {
        const actionBtn = document.querySelector('.card-footer');
        if (actionBtn) {
          actionBtn.scrollIntoView({
            behavior: 'smooth',
            block: 'center' // 滚动到屏幕中间，视觉效果最好
          });
        }
      }, 100);
    });
};

const uploadAndIdentify = async () => {
  if (!selectedFile.value) return;
  // 立即停止正在播放的语音
  resultCardRef.value?.stopVoice();

  isProcessing.value = true;
  streamText.value = '';
  resultSource.value = '';
  identificationError.value = ''; // 开始时清空错误

  try {
    const formData = new FormData();
    formData.append('image', selectedFile.value);

    const response = await api.identifyImage(selectedFile.value!);;
    const data = response.data;

    if (data.success) {
      resultName.value = data.name;
      resultScore.value = data.score;
      resultSource.value = data.source || '智能识别';

      // 🌟 调用重构后的方法
      await callLlmService(resultName.value, true);
    } else {
      // 🌟 后端明确返回识别失败
      identificationError.value = data.message || "这张图可能来自外太空，我的知识库里还没收录呢！";
    }
  } catch (error) {
    console.error("识别请求失败:", error);
    identificationError.value = "糟糕，和识别服务器的连接好像断了...";
  } finally {
    isProcessing.value = false;
  }
};

// --- 新的调用 LLM 的封装函数 ---
const callLlmService = async (keyword: string, isModelResult: boolean) => {
   // 🌟 1. 如果有正在进行的请求，立刻掐断！
  if (llmAbortController) {
    llmAbortController.abort();
  }
  // 🌟 2. 创建新的控制器
  llmAbortController = new AbortController();

  loadingLLM.value = true;
  streamText.value = '';
  identificationError.value = '';

  // 获取滚动容器
  const scrollContainer = document.querySelector('.main-content');

  // 🌟 自动启动朗读组件
  nextTick(() => {
    resultCardRef.value?.startVoice();
  });


  await fetchStreamWiki(
    keyword,
    isModelResult,
    (textChunk) => {
      if (llmAbortController?.signal.aborted) return;
      streamText.value += textChunk;

      if (scrollContainer) {
        // 🌟 智能滚动逻辑
        // 1. 计算用户当前距离底部的距离
        // scrollHeight (总高) - scrollTop (已滚距离) - clientHeight (可视高度)
        const distanceToBottom = scrollContainer.scrollHeight - scrollContainer.scrollTop - scrollContainer.clientHeight;
        if (distanceToBottom < 100) {
          nextTick(() => {
            // 使用 requestAnimationFrame 保证在高频更新下依然流畅
            requestAnimationFrame(() => {
              scrollContainer.scrollTo({
                top: scrollContainer.scrollHeight,
                behavior: 'smooth' // 使用平滑滚动
              });
            });
          });
        }
      }
    },
    () => {
      if (llmAbortController?.signal.aborted) return;

      loadingLLM.value = false;
      resultName.value = keyword;
      // 结束时补一次平滑滚动
      scrollContainer?.scrollTo({ top: scrollContainer.scrollHeight, behavior: 'smooth' });
    },
    (error) => {
      if (llmAbortController?.signal.aborted) return;
      loadingLLM.value = false;
      resultCardRef.value?.stopVoice();
      console.error("LLM 生成失败:", error);
      llmAbortController = null;
    },
    llmAbortController.signal // 🌟 传入中断信号
  );
};
</script>

<style scoped lang="scss">
// 1. 基础布局与极光背景
.app-wrapper {
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: #f0f2f5;
  font-family: 'Inter', 'PingFang SC', sans-serif;
  position: relative;

  // 🌟 极光背景层
  .ambient-bg {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 0;
    filter: blur(100px);
    opacity: 0.9;
    pointer-events: none;

    .blob {
      position: absolute;
      border-radius: 50%;
      animation: move 20s infinite alternate;
    }

    .blob-1 {
      width: 500px; height: 500px;
      background: rgba(66, 185, 131, 0.4);
      top: -10%; left: -10%;
    }

    .blob-2 {
      width: 400px; height: 400px;
      background: rgba(64, 158, 255, 0.3);
      bottom: -10%; right: 10%;
      animation-delay: -5s;
    }

    .blob-3 {
      width: 300px; height: 300px;
      background: rgba(168, 124, 255, 0.2);
      top: 40%; right: -5%;
      animation-delay: -10s;
    }
  }
}

@keyframes move {
  from { transform: translate(0, 0) scale(1); }
  to { transform: translate(50px, 100px) scale(1.2); }
}

// 2. 玻璃拟态卡片通用样式
.glass-card {
  background: rgba(255, 255, 255, 0.75); // 半透明
  backdrop-filter: blur(20px) saturate(180%); // 关键：磨砂效果
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow:
    0 4px 6px -1px rgba(0, 0, 0, 0.05),
    0 20px 25px -5px rgba(0, 0, 0, 0.1);
  margin-bottom: 30px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);

  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.15);
    background: rgba(255, 255, 255, 0.85);
  }
}

// 3. 导航栏美化
.nav-header {
  height: 70px !important;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(15px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;

  .brand {
    display: flex;
    align-items: center;
    gap: 12px;

    .brand-text {
      font-size: 1.6rem;
      font-weight: 800;
      letter-spacing: -1px;
      background: linear-gradient(135deg, #2d5a27 0%, #42b983 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;

      small {
        font-size: 0.8rem;
        -webkit-text-fill-color: #409eff;
        letter-spacing: 1px;
        font-weight: 500;
      }
    }
  }
}

// 4. 内容滚动区
.main-layout { flex: 1; overflow: hidden; display: flex; flex-direction: column; }
.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 40px 15px;
  scroll-behavior: smooth;
  z-index: 1;
}
.upload-card-container {
  margin-top: 20px;
}
</style>
