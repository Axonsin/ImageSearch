import sys
import os
import time
import shutil
from datetime import datetime
from pathlib import Path
from PIL import Image
import imagehash
from qtpy import QtWidgets, QtCore, QtGui
import DCCdetect

# 尝试导入Qt Material
try:
    from qt_material import apply_stylesheet
    HAS_QT_MATERIAL = True
except ImportError:
    HAS_QT_MATERIAL = False
    print("提示: 要使用Material Design风格，请安装qt-material: pip install qt-material")

class ImageSimilarityApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.source_image_path = None
        self.search_folders = []  # 修改为列表，存储多个文件夹路径
        self.similarity_results = []
        self.current_sort_mode = 0  # 默认按相似度排序
        
    def initUI(self):
        self.setWindowTitle('图像相似度搜索')
        self.setGeometry(100, 100, 1000, 700)
        
        # 创建菜单栏
        menu_bar = self.menuBar()  # 获取主窗口的菜单栏

        # 创建顶级菜单（如“文件”、“编辑”等）
        file_menu = menu_bar.addMenu("文件")  # 添加“文件”菜单
        edit_menu = menu_bar.addMenu("编辑")  # 添加“编辑”菜单
        help_menu = menu_bar.addMenu("帮助")  # 添加“帮助”菜单

        # 为“文件”菜单添加子菜单项
        open_action = QtGui.QAction("打开", self)
        save_action = QtGui.QAction("保存", self)
        exit_action = QtGui.QAction("退出", self)
        open_unity_action = QtGui.QAction("打开当前Unity项目路径", self)

         # 将子菜单项添加到“文件”菜单中
        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addAction(exit_action)
        file_menu.addAction(open_unity_action)

        # 连接信号与槽（与PyQt5一致）
        exit_action.triggered.connect(self.close)  # 点击“退出”关闭窗口
        open_unity_action.triggered.connect(self.handle_open_unity)



        # 创建中央部件
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        
        # 创建拖放区域
        self.drop_area = DropArea(self)
        self.drop_area.setMinimumHeight(200)
        
        # 创建图像信息显示区域
        self.image_info_frame = QtWidgets.QFrame()
        self.image_info_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.image_info_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.image_info_frame.setVisible(False)
        
        info_layout = QtWidgets.QGridLayout(self.image_info_frame)
        
        # 添加图像信息标签
        self.format_label = QtWidgets.QLabel("格式:")
        self.type_label = QtWidgets.QLabel("类型:")
        self.depth_label = QtWidgets.QLabel("位元深度:")
        self.resolution_label = QtWidgets.QLabel("分辨率:")
        self.path_label = QtWidgets.QLabel("路径:")
        
        self.format_value = QtWidgets.QLabel()
        self.type_value = QtWidgets.QLabel()
        self.depth_value = QtWidgets.QLabel()
        self.resolution_value = QtWidgets.QLabel()
        self.path_value = QtWidgets.QLabel()
        self.path_value.setWordWrap(True)
        
        # 添加到布局
        info_layout.addWidget(self.format_label, 0, 0)
        info_layout.addWidget(self.format_value, 0, 1)
        info_layout.addWidget(self.type_label, 1, 0)
        info_layout.addWidget(self.type_value, 1, 1)
        info_layout.addWidget(self.depth_label, 2, 0)
        info_layout.addWidget(self.depth_value, 2, 1)
        info_layout.addWidget(self.resolution_label, 3, 0)
        info_layout.addWidget(self.resolution_value, 3, 1)
        info_layout.addWidget(self.path_label, 4, 0, QtCore.Qt.AlignTop)
        info_layout.addWidget(self.path_value, 4, 1)
        
        # 多选文件夹选择区域
        folder_layout = QtWidgets.QVBoxLayout()  # 改为垂直布局
        folder_header = QtWidgets.QHBoxLayout()  # 顶部按钮和标签布局

        self.folder_count_label = QtWidgets.QLabel("已选择 0 个搜索文件夹")
        self.add_folder_btn = QtWidgets.QPushButton("添加文件夹")
        self.clear_folders_btn = QtWidgets.QPushButton("清除所有文件夹")

        self.add_folder_btn.clicked.connect(self.add_search_folder)
        self.clear_folders_btn.clicked.connect(self.clear_search_folders)

        folder_header.addWidget(self.folder_count_label, 1)
        folder_header.addWidget(self.add_folder_btn, 0)
        folder_header.addWidget(self.clear_folders_btn, 0)

        # 创建文件夹列表
        self.folders_list = QtWidgets.QListWidget()
        self.folders_list.setMaximumHeight(100)  # 限制高度
        self.folders_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.folders_list.customContextMenuRequested.connect(self.show_folder_context_menu)

        folder_layout.addLayout(folder_header)
        folder_layout.addWidget(self.folders_list)

        # 将修改后的文件夹选择区域添加到主布局
        main_layout.addLayout(folder_layout)
        
        # 创建哈希算法选择下拉框
        hash_layout = QtWidgets.QHBoxLayout()
        hash_layout.addWidget(QtWidgets.QLabel("哈希算法:"))
        self.hash_combo = QtWidgets.QComboBox()
        self.hash_combo.addItems(["pHash (感知哈希)", "aHash (平均哈希)", "dHash (差异哈希)"])
        hash_layout.addWidget(self.hash_combo)
        hash_layout.addStretch(1)
        
        # 创建搜索按钮
        self.search_btn = QtWidgets.QPushButton("开始搜索")
        self.search_btn.clicked.connect(self.start_search)
        self.search_btn.setEnabled(False)
        
        # 创建结果控制面板
        result_control_panel = QtWidgets.QFrame()
        result_control_layout = QtWidgets.QHBoxLayout(result_control_panel)
        
        # 添加排序选择控件
        sort_label = QtWidgets.QLabel("排序方式:")
        sort_label.setFixedWidth(80)
        self.sort_combo = QtWidgets.QComboBox()
        self.sort_combo.addItems([
            "按相似度排序", 
            "按名称排序", 
            "按日期排序", 
            "按图片类型排序", 
            "按分辨率排序（从大到小）",
            "按分辨率排序（从小到大）"
        ])
        self.sort_combo.setEnabled(False)
        
        # 添加应用排序按钮
        self.apply_sort_btn = QtWidgets.QPushButton("应用排序")
        self.apply_sort_btn.setEnabled(False)
        self.apply_sort_btn.clicked.connect(self.apply_sort)
        
        result_control_layout.addWidget(sort_label)
        result_control_layout.addWidget(self.sort_combo)
        result_control_layout.addWidget(self.apply_sort_btn)
        result_control_layout.addStretch(1)
        
        # 创建结果数量标签
        self.result_count_label = QtWidgets.QLabel("")
        
        # 创建结果表格
        self.result_table = QtWidgets.QTableWidget()
        self.result_table.setColumnCount(5)  # 缩略图、名称、类型、分辨率、相似度
        self.result_table.setHorizontalHeaderLabels(["缩略图", "名称", "类型", "分辨率", "相似度"])
        self.result_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.result_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.result_table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        self.result_table.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        self.result_table.horizontalHeader().setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
        self.result_table.verticalHeader().setVisible(False)
        self.result_table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.result_table.setSelectionBehavior(QtWidgets.QTableWidget.SelectRows)
        self.result_table.setSelectionMode(QtWidgets.QTableWidget.ExtendedSelection)
        self.result_table.cellDoubleClicked.connect(self.open_image_from_table)
        
        # 设置表格支持右键菜单
        self.result_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.result_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # 创建文件操作按钮区域
        file_ops_frame = QtWidgets.QFrame()
        file_ops_layout = QtWidgets.QHBoxLayout(file_ops_frame)
        self.delete_btn = QtWidgets.QPushButton("删除选中项")
        self.copy_btn = QtWidgets.QPushButton("复制到...")
        self.rename_btn = QtWidgets.QPushButton("批量重命名...")
        self.open_folder_btn = QtWidgets.QPushButton("在文件管理器中打开")

        # 连接按钮到对应方法
        self.delete_btn.clicked.connect(self.delete_selected)
        self.copy_btn.clicked.connect(self.copy_selected)
        self.rename_btn.clicked.connect(self.rename_selected)
        self.open_folder_btn.clicked.connect(self.open_in_file_manager)

        # 添加按钮到布局
        file_ops_layout.addWidget(self.delete_btn)
        file_ops_layout.addWidget(self.copy_btn)
        file_ops_layout.addWidget(self.rename_btn)
        file_ops_layout.addWidget(self.open_folder_btn)
        file_ops_layout.addStretch(1)
        
        # 创建状态栏
        self.statusBar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusBar)
        
        # 添加到主布局
        main_layout.addWidget(QtWidgets.QLabel("将源图像拖放到下方区域:"))
        main_layout.addWidget(self.drop_area)
        main_layout.addWidget(self.image_info_frame)
        main_layout.addLayout(folder_layout)
        main_layout.addLayout(hash_layout)
        main_layout.addWidget(self.search_btn)
        main_layout.addWidget(result_control_panel)
        main_layout.addWidget(self.result_count_label)
        main_layout.addWidget(QtWidgets.QLabel("搜索结果 (双击打开图像):"))
        main_layout.addWidget(self.result_table)
        main_layout.addWidget(file_ops_frame)
        
    
    #def init_actions(self):
        # 创建并连接菜单项
        #self.open_unity_action = QtGui.QAction("打开当前Unity项目路径", self)
        #self.open_unity_action.triggered.connect(self.handle_open_unity)
        #self.file_menu.addAction(self.open_unity_action)
    
    def add_search_folder(self):
        """添加搜索文件夹"""
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "选择搜索文件夹")
        if folder:
            # 检查是否已经添加过这个文件夹
            if folder in self.search_folders:
                QtWidgets.QMessageBox.information(self, "提示", "此文件夹已添加")
                return
                
            # 添加到列表和UI
            self.search_folders.append(folder)
            self.folders_list.addItem(folder)
            self.folder_count_label.setText(f"已选择 {len(self.search_folders)} 个搜索文件夹")
            self.update_search_button_state()

    def clear_search_folders(self):
        """清除所有搜索文件夹"""
        self.search_folders.clear()
        self.folders_list.clear()
        self.folder_count_label.setText("已选择 0 个搜索文件夹")
        self.update_search_button_state()

    def show_folder_context_menu(self, position):
        """显示文件夹列表的右键菜单"""
        menu = QtWidgets.QMenu()
        current_row = self.folders_list.currentRow()
        
        if current_row >= 0:
            remove_action = menu.addAction("删除此文件夹")
            action = menu.exec_(self.folders_list.mapToGlobal(position))
            
            if action == remove_action:
                # 从数据和UI中移除
                self.search_folders.pop(current_row)
                self.folders_list.takeItem(current_row)
                self.folder_count_label.setText(f"已选择 {len(self.search_folders)} 个搜索文件夹")
                self.update_search_button_state()
    def handle_open_unity(self):
        # 调用独立模块的检测函数
        project_paths, error = DCCdetect.get_unity_project_paths()  # 使用新函数名
        
        if error:
            DCCdetect.show_message_box(self, "错误", "不支持的操作系统", info=False)
            return

        if not project_paths:
            DCCdetect.show_message_box(self, "提示", "未检测到正在运行的Unity项目。")
            return
        
        # 过滤掉不存在的路径
        valid_paths = [path for path in project_paths if Path(path).exists()]
        
        if not valid_paths:
            DCCdetect.show_message_box(self, "错误", "检测到项目路径，但所有路径都不存在。", info=False)
            return
        
        # 只有一个项目时直接询问
        if len(valid_paths) == 1:
            project_path = valid_paths[0]
            reply = QtWidgets.QMessageBox.question(
                self,
                "确认操作",
                f"检测到Unity项目路径：\n{project_path}\n\n是否打开该项目文件夹？",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            
            if reply == QtWidgets.QMessageBox.Yes:
                result = DCCdetect.open_project_folder(project_path)
                if isinstance(result, str):
                    DCCdetect.show_message_box(self, "错误", result, info=False)
                else:
                    DCCdetect.show_message_box(self, "成功", "正在打开项目文件夹...", info=True)
        else:
            # 多个项目时显示选择对话框
            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle("选择Unity项目")
            layout = QtWidgets.QVBoxLayout()
            
            label = QtWidgets.QLabel("检测到多个Unity项目，请选择要打开的项目文件夹：")
            layout.addWidget(label)
            
            list_widget = QtWidgets.QListWidget()
            for path in valid_paths:
                item = QtWidgets.QListWidgetItem(path)
                list_widget.addItem(item)
            list_widget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
            list_widget.setCurrentRow(0)  # 默认选中第一个
            layout.addWidget(list_widget)
            
            buttons = QtWidgets.QDialogButtonBox(
                QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
            )
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            
            dialog.setLayout(layout)
            
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                selected_items = list_widget.selectedItems()
                if selected_items:
                    selected_path = selected_items[0].text()
                    result = DCCdetect.open_project_folder(selected_path)
                    if isinstance(result, str):
                        DCCdetect.show_message_box(self, "错误", result, info=False)
                    else:
                        DCCdetect.show_message_box(self, "成功", "已打开文件夹。", info=True)
    
    def select_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "选择搜索文件夹")
        if folder:
            self.search_folder = folder
            self.folder_path_label.setText(f"搜索文件夹: {folder}")
            self.update_search_button_state()
    
    def set_source_image(self, file_path):
        self.source_image_path = file_path
        self.drop_area.set_image(file_path)
        self.update_image_info(file_path)
        self.update_search_button_state()
    
    def update_image_info(self, file_path):
        try:
            # 获取文件信息
            file_ext = os.path.splitext(file_path)[1].lower()
            
            # 使用PIL获取详细信息
            with Image.open(file_path) as img:
                # 获取文件格式
                format_info = img.format if img.format else "未知"
                
                # 获取分辨率
                width, height = img.size
                resolution = f"{width} × {height} 像素"
                
                # 获取位元深度
                mode = img.mode
                if mode == '1':  # 1-bit pixels, black and white
                    bit_depth = "1-bit"
                elif mode == 'L':  # 8-bit pixels, grayscale
                    bit_depth = "8-bit 灰度"
                elif mode == 'P':  # 8-bit pixels, mapped to any other mode using a color palette
                    bit_depth = "8-bit 调色板"
                elif mode == 'RGB':  # 3x8-bit pixels, true color
                    bit_depth = "24-bit RGB"
                elif mode == 'RGBA':  # 4x8-bit pixels, true color with transparency
                    bit_depth = "32-bit RGBA"
                elif mode == 'CMYK':  # 4x8-bit pixels, color separation
                    bit_depth = "32-bit CMYK"
                elif mode == 'YCbCr':  # 3x8-bit pixels, color video format
                    bit_depth = "24-bit YCbCr"
                elif mode == 'I':  # 32-bit signed integer pixels
                    bit_depth = "32-bit 整数"
                elif mode == 'F':  # 32-bit floating point pixels
                    bit_depth = "32-bit 浮点数"
                elif mode == 'LA':  # 8-bit pixels grayscale with alpha
                    bit_depth = "16-bit 灰度+Alpha"
                elif mode == 'RGBX':  # true color with padding
                    bit_depth = "32-bit RGBX"
                elif mode == 'HSV':  # 3x8-bit pixels, Hue, Saturation, Value color space
                    bit_depth = "24-bit HSV"
                else:
                    bit_depth = f"{mode} 模式"
            
            # 设置信息到标签
            self.format_value.setText(format_info)
            self.type_value.setText(file_ext[1:].upper())
            self.depth_value.setText(bit_depth)
            self.resolution_value.setText(resolution)
            self.path_value.setText(file_path)
            
            # 显示信息框
            self.image_info_frame.setVisible(True)
        
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "警告", f"获取图像信息时出错: {e}")
            self.image_info_frame.setVisible(False)
    
    def update_search_button_state(self):
        self.search_btn.setEnabled(self.source_image_path is not None and 
                                len(self.search_folders) > 0)
    
    def get_selected_hash_algorithm(self):
        selected_index = self.hash_combo.currentIndex()
        if selected_index == 1:
            return imagehash.average_hash
        elif selected_index == 2:
            return imagehash.dhash
        else:  # 默认使用pHash
            return imagehash.phash
            
    def start_search(self):
        if not self.source_image_path or not self.search_folders:
            return
        
        # 清空之前的结果
        self.result_table.setRowCount(0)
        self.similarity_results = []
        self.statusBar.showMessage("正在搜索中...")
        
        # 显示进度对话框
        progress = QtWidgets.QProgressDialog("计算图像相似度...", "取消", 0, 100, self)
        progress.setWindowModality(QtCore.Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        QtWidgets.QApplication.processEvents()
        
        # 获取选择的哈希算法
        hash_algorithm = self.get_selected_hash_algorithm()
        
        # 加载源图像
        try:
            source_hash = self.compute_image_hash(self.source_image_path, hash_algorithm)
            
            # 获取所有文件夹中的图片
            image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']
            image_files = []
            
            # 遍历每个选择的文件夹
            for folder in self.search_folders:
                for ext in image_extensions:
                    image_files.extend(list(Path(folder).glob(f'*{ext}')))
                    image_files.extend(list(Path(folder).glob(f'*{ext.upper()}')))
            
            total_files = len(image_files)
            if total_files == 0:
                QtWidgets.QMessageBox.information(self, "信息", "在选定的文件夹中没有找到图像文件。")
                progress.close()
                return
            
            # 计算每个图像的相似度
            for i, img_path in enumerate(image_files):
                if progress.wasCanceled():
                    break
                
                progress.setValue(int((i / total_files) * 100))
                QtWidgets.QApplication.processEvents()
                
                try:
                    # 获取文件信息
                    file_path = str(img_path)
                    file_name = os.path.basename(file_path)
                    file_ext = os.path.splitext(file_path)[1].lower()
                    file_type = file_ext[1:].upper()
                    
                    # 获取文件修改日期
                    file_mtime = os.path.getmtime(file_path)
                    file_date = datetime.fromtimestamp(file_mtime)
                    
                    # 获取图像分辨率
                    with Image.open(file_path) as img:
                        width, height = img.size
                        resolution = width * height  # 总像素数
                        resolution_str = f"{width} × {height}"
                    
                    # 计算相似度
                    img_hash = self.compute_image_hash(file_path, hash_algorithm)
                    hash_distance = source_hash - img_hash
                    max_distance = len(source_hash.hash) ** 2
                    similarity = 1 - (hash_distance / max_distance)
                    
                    # 存储所有信息
                    image_info = {
                        'path': file_path,
                        'name': file_name,
                        'type': file_type,
                        'date': file_date,
                        'mtime': file_mtime,
                        'resolution': resolution,
                        'resolution_str': resolution_str,
                        'width': width,
                        'height': height,
                        'similarity': similarity
                    }
                    
                    self.similarity_results.append(image_info)
                except Exception as e:
                    print(f"处理图像 {img_path} 时出错: {e}")
            
            # 更新结果数量标签
            self.result_count_label.setText(f"找到 {len(self.similarity_results)} 个结果")
            
            # 启用排序功能
            self.sort_combo.setEnabled(True)
            self.apply_sort_btn.setEnabled(True)
            
            # 默认按相似度排序并显示结果
            self.sort_combo.setCurrentIndex(0)
            self.apply_sort()
            
            progress.setValue(100)
            self.statusBar.showMessage("搜索完成")
            
            # 显示搜索完成的消息
            QtWidgets.QMessageBox.information(self, "搜索完成", 
                                            f"找到 {len(self.similarity_results)} 个结果。")
        
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "错误", f"处理图像时出错: {e}")
            self.statusBar.showMessage("搜索出错")
        finally:
            progress.close()
    
    def apply_sort(self):
        """应用所选的排序方式"""
        if not self.similarity_results:
            return
        
        self.statusBar.showMessage("正在排序...")
        QtWidgets.QApplication.processEvents()
        
        # 获取排序方式
        sort_index = self.sort_combo.currentIndex()
        self.current_sort_mode = sort_index
        
        # 根据选择的方式排序
        if sort_index == 0:  # 按相似度排序
            sorted_results = sorted(self.similarity_results, 
                                   key=lambda x: x['similarity'], reverse=True)
        
        elif sort_index == 1:  # 按名称排序
            sorted_results = sorted(self.similarity_results, 
                                   key=lambda x: x['name'].lower())
        
        elif sort_index == 2:  # 按日期排序
            sorted_results = sorted(self.similarity_results, 
                                   key=lambda x: x['mtime'], reverse=True)
        
        elif sort_index == 3:  # 按图片类型排序
            sorted_results = sorted(self.similarity_results, 
                                   key=lambda x: x['type'])
        
        elif sort_index == 4:  # 按分辨率排序 (从大到小)
            sorted_results = sorted(self.similarity_results, 
                                   key=lambda x: x['resolution'], reverse=True)
        
        elif sort_index == 5:  # 按分辨率排序 (从小到大)
            sorted_results = sorted(self.similarity_results, 
                                   key=lambda x: x['resolution'])
        
        # 显示排序后的结果
        self.populate_result_table(sorted_results)
        
        self.statusBar.showMessage(f"已按{self.sort_combo.currentText()}排序")
    
    def populate_result_table(self, results):
        """填充结果表格"""
        # 清空表格
        self.result_table.setRowCount(0)
        
        # 设置行数
        self.result_table.setRowCount(len(results))
        
        # 填充表格
        for row, result in enumerate(results):
            # 创建缩略图单元格
            thumbnail_cell = QtWidgets.QTableWidgetItem()
            thumbnail_cell.setTextAlignment(QtCore.Qt.AlignCenter)
            
            try:
                # 创建缩略图
                pixmap = QtGui.QPixmap(result['path'])
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(80, 80, QtCore.Qt.KeepAspectRatio, 
                                          QtCore.Qt.SmoothTransformation)
                    thumbnail_cell.setData(QtCore.Qt.DecorationRole, pixmap)
            except Exception as e:
                print(f"创建缩略图时出错: {e}")
            
            # 设置单元格的工具提示为文件路径
            thumbnail_cell.setToolTip(result['path'])
            
            # 创建其他信息单元格
            name_cell = QtWidgets.QTableWidgetItem(result['name'])
            name_cell.setToolTip(result['path'])
            
            type_cell = QtWidgets.QTableWidgetItem(result['type'])
            resolution_cell = QtWidgets.QTableWidgetItem(result['resolution_str'])
            
            # 创建相似度单元格并设置背景颜色
            similarity_value = result['similarity']
            similarity_cell = QtWidgets.QTableWidgetItem(f"{similarity_value:.4f}")
            
            # 根据相似度设置不同的背景颜色
            if similarity_value < 0.5:
                # 红色背景
                similarity_cell.setBackground(QtGui.QColor(255, 150, 150))
            elif similarity_value < 0.8:
                # 黄色背景
                similarity_cell.setBackground(QtGui.QColor(255, 255, 150))
            else:
                # 绿色背景
                similarity_cell.setBackground(QtGui.QColor(150, 255, 150))
            
            # 将单元格添加到表格
            self.result_table.setItem(row, 0, thumbnail_cell)
            self.result_table.setItem(row, 1, name_cell)
            self.result_table.setItem(row, 2, type_cell)
            self.result_table.setItem(row, 3, resolution_cell)
            self.result_table.setItem(row, 4, similarity_cell)
            
            # 设置行高以适应缩略图
            self.result_table.setRowHeight(row, 85)
    
    def compute_image_hash(self, image_path, hash_algorithm):
        # 计算图像哈希
        img = Image.open(image_path)
        # 转换为RGB模式（处理RGBA或其他模式）
        if img.mode != 'RGB':
            img = img.convert('RGB')
        return hash_algorithm(img)
    
    def open_image_from_table(self, row, column):
        """从表格中打开图像"""
        # 获取所选行的第一列（缩略图列）中的工具提示，其中包含文件路径
        item = self.result_table.item(row, 0)
        if item and item.toolTip():
            self.open_image_file(item.toolTip())
    
    def open_image_file(self, file_path):
        """打开图像文件"""
        try:
            # 根据操作系统使用适当的方法打开图像
            if sys.platform.startswith('darwin'):  # macOS
                os.system(f'open "{file_path}"')
            elif sys.platform.startswith('win'):   # Windows
                os.system(f'start "" "{file_path}"')
            else:  # Linux
                os.system(f'xdg-open "{file_path}"')
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "警告", f"无法打开图像: {e}")
    
    def show_context_menu(self, position):
        """显示右键菜单"""
        # 创建右键菜单
        menu = QtWidgets.QMenu()
        
        # 获取选中项
        selected_rows = set(item.row() for item in self.result_table.selectedItems())
        if selected_rows:
            menu.addAction("删除选中项", self.delete_selected)
            menu.addAction("复制到...", self.copy_selected)
            menu.addAction("批量重命名...", self.rename_selected)
            menu.addAction("在文件管理器中打开", self.open_in_file_manager)
        
        # 显示菜单
        menu.exec_(self.result_table.mapToGlobal(position))
    
    def delete_selected(self):
        """删除选中的图像文件"""
        selected_rows = sorted(set(item.row() for item in self.result_table.selectedItems()), reverse=True)
        if not selected_rows:
            return
        
        # 确认对话框
        reply = QtWidgets.QMessageBox.question(
            self, '确认删除', 
            f'确定要删除选中的 {len(selected_rows)} 个文件吗？\n此操作无法撤销！',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            deleted_count = 0
            # 获取要删除的文件路径
            files_to_delete = []
            for row in selected_rows:
                file_path = self.result_table.item(row, 0).toolTip()
                files_to_delete.append(file_path)
            
            # 删除文件并更新数据
            for file_path in files_to_delete:
                try:
                    os.remove(file_path)
                    # 从结果中移除
                    for i, result in enumerate(self.similarity_results[:]):
                        if result['path'] == file_path:
                            self.similarity_results.pop(i)
                            deleted_count += 1
                            break
                except Exception as e:
                    QtWidgets.QMessageBox.warning(self, "删除失败", f"无法删除文件: {file_path}\n错误: {e}")
            
            # 更新UI
            self.apply_sort()
            self.result_count_label.setText(f"找到 {len(self.similarity_results)} 个结果")
            QtWidgets.QMessageBox.information(self, "删除完成", f"成功删除 {deleted_count} 个文件")
    
    def copy_selected(self):
        """复制选中的图像文件到指定文件夹"""
        selected_rows = set(item.row() for item in self.result_table.selectedItems())
        if not selected_rows:
            return
        
        # 选择目标文件夹
        dest_folder = QtWidgets.QFileDialog.getExistingDirectory(self, "选择目标文件夹")
        if not dest_folder:
            return
        
        # 收集要复制的文件
        files_to_copy = []
        for row in selected_rows:
            file_path = self.result_table.item(row, 0).toolTip()
            files_to_copy.append(file_path)
        
        # 显示进度对话框
        progress = QtWidgets.QProgressDialog("正在复制文件...", "取消", 0, len(files_to_copy), self)
        progress.setWindowModality(QtCore.Qt.WindowModal)
        
        # 复制文件
        copied_count = 0
        for i, src_path in enumerate(files_to_copy):
            if progress.wasCanceled():
                break
            
            try:
                file_name = os.path.basename(src_path)
                dest_path = os.path.join(dest_folder, file_name)
                
                # 处理文件名冲突
                counter = 1
                name, ext = os.path.splitext(file_name)
                while os.path.exists(dest_path):
                    dest_path = os.path.join(dest_folder, f"{name}_copy{counter}{ext}")
                    counter += 1
                
                # 复制文件
                shutil.copy2(src_path, dest_path)
                copied_count += 1
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "复制失败", f"无法复制文件: {src_path}\n错误: {e}")
            
            progress.setValue(i + 1)
        
        progress.close()
        QtWidgets.QMessageBox.information(self, "复制完成", f"成功复制 {copied_count} 个文件到 {dest_folder}")
    
    def rename_selected(self):
        """批量重命名选中的图像文件"""
        selected_rows = sorted(set(item.row() for item in self.result_table.selectedItems()))
        if not selected_rows:
            return
        
        # 创建重命名对话框
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("批量重命名")
        dialog.setMinimumWidth(400)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        # 添加说明标签
        layout.addWidget(QtWidgets.QLabel("输入重命名格式："))
        layout.addWidget(QtWidgets.QLabel("{n} - 序号  {old} - 原文件名  {ext} - 扩展名"))
        
        # 添加格式输入框
        format_input = QtWidgets.QLineEdit("image_{n}")
        layout.addWidget(format_input)
        
        # 添加起始编号选择
        start_num_layout = QtWidgets.QHBoxLayout()
        start_num_layout.addWidget(QtWidgets.QLabel("起始编号:"))
        start_num_spin = QtWidgets.QSpinBox()
        start_num_spin.setMinimum(1)
        start_num_spin.setValue(1)
        start_num_layout.addWidget(start_num_spin)
        layout.addLayout(start_num_layout)
        
        # 添加预览区域
        layout.addWidget(QtWidgets.QLabel("预览:"))
        preview_list = QtWidgets.QListWidget()
        layout.addWidget(preview_list)
        
        # 添加按钮
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        # 更新预览函数
        def update_preview():
            preview_list.clear()
            name_format = format_input.text()
            start_idx = start_num_spin.value()
            
            for i, row in enumerate(selected_rows):
                file_path = self.result_table.item(row, 0).toolTip()
                old_name = os.path.basename(file_path)
                name, ext = os.path.splitext(old_name)
                
                # 生成新文件名
                new_name = name_format.replace("{n}", str(start_idx + i))
                new_name = new_name.replace("{old}", name)
                new_name = new_name.replace("{ext}", ext)
                if not new_name.endswith(ext):
                    new_name += ext
                
                preview_list.addItem(f"{old_name} → {new_name}")
        
        # 连接信号
        format_input.textChanged.connect(update_preview)
        start_num_spin.valueChanged.connect(update_preview)
        
        # 初始化预览
        update_preview()
        
        # 显示对话框
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            # 执行重命名
            name_format = format_input.text()
            start_idx = start_num_spin.value()
            renamed_count = 0
            
            for i, row in enumerate(selected_rows):
                file_path = self.result_table.item(row, 0).toolTip()
                folder = os.path.dirname(file_path)
                old_name = os.path.basename(file_path)
                name, ext = os.path.splitext(old_name)
                
                # 生成新文件名
                new_name = name_format.replace("{n}", str(start_idx + i))
                new_name = new_name.replace("{old}", name)
                new_name = new_name.replace("{ext}", ext)
                if not new_name.endswith(ext):
                    new_name += ext
                    
                new_path = os.path.join(folder, new_name)
                
                # 执行重命名
                try:
                    os.rename(file_path, new_path)
                    # 更新数据
                    for result in self.similarity_results:
                        if result['path'] == file_path:
                            result['path'] = new_path
                            result['name'] = new_name
                            renamed_count += 1
                            break
                except Exception as e:
                    QtWidgets.QMessageBox.warning(self, "重命名失败", f"无法重命名文件: {file_path}\n错误: {e}")
            
            # 更新UI
            self.apply_sort()
            QtWidgets.QMessageBox.information(self, "重命名完成", f"成功重命名 {renamed_count} 个文件")
    
    def open_in_file_manager(self):
        """在文件管理器中打开选中图像所在的文件夹"""
        selected_rows = set(item.row() for item in self.result_table.selectedItems())
        if not selected_rows:
            return
        
        # 获取第一个选中行的文件路径
        first_row = min(selected_rows)
        file_path = self.result_table.item(first_row, 0).toolTip()
        folder_path = os.path.dirname(file_path)
        
        # 根据操作系统打开文件夹
        try:
            if sys.platform.startswith('darwin'):  # macOS
                os.system(f'open "{folder_path}"')
            elif sys.platform.startswith('win'):   # Windows
                os.startfile(folder_path)
            else:  # Linux
                os.system(f'xdg-open "{folder_path}"')
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "警告", f"无法打开文件夹: {e}")


