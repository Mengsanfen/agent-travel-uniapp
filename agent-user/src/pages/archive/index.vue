<template>
    <view class="page">
        <view class="topbar">
            <button class="back-btn" plain @click="goBack">返回</button>
            <view class="top-copy">
                <text class="eyebrow">旅行档案</text>
                <text class="title">收藏好的行程单</text>
            </view>
        </view>

        <view class="empty" v-if="!loading && archiveList.length === 0">
            <text class="empty-title">还没有收藏行程</text>
            <text class="empty-desc">在聊天回复中点击“收藏到档案”，系统会生成完整 PDF 并保存到这里。</text>
        </view>

        <view class="archive-list" v-else>
            <view class="archive-item" v-for="item in archiveList" :key="item.id">
                <view class="item-head">
                    <view class="item-title-wrap">
                        <text class="item-title">{{ item.title }}</text>
                        <text class="item-time">{{ item.created_at }}</text>
                    </view>
                    <text class="file-badge">{{ item.export_type.toUpperCase() }}</text>
                </view>
                <text class="preview">{{ item.content_preview || '暂无摘要' }}</text>
                <view class="meta-row">
                    <text class="meta-pill">路线 {{ item.route_count }} 组</text>
                    <text class="meta-pill">景点 {{ item.marker_count }} 个</text>
                </view>
                <view class="note" v-if="item.note">
                    <text class="note-text">{{ item.note }}</text>
                </view>
                <view class="item-actions">
                    <button class="action-btn primary" plain @click="openArchive(item)">打开PDF</button>
                    <button class="action-btn" plain @click="editArchive(item)">备注</button>
                    <button class="action-btn danger" plain @click="removeArchive(item)">删除</button>
                </view>
            </view>
        </view>

        <up-loading-page bg-color="#0000002e" :loading="loading"></up-loading-page>
        <up-popup :show="editVisible" mode="center" closeOnClickOverlay @close="editVisible = false">
            <view class="edit-popup">
                <text class="edit-title">编辑档案备注</text>
                <view class="edit-field">
                    <text class="edit-label">标题</text>
                    <input class="edit-input" v-model="editTitle" />
                </view>
                <view class="edit-field">
                    <text class="edit-label">备注</text>
                    <textarea class="edit-textarea" v-model="editNote" maxlength="200" auto-height />
                </view>
                <view class="edit-actions">
                    <button class="edit-btn" plain @click="editVisible = false">取消</button>
                    <button class="edit-btn primary" plain @click="saveEdit">保存</button>
                </view>
            </view>
        </up-popup>
    </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { archiveListApi, baseHttpUrl, deleteArchiveApi, updateArchiveApi } from '@/api/request'
import { useAppStore } from '@/store/index'
import type { TravelArchiveType } from '@/types'

const appStore = useAppStore()
const archiveList = ref<TravelArchiveType[]>([])
const loading = ref(false)
const editVisible = ref(false)
const editingId = ref<number | null>(null)
const editTitle = ref('')
const editNote = ref('')

const loadArchives = async () => {
    loading.value = true
    try {
        const res = await archiveListApi()
        archiveList.value = res.data
    } finally {
        loading.value = false
    }
}

const goBack = () => {
    uni.navigateBack({
        fail: () => uni.reLaunch({ url: '/pages/chat/index' })
    })
}

const openArchive = (item: TravelArchiveType) => {
    uni.showLoading({ title: '正在打开' })
    uni.downloadFile({
        url: `${baseHttpUrl}${item.file_url}`,
        header: { Authorization: `Bearer ${appStore.userInfo?.access_token}` },
        success: (res) => {
            uni.hideLoading()
            if (res.statusCode === 200) {
                uni.openDocument({
                    filePath: res.tempFilePath,
                    fileType: 'pdf',
                    showMenu: true,
                    fail: () => uni.showToast({ title: '文件已下载，打开失败', icon: 'none' })
                })
            } else {
                uni.showToast({ title: '下载失败', icon: 'none' })
            }
        },
        fail: () => {
            uni.hideLoading()
            uni.showToast({ title: '下载失败', icon: 'none' })
        }
    })
}

const editArchive = (item: TravelArchiveType) => {
    editingId.value = item.id
    editTitle.value = item.title
    editNote.value = item.note || ''
    editVisible.value = true
}

const saveEdit = async () => {
    if (!editingId.value) return
    loading.value = true
    try {
        await updateArchiveApi(editingId.value, {
            title: editTitle.value,
            note: editNote.value
        })
        editVisible.value = false
        await loadArchives()
        uni.showToast({ title: '已保存', icon: 'success' })
    } finally {
        loading.value = false
    }
}

const removeArchive = (item: TravelArchiveType) => {
    uni.showModal({
        title: '删除档案',
        content: `确认删除“${item.title}”？PDF记录会从档案中移除。`,
        success: async (res) => {
            if (!res.confirm) return
            loading.value = true
            try {
                await deleteArchiveApi(item.id)
                await loadArchives()
                uni.showToast({ title: '已删除', icon: 'success' })
            } finally {
                loading.value = false
            }
        }
    })
}

