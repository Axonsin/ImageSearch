# search_history.py - 图像搜索历史记录管理模块
import os
import json
import time
from datetime import datetime
from qtpy import QtWidgets, QtGui, QtCore

class SearchHistoryManager:
    """图像搜索历史记录管理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window  # 主窗口引用
        self.history_list = []  # 历史记录列表
        self.max_history_items = 20  # 最大历史记录数量
        self.history_file = "image_similarity_history.json"
        self.history_menu_actions = []  # 历史记录菜单项

        # 初始化时加载历史记录
        self.load_history()
        
    def add_history_item(self, source_image, search_folders, hash_method, results_count, filter_settings=None):
        """添加新的历史记录"""
        if not source_image or not search_folders:
            return
        
        # 创建历史记录条目
        history_item = {
            'source_image': source_image,
            'search_folders': search_folders.copy() if isinstance(search_folders, list) else [search_folders],
            'timestamp': time.time(),
            'hash_method': hash_method,
            'result_count': results_count,
            'filter_settings': filter_settings or {}  # 添加筛选设置
        }
        
        # 检查是否与最近的历史记录相同
        if self.history_list and self._is_same_history(self.history_list[0], history_item):
            # 只更新时间戳和结果数量
            self.history_list[0]['timestamp'] = history_item['timestamp']
            self.history_list[0]['result_count'] = history_item['result_count']
            self.history_list[0]['filter_settings'] = history_item['filter_settings']
        else:
            # 添加新的历史记录
            self.history_list.insert(0, history_item)
            
            # 限制历史记录数量
            if len(self.history_list) > self.max_history_items:
                self.history_list.pop()
        
        # 保存历史记录
        self.save_history()
        
    def _is_same_history(self, history1, history2):
        """检查两个历史记录是否相同"""
        folders1 = set(history1['search_folders'])
        folders2 = set(history2['search_folders'])
        
        return (history1['source_image'] == history2['source_image'] and 
                folders1 == folders2 and
                history1['hash_method'] == history2['hash_method'])
    
    def save_history(self):
        """保存历史记录到文件"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history_list, f, ensure_ascii=False)
        except Exception as e:
            print(f"保存历史记录失败: {e}")
    
    def load_history(self):
        """从文件加载历史记录"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history_list = json.load(f)
        except Exception as e:
            print(f"加载历史记录失败: {e}")
            self.history_list = []
    
    def clear_history(self):
        """清除所有历史记录"""
        reply = QtWidgets.QMessageBox.question(
            self.main_window, '确认操作', 
            '确定要清除所有历史记录吗？',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            self.history_list = []
            self.save_history()
            QtWidgets.QMessageBox.information(self.main_window, "操作完成", "历史记录已清除")
            return True
        return False
    
    def create_history_menu(self, menu_bar):
        """创建历史记录菜单"""
        # 创建历史记录菜单
        history_menu = menu_bar.addMenu("历史记录")
        
        # 添加清除历史记录选项
        clear_history_action = QtGui.QAction("清除所有历史记录", self.main_window)
        clear_history_action.triggered.connect(self.on_clear_history)
        history_menu.addAction(clear_history_action)
        history_menu.addSeparator()
        
        # 更新历史记录菜单项
        self.update_history_menu(history_menu)
        
        return history_menu
    
    def update_history_menu(self, menu):
        """更新历史记录菜单项"""
        # 清除现有的历史菜单项
        for action in self.history_menu_actions:
            menu.removeAction(action)
        self.history_menu_actions.clear()
        
        # 如果没有历史记录，添加提示
        if not self.history_list:
            empty_action = QtGui.QAction("暂无历史记录", self.main_window)
            empty_action.setEnabled(False)
            menu.addAction(empty_action)
            self.history_menu_actions.append(empty_action)
            return
        
        # 添加历史记录菜单项
        for i, history in enumerate(self.history_list):
            # 格式化时间
            timestamp = datetime.fromtimestamp(history['timestamp'])
            time_str = timestamp.strftime("%Y-%m-%d %H:%M")
            
            # 创建菜单项文本
            source_name = os.path.basename(history['source_image'])
            folders_count = len(history['search_folders'])
            results_count = history.get('result_count', 0)
            
            # 创建菜单项
            action_text = f"{time_str} - {source_name} (搜索{folders_count}个文件夹, {results_count}个结果)"
            action = QtGui.QAction(action_text, self.main_window)
            
            # 使用闭包确保正确的索引值传递给槽函数
            def create_callback(idx):
                return lambda: self.on_history_selected(idx)
            
            action.triggered.connect(create_callback(i))
            
            menu.addAction(action)
            self.history_menu_actions.append(action)
    
    def on_clear_history(self):
        """清除历史记录处理函数"""
        if self.clear_history():
            # 找到历史记录菜单并更新
            menu = None
            for action in self.main_window.menuBar().actions():
                if action.text() == "历史记录":
                    menu = action.menu()
                    break
            
            if menu:
                self.update_history_menu(menu)
    
    def on_history_selected(self, history_index):
        """处理历史记录选择"""
        if history_index < 0 or history_index >= len(self.history_list):
            return
        
        history = self.history_list[history_index]
        
        # 检查源图像文件是否存在
        if not os.path.exists(history['source_image']):
            QtWidgets.QMessageBox.warning(
                self.main_window, "警告", 
                f"源图像文件不存在: {history['source_image']}"
            )
            return
        
        # 检查搜索文件夹是否存在
        valid_folders = []
        for folder in history['search_folders']:
            if os.path.exists(folder) and os.path.isdir(folder):
                valid_folders.append(folder)
        
        if not valid_folders:
            QtWidgets.QMessageBox.warning(
                self.main_window, "警告", 
                "所有搜索文件夹均不存在，无法恢复此历史记录"
            )
            return
        
        # 询问用户是否要加载历史记录
        reply = QtWidgets.QMessageBox.question(
            self.main_window, '确认操作', 
            f'是否加载此历史记录并设置对应的源图像和搜索文件夹？\n\n源图像: {os.path.basename(history["source_image"])}\n搜索文件夹: {len(valid_folders)}个',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.Yes
        )
        
        if reply != QtWidgets.QMessageBox.Yes:
            return
        
        # 通知主窗口恢复历史记录状态
        self.restore_history_state(history, valid_folders)
    
    def restore_history_state(self, history, valid_folders):
        """恢复历史记录状态"""
        # 设置源图像
        self.set_source_image(history['source_image'])
        
        # 清除并设置搜索文件夹
        self.search_folders = valid_folders
        self.folders_list.clear()
        for folder in valid_folders:
            self.folders_list.addItem(folder)
        self.folder_count_label.setText(f"已选择 {len(valid_folders)} 个搜索文件夹")
        
        # 设置哈希算法
        hash_method = history.get('hash_method', 0)
        self.hash_combo.setCurrentIndex(hash_method)
        
        # 恢复筛选设置
        filter_settings = history.get('filter_settings', {})
        if filter_settings:
            self.filter_checkbox.setChecked(filter_settings.get('filter_enabled', False))
            self.min_similarity.setValue(filter_settings.get('min_similarity', 0.5))
            self.max_similarity.setValue(filter_settings.get('max_similarity', 1.0))
        
        # 更新搜索按钮状态
        self.update_search_button_state()
        
        # 询问是否立即执行搜索
        reply = QtWidgets.QMessageBox.question(
            self, '确认操作', 
            '是否立即执行搜索？',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.Yes
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            self.start_search()