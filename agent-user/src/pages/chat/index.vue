<template>
    <view>
        <!-- 顶部侧边栏按钮 -->
        <view class="menu-outer">
            <view class="button-top"></view>
            <view class="menu-style">
                <image src="/static/chat-list.png" @click="switchFn" mode="widthFix" />
                <button class="archive-entry" plain @click="goArchive">行程档案</button>
            </view>
        </view>
        <!-- 欢迎界面 -->
        <Welcome v-if="appStore.selectedThreadId == ''" />
        <PlannerForm v-if="appStore.selectedThreadId == ''" />
        <!-- 快速卡片 -->
        <GridCard :cardData="computedCardData" v-if="appStore.selectedThreadId == ''" />
        <!-- 输入框 -->
        <ChatInput v-show="!appStore.isVoice"/>
        <Voice v-show="appStore.isVoice"/>
        <!-- 对话窗口 -->
        <Window />
        <!-- 历史对话记录 -->
        <History />
    </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
const { height, top, bottom } = uni.getStorageSync("buttonPosition")
import type { CardDataType } from '@/types'
import Welcome from './components/welcome.vue'
import PlannerForm from './components/plannerForm.vue'
import GridCard from "./components/gridCard.vue"
import ChatInput from "./components/chatInput.vue"
import Voice from "./components/voice.vue"
import Window from "./components/window.vue"
import History from "./components/history.vue"

import iconA from "@/static/icon-a.png"
import iconB from "@/static/icon-b.png"
import iconC from "@/static/icon-c.png"
import iconD from "@/static/icon-d.png"

import { useAppStore } from '@/store/index'
const appStore = useAppStore()

const cardData = ref<CardDataType>([
    {
        icon: iconA,
        title: '发现目的地',
        prompt: ''
    },
    {
        icon: iconB,
        title: '查询高铁票',
        prompt: ''
    },
    {
        icon: iconC,
        title: '规划行程',
        prompt: ''
    },
    {
        icon: iconD,
        title: '查询目的地天气',
        prompt: ''
    }

])

const computedCardData = computed(() => {
    if (appStore.CardDataList.length > 0) {
        const data = appStore.CardDataList
        for (let i = 0; i < data.length; i++) {
            cardData.value[i].prompt = data[i].prompt
        }
        return cardData.value
    } else {
        return [
            {
                icon: iconA,
                title: '发现目的地',
                prompt: ''
            },
            {
                icon: iconB,
                title: '查询高铁票',
                prompt: ''
            },
            {
                icon: iconC,
                title: '规划行程',
                prompt: ''
            },
            {
                icon: iconD,
                title: '查询目的地天气',
                prompt: ''
            }

        ]
    }
})

const switchFn = () => {
    if (appStore.disabledStatus) return;
    appStore.switchHistoryAndChat = !appStore.switchHistoryAndChat
    // console.log(appStore.switchHistoryAndChat)
    console.log('点击')
}

const goArchive = () => {
    if (appStore.disabledStatus) return
    uni.navigateTo({ url: '/pages/archive/index' })
}
</script>

<style scoped lang="less">

.menu-outer {
    // height: v-bind('height + "px"');
    // background-color: linear-gradient(#e7ebff, #dedfff);
    // background-color: #fff;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 999;

    .button-top {
        height: v-bind('top + "px"');
        background-color: #fff;

    }

    .menu-style {
        display: flex;
        align-items: center;
        justify-content: space-between;
        height: v-bind('height + 10 + "px"');
        padding: 0 22rpx 0 20rpx;
        background-color: #fff;

        image {
            width: 40rpx;
            padding: 10px;
        }

        .archive-entry {
            height: 56rpx;
            line-height: 56rpx;
            margin: 0;
            padding: 0 18rpx;
            border: 1rpx solid #9bc5ab;
            border-radius: 6rpx;
            color: #1f7a5b;
            font-size: 24rpx;
            background: #f7fbf7;
        }
    }
}
</style>
