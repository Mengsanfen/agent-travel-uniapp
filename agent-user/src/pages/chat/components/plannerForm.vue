<template>
    <view class="planner">
        <view class="planner-head">
            <view>
                <text class="eyebrow">表单规划</text>
                <text class="title">把需求一次说清楚</text>
            </view>
            <text class="mode">保留聊天生成</text>
        </view>

        <view class="field">
            <text class="label">目的地</text>
            <input v-model="form.destination" placeholder="例如：新疆、成都、桂林" />
        </view>

        <view class="row">
            <view class="field half">
                <text class="label">出发日期</text>
                <picker mode="date" :value="form.startDate" @change="onDateChange">
                    <view class="picker-value">{{ form.startDate || '选择日期' }}</view>
                </picker>
            </view>
            <view class="field half">
                <text class="label">天数</text>
                <input v-model.number="form.days" type="number" placeholder="3" />
            </view>
        </view>

        <view class="row">
            <view class="field half">
                <text class="label">同行</text>
                <picker :range="companionOptions" :value="companionIndex" @change="onCompanionChange">
                    <view class="picker-value">{{ form.companions }}</view>
                </picker>
            </view>
            <view class="field half">
                <text class="label">预算</text>
                <picker :range="budgetOptions" :value="budgetIndex" @change="onBudgetChange">
                    <view class="picker-value">{{ form.budget }}</view>
                </picker>
            </view>
        </view>

        <view class="row">
            <view class="field half">
                <text class="label">交通</text>
                <picker :range="transportOptions" :value="transportIndex" @change="onTransportChange">
                    <view class="picker-value">{{ form.transport }}</view>
                </picker>
            </view>
            <view class="field half">
                <text class="label">住宿</text>
                <picker :range="accommodationOptions" :value="accommodationIndex" @change="onAccommodationChange">
                    <view class="picker-value">{{ form.accommodation }}</view>
                </picker>
            </view>
        </view>

        <view class="tag-section">
            <text class="label">偏好</text>
            <view class="tags">
                <text v-for="item in preferenceOptions" :key="item"
                    :class="['tag', form.preferences.includes(item) && 'active']" @click="togglePreference(item)">
                    {{ item }}
                </text>
            </view>
        </view>

        <view class="field">
            <text class="label">额外要求</text>
            <textarea v-model="form.notes" auto-height maxlength="300" placeholder="例如：老人同行、少走路、想看日出、需要清真餐等" />
        </view>

        <button class="submit" :disabled="appStore.disabledStatus" @click="submitPlan">生成完整行程</button>
    </view>
</template>

<script setup lang="ts">
import { reactive, computed } from 'vue'
import { sendMessageApi } from '@/api/request'
import { useAppStore } from '@/store/index'
import type { TripPlannerFormType } from '@/types'

const appStore = useAppStore()

const companionOptions = ['一个人', '情侣', '家庭亲子', '朋友同行', '带老人']
const budgetOptions = ['经济', '舒适', '品质', '轻奢']
const transportOptions = ['公共交通', '自驾', '打车', '步行优先', '混合交通']
const accommodationOptions = ['经济型酒店', '舒适型酒店', '精品民宿', '高端酒店']
const preferenceOptions = ['自然风光', '历史文化', '当地美食', '亲子友好', '轻松慢游', '拍照出片', '小众路线', '购物']

const form = reactive<TripPlannerFormType>({
    destination: '',
    startDate: '',
    days: 3,
    companions: companionOptions[0],
    budget: budgetOptions[1],
    transport: transportOptions[0],
    accommodation: accommodationOptions[1],
    preferences: ['当地美食', '轻松慢游'],
    notes: ''
})

const companionIndex = computed(() => companionOptions.indexOf(form.companions))
const budgetIndex = computed(() => budgetOptions.indexOf(form.budget))
const transportIndex = computed(() => transportOptions.indexOf(form.transport))
const accommodationIndex = computed(() => accommodationOptions.indexOf(form.accommodation))

