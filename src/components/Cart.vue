<template>
  <div>
    <div>
      <!--<button @click="sortByTag('generation')">ユニット順</button>-->
      <!--<button @click="sortByTag('talent')">タレント順</button>-->
      <!--<button @click="sortByTag('category')">カテゴリ順</button>-->
      <button @click="downloadImage">画像保存</button>
    </div>
    <div id="cart-list-image">
      <table border="1" style="margin-top: 1em; width: 100%">
        <thead>
          <tr>
            <th>商品名</th>
            <th>値段</th>
            <th>数量</th>
            <th>合計</th>
            <th v-if="!isDownloadingImage"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in sortedCart" :key="item.product.id">
            <td data-label="商品名">
              <div class="cart-product-name">{{ item.product.name }}</div>
            </td>
            <td data-label="値段" class="cart-product-price">￥{{ item.product.price.toLocaleString() }}</td>
            <td data-label="数量">
              <template v-if="!isDownloadingImage">
                <div class="qty-row-amazon">
                  <input type="number" v-model.number="localQuantities[item.product.id]" min="1" class="qty-input" @change="onQtyInput(item.product.id)" />
                </div>
              </template>
              <template v-else>
                {{ item.quantity }}
              </template>
            </td>
            <td data-label="合計">
              ￥{{ (item.product.price * item.quantity).toLocaleString() }}
            </td>
            <td v-if="!isDownloadingImage" data-label="操作">
              <button @click="removeItem(item.product.id)" class="remove-btn">削除</button>
            </td>
          </tr>
          <tr class="cart-total-row">
            <td colspan="3" style="text-align:right; font-weight:bold; color:#1976d2;" data-label="合計金額">
              合計金額
            </td>
            <td style="font-weight:bold; color:#d32f2f;" data-label="合計">
              ￥{{ totalPrice.toLocaleString() }}
            </td>
            <td v-if="!isDownloadingImage"></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch } from "vue";
import html2canvas from "html2canvas";
const props = defineProps({
  cart: Array,
  tagOrder: Object,
  products: Array,
});
const emit = defineEmits(["remove-from-cart"]);
const sortKey = ref("generation");
const isDownloadingImage = ref(false);
// 商品ソート用共通関数（ProductList.vueと同じロジック、タグ数優先）
function sortProductsByTagOrder(list, tagOrder) {
  const genOrder = tagOrder.generation;
  const talentOrder = tagOrder.talent;
  const catOrder = tagOrder.category;
  return list.slice().sort((a, b) => {
    const aGenArr = [].concat(a.product ? a.product.generation : a.generation || []);
    const bGenArr = [].concat(b.product ? b.product.generation : b.generation || []);
    if (aGenArr.length !== bGenArr.length) return bGenArr.length - aGenArr.length;
    const aGenIdx = Math.min(...aGenArr.map(g => genOrder.indexOf(g)).filter(i => i >= 0), 9999);
    const bGenIdx = Math.min(...bGenArr.map(g => genOrder.indexOf(g)).filter(i => i >= 0), 9999);
    if (aGenIdx !== bGenIdx) return aGenIdx - bGenIdx;
    const aTalArr = [].concat(a.product ? a.product.talent : a.talent || []);
    const bTalArr = [].concat(b.product ? b.product.talent : b.talent || []);
    if (aTalArr.length !== bTalArr.length) return bTalArr.length - aTalArr.length;
    const aTalIdx = Math.min(...aTalArr.map(t => talentOrder.indexOf(t)).filter(i => i >= 0), 9999);
    const bTalIdx = Math.min(...bTalArr.map(t => talentOrder.indexOf(t)).filter(i => i >= 0), 9999);
    if (aTalIdx !== bTalIdx) return aTalIdx - bTalIdx;
    const aCatArr = [].concat(a.product ? a.product.category : a.category || []);
    const bCatArr = [].concat(b.product ? b.product.category : b.category || []);
    if (aCatArr.length !== bCatArr.length) return bCatArr.length - aCatArr.length;
    const aCatIdx = Math.min(...aCatArr.map(c => catOrder.indexOf(c)).filter(i => i >= 0), 9999);
    const bCatIdx = Math.min(...bCatArr.map(c => catOrder.indexOf(c)).filter(i => i >= 0), 9999);
    if (aCatIdx !== bCatIdx) return aCatIdx - bCatIdx;
    if (a.product && b.product) {
      if (!isNaN(Number(a.product.id)) && !isNaN(Number(b.product.id))) {
        return Number(a.product.id) - Number(b.product.id);
      }
      return String(a.product.id).localeCompare(String(b.product.id), 'ja');
    } else {
      if (!isNaN(Number(a.id)) && !isNaN(Number(b.id))) {
        return Number(a.id) - Number(b.id);
      }
      return String(a.id).localeCompare(String(b.id), 'ja');
    }
  });
}

const sortedCart = computed(() => {
  return sortProductsByTagOrder(props.cart, props.tagOrder);
});
const totalPrice = computed(() =>
  props.cart.reduce((sum, item) => sum + item.product.price * item.quantity, 0)
);
function sortByTag(key) {
  sortKey.value = key;
}
async function downloadImage() {
  isDownloadingImage.value = true;
  await nextTick();
  const el = document.getElementById("cart-list-image");
  await html2canvas(el).then((canvas) => {
    const link = document.createElement("a");
    // タイムスタンプ付きファイル名生成
    const now = new Date();
    const pad = (n) => n.toString().padStart(2, '0');
    const y = now.getFullYear();
    const m = pad(now.getMonth() + 1);
    const d = pad(now.getDate());
    const h = pad(now.getHours());
    const min = pad(now.getMinutes());
    const s = pad(now.getSeconds());
    const filename = `c106-fsp_${y}${m}${d}${h}${min}${s}.png`;
    link.href = canvas.toDataURL("image/png");
    link.download = filename;
    link.click();
  });
  isDownloadingImage.value = false;
}
function removeItem(productId) {
  emit("remove-from-cart", productId);
}
// 数量変更用ローカル状態
const localQuantities = ref({});
watch(
  () => props.cart.map(item => ({ id: item.product.id, quantity: item.quantity })),
  (val) => {
    val.forEach((item) => {
      // localQuantitiesに未定義（undefinedやnull、空文字、NaNも含む）の場合のみ初期化
      if (
        localQuantities.value[item.id] === undefined ||
        localQuantities.value[item.id] === null ||
        localQuantities.value[item.id] === '' ||
        isNaN(localQuantities.value[item.id])
      ) {
        localQuantities.value[item.id] = item.quantity;
      }
    });
  },
  { immediate: true }
);
function changeQty(id, diff) {
  const newVal = Math.max(1, (localQuantities.value[id] || 1) + diff);
  localQuantities.value[id] = newVal;
  emit('update-quantity', id, newVal);
}
function onQtyInput(id) {
  const newVal = Math.max(1, Number(localQuantities.value[id]) || 1);
  localQuantities.value[id] = newVal;
  emit('update-quantity', id, newVal);
}
</script>

<style scoped>
.remove-btn {
  background: #d32f2f;
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 0.5em 0.5em;
  cursor: pointer;
  font-size: 0.75em;
  transition: background 0.2s;
}
.remove-btn:hover {
  background: #a31515;
}
table {
  background: #fff;
  border-collapse: collapse;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}
thead th {
  background: #f5f5f5;
  color: #1976d2;
  font-weight: bold;
  font-size: 0.8em;
  border-bottom: 2px solid #e0e0e0;
}
td,
th {
  border: 1px solid #e0e0e0;
  padding: 0.5em 0.7em;
  text-align: left;
  vertical-align: middle;
  color: #222;
}
thead th:nth-child(1),
tbody td:nth-child(1) {
  width: 1%;
  min-width: 200px;
  max-width: 200px;
  text-align: left;
  padding-left: 0.2em;
  padding-right: 0.2em;
  font-size: clamp(0.8em, 1.2vw, 1.0em);
}
thead th:nth-child(2),
tbody td:nth-child(2) {
  width: 1%;
  min-width: 65px;
  max-width: 65px;
  text-align: right;
  padding-left: 0.2em;
  padding-right: 0.2em;
  font-size: clamp(0.8em, 1.2vw, 1.0em);
}
thead th:nth-child(3),
tbody td:nth-child(3) {
  width: 1%;
  min-width: 28px;
  max-width: 60px;
  text-align: right;
  padding-left: 0.2em;
  padding-right: 0.2em;
  font-size: clamp(0.8em, 1.2vw, 1.0em);
}
thead th:nth-child(4),
tbody td:nth-child(4) {
  width: 1%;
  min-width: 75px;
  max-width: 80px;
  text-align: right !important;
  padding-left: 0.1em;
  padding-right: 0.1em;
  font-size: clamp(0.8em, 1.2vw, 1.0em);
}
thead th:last-child,
tbody td:last-child {
  width: 1%;
  min-width: 38px;
  max-width: 40px;
  text-align: center;
  padding-left: 0.01em;
  padding-right: 0.01em;
  font-size: 0.85em;
}
tbody tr:nth-child(even) {
  background: #fafbfc;
}
tbody tr:nth-child(odd) {
  background: #fff;
}
body,
#cart-list-image {
  background: #f8f9fa;
}
.cart-total-row {
  background: #f1f8e9;
}
.cart-product-name {
  font-weight: bold;
  color: #222;
  font-size: 1em;
}
.cart-product-price {
  color: #1976d2;
  font-size: 0.6em;
  margin-top: 0.1em;
  margin-bottom: 0.1em;
}
.cart-total-row td[data-label="合計"] {
  min-width: 75px;
  max-width: 60px;
  font-size: 0.92em;
  text-align: right;
  padding-left: 0.1em;
  padding-right: 0.1em;
}
.qty-row-amazon {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  gap: 0.3em;
  justify-content: center !important;
  overflow-x: auto;
  max-width: 100%;
  box-sizing: border-box;
  margin-top: 0.5em;
}
.qty-input {
  width: 2.2em;
  min-width: 0;
  max-width: 100%;
  text-align: right;
  font-size: 1em;
  letter-spacing: 0.05em;
}
@media (max-width: 600px) {
  table,
  thead,
  tbody {
    width: 100% !important;
    box-sizing: border-box;
  }
  th,
  td {
    padding: 0.4em 0.3em;
    font-size: 0.95em;
    word-break: break-word;
  }
  th:nth-child(4),
  td:nth-child(4) {
    text-align: right !important;
  }
  .cart-total-row td {
    text-align: right;
    padding-left: 0;
    background: #f1f8e9;
    font-size: 1.1em;
  }
  .cart-product-name {
    font-size: 0.98em;
  }
  .cart-product-price {
    font-size: 0.88em;
  }
}
</style>
