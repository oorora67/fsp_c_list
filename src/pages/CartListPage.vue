<template>
  <div class="list-page">
    <h1>リスト</h1>
    <Cart :cart="cart" :tagOrder="tagOrder" :products="products" 
      @remove-from-cart="removeFromCart" 
      @update-quantity="updateCartQuantity" />
    <button @click="goBackWithCart">← 商品一覧へ戻る</button>
  </div>
</template>

<script setup>
import Cart from "../components/Cart.vue";
import { ref, computed, watch } from "vue";
import productsData from "../products.js";
import { encodeCartForUrlBrotli, decodeCartFromUrlBrotli } from '../utils/cartCrypto';
import { useRoute, useRouter } from 'vue-router';

// 商品データ
const productsRaw = ref(productsData);
const products = computed(() => productsRaw.value);

// タグ順序（App.vueと同じロジックを必要に応じて追加）
const tagOrder = computed(() => {
  const tagFlagTrue = productsRaw.value.filter(p => p.tagFlag);
  const gens = [], talents = [], cats = [];
  tagFlagTrue.forEach((p) => {
    (Array.isArray(p.generation) ? p.generation : (p.generation ? [p.generation] : [])).forEach(g => { if (g && !gens.includes(g)) gens.push(g); });
    (Array.isArray(p.talent) ? p.talent : (p.talent ? [p.talent] : [])).forEach(t => { if (t && !talents.includes(t)) talents.push(t); });
    (Array.isArray(p.category) ? p.category : (p.category ? [p.category] : [])).forEach(c => { if (c && !cats.includes(c)) cats.push(c); });
  });
  return { generation: gens, talent: talents, category: cats };
});

const route = useRoute();
const router = useRouter();
const cart = ref([]);

// URLから暗号化データを取得し復号化
if (route.query.d) {
  cart.value = decodeCartFromUrlBrotli(route.query.d, products.value);
}

// URLのdataクエリが変化したらcartも更新
watch(
  () => route.query.d,
  (val) => {
    if (val) {
      cart.value = decodeCartFromUrlBrotli(val, products.value);
    } else {
      cart.value = [];
    }
  }
);

function removeFromCart(productId) {
  // route.query.dataがあればそちらをベースに編集
  let baseCart = cart.value;
  const idx = baseCart.findIndex((item) => item.product.id === productId);
  if (idx !== -1) baseCart.splice(idx, 1);
  cart.value = baseCart;
  // URLも更新
  updateUrlWithCart();
}
function updateCartQuantity(productId, newQty) {
  if (newQty > 255) {
    alert('数量は255以下で入力してください');
    return;
  }
  let baseCart = cart.value;
  const idx = baseCart.findIndex((item) => item.product.id === productId);
  if (idx !== -1) baseCart[idx].quantity = newQty;
  cart.value = baseCart;
  updateUrlWithCart();
}
function updateUrlWithCart() {
  const enc = cart.value.length ? encodeCartForUrlBrotli(cart.value) : '';
  router.replace({ path: '/list', query: enc ? { d: enc } : {} });
}

// 戻るボタンでリストデータをURLに付与して遷移
function goBackWithCart() {
  const enc = cart.value.length ? encodeCartForUrlBrotli(cart.value) : '';
  router.push({ path: '/', query: enc ? { d: enc } : {} });
}
</script>

<style scoped>
.list-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 2em 1em;
  background: #fff;
}
h1,
h2 {
  margin-top: 1em;
  color: #1976d2;
  text-shadow: 0 1px 4px #e3f2fd;
}
</style>
