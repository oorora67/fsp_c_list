<template>
  <div class="product-list-amazon">
    <!-- タグ一覧バー（種類ごとに分割、複数選択対応） -->
    <div class="tag-list-bar">
      <div class="tag-list-group">
        <span class="tag-list-label">ユニット</span>
        <span v-for="gen in sortedUnique(flattenTagArray(tagOrder.generation), 'generation')" :key="'gen-'+gen" class="tag-badge tag-list-badge generation-badge" :class="{ selected: selectedTag.generation.includes(gen) }" @click="toggleTag('generation', gen)">{{ gen }}</span>
      </div>
      <!-- タレントタグをユニットごとに分けて表示。ユニットで絞り込み中は選択中のみ表示 -->
      <div class="tag-list-group" v-for="gen in sortedUnique(flattenTagArray(tagOrder.generation), 'generation')" :key="'talent-group-'+gen">
        <span class="tag-list-label">{{ gen }}</span>
        <span v-for="talent in sortedUnique(getTalentsByGeneration(gen), 'talent', gen)" :key="'talent-'+gen+'-'+talent" class="tag-badge tag-list-badge talent-badge" :class="{ selected: selectedTag.talent.includes(talent) }" @click="toggleTag('talent', talent)">{{ talent }}</span>
      </div>
      <div class="tag-list-group">
        <span class="tag-list-label">カテゴリ</span>
        <span v-for="cat in sortedUnique(flattenTagArray(tagOrder.category), 'category')" :key="'cat-'+cat" class="tag-badge tag-list-badge category-badge" :class="{ selected: selectedTag.category.includes(cat) }" @click="toggleTag('category', cat)">{{ cat }}</span>
      </div>
    </div>
    <!-- 絞り込み中のタグ表示（タグ一覧バーの下） -->
    <div v-if="hasAnyTagSelected" class="tag-filter-bar">
      <span v-if="selectedTag.generation.length">
        <span class="tag-list-label">ユニット</span>
        <span v-for="gen in selectedTag.generation" :key="'filter-gen-'+gen" class="tag-badge tag-list-badge generation-badge selected" @click="toggleTag('generation', gen)">{{ gen }}</span>
      </span>
      <span v-if="selectedTag.talent.length" style="margin-left: 1em;">
        <span class="tag-list-label">タレント</span>
        <span v-for="talent in selectedTag.talent" :key="'filter-talent-'+talent" class="tag-badge tag-list-badge talent-badge selected" @click="toggleTag('talent', talent)">{{ talent }}</span>
      </span>
      <span v-if="selectedTag.category.length" style="margin-left: 1em;">
        <span class="tag-list-label">カテゴリ</span>
        <span v-for="cat in selectedTag.category" :key="'filter-cat-'+cat" class="tag-badge tag-list-badge category-badge selected" @click="toggleTag('category', cat)">{{ cat }}</span>
      </span>
      <span style="margin-left: 1em;">で絞り込み中</span>
      <button class="tag-clear-btn" @click="clearTagFilter()">絞り込み解除</button>
    </div>
    <table class="product-table-amazon">
      <thead>
        <tr>
          <th v-if="showImage">画像</th>
          <th>商品名/価格/タグ</th>
          <th>数量</th>
          <th>合計</th>
          <th>リスト追加</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="product in flatFilteredProducts" :key="product.id">
          <td v-if="showImage">
            <img :src="product.image" :alt="product.name" class="product-image-amazon-table" />
          </td>
          <td class="product-name-cell">
            <div class="product-row-mobile">
              <div class="product-name">
                <template v-if="product.url">
                  <a :href="product.url" target="_blank" rel="noopener noreferrer" class="plain-link">{{ product.name }}</a>
                </template>
                <template v-else>
                  {{ product.name }}
                </template>
              </div>
              <div class="product-price">￥{{ product.price.toLocaleString() }}</div>
            </div>
            <div class="product-tags">
              <span v-for="gen in product.generation || []" :key="'pgen-'+product.id+gen" class="tag-badge generation-badge" @click="filterByTag('generation', gen)">{{ gen }}</span>
              <span v-for="talent in product.talent || []" :key="'ptalent-'+product.id+talent" class="tag-badge talent-badge" @click="filterByTag('talent', talent)">{{ talent }}</span>
              <span v-for="cat in product.category || []" :key="'pcat-'+product.id+cat" class="tag-badge category-badge" @click="filterByTag('category', cat)">{{ cat }}</span>
            </div>
          </td>
          <td>
            <div class="qty-row-amazon">
              <button @click="changeQty(product.id, -1)">-1</button>
              <input
                type="number"
                v-model.number="quantities[product.id]"
                min="1"
                class="qty-input"
              />
              <button @click="changeQty(product.id, 1)">+1</button>
            </div>
          </td>
          <td class="product-total-price">
            ￥{{ (product.price * (quantities[product.id] || 1)).toLocaleString() }}
          </td>
          <td>
            <button @click="add(product)" class="add-cart-btn">追加</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, watch, computed } from "vue";