onShow(loadArchives)
</script>

<style scoped lang="less">
.page {
    min-height: 100vh;
    padding: 34rpx 26rpx 60rpx;
    box-sizing: border-box;
    background: #f4f8f5;
}

.topbar {
    display: flex;
    align-items: center;
    gap: 18rpx;
    margin-bottom: 28rpx;
}

.back-btn {
    width: 104rpx;
    height: 58rpx;
    line-height: 58rpx;
    margin: 0;
    border: 1rpx solid #9bc5ab;
    border-radius: 6rpx;
    color: #1f7a5b;
    font-size: 24rpx;
    background: #ffffff;
}

.top-copy {
    display: flex;
    flex-direction: column;
}

.eyebrow {
    color: #34725a;
    font-size: 22rpx;
    font-weight: 700;
}

.title {
    margin-top: 4rpx;
    color: #17231f;
    font-size: 42rpx;
    font-weight: 900;
}

.empty {
    margin-top: 140rpx;
    padding: 42rpx;
    border: 1rpx solid #cfe4d2;
    border-radius: 8rpx;
    background: #ffffff;
}

.empty-title {
    display: block;
    color: #1f2f2a;
    font-size: 34rpx;
    font-weight: 800;
}

.empty-desc {
    display: block;
    margin-top: 14rpx;
    color: #5c6b66;
    font-size: 26rpx;
    line-height: 1.6;
}

.archive-list {
    display: flex;
    flex-direction: column;
    gap: 22rpx;
}

.archive-item {
    padding: 24rpx;
    border: 1rpx solid #d5e6dc;
    border-radius: 8rpx;
    background: #ffffff;
}

.item-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 18rpx;
}

.item-title-wrap {
    flex: 1;
    min-width: 0;
}

.item-title {
    display: block;
    color: #17231f;
    font-size: 32rpx;
    font-weight: 800;
    line-height: 1.35;
}

.item-time {
    display: block;
    margin-top: 6rpx;
    color: #7a8883;
    font-size: 22rpx;
}

.file-badge {
    padding: 8rpx 12rpx;
    border-radius: 6rpx;
    color: #ffffff;
    font-size: 22rpx;
    font-weight: 800;
    background: #1f7a5b;
}

.preview {
    display: block;
    margin-top: 18rpx;
    color: #45554f;
    font-size: 25rpx;
    line-height: 1.55;
}

.meta-row {
    display: flex;
    gap: 12rpx;
    margin-top: 16rpx;
}

.meta-pill {
    padding: 7rpx 12rpx;
    border-radius: 6rpx;
    color: #35614f;
    font-size: 22rpx;
    background: #edf6ef;
}

.note {
    margin-top: 16rpx;
    padding: 16rpx;
    border-left: 6rpx solid #d86b3d;
    border-radius: 6rpx;
    background: #fff8f3;
}

.note-text {
    color: #784028;
    font-size: 24rpx;
    line-height: 1.5;
}

.item-actions {
    display: flex;
    gap: 12rpx;
    margin-top: 20rpx;
}

.action-btn {
    flex: 1;
    height: 58rpx;
    line-height: 58rpx;
    margin: 0;
    border: 1rpx solid #b8c9c1;
    border-radius: 6rpx;
    color: #40534d;
    font-size: 24rpx;
    background: #ffffff;
}

.action-btn.primary {
    border-color: #1f7a5b;
    color: #ffffff;
    background: #1f7a5b;
}

.action-btn.danger {
    border-color: #e1b4a4;
    color: #a33f25;
    background: #fff8f3;
}

.edit-popup {
    width: 620rpx;
    padding: 30rpx;
    box-sizing: border-box;
    border-radius: 8rpx;
    background: #ffffff;
}

.edit-title {
    display: block;
    color: #17231f;
    font-size: 34rpx;
    font-weight: 800;
}

.edit-field {
    margin-top: 20rpx;
}

.edit-label {
    display: block;
    margin-bottom: 8rpx;
    color: #40534d;
    font-size: 24rpx;
    font-weight: 700;
}

.edit-input,
.edit-textarea {
    width: 100%;
    min-height: 72rpx;
    padding: 18rpx;
    box-sizing: border-box;
    border: 1rpx solid #bfd8c8;
    border-radius: 6rpx;
    color: #23312d;
    font-size: 26rpx;
}

.edit-actions {
    display: flex;
    gap: 16rpx;
    margin-top: 26rpx;
}

.edit-btn {
    flex: 1;
    height: 64rpx;
    line-height: 64rpx;
    margin: 0;
    border: 1rpx solid #b8c9c1;
    border-radius: 6rpx;
    color: #40534d;
    font-size: 26rpx;
}

.edit-btn.primary {
    border-color: #1f7a5b;
    color: #ffffff;
    background: #1f7a5b;
}
</style>
