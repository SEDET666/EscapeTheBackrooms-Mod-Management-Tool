import os, sys, shutil, winreg, re, json
from pathlib import Path
from PySide6.QtWidgets import QApplication, QFileDialog, QHeaderView, QWidget, QVBoxLayout, QHBoxLayout, QTableWidgetItem
from PySide6.QtCore import Qt, QThread, Signal
from qfluentwidgets import (FluentWindow, NavigationItemPosition, TableWidget, PushButton, PrimaryPushButton, 
                            InfoBar, InfoBarPosition, FluentIcon, RoundMenu, Action, MenuAnimationType, 
                            TitleLabel, BodyLabel, StrongBodyLabel, CardWidget, LineEdit, ComboBox, 
                            ListWidget, ProgressBar, Theme, setTheme, NavigationToolButton)
import requests, urllib3
from PySide6.QtGui import QColor
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LANG_DATA = {
    "zh": {
        "app_title": "逃离后室 - 工具箱",
        "nav_mod": "Mod 管理",
        "nav_lua": "Lua Mod 管理",
        "nav_ue4ss": "UE4SS 安装",
        "nav_about": "关于",
        "nav_setting": "设置",
        
        "btn_install": "安装 Mod (.pak)",
        "btn_refresh": "刷新列表",
        "btn_delete": "删除 Mod",
        "table_name": "文件名",
        "table_path": "所在路径",
        "table_root": "根目录",
        "ctx_delete": "删除选中的 Mod",
        "msg_err_path": "找不到游戏路径或 Paks 文件夹，请确认游戏是否已安装！",
        "msg_no_mod": "当前没有安装任何 Mod。",
        "msg_select_mod": "请先在列表中选择要删除的 Mod！",
        "msg_del_success": "已成功删除 {count} 个 Mod。",
        "msg_del_fail": "文件 {name} 删除失败(可能被占用): {err}",
        "msg_install_success": "已成功安装 {count} 个 Mod 到 LogicMods 文件夹。",
        "msg_copy_fail": "文件 {name} 复制失败: {err}",
        "msg_install_title": "安装成功",
        "msg_delete_title": "删除成功",
        "msg_drop_err": "仅支持拖入 .pak 文件！",
        
        "ue4ss_title": "UE4SS 自动下载与安装",
        "btn_fetch": "获取在线版本列表",
        "btn_dl_install": "下载并自动安装",
        "btn_dl_save": "下载到指定位置(不安装)",
        "msg_fetching": "正在连接 GitHub 获取版本列表，请稍候...",
        "msg_fetch_success": "获取到 {count} 个可用版本，请选择后操作。",
        "msg_select_ver": "请先获取列表并选择一个版本！",
        "msg_downloading": "正在下载中，请等待完成！",
        "msg_installing": "下载完成，正在解压覆盖到游戏目录，请稍候...",
        "msg_install_ok": "UE4SS 已成功安装到:\n{path}",
        "msg_install_err": "解压时出错(可能文件被占用): {err}\n临时文件保留在: {path}",
        "msg_save_ok": "文件已保存到:\n{path}",
        "msg_no_release": "未找到可用的发行版",
        "ctx_dl_install": "下载并自动安装",
        "ctx_dl_save": "下载到指定位置",
        
        "lua_title": "UE4SS Lua Mod 管理",
        "lua_btn_install": "安装 Lua Mod",
        "lua_btn_refresh": "刷新列表",
        "lua_table_name": "模组名称",
        "lua_table_status": "状态",
        "lua_status_enabled": "已启用",
        "lua_status_disabled": "已禁用",
        "lua_ctx_toggle": "切换启用/禁用",
        "lua_ctx_delete": "删除模组",
        "lua_msg_err_path": "找不到 UE4SS 的 Mods 目录，请确认是否已安装 UE4SS！",
        "lua_msg_no_mod": "当前没有安装任何 Lua Mod。",
        "lua_msg_install_ok": "Lua Mod {name} 安装成功并已默认启用。",
        "lua_msg_copy_err": "安装失败: {err}",
        "lua_msg_toggle_ok": "已将 {name} 状态更改为 {status}。",
        "lua_msg_toggle_err": "修改 mods.txt 失败: {err}",
        "lua_msg_del_ok": "已成功删除 {name}。",
        "lua_msg_del_err": "删除失败: {err}",
        "lua_msg_drop_err": "仅支持拖入 .lua 文件！",
        "lua_msg_select": "请先在列表中选择一个模组！",
        
        "setting_theme": "外观设置",
        "setting_theme_label": "主题模式：",
        "setting_path": "游戏路径设置",
        "setting_path_label": "安装目录:",
        "setting_path_tip": "修改路径后，切换到其他页面即可生效。留空则自动读取 Steam 注册表。",
        "setting_browse": "浏览",
        "setting_lang": "语言设置 / Language",
        "setting_lang_label": "界面语言：",
        "msg_path_err": "该目录下未找到 Content 文件夹，请确认是否选对了 EscapeTheBackrooms 目录！",
        "msg_path_ok": "游戏路径已更新，切换到其他页面即可生效。",
        "msg_path_select": "选择 EscapeTheBackrooms 文件夹",
        "msg_path_placeholder": "未检测到游戏路径",
        "theme_system": "跟随系统",
        "theme_light": "浅色模式",
        "theme_dark": "深色模式",
        
        "about_title": "逃离后室 - 工具箱(Ver:1.1)",
        "about_dev": "开发者：SEDET",
        "about_qq": "开发者QQ：248881284",
        "about_group": "交流群：",
    },
    "en": {
        "app_title": "Escape The Backrooms - ToolBox",
        "nav_mod": "Mod Manager",
        "nav_lua": "Lua Mod Manager",
        "nav_ue4ss": "UE4SS Install",
        "nav_about": "About",
        "nav_setting": "Settings",
        
        "btn_install": "Install Mod (.pak)",
        "btn_refresh": "Refresh List",
        "btn_delete": "Delete Mod",
        "table_name": "File Name",
        "table_path": "Location",
        "table_root": "Root",
        "ctx_delete": "Delete Selected Mods",
        "msg_err_path": "Game path or Paks folder not found!",
        "msg_no_mod": "No mods installed currently.",
        "msg_select_mod": "Please select mods to delete first!",
        "msg_del_success": "Successfully deleted {count} mod(s).",
        "msg_del_fail": "Failed to delete {name}: {err}",
        "msg_install_success": "Successfully installed {count} mod(s) to LogicMods.",
        "msg_copy_fail": "Failed to copy {name}: {err}",
        "msg_install_title": "Install Success",
        "msg_delete_title": "Delete Success",
        "msg_drop_err": "Only .pak files are supported!",
        
        "ue4ss_title": "UE4SS Auto Download & Install",
        "btn_fetch": "Fetch Online Versions",
        "btn_dl_install": "Download & Install",
        "btn_dl_save": "Save to Location",
        "msg_fetching": "Connecting to GitHub, please wait...",
        "msg_fetch_success": "Found {count} versions available.",
        "msg_select_ver": "Please fetch and select a version first!",
        "msg_downloading": "Currently downloading, please wait!",
        "msg_installing": "Download complete, extracting to game directory...",
        "msg_install_ok": "UE4SS installed successfully to:\n{path}",
        "msg_install_err": "Extraction error (file in use?): {err}\nTemp file saved at: {path}",
        "msg_save_ok": "File saved to:\n{path}",
        "msg_no_release": "No available releases found",
        "ctx_dl_install": "Download & Install",
        "ctx_dl_save": "Save to Location",
        
        "lua_title": "UE4SS Lua Mod Manager",
        "lua_btn_install": "Install Lua Mod",
        "lua_btn_refresh": "Refresh List",
        "lua_table_name": "Mod Name",
        "lua_table_status": "Status",
        "lua_status_enabled": "Enabled",
        "lua_status_disabled": "Disabled",
        "lua_ctx_toggle": "Toggle Enable/Disable",
        "lua_ctx_delete": "Delete Mod",
        "lua_msg_err_path": "UE4SS Mods directory not found, please confirm UE4SS is installed!",
        "lua_msg_no_mod": "No Lua Mods installed currently.",
        "lua_msg_install_ok": "Lua Mod {name} installed and enabled successfully.",
        "lua_msg_copy_err": "Install failed: {err}",
        "lua_msg_toggle_ok": "Changed {name} status to {status}.",
        "lua_msg_toggle_err": "Failed to modify mods.txt: {err}",
        "lua_msg_del_ok": "Successfully deleted {name}.",
        "lua_msg_del_err": "Delete failed: {err}",
        "lua_msg_drop_err": "Only .lua files are supported!",
        "lua_msg_select": "Please select a mod in the list first!",
        
        "setting_theme": "Appearance",
        "setting_theme_label": "Theme Mode:",
        "setting_path": "Game Path Settings",
        "setting_path_label": "Install Dir:",
        "setting_path_tip": "Changes take effect after switching pages. Leave blank to auto-detect via Steam registry.",
        "setting_browse": "Browse",
        "setting_lang": "Language Settings",
        "setting_lang_label": "UI Language:",
        "msg_path_err": "Content folder not found! Did you select the correct EscapeTheBackrooms directory?",
        "msg_path_ok": "Game path updated, switch pages to apply.",
        "msg_path_select": "Select EscapeTheBackrooms Folder",
        "msg_path_placeholder": "Game path not detected",
        "theme_system": "Follow System",
        "theme_light": "Light Mode",
        "theme_dark": "Dark Mode",
        
        "about_title": "Escape The Backrooms - ToolBox(Ver:1.1)",
        "about_dev": "Developer: SEDT",
        "about_qq": "Developer QQ: 248881284",
        "about_group": "QQ Group: ",
    }
}
CONFIG_FILE = "tool_config.json"
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                c = f.read()
                return json.loads(c) if c.strip() else {}
        except: return {}
    return {}