const props = defineProps({
  products: Array,
  tagOrder: Object,
});
const emit = defineEmits(["add-to-cart"]);
const quantities = ref({});
const selectedTag = ref({ generation: [], talent: [], category: [] });
const showImage = ref(false);
watch(
  () => props.products,
  (val) => {
    val.forEach((p) => {
      if (!quantities.value[p.id]) quantities.value[p.id] = 1;
    });
  },
  { immediate: true }
);
const hasAnyTagSelected = computed(() =>
  selectedTag.value.generation.length > 0 ||
  selectedTag.value.talent.length > 0 ||
  selectedTag.value.category.length > 0
);
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
const flatFilteredProducts = computed(() => {
  let list = props.products.filter((p) => !p.tagFlag);
  if (selectedTag.value.talent.length) {
    list = list.filter((p) => (p.talent || []).some((t) => selectedTag.value.talent.includes(t)));
  }
  if (selectedTag.value.category.length) {
    list = list.filter((p) => (p.category || []).some((c) => selectedTag.value.category.includes(c)));
  }
  return sortProductsByTagOrder(list, props.tagOrder);
});
function getTalentsByGeneration(gen) {
  const talents = [];
  props.products.forEach((p) => {
    if ((p.generation || []).includes(gen)) {
      talents.push(...(p.talent || []));
    }
  });
  return [...new Set(talents)].sort();
}
function changeQty(id, diff) {
  if (!quantities.value[id]) quantities.value[id] = 1;
  quantities.value[id] = Math.max(1, quantities.value[id] + diff);
}
function add(product) {
  emit("add-to-cart", product, quantities.value[product.id]);
  quantities.value[product.id] = 1;
}
function filterByTag(type, value) {
  toggleTag(type, value);
}
function clearTagFilter(type) {
  if (type) {
    selectedTag.value[type] = [];
  } else {
    selectedTag.value = { generation: [], talent: [], category: [] };
  }
}
function toggleTag(type, value) {
  const idx = selectedTag.value[type].indexOf(value);
  if (idx !== -1) {
    selectedTag.value[type].splice(idx, 1);
    if (type === 'generation') {
      const relatedTalents = [];
      props.products.forEach((p) => {
        if (p.tagFlag && (p.generation || []).includes(value)) {
          relatedTalents.push(...(p.talent || []));
        }
      });
      selectedTag.value.talent = selectedTag.value.talent.filter(t => !relatedTalents.includes(t));
    }
  } else {
    selectedTag.value[type].push(value);
    if (type === 'generation') {
      const relatedTalents = [];
      props.products.forEach((p) => {
        if (p.tagFlag && (p.generation || []).includes(value)) {
          relatedTalents.push(...(p.talent || []));
        }
      });
      relatedTalents.forEach(t => {
        if (t && !selectedTag.value.talent.includes(t)) selectedTag.value.talent.push(t);
      });
    }
  }
}
function flattenTagArray(arr) {
  return (Array.isArray(arr) ? arr.flat(Infinity) : [arr]).filter(v => v != null && v !== "");
}
function sortedUnique(arr, type, gen) {
  if (type && props.tagOrder && props.products) {
    let tagFlagTrue = props.products.filter(p => p.tagFlag);
    if (type === 'talent' && gen) {
      tagFlagTrue = tagFlagTrue.filter(p => (p.generation || []).includes(gen));
    }
    tagFlagTrue = tagFlagTrue.sort((a, b) => {
      if (!isNaN(Number(a.id)) && !isNaN(Number(b.id))) {
        return Number(a.id) - Number(b.id);
      }
      return String(a.id).localeCompare(String(b.id), 'ja');
    });
    const tagArr = [];
    tagFlagTrue.forEach(p => {
      (Array.isArray(p[type]) ? p[type] : (p[type] ? [p[type]] : [])).forEach(t => {
        if (t && !tagArr.includes(t)) tagArr.push(t);
      });
    });
    return tagArr;
  }
  return [...new Set(arr)].sort((a, b) => (a > b ? 1 : a < b ? -1 : 0));
}
watch(
  () => selectedTag.value.talent.slice(),
  (newTalents) => {
    selectedTag.value.generation = selectedTag.value.generation.filter(gen => {
      const relatedTalents = [];
      props.products.forEach((p) => {
        if (p.tagFlag && (p.generation || []).includes(gen)) {
          relatedTalents.push(...(p.talent || []));
        }
      });
      return relatedTalents.every(t => newTalents.includes(t));
    });
  },
  { deep: true }
);
</script>

