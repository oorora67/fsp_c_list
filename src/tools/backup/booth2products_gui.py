import io
from PIL import Image, ImageTk
import requests
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import re
import requests


def booth_to_products(booth_json):
    main = booth_json
    category = main.get("category", {}).get("name", "")
    image = main.get("images", [{}])
    description = main.get("description", "")
    tags = [t["name"] for t in main.get("tags", [])]
    variations = main.get("variations") or []
    if not variations:
        variations = [
            {"id": main.get("id"), "name": main.get("name"), "price": main.get("price")}
        ]
    products = []
    for v in variations:
        price = v.get("price")
        if isinstance(price, str):
            price = int("".join(filter(str.isdigit, price)))
        products.append(
            {
                "id": v.get("id"),
                "name": main.get("name")
                + (
                    f" ({v.get('name')})"
                    if v.get("name") and v.get("name") != main.get("name")
                    else ""
                ),
                "price": price,
                "category": [category] if category else [],
                "image": image,
                "description": description,
                "tags": tags,
            }
        )
    return products


class BoothGUI:
    def move_item_up(self, kind):
        if kind == "talent":
            tree, items = self.tree_talent, self.items_talent
        elif kind == "unit":
            tree, items = self.tree_unit, self.items_unit
        elif kind == "category":
            tree, items = self.tree_category, self.items_category
        else:
            tree, items = self.tree_goods, self.items_goods
        selected = tree.selection()
        if not selected:
            return
        idx = tree.index(selected[0])
        if idx <= 0 or idx >= len(items):
            return
        # itemsリスト内で入れ替え
        items[idx - 1], items[idx] = items[idx], items[idx - 1]
        # loaded_json側もID一致で順序を入れ替える
        id1 = str(items[idx]["id"])
        id2 = str(items[idx - 1]["id"])
        idx1 = next(
            (i for i, p in enumerate(self.loaded_json) if str(p.get("id")) == id1), None
        )
        idx2 = next(
            (i for i, p in enumerate(self.loaded_json) if str(p.get("id")) == id2), None
        )
        if idx1 is not None and idx2 is not None:
            self.loaded_json[idx1], self.loaded_json[idx2] = (
                self.loaded_json[idx2],
                self.loaded_json[idx1],
            )
        self.refresh_listbox_all()
        # 再描画後、移動先の行を再選択
        children = tree.get_children()
        if 0 <= idx - 1 < len(children):
            tree.selection_set(children[idx - 1])
            tree.focus(children[idx - 1])

    def move_item_down(self, kind):
        if kind == "talent":
            tree, items = self.tree_talent, self.items_talent
        elif kind == "unit":
            tree, items = self.tree_unit, self.items_unit
        elif kind == "category":
            tree, items = self.tree_category, self.items_category
        else:
            tree, items = self.tree_goods, self.items_goods
        selected = tree.selection()
        if not selected:
            return
        idx = tree.index(selected[0])
        if idx < 0 or idx >= len(items) - 1:
            return
        # itemsリスト内で入れ替え
        items[idx], items[idx + 1] = items[idx + 1], items[idx]
        # loaded_json側もID一致で順序を入れ替える
        id1 = str(items[idx]["id"])
        id2 = str(items[idx + 1]["id"])
        idx1 = next(
            (i for i, p in enumerate(self.loaded_json) if str(p.get("id")) == id1), None
        )
        idx2 = next(
            (i for i, p in enumerate(self.loaded_json) if str(p.get("id")) == id2), None
        )
        if idx1 is not None and idx2 is not None:
            self.loaded_json[idx1], self.loaded_json[idx2] = (
                self.loaded_json[idx2],
                self.loaded_json[idx1],
            )
        self.refresh_listbox_all()
        # 再描画後、移動先の行を再選択
        children = tree.get_children()
        if 0 <= idx + 1 < len(children):
            tree.selection_set(children[idx + 1])
            tree.focus(children[idx + 1])

    def add_selected_category(self):
        selected = [
            self.items_category[i]["name"]
            for i in self.listbox_category_select.curselection()
        ]
        self.edit_category_goods.config(state="normal")
        self.edit_category_goods.delete(0, tk.END)
        self.edit_category_goods.insert(0, ",".join(selected))
        self.edit_category_goods.config(state="readonly")

    def add_new_talent(self):
        name = self.edit_name_talent.get().strip()
        generation = [
            s.strip() for s in self.edit_generation_talent.get().split(",") if s.strip()
        ]
        talent = [
            s.strip() for s in self.edit_talent_talent.get().split(",") if s.strip()
        ]
        tagflag = self.edit_tagflag_talent.get() == "true"
        # ID自動付与（T+3桁連番）
        existing_ids = [
            int(str(p.get("id"))[1:])
            for p in self.items_talent
            if str(p.get("id", "")).startswith("T") and str(p.get("id"))[1:].isdigit()
        ]
        next_num = max(existing_ids + [0]) + 1
        new_id = f"T{next_num:03d}"
        # 重複チェック
        if any(p.get("name") == name for p in self.items_talent):
            messagebox.showwarning(
                "追加エラー", "同じ名前のタレントタグが既に存在します"
            )
            return
        new_item = {
            "id": new_id,
            "name": name,
            "generation": generation,
            "talent": talent,
            "tagFlag": tagflag,
        }
        self.items_talent.append(new_item)
        self.loaded_json.append(new_item)
        self.refresh_listbox_all()
        messagebox.showinfo("追加", "新規タレントタグを追加しました")

    def add_new_unit(self):
        name = self.edit_name_unit.get().strip()
        generation = [
            s.strip() for s in self.edit_generation_unit.get().split(",") if s.strip()
        ]
        talent = [
            s.strip() for s in self.edit_talent_unit.get().split(",") if s.strip()
        ]
        tagflag = self.edit_tagflag_unit.get() == "true"
        existing_ids = [
            int(str(p.get("id"))[1:])
            for p in self.items_unit
            if str(p.get("id", "")).startswith("U") and str(p.get("id"))[1:].isdigit()
        ]
        next_num = max(existing_ids + [0]) + 1
        new_id = f"U{next_num:03d}"
        if any(p.get("name") == name for p in self.items_unit):
            messagebox.showwarning(
                "追加エラー", "同じ名前のユニットタグが既に存在します"
            )
            return
        new_item = {
            "id": new_id,
            "name": name,
            "generation": generation,
            "talent": talent,
            "tagFlag": tagflag,
        }
        self.items_unit.append(new_item)
        self.loaded_json.append(new_item)
        self.refresh_listbox_all()
        messagebox.showinfo("追加", "新規ユニットタグを追加しました")

    def add_new_category(self):
        name = self.edit_name_category.get().strip()
        category = [
            s.strip() for s in self.edit_category_category.get().split(",") if s.strip()
        ]
        tagflag = self.edit_tagflag_category.get() == "true"
        existing_ids = [
            int(str(p.get("id"))[1:])
            for p in self.items_category
            if str(p.get("id", "")).startswith("C") and str(p.get("id"))[1:].isdigit()
        ]
        next_num = max(existing_ids + [0]) + 1
        new_id = f"C{next_num:03d}"
        if any(p.get("name") == name for p in self.items_category):
            messagebox.showwarning(
                "追加エラー", "同じ名前のカテゴリタグが既に存在します"
            )
            return
        new_item = {
            "id": new_id,
            "name": name,
            "category": category,
            "tagFlag": tagflag,
        }
        self.items_category.append(new_item)
        self.loaded_json.append(new_item)
        self.refresh_listbox_all()
        messagebox.showinfo("追加", "新規カテゴリタグを追加しました")

    def new_json(self):
        if messagebox.askyesno("新規作成", "現在のデータを破棄して新規作成しますか？"):
            self.loaded_json_path = None
            self.loaded_json = []
            self.items_talent = []
            self.items_unit = []
            self.items_category = []
            self.items_goods = []
            self.refresh_listbox_all()
            messagebox.showinfo("新規作成", "新しいJSONデータを作成しました")

    def load_json(self):
        path = filedialog.askopenfilename(
            filetypes=[("JSONファイル", "*.json"), ("すべてのファイル", "*.*")],
            title="JSONファイルを開く",
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.loaded_json_path = path
            self.loaded_json = data if isinstance(data, list) else [data]
            self.refresh_listbox_all()
            messagebox.showinfo("読み込み", f"{path} を読み込みました")
        except Exception as e:
            messagebox.showerror(
                "読み込みエラー", f"ファイルの読み込みに失敗しました\n{e}"
            )

    def save_json(self):
        if not self.loaded_json_path:
            path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSONファイル", "*.json"), ("すべてのファイル", "*.*")],
                title="JSONファイルに保存",
            )
            if not path:
                return
            self.loaded_json_path = path
        else:
            path = self.loaded_json_path
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.loaded_json, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("保存", f"{path} に保存しました")
        except Exception as e:
            messagebox.showerror("保存エラー", f"ファイルの保存に失敗しました\n{e}")

    def __init__(self, master):
        self.master = master
        master.title("Booth商品JSON追加ツール")
        self.products = []
        self.loaded_json_path = None
        self.loaded_json = []

        # --- メニューリボン ---
        self.menu = tk.Menu(master)
        master.config(menu=self.menu)
        self.filemenu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="ファイル", menu=self.filemenu)
        self.filemenu.add_command(label="新規作成", command=self.new_json)
        self.filemenu.add_command(label="読み込み", command=self.load_json)
        self.filemenu.add_command(label="保存", command=self.save_json)

        # ...既存の初期化処理...

        # --- タブ構成 ---
        self.notebook = ttk.Notebook(master)
        self.notebook.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        self.tab_talent = tk.Frame(self.notebook)
        self.tab_unit = tk.Frame(self.notebook)
        self.tab_category = tk.Frame(self.notebook)
        self.tab_goods = tk.Frame(self.notebook)
        self.notebook.add(self.tab_talent, text="タレントタグ(T)")
        self.notebook.add(self.tab_unit, text="ユニットタグ(U)")
        self.notebook.add(self.tab_category, text="カテゴリタグ(C)")
        self.notebook.add(self.tab_goods, text="グッズ")
        # --- タレントタブ: Treeview（表形式） ---
        self.tree_talent = ttk.Treeview(
            self.tab_talent,
            columns=("id", "name", "generation", "talent", "tagFlag"),
            show="headings",
            height=10,
        )
        self.tree_talent.heading("id", text="ID")
        self.tree_talent.heading("name", text="名前")
        self.tree_talent.heading("generation", text="期生")
        self.tree_talent.heading("talent", text="タレント")
        self.tree_talent.heading("tagFlag", text="タグフラグ")
        self.tree_talent.column("id", width=60)
        self.tree_talent.column("name", width=160)
        self.tree_talent.column("generation", width=120)
        self.tree_talent.column("talent", width=160)
        self.tree_talent.column("tagFlag", width=60)
        self.tree_talent.pack(fill="both", expand=True)

        # 並び替えボタン（タレント）
        self.btn_frame_talent = tk.Frame(self.tab_talent)
        self.btn_frame_talent.pack(fill="x", padx=12, pady=2)
        self.btn_up_talent = tk.Button(
            self.btn_frame_talent,
            text="↑上へ",
            width=8,
            command=lambda: self.move_item_up("talent"),
        )
        self.btn_up_talent.pack(side="left", padx=2)
        self.btn_down_talent = tk.Button(
            self.btn_frame_talent,
            text="↓下へ",
            width=8,
            command=lambda: self.move_item_down("talent"),
        )
        self.btn_down_talent.pack(side="left", padx=2)

        # --- ユニットタブ: Treeview ---
        self.tree_unit = ttk.Treeview(
            self.tab_unit,
            columns=("id", "name", "generation", "talent", "tagFlag"),
            show="headings",
            height=10,
        )
        self.tree_unit.heading("id", text="ID")
        self.tree_unit.heading("name", text="名前")
        self.tree_unit.heading("generation", text="期生")
        self.tree_unit.heading("talent", text="タレント")
        self.tree_unit.heading("tagFlag", text="タグフラグ")
        self.tree_unit.column("id", width=60)
        self.tree_unit.column("name", width=160)
        self.tree_unit.column("generation", width=120)
        self.tree_unit.column("talent", width=160)
        self.tree_unit.column("tagFlag", width=60)
        self.tree_unit.pack(fill="both", expand=True)

        # 並び替えボタン（ユニット）
        self.btn_frame_unit = tk.Frame(self.tab_unit)
        self.btn_frame_unit.pack(fill="x", padx=12, pady=2)
        self.btn_up_unit = tk.Button(
            self.btn_frame_unit,
            text="↑上へ",
            width=8,
            command=lambda: self.move_item_up("unit"),
        )
        self.btn_up_unit.pack(side="left", padx=2)
        self.btn_down_unit = tk.Button(
            self.btn_frame_unit,
            text="↓下へ",
            width=8,
            command=lambda: self.move_item_down("unit"),
        )
        self.btn_down_unit.pack(side="left", padx=2)

        # --- カテゴリタブ: Treeview ---
        self.tree_category = ttk.Treeview(
            self.tab_category,
            columns=("id", "name", "category", "tagFlag"),
            show="headings",
            height=10,
        )
        self.tree_category.heading("id", text="ID")
        self.tree_category.heading("name", text="名前")
        self.tree_category.heading("category", text="カテゴリ")
        self.tree_category.heading("tagFlag", text="タグフラグ")
        self.tree_category.column("id", width=60)
        self.tree_category.column("name", width=160)
        self.tree_category.column("category", width=160)
        self.tree_category.column("tagFlag", width=60)
        self.tree_category.pack(fill="both", expand=True)

        # 並び替えボタン（カテゴリ）
        self.btn_frame_category = tk.Frame(self.tab_category)
        self.btn_frame_category.pack(fill="x", padx=12, pady=2)
        self.btn_up_category = tk.Button(
            self.btn_frame_category,
            text="↑上へ",
            width=8,
            command=lambda: self.move_item_up("category"),
        )
        self.btn_up_category.pack(side="left", padx=2)
        self.btn_down_category = tk.Button(
            self.btn_frame_category,
            text="↓下へ",
            width=8,
            command=lambda: self.move_item_down("category"),
        )
        self.btn_down_category.pack(side="left", padx=2)

        # --- グッズタブ: Treeview ---
        self.tree_goods = ttk.Treeview(
            self.tab_goods,
            columns=(
                "id",
                "name",
                "price",
                "generation",
                "talent",
                "category",
                "tagFlag",
            ),
            show="headings",
            height=10,
        )
        self.tree_goods.heading("id", text="ID")
        self.tree_goods.heading("name", text="名前")
        self.tree_goods.heading("price", text="価格")
        self.tree_goods.heading("generation", text="期生")
        self.tree_goods.heading("talent", text="タレント")
        self.tree_goods.heading("category", text="カテゴリ")
        self.tree_goods.heading("tagFlag", text="タグフラグ")
        self.tree_goods.column("id", width=40)
        self.tree_goods.column("name", width=160)
        self.tree_goods.column("price", width=60)
        self.tree_goods.column("generation", width=120)
        self.tree_goods.column("talent", width=120)
        self.tree_goods.column("category", width=120)
        self.tree_goods.column("tagFlag", width=60)
        self.tree_goods.pack(fill="both", expand=True)

        # 並び替えボタン（グッズ）
        self.btn_frame_goods = tk.Frame(self.tab_goods)
        self.btn_frame_goods.pack(fill="x", padx=12, pady=2)
        self.btn_up_goods = tk.Button(
            self.btn_frame_goods,
            text="↑上へ",
            width=8,
            command=lambda: self.move_item_up("goods"),
        )
        self.btn_up_goods.pack(side="left", padx=2)
        self.btn_down_goods = tk.Button(
            self.btn_frame_goods,
            text="↓下へ",
            width=8,
            command=lambda: self.move_item_down("goods"),
        )
        self.btn_down_goods.pack(side="left", padx=2)

        # --- グッズタブ用: Booth商品URL・バリエーション追加UI（リストの上に移動） ---
        self.goods_top_frame = tk.Frame(self.tab_goods)
        self.goods_top_frame.pack(fill="x", padx=5, pady=5)
        self.url_label = tk.Label(self.goods_top_frame, text="Booth商品URL:")
        self.url_label.grid(row=0, column=0, sticky="e")
        self.url_entry = tk.Entry(self.goods_top_frame, width=60)
        self.url_entry.grid(row=0, column=1, padx=5, pady=5)
        self.fetch_btn = tk.Button(
            self.goods_top_frame, text="取得", command=self.fetch
        )
        self.fetch_btn.grid(row=0, column=2, padx=5)
        self.variation_label = tk.Label(
            self.goods_top_frame, text="バリエーション選択:"
        )
        self.variation_label.grid(row=1, column=0, sticky="e")
        self.variation_combo = ttk.Combobox(
            self.goods_top_frame, state="readonly", width=57
        )
        self.variation_combo.grid(row=1, column=1, padx=5, pady=5)
        self.add_btn = tk.Button(
            self.goods_top_frame, text="リストに追加", command=self.add_to_list
        )
        self.add_btn.grid(row=1, column=2, padx=5)

        # self.listbox_goods = tk.Listbox(self.tab_goods, width=90, height=10)
        # self.listbox_goods.pack(fill="both", expand=True)
        # --- 編集フォームを各タブごとに分離 ---
        # タレントタグ編集フォーム
        self.edit_frame_talent = tk.LabelFrame(
            self.tab_talent, text="タレントタグ編集", padx=10, pady=8
        )
        self.edit_frame_talent.pack(fill="x", padx=12, pady=8)
        tk.Label(self.edit_frame_talent, text="ID:").grid(
            row=0, column=0, sticky="e", padx=4, pady=2
        )
        self.edit_id_talent = tk.Entry(self.edit_frame_talent, width=12)
        self.edit_id_talent.grid(row=0, column=1, sticky="w", padx=4, pady=2)
        tk.Label(self.edit_frame_talent, text="名前:").grid(
            row=0, column=2, sticky="e", padx=4, pady=2
        )
        self.edit_name_talent = tk.Entry(self.edit_frame_talent, width=24)
        self.edit_name_talent.grid(row=0, column=3, sticky="w", padx=4, pady=2)
        tk.Label(self.edit_frame_talent, text="期生(カンマ区切り):").grid(
            row=1, column=0, sticky="e", padx=4, pady=2
        )
        self.edit_generation_talent = tk.Entry(self.edit_frame_talent, width=24)
        self.edit_generation_talent.grid(row=1, column=1, sticky="w", padx=4, pady=2)
        tk.Label(self.edit_frame_talent, text="タレント(カンマ区切り):").grid(
            row=1, column=2, sticky="e", padx=4, pady=2
        )
        self.edit_talent_talent = tk.Entry(self.edit_frame_talent, width=24)
        self.edit_talent_talent.grid(row=1, column=3, sticky="w", padx=4, pady=2)
        tk.Label(self.edit_frame_talent, text="タグフラグ:").grid(
            row=2, column=0, sticky="e", padx=4, pady=2
        )
        self.edit_tagflag_talent = ttk.Combobox(
            self.edit_frame_talent, values=["true", "false"], width=8, state="readonly"
        )
        self.edit_tagflag_talent.grid(row=2, column=1, sticky="w", padx=4, pady=2)
        self.update_btn_talent = tk.Button(
            self.edit_frame_talent,
            text="選択タレントタグを更新",
            width=18,
            command=lambda: self.update_selected("talent"),
        )
        self.update_btn_talent.grid(row=2, column=2, padx=8, pady=5)
        self.add_btn_talent = tk.Button(
            self.edit_frame_talent,
            text="新規タレントタグを追加",
            width=18,
            command=self.add_new_talent,
        )
        self.add_btn_talent.grid(row=2, column=3, padx=8, pady=5)

        # タレント削除ボタン
        self.delete_btn_talent = tk.Button(
            self.edit_frame_talent,
            text="選択タレントタグを削除",
            width=18,
            command=lambda: self.delete_selected("talent"),
        )
        self.delete_btn_talent.grid(row=2, column=4, padx=8, pady=5)

        # ユニットタグ編集フォーム
        self.edit_frame_unit = tk.LabelFrame(
            self.tab_unit, text="ユニットタグ編集", padx=10, pady=8
        )
        self.edit_frame_unit.pack(fill="x", padx=12, pady=8)
        tk.Label(self.edit_frame_unit, text="ID:").grid(
            row=0, column=0, sticky="e", padx=4, pady=2
        )
        self.edit_id_unit = tk.Entry(self.edit_frame_unit, width=12)
        self.edit_id_unit.grid(row=0, column=1, sticky="w", padx=4, pady=2)
        tk.Label(self.edit_frame_unit, text="名前:").grid(
            row=0, column=2, sticky="e", padx=4, pady=2
        )
        self.edit_name_unit = tk.Entry(self.edit_frame_unit, width=24)
        self.edit_name_unit.grid(row=0, column=3, sticky="w", padx=4, pady=2)
        tk.Label(self.edit_frame_unit, text="期生(カンマ区切り):").grid(
            row=1, column=0, sticky="e", padx=4, pady=2
        )
        self.edit_generation_unit = tk.Entry(self.edit_frame_unit, width=24)
        self.edit_generation_unit.grid(row=1, column=1, sticky="w", padx=4, pady=2)
        tk.Label(self.edit_frame_unit, text="タレント(カンマ区切り):").grid(
            row=1, column=2, sticky="e", padx=4, pady=2
        )
        self.edit_talent_unit = tk.Entry(self.edit_frame_unit, width=24)
        self.edit_talent_unit.grid(row=1, column=3, sticky="w", padx=4, pady=2)
        # タレントタグ選択（ユニット編集用）
        tk.Label(self.edit_frame_unit, text="タレントタグ選択:").grid(
            row=2, column=2, sticky="e", padx=4, pady=2
        )
        self.listbox_talent_unit = tk.Listbox(
            self.edit_frame_unit,
            selectmode=tk.MULTIPLE,
            height=4,
            exportselection=False,
        )
        self.listbox_talent_unit.grid(row=2, column=3, sticky="w")
        self.btn_add_talent_unit = tk.Button(
            self.edit_frame_unit, text="追加", command=self.add_selected_talent_unit
        )
        self.btn_add_talent_unit.grid(row=2, column=4, sticky="w")
        tk.Label(self.edit_frame_unit, text="タグフラグ:").grid(
            row=2, column=0, sticky="e", padx=4, pady=2
        )
        self.edit_tagflag_unit = ttk.Combobox(
            self.edit_frame_unit, values=["true", "false"], width=8, state="readonly"
        )
        self.edit_tagflag_unit.grid(row=2, column=1, sticky="w", padx=4, pady=2)
        self.update_btn_unit = tk.Button(
            self.edit_frame_unit,
            text="選択ユニットタグを更新",
            width=18,
            command=lambda: self.update_selected("unit"),
        )
        self.update_btn_unit.grid(row=3, column=2, padx=8, pady=5)
        self.add_btn_unit = tk.Button(
            self.edit_frame_unit,
            text="新規ユニットタグを追加",
            width=18,
            command=self.add_new_unit,
        )
        self.add_btn_unit.grid(row=3, column=3, padx=8, pady=5)

        # ユニット削除ボタン
        self.delete_btn_unit = tk.Button(
            self.edit_frame_unit,
            text="選択ユニットタグを削除",
            width=18,
            command=lambda: self.delete_selected("unit"),
        )
        self.delete_btn_unit.grid(row=3, column=4, padx=8, pady=5)

        # カテゴリタグ編集フォーム
        self.edit_frame_category = tk.LabelFrame(
            self.tab_category, text="カテゴリタグ編集", padx=10, pady=8
        )
        self.edit_frame_category.pack(fill="x", padx=12, pady=8)
        tk.Label(self.edit_frame_category, text="ID:").grid(
            row=0, column=0, sticky="e", padx=4, pady=2
        )
        self.edit_id_category = tk.Entry(self.edit_frame_category, width=12)
        self.edit_id_category.grid(row=0, column=1, sticky="w", padx=4, pady=2)
        tk.Label(self.edit_frame_category, text="名前:").grid(
            row=0, column=2, sticky="e", padx=4, pady=2
        )
        self.edit_name_category = tk.Entry(self.edit_frame_category, width=24)
        self.edit_name_category.grid(row=0, column=3, sticky="w", padx=4, pady=2)
        tk.Label(self.edit_frame_category, text="カテゴリ(カンマ区切り):").grid(
            row=1, column=0, sticky="e", padx=4, pady=2
        )
        self.edit_category_category = tk.Entry(self.edit_frame_category, width=30)
        self.edit_category_category.grid(
            row=1, column=1, columnspan=2, sticky="w", padx=4, pady=2
        )
        tk.Label(self.edit_frame_category, text="タグフラグ:").grid(
            row=1, column=3, sticky="e", padx=4, pady=2
        )
        self.edit_tagflag_category = ttk.Combobox(
            self.edit_frame_category,
            values=["true", "false"],
            width=8,
            state="readonly",
        )
        self.edit_tagflag_category.grid(row=1, column=4, sticky="w", padx=4, pady=2)
        self.update_btn_category = tk.Button(
            self.edit_frame_category,
            text="選択カテゴリタグを更新",
            width=18,
            command=lambda: self.update_selected("category"),
        )
        self.update_btn_category.grid(row=2, column=1, padx=8, pady=5)
        self.add_btn_category = tk.Button(
            self.edit_frame_category,
            text="新規カテゴリタグを追加",
            width=18,
            command=self.add_new_category,
        )
        self.add_btn_category.grid(row=2, column=2, padx=8, pady=5)

        # カテゴリ削除ボタン
        self.delete_btn_category = tk.Button(
            self.edit_frame_category,
            text="選択カテゴリタグを削除",
            width=18,
            command=lambda: self.delete_selected("category"),
        )
        self.delete_btn_category.grid(row=2, column=3, padx=8, pady=5)

        # グッズ編集フォーム
        self.edit_frame_goods = tk.LabelFrame(
            self.tab_goods, text="グッズ編集", padx=5, pady=5
        )
        self.edit_frame_goods.pack(fill="x", padx=5, pady=5)
        tk.Label(self.edit_frame_goods, text="ID:").grid(row=0, column=0, sticky="e")
        self.edit_id_goods = tk.Entry(self.edit_frame_goods, width=10)
        self.edit_id_goods.grid(row=0, column=1, sticky="w")
        tk.Label(self.edit_frame_goods, text="名前:").grid(row=0, column=2, sticky="e")
        self.edit_name_goods = tk.Entry(self.edit_frame_goods, width=30)
        self.edit_name_goods.grid(row=0, column=3, sticky="w")
        tk.Label(self.edit_frame_goods, text="価格:").grid(row=0, column=4, sticky="e")
        self.edit_price_goods = tk.Entry(self.edit_frame_goods, width=8)
        self.edit_price_goods.grid(row=0, column=5, sticky="w")

        # --- カテゴリタグ選択 ---
        tk.Label(self.edit_frame_goods, text="カテゴリタグ選択:").grid(
            row=1, column=0, sticky="e"
        )
        self.listbox_category_select = tk.Listbox(
            self.edit_frame_goods,
            selectmode=tk.MULTIPLE,
            height=4,
            exportselection=False,
        )
        self.listbox_category_select.grid(row=1, column=1, sticky="w")
        self.btn_add_category = tk.Button(
            self.edit_frame_goods, text="追加", command=self.add_selected_category
        )
        self.btn_add_category.grid(row=1, column=2, sticky="w")
        # 選択済み表示（readonly Entry）
        self.edit_category_goods = tk.Entry(
            self.edit_frame_goods, width=60, state="readonly"
        )
        self.edit_category_goods.grid(row=1, column=3, columnspan=3, sticky="w")

        # --- タレントタグ選択 ---
        tk.Label(self.edit_frame_goods, text="タレントタグ選択:").grid(
            row=2, column=0, sticky="e"
        )
        self.listbox_talent_select = tk.Listbox(
            self.edit_frame_goods,
            selectmode=tk.MULTIPLE,
            height=4,
            exportselection=False,
        )
        self.listbox_talent_select.grid(row=2, column=1, sticky="w")
        self.btn_add_talent = tk.Button(
            self.edit_frame_goods, text="追加", command=self.add_selected_talent
        )
        self.btn_add_talent.grid(row=2, column=2, sticky="w")
        self.edit_talent_goods = tk.Entry(
            self.edit_frame_goods, width=60, state="readonly"
        )
        self.edit_talent_goods.grid(row=2, column=3, columnspan=3, sticky="w")

        # --- ユニットタグ選択 ---
        tk.Label(self.edit_frame_goods, text="ユニットタグ選択:").grid(
            row=3, column=0, sticky="e"
        )
        self.listbox_unit_select = tk.Listbox(
            self.edit_frame_goods,
            selectmode=tk.MULTIPLE,
            height=4,
            exportselection=False,
        )
        self.listbox_unit_select.grid(row=3, column=1, sticky="w")
        self.btn_add_unit = tk.Button(
            self.edit_frame_goods, text="追加", command=self.add_selected_unit
        )
        self.btn_add_unit.grid(row=3, column=2, sticky="w")
        self.edit_generation_goods = tk.Entry(
            self.edit_frame_goods, width=60, state="readonly"
        )
        self.edit_generation_goods.grid(row=3, column=3, columnspan=3, sticky="w")

        # タグフラグ
        tk.Label(self.edit_frame_goods, text="タグフラグ:").grid(
            row=4, column=0, sticky="e"
        )
        self.edit_tagflag_goods = ttk.Combobox(
            self.edit_frame_goods, values=["true", "false"], width=6, state="readonly"
        )
        self.edit_tagflag_goods.grid(row=4, column=1, sticky="w")
        # 画像URL
        tk.Label(self.edit_frame_goods, text="画像URL:").grid(
            row=4, column=2, sticky="e"
        )
        self.edit_image_goods = tk.Entry(self.edit_frame_goods, width=60)
        self.edit_image_goods.grid(row=4, column=3, columnspan=3, sticky="w")

        self.update_btn_goods = tk.Button(
            self.edit_frame_goods,
            text="選択グッズを更新",
            command=lambda: self.update_selected("goods"),
        )
        self.update_btn_goods.grid(row=5, column=0, columnspan=6, pady=5)

        # --- 新規グッズ追加ボタン ---
        self.add_btn_goods = tk.Button(
            self.edit_frame_goods,
            text="新規グッズを追加",
            command=self.add_new_goods,
        )
        self.add_btn_goods.grid(row=6, column=0, columnspan=6, pady=5)

        # グッズ削除ボタン
        self.delete_btn_goods = tk.Button(
            self.edit_frame_goods,
            text="選択グッズを削除",
            command=lambda: self.delete_selected("goods"),
        )
        self.delete_btn_goods.grid(row=7, column=0, columnspan=6, pady=5)

    def delete_selected(self, kind):
        if kind == "talent":
            tree, items = self.tree_talent, self.items_talent
        elif kind == "unit":
            tree, items = self.tree_unit, self.items_unit
        elif kind == "category":
            tree, items = self.tree_category, self.items_category
        else:
            tree, items = self.tree_goods, self.items_goods
        selected = tree.selection()
        if not selected:
            messagebox.showwarning(
                "削除エラー", "削除するアイテムをリストから選択してください"
            )
            return
        idx = tree.index(selected[0])
        item_id = items[idx]["id"]
        # itemsから削除
        del items[idx]
        # loaded_jsonからも削除
        self.loaded_json = [
            p for p in self.loaded_json if str(p.get("id")) != str(item_id)
        ]
        self.refresh_listbox_all()
        messagebox.showinfo("削除", "選択アイテムを削除しました")

    def add_new_goods(self):
        # 入力欄から値を取得
        name = self.edit_name_goods.get().strip()
        price = self.edit_price_goods.get().strip()
        category = [
            s.strip() for s in self.edit_category_goods.get().split(",") if s.strip()
        ]
        talent = [
            s.strip() for s in self.edit_talent_goods.get().split(",") if s.strip()
        ]
        generation = [
            s.strip() for s in self.edit_generation_goods.get().split(",") if s.strip()
        ]
        tagflag = self.edit_tagflag_goods.get() == "true"
        image = self.edit_image_goods.get().strip()
        # 必須項目チェック
        if not name:
            messagebox.showwarning("入力エラー", "名前を入力してください")
            return
        try:
            price_val = int(price) if price else 0
        except Exception:
            messagebox.showwarning("入力エラー", "価格は数値で入力してください")
            return
        # 新しいIDはグッズリストの最大ID+1または1
        if self.items_goods:
            new_id = (
                max(
                    [
                        int(p.get("id", 0))
                        for p in self.items_goods
                        if str(p.get("id", "")).isdigit()
                    ]
                    + [0]
                )
                + 1
            )
        else:
            new_id = 1
        new_item = {
            "id": new_id,
            "name": name,
            "price": price_val,
            "category": category,
            "talent": talent,
            "generation": generation,
            "tagFlag": tagflag,
            "image": image,
        }
        self.items_goods.append(new_item)
        self.loaded_json.append(new_item)
        self.refresh_listbox_all()
        messagebox.showinfo("追加", "新規グッズを追加しました")

        # タグリスト初期化
        # すべてのウィジェット生成後にのみ呼ぶ
        self.refresh_listbox_all()

    def add_selected_talent(self):
        selected = [
            self.items_talent[i]["name"]
            for i in self.listbox_talent_select.curselection()
        ]
        self.edit_talent_goods.config(state="normal")
        self.edit_talent_goods.delete(0, tk.END)
        self.edit_talent_goods.insert(0, ",".join(selected))
        self.edit_talent_goods.config(state="readonly")

    def add_selected_unit(self):
        selected = [
            self.items_unit[i]["name"] for i in self.listbox_unit_select.curselection()
        ]
        self.edit_generation_goods.config(state="normal")
        self.edit_generation_goods.delete(0, tk.END)
        self.edit_generation_goods.insert(0, ",".join(selected))
        self.edit_generation_goods.config(state="readonly")

    def add_selected_talent_unit(self):
        selected = [
            self.items_talent[i]["name"]
            for i in self.listbox_talent_unit.curselection()
        ]
        self.edit_talent_unit.config(state="normal")
        self.edit_talent_unit.delete(0, tk.END)
        self.edit_talent_unit.insert(0, ",".join(selected))
        self.edit_talent_unit.config(state="readonly")

    def on_tab_changed(self, event):
        # Notebookのindex取得はevent.widgetから行うことでTclErrorを防ぐ
        notebook = event.widget
        try:
            tab = notebook.index(notebook.select())
        except Exception:
            return
        is_goods = tab == 3  # 0:T, 1:U, 2:C, 3:グッズ
        state = "normal" if is_goods else "disabled"
        for w in [
            self.url_label,
            self.url_entry,
            self.fetch_btn,
            self.variation_label,
            self.variation_combo,
            self.add_btn,
        ]:
            try:
                w.configure(state=state)
            except Exception:
                pass
        # （上記タブ追加処理は__init__でのみ実行。on_tab_changedでは絶対に追加しない）

        # 追加保存・既存JSON読み込みボタンはメニューに統合したため削除

        # 各リストボックス選択時に編集フォームへ反映
        self.tree_talent.bind(
            "<<TreeviewSelect>>", lambda e: self.on_treeview_select("talent")
        )
        self.tree_unit.bind(
            "<<TreeviewSelect>>", lambda e: self.on_treeview_select("unit")
        )
        self.tree_category.bind(
            "<<TreeviewSelect>>", lambda e: self.on_treeview_select("category")
        )
        self.tree_goods.bind(
            "<<TreeviewSelect>>", lambda e: self.on_treeview_select("goods")
        )

    def on_treeview_select(self, kind):
        if kind == "talent":
            tree = self.tree_talent
            items = self.items_talent
            edit_id = self.edit_id_talent
            edit_name = self.edit_name_talent
            edit_generation = self.edit_generation_talent
            edit_talent = self.edit_talent_talent
            edit_tagflag = self.edit_tagflag_talent
        elif kind == "unit":
            tree = self.tree_unit
            items = self.items_unit
            edit_id = self.edit_id_unit
            edit_name = self.edit_name_unit
            edit_generation = self.edit_generation_unit
            edit_talent = self.edit_talent_unit
            edit_tagflag = self.edit_tagflag_unit
        elif kind == "category":
            tree = self.tree_category
            items = self.items_category
            edit_id = self.edit_id_category
            edit_name = self.edit_name_category
            edit_generation = None
            edit_talent = None
            edit_tagflag = self.edit_tagflag_category
        else:
            tree = self.tree_goods
            items = self.items_goods
            edit_id = self.edit_id_goods
            edit_name = self.edit_name_goods
            edit_generation = self.edit_generation_goods
            edit_talent = self.edit_talent_goods
            edit_tagflag = self.edit_tagflag_goods
            edit_price = self.edit_price_goods
            edit_category = self.edit_category_goods
            edit_image = self.edit_image_goods
        selected = tree.selection()
        if not selected:
            return
        idx = tree.index(selected[0])
        p = items[idx]
        # タレント
        if kind == "talent":
            edit_id.delete(0, tk.END)
            edit_id.insert(0, p.get("id", ""))
            edit_name.delete(0, tk.END)
            edit_name.insert(0, p.get("name", ""))
            edit_generation.delete(0, tk.END)
            edit_generation.insert(
                0,
                (
                    ",".join(p.get("generation", []))
                    if isinstance(p.get("generation", []), list)
                    else str(p.get("generation", ""))
                ),
            )
            edit_talent.delete(0, tk.END)
            edit_talent.insert(
                0,
                (
                    ",".join(p.get("talent", []))
                    if isinstance(p.get("talent", []), list)
                    else str(p.get("talent", ""))
                ),
            )
            if edit_tagflag:
                edit_tagflag.set(str(p.get("tagFlag", "false")).lower())
        # ユニット
        elif kind == "unit":
            edit_id.delete(0, tk.END)
            edit_id.insert(0, p.get("id", ""))
            edit_name.delete(0, tk.END)
            edit_name.insert(0, p.get("name", ""))
            edit_generation.delete(0, tk.END)
            edit_generation.insert(
                0,
                (
                    ",".join(p.get("generation", []))
                    if isinstance(p.get("generation", []), list)
                    else str(p.get("generation", ""))
                ),
            )
            edit_talent.delete(0, tk.END)
            edit_talent.insert(
                0,
                (
                    ",".join(p.get("talent", []))
                    if isinstance(p.get("talent", []), list)
                    else str(p.get("talent", ""))
                ),
            )
            if edit_tagflag:
                edit_tagflag.set(str(p.get("tagFlag", "false")).lower())
        # カテゴリ
        elif kind == "category":
            edit_id.delete(0, tk.END)
            edit_id.insert(0, p.get("id", ""))
            edit_name.delete(0, tk.END)
            edit_name.insert(0, p.get("name", ""))
            self.edit_category_category.delete(0, tk.END)
            self.edit_category_category.insert(
                0,
                (
                    ",".join(p.get("category", []))
                    if isinstance(p.get("category", []), list)
                    else str(p.get("category", ""))
                ),
            )
            if edit_tagflag:
                edit_tagflag.set(str(p.get("tagFlag", "false")).lower())
        # グッズ
        else:
            edit_id.delete(0, tk.END)
            edit_id.insert(0, p.get("id", ""))
            edit_name.delete(0, tk.END)
            edit_name.insert(0, p.get("name", ""))
            edit_price.delete(0, tk.END)
            edit_price.insert(0, p.get("price", ""))
            edit_category.config(state="normal")
            edit_category.delete(0, tk.END)
            edit_category.insert(
                0,
                (
                    ",".join(p.get("category", []))
                    if isinstance(p.get("category", []), list)
                    else str(p.get("category", ""))
                ),
            )
            edit_category.config(state="readonly")
            edit_talent.config(state="normal")
            edit_talent.delete(0, tk.END)
            edit_talent.insert(
                0,
                (
                    ",".join(p.get("talent", []))
                    if isinstance(p.get("talent", []), list)
                    else str(p.get("talent", ""))
                ),
            )
            edit_talent.config(state="readonly")
            edit_generation.config(state="normal")
            edit_generation.delete(0, tk.END)
            edit_generation.insert(
                0,
                (
                    ",".join(p.get("generation", []))
                    if isinstance(p.get("generation", []), list)
                    else str(p.get("generation", ""))
                ),
            )
            edit_generation.config(state="readonly")
            if edit_tagflag:
                edit_tagflag.set(str(p.get("tagFlag", "false")).lower())
            edit_image.delete(0, tk.END)
            edit_image.insert(0, p.get("image", ""))

    def update_selected(self, kind=None):
        # kindが指定されていればそれを優先、なければタブインデックスで判定
        if kind is None:
            tab = self.notebook.index(self.notebook.select())
            if tab == 0:
                kind = "talent"
            elif tab == 1:
                kind = "unit"
            elif tab == 2:
                kind = "category"
            else:
                kind = "goods"

        if kind == "talent":
            tree, items = self.tree_talent, self.items_talent
            edit_id = self.edit_id_talent
            edit_name = self.edit_name_talent
            edit_generation = self.edit_generation_talent
            edit_talent = self.edit_talent_talent
            edit_tagflag = self.edit_tagflag_talent
            edit_price = None
            edit_category = None
            edit_image = None
        elif kind == "unit":
            tree, items = self.tree_unit, self.items_unit
            edit_id = self.edit_id_unit
            edit_name = self.edit_name_unit
            edit_generation = self.edit_generation_unit
            edit_talent = self.edit_talent_unit
            edit_tagflag = self.edit_tagflag_unit
            edit_price = None
            edit_category = None
            edit_image = None
        elif kind == "category":
            tree, items = self.tree_category, self.items_category
            edit_id = self.edit_id_category
            edit_name = self.edit_name_category
            edit_generation = None
            edit_talent = None
            edit_tagflag = self.edit_tagflag_category
            edit_price = None
            edit_category = self.edit_category_category
            edit_image = None
        else:
            tree, items = self.tree_goods, self.items_goods
            edit_id = self.edit_id_goods
            edit_name = self.edit_name_goods
            edit_generation = self.edit_generation_goods
            edit_talent = self.edit_talent_goods
            edit_tagflag = self.edit_tagflag_goods
            edit_price = self.edit_price_goods
            edit_category = self.edit_category_goods
            edit_image = self.edit_image_goods

        selected = tree.selection()
        if not selected:
            messagebox.showwarning(
                "選択エラー", "編集するアイテムをリストから選択してください"
            )
            return
        idx = tree.index(selected[0])

        # 値取得
        if edit_price:
            try:
                price = int(edit_price.get()) if edit_price.get() else 0
            except Exception:
                price = edit_price.get()
        else:
            price = None
        if edit_category:
            category_val = [
                s.strip() for s in edit_category.get().split(",") if s.strip()
            ]
        else:
            category_val = None
        if edit_talent:
            talent_val = [s.strip() for s in edit_talent.get().split(",") if s.strip()]
        else:
            talent_val = None
        if edit_generation:
            generation_val = [
                s.strip() for s in edit_generation.get().split(",") if s.strip()
            ]
        else:
            generation_val = None
        tagflag_val = edit_tagflag.get() == "true" if edit_tagflag else False
        image_val = edit_image.get() if edit_image else ""

        # IDで該当アイテムを特定し、items/loaded_json両方を更新
        if kind == "goods":
            # グッズはIDが連番なので、IDで該当アイテムを探す
            item_id = self.edit_id_goods.get().strip()
            # items_goods内の該当アイテム
            for i, p in enumerate(self.items_goods):
                if str(p.get("id")) == item_id:
                    idx = i
                    break
            else:
                messagebox.showwarning("エラー", "該当グッズが見つかりません")
                return
            # loaded_json内の該当アイテムも更新
            for j, p in enumerate(self.loaded_json):
                if str(p.get("id")) == item_id and not (
                    str(p.get("id", "")).startswith("T")
                    or str(p.get("id", "")).startswith("U")
                    or str(p.get("id", "")).startswith("C")
                ):
                    self.loaded_json[j] = {
                        "id": item_id,
                        "name": edit_name.get(),
                        "price": price,
                        "category": category_val,
                        "talent": talent_val,
                        "generation": generation_val,
                        "tagFlag": tagflag_val,
                        "image": image_val,
                    }
                    break
            # items_goodsも更新
            self.items_goods[idx] = {
                "id": item_id,
                "name": edit_name.get(),
                "price": price,
                "category": category_val,
                "talent": talent_val,
                "generation": generation_val,
                "tagFlag": tagflag_val,
                "image": image_val,
            }
        else:
            # タレント・ユニット・カテゴリもIDで該当アイテムを探して更新
            item_id = edit_id.get().strip()
            for i, p in enumerate(items):
                if str(p.get("id")) == item_id:
                    idx = i
                    break
            else:
                messagebox.showwarning("エラー", "該当アイテムが見つかりません")
                return
            new_item = dict(items[idx])
            if edit_id:
                new_item["id"] = edit_id.get()
            if edit_name:
                new_item["name"] = edit_name.get()
            if price is not None:
                new_item["price"] = price
            if category_val is not None:
                new_item["category"] = category_val
            if talent_val is not None:
                new_item["talent"] = talent_val
            if generation_val is not None:
                new_item["generation"] = generation_val
            if edit_tagflag:
                new_item["tagFlag"] = tagflag_val
            if image_val != "":
                new_item["image"] = image_val
            items[idx] = new_item
            # loaded_json側もID一致で更新
            for j, p in enumerate(self.loaded_json):
                if str(p.get("id")) == str(new_item["id"]):
                    self.loaded_json[j] = new_item
                    break

        self.refresh_listbox_all()
        # 再描画後、同じIDの行を再選択
        children = tree.get_children()
        select_idx = None
        if kind == "goods":
            for i, iid in enumerate(children):
                vals = tree.item(iid, "values")
                if str(vals[0]) == str(item_id):
                    select_idx = i
                    break
        else:
            for i, iid in enumerate(children):
                vals = tree.item(iid, "values")
                if str(vals[0]) == str(new_item["id"]):
                    select_idx = i
                    break
        tree.selection_remove(tree.selection())
        if select_idx is not None and 0 <= select_idx < len(children):
            tree.selection_set(children[select_idx])
        messagebox.showinfo("更新", "アイテム情報を更新しました")

    def fetch(self):
        url = self.url_entry.get().strip()
        m = re.search(r"/items/(\d+)", url)
        if not m:
            messagebox.showerror("エラー", "URLから商品IDが取得できません")
            return
        item_id = m.group(1)
        api_url = f'https://{url.split("/")[2]}/items/{item_id}.json'
        try:
            resp = requests.get(api_url)
            resp.raise_for_status()
            booth_json = resp.json()
        except Exception as e:
            messagebox.showerror("API取得エラー", str(e))
            return
        self.products = booth_to_products(booth_json)
        self.variation_combo["values"] = [p["name"] for p in self.products]
        if self.products:
            self.variation_combo.current(0)
        messagebox.showinfo(
            "取得完了", f"{len(self.products)}件のバリエーションを取得しました"
        )

    def add_to_list(self):
        idx = self.variation_combo.current()
        if idx < 0 or not self.products:
            messagebox.showwarning("選択エラー", "バリエーションを選択してください")
            return
        product = self.products[idx]
        # 編集欄に反映
        self.edit_id_goods.delete(0, tk.END)
        self.edit_id_goods.insert(0, product.get("id", ""))
        self.edit_name_goods.delete(0, tk.END)
        self.edit_name_goods.insert(0, product.get("name", ""))
        self.edit_price_goods.delete(0, tk.END)
        self.edit_price_goods.insert(0, product.get("price", ""))
        self.edit_category_goods.config(state="normal")
        self.edit_category_goods.delete(0, tk.END)
        self.edit_category_goods.insert(
            0,
            (
                ",".join(product.get("category", []))
                if isinstance(product.get("category", []), list)
                else str(product.get("category", ""))
            ),
        )
        self.edit_category_goods.config(state="readonly")
        self.edit_talent_goods.config(state="normal")
        self.edit_talent_goods.delete(0, tk.END)
        self.edit_talent_goods.insert(
            0,
            (
                ",".join(product.get("talent", []))
                if isinstance(product.get("talent", []), list)
                else str(product.get("talent", ""))
            ),
        )
        self.edit_talent_goods.config(state="readonly")
        self.edit_generation_goods.config(state="normal")
        self.edit_generation_goods.delete(0, tk.END)
        self.edit_generation_goods.insert(
            0,
            (
                ",".join(product.get("generation", []))
                if isinstance(product.get("generation", []), list)
                else str(product.get("generation", ""))
            ),
        )
        self.edit_generation_goods.config(state="readonly")
        self.edit_tagflag_goods.set(str(product.get("tagFlag", "false")).lower())
        # バリエーションのインデックスに紐づくimagesの画像URLを設定
        image_url = ""
        images = product.get("image", [{}])[idx + 1].get("original", "")
        image_url = images
        self.edit_image_goods.delete(0, tk.END)
        self.edit_image_goods.insert(0, image_url)

        # 画像プレビュー表示
        self.show_goods_image_preview(image_url)
        messagebox.showinfo("反映", "バリエーション情報を編集欄に反映しました")

    def show_goods_image_preview(self, url):
        if not hasattr(self, "goods_image_label"):
            # 初回のみラベル生成
            self.goods_image_label = tk.Label(self.edit_frame_goods)
            self.goods_image_label.grid(row=4, column=6, rowspan=3, padx=8, pady=2)
        if not url:
            self.goods_image_label.config(image="", text="No Image")
            self.goods_image_label.image = None
            return
        try:
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            img_data = resp.content
            img = Image.open(io.BytesIO(img_data))
            img.thumbnail((80, 80))
            tk_img = ImageTk.PhotoImage(img)
            self.goods_image_label.config(image=tk_img, text="")
            self.goods_image_label.image = tk_img  # 保持
        except Exception:
            self.goods_image_label.config(image="", text="No Image")
            self.goods_image_label.image = None

    def refresh_listbox_all(self):
        # データを4分類（ID重複を排除）
        seen_ids = set()
        self.items_talent = []
        self.items_unit = []
        self.items_category = []
        self.items_goods = []
        for p in self.loaded_json:
            pid = str(p.get("id", ""))
            if pid.startswith("T"):
                if pid not in seen_ids:
                    self.items_talent.append(p)
                    seen_ids.add(pid)
            elif pid.startswith("U"):
                if pid not in seen_ids:
                    self.items_unit.append(p)
                    seen_ids.add(pid)
            elif pid.startswith("C"):
                if pid not in seen_ids:
                    self.items_category.append(p)
                    seen_ids.add(pid)
            else:
                if pid not in seen_ids:
                    self.items_goods.append(p)
                    seen_ids.add(pid)

        # IDを順番に振り直す
        # タレント
        for idx, p in enumerate(self.items_talent, 1):
            p["id"] = f"T{idx:03d}"
        # ユニット
        for idx, p in enumerate(self.items_unit, 1):
            p["id"] = f"U{idx:03d}"
        # カテゴリ
        for idx, p in enumerate(self.items_category, 1):
            p["id"] = f"C{idx:03d}"
        # グッズ
        for idx, p in enumerate(self.items_goods, 1):
            p["id"] = idx
        # 各リストボックスを更新（グッズ編集欄のタグ選択リストも含む）
        # Treeviewの内容をクリア
        for tree in [
            self.tree_talent,
            self.tree_unit,
            self.tree_category,
            self.tree_goods,
        ]:
            for i in tree.get_children():
                tree.delete(i)
        # --- タレント ---
        for p in self.items_talent:
            self.tree_talent.insert(
                "",
                "end",
                values=(
                    p.get("id", ""),
                    p.get("name", ""),
                    (
                        ",".join(p.get("generation", []))
                        if isinstance(p.get("generation", []), list)
                        else str(p.get("generation", ""))
                    ),
                    (
                        ",".join(p.get("talent", []))
                        if isinstance(p.get("talent", []), list)
                        else str(p.get("talent", ""))
                    ),
                    str(p.get("tagFlag", "")),
                ),
            )
        # --- ユニット ---
        for p in self.items_unit:
            self.tree_unit.insert(
                "",
                "end",
                values=(
                    p.get("id", ""),
                    p.get("name", ""),
                    (
                        ",".join(p.get("generation", []))
                        if isinstance(p.get("generation", []), list)
                        else str(p.get("generation", ""))
                    ),
                    (
                        ",".join(p.get("talent", []))
                        if isinstance(p.get("talent", []), list)
                        else str(p.get("talent", ""))
                    ),
                    str(p.get("tagFlag", "")),
                ),
            )
        # --- カテゴリ ---
        for p in self.items_category:
            self.tree_category.insert(
                "",
                "end",
                values=(
                    p.get("id", ""),
                    p.get("name", ""),
                    (
                        ",".join(p.get("category", []))
                        if isinstance(p.get("category", []), list)
                        else str(p.get("category", ""))
                    ),
                    str(p.get("tagFlag", "")),
                ),
            )
        # --- グッズ ---

        for p in self.items_goods:
            self.tree_goods.insert(
                "",
                "end",
                values=(
                    p.get("id", ""),
                    p.get("name", ""),
                    p.get("price", ""),
                    (
                        ",".join(p.get("generation", []))
                        if isinstance(p.get("generation", []), list)
                        else str(p.get("generation", ""))
                    ),
                    (
                        ",".join(p.get("talent", []))
                        if isinstance(p.get("talent", []), list)
                        else str(p.get("talent", ""))
                    ),
                    (
                        ",".join(p.get("category", []))
                        if isinstance(p.get("category", []), list)
                        else str(p.get("category", ""))
                    ),
                    str(p.get("tagFlag", "")),
                ),
            )
        # グッズ編集欄のタグ選択リスト
        self.listbox_category_select.delete(0, tk.END)
        for p in self.items_category:
            self.listbox_category_select.insert(tk.END, p.get("name", ""))
        self.listbox_talent_select.delete(0, tk.END)
        for p in self.items_talent:
            self.listbox_talent_select.insert(tk.END, p.get("name", ""))
        # ユニット編集欄のタレントリストも更新
        self.listbox_talent_unit.delete(0, tk.END)
        for p in self.items_talent:
            self.listbox_talent_unit.insert(tk.END, p.get("name", ""))
        self.listbox_unit_select.delete(0, tk.END)
        for p in self.items_unit:
            self.listbox_unit_select.insert(tk.END, p.get("name", ""))


def main():
    root = tk.Tk()
    app = BoothGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
