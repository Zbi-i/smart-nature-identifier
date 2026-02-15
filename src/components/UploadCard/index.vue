<template>
  <el-card class="glass-card upload-card" shadow="never">
    <div class="upload-area" @click="triggerInput" :class="{ 'has-image': imgUrl }">
      <input type="file" ref="fileInput" accept="image/*" @change="onFileChange" hidden />

      <template v-if="!imgUrl">
        <div class="placeholder-content">
          <el-icon class="upload-icon"><UploadFilled /></el-icon>
          <h3>或者，上传你自己的图片</h3>
          <p class="sub-text">本地 AI 模型，极速识别，保护隐私</p>
        </div>
      </template>

      <template v-else>
        <el-image :src="imgUrl" class="preview-image" fit="contain">
          <template #placeholder>
            <div class="image-slot">加载中...</div>
          </template>
        </el-image>

        <!-- 探索模式提示 -->
        <div v-if="!hasFile" class="explore-tag">
          <el-icon><Compass /></el-icon> 探索模式
        </div>

        <div class="overlay-actions">
          <el-button type="primary" circle :icon="Refresh" @click.stop="triggerInput" />
        </div>
      </template>
    </div>

    <div class="card-footer" v-if="imgUrl && hasFile">
      <el-button
        type="success"
        size="large"
        class="action-btn"
        :loading="isProcessing"
        @click="$emit('startIdentify')"
        round
      >
        <el-icon class="el-icon--left"><DArrowRight /></el-icon>
        {{ isProcessing ? '本地识别中...' : '开始识别' }}
      </el-button>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { UploadFilled, Refresh, DArrowRight, Compass } from '@element-plus/icons-vue';

const props = defineProps<{
  imgUrl: string,
  isProcessing: boolean,
  hasFile: boolean // 是否有本地文件
}>();

const emit = defineEmits(['update:file', 'update:imgUrl', 'startIdentify']);

const fileInput = ref<HTMLInputElement | null>(null);

const triggerInput = () => fileInput.value?.click();

const onFileChange = (e: Event) => {
  const file = (e.target as HTMLInputElement).files?.[0];
  if (file) {
    emit('update:file', file);
    emit('update:imgUrl', URL.createObjectURL(file));
  }
};
</script>

<style scoped lang="scss">
/* 直接把 Home.vue 里 .upload-card 相关的样式剪切过来 */
/* 包括 .upload-area, .preview-image, .action-btn 等 */
// 5. 上传与识别区
.upload-area {
  min-height: 300px;
  max-height: 550px;
  width: 100%;
  border: 2px dashed rgba(64, 158, 255, 0.3);
  border-radius: 20px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background-color: rgba(255, 255, 255, 0.4);
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;

  &.has-image {
    border-style: solid;
    border-color: rgba(255, 255, 255, 0.5);
    background: #fff;
    // 有图时，高度自动适应内容（但受限于上面的 max-height）
    height: auto;
    padding: 10px;
  }

  // 内部图片展示区
  .preview-image {
    width: 100%;
    // 关键：让图片在最大高度内自适应
    max-height: 530px;
    display: flex;
    justify-content: center;
    align-items: center;

    :deep(img) {
      width: auto;
      height: auto;
      max-width: 100%;
      max-height: 500px;
      object-fit: contain;
      border-radius: 12px;
      filter: drop-shadow(0 10px 30px rgba(0,0,0,0.12));
    }
  }

  &:hover:not(.disabled) {
    border-color: #42b983;
    background-color: rgba(66, 185, 131, 0.05);
    .upload-icon { transform: scale(1.1) rotate(5deg); color: #42b983; }
  }

  .upload-icon {
    font-size: 64px;
    color: #909399;
    margin-bottom: 20px;
    transition: all 0.4s;
    display: block;
    margin: 0 auto;
  }

  // 探索模式标签
  .explore-tag {
    position: absolute;
    top: 20px;
    left: 20px;
    background: rgba(66, 185, 131, 0.85);
    padding: 8px 16px;
    border-radius: 30px;
    color: white;
    font-size: 0.85rem;
    font-weight: 600;
    backdrop-filter: blur(10px);
    box-shadow: 0 4px 12px rgba(66, 185, 131, 0.3);
  }
}
// 🌟 流光按钮
.action-btn {
  width: 100%;
  height: 55px;
  margin-top: 12px;
  font-size: 1.1rem;
  font-weight: 700;
  letter-spacing: 4px;
  border: none;
  background: linear-gradient(135deg, #42b983 0%, #34a853 100%);
  color: white;
  box-shadow: 0 10px 25px -5px rgba(66, 185, 131, 0.4);
  transition: all 0.3s;

  &:hover {
    transform: scale(1.02);
    box-shadow: 0 15px 35px -5px rgba(66, 185, 131, 0.6);
    filter: brightness(1.1);
  }

  &:active { transform: scale(0.98); }
}
// 8. 响应式微调
@media (max-width: 768px) {
  .upload-area {
    min-height: 240px;
    max-height: 400px;

    .preview-image :deep(img) {
      max-height: 380px;
    }
  }
}
</style>