class DropArea(QtWidgets.QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setText("拖放图像到这里")
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 5px;
                background-color: #f8f8f8;
            }
        """)
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls and len(urls) > 0:
            file_path = str(urls[0].toLocalFile())
            if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp')):
                self.parent.set_source_image(file_path)
            else:
                QtWidgets.QMessageBox.warning(self.parent, "警告", "请拖放有效的图像文件")
    
    def set_image(self, image_path):
        pixmap = QtGui.QPixmap(image_path)
        if pixmap.isNull():
            self.setText("无法加载图像")
            return
            
        # 保持纵横比缩放图像以适应标签
        scaled_pixmap = pixmap.scaled(self.width() - 10, self.height() - 10, 
                                     QtCore.Qt.KeepAspectRatio, 
                                     QtCore.Qt.SmoothTransformation)
        self.setPixmap(scaled_pixmap)
    
    def resizeEvent(self, event):
        # 当部件大小变化时重新调整图像大小
        if hasattr(self.parent, 'source_image_path') and self.parent.source_image_path and not self.text():
            self.set_image(self.parent.source_image_path)
        super().resizeEvent(event)


def main():
    app = QtWidgets.QApplication(sys.argv)
    
    # 应用Qt Material风格（如果可用）
    # if HAS_QT_MATERIAL:
    #     # 使用蓝色主题
    #     apply_stylesheet(app, theme='light_blue.xml')
    
    window = ImageSimilarityApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()