def save_config(d):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f: json.dump(d, f, ensure_ascii=False, indent=4)
def get_current_lang(): return load_config().get("lang", "en")
def tr(k, **kw):
    t = LANG_DATA.get(get_current_lang(), LANG_DATA["zh"]).get(k, LANG_DATA["zh"].get(k, k))
    return t.format(**kw) if kw else t
def get_game_path():
    p = load_config().get("game_path")
    if p and os.path.exists(p): return p
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
        sp, _ = winreg.QueryValueEx(key, "SteamPath"); winreg.CloseKey(key)
    except: return None
    vf = os.path.join(sp, "steamapps", "libraryfolders.vdf")
    if not os.path.exists(vf): return None
    with open(vf, 'r', encoding='utf-8') as f: vc = f.read()
    for m in re.finditer(r'"\d+"\s*\{(.*?)\}', vc, re.DOTALL):
        if '"1943950"' in m.group(1):
            pm = re.search(r'"path"\s+"(.*?)"', m.group(1))
            if pm: return os.path.join(pm.group(1), "steamapps", "common", "EscapeTheBackrooms")
    return None

class DownloadThread(QThread):
    progress = Signal(int); finished = Signal(bool, str)
    def __init__(self, url, path): super().__init__(); self.url = url; self.path = path
    def run(self):
        try:
            with requests.get(self.url, stream=True, timeout=30, verify=False) as r:
                r.raise_for_status(); ts = int(r.headers.get('content-length', 0)); ds = 0
                with open(self.path, 'wb') as f:
                    for ch in r.iter_content(8192):
                        if ch: f.write(ch); ds += len(ch)
                        if ts > 0: self.progress.emit(int((ds / ts) * 100))
            self.finished.emit(True, self.path)
        except Exception as e: self.finished.emit(False, str(e))

class ModManagerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.setObjectName("ModManagerInterface"); self.parent_window = parent
        self.setup_ui(); self.load_mods(); self.setAcceptDrops(True)
    def setup_ui(self):
        self.lay = QVBoxLayout(self); self.lay.setContentsMargins(36, 20, 36, 20)
        self.bi = PrimaryPushButton(tr("btn_install")); self.br = PushButton(tr("btn_refresh")); self.bd = PushButton(tr("btn_delete"))
        self.bi.setFixedWidth(160); self.br.setFixedWidth(120); self.bd.setFixedWidth(120)
        h = QHBoxLayout(); h.addWidget(self.bi); h.addWidget(self.br); h.addWidget(self.bd); h.addStretch(); self.lay.addLayout(h)
        self.tbl = TableWidget(self); self.tbl.setColumnCount(2); self.tbl.setHorizontalHeaderLabels([tr("table_name"), tr("table_path")])
        self.tbl.verticalHeader().hide(); self.tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive); self.tbl.setColumnWidth(1, 200)
        self.tbl.setEditTriggers(TableWidget.NoEditTriggers); self.tbl.setAlternatingRowColors(True); self.lay.addWidget(self.tbl)
        self.tbl.setContextMenuPolicy(Qt.CustomContextMenu); self.tbl.customContextMenuRequested.connect(self.ctx_menu)
        self.bi.clicked.connect(self.install_mod); self.br.clicked.connect(self.load_mods); self.bd.clicked.connect(self.del_mods)
    def update_language(self):
        self.bi.setText(tr("btn_install")); self.br.setText(tr("btn_refresh")); self.bd.setText(tr("btn_delete"))
        self.tbl.setHorizontalHeaderLabels([tr("table_name"), tr("table_path")]); self.load_mods()
    def get_paks(self):
        bp = get_game_path()
        if not bp: return None
        pp = Path(bp) / "EscapeTheBackrooms" / "Content" / "Paks"
        return pp if pp.exists() else None
    def load_mods(self):
        self.tbl.setRowCount(0); pd = self.get_paks()
        if not pd: return self.msg("Error", tr("msg_err_path"), InfoBarPosition.TOP, True)
        mfs = [f for f in pd.rglob("*.pak") if f.name != "EscapeTheBackrooms-WindowsNoEditor.pak"]
        if not mfs: return self.msg("Info", tr("msg_no_mod"), InfoBarPosition.TOP)
        for r, mf in enumerate(mfs):
            self.tbl.insertRow(r); ni = QTableWidgetItem(str(mf.name)); ni.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            ni.setData(Qt.UserRole, str(mf)); self.tbl.setItem(r, 0, ni)
            ps = str(mf.relative_to(pd).parent); ps = tr("table_root") if ps == "." else ps
            pi = QTableWidgetItem(ps); pi.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter); self.tbl.setItem(r, 1, pi)
    def dragEnterEvent(self, e): e.acceptProposedAction() if e.mimeData().hasUrls() else e.ignore()
    def dropEvent(self, e):
        fs = [u.toLocalFile() for u in e.mimeData().urls() if os.path.isfile(u.toLocalFile()) and u.toLocalFile().lower().endswith('.pak')]
        self.do_install(fs) if fs else self.msg("Error", tr("msg_drop_err"), InfoBarPosition.TOP, True)
    def install_mod(self):
        if not self.get_paks(): return self.msg("Error", tr("msg_err_path"), InfoBarPosition.TOP, True)
        fs, _ = QFileDialog.getOpenFileNames(self, tr("btn_install"), "", "Pak (*.pak)")
        if fs: self.do_install(fs)
    def do_install(self, fs):
        pd = self.get_paks()
        if not pd: return self.msg("Error", tr("msg_err_path"), InfoBarPosition.TOP, True)
        ld = pd / "LogicMods"; ld.mkdir(parents=True, exist_ok=True); sc = 0
        for fp in fs:
            try: shutil.copy2(fp, ld / Path(fp).name); sc += 1
            except Exception as e: self.msg("Error", tr("msg_copy_fail", name=Path(fp).name, err=str(e)), InfoBarPosition.TOP, True)
        if sc > 0: self.msg(tr("msg_install_title"), tr("msg_install_success", count=sc), InfoBarPosition.TOP); self.load_mods()
    def msg(self, t, c, p, err=False):
        (InfoBar.error if err else InfoBar.success)(title=t, content=c, parent=self.parent_window, position=p, duration=5000 if err else 3000)
    def del_mods(self):
        rs = set(i.row() for i in self.tbl.selectedItems())
        if not rs: return self.msg("Info", tr("msg_select_mod"), InfoBarPosition.TOP)
        sc = ec = 0
        for r in rs:
            try:
                fp = self.tbl.item(r, 0).data(Qt.UserRole)
                if os.path.exists(fp): os.remove(fp)
                sc += 1
            except Exception as e: ec += 1; self.msg("Error", tr("msg_del_fail", name=os.path.basename(fp), err=str(e)), InfoBarPosition.TOP, True)
        if sc > 0:
            m = tr("msg_del_success", count=sc)
            if ec > 0: m += f" ({ec} Failed)"
            self.msg(tr("msg_delete_title"), m, InfoBarPosition.TOP); self.load_mods()
    def ctx_menu(self, p):
        if not self.tbl.selectedItems(): return
        mu = RoundMenu(parent=self.tbl); mu.addAction(Action(FluentIcon.DELETE, tr("ctx_delete"), triggered=self.del_mods))
        mu.exec(self.tbl.mapToGlobal(p), MenuAnimationType.DROP_DOWN)

class LuaModManagerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LuaModInterface")
        self.parent_window = parent
        self.setup_ui()
        self.load_mods()
        self.setAcceptDrops(True)

    def setup_ui(self):
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(36, 20, 36, 20)
        
        self.tit = StrongBodyLabel(tr("lua_title"))
        self.lay.addWidget(self.tit)

        h = QHBoxLayout()
        self.bi = PrimaryPushButton(tr("lua_btn_install"))
        self.bi.setFixedWidth(160)
        self.br = PushButton(tr("lua_btn_refresh"))
        self.br.setFixedWidth(120)
        h.addWidget(self.bi); h.addWidget(self.br); h.addStretch()
        self.lay.addLayout(h)

        self.tbl = TableWidget(self)
        self.tbl.setColumnCount(2)
        self.tbl.setHorizontalHeaderLabels([tr("lua_table_name"), tr("lua_table_status")])
        self.tbl.verticalHeader().hide()
        self.tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.tbl.setColumnWidth(1, 120)
        self.tbl.setEditTriggers(TableWidget.NoEditTriggers)
        self.tbl.setAlternatingRowColors(True)
        self.lay.addWidget(self.tbl)

        self.tbl.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tbl.customContextMenuRequested.connect(self.ctx_menu)
        self.bi.clicked.connect(self.install_mod)
        self.br.clicked.connect(self.load_mods)

    def update_language(self):
        self.tit.setText(tr("lua_title"))
        self.bi.setText(tr("lua_btn_install"))
        self.br.setText(tr("lua_btn_refresh"))
        self.tbl.setHorizontalHeaderLabels([tr("lua_table_name"), tr("lua_table_status")])
        self.load_mods()

    def get_dirs(self):
        bp = get_game_path()
        if not bp: return None, None
        mods_dir = Path(bp) / "EscapeTheBackrooms" / "Binaries" / "Win64" / "ue4ss" / "Mods"
        txt_path = mods_dir / "mods.txt"
        return (mods_dir, txt_path) if mods_dir.exists() else (None, None)

    def load_mods(self):
        self.tbl.setRowCount(0)
        mods_dir, txt_path = self.get_dirs()
        if not mods_dir: return self.msg("Error", tr("lua_msg_err_path"), InfoBarPosition.TOP, True)
        
        if not os.path.exists(txt_path):
            return self.msg("Info", tr("lua_msg_no_mod"), InfoBarPosition.TOP)

        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            return self.msg("Error", str(e), InfoBarPosition.TOP, True)

        row = 0
        for line in lines:
            line = line.strip()
            # 匹配格式：xxx : 0 或 xxx : 1
            match = re.match(r'^(.+?)\s*:\s*(0|1)\s*$', line)
            if match:
                name = match.group(1).strip()
                status = int(match.group(2))
                
                self.tbl.insertRow(row)
                
                ni = QTableWidgetItem(name)
                ni.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                ni.setData(Qt.UserRole, name) # 存储纯净的名字用于操作
                self.tbl.setItem(row, 0, ni)

                si = QTableWidgetItem(tr("lua_status_enabled") if status == 1 else tr("lua_status_disabled"))
                si.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                # 设置颜色直观区分
                si.setForeground(QColor(67, 167, 115) if status == 1 else QColor(255, 100, 100))
                self.tbl.setItem(row, 1, si)
                row += 1

        if row == 0: self.msg("Info", tr("lua_msg_no_mod"), InfoBarPosition.TOP)

    def install_mod(self):
        fs, _ = QFileDialog.getOpenFileNames(self, tr("lua_btn_install"), "", "Lua Files (*.lua)")
        if fs: self.do_install(fs)

    def do_install(self, fs):
        mods_dir, txt_path = self.get_dirs()
        if not mods_dir: return self.msg("Error", tr("lua_msg_err_path"), InfoBarPosition.TOP, True)
        
        if not os.path.exists(txt_path):
            open(txt_path, 'w', encoding='utf-8').close()

        for fp in fs:
            try:
                mod_name = Path(fp).stem # 不带后缀的名字
                script_dir = mods_dir / mod_name / "Scripts"
                script_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(fp, script_dir / "main.lua")
                
                # 追加写入 mods.txt
                with open(txt_path, 'a', encoding='utf-8') as f:
                    f.write(f"\n{mod_name} : 1")
                    
                self.msg("Success", tr("lua_msg_install_ok", name=mod_name), InfoBarPosition.TOP)
            except Exception as e:
                self.msg("Error", tr("lua_msg_copy_err", err=str(e)), InfoBarPosition.TOP, True)
        self.load_mods()

    def dragEnterEvent(self, e): e.acceptProposedAction() if e.mimeData().hasUrls() else e.ignore()
    def dropEvent(self, e):
        fs = [u.toLocalFile() for u in e.mimeData().urls() if os.path.isfile(u.toLocalFile()) and u.toLocalFile().lower().endswith('.lua')]
        self.do_install(fs) if fs else self.msg("Error", tr("lua_msg_drop_err"), InfoBarPosition.TOP, True)

    def toggle_mod_status(self):
        item = self.tbl.currentItem()
        if not item: return self.msg("Info", tr("lua_msg_select"), InfoBarPosition.TOP)
        
        row = item.row()
        mod_name = self.tbl.item(row, 0).data(Qt.UserRole)
        current_status_text = self.tbl.item(row, 1).text()
        
        # 判断当前是启用还是禁用
        is_enabled = (current_status_text == tr("lua_status_enabled"))
        new_status = 0 if is_enabled else 1
        new_status_text = tr("lua_status_disabled") if is_enabled else tr("lua_status_enabled")

        mods_dir, txt_path = self.get_dirs()
        if not txt_path or not os.path.exists(txt_path): return

        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            new_lines = []
            for line in lines:
                match = re.match(rf'^({re.escape(mod_name)})\s*:\s*(0|1)\s*$', line.strip())
                if match:
                    new_lines.append(f"{mod_name} : {new_status}\n")
                else:
                    new_lines.append(line)
            
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
                
            self.msg("Success", tr("lua_msg_toggle_ok", name=mod_name, status=new_status_text), InfoBarPosition.TOP)
            self.load_mods()
        except Exception as e:
            self.msg("Error", tr("lua_msg_toggle_err", err=str(e)), InfoBarPosition.TOP, True)

    def delete_mod(self):
        item = self.tbl.currentItem()
        if not item: return self.msg("Info", tr("lua_msg_select"), InfoBarPosition.TOP)
        
        mod_name = self.tbl.item(item.row(), 0).data(Qt.UserRole)
        mods_dir, txt_path = self.get_dirs()

        try:
            # 1. 删除文件夹
            mod_folder = mods_dir / mod_name
            if mod_folder.exists(): shutil.rmtree(mod_folder)
            
            # 2. 删除 txt 对应行
            if os.path.exists(txt_path):
                with open(txt_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.writelines([line for line in lines if not re.match(rf'^{re.escape(mod_name)}\s*:', line.strip())])
                    
            self.msg("Success", tr("lua_msg_del_ok", name=mod_name), InfoBarPosition.TOP)
            self.load_mods()
        except Exception as e:
            self.msg("Error", tr("lua_msg_del_err", err=str(e)), InfoBarPosition.TOP, True)

    def ctx_menu(self, p):
        if not self.tbl.currentItem(): return
        mu = RoundMenu(parent=self.tbl)
        mu.addAction(Action(FluentIcon.SYNC, tr("lua_ctx_toggle"), triggered=self.toggle_mod_status))
        mu.addAction(Action(FluentIcon.DELETE, tr("lua_ctx_delete"), triggered=self.delete_mod))
        mu.exec(self.tbl.mapToGlobal(p), MenuAnimationType.DROP_DOWN)

    def msg(self, t, c, p, err=False):
        (InfoBar.error if err else InfoBar.success)(title=t, content=c, parent=self.parent_window, position=p, duration=5000 if err else 3000)

class UE4SSWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.parent_window = parent; self.setObjectName("UE4SSInterface")
        self.rd = []; self.dt = None; self.setup_ui()
    def setup_ui(self):
        self.lay = QVBoxLayout(self); self.lay.setContentsMargins(36, 20, 36, 20)
        self.tit = StrongBodyLabel(tr("ue4ss_title")); self.lay.addWidget(self.tit)
        h = QHBoxLayout(); self.bf = PrimaryPushButton(tr("btn_fetch")); self.bf.clicked.connect(self.fetch); h.addWidget(self.bf); h.addStretch(); self.lay.addLayout(h)
        self.vl = ListWidget(); self.vl.setAlternatingRowColors(True); self.lay.addWidget(self.vl)
        self.vl.setContextMenuPolicy(Qt.CustomContextMenu); self.vl.customContextMenuRequested.connect(self.vctx)
        h2 = QHBoxLayout(); self.bi = PushButton(FluentIcon.DOWNLOAD, tr("btn_dl_install")); self.bi.clicked.connect(self.dl_install)
        self.bs = PushButton(FluentIcon.FOLDER, tr("btn_dl_save")); self.bs.clicked.connect(self.dl_custom)
        h2.addWidget(self.bi); h2.addWidget(self.bs); self.lay.addLayout(h2)
        self.pb = ProgressBar(); self.pb.setRange(0, 100); self.pb.setValue(0); self.pb.setVisible(False); self.lay.addWidget(self.pb)
    def update_language(self):
        self.tit.setText(tr("ue4ss_title")); self.bf.setText(tr("btn_fetch")); self.bi.setText(tr("btn_dl_install")); self.bs.setText(tr("btn_dl_save"))
    def fetch(self):
        self.bf.setEnabled(False); self.vl.clear(); self.rd = []; self.msg("Info", tr("msg_fetching"), InfoBarPosition.TOP)
        try:
            r = requests.get("https://api.github.com/repos/UE4SS-RE/RE-UE4SS/releases", timeout=10, verify=False); r.raise_for_status()
            for rel in r.json():
                tag = rel.get('tag_name', ''); zu = ""
                for a in rel.get('assets', []):
                    if a['name'].endswith('.zip') and 'source' not in a['name'].lower(): zu = a['browser_download_url']; break
                if zu: self.rd.append({"tag": tag, "url": zu}); self.vl.addItem(f"{tag}  ({zu.split('/')[-1]})")
            if not self.rd: self.vl.addItem(tr("msg_no_release"))
            else: self.msg("Success", tr("msg_fetch_success", count=len(self.rd)), InfoBarPosition.TOP)
        except Exception as e: self.msg("Network Error", str(e), InfoBarPosition.TOP, True)
        finally: self.bf.setEnabled(True)
    def dl_install(self):
        if not self.chk(): return
        bp = get_game_path()
        if not bp: return self.msg("Error", tr("msg_err_path"), InfoBarPosition.TOP, True)
        idir = Path(bp) / "EscapeTheBackrooms" / "Binaries" / "Win64"
        if not idir.exists(): return self.msg("Error", str(idir), InfoBarPosition.TOP, True)
        ud = self.rd[self.vl.currentRow()]; fn = ud['url'].split('/')[-1]
        self.start_dl(ud['url'], os.path.join(os.environ.get('TEMP', '.'), fn), idir)
    def dl_custom(self):
        if not self.chk(): return
        ud = self.rd[self.vl.currentRow()]; fn = ud['url'].split('/')[-1]
        sd = QFileDialog.getExistingDirectory(self, tr("btn_dl_save"))
        if sd: self.start_dl(ud['url'], os.path.join(sd, fn), None)
    def chk(self):
        if self.vl.count() == 0 or self.vl.currentRow() == -1: self.msg("Info", tr("msg_select_ver"), InfoBarPosition.TOP); return False
        if self.dt and self.dt.isRunning(): self.msg("Info", tr("msg_downloading"), InfoBarPosition.TOP); return False
        return True
    def vctx(self, p):
        it = self.vl.itemAt(p)
        if not it: return
        self.vl.setCurrentItem(it); mu = RoundMenu(parent=self.vl)
        mu.addAction(Action(FluentIcon.DOWNLOAD, tr("ctx_dl_install"), triggered=self.dl_install))
        mu.addAction(Action(FluentIcon.FOLDER, tr("ctx_dl_save"), triggered=self.dl_custom))
        mu.exec(self.vl.mapToGlobal(p), MenuAnimationType.DROP_DOWN)
    def start_dl(self, ou, sp, idir):
        self.pb.setVisible(True); self.pb.setValue(0); self.bi.setEnabled(False); self.bs.setEnabled(False)
        self.dt = DownloadThread(f"https://gh-proxy.org/{ou}", sp)
        self.dt.progress.connect(self.pb.setValue); self.dt.finished.connect(lambda s, p: self.dl_done(s, p, idir)); self.dt.start()
    def dl_done(self, s, p, idir):
        self.bi.setEnabled(True); self.bs.setEnabled(True)
        if not s: self.pb.setVisible(False); return self.msg("Error", p, InfoBarPosition.TOP, True)
        if idir:
            self.msg("Info", tr("msg_installing"), InfoBarPosition.TOP); QApplication.processEvents()
            try: shutil.unpack_archive(p, idir); os.remove(p); self.msg("Success", tr("msg_install_ok", path=idir), InfoBarPosition.TOP)
            except Exception as e: self.msg("Error", tr("msg_install_err", err=str(e), path=p), InfoBarPosition.TOP, True)
        else: self.msg("Success", tr("msg_save_ok", path=p), InfoBarPosition.TOP)
        self.pb.setVisible(False)
    def msg(self, t, c, p, err=False):
        (InfoBar.error if err else InfoBar.success)(title=t, content=c, parent=self.parent_window, position=p, duration=5000 if err else 4000)

class AboutWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.parent_window = parent; self.setObjectName("AboutInterface"); self.setup_ui()
    def setup_ui(self):
        self.lay = QVBoxLayout(self); self.lay.setContentsMargins(36, 50, 36, 36)
        self.cd = CardWidget(self); self.cd.setFixedHeight(250); self.cd.setFixedWidth(400)
        cl = QVBoxLayout(self.cd); cl.setContentsMargins(30, 30, 30, 30); cl.setSpacing(15)
        self.tit = TitleLabel(tr("about_title")); self.tit.setAlignment(Qt.AlignCenter); cl.addWidget(self.tit)
        self.dev = BodyLabel(tr("about_dev")); self.dev.setAlignment(Qt.AlignCenter); cl.addWidget(self.dev)
        self.qq = BodyLabel(tr("about_qq")); self.qq.setAlignment(Qt.AlignCenter); cl.addWidget(self.qq)
        self.grp = BodyLabel(); self.grp.setAlignment(Qt.AlignCenter)
        self.gurl = "https://qm.qq.com/cgi-bin/qm/qr?k=qkHKToHIP3AAhcGo4NPqCVV4tBGA_Wct&jump_from=webapi&authKey=Ow+OtF2suJcrafPY0wxAVWHwWLX0BtZIxn2u8a+Z+A6uh/04bSLIfoKspY4j9C1K"
        self.set_grp(); self.grp.setOpenExternalLinks(True); cl.addWidget(self.grp)
        self.lay.addStretch(); self.lay.addWidget(self.cd, alignment=Qt.AlignCenter); self.lay.addStretch()
    def set_grp(self): self.grp.setText(f'{tr("about_group")}<a href="{self.gurl}" style="color:#0078D4;text-decoration:none;">929296000</a>')
    def update_language(self): self.tit.setText(tr("about_title")); self.dev.setText(tr("about_dev")); self.qq.setText(tr("about_qq")); self.set_grp()

class SettingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.parent_window = parent; self.setObjectName("SettingInterface"); self.setup_ui(); self.load_st()
    def setup_ui(self):
        self.lay = QVBoxLayout(self); self.lay.setContentsMargins(36, 30, 36, 36); self.lay.setSpacing(20)
        
        self.tc = CardWidget(self); tl = QVBoxLayout(self.tc); tl.setContentsMargins(20, 15, 20, 15)
        self.tt = StrongBodyLabel(tr("setting_theme")); tl.addWidget(self.tt)
        th = QHBoxLayout(); self.tl = BodyLabel(tr("setting_theme_label")); th.addWidget(self.tl)
        self.tcb = ComboBox(); self.tcb.addItems([tr("theme_system"), tr("theme_light"), tr("theme_dark")])
        self.tcb.setFixedWidth(150); self.tcb.currentIndexChanged.connect(self.chg_theme); th.addWidget(self.tcb); th.addStretch(); tl.addLayout(th)

        self.lc = CardWidget(self); ll = QVBoxLayout(self.lc); ll.setContentsMargins(20, 15, 20, 15)
        self.lt = StrongBodyLabel(tr("setting_lang")); ll.addWidget(self.lt)
        lh = QHBoxLayout(); self.ll = BodyLabel(tr("setting_lang_label")); lh.addWidget(self.ll)
        self.lcb = ComboBox(); self.lcb.addItems(["中文", "English"]); self.lcb.setFixedWidth(150)
        self.lcb.currentIndexChanged.connect(self.chg_lang); lh.addWidget(self.lcb); lh.addStretch(); ll.addLayout(lh)

        self.pc = CardWidget(self); pl = QVBoxLayout(self.pc); pl.setContentsMargins(20, 15, 20, 15)
        self.pt = StrongBodyLabel(tr("setting_path")); pl.addWidget(self.pt)
        ph = QHBoxLayout(); self.pl = BodyLabel(tr("setting_path_label")); ph.addWidget(self.pl)
        self.pi = LineEdit(); self.pi.setReadOnly(True); ph.addWidget(self.pi)
        self.bb = PushButton(FluentIcon.FOLDER, tr("setting_browse")); self.bb.clicked.connect(self.sel_path); ph.addWidget(self.bb); pl.addLayout(ph)
        self.tip = BodyLabel()
        self.update_tip_text(); pl.addWidget(self.tip)

        self.lay.addWidget(self.tc); self.lay.addWidget(self.lc); self.lay.addWidget(self.pc); self.lay.addStretch()
    def update_language(self):
        self.tt.setText(tr("setting_theme")); self.tl.setText(tr("setting_theme_label"))
        self.tcb.blockSignals(True); self.tcb.clear(); self.tcb.addItems([tr("theme_system"), tr("theme_light"), tr("theme_dark")])
        self.tcb.setCurrentIndex(load_config().get("theme", 0)); self.tcb.blockSignals(False)
        self.lt.setText(tr("setting_lang")); self.ll.setText(tr("setting_lang_label"))
        self.pt.setText(tr("setting_path")); self.pl.setText(tr("setting_path_label")); self.bb.setText(tr("setting_browse"))
        self.update_tip_text()
    def update_tip_text(self):
        """使用HTML设置灰色，完美保留Fluent原生漂亮字体"""
        self.tip.setText(f'<span style="color: gray;">{tr("setting_path_tip")}</span>')
    def load_st(self):
        c = load_config(); self.tcb.setCurrentIndex(c.get("theme", 0)); self.lcb.setCurrentIndex(0 if c.get("lang", "en") == "zh" else 1)
        cp = get_game_path(); self.pi.setPlaceholderText(tr("msg_path_placeholder"))
        if cp: self.pi.setText(cp.replace('\\\\', '\\'))
    def chg_theme(self, i):
        if i == 0: setTheme(Theme.AUTO)
        elif i == 1: setTheme(Theme.LIGHT)
        elif i == 2: setTheme(Theme.DARK)
        c = load_config(); c["theme"] = i; save_config(c)
    def chg_lang(self, i):
        c = load_config(); c["lang"] = "zh" if i == 0 else "en"; save_config(c)
        if self.parent_window: self.parent_window.update_all_ui_language()
    def sel_path(self):
        sd = QFileDialog.getExistingDirectory(self, tr("msg_path_select"))
        if not sd: return
        if not os.path.exists(os.path.join(sd, "Content")): return self.msg("Error", tr("msg_path_err"), True)
        cp = sd.replace('\\\\', '\\'); self.pi.setText(cp); c = load_config(); c["game_path"] = cp; save_config(c); self.msg("Success", tr("msg_path_ok"))
    def msg(self, t, c, err=False):
        (InfoBar.error if err else InfoBar.success)(title=t, content=c, parent=self.parent_window, position=InfoBarPosition.TOP, duration=4000 if err else 3000)

class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("app_title"))
        self.resize(800, 600)
        self.setMinimumSize(600, 400)
        self.mod_manager = ModManagerWidget(self)
        self.lua_manager = LuaModManagerWidget(self)
        self.ue4ss_manager = UE4SSWidget(self)
        self.about_page = AboutWidget(self)
        self.setting_page = SettingWidget(self)
        self.addSubInterface(self.mod_manager, FluentIcon.FOLDER, tr("nav_mod"), NavigationItemPosition.SCROLL)
        self.addSubInterface(self.lua_manager, FluentIcon.CODE, tr("nav_lua"), NavigationItemPosition.SCROLL)
        self.addSubInterface(self.ue4ss_manager, FluentIcon.DOWNLOAD, tr("nav_ue4ss"), NavigationItemPosition.SCROLL)
        self.addSubInterface(self.about_page, FluentIcon.INFO, tr("nav_about"), NavigationItemPosition.SCROLL)
        self.addSubInterface(self.setting_page, FluentIcon.SETTING, tr("nav_setting"), NavigationItemPosition.BOTTOM)
        d = QApplication.primaryScreen().availableGeometry()
        self.move((d.width() - self.width()) // 2, (d.height() - self.height()) // 2)
    def update_all_ui_language(self):
        self.setWindowTitle(tr("app_title"))
        if hasattr(self, 'navigationInterface'):
            for n, k in [("ModManagerInterface","nav_mod"),("LuaModInterface","nav_lua"),("UE4SSInterface","nav_ue4ss"),("AboutInterface","nav_about"),("SettingInterface","nav_setting")]:
                b = self.navigationInterface.findChild(NavigationToolButton, n)
                if b: b.setText(tr(k))
        if hasattr(self, 'mod_manager'): self.mod_manager.update_language()
        if hasattr(self, 'lua_manager'): self.lua_manager.update_language()  # 新增
        if hasattr(self, 'ue4ss_manager'): self.ue4ss_manager.update_language()
        if hasattr(self, 'about_page'): self.about_page.update_language()
        if hasattr(self, 'setting_page'): self.setting_page.update_language()

if __name__ == '__main__':
    app = QApplication(sys.argv); app.setStyle("Fusion")
    w = MainWindow(); w.show(); sys.exit(app.exec())