<style scoped>
/* 商品名リンクの色や装飾を通常テキストと同じに */
.plain-link {
  color: inherit;
  text-decoration: none;
  cursor: pointer;
}
.plain-link:visited {
  color: inherit;
}
.plain-link:hover {
  color: inherit;
  text-decoration: underline dotted #aaa;
}
body {
  background: #fff !important;
}
.product-list-amazon {
  width: 100%;
  box-sizing: border-box;
  background: #fff;
}
.product-table-amazon {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1em;
  background: #fff;
}
.product-table-amazon th,
.product-table-amazon td {
  border: 1px solid #ccc;
  padding: 0.5em 0.7em;
  text-align: left;
  vertical-align: middle;
}
.product-table-amazon th {
  background: #f5f5f5;
  color: #1976d2;
  font-weight: bold;
}
.product-image-amazon-table {
  width: 80px;
  height: 80px;
  object-fit: contain;
  border-radius: 4px;
  background: #f8f8f8;
}
.product-name-cell {
  min-width: 180px;
  max-width: 320px;
}
.product-name {
  font-weight: bold;
  color: #222;
  word-break: break-all;
  margin-bottom: 0.3em;
}
.product-tags {
  margin-bottom: 0.1em;
  display: flex;
  flex-wrap: wrap;
  gap: 0.2em;
}
.product-tags .tag-badge {
  font-size: 0.7em;
  padding: 0.05em 0.5em;
  margin-right: 0.05em;
  margin-bottom: 0.05em;
}
.product-price {
  color: #1976d2;
  margin-bottom: 0.5em;
  text-align: left;
}
.tag-badge,
.tag-list-badge {
  font-size: 0.8em;
  padding: 0.1em 0.7em;
  border-radius: 999px;
  background: #e3f2fd;
  color: #1976d2;
  border: 1.5px solid #90caf9;
  font-weight: bold;
  box-shadow: 0 1px 4px rgba(25, 118, 210, 0.08);
  display: inline-block;
  margin-bottom: 0.1em;
  margin-right: 0.2em;
  transition: background 0.2s, color 0.2s, border 0.2s;
}
.tag-badge.selected {
  background: #1976d2;
  color: #fff;
  border: 2px solid #1976d2;
  box-shadow: 0 0 0 2px #dbeafe;
}
.tag-badge.selected.generation-badge {
  background: #1976d2;
  color: #fff;
  border: 2px solid #1976d2;
  box-shadow: 0 0 0 2px #dbeafe;
}
.tag-badge.selected.talent-badge {
  background: #c2185b;
  color: #fff;
  border: 2px solid #c2185b;
  box-shadow: 0 0 0 2px #fce4ec;
}
.tag-badge.selected.category-badge {
  background: #388e3c;
  color: #fff;
  border: 2px solid #388e3c;
  box-shadow: 0 0 0 2px #e8f5e9;
}
.tag-badge:hover,
.tag-list-badge:hover {
  filter: brightness(0.95);
  text-decoration: underline dotted #aaa;
}
.generation-badge:hover,
.tag-list-badge.generation-badge:hover {
  background: #1976d2;
  color: #fff;
  border-color: #1976d2;
}
.talent-badge:hover,
.tag-list-badge.talent-badge:hover {
  background: #c2185b;
  color: #fff;
  border-color: #c2185b;
}
.category-badge:hover,
.tag-list-badge.category-badge:hover {
  background: #388e3c;
  color: #fff;
  border-color: #388e3c;
}
.tag-filter-bar {
  margin-bottom: 1em;
  font-weight: bold;
  color: #1976d2;
}
.tag-filter-bar .tag-badge,
.tag-filter-bar .tag-list-badge {
  font-size: 0.65em;
  padding: 0.05em 0.4em;
}
.tag-filter-bar button,
.tag-clear-btn {
  margin-left: 0.5em;
  background: #1976d2;
  color: #fff;
  border: 1.5px solid #1976d2;
  border-radius: 4px;
  cursor: pointer;
  padding: 0.1em 0.9em;
  font-size: 0.95em;
  font-weight: bold;
  transition: background 0.2s, color 0.2s, border 0.2s;
}
.tag-filter-bar button:hover,
.tag-clear-btn:hover {
  background: #fff;
  color: #1976d2;
  border: 2px solid #1976d2;
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
.qty-row-amazon button {
  font-size: 1.20em;
  padding: 0.01em 0.2em;
  min-width: 2.0em;
  height: 2em;
  border-radius: 5px;
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
  .qty-row-amazon {
    justify-content: center !important;
  }
}
.add-cart-btn {
  background: #1976d2;
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 0.3em 0.7em;
  margin-left: 0.5em;
  cursor: pointer;
  transition: background 0.2s;
}
.add-cart-btn:hover {
  background: #125199;
}
.tag-list-bar {
  margin-bottom: 1em;
  display: flex;
  flex-direction: column;
  gap: 0.7em 0;
  align-items: flex-start;
}
.tag-list-group {
  display: flex;
  align-items: center;
  gap: 0.5em;
  flex-wrap: wrap;
}
.tag-list-label {
  font-weight: bold;
  color: #1976d2;
  margin-right: 0.5em;
  min-width: 3em;
}
.product-total-price {
  color: #d32f2f;
  font-weight: bold;
  min-width: 60px;
  max-width: 80px;
  width: 6em;
  text-align: right;
}
.tag-clear-btn {
  margin-left: 0.5em;
  background: #1976d2;
  color: #fff;
  border: 1.5px solid #1976d2;
  border-radius: 4px;
  cursor: pointer;
  padding: 0.1em 0.9em;
  font-size: 0.95em;
  font-weight: bold;
  transition: background 0.2s, color 0.2s, border 0.2s;
}
.tag-clear-btn:hover {
  background: #fff;
  color: #1976d2;
  border: 2px solid #1976d2;
}
.product-table-amazon td:nth-child(3),
.product-table-amazon th:nth-child(3) {
  text-align: center;
  vertical-align: middle;
}
.product-table-amazon td.product-total-price,
.product-table-amazon th:nth-child(4) {
  text-align: center;
}
@media (max-width: 900px) {
  .product-row {
    max-width: 98vw;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5em;
  }
  .product-image-amazon {
    width: 100%;
    height: 30vw;
    max-height: 180px;
    margin-bottom: 0.5em;
  }
}
@media (max-width: 600px) {
  .product-table-amazon,
  .product-table-amazon thead,
  .product-table-amazon tbody,
  .product-table-amazon th,
  .product-table-amazon td,
  .product-table-amazon tr {
    display: block;
    width: 100%;
    box-sizing: border-box;
  }
  .product-table-amazon thead {
    display: none;
  }
  .product-table-amazon tr {
    margin-bottom: 1.2em;
    border: 1px solid #ccc;
    border-radius: 8px;
    box-shadow: 0 1px 4px rgba(25, 118, 210, 0.06);
    background: #fff;
    padding: 0.7em 0.2em;
  }
  .product-table-amazon td {
    border: none;
    border-bottom: 1px solid #eee;
    position: relative;
    padding-left: 0;
    min-height: 2.2em;
    text-align: left;
    background: none;
    width: 100%;
    max-width: 100vw;
    word-break: break-word;
  }
  .product-table-amazon td:last-child {
    border-bottom: none;
  }
  .product-image-amazon-table {
    display: block;
    margin: 0 auto 0.7em auto;
    width: 60vw;
    max-width: 180px;
    height: auto;
  }
  .product-name-cell {
    max-width: 100vw;
    min-width: 0;
    margin-bottom: 0.5em;
  }
  .product-tags {
    margin-bottom: 0.3em;
  }
  .qty-row-amazon {
    margin-top: 0.7em;
    margin-bottom: 0.7em;
    justify-content: flex-start;
  }
  .product-total-price {
    margin-bottom: 0.7em;
    width: 100%;
    min-width: 0;
    max-width: 100vw;
    text-align: left;
  }
  .add-cart-btn {
    width: 100%;
    margin: 0.5em 0 0 0;
    padding: 0.5em 0;
    font-size: 1em;
  }
  .product-row-mobile {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: 0.7em;
    width: 100%;
    margin-bottom: 0.3em;
  }
  .product-row-mobile .product-name {
    flex: 1 1 60%;
    font-size: 1em;
    margin-bottom: 0;
    min-width: 0;
    word-break: break-all;
  }
  .product-row-mobile .product-price {
    flex: 0 0 auto;
    font-size: 1em;
    color: #1976d2;
    margin-bottom: 0;
    text-align: right;
    min-width: 5em;
  }
}
.generation-badge { background: #e3f2fd; color: #1976d2; border-color: #90caf9; }
.talent-badge { background: #fce4ec; color: #c2185b; border-color: #f8bbd0; }
.category-badge { background: #e8f5e9; color: #388e3c; border-color: #a5d6a7; }
</style>
