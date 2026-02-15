<template>
  <el-card v-if="visible" class="glass-card result-card" id="result-card">
    <template #header>
      <div class="result-header">
        <div class="left-info">
          <span class="result-name">{{ resultName }}</span>
          <el-tag v-if="resultSource" type="warning" size="small">{{ resultSource }}</el-tag>
        </div>

        <div class="right-actions">
          <VoiceReader
            ref="voiceReaderRef"
            :text="streamText"
            :is-generating="loadingLLM"
            :backend-url="backendUrl"
          />
          <el-tag v-if="resultScore" effect="dark" type="success" round style="margin-left: 10px;">
            置信度 {{ (resultScore * 100).toFixed(0) }}%
          </el-tag>
        </div>
      </div>
    </template>

    <div v-if="errorMsg" class="error-state">
      <el-icon :size="50"><MagicStick /></el-icon>
      <h3>哎呀，AI 也有看走眼的时候...</h3>
      <p>{{ errorMsg }}</p>
      <el-button type="primary" round @click="$emit('retry')">换张图试试？</el-button>
    </div>

    <div v-else class="wiki-content">
      <div class="markdown-body" v-html="renderedMarkdown"></div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { MagicStick } from '@element-plus/icons-vue';
import { marked } from 'marked';
import VoiceReader from '@/components/VoiceReader/index.vue';

const props = defineProps<{
  visible: boolean,
  resultName: string,
  resultSource: string,
  resultScore: number | null,
  streamText: string,
  loadingLLM: boolean,
  errorMsg: string,
  backendUrl: string
}>();

defineEmits(['retry']);

const voiceReaderRef = ref<InstanceType<typeof VoiceReader> | null>(null);
const renderedMarkdown = computed(() => marked.parse(props.streamText));

// 暴露给父组件调用
const startVoice = () => voiceReaderRef.value?.start();
const stopVoice = () => voiceReaderRef.value?.stop();

defineExpose({ startVoice, stopVoice });
</script>

<style scoped lang="scss">
// 结果卡片内部排版
.result-header {
  .result-name {
    font-size: 2.2rem;
    font-weight: 800;
    color: #1a1a1a;
    letter-spacing: -1px;
  }

  .voice-btn {
    box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
    &:hover { transform: scale(1.1); }
  }
}

// 🌟 Markdown 内容深度美化
.markdown-body {
  padding: 15px 5px;
  color: #374151;
  font-size: 1.1rem;
  line-height: 1.8;

  :deep(h1), :deep(h2) {
    color: #111827;
    margin-top: 24px;
    padding-bottom: 8px;
    border-bottom: 2px solid #f3f4f6;
  }

  :deep(p) { margin-bottom: 16px; }

  :deep(strong) {
    color: #2d5a27;
    background: rgba(66, 185, 131, 0.1);
    padding: 0 4px;
    border-radius: 4px;
  }

  :deep(ul) {
    padding-left: 20px;
    li {
      margin-bottom: 8px;
      list-style-type: disc;
      &::marker { color: #42b983; }
    }
  }
}

// 7. 错误状态
.error-state {
  padding: 60px 20px;
  h3 { font-size: 1.6rem; color: #1f2937; margin-bottom: 12px; }
  p { font-size: 1rem; color: #6b7280; margin-bottom: 30px; }
}
</style>
