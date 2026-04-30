import sys
import os
import json
import re
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QPushButton, QLabel, QFileDialog, QTextEdit, 
                            QMessageBox, QProgressBar, QSplitter, QTabWidget,
                            QPlainTextEdit, QCheckBox, QSpinBox, QGroupBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QTextCursor

class StructureParser:
    """Parse text-based hierarchy into structured data"""
    
    @staticmethod
    def parse_text_structure(text):
        """Parse text structure into nested dictionary"""
        lines = text.strip().split('\n')
        structure = {}
        stack = [(structure, -1)]  # (current_dict, indent_level)
        
        for line in lines:
            if not line.strip():
                continue
                
            # Calculate indentation level
            indent = len(line) - len(line.lstrip())
            clean_line = line.strip()
            
            # Remove tree characters and comments
            clean_line = re.sub(r'^[│├└─\s]*', '', clean_line)
            
            # Split name and comment
            if '#' in clean_line:
                name, comment = clean_line.split('#', 1)
                name = name.strip()
                comment = comment.strip()
            else:
                name = clean_line
                comment = ''
            
            if not name:
                continue
                
            # Find the appropriate parent level
            while stack and stack[-1][1] >= indent:
                stack.pop()
            
            current_dict = stack[-1][0]
            
            # Determine if it's a directory or file
            is_directory = name.endswith('/')
            if is_directory:
                name = name[:-1]  # Remove trailing slash
                
            if is_directory:
                # Create directory structure
                if name not in current_dict:
                    current_dict[name] = {'files': [], 'subdirs': {}, 'comments': {}}
                stack.append((current_dict[name]['subdirs'], indent))
                if comment:
                    current_dict[name]['comments']['_dir'] = comment
            else:
                # Add file
                if 'files' not in current_dict:
                    current_dict['files'] = []
                if 'comments' not in current_dict:
                    current_dict['comments'] = {}
                    
                current_dict['files'].append(name)
                if comment:
                    current_dict['comments'][name] = comment
        
        return structure
    
    @staticmethod
    def structure_to_text(structure, indent=0):
        """Convert structured data back to text representation"""
        text = []
        indent_str = "    " * indent
        
        for name, content in structure.items():
            if isinstance(content, dict):
                # Directory
                dir_comment = content.get('comments', {}).get('_dir', '')
                comment_str = f"  # {dir_comment}" if dir_comment else ""
                text.append(f"{indent_str}{name}/{comment_str}")
                
                # Files in this directory
                files = content.get('files', [])
                comments = content.get('comments', {})
                for file in files:
                    file_comment = comments.get(file, '')
                    comment_str = f"  # {file_comment}" if file_comment else ""
                    text.append(f"{indent_str}    {file}{comment_str}")
                
                # Subdirectories
                subdirs = content.get('subdirs', {})
                if subdirs:
                    subdir_text = StructureParser.structure_to_text(subdirs, indent + 1)
                    text.extend(subdir_text)
        
        return text

