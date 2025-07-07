<script setup>
import ProductList from "./components/ProductList.vue";
import Cart from "./components/Cart.vue";
import { ref, computed } from "vue";
import productsData from "./products.js";

// 商品データ（外部ファイルから）
const productsRaw = ref(productsData);

// 商品データからタグ一覧を自動生成
const tagOrder = computed(() => {
  const gens = [];
  const talents = [];
  const cats = [];
  productsRaw.value.forEach((p) => {
    (Array.isArray(p.generation) ? p.generation : (p.generation ? [p.generation] : [])).forEach(g => { if (g && !gens.includes(g)) gens.push(g); });
    (Array.isArray(p.talent) ? p.talent : (p.talent ? [p.talent] : [])).forEach(t => { if (t && !talents.includes(t)) talents.push(t); });
    (Array.isArray(p.category) ? p.category : (p.category ? [p.category] : [])).forEach(c => { if (c && !cats.includes(c)) cats.push(c); });
  });
  return {
    generation: gens,
    talent: talents,
    category: cats,
  };
});

// 商品一覧はタグ順でソート
const products = computed(() => {
  return productsRaw.value.slice().sort((a, b) => {
    // ジェネレーション
    const genA = Math.min(...(a.generation ? [].concat(a.generation) : []).map(g => tagOrder.value.generation.indexOf(g)).filter(i => i >= 0));
    const genB = Math.min(...(b.generation ? [].concat(b.generation) : []).map(g => tagOrder.value.generation.indexOf(g)).filter(i => i >= 0));
    if (genA !== genB) return genA - genB;
    // タレント
    const talA = Math.min(...(a.talent ? [].concat(a.talent) : []).map(t => tagOrder.value.talent.indexOf(t)).filter(i => i >= 0));
    const talB = Math.min(...(b.talent ? [].concat(b.talent) : []).map(t => tagOrder.value.talent.indexOf(t)).filter(i => i >= 0));
    if (talA !== talB) return talA - talB;
    // カテゴリ
    const catA = Math.min(...(a.category ? [].concat(a.category) : []).map(c => tagOrder.value.category.indexOf(c)).filter(i => i >= 0));
    const catB = Math.min(...(b.category ? [].concat(b.category) : []).map(c => tagOrder.value.category.indexOf(c)).filter(i => i >= 0));
    return catA - catB;
  });
});

// カート情報
const cart = ref([]);

// タグ順序の更新
function updateTagOrder(type, newOrder) {
  tagOrder.value[type] = newOrder;
}

// カートに商品追加
function addToCart(product, quantity) {
  const idx = cart.value.findIndex((item) => item.product.id === product.id);
  if (idx !== -1) {
    cart.value[idx].quantity += quantity;
  } else {
    cart.value.push({ product, quantity });
  }
}

// カートから商品削除
function removeFromCart(productId) {
  const idx = cart.value.findIndex((item) => item.product.id === productId);
  if (idx !== -1) {
    cart.value.splice(idx, 1);
  }
}
</script>

<template>
  <div>
    <h1>商品一覧</h1>
    <ProductList
      :products="products"
      :tagOrder="tagOrder"
      @add-to-cart="addToCart"
    />
    <h2>リスト</h2>
    <Cart
      :cart="cart"
      :tagOrder="tagOrder"
      :products="products"
      @remove-from-cart="removeFromCart"
    />
    <!-- タグ順序設定UIは後で追加 -->
  </div>
</template>

<style scoped>
.logo {
  height: 6em;
  padding: 1.5em;
  will-change: filter;
  transition: filter 300ms;
}
.logo:hover {
  filter: drop-shadow(0 0 2em #646cffaa);
}
.logo.vue:hover {
  filter: drop-shadow(0 0 2em #42b883aa);
}
h1,
h2 {
  margin-top: 1em;
  color: #1976d2;
  text-shadow: 0 1px 4px #e3f2fd;
}
</style>