const onDateChange = (event: { detail: { value: string } }) => {
    form.startDate = event.detail.value
}

const onCompanionChange = (event: { detail: { value: number } }) => {
    form.companions = companionOptions[Number(event.detail.value)]
}

const onBudgetChange = (event: { detail: { value: number } }) => {
    form.budget = budgetOptions[Number(event.detail.value)]
}

const onTransportChange = (event: { detail: { value: number } }) => {
    form.transport = transportOptions[Number(event.detail.value)]
}

const onAccommodationChange = (event: { detail: { value: number } }) => {
    form.accommodation = accommodationOptions[Number(event.detail.value)]
}

const togglePreference = (item: string) => {
    const index = form.preferences.indexOf(item)
    if (index >= 0) {
        form.preferences.splice(index, 1)
    } else {
        form.preferences.push(item)
    }
}

const buildPrompt = () => {
    return [
        `请帮我规划一次${form.destination || '目的地待定'}旅行。`,
        `出发日期：${form.startDate || '未定'}，行程天数：${form.days || 3}天。`,
        `同行情况：${form.companions}；预算档位：${form.budget}；主要交通：${form.transport}；住宿偏好：${form.accommodation}。`,
        `旅行偏好：${form.preferences.length ? form.preferences.join('、') : '无特别偏好'}。`,
        form.notes ? `额外要求：${form.notes}。` : '',
        '请按天输出完整路线规划，包含景点顺序、餐饮建议、住宿建议、天气提醒、预算估算，并尽量调用地图/天气工具生成路线图。'
    ].filter(Boolean).join('\n')
}

const submitPlan = async () => {
    if (!form.destination.trim()) {
        uni.showToast({ title: '请先填写目的地', icon: 'none' })
        return
    }
    if (!form.days || form.days < 1) {
        uni.showToast({ title: '天数至少为 1 天', icon: 'none' })
        return
    }
    await sendMessageApi(buildPrompt())
}
</script>

<style scoped lang="less">
.planner {
    margin: 24rpx;
    padding: 24rpx;
    background: #f7fbf7;
    border: 1rpx solid #cfe4d2;
    border-radius: 8rpx;
}

.planner-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 20rpx;
}

.eyebrow,
.mode {
    display: block;
    color: #34725a;
    font-size: 22rpx;
}

.title {
    display: block;
    margin-top: 4rpx;
    color: #1f2f2a;
    font-size: 36rpx;
    font-weight: 700;
}

.mode {
    padding: 8rpx 12rpx;
    border: 1rpx solid #9bc5ab;
    border-radius: 6rpx;
}

.row {
    display: flex;
    gap: 16rpx;
}

.field,
.tag-section {
    margin-bottom: 16rpx;
}

.half {
    flex: 1;
    min-width: 0;
}

.label {
    display: block;
    margin-bottom: 8rpx;
    color: #4f615b;
    font-size: 24rpx;
    font-weight: 600;
}

input,
textarea,
.picker-value {
    width: 100%;
    min-height: 72rpx;
    padding: 18rpx;
    box-sizing: border-box;
    background: #ffffff;
    border: 1rpx solid #bfd8c8;
    border-radius: 6rpx;
    color: #23312d;
    font-size: 28rpx;
}

textarea {
    min-height: 112rpx;
}

.tags {
    display: flex;
    flex-wrap: wrap;
    gap: 12rpx;
}

.tag {
    padding: 10rpx 16rpx;
    background: #ffffff;
    border: 1rpx solid #bfd8c8;
    border-radius: 6rpx;
    color: #3c514a;
    font-size: 24rpx;
}

.tag.active {
    background: #1f7a5b;
    border-color: #1f7a5b;
    color: #ffffff;
}

.submit {
    margin-top: 8rpx;
    height: 82rpx;
    line-height: 82rpx;
    background: #e55934;
    color: #ffffff;
    border-radius: 8rpx;
    font-size: 30rpx;
    font-weight: 700;
}

.submit[disabled] {
    background: #b8c4bf;
    color: #ffffff;
}
</style>
