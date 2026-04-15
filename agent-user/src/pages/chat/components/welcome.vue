<template>
    <view class="outer">
        <view class="hero-copy">
            <text class="kicker">AI旅行中枢</text>
            <text class="title">从灵感到路线，一次规划清楚</text>
            <text class="subtitle">支持地图路线、天气查询、语音输入、历史会话和PDF导出。</text>
        </view>
        <image src="/static/travel.png" mode="widthFix" />
    </view>
</template>

<script setup lang="ts">
</script>

<style scoped lang="less">
.outer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20rpx;
    padding: 170rpx 28rpx 12rpx 28rpx;
}

.hero-copy {
    flex: 1;
    min-width: 0;
}

.kicker {
    display: block;
    color: #1f7a5b;
    font-size: 24rpx;
    font-weight: 700;
}

.title {
    display: block;
    margin-top: 10rpx;
    color: #17231f;
    font-size: 42rpx;
    font-weight: 800;
    line-height: 1.18;
}

.subtitle {
    display: block;
    margin-top: 14rpx;
    color: #5c6b66;
    font-size: 25rpx;
    line-height: 1.5;
}

image {
    width: 210rpx;
    height: 210rpx;
    border-radius: 8rpx;
}
</style>