class FileStructureGenerator(QThread):
    """Thread to handle file structure creation"""
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, base_path, structure, create_files=True, file_template=""):
        super().__init__()
        self.base_path = base_path
        self.structure = structure
        self.create_files = create_files
        self.file_template = file_template
        
    def run(self):
        try:
            total_files = self._count_files(self.structure)
            current_file = 0
            
            current_file = self._create_structure(self.structure, self.base_path, current_file, total_files)
            
            self.finished_signal.emit(True, "File structure created successfully!")
            
        except Exception as e:
            self.finished_signal.emit(False, f"Error: {str(e)}")
    
    def _count_files(self, structure):
        """Count total number of files to create"""
        count = 0
        for key, value in structure.items():
            if isinstance(value, dict):
                if 'files' in value:
                    count += len(value['files'])
                if 'subdirs' in value:
                    count += self._count_files(value['subdirs'])
        return count
    
    def _create_structure(self, structure, base_path, current_file, total_files):
        """Recursively create directory structure and files"""
        for name, content in structure.items():
            current_path = os.path.join(base_path, name)
            
            # Create directory
            os.makedirs(current_path, exist_ok=True)
            self.status_updated.emit(f"Created directory: {current_path}")
            
            if isinstance(content, dict):
                # Create files in this directory
                if 'files' in content and self.create_files:
                    comments = content.get('comments', {})
                    for filename in content['files']:
                        file_path = os.path.join(current_path, filename)
                        with open(file_path, 'w') as f:
                            # Write file template
                            if self.file_template:
                                f.write(self.file_template + '\n')
                            
                            # Write comment if available
                            if filename in comments:
                                f.write(f"# {comments[filename]}\n")
                        
                        current_file += 1
                        progress = int((current_file / total_files) * 100)
                        self.progress_updated.emit(progress)
                        self.status_updated.emit(f"Created file: {file_path}")
                
                # Create subdirectories
                if 'subdirs' in content:
                    current_file = self._create_structure(content['subdirs'], current_path, 
                                                        current_file, total_files)
        
        return current_file

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.selected_path = ""
        self.current_structure = {}
        self.init_ui()
        self.load_default_template()
        
    def init_ui(self):
        self.setWindowTitle("Universal File Structure Generator")
        self.setGeometry(100, 100, 1000, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Title
        title_label = QLabel("Universal File Structure Generator")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Path selection
        path_layout = QHBoxLayout()
        self.path_label = QLabel("No folder selected")
        self.path_label.setStyleSheet("padding: 8px; border: 1px solid #ccc; background: #f5f5f5;")
        path_layout.addWidget(self.path_label)
        
        self.browse_button = QPushButton("Browse Folder")
        self.browse_button.clicked.connect(self.browse_folder)
        self.browse_button.setStyleSheet("padding: 8px; font-weight: bold;")
        path_layout.addWidget(self.browse_button)
        
        layout.addLayout(path_layout)
        
        # Template buttons
        template_layout = QHBoxLayout()
        self.load_template_button = QPushButton("Load Template")
        self.load_template_button.clicked.connect(self.load_template)
        template_layout.addWidget(self.load_template_button)
        
        self.save_template_button = QPushButton("Save Template")
        self.save_template_button.clicked.connect(self.save_template)
        template_layout.addWidget(self.save_template_button)
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_structure)
        template_layout.addWidget(self.clear_button)
        
        layout.addLayout(template_layout)
        
        # Main content area with splitter
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel - Editor
        editor_widget = QWidget()
        editor_layout = QVBoxLayout()
        editor_widget.setLayout(editor_layout)
        
        editor_label = QLabel("Edit Structure (use '/' for directories, add '# comment' for descriptions):")
        editor_label.setFont(QFont("Arial", 12, QFont.Bold))
        editor_layout.addWidget(editor_label)
        
        self.structure_editor = QPlainTextEdit()
        self.structure_editor.setFont(QFont("Consolas", 10))
        self.structure_editor.textChanged.connect(self.update_preview)
        editor_layout.addWidget(self.structure_editor)
        
        splitter.addWidget(editor_widget)
        
        # Right panel - Preview and options
        preview_widget = QWidget()
        preview_layout = QVBoxLayout()
        preview_widget.setLayout(preview_layout)
        
        # Options group
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()
        options_group.setLayout(options_layout)
        
        self.create_files_checkbox = QCheckBox("Create files (not just directories)")
        self.create_files_checkbox.setChecked(True)
        options_layout.addWidget(self.create_files_checkbox)
        
        template_layout = QHBoxLayout()
        template_layout.addWidget(QLabel("File template:"))
        self.file_template_edit = QTextEdit()
        self.file_template_edit.setPlainText("# Generated file")
        self.file_template_edit.setMaximumHeight(60)
        template_layout.addWidget(self.file_template_edit)
        options_layout.addLayout(template_layout)
        
        preview_layout.addWidget(options_group)
        
        # Preview
        preview_label = QLabel("Preview:")
        preview_label.setFont(QFont("Arial", 12, QFont.Bold))
        preview_layout.addWidget(preview_label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setFont(QFont("Consolas", 9))
        preview_layout.addWidget(self.preview_text)
        
        splitter.addWidget(preview_widget)
        splitter.setSizes([500, 500])
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready to create file structure")
        self.status_label.setStyleSheet("padding: 5px; color: #666;")
        layout.addWidget(self.status_label)
        
        # Generate button
        self.generate_button = QPushButton("Generate File Structure")
        self.generate_button.clicked.connect(self.generate_structure)
        self.generate_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.generate_button.setEnabled(False)
        layout.addWidget(self.generate_button)
        
    def load_default_template(self):
        """Load the default hunting club template"""
        default_template = """project_root/  # Main project directory
    main.py  # Application entry point
    README.md  # Project documentation
    requirements.txt  # Python dependencies
    models/  # Data models
        __init__.py
        member.py  # Member data model
        reservation.py  # Reservation data model
        lottery.py  # Lottery system logic
    views/  # User interface
        __init__.py
        main_window.py  # Main application window
        calendar_widget.py  # Custom calendar widget
        dialogs.py  # Various dialog windows
    controllers/  # Business logic
        __init__.py
        app_controller.py  # Main application controller
        lottery_controller.py  # Lottery management
    utils/  # Utility functions
        __init__.py
        data_manager.py  # JSON file operations
        constants.py  # App constants and configuration
    data/  # Data files
        members.json  # Member list
        reservations.json  # Current reservations
        lottery_history.json  # Past lottery records
    tests/  # Test files
        __init__.py
        test_models.py  # Model tests
        test_controllers.py  # Controller tests"""
        
        self.structure_editor.setPlainText(default_template)
        self.update_preview()
    
    def update_preview(self):
        """Update the preview based on current editor content"""
        try:
            text = self.structure_editor.toPlainText()
            self.current_structure = StructureParser.parse_text_structure(text)
            
            # Generate tree preview
            preview = self.generate_tree_preview(self.current_structure)
            self.preview_text.setPlainText(preview)
            
            # Enable generate button if structure is valid and path is selected
            self.generate_button.setEnabled(bool(self.current_structure and self.selected_path))
            
        except Exception as e:
            self.preview_text.setPlainText(f"Error parsing structure: {str(e)}")
            self.generate_button.setEnabled(False)
    
    def generate_tree_preview(self, structure, prefix="", is_last=True):
        """Generate a tree-like preview of the structure"""
        if not structure:
            return "No structure defined"
        
        lines = []
        items = list(structure.items())
        
        for i, (name, content) in enumerate(items):
            is_last_item = i == len(items) - 1
            
            if isinstance(content, dict):
                # Directory
                connector = "└── " if is_last_item else "├── "
                dir_comment = content.get('comments', {}).get('_dir', '')
                comment_str = f"  # {dir_comment}" if dir_comment else ""
                lines.append(f"{prefix}{connector}{name}/{comment_str}")
                
                # Files in this directory
                files = content.get('files', [])
                comments = content.get('comments', {})
                subdirs = content.get('subdirs', {})
                
                extension = "    " if is_last_item else "│   "
                
                for j, file in enumerate(files):
                    is_last_file = j == len(files) - 1 and not subdirs
                    file_connector = "└── " if is_last_file else "├── "
                    file_comment = comments.get(file, '')
                    comment_str = f"  # {file_comment}" if file_comment else ""
                    lines.append(f"{prefix}{extension}{file_connector}{file}{comment_str}")
                
                # Subdirectories
                if subdirs:
                    subdir_preview = self.generate_tree_preview(subdirs, prefix + extension, True)
                    lines.extend(subdir_preview.split('\n')[1:])  # Skip first empty line
        
        return '\n'.join(lines)
    
    def browse_folder(self):
        """Open folder selection dialog"""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.selected_path = folder_path
            self.path_label.setText(f"Selected: {folder_path}")
            self.generate_button.setEnabled(bool(self.current_structure))
            self.status_label.setText("Ready to create file structure")
    
    def load_template(self):
        """Load a template from file"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Template", "", 
                                                  "Text Files (*.txt);;JSON Files (*.json);;All Files (*)")
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    if file_path.endswith('.json'):
                        # Load JSON structure
                        structure = json.load(f)
                        text_lines = StructureParser.structure_to_text(structure)
                        self.structure_editor.setPlainText('\n'.join(text_lines))
                    else:
                        # Load text structure
                        self.structure_editor.setPlainText(f.read())
                        
                self.update_preview()
                self.status_label.setText(f"Template loaded from {file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load template: {str(e)}")
    
    def save_template(self):
        """Save current structure as template"""
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Template", "", 
                                                  "Text Files (*.txt);;JSON Files (*.json);;All Files (*)")
        if file_path:
            try:
                if file_path.endswith('.json'):
                    # Save as JSON
                    with open(file_path, 'w') as f:
                        json.dump(self.current_structure, f, indent=2)
                else:
                    # Save as text
                    with open(file_path, 'w') as f:
                        f.write(self.structure_editor.toPlainText())
                        
                self.status_label.setText(f"Template saved to {file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save template: {str(e)}")
    
    def clear_structure(self):
        """Clear the current structure"""
        self.structure_editor.clear()
        self.preview_text.clear()
        self.current_structure = {}
        self.generate_button.setEnabled(False)
        self.status_label.setText("Structure cleared")
    
    def generate_structure(self):
        """Generate the file structure"""
        if not self.selected_path:
            QMessageBox.warning(self, "Warning", "Please select a folder first!")
            return
        
        if not self.current_structure:
            QMessageBox.warning(self, "Warning", "Please define a structure first!")
            return
        
        # Get the root directory name
        root_name = list(self.current_structure.keys())[0]
        target_path = os.path.join(self.selected_path, root_name)
        
        if os.path.exists(target_path):
            reply = QMessageBox.question(self, "Folder Exists", 
                                       f"The folder '{root_name}' already exists in:\n{self.selected_path}\n\n"
                                       "Do you want to continue? This may overwrite existing files.",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return
        
        # Disable controls and show progress
        self.generate_button.setEnabled(False)
        self.browse_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Start the file generation thread
        create_files = self.create_files_checkbox.isChecked()
        file_template = self.file_template_edit.toPlainText()
        
        self.generator_thread = FileStructureGenerator(
            self.selected_path, self.current_structure, create_files, file_template
        )
        self.generator_thread.progress_updated.connect(self.update_progress)
        self.generator_thread.status_updated.connect(self.update_status)
        self.generator_thread.finished_signal.connect(self.generation_finished)
        self.generator_thread.start()
    
    def update_progress(self, value):
        """Update progress bar"""
        self.progress_bar.setValue(value)
    
    def update_status(self, message):
        """Update status label"""
        self.status_label.setText(message)
    
    def generation_finished(self, success, message):
        """Handle generation completion"""
        self.progress_bar.setVisible(False)
        self.generate_button.setEnabled(True)
        self.browse_button.setEnabled(True)
        
        if success:
            self.status_label.setText("File structure created successfully!")
            QMessageBox.information(self, "Success", message)
        else:
            self.status_label.setText("Error occurred during generation")
            QMessageBox.critical(self, "Error", message)

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()