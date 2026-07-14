from __future__ import annotations

import os
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk

from PIL import Image, ImageTk

from product_reco_bot.desktop.service import DesktopService


class DesktopApp(tk.Tk):
    def __init__(self, service: DesktopService) -> None:
        super().__init__()
        self.service = service
        self.title("精品推荐运营台")
        self.geometry("1180x760")
        self.minsize(980, 640)
        self.configure(background="#f4f1ea")
        self.products: list[dict[str, object]] = []
        self._card_image: ImageTk.PhotoImage | None = None
        self._configure_style()
        self._build()
        self.refresh_products()

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook", background="#f4f1ea", borderwidth=0)
        style.configure("TNotebook.Tab", padding=(20, 10), font=("Microsoft YaHei UI", 10))
        style.configure("Treeview", rowheight=34, font=("Microsoft YaHei UI", 10))
        style.configure("Treeview.Heading", font=("Microsoft YaHei UI", 10, "bold"))
        style.configure("Accent.TButton", font=("Microsoft YaHei UI", 10, "bold"))

    def _build(self) -> None:
        header = tk.Frame(self, bg="#1f2b26", height=72)
        header.pack(fill="x")
        tk.Label(
            header,
            text="精品推荐 · 本地运营台",
            bg="#1f2b26",
            fg="white",
            font=("Microsoft YaHei UI", 18, "bold"),
        ).pack(side="left", padx=24, pady=18)
        tk.Label(
            header,
            text="本机运行 · 默认 Dry Run",
            bg="#1f2b26",
            fg="#b8c8c0",
            font=("Microsoft YaHei UI", 10),
        ).pack(side="right", padx=24)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=18, pady=16)
        self.products_tab = ttk.Frame(notebook)
        self.sources_tab = ttk.Frame(notebook)
        self.logs_tab = ttk.Frame(notebook)
        notebook.add(self.products_tab, text="候选商品")
        notebook.add(self.sources_tab, text="数据源")
        notebook.add(self.logs_tab, text="同步日志")
        notebook.bind("<<NotebookTabChanged>>", self._tab_changed)
        self._build_products()
        self._build_sources()
        self._build_logs()

    def _build_products(self) -> None:
        toolbar = ttk.Frame(self.products_tab, padding=10)
        toolbar.pack(fill="x")
        self.query = tk.StringVar()
        self.category = tk.StringVar(value="全部")
        ttk.Label(toolbar, text="搜索").pack(side="left")
        search = ttk.Entry(toolbar, textvariable=self.query, width=28)
        search.pack(side="left", padx=(6, 14))
        search.bind("<KeyRelease>", lambda event: self.render_products())
        category = ttk.Combobox(
            toolbar,
            textvariable=self.category,
            values=("全部", "饰品", "玩具"),
            state="readonly",
            width=9,
        )
        category.pack(side="left")
        category.bind("<<ComboboxSelected>>", lambda event: self.render_products())
        ttk.Button(toolbar, text="刷新", command=self.refresh_products).pack(side="right")
        ttk.Button(
            toolbar,
            text="批量批准",
            style="Accent.TButton",
            command=self.batch_approve,
        ).pack(side="right", padx=8)

        columns = ("category", "name", "price", "score", "label", "approved")
        self.product_tree = ttk.Treeview(
            self.products_tab, columns=columns, show="headings", selectmode="extended"
        )
        headings = {
            "category": "类目",
            "name": "商品名称",
            "price": "价格",
            "score": "火热指数",
            "label": "状态",
            "approved": "审核",
        }
        widths = {
            "category": 70,
            "name": 340,
            "price": 110,
            "score": 90,
            "label": 100,
            "approved": 80,
        }
        for key in columns:
            self.product_tree.heading(key, text=headings[key])
            anchor = "center" if key != "name" else "w"
            self.product_tree.column(key, width=widths[key], anchor=anchor)
        self.product_tree.pack(fill="both", expand=True, padx=10)
        self.product_tree.bind("<Double-1>", lambda event: self.show_detail())

        actions = ttk.Frame(self.products_tab, padding=10)
        actions.pack(fill="x")
        ttk.Button(actions, text="查看详情", command=self.show_detail).pack(side="left")
        ttk.Button(actions, text="批准", command=self.approve_selected).pack(side="left", padx=8)
        ttk.Button(actions, text="撤销批准", command=self.revoke_selected).pack(side="left")

    def _build_sources(self) -> None:
        columns = ("name", "configured", "enabled", "missing", "last")
        self.source_tree = ttk.Treeview(self.sources_tab, columns=columns, show="headings")
        for key, title, width in (
            ("name", "数据源", 180),
            ("configured", "配置", 90),
            ("enabled", "启用", 80),
            ("missing", "缺少凭证", 220),
            ("last", "最近同步", 300),
        ):
            self.source_tree.heading(key, text=title)
            self.source_tree.column(key, width=width)
        self.source_tree.pack(fill="both", expand=True, padx=10, pady=10)
        actions = ttk.Frame(self.sources_tab, padding=10)
        actions.pack(fill="x")
        ttk.Button(actions, text="刷新状态", command=self.refresh_sources).pack(side="left")
        ttk.Button(actions, text="启用 / 停用", command=self.toggle_source).pack(
            side="left", padx=8
        )
        ttk.Button(actions, text="测试多多进宝", command=self.test_pdd).pack(side="left")

    def _build_logs(self) -> None:
        columns = ("time", "source", "result", "message")
        self.log_tree = ttk.Treeview(self.logs_tab, columns=columns, show="headings")
        for key, title, width in (
            ("time", "时间", 220),
            ("source", "数据源", 160),
            ("result", "结果", 80),
            ("message", "信息", 520),
        ):
            self.log_tree.heading(key, text=title)
            self.log_tree.column(key, width=width)
        self.log_tree.pack(fill="both", expand=True, padx=10, pady=10)
        ttk.Button(self.logs_tab, text="刷新日志", command=self.refresh_logs).pack(
            anchor="w", padx=10, pady=(0, 10)
        )

    def refresh_products(self) -> None:
        try:
            self.products = self.service.recommendations()
            self.render_products()
        except Exception as exc:
            messagebox.showerror("读取失败", str(exc), parent=self)

    def render_products(self) -> None:
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)
        query = self.query.get().strip().lower()
        category = self.category.get()
        for product in self.products:
            if category != "全部" and product["category"] != category:
                continue
            if query and query not in f"{product['name']} {product['product_id']}".lower():
                continue
            self.product_tree.insert(
                "",
                "end",
                iid=str(product["product_id"]),
                values=(
                    product["category"],
                    product["name"],
                    f"{product['currency']} {float(product['price']):.2f}",
                    f"{float(product['score']):.1f}",
                    product["label"],
                    "已批准" if product["approved"] else "待审核",
                ),
            )

    def _selected_ids(self) -> list[str]:
        return [str(item) for item in self.product_tree.selection()]

    def approve_selected(self) -> None:
        selected = self._selected_ids()
        if not selected:
            messagebox.showinfo("提示", "请先选择商品", parent=self)
            return
        note = simpledialog.askstring("审核备注", "可填写审核备注：", parent=self) or ""
        for product_id in selected:
            self.service.approve(product_id, note)
        self.refresh_products()

    def batch_approve(self) -> None:
        selected = self._selected_ids() or [str(item) for item in self.product_tree.get_children()]
        if not selected:
            return
        if not messagebox.askyesno("确认", f"批准选中的 {len(selected)} 个商品？", parent=self):
            return
        note = simpledialog.askstring("统一备注", "可填写统一审核备注：", parent=self) or ""
        self.service.approve_many(selected, note)
        self.refresh_products()

    def revoke_selected(self) -> None:
        for product_id in self._selected_ids():
            self.service.revoke(product_id)
        self.refresh_products()

    def show_detail(self) -> None:
        selected = self._selected_ids()
        if not selected:
            messagebox.showinfo("提示", "请先选择一个商品", parent=self)
            return
        try:
            detail = self.service.detail(selected[0])
        except Exception as exc:
            messagebox.showerror("详情读取失败", str(exc), parent=self)
            return
        window = tk.Toplevel(self)
        window.title(str(detail["recommendation"].product.product_name))
        window.geometry("940x700")
        body = ttk.Frame(window, padding=14)
        body.pack(fill="both", expand=True)
        image = Image.open(detail["card"]).convert("RGB")
        image.thumbnail((360, 540))
        self._card_image = ImageTk.PhotoImage(image)
        ttk.Label(body, image=self._card_image).pack(side="left", fill="y", padx=(0, 16))
        texts = ttk.Notebook(body)
        texts.pack(side="left", fill="both", expand=True)
        for title, key in (("私域详情", "private_detail"), ("公域文案", "public_post")):
            frame = ttk.Frame(texts)
            widget = tk.Text(frame, wrap="word", font=("Microsoft YaHei UI", 10), padx=12, pady=12)
            widget.insert("1.0", str(detail[key]))
            widget.pack(fill="both", expand=True)
            ttk.Button(
                frame,
                text="复制",
                command=lambda w=widget: self._copy(w.get("1.0", "end-1c")),
            ).pack(
                anchor="e", pady=8
            )
            texts.add(frame, text=title)

    def _copy(self, text: str) -> None:
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("复制成功", "文案已复制到剪贴板", parent=self)

    def refresh_sources(self) -> None:
        for item in self.source_tree.get_children():
            self.source_tree.delete(item)
        for source in self.service.source_statuses():
            sync = source.get("last_sync") or {}
            last = sync.get("synced_at", "尚未同步") if isinstance(sync, dict) else "尚未同步"
            self.source_tree.insert(
                "",
                "end",
                iid=str(source["name"]),
                values=(
                    source["display_name"],
                    "完整" if source["configured"] else "未完成",
                    "是" if source["enabled"] else "否",
                    "、".join(source["missing_credentials"]),
                    last,
                ),
            )

    def toggle_source(self) -> None:
        selected = self.source_tree.selection()
        if not selected:
            return
        name = str(selected[0])
        current = self.service.sources.status(name)
        try:
            self.service.set_source_enabled(name, not current.enabled)
            self.refresh_sources()
        except Exception as exc:
            messagebox.showerror("操作失败", str(exc), parent=self)

    def test_pdd(self) -> None:
        try:
            self.service.test_pdd()
            messagebox.showinfo("连接成功", "多多进宝连接测试成功", parent=self)
        except Exception as exc:
            messagebox.showerror("连接失败", str(exc), parent=self)
        self.refresh_sources()

    def refresh_logs(self) -> None:
        for item in self.log_tree.get_children():
            self.log_tree.delete(item)
        for index, item in enumerate(self.service.sync_history()):
            self.log_tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    item.get("synced_at", ""),
                    item.get("source", ""),
                    "成功" if item.get("success") else "失败",
                    item.get("message", ""),
                ),
            )

    def _tab_changed(self, event) -> None:
        title = event.widget.tab(event.widget.select(), "text")
        if title == "数据源":
            self.refresh_sources()
        elif title == "同步日志":
            self.refresh_logs()


def main() -> None:
    root = Path(os.getenv("PRODUCT_RECO_PROJECT_ROOT", Path.cwd()))
    DesktopApp(DesktopService(root)).mainloop()


if __name__ == "__main__":
    main()
