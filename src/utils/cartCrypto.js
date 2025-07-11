import LZString from 'lz-string';
import pako from './pako';
import brotli from './brotli';


// 0x21〜0x7E（94進数, スペース除外）で数値をエンコード
function toBase94(num) {
    let res = '';
    do {
        res = String.fromCharCode(0x21 + (num % 94)) + res;
        num = Math.floor(num / 94);
    } while (num > 0);
    return res;
}
// 0x21〜0x7E（94進数, スペース除外）から数値をデコード
function fromBase94(str) {
    let num = 0;
    for (let i = 0; i < str.length; i++) {
        num = num * 94 + (str.charCodeAt(i) - 0x21);
    }
    return num;
}

// --- ここからバイナリ直列化＋base64方式を標準に ---

// カートをバイナリ直列化＋base64（URLセーフ）でエンコード
export function encodeCartForUrl(cart) {
    // 各商品ID・数量を1バイトずつ詰める
    const arr = new Uint8Array(cart.length * 2);
    for (let i = 0; i < cart.length; i++) {
        const id = Number(cart[i].product.id);
        const quantity = Number(cart[i].quantity);
        if (id < 0 || id > 255 || quantity < 0 || quantity > 255) {
            throw new Error('ID/数量は0〜255のみ対応');
        }
        arr[i * 2] = id;
        arr[i * 2 + 1] = quantity;
    }
    // バイナリをbase64化＋URLセーフ
    const bin = String.fromCharCode(...arr);
    return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

// base64（URLセーフ）→バイナリ直列化でカート復元
export function decodeCartFromUrl(data, products) {
    try {
        // base64デコード
        const bin = atob(data.replace(/-/g, '+').replace(/_/g, '/'));
        const arr = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; ++i) arr[i] = bin.charCodeAt(i);
        const result = [];
        for (let i = 0; i + 1 < arr.length; i += 2) {
            const id = arr[i];
            const quantity = arr[i + 1];
            const product = products.find(p => Number(p.id) === id);
            if (product) result.push({ product, quantity });
        }
        return result;
    } catch (e) {
        return [];
    }
}

// 超圧縮バージョン: 商品ID・個数をbase94で可変長エンコードし、スペース区切り、圧縮＋BASE64でURLセーフ化
export function encodeCartForUrlUltraCompact(cart) {
    // ID・数量をbase94で可変長エンコードし、スペース区切りで連結
    const parts = [];
    for (const item of cart) {
        parts.push(toBase94(Number(item.product.id)));
        parts.push(toBase94(Number(item.quantity)));
    }
    const compactStr = parts.join(' '); // スペース区切り
    // 圧縮
    const compressed = LZString.compressToUint8Array(compactStr);
    // BASE64エンコード＋URLセーフ化
    const base64 = btoa(String.fromCharCode(...compressed)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
    return base64;
}

export function decodeCartFromUrlUltraCompact(data, products) {
    try {
        // URLセーフBase64をデコード
        const bin = atob(data.replace(/-/g, '+').replace(/_/g, '/'));
        const arr = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; ++i) arr[i] = bin.charCodeAt(i);
        // LZStringで解凍
        const compactStr = LZString.decompressFromUint8Array(arr);
        if (!compactStr) return [];
        const parts = compactStr.split(' ');
        const result = [];
        for (let i = 0; i + 1 < parts.length; i += 2) {
            const id = fromBase94(parts[i]);
            const quantity = fromBase94(parts[i + 1]);
            const product = products.find(p => Number(p.id) === id);
            if (product) result.push({ product, quantity });
        }
        return result;
    } catch (e) {
        return [];
    }
}

// バイナリ直列化＋base64（ID/数量は0〜255のみ対応）
export function encodeCartForUrlBinary(cart) {
    // 各商品ID・数量を1バイトずつ詰める
    const arr = new Uint8Array(cart.length * 2);
    for (let i = 0; i < cart.length; i++) {
        const id = Number(cart[i].product.id);
        const quantity = Number(cart[i].quantity);
        if (id < 0 || id > 255 || quantity < 0 || quantity > 255) {
            throw new Error('ID/数量は0〜255のみ対応');
        }
        arr[i * 2] = id;
        arr[i * 2 + 1] = quantity;
    }
    // バイナリをbase64化＋URLセーフ
    const bin = String.fromCharCode(...arr);
    return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

export function decodeCartFromUrlBinary(data, products) {
    try {
        // base64デコード
        const bin = atob(data.replace(/-/g, '+').replace(/_/g, '/'));
        const arr = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; ++i) arr[i] = bin.charCodeAt(i);
        const result = [];
        for (let i = 0; i + 1 < arr.length; i += 2) {
            const id = arr[i];
            const quantity = arr[i + 1];
            const product = products.find(p => Number(p.id) === id);
            if (product) result.push({ product, quantity });
        }
        return result;
    } catch (e) {
        return [];
    }
}

