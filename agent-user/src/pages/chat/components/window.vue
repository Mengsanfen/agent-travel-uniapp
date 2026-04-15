<template>
    <view class="outer">
        <template v-for="(item, index) in appStore.messageList" :key="index">
            <!-- 用户消息 -->
            <view class="user-message" v-if="item.role === 'user'">
                <text>{{ item.content }}</text>
            </view>
            <!-- 工具回复的消息 -->
            <view class="tool-message" v-if="item.role === 'assistant' && item.toolList && item.toolList.length">
                <text>{{ item.toolThinking ? '分析思考中...' : '分析思考完毕' }}</text>
                <!-- <ToolSteps :tool-list="item.toolList" /> -->
                <up-steps :current="item.toolList.length - 1" direction="column" :dot="true">
                    <up-steps-item :title="step" v-for="(step, index) in item.toolList" :key="`${step}-${index}`" />
                </up-steps>
            </view>
            <!-- 模型回复的消息 -->
            <view class="ai-message" v-if="item.role === 'assistant' && item.content != ''">
                <up-markdown :content="item.content" />
                <view class="message-actions">
                    <button plain :disabled="item.loading || item.toolThinking || item.modelSuccess === false" @click="exportTravelReport(item)">导出完整行程PDF</button>
                    <button class="archive-btn" plain :disabled="item.loading || item.toolThinking || item.modelSuccess === false" @click="openArchivePopup(item)">收藏到档案</button>
                </view>
                <!-- 地图 -->
                <Map style="width: 100%;height: auto;" v-if="item.mapDataList && item.mapDataList.length > 0"
                    :map-data-list="item.mapDataList" />
            </view>
            <up-skeleton v-if="item.loading" style="margin-top: 30rpx;" rows="4" :loading="true" :title="false">
                <up-text>loading为false时，将会展示此处插槽内容</up-text>
            </up-skeleton>
            <!-- 地图数据 -->
            <!-- <view class="view-map" v-if="item.role == 'assistant' && item.content && item.modelSuccess">
                <Map style="width: 100%;height: auto;" :index="index"
                    v-if="item.locationData && item.locationData.length > 0" />
                <view class="map-seek" @click="getLoacationData(item.content, index)"
                    v-if="!item.locationData && !item.mapLoading">
                    <text>查看地图规划</text>
                    <text class="map-seek-text">点击查看</text>
                </view>
                <up-skeleton v-if="item.mapLoading" style="margin-top: 30rpx;" rows="4" :loading="true" :title="false">
                    <up-text>loading为false时，将会展示此处插槽内容</up-text>
                </up-skeleton>
            </view> -->
        </template>
    </view>
    <up-popup :show="archivePopupVisible" mode="center" closeOnClickOverlay @close="archivePopupVisible = false">
        <view class="archive-popup">
            <text class="archive-title">收藏行程档案</text>
            <text class="archive-desc">保存后会生成一份完整 PDF，并记录在行程档案中。</text>
            <view class="archive-field">
                <text class="archive-label">标题</text>
                <input class="archive-input" v-model="archiveTitle" placeholder="例如：新疆 5 日家庭游" />
            </view>
            <view class="archive-field">
                <text class="archive-label">备注</text>
                <textarea class="archive-textarea" v-model="archiveNote" maxlength="200" auto-height placeholder="例如：已订酒店、适合带老人、出发前再确认天气" />
            </view>
            <view class="archive-actions">
                <button class="archive-action-btn" plain @click="archivePopupVisible = false">取消</button>
                <button class="archive-action-btn primary" plain @click="saveArchive">保存档案</button>
            </view>
        </view>
    </up-popup>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ToolSteps from './toolSteps.vue';
const { top, bottom, right } = uni.getStorageSync("buttonPosition")
import Map from '../components/map.vue'
import { useAppStore } from '@/store/index'
import { archivePlanApi, baseHttpUrl, exportPlanPdfApi, getLoacationDataApi } from '@/api/request';
import type { MessageListType } from '@/types'
const appStore = useAppStore()
const archivePopupVisible = ref(false)
const archiveTarget = ref<MessageListType | null>(null)
const archiveTitle = ref('旅行规划报告')
const archiveNote = ref('')

const canArchive = (item: MessageListType) => {
    return Boolean(item.content.trim()) && !item.loading && !item.toolThinking && item.modelSuccess !== false
}

