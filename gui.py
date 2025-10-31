import sys, json
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QHBoxLayout,
    QLineEdit, QListWidget, QMessageBox, QFormLayout, QDialog,
    QTextEdit, QLabel, QComboBox, QInputDialog, QFileDialog, QMenuBar, QMenu, QAbstractItemView
)
from PyQt6.QtCore import QSettings, Qt
from bibliography import Bibliography  # Assumes your Bibliography code is in bibliography.py


class ManualEntryDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Entry" if data else "Add Entry Manually")
        self.data = data or {}
        self.result_data = {}

        layout = QFormLayout()
        self.fields = {}
        for field in ['Authors', 'DOI', 'Year', 'Pages', 'Journal', 'Title', 'Volume', 'Issue', 'Citation position']:
            value = self.data.get(field, "")
            widget = QLineEdit(str(value))
            layout.addRow(field, widget)
            self.fields[field] = widget

        btn_save = QPushButton("Save")
        btn_save.clicked.connect(self.accept)
        layout.addRow(btn_save)
        self.setLayout(layout)

    def accept(self):
        for key, widget in self.fields.items():
            self.result_data[key] = widget.text()
        super().accept()
    
class DoiEntryDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Add Entry by DOI")
        self.data = data or {}
        self.result_data = {}

        layout = QFormLayout()
        self.fields = {}
        for field in ['DOI', 'Citation position']:
            value = self.data.get(field, "")
            widget = QLineEdit(str(value))
            layout.addRow(field, widget)
            self.fields[field] = widget

        btn_save = QPushButton("Save")
        btn_save.clicked.connect(self.accept)
        layout.addRow(btn_save)
        self.setLayout(layout)

    def accept(self):
        for key, widget in self.fields.items():
            self.result_data[key] = widget.text()
        super().accept()

class ReorderableListWidget(QListWidget):
    def __init__(self, parent=None, on_reorder_callback=None):
        super().__init__(parent)
        self.on_reorder_callback = on_reorder_callback
        self.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)

    def dropEvent(self, event):
        super().dropEvent(event)
        if self.on_reorder_callback:
            self.on_reorder_callback()

class BibliographyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bibliography Manager")
        self.resize(900, 600)

        self.settings = QSettings("MyCompany", "BibliographyApp")
        self.restoreGeometry(self.settings.value("geometry", b""))

        # Ask user to choose a bibliography file
        self.bib_path = self.ask_for_file()
        if not self.bib_path:
            QMessageBox.warning(self, "No File Selected", "No file chosen. Exiting.")
            sys.exit(0)

        try:
            self.bib = Bibliography(self.bib_path)
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Could not load bibliography:\n{e}")
            sys.exit(1)

        self.settings.setValue("lastFile", self.bib_path)

        self.build_ui()
        self.refresh_list()

    def ask_for_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Bibliography File", "", "JSON Files (*.json);;All Files (*)"
        )
        if path:
            return path
        create_new = QMessageBox.question(
            self, "Create New", "No file selected. Create a new bibliography?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if create_new == QMessageBox.StandardButton.Yes:
            path, _ = QFileDialog.getSaveFileName(
                self, "Save New Bibliography As", "new_bibliography.json", "JSON Files (*.json)"
            )
            if path:
                with open(path, "w") as f:
                    json.dump({}, f)
                return path
        return None

    def build_ui(self):
        self.layout = QVBoxLayout()

        # Menu bar for opening new files
        menu_bar = QMenuBar()
        file_menu = QMenu("File", self)
        open_action = file_menu.addAction("Open Other Bibliography")
        open_action.triggered.connect(self.open_other_file)
        menu_bar.addMenu(file_menu)
        self.layout.setMenuBar(menu_bar)

        self.list_widget = ReorderableListWidget(on_reorder_callback=self.handle_reorder)
        self.list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.list_widget.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)

        self.layout.addWidget(QLabel("Bibliography Entries:"))
        self.layout.addWidget(self.list_widget)
        self.layout.addWidget(QLabel("Live Citation Preview:"))
        self.layout.addWidget(self.preview)

        controls = QHBoxLayout()
        self.btn_add_doi = QPushButton("Add via DOI")
        self.btn_add_manual = QPushButton("Add Manually")
        self.btn_edit = QPushButton("Edit Entry")
        self.btn_remove = QPushButton("Remove")
        self.btn_save = QPushButton("Save JSON")
        self.refresh_button = QPushButton("Refresh List")
        for btn in [self.btn_add_doi, self.btn_add_manual, self.btn_edit, self.btn_remove, self.btn_save, self.refresh_button]:
            controls.addWidget(btn)

        export_row = QHBoxLayout()
        self.style_combo = QComboBox()
        self.style_combo.addItems(["Chicago", "RSC"])
        self.btn_export = QPushButton("Export to DOCX")
        export_row.addWidget(QLabel("Style:"))
        export_row.addWidget(self.style_combo)
        export_row.addWidget(self.btn_export)

        self.layout.addLayout(controls)
        self.layout.addLayout(export_row)
        self.setLayout(self.layout)

        self.btn_add_doi.clicked.connect(self.add_by_doi)
        self.btn_add_manual.clicked.connect(self.add_manual)
        self.btn_edit.clicked.connect(self.edit_entry)
        self.btn_remove.clicked.connect(self.remove_entry)
        self.btn_save.clicked.connect(self.save_json)
        self.btn_export.clicked.connect(self.export_docx)
        self.refresh_button.clicked.connect(self.refresh_list)
        self.list_widget.currentRowChanged.connect(self.update_preview)

    def open_other_file(self):
        new_path, _ = QFileDialog.getOpenFileName(self, "Open Bibliography File", "", "JSON Files (*.json)")
        if new_path:
            try:
                self.bib = Bibliography(new_path)
                self.bib_path = new_path
                self.settings.setValue("lastFile", new_path)
                self.refresh_list()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not load file:\n{e}")

    def closeEvent(self, event):
        # Save GUI state
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("lastFile", self.bib_path)
        super().closeEvent(event)

    def refresh_list(self):
        self.list_widget.clear()
        for index in sorted(self.bib.bib.keys(), key=int):
            entry = self.bib.bib[index]
            display_text = f"{index}: {entry['Authors']} - {entry['Title']}"
            self.list_widget.addItem(display_text)
        self.update_preview()

    def update_preview(self):
        current = self.list_widget.currentRow()
        if current < 0:
            self.preview.setText("No entry selected.")
            return
        index = sorted(self.bib.bib.keys(), key=int)[current]
        entry = self.bib.bib[index]
        # Live preview (simplified Chicago)
        authors = entry.get("Authors", "")
        title = entry.get("Title", "")
        journal = entry.get("Journal", "")
        year = entry.get("Year", "")
        volume = entry.get("Volume", "")
        issue = entry.get("Issue", "")
        pages = entry.get("Pages", "")
        doi = entry.get("DOI", "")
        preview_text = f"{authors}. \"{title}.\" *{journal}* {year}, {volume}({issue}): {pages}. DOI: {doi}"
        self.preview.setText(preview_text)

    def add_by_doi(self):
        dialog = DoiEntryDialog(self)
        if dialog.exec():
            index = int(dialog.result_data['Citation position']) if dialog.result_data['Citation position'] not in ['', ' ', None] else 99999
            try:
                self.bib.insert_from_doi(dialog.result_data['DOI'], index)
                self.refresh_list()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to fetch DOI:\n{e}")

    def add_manual(self):
        dialog = ManualEntryDialog(self)
        if dialog.exec():
            index = int(dialog.result_data['Citation position']) if dialog.result_data['Citation position'] not in ['', ' ', None] else 99999
            del dialog.result_data['Citation position']
            self.bib.insert(dialog.result_data, index)
            self.refresh_list()

    def edit_entry(self):
        current = self.list_widget.currentRow()
        if current < 0:
            QMessageBox.warning(self, "Select Entry", "Please select an entry to edit.")
            return
        index = sorted(self.bib.bib.keys(), key=int)[current]
        data = self.bib.bib[index]
        dialog = ManualEntryDialog(self, data)
        if dialog.exec():
            self.bib.bib[index] = dialog.result_data
            self.refresh_list()

    def remove_entry(self):
        current = self.list_widget.currentRow()
        if current < 0:
            QMessageBox.warning(self, "Select Entry", "Please select an entry to remove.")
            return
        index = sorted(self.bib.bib.keys(), key=int)[current]
        self.bib.remove(index)
        self.refresh_list()

    def save_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export to json", "bibliography.json", "JSON Files (*.json)")
        if path:
            try:
                self.bib.save_json(filename=path)
                QMessageBox.information(self, "Exported", f"Exported to {path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))

    def export_docx(self):
        style = self.style_combo.currentText()
        path, _ = QFileDialog.getSaveFileName(self, "Export to DOCX", "bibliography.docx", "Word Files (*.docx)")
        if path:
            try:
                self.bib.export_bibliography(style, filename=path)
                QMessageBox.information(self, "Exported", f"Exported to {path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))
    
    def handle_reorder(self):
        # Get new order from QListWidget
        new_order = []
        for i in range(self.list_widget.count()):
            text = self.list_widget.item(i).text()
            index = text.split(":", 1)[0]
            new_order.append(index)

        # Rebuild the bib dict in new order with integer keys starting from 1
        reordered = {}
        for new_idx, old_idx in enumerate(new_order):
            reordered[str(new_idx + 1)] = self.bib.bib[old_idx]

        self.bib.bib = reordered
        self.refresh_list()


def run_gui():
    app = QApplication(sys.argv)
    window = BibliographyApp()
    window.show()
    sys.exit(app.exec())