// アイテムID:9ビット、数量:8ビットでバイナリ直列化＋base64
export function encodeCartForUrl9bitId8bitQty(cart) {
    const bits = [];
    for (const item of cart) {
        const id = Number(item.product.id);
        const qty = Number(item.quantity);
        if (id < 0 || id > 511 || qty < 0 || qty > 255) {
            throw new Error('IDは0〜511、数量は0〜255のみ対応');
        }
        // 9ビットID
        for (let i = 8; i >= 0; i--) bits.push((id >> i) & 1);
        // 8ビット数量
        for (let i = 7; i >= 0; i--) bits.push((qty >> i) & 1);
    }
    // 8ビットごとにバイト配列化
    const byteLen = Math.ceil(bits.length / 8);
    const arr = new Uint8Array(byteLen);
    for (let i = 0; i < bits.length; i++) {
        arr[Math.floor(i / 8)] |= bits[i] << (7 - (i % 8));
    }
    // zlib圧縮
    const compressed = pako.deflate(arr);
    const bin = String.fromCharCode(...compressed);
    return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

export function decodeCartFromUrl9bitId8bitQty(data, products) {
    try {
        const bin = atob(data.replace(/-/g, '+').replace(/_/g, '/'));
        const arr = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; ++i) arr[i] = bin.charCodeAt(i);
        // zlib解凍
        const decompressed = pako.inflate(arr);
        // ビット列に展開
        const bits = [];
        for (let i = 0; i < decompressed.length; i++) {
            for (let j = 7; j >= 0; j--) {
                bits.push((decompressed[i] >> j) & 1);
            }
        }
        const result = [];
        let idx = 0;
        while (idx + 17 <= bits.length) {
            let id = 0, qty = 0;
            for (let i = 0; i < 9; i++) id = (id << 1) | bits[idx++];
            for (let i = 0; i < 8; i++) qty = (qty << 1) | bits[idx++];
            const product = products.find(p => Number(p.id) === id);
            if (product) result.push({ product, quantity: qty });
        }
        return result;
    } catch (e) {
        return [];
    }
}

// ハフマン符号化ユーティリティ
function buildHuffmanTree(freqMap) {
    const nodes = Object.entries(freqMap).map(([value, freq]) => ({ value, freq, left: null, right: null }));
    while (nodes.length > 1) {
        nodes.sort((a, b) => a.freq - b.freq);
        const left = nodes.shift();
        const right = nodes.shift();
        nodes.push({ value: null, freq: left.freq + right.freq, left, right });
    }
    return nodes[0];
}
function buildHuffmanCodeMap(tree, prefix = '', map = {}) {
    if (tree.value !== null) {
        map[tree.value] = prefix || '0';
    } else {
        buildHuffmanCodeMap(tree.left, prefix + '0', map);
        buildHuffmanCodeMap(tree.right, prefix + '1', map);
    }
    return map;
}
function serializeHuffmanTree(tree) {
    // プレオーダー: 0=内部, 1=葉+値
    if (tree.value !== null) {
        return '1' + String.fromCharCode(Number(tree.value));
    } else {
        return '0' + serializeHuffmanTree(tree.left) + serializeHuffmanTree(tree.right);
    }
}
function deserializeHuffmanTree(str, idx = { v: 0 }) {
    if (str[idx.v] === '1') {
        idx.v++;
        const value = str.charCodeAt(idx.v++);
        return { value, left: null, right: null };
    } else {
        idx.v++;
        const left = deserializeHuffmanTree(str, idx);
        const right = deserializeHuffmanTree(str, idx);
        return { value: null, left, right };
    }
}
function huffmanEncode(data) {
    // data: 数値配列
    const freq = {};
    for (const v of data) freq[v] = (freq[v] || 0) + 1;
    const tree = buildHuffmanTree(freq);
    const codeMap = buildHuffmanCodeMap(tree);
    let bits = '';
    for (const v of data) bits += codeMap[v];
    // 8ビットごとにバイト化
    const byteLen = Math.ceil(bits.length / 8);
    const arr = new Uint8Array(byteLen);
    for (let i = 0; i < bits.length; i++) {
        if (bits[i] === '1') arr[Math.floor(i / 8)] |= 1 << (7 - (i % 8));
    }
    return { tree, arr, bitLen: bits.length };
}
function huffmanDecode(tree, arr, bitLen) {
    const result = [];
    let node = tree;
    let total = 0;
    for (let i = 0; i < arr.length && total < bitLen; i++) {
        for (let j = 7; j >= 0 && total < bitLen; j--) {
            node = (arr[i] & (1 << j)) ? node.right : node.left;
            if (node.value !== null) {
                result.push(node.value);
                node = tree;
            }
            total++;
        }
    }
    return result;
}

