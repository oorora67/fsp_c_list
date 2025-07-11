// fflateのBrotli圧縮/展開ラッパー
import { compressSync, decompressSync } from 'fflate';
export default {
    compress: (input) => compressSync(input, { mode: 1 }),
    decompress: (input) => decompressSync(input)
};
