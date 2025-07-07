<template>
  <div>
    <div>
      <button @click="sortByTag('generation')">ユニット順</button>
      <button @click="sortByTag('talent')">タレント順</button>
      <button @click="sortByTag('category')">カテゴリ順</button>
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
            <td data-label="数量">{{ item.quantity }}</td>
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
import { ref, computed, nextTick } from "vue";
import html2canvas from "html2canvas";
const props = defineProps({
  cart: Array,
  tagOrder: Object,
  products: Array,
});
const emit = defineEmits(["remove-from-cart"]);
const sortKey = ref("generation");
const isDownloadingImage = ref(false);
const sortedCart = computed(() => {
  const key = sortKey.value;
  const order = props.tagOrder[key];
  return [...props.cart].sort((a, b) => {
    const aIdx = order.indexOf(a.product[key]);
    const bIdx = order.indexOf(b.product[key]);
    if (aIdx !== bIdx) return aIdx - bIdx;
    return a.product.id - b.product.id;
  });
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
    link.href = canvas.toDataURL("image/png");
    link.download = "cart.png";
    link.click();
  });
  isDownloadingImage.value = false;
}
function removeItem(productId) {
  emit("remove-from-cart", productId);
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
  text-align: right;
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
