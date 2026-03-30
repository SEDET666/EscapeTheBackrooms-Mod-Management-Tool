import os
import sys
import shutil
import winreg
import re
import json
from pathlib import Path
from PySide6.QtWidgets import QApplication, QFileDialog, QHeaderView, QWidget, QVBoxLayout, QHBoxLayout, QTableWidgetItem
from PySide6.QtWidgets import QTableWidgetItem
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QFileDialog, QHeaderView
from qfluentwidgets import (ComboBox, Theme, setTheme)
from qfluentwidgets import (FluentWindow, NavigationItemPosition, TableWidget, 
                            PushButton, PrimaryPushButton, InfoBar, InfoBarPosition, FluentIcon, RoundMenu, Action, MenuAnimationType, TitleLabel, BodyLabel, CardWidget, LineEdit)
import requests
import shutil
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from PySide6.QtCore import QThread, Signal
from qfluentwidgets import (ListWidget, ProgressBar, BodyLabel, StrongBodyLabel)


# 工具函数
CONFIG_FILE = "tool_config.json"

def load_config():
    """读取配置文件，如果没有或损坏则返回空字典"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                # 如果文件为空，read() 会返回空字符串，json.loads 会报错
                content = f.read()
                if not content.strip():
                    return {}
                return json.loads(content)
        except json.JSONDecodeError:
            # 如果解析失败（比如文件内容被破坏），也当做空字典处理
            return {}
    return {}

def save_config(data):
    """保存配置到文件"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# ==================== 核心逻辑 ====================

def get_game_path():
    """获取逃离后室的 common/EscapeTheBackrooms 路径"""
    # 优先读取用户在设置里手动配置的路径
    config = load_config()
    custom_path = config.get("game_path")
    if custom_path and os.path.exists(custom_path):
        return custom_path

    # 自动读取注册表
    app_id = "1943950"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
        steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
        winreg.CloseKey(key)
    except FileNotFoundError:
        return None

    vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
    if not os.path.exists(vdf_path):
        return None

    with open(vdf_path, 'r', encoding='utf-8') as f:
        vdf_content = f.read()

    blocks = re.finditer(r'"\d+"\s*\{(.*?)\}', vdf_content, re.DOTALL)
    for block_match in blocks:
        block_text = block_match.group(1)
        if f'"{app_id}"' in block_text:
            path_match = re.search(r'"path"\s+"(.*?)"', block_text)
            if path_match:
                base_path = path_match.group(1)
                # 这里补全后面的路径，保持和手动选择时一致
                return os.path.join(base_path, "steamapps", "common", "EscapeTheBackrooms")
    return None

