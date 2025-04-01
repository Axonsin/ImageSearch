import sys
import os
from pathlib import Path
from PIL import Image
import imagehash
from qtpy import QtWidgets, QtCore, QtGui

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
        self.search_folder = None
        self.similarity_results = []
        
    def initUI(self):
        self.setWindowTitle('图像相似度搜索')
        self.setGeometry(100, 100, 900, 700)
        
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
        self.path_label = QtWidgets.QLabel("路径:")
        
        self.format_value = QtWidgets.QLabel()
        self.type_value = QtWidgets.QLabel()
        self.depth_value = QtWidgets.QLabel()
        self.path_value = QtWidgets.QLabel()
        self.path_value.setWordWrap(True)
        
        # 添加到布局
        info_layout.addWidget(self.format_label, 0, 0)
        info_layout.addWidget(self.format_value, 0, 1)
        info_layout.addWidget(self.type_label, 1, 0)
        info_layout.addWidget(self.type_value, 1, 1)
        info_layout.addWidget(self.depth_label, 2, 0)
        info_layout.addWidget(self.depth_value, 2, 1)
        info_layout.addWidget(self.path_label, 3, 0, QtCore.Qt.AlignTop)
        info_layout.addWidget(self.path_value, 3, 1)
        
        # 创建文件夹选择区域
        folder_layout = QtWidgets.QHBoxLayout()
        self.folder_path_label = QtWidgets.QLabel("请选择搜索文件夹")
        self.select_folder_btn = QtWidgets.QPushButton("选择文件夹")
        self.select_folder_btn.clicked.connect(self.select_folder)
        folder_layout.addWidget(self.folder_path_label, 1)
        folder_layout.addWidget(self.select_folder_btn, 0)
        
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
        
        # 创建结果列表
        self.result_list = QtWidgets.QListWidget()
        self.result_list.setIconSize(QtCore.QSize(100, 100))
        self.result_list.itemDoubleClicked.connect(self.open_image)
        
        # 添加到主布局
        main_layout.addWidget(QtWidgets.QLabel("将源图像拖放到下方区域:"))
        main_layout.addWidget(self.drop_area)
        main_layout.addWidget(self.image_info_frame)
        main_layout.addLayout(folder_layout)
        main_layout.addLayout(hash_layout)
        main_layout.addWidget(self.search_btn)
        main_layout.addWidget(QtWidgets.QLabel("搜索结果 (双击打开图像):"))
        main_layout.addWidget(self.result_list)
        
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
            self.path_value.setText(file_path)
            
            # 显示信息框
            self.image_info_frame.setVisible(True)
        
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "警告", f"获取图像信息时出错: {e}")
            self.image_info_frame.setVisible(False)
    
    def update_search_button_state(self):
        self.search_btn.setEnabled(self.source_image_path is not None and 
                                   self.search_folder is not None)
    
    def get_selected_hash_algorithm(self):
        selected_index = self.hash_combo.currentIndex()
        if selected_index == 1:
            return imagehash.average_hash
        elif selected_index == 2:
            return imagehash.dhash
        else:  # 默认使用pHash
            return imagehash.phash
            
    def start_search(self):
        if not self.source_image_path or not self.search_folder:
            return
        
        # 清空之前的结果
        self.result_list.clear()
        self.similarity_results = []
        
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
            
            # 获取文件夹中的所有图片
            image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']
            image_files = []
            
            for ext in image_extensions:
                image_files.extend(list(Path(self.search_folder).glob(f'*{ext}')))
                image_files.extend(list(Path(self.search_folder).glob(f'*{ext.upper()}')))
            
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
                    img_hash = self.compute_image_hash(str(img_path), hash_algorithm)
                    # 计算哈希距离并转换为相似度
                    hash_distance = source_hash - img_hash
                    max_distance = len(source_hash.hash) ** 2
                    similarity = 1 - (hash_distance / max_distance)
                    self.similarity_results.append((str(img_path), similarity))
                except Exception as e:
                    print(f"处理图像 {img_path} 时出错: {e}")
            
            # 按相似度排序
            self.similarity_results.sort(key=lambda x: x[1], reverse=True)
            
            # 显示结果
            for img_path, similarity in self.similarity_results:
                item = QtWidgets.QListWidgetItem()
                item.setText(f"{os.path.basename(img_path)} - 相似度: {similarity:.2f}")
                item.setToolTip(img_path)
                
                # 创建缩略图
                try:
                    pixmap = QtGui.QPixmap(img_path)
                    if not pixmap.isNull():
                        pixmap = pixmap.scaled(100, 100, QtCore.Qt.KeepAspectRatio, 
                                              QtCore.Qt.SmoothTransformation)
                        item.setIcon(QtGui.QIcon(pixmap))
                except Exception as e:
                    print(f"创建缩略图时出错: {e}")
                
                self.result_list.addItem(item)
            
            progress.setValue(100)
            
            # 显示搜索完成的消息
            QtWidgets.QMessageBox.information(self, "搜索完成", 
                                            f"找到 {len(self.similarity_results)} 个结果。")
        
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "错误", f"处理图像时出错: {e}")
        finally:
            progress.close()
    
    def compute_image_hash(self, image_path, hash_algorithm):
        # 计算图像哈希
        img = Image.open(image_path)
        # 转换为RGB模式（处理RGBA或其他模式）
        if img.mode != 'RGB':
            img = img.convert('RGB')
        return hash_algorithm(img)
    
    def open_image(self, item):
        # 打开选中的图像
        if item and item.toolTip():
            try:
                # 根据操作系统使用适当的方法打开图像
                if sys.platform.startswith('darwin'):  # macOS
                    os.system(f'open "{item.toolTip()}"')
                elif sys.platform.startswith('win'):   # Windows
                    os.system(f'start "" "{item.toolTip()}"')
                else:  # Linux
                    os.system(f'xdg-open "{item.toolTip()}"')
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "警告", f"无法打开图像: {e}")


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
    if HAS_QT_MATERIAL:
        # 使用蓝色主题
        apply_stylesheet(app, theme='light_blue.xml')
    
    window = ImageSimilarityApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()