const guessArchiveTitle = (content: string) => {
    const line = content.split('\n').map(item => item.replace(/[#*`>]/g, '').trim()).find(Boolean)
    return line?.slice(0, 24) || '旅行规划报告'
}

const exportTravelReport = async (item: MessageListType) => {
    if (item.loading || item.toolThinking || item.modelSuccess === false) {
        uni.showToast({ title: '请等待行程和路线生成完成后再导出', icon: 'none' })
        return
    }
    if (!item.content.trim()) return
    try {
        uni.showLoading({ title: '正在生成行程PDF' })
        const res = await exportPlanPdfApi({
            title: '旅行规划报告',
            content: item.content,
            maps: item.mapDataList || [],
            export_type: 'pdf'
        })
        uni.downloadFile({
            url: `${baseHttpUrl}${res.data.url}`,
            header: { Authorization: `Bearer ${appStore.userInfo?.access_token}` },
            success: (downloadRes) => {
                uni.hideLoading()
                if (downloadRes.statusCode === 200) {
                    uni.openDocument({
                        filePath: downloadRes.tempFilePath,
                        fileType: 'pdf',
                        showMenu: true,
                        fail: () => uni.showToast({ title: 'PDF已生成，打开失败', icon: 'none' })
                    })
                } else {
                    uni.showToast({ title: '下载PDF失败', icon: 'none' })
                }
            },
            fail: () => {
                uni.hideLoading()
                uni.showToast({ title: '下载PDF失败', icon: 'none' })
            }
        })
    } catch (error) {
        uni.hideLoading()
        uni.showToast({ title: '生成PDF失败', icon: 'none' })
    }
}

const openArchivePopup = (item: MessageListType) => {
    if (!canArchive(item)) {
        uni.showToast({ title: '请等待行程和路线生成完成后再收藏', icon: 'none' })
        return
    }
    archiveTarget.value = item
    archiveTitle.value = guessArchiveTitle(item.content)
    archiveNote.value = ''
    archivePopupVisible.value = true
}

const saveArchive = async () => {
    const item = archiveTarget.value
    if (!item) return
    try {
        uni.showLoading({ title: '正在保存档案' })
        await archivePlanApi({
            title: archiveTitle.value.trim() || '旅行规划报告',
            content: item.content,
            maps: item.mapDataList || [],
            export_type: 'pdf',
            source_thread_id: appStore.selectedThreadId,
            note: archiveNote.value
        })
        archivePopupVisible.value = false
        uni.showToast({ title: '已收藏到档案', icon: 'success' })
    } catch (error) {
        uni.showToast({ title: '收藏失败', icon: 'none' })
    } finally {
        uni.hideLoading()
    }
}

// 请求地图数据
// const getLoacationData = async (content: string, index: number) => {
//     const messageObj = appStore.messageList[index]
//     messageObj.mapLoading = true
//     const res = await getLoacationDataApi({ content })
//     const mapId = String(Date.now() + index)
//     messageObj.mapId = mapId
//     messageObj.locationData = res.data
//     // 更新地图, 默认展示第一天数据
//     appStore.changeDay(index, 0)
//     messageObj.mapLoading = false
// }
</script>

<style scoped lang="less">
.outer {
    padding-top: v-bind('bottom + 10 + "px"');
    display: flex;
    flex-direction: column;
    margin: 0 15rpx;
    padding-bottom: 250rpx;

    .user-message {
        margin-top: 30rpx;
        max-width: 70%;
        align-self: flex-end;
        background-color: #3a71e8;
        padding: 10rpx;
        color: #fff;
        border-radius: 10rpx;

        text {
            line-height: 1.5;
            font-size: 30rpx;
        }
    }

    .tool-message {
        margin-top: 30rpx;
        background-color: #eee;
        padding: 10rpx;
        border-radius: 10rpx;
        font-size: 30rpx;

        text {
            font-weight: bold;
            color: darkmagenta;
            padding-bottom: 6rpx;
        }
    }

    .ai-message {
        margin-top: 30rpx;
        background-color: #fff;
        padding: 10rpx;
        border-radius: 8rpx;
        border: 1rpx solid #e1e8e4;
    }

    .message-actions {
        display: flex;
        justify-content: flex-end;
        margin-top: 16rpx;

        button {
            height: 56rpx;
            line-height: 56rpx;
            margin: 0;
            padding: 0 18rpx;
            border: 1rpx solid #1f7a5b;
            border-radius: 6rpx;
            color: #1f7a5b;
            font-size: 24rpx;
            background: #f7fbf7;
        }

        .archive-btn {
            margin-left: 12rpx;
            border-color: #d86b3d;
            color: #b75129;
            background: #fff8f3;
        }
    }

    .view-map {
        background-color: #8bffff;
        border-radius: 15rpx;
        padding: 20rpx;
        margin: 40rpx 0;
        font-size: 30rpx;
        color: #5ea5f5;

        .map-seek {
            display: flex;
            justify-content: space-between;
        }

        .map-seek-text {
            font-size: 25rpx;
        }
    }
}

.archive-popup {
    width: 620rpx;
    padding: 30rpx;
    box-sizing: border-box;
    background: #ffffff;
    border-radius: 8rpx;
}

.archive-title {
    display: block;
    color: #17231f;
    font-size: 34rpx;
    font-weight: 800;
}

.archive-desc {
    display: block;
    margin-top: 10rpx;
    color: #64726d;
    font-size: 24rpx;
    line-height: 1.5;
}

.archive-field {
    margin-top: 22rpx;
}

.archive-label {
    display: block;
    margin-bottom: 8rpx;
    color: #40534d;
    font-size: 24rpx;
    font-weight: 700;
}

.archive-input,
.archive-textarea {
    width: 100%;
    min-height: 72rpx;
    padding: 18rpx;
    box-sizing: border-box;
    border: 1rpx solid #bfd8c8;
    border-radius: 6rpx;
    color: #23312d;
    font-size: 26rpx;
}

.archive-actions {
    display: flex;
    gap: 16rpx;
    margin-top: 26rpx;
}

.archive-action-btn {
    flex: 1;
    height: 64rpx;
    line-height: 64rpx;
    border-radius: 6rpx;
    border: 1rpx solid #b8c9c1;
    color: #40534d;
    font-size: 26rpx;
}

.archive-actions .primary {
    border-color: #1f7a5b;
    background: #1f7a5b;
    color: #ffffff;
}
</style>