// カートをハフマン符号化＋base64（URLセーフ）でエンコード
export function encodeCartForUrlHuffman(cart) {
    // [ID,数量,ID,数量,...]の配列化
    const flat = [];
    for (const item of cart) {
        flat.push(Number(item.product.id));
        flat.push(Number(item.quantity));
    }
    const { tree, arr, bitLen } = huffmanEncode(flat);
    const treeStr = serializeHuffmanTree(tree);
    // tree長(2byte) + tree + bitLen(2byte) + データ
    const meta = new Uint8Array(4);
    meta[0] = (treeStr.length >> 8) & 0xff;
    meta[1] = treeStr.length & 0xff;
    meta[2] = (bitLen >> 8) & 0xff;
    meta[3] = bitLen & 0xff;
    const treeBytes = new Uint8Array(treeStr.length);
    for (let i = 0; i < treeStr.length; i++) treeBytes[i] = treeStr.charCodeAt(i);
    const all = new Uint8Array(meta.length + treeBytes.length + arr.length);
    all.set(meta, 0);
    all.set(treeBytes, meta.length);
    all.set(arr, meta.length + treeBytes.length);
    const bin = String.fromCharCode(...all);
    return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

export function decodeCartFromUrlHuffman(data, products) {
    try {
        const bin = atob(data.replace(/-/g, '+').replace(/_/g, '/'));
        const all = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; ++i) all[i] = bin.charCodeAt(i);
        const treeLen = (all[0] << 8) | all[1];
        const bitLen = (all[2] << 8) | all[3];
        const treeStr = String.fromCharCode(...all.slice(4, 4 + treeLen));
        const arr = all.slice(4 + treeLen);
        const tree = deserializeHuffmanTree(treeStr);
        const flat = huffmanDecode(tree, arr, bitLen);
        const result = [];
        for (let i = 0; i + 1 < flat.length; i += 2) {
            const id = flat[i], qty = flat[i + 1];
            const product = products.find(p => Number(p.id) === id);
            if (product) result.push({ product, quantity: qty });
        }
        return result;
    } catch (e) {
        return [];
    }
}

// カートをBrotli圧縮＋base64（URLセーフ）でエンコード

// Brotli圧縮＋base64（URLセーフ）方式
export function encodeCartForUrlBrotli(cart) {
    const flat = [];
    for (const item of cart) {
        flat.push(Number(item.product.id));
        flat.push(Number(item.quantity));
    }
    const arr = new Uint8Array(flat.length);
    for (let i = 0; i < flat.length; i++) arr[i] = flat[i];
    const compressed = brotli.compress(arr);
    const bin = String.fromCharCode(...compressed);
    return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

export function decodeCartFromUrlBrotli(data, products) {
    try {
        const bin = atob(data.replace(/-/g, '+').replace(/_/g, '/'));
        const arr = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; ++i) arr[i] = bin.charCodeAt(i);
        const decompressed = brotli.decompress(arr);
        const result = [];
        for (let i = 0; i + 1 < decompressed.length; i += 2) {
            const id = decompressed[i], qty = decompressed[i + 1];
            const product = products.find(p => Number(p.id) === id);
            if (product) result.push({ product, quantity: qty });
        }
        return result;
    } catch (e) {
        return [];
    }
}

