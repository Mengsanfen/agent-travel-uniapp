<script setup lang="ts">
import { onLaunch, onShow, onHide } from "@dcloudio/uni-app";
import { useAppStore } from '@/store/index'
import { conversationListApi, getQuickQuestionApi } from "./api/request";
const appStore = useAppStore()

onLaunch(async () => {
  console.log("App Launch");
  appStore.messageList = []
  appStore.mapDataList = []
  appStore.newSessionData = []
  appStore.historyToolList = []
  // 鑾峰彇鑳跺泭鎸夐挳鍧愭爣
  const buttonPosition = uni.getStorageSync('buttonPosition')
  if (!buttonPosition) {
    const res = uni.getMenuButtonBoundingClientRect()
    // 瀛樺偍鏈湴缂撳瓨
    uni.setStorageSync('buttonPosition', res)
  }
  // 鑾峰彇瀵硅瘽鍒楄〃鏁版嵁
  const res = await conversationListApi()
  appStore.conversationList = res.data
  if (appStore.selectedThreadId != '') {
    appStore.getContent(appStore.selectedThreadId)
  } else {
    appStore.cardSkeleton = true
    const res = await getQuickQuestionApi()
    appStore.CardDataList = res.data
    appStore.cardSkeleton = false
  }
  if (appStore.userInfo?.access_token) {
    appStore.connectWebSocket()
  }

});
onShow(() => {
  console.log("App Show");
});
onHide(() => {
  console.log("App Hide");
});
</script>
<style lang="scss">
/* 娉ㄦ剰瑕佸啓鍦ㄧ涓€琛岋紝鍚屾椂缁檚tyle鏍囩鍔犲叆lang="scss"灞炴€?*/
@import "uview-plus/index.scss";
</style>
