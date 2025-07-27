<template>
  <div>
    <h1>商品一覧</h1>
    <p>このサイトは、非公式です。<br></p>
    <p><a href="https://firststage-pro.com/">FIRST STAGE PRODUCTION</a>の公式サイトではありません。</p>
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
      @update-quantity="updateCartQuantity"
    />
    <router-link :to="cartLink">
      <button class="to-cart-btn">リストページへ</button>
    </router-link>
  </div>
</template>

<script setup>
import ProductList from "../components/ProductList.vue";
import Cart from "../components/Cart.vue";
import { ref, computed, watch } from "vue";
import productsData from "../products.js";
import { useRoute, useRouter } from 'vue-router';
import { encodeCartForUrlBrotli, decodeCartFromUrlBrotli } from '../utils/cartCrypto';

const productsRaw = ref(productsData);
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
const products = computed(() => {
  const tagFlagTrue = productsRaw.value.filter(p => p.tagFlag);
  const genOrder = [], talentOrder = [], catOrder = [];
  tagFlagTrue.forEach((p) => {
    (Array.isArray(p.generation) ? p.generation : (p.generation ? [p.generation] : [])).forEach(g => { if (g && !genOrder.includes(g)) genOrder.push(g); });
    (Array.isArray(p.talent) ? p.talent : (p.talent ? [p.talent] : [])).forEach(t => { if (t && !talentOrder.includes(t)) talentOrder.push(t); });
    (Array.isArray(p.category) ? p.category : (p.category ? [p.category] : [])).forEach(c => { if (c && !catOrder.includes(c)) catOrder.push(c); });
  });
  return productsRaw.value.slice().sort((a, b) => {
    const genA = Math.min(...(a.generation ? [].concat(a.generation) : []).map(g => genOrder.indexOf(g)).filter(i => i >= 0));
    const genB = Math.min(...(b.generation ? [].concat(b.generation) : []).map(g => genOrder.indexOf(g)).filter(i => i >= 0));
    if (genA !== genB) return genA - genB;
    const talA = Math.min(...(a.talent ? [].concat(a.talent) : []).map(t => talentOrder.indexOf(t)).filter(i => i >= 0));
    const talB = Math.min(...(b.talent ? [].concat(b.talent) : []).map(t => talentOrder.indexOf(t)).filter(i => i >= 0));
    if (talA !== talB) return talA - talB;
    const catA = Math.min(...(a.category ? [].concat(a.category) : []).map(c => catOrder.indexOf(c)).filter(i => i >= 0));
    const catB = Math.min(...(b.category ? [].concat(b.category) : []).map(c => catOrder.indexOf(c)).filter(i => i >= 0));
    if (catA !== catB) return catA - catB;
    if (!isNaN(Number(a.id)) && !isNaN(Number(b.id))) {
      return Number(a.id) - Number(b.id);
    }
    return String(a.id).localeCompare(String(b.id), 'ja');
  });
});
const route = useRoute();
const router = useRouter();
const cart = ref([]);
if (route.query.d) {
  cart.value = decodeCartFromUrlBrotli(route.query.d, products.value);
}
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
watch(
  cart,
  (newCart) => {
    const enc = newCart.length ? encodeCartForUrlBrotli(newCart) : undefined;
    const currentD = route.query.d;
    if ((enc || '') !== (currentD || '')) {
      router.replace({
        query: {
          ...route.query,
          d: enc || undefined,
        },
      });
    }
  },
  { deep: true }
);
const cartLink = computed(() => {
  if (route.query.d) {
    return `/list?d=${route.query.d}`;
  }
  if (!cart.value.length) return '/list';
  const enc = encodeCartForUrlBrotli(cart.value);
  return `/list?d=${enc}`;
});
function addToCart(product, quantity) {
  if (quantity > 255) {
    alert('数量は255以下で入力してください');
    return;
  }
  const idx = cart.value.findIndex((item) => item.product.id === product.id);
  if (idx !== -1) {
    const newQty = cart.value[idx].quantity + quantity;
    if (newQty > 255) {
      alert('合計数量が255以下になるようにしてください');
      return;
    }
    cart.value = cart.value.map((item, i) =>
      i === idx ? { ...item, quantity: newQty } : item
    );
  } else {
    cart.value = [...cart.value, { product, quantity }];
  }
}
function removeFromCart(productId) {
  const idx = cart.value.findIndex((item) => item.product.id === productId);
  if (idx !== -1) cart.value.splice(idx, 1);
}
function updateCartQuantity(productId, newQty) {
  if (newQty > 255) {
    alert('数量は255以下で入力してください');
    return;
  }
  const idx = cart.value.findIndex((item) => item.product.id === productId);
  if (idx !== -1) {
    cart.value = cart.value.map((item, i) =>
      i === idx ? { ...item, quantity: newQty } : item
    );
  }
}
</script>

<style scoped>
.to-cart-btn {
  margin-bottom: 1em;
  background: #1976d2;
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 0.5em 1.2em;
  font-size: 1.1em;
  font-weight: bold;
  cursor: pointer;
}
h1,
h2,
p {
  margin-top: 1em;
  color: #1976d2;
  text-shadow: 0 1px 4px #e3f2fd;
}
</style>
