<template>
  <div class="explore-section">
     <div class="section-header">
      <div class="title-wrapper">
        <div class="icon-box">
          <el-icon><Compass /></el-icon>
        </div>
        <div class="text-group">
          <h3 class="main-title">探索发现</h3>
          <span class="sub-title">DISCOVER NATURE</span>
        </div>
      </div>
      <div class="header-decoration"></div>
    </div>

    <el-skeleton v-if="loading" style="height: 300px;" animated>
      <template #template>
        <el-skeleton-item variant="image" style="width: 100%; height: 100%; border-radius: 18px;" />
      </template>
    </el-skeleton>

    <el-carousel
      v-else-if="recommendations.length > 0"
      type="card"
      height="300px"
      trigger="click"
    >
      <el-carousel-item
        v-for="item in recommendations"
        :key="item.name"
        class="carousel-item"
        @click="onItemClick(item)"
      >
        <el-image
          :src="item.imageUrl"
          class="carousel-img"
          fit="cover"
          lazy
        >
          <template #placeholder>
            <div class="image-slot">🔍 正在搜索全网资源...</div>
          </template>
          <template #error>
            <div class="image-slot error-slot">
              <el-icon><Picture /></el-icon>
              <span>图片暂不可用</span>
            </div>
          </template>
        </el-image>

        <div class="carousel-title">
          <span>{{ item.name }}</span>
        </div>
      </el-carousel-item>
    </el-carousel>
  </div>
</template>

<script setup lang="ts">
import { Compass, Picture } from '@element-plus/icons-vue';
import { ref, onMounted } from 'vue';
import { api } from '@/services/api';

const emit = defineEmits(['exploreItemClick']);
const recommendations = ref<{ name: string, imageUrl: string }[]>([]);
const loading = ref(true);
const onItemClick = (item: { name: string, imageUrl: string }) => {
  emit('exploreItemClick', item);
};

onMounted(() => {
  fetchRecommendations();
});

const fetchRecommendations = async () => {
  try {
    const response = await api.getRecommendations();
    if (response.data.success) {
      console.log("获取推荐成功:", response.data.data);
      recommendations.value = response.data.data;
      loading.value = false;
    }
  } catch (error) {
    console.error("获取推荐失败:", error);
    // 即使失败也要关闭 loading，否则骨架屏会一直卡在那里
    loading.value = false;
  }
};

</script>

<style scoped lang="scss">
/* 样式保持不变 */
.explore-module {
  margin-bottom: 50px;
  position: relative;
  z-index: 1;
}

// 🌟 标题栏深度美化
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 30px;
  padding: 0 5px;

  .title-wrapper {
    display: flex;
    align-items: center;
    gap: 15px;

    // 图标发光底座
    .icon-box {
      width: 44px;
      height: 44px;
      background: rgba(66, 185, 131, 0.15);
      border: 1px solid rgba(66, 185, 131, 0.3);
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      backdrop-filter: blur(10px);
      box-shadow: 0 4px 15px rgba(66, 185, 131, 0.2);

      .el-icon {
        font-size: 24px;
        color: #2d5a27;
        filter: drop-shadow(0 0 5px rgba(66, 185, 131, 0.5));
        animation: rotate-compass 10s linear infinite; // 罗盘轻微旋转动画
      }
    }

    // 文字组
    .text-group {
      display: flex;
      flex-direction: column;

      .main-title {
        font-size: 1.8rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: 1px;
        // 渐变文字效果
        background: linear-gradient(135deg, #1a3a16 0%, #42b983 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
      }

      .sub-title {
        font-size: 0.75rem;
        font-weight: 600;
        color: #909399;
        letter-spacing: 3px;
        margin-top: -2px;
        opacity: 0.8;
      }
    }
  }

  // 右侧装饰线
  .header-decoration {
    flex: 1;
    height: 2px;
    margin-left: 30px;
    background: linear-gradient(to right, rgba(66, 185, 131, 0.3), transparent);
    border-radius: 2px;
  }
}

// 罗盘旋转动画
@keyframes rotate-compass {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

// 🌟 轮播图样式同步优化
.carousel-item {
  border-radius: 24px; // 调大圆角，配合整体风格
  border: 1px solid rgba(255, 255, 255, 0.4);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);

  .carousel-title {
    // 标题文字微调
    font-size: 1.4rem;
    letter-spacing: 2px;
    padding-bottom: 25px;
    text-shadow: 0 2px 10px rgba(0,0,0,0.8);
  }
}
.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 1.6rem;
  font-weight: 600;
  color: #303133;
  margin-bottom: 25px;
}
.el-carousel {
  margin: 0 -20px;
}
.carousel-item {
  border-radius: 18px;
  overflow: hidden;
  cursor: pointer;
  box-shadow: 0 10px 30px rgba(0,0,0,0.1);
  transition: transform 0.3s;
}
.el-carousel__item.is-active {
  transform: translateY(-5px) scale(1.02);
}
.carousel-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.carousel-title {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 30px 20px 15px;
  background: linear-gradient(to top, rgba(0,0,0,0.7) 0%, transparent 100%);
  color: white;
  text-align: center;
  font-size: 1.2rem;
  font-weight: bold;
  text-shadow: 0 1px 3px rgba(0,0,0,0.5);
}
:deep(.el-carousel__indicators--outside button) {
  background-color: #42b983;
  opacity: 0.5;
}
:deep(.el-carousel__indicators--outside button.is-active) {
  opacity: 1;
}
.image-slot {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
  background: #f5f7fa;
  color: #909399;
}
.error-slot {
  background: #fdf6ec; /* 淡淡的橘色背景表示没找到图 */
  color: #e6a23c;
}
</style>