# ==================== 下载线程类 ====================
class DownloadThread(QThread):
    """后台下载线程，防止下载时界面卡死"""
    progress = Signal(int)       # 下载进度 0-100
    finished = Signal(bool, str) # 完成信号：(是否成功, 文件路径或错误信息)

    def __init__(self, url, save_path):
        super().__init__()
        self.url = url
        self.save_path = save_path

    def run(self):
        try:
            # stream=True 表示流式下载，不一次性占用全部内存
            with requests.get(self.url, stream=True, timeout=30, verify=False) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                downloaded_size = 0
                
                with open(self.save_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            if total_size > 0:
                                self.progress.emit(int((downloaded_size / total_size) * 100))
            
            self.finished.emit(True, self.save_path)
        except Exception as e:
            self.finished.emit(False, str(e))

# ==================== UI 界面 ====================

class ModManagerWidget(QWidget):
    """Mod管理主界面（作为FluentWindow的子页面）"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ModManagerInterface")
        self.parent_window = parent
        self.setup_ui()
        self.load_mods()

    def setup_ui(self):
        # 使用基础的QWidget布局
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(36, 20, 36, 20)

        # 1. 按钮区域
        self.btn_install = PrimaryPushButton("安装 Mod (.pak)")
        self.btn_refresh = PushButton("刷新列表")
        self.btn_delete = PushButton("删除 Mod")
        self.btn_install.setFixedWidth(160)
        self.btn_refresh.setFixedWidth(120)
        self.btn_delete.setFixedWidth(120)
        
        # 按钮水平布局
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.btn_install)
        h_layout.addWidget(self.btn_refresh)
        h_layout.addWidget(self.btn_delete)
        h_layout.addStretch()
        self.layout.addLayout(h_layout)

        # 2. Mod 列表
        self.table = TableWidget(self)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["文件名", "所在路径"])
        
        # 隐藏左侧行号
        self.table.verticalHeader().hide()
        # 设置表头自适应拉伸
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(1, 200)
        # 设置表格不可编辑
        self.table.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        # 启用交替行颜色
        self.table.setAlternatingRowColors(True)

        self.layout.addWidget(self.table)
        # 开启表格右键菜单
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_table_context_menu)
        # 3. 绑定事件
        self.btn_install.clicked.connect(self.install_mod)
        self.btn_refresh.clicked.connect(self.load_mods)
        self.btn_delete.clicked.connect(self.on_btn_delete_clicked)

    def get_paks_dir(self):
        base_path = get_game_path()
        if not base_path:
            return None
        paks_path = Path(base_path) / "EscapeTheBackrooms" / "Content" / "Paks"
        return paks_path if paks_path.exists() else None

    def load_mods(self):
        """扫描并加载所有 Mod"""
        self.table.setRowCount(0)
        paks_dir = self.get_paks_dir()

        if not paks_dir:
            self.show_message("错误", "找不到游戏路径或 Paks 文件夹，请确认游戏是否已安装！", InfoBarPosition.TOP, is_error=True)
            return

        # 递归查找所有 .pak 文件
        exclude_file = "EscapeTheBackrooms-WindowsNoEditor.pak"
        mod_files = [f for f in paks_dir.rglob("*.pak") if f.name != exclude_file]

        if not mod_files:
            self.show_message("提示", "当前没有安装任何 Mod。", InfoBarPosition.TOP)
            return

        # 填充表格
        for row, mod_file in enumerate(mod_files):
            self.table.insertRow(row)
            
            # 文件名
            item_name = QTableWidgetItem(str(mod_file.name))
            item_name.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            item_name.setData(Qt.ItemDataRole.UserRole, str(mod_file))
            self.table.setItem(row, 0, item_name)

            # 相对路径 (例如 "LogicMods" 或 ".")
            rel_path = mod_file.relative_to(paks_dir)
            path_str = str(rel_path.parent)
            if path_str == ".":
                path_str = "根目录"
            
            item_path = QTableWidgetItem(path_str)
            item_path.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 1, item_path)

    def install_mod(self):
        """选择并安装 Mod 到 LogicMods 文件夹"""
        paks_dir = self.get_paks_dir()
        if not paks_dir:
            self.show_message("错误", "找不到游戏路径，无法安装！", InfoBarPosition.TOP, is_error=True)
            return

        # 弹出文件选择框，支持多选
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择要安装的 Mod 文件", "", "Pak 文件"
        )
        if not files:
            return

        # 确定目标文件夹
        logic_mods_dir = paks_dir / "LogicMods"
        
        # 如果不存在则自动创建
        logic_mods_dir.mkdir(parents=True, exist_ok=True)

        success_count = 0
        for file_path in files:
            try:
                dest_file = logic_mods_dir / Path(file_path).name
                # 复制文件并覆盖已存在的同名文件
                shutil.copy2(file_path, dest_file)
                success_count += 1
            except Exception as e:
                self.show_message("复制错误", f"文件 {Path(file_path).name} 复制失败: {str(e)}", InfoBarPosition.TOP, is_error=True)

        if success_count > 0:
            self.show_message("安装成功", f"已成功安装 {success_count} 个 Mod 到 LogicMods 文件夹。", InfoBarPosition.TOP)
            self.load_mods() # 刷新列表

    def show_message(self, title, content, position, is_error=False):
        """封装的提示框显示方法"""
        if is_error:
            InfoBar.error(title=title, content=content, parent=self.parent_window, position=position, duration=5000)
        else:
            InfoBar.success(title=title, content=content, parent=self.parent_window, position=position, duration=3000)

    def delete_selected_mods(self):
        """通用的删除选中 Mod 的逻辑"""
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())
            
        if not selected_rows:
            self.show_message("提示", "请先在列表中选择要删除的 Mod！", InfoBarPosition.TOP)
            return

        success_count = 0
        error_count = 0
        for row in selected_rows:
            # 取出之前隐藏存的完整路径
            item = self.table.item(row, 0)
            full_path = item.data(Qt.ItemDataRole.UserRole)
            
            try:
                if os.path.exists(full_path):
                    os.remove(full_path) # 执行删除
                    success_count += 1
            except Exception as e:
                error_count += 1
                self.show_message("删除失败", f"文件 {os.path.basename(full_path)} 删除失败(可能被占用): {str(e)}", InfoBarPosition.TOP, is_error=True)

        if success_count > 0:
            msg = f"已成功删除 {success_count} 个 Mod。"
            if error_count > 0:
                msg += f" (失败 {error_count} 个)"
            self.show_message("删除成功", msg, InfoBarPosition.TOP)
            self.load_mods() # 删完刷新列表

    def on_btn_delete_clicked(self):
        """绑定给删除按钮的事件"""
        self.delete_selected_mods()

    def show_table_context_menu(self, pos):
        """显示右键菜单"""
        # 如果右键点击的位置没有选中任何行，就不弹菜单
        if not self.table.selectedItems():
            return

        menu = RoundMenu(parent=self.table)
        
        # 添加一个带图标的"删除"动作，触发时调用 delete_selected_mods
        delete_action = Action(FluentIcon.DELETE, '删除选中的 Mod', triggered=self.delete_selected_mods)
        menu.addAction(delete_action)

        # 在鼠标右键点击的位置弹出菜单
        menu.exec(self.table.mapToGlobal(pos), aniType=MenuAnimationType.DROP_DOWN)

class UE4SSWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setObjectName("UE4SSInterface") # 必须设置，不然加不进左侧导航
        
        self.releases_data = [] # 缓存版本数据
        self.download_thread = None
        
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(36, 20, 36, 20)

        # 标题
        self.title = StrongBodyLabel("UE4SS 自动下载与安装")
        self.layout.addWidget(self.title)

        # 1. 操作按钮区
        h_btn_layout = QHBoxLayout()
        self.btn_fetch = PrimaryPushButton("获取在线版本列表")
        self.btn_fetch.clicked.connect(self.fetch_releases)
        h_btn_layout.addWidget(self.btn_fetch)
        h_btn_layout.addStretch()
        self.layout.addLayout(h_btn_layout)

        # 2. 版本列表
        self.version_list = ListWidget()
        self.version_list.setAlternatingRowColors(True)
        self.layout.addWidget(self.version_list)
        self.version_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.version_list.customContextMenuRequested.connect(self.show_version_context_menu)

        # 3. 下载与安装按钮区
        h_dl_layout = QHBoxLayout()
        self.btn_install = PushButton(FluentIcon.DOWNLOAD, "下载并自动安装")
        self.btn_install.clicked.connect(self.download_and_install)
        
        self.btn_save = PushButton(FluentIcon.FOLDER, "下载到指定位置(不安装)")
        self.btn_save.clicked.connect(self.download_to_custom)

        h_dl_layout.addWidget(self.btn_install)
        h_dl_layout.addWidget(self.btn_save)
        self.layout.addLayout(h_dl_layout)

        # 4. 进度条
        self.progress_bar = ProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False) # 默认隐藏
        self.layout.addWidget(self.progress_bar)

    def fetch_releases(self):
        """从 GitHub 获取 Release 列表"""
        self.btn_fetch.setEnabled(False)
        self.version_list.clear()
        self.releases_data = []
        
        self.show_message("提示", "正在连接 GitHub 获取版本列表，请稍候...", InfoBarPosition.TOP)

        try:
            api_url = "https://api.github.com/repos/UE4SS-RE/RE-UE4SS/releases"
            response = requests.get(api_url, timeout=10, verify=False)
            response.raise_for_status()
            releases = response.json()

            for rel in releases:
                tag = rel.get('tag_name', '')
                # 寻找 zip 压缩包资源（排除源码包 Source code）
                assets = rel.get('assets', [])
                zip_url = ""
                for asset in assets:
                    if asset['name'].endswith('.zip') and 'source' not in asset['name'].lower():
                        zip_url = asset['browser_download_url']
                        break
                
                if zip_url:
                    self.releases_data.append({"tag": tag, "url": zip_url})
                    self.version_list.addItem(f"{tag}  ({zip_url.split('/')[-1]})")

            if not self.releases_data:
                self.version_list.addItem("未找到可用的发行版")
            else:
                self.show_message("成功", f"获取到 {len(self.releases_data)} 个可用版本，请选择后操作。", InfoBarPosition.TOP)
                
        except Exception as e:
            self.show_message("网络错误", f"获取版本列表失败: {str(e)}", InfoBarPosition.TOP, is_error=True)
        finally:
            self.btn_fetch.setEnabled(True)

    def download_and_install(self):
        """下载并安装到游戏目录"""
        if not self.check_selection(): return
        
        base_path = get_game_path()
        if not base_path:
            self.show_message("错误", "找不到游戏路径！", InfoBarPosition.TOP, is_error=True)
            return

        # 目标解压目录：Binaries/Win64
        install_dir = Path(base_path) / "EscapeTheBackrooms" / "Binaries" / "Win64"
        if not install_dir.exists():
            self.show_message("错误", f"目标安装路径不存在:\n{install_dir}", InfoBarPosition.TOP, is_error=True)
            return

        url_data = self.releases_data[self.version_list.currentRow()]
        file_name = url_data['url'].split('/')[-1]
        # 暂时下载到系统临时目录
        temp_zip_path = os.path.join(os.environ.get('TEMP', '.'), file_name)
        
        self.start_download(url_data['url'], temp_zip_path, install_dir)

    def download_to_custom(self):
        """下载到用户指定位置"""
        if not self.check_selection(): return
        
        url_data = self.releases_data[self.version_list.currentRow()]
        file_name = url_data['url'].split('/')[-1]
        
        # 弹出文件夹选择框
        save_dir = QFileDialog.getExistingDirectory(self, "选择保存位置")
        if not save_dir: return
        
        save_path = os.path.join(save_dir, file_name)
        self.start_download(url_data['url'], save_path, None) # 传 None 表示不自动解压安装

    def check_selection(self):
        if self.version_list.count() == 0 or self.version_list.currentRow() == -1:
            self.show_message("提示", "请先获取列表并选择一个版本！", InfoBarPosition.TOP)
            return False
        if self.download_thread and self.download_thread.isRunning():
            self.show_message("提示", "正在下载中，请等待完成！", InfoBarPosition.TOP)
            return False
        return True

    def show_version_context_menu(self, pos):
        """显示版本列表的右键菜单"""
        # 获取鼠标右键点击位置对应的列表项
        item = self.version_list.itemAt(pos)
        if not item:
            return # 如果右键点在了空白处，什么都不做
        
        # 关键：自动选中右键点击的这一项
        self.version_list.setCurrentItem(item)

        # 创建 Fluent 风格的右键菜单
        menu = RoundMenu(parent=self.version_list)
        
        # 添加两个动作，直接复用已有的下载方法
        menu.addAction(Action(FluentIcon.DOWNLOAD, '下载并自动安装', triggered=self.download_and_install))
        menu.addAction(Action(FluentIcon.FOLDER, '下载到指定位置', triggered=self.download_to_custom))

        # 在鼠标位置弹出菜单
        menu.exec(self.version_list.mapToGlobal(pos), aniType=MenuAnimationType.DROP_DOWN)

    def start_download(self, original_url, save_path, install_dir):
        """启动下载线程"""
        # 加上加速前缀
        final_url = f"https://gh-proxy.org/{original_url}"
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.btn_install.setEnabled(False)
        self.btn_save.setEnabled(False)

        self.download_thread = DownloadThread(final_url, save_path)
        self.download_thread.progress.connect(self.progress_bar.setValue)
        self.download_thread.finished.connect(lambda success, path: self.on_download_finished(success, path, install_dir))
        self.download_thread.start()

    def on_download_finished(self, success, path, install_dir):
        """下载完成后的回调"""
        self.btn_install.setEnabled(True)
        self.btn_save.setEnabled(True)
        
        if not success:
            self.progress_bar.setVisible(False)
            self.show_message("下载失败", f"错误: {path}", InfoBarPosition.TOP, is_error=True)
            return

        if install_dir:
            # 需要自动安装（解压覆盖）
            self.show_message("安装中", "下载完成，正在解压覆盖到游戏目录，请稍候...", InfoBarPosition.TOP)
            QApplication.processEvents() # 强制刷新界面显示上面这句话
            
            try:
                # 解压并覆盖
                shutil.unpack_archive(path, install_dir)
                os.remove(path) # 解压完删掉临时zip
                self.show_message("安装成功", f"UE4SS 已成功安装到:\n{install_dir}", InfoBarPosition.TOP)
            except Exception as e:
                self.show_message("安装失败", f"解压时出错(可能文件被占用): {str(e)}\n临时文件保留在: {path}", InfoBarPosition.TOP, is_error=True)
        else:
            # 仅保存
            self.show_message("保存成功", f"文件已保存到:\n{path}", InfoBarPosition.TOP)

        self.progress_bar.setVisible(False)

    def show_message(self, title, content, position, is_error=False):
        if is_error:
            InfoBar.error(title=title, content=content, parent=self.parent_window, position=position, duration=5000)
        else:
            InfoBar.success(title=title, content=content, parent=self.parent_window, position=position, duration=4000)

class AboutWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setObjectName("AboutInterface") 
        
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(36, 50, 36, 36)

        # 创建一个卡片容器包裹内容
        self.card = CardWidget(self)
        self.card.setFixedHeight(250)  # 调高一点，容纳更多信息
        self.card.setFixedWidth(400)
        
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(15) # 设置每行信息之间的间距

        # 标题
        self.title = TitleLabel("逃离后室 - 工具箱(Ver:1.0)")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.title)

        # 开发者信息
        self.dev_label = BodyLabel("开发者：SEDET")
        self.dev_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.dev_label)

        # QQ信息
        self.qq_label = BodyLabel("开发者QQ：248881284")
        self.qq_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.qq_label)

        # 交流群信息 (重点在这里：使用 HTML a 标签实现超链接)
        self.group_label = BodyLabel()
        self.group_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 你提供的加群链接
        group_url = "https://qm.qq.com/cgi-bin/qm/qr?k=qkHKToHIP3AAhcGo4NPqCVV4tBGA_Wct&jump_from=webapi&authKey=Ow+OtF2suJcrafPY0wxAVWHwWLX0BtZIxn2u8a+Z+A6uh/04bSLIfoKspY4j9C1K"
        
        # 使用富文本渲染，style 里设置了 Win11 主题蓝色并去掉了下划线
        self.group_label.setText(f'交流群：<a href="{group_url}" style="color: #0078D4; text-decoration: none;">929296000</a>')
        
        # 核心代码：允许点击这个 Label 时自动调用系统默认浏览器打开链接
        self.group_label.setOpenExternalLinks(True) 
        
        card_layout.addWidget(self.group_label)

        # 把卡片放到主布局中，并居中显示
        self.layout.addStretch()
        self.layout.addWidget(self.card, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addStretch()

class SettingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setObjectName("SettingInterface")
        
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(36, 30, 36, 36)
        self.layout.setSpacing(20)

        # 1. 外观设置卡片
        theme_card = CardWidget(self)
        theme_layout = QVBoxLayout(theme_card)
        theme_layout.setContentsMargins(20, 15, 20, 15)
        
        theme_title = StrongBodyLabel("外观设置")
        theme_layout.addWidget(theme_title)
        
        theme_h_layout = QHBoxLayout()
        theme_h_layout.addWidget(BodyLabel("主题模式："))
        
        self.theme_combo = ComboBox()
        self.theme_combo.addItems(["跟随系统", "浅色模式", "深色模式"])
        self.theme_combo.setFixedWidth(150)
        self.theme_combo.currentIndexChanged.connect(self.change_theme)
        
        theme_h_layout.addWidget(self.theme_combo)
        theme_h_layout.addStretch()
        theme_layout.addLayout(theme_h_layout)

        # 2. 游戏路径设置卡片
        path_card = CardWidget(self)
        path_layout = QVBoxLayout(path_card)
        path_layout.setContentsMargins(20, 15, 20, 15)
        
        path_title = StrongBodyLabel("游戏路径设置")
        path_layout.addWidget(path_title)
        
        path_h_layout = QHBoxLayout()
        path_h_layout.addWidget(BodyLabel("安装目录："))
        
        self.path_input = LineEdit()
        self.path_input.setReadOnly(True) # 只能通过按钮选择，不能手动乱敲
        path_h_layout.addWidget(self.path_input)
        
        self.btn_browse = PushButton(FluentIcon.FOLDER, "浏览")
        self.btn_browse.clicked.connect(self.select_path)
        path_h_layout.addWidget(self.btn_browse)
        
        path_layout.addLayout(path_h_layout)
        tip_label = BodyLabel("提示：修改路径后，切换到其他页面即可生效。留空则自动读取 Steam 注册表。")
        tip_label.setStyleSheet("color: gray; font-size: 12px;")
        path_layout.addWidget(tip_label)

        # 把卡片加入主布局
        self.layout.addWidget(theme_card)
        self.layout.addWidget(path_card)
        self.layout.addStretch()

    def load_settings(self):
        """启动时加载配置"""
        config = load_config()
        
        # 加载主题
        theme_mode = config.get("theme", 0) # 默认 0 (跟随系统)
        self.theme_combo.setCurrentIndex(theme_mode)
        
        # 加载路径
        current_path = get_game_path() 
        self.path_input.setPlaceholderText("未检测到游戏路径")
        if current_path:
            # 强制将双反斜杠替换为单反斜杠再显示
            clean_path = current_path.replace('\\\\', '\\')
            self.path_input.setText(clean_path)

    def change_theme(self, index):
        """切换主题"""
        if index == 0:
            setTheme(Theme.AUTO)
        elif index == 1:
            setTheme(Theme.LIGHT)
        elif index == 2:
            setTheme(Theme.DARK)
        
        # 保存选择
        config = load_config()
        config["theme"] = index
        save_config(config)

    def select_path(self):
        """选择游戏目录"""
        selected_dir = QFileDialog.getExistingDirectory(self, "选择 EscapeTheBackrooms 文件夹")
        if not selected_dir:
            return
        
        # 简单校验一下选的对不对（看里面有没有 Content 文件夹）
        if not os.path.exists(os.path.join(selected_dir, "Content")):
            self.show_message("路径错误", "该目录下未找到 Content 文件夹，请确认是否选对了 EscapeTheBackrooms 目录！", is_error=True)
            return

        clean_path = selected_dir.replace('\\\\', '\\')
        self.path_input.setText(clean_path)
        # 保存时也保存干净的路径
        config["game_path"] = clean_path
        
        # 保存选择
        config = load_config()
        config["game_path"] = selected_dir
        save_config(config)
        self.show_message("保存成功", "游戏路径已更新，切换到其他页面即可生效。")

    def show_message(self, title, content, is_error=False):
        if is_error:
            InfoBar.error(title=title, content=content, parent=self.parent_window, position=InfoBarPosition.TOP, duration=4000)
        else:
            InfoBar.success(title=title, content=content, parent=self.parent_window, position=InfoBarPosition.TOP, duration=3000)

class MainWindow(FluentWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("逃离后室 - Mod 管理工具")
        self.resize(800, 600)
        self.setMinimumSize(600, 400)

        # 初始化子页面
        self.mod_manager = ModManagerWidget(self)
        self.ue4ss_manager = UE4SSWidget(self)
        self.about_page = AboutWidget(self)
        self.setting_page = SettingWidget(self)

        # 添加到主区域（SCROLL）
        self.addSubInterface(self.mod_manager, FluentIcon.FOLDER, "Mod 管理", NavigationItemPosition.SCROLL)
        self.addSubInterface(self.ue4ss_manager, FluentIcon.DOWNLOAD, "UE4SS 安装", NavigationItemPosition.SCROLL)
        self.addSubInterface(self.about_page, FluentIcon.INFO, "关于", NavigationItemPosition.SCROLL) # 关于放上面

        # 添加到底部固定区域（BOTTOM）
        self.addSubInterface(
            self.setting_page, 
            FluentIcon.SETTING, # 使用设置齿轮图标
            "设置", 
            NavigationItemPosition.BOTTOM # 设置放最底下
        )

        # 居中显示窗口
        desktop = QApplication.primaryScreen().availableGeometry()
        w, h = self.width(), self.height()
        self.move((desktop.width() - w) // 2, (desktop.height() - h) // 2)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # 适配高DPI缩放
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
