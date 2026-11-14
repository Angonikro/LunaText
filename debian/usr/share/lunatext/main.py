#!/usr/bin/env python3
"""LunaText 0.1.11 - neu aufgebauter Qt6-Texteditor."""
import os, re, sys, json
from pathlib import Path
from PySide6.QtCore import Qt, QSettings, QRegularExpression
from PySide6.QtGui import (QAction, QColor, QFont, QKeySequence, QPainter,
    QTextCharFormat, QSyntaxHighlighter, QTextFormat, QTextCursor, QPalette)
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import (QApplication, QMainWindow, QPlainTextEdit,
    QFileDialog, QMessageBox, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QMenu, QStatusBar, QTextEdit, QToolBar,
    QDialog, QCheckBox, QDialogButtonBox, QColorDialog, QSpinBox, QFormLayout,
    QComboBox, QToolButton)

VERSION = "0.1.11"
TEXT = {
"de": {
"file":"Datei","new":"Neu","open":"Öffnen…","save":"Speichern","saveas":"Speichern unter…","close":"Tab schließen","quit":"Beenden",
"edit":"Bearbeiten","undo":"Rückgängig","redo":"Wiederholen","cut":"Ausschneiden","copy":"Kopieren","paste":"Einfügen","select":"Alles auswählen","find":"Suchen","replace":"Ersetzen",
"view":"Ansicht","toolbar":"Werkzeugleiste","statusbar":"Statusleiste","settings":"Einstellungen","language":"Sprache","german":"Deutsch","english":"Englisch",
"light":"Helles Theme","dark":"Dunkles Theme","settings_title":"Einstellungen","remember":"Fenstergröße merken","font_size":"Schriftgröße","font_color":"Schriftfarbe","choose":"Farbe wählen…",
"help":"Hilfe","about":"Über LunaText","untitled":"Unbenannt","saveprompt":"Änderungen an „{name}“ speichern?","save_title":"Ungespeicherte Änderungen","error":"Fehler",
"open_error":"Datei konnte nicht geöffnet werden:\n{err}","save_error":"Datei konnte nicht gespeichert werden:\n{err}","textfiles":"Textdateien (*.txt)","allfiles":"Alle Dateien (*)",
"line":"Zeile","column":"Spalte","file_size":"Dateigröße","encoding":"UTF-8","find_hint":"Suchen…","replace_hint":"Ersetzen durch…","next":"Weiter","close_find":"Schließen","not_found":"Text nicht gefunden.",
"about_text":"LunaText 0.1.11\nGoldisoft 2026\nQt6-Texteditor"
},
"en": {
"file":"File","new":"New","open":"Open…","save":"Save","saveas":"Save As…","close":"Close Tab","quit":"Quit",
"edit":"Edit","undo":"Undo","redo":"Redo","cut":"Cut","copy":"Copy","paste":"Paste","select":"Select All","find":"Find","replace":"Replace",
"view":"View","toolbar":"Toolbar","statusbar":"Status bar","settings":"Settings","language":"Language","german":"German","english":"English",
"light":"Light theme","dark":"Dark theme","settings_title":"Settings","remember":"Remember window size","font_size":"Font size","font_color":"Font color","choose":"Choose color…",
"help":"Help","about":"About LunaText","untitled":"Untitled","saveprompt":"Save changes to “{name}”?","save_title":"Unsaved changes","error":"Error",
"open_error":"Could not open file:\n{err}","save_error":"Could not save file:\n{err}","textfiles":"Text files (*.txt)","allfiles":"All files (*)",
"line":"Line","column":"Column","file_size":"File size","encoding":"UTF-8","find_hint":"Find…","replace_hint":"Replace with…","next":"Next","close_find":"Close","not_found":"Text not found.",
"about_text":"LunaText 0.1.11\nGoldisoft 2026\nQt6 text editor"
}}

class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        def style(color, bold=False, italic=False):
            f=QTextCharFormat(); f.setForeground(QColor(color))
            if bold: f.setFontWeight(QFont.Weight.Bold)
            if italic: f.setFontItalic(True)
            return f
        self.rules=[
            (QRegularExpression(r'"[^"\\]*(?:\\.[^"\\]*)*"'),style("#a8c7fa")),
            (QRegularExpression(r"'[^'\\]*(?:\\.[^'\\]*)*'"),style("#a8c7fa")),
            (QRegularExpression(r'\b(class|def|return|if|else|elif|for|while|in|import|from|as|try|except|finally|with|pass|break|continue|yield|lambda|True|False|None)\b'),style("#8ab4f8",True)),
            (QRegularExpression(r'\b[0-9]+(?:\.[0-9]+)?\b'),style("#c6a0f6")),
            (QRegularExpression(r'#[^\n]*'),style("#7f929f",False,True)),
            (QRegularExpression(r'\b(self|super)\b'),style("#f2a65a"))]
    def highlightBlock(self,text):
        for rx,fmt in self.rules:
            it=rx.globalMatch(text)
            while it.hasNext():
                m=it.next(); self.setFormat(m.capturedStart(),m.capturedLength(),fmt)

class Gutter(QWidget):
    def __init__(self, editor): super().__init__(editor); self.editor=editor
    def sizeHint(self): return self.editor.gutter_width(),0
    def paintEvent(self,event): self.editor.paint_gutter(event)

class Editor(QPlainTextEdit):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.theme="dark"; self.gutter=Gutter(self)
        self.blockCountChanged.connect(self.update_gutter_width)
        self.updateRequest.connect(self.update_gutter)
        self.cursorPositionChanged.connect(self.highlight_line)
        self.highlighter=PythonHighlighter(self.document())
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ")*4)
        self.set_editor_style("dark",10,"#ffffff")
        self.update_gutter_width(0)
    def set_editor_style(self,theme,size,color):
        self.theme=theme; bg="#ffffff" if theme=="light" else "#20252b"
        font=QFont("DejaVu Sans Mono",size)
        self.setFont(font)
        self.document().setDefaultFont(font)
        # Explicitly style both the editor and its viewport. The parent
        # window stylesheet must never decide the document text color.
        self.setStyleSheet(
            f"QPlainTextEdit{{background-color:{bg};color:{color};border:0;"
            f"padding:8px;selection-background-color:#287fc4;"
            f"font-family:'DejaVu Sans Mono',monospace;font-size:{size}pt;}}"
        )
        self.viewport().setStyleSheet(f"background-color:{bg};color:{color};")
        pal=self.palette()
        pal.setColor(QPalette.ColorRole.Base,QColor(bg))
        pal.setColor(QPalette.ColorRole.Text,QColor(color))
        pal.setColor(QPalette.ColorRole.WindowText,QColor(color))
        pal.setColor(QPalette.ColorRole.Highlight,QColor("#287fc4"))
        pal.setColor(QPalette.ColorRole.HighlightedText,QColor("#ffffff"))
        self.setPalette(pal)
        self.viewport().setPalette(pal)
        self.viewport().setAutoFillBackground(True)
        self.document().setDefaultFont(font)
        # Force the foreground into the document's character format too.
        # QPlainTextEdit palette/style alone can be ignored by existing
        # QTextDocument character formats on some Qt platform themes.
        default_format=QTextCharFormat()
        default_format.setForeground(QColor(color))
        default_format.setFont(font)
        self.document().setDefaultFont(font)
        cursor=QTextCursor(self.document())
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.setCharFormat(default_format)
        self.setCurrentCharFormat(default_format)
        self.highlight_line()
        self.gutter.update()
    def gutter_width(self): return self.fontMetrics().horizontalAdvance("9")*max(2,len(str(max(1,self.blockCount()))))+18
    def update_gutter_width(self,_): self.setViewportMargins(self.gutter_width(),0,0,0)
    def update_gutter(self,rect,dy):
        if dy: self.gutter.scroll(0,dy)
        else: self.gutter.update(0,rect.y(),self.gutter.width(),rect.height())
        if rect.contains(self.viewport().rect()): self.update_gutter_width(0)
    def resizeEvent(self,event):
        super().resizeEvent(event); r=self.contentsRect(); self.gutter.setGeometry(r.left(),r.top(),self.gutter_width(),r.height())
    def paint_gutter(self,event):
        p=QPainter(self.gutter); light=self.theme=="light"
        p.fillRect(event.rect(),QColor("#e8eef4" if light else "#252c34"))
        p.setPen(QColor("#526579" if light else "#8fa3b8"))
        block=self.firstVisibleBlock(); number=block.blockNumber()
        top=int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        while block.isValid() and top<=event.rect().bottom():
            bottom=top+int(self.blockBoundingRect(block).height())
            if block.isVisible() and bottom>=event.rect().top():
                p.drawText(0,top,self.gutter.width()-7,self.fontMetrics().height(),Qt.AlignmentFlag.AlignRight,str(number+1))
            block=block.next(); top=bottom; number+=1
    def highlight_line(self):
        sel=QTextEdit.ExtraSelection(); sel.format.setBackground(QColor("#eaf3fb" if self.theme=="light" else "#2b3540"))
        sel.format.setProperty(QTextFormat.Property.FullWidthSelection,True); sel.cursor=self.textCursor(); sel.cursor.clearSelection()
        self.setExtraSelections([sel])
    def keyPressEvent(self,event):
        if event.key() in (Qt.Key.Key_Return,Qt.Key.Key_Enter):
            indent=re.match(r"[ \t]*",self.textCursor().block().text()).group(0)
            super().keyPressEvent(event)
            if indent:self.insertPlainText(indent)
        else: super().keyPressEvent(event)

class SettingsDialog(QDialog):
    """Eigenständiger Dialog; alle Beschriftungen sind explizite QLabel."""
    def __init__(self,parent,lang,theme,settings):
        super().__init__(parent); self.lang=lang; self.settings=settings
        t=lambda k:TEXT[lang][k]
        self.setWindowTitle(t("settings_title")); self.setMinimumWidth(390)
        light=theme=="light"
        bg,fg,field,border=("#f2f5f8","#243447","#ffffff","#9bbbd5") if light else ("#20252b","#e5e9ef","#151c24","#176da8")
        self.setStyleSheet(f"""
        QDialog{{background:{bg};color:{fg};}}
        QLabel,QCheckBox{{color:{fg};background:transparent;}}
        QSpinBox{{background:{field};color:{fg};border:1px solid {border};padding:6px;}}
        QPushButton{{background:{'#d6e9f7' if light else '#17466a'};color:{'#173d5c' if light else '#f3f8ff'};border:1px solid {border};padding:7px 12px;}}
        """)
        outer=QVBoxLayout(self); form=QFormLayout(); form.setVerticalSpacing(14); form.setHorizontalSpacing(16)
        self.remember=QCheckBox(t("remember")); self.remember.setChecked(settings.value("remember_window_size",True,type=bool))
        form.addRow(self.remember)
        self.size=QSpinBox(); self.size.setRange(7,36); self.size.setValue(int(settings.value("editor_font_size",10)))
        self.size_label=QLabel(t("font_size")); form.addRow(self.size_label,self.size)
        self.color=settings.value("editor_font_color","#ffffff" if not light else "#20252b")
        self.color_label=QLabel(t("font_color")); row=QHBoxLayout()
        self.color_button=QPushButton(t("choose")); self.preview=QLabel("     "); self.preview.setMinimumSize(44,28)
        self._preview()
        self.color_button.clicked.connect(self.pick_color); row.addWidget(self.color_button); row.addWidget(self.preview); row.addStretch()
        form.addRow(self.color_label,row); outer.addLayout(form)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); outer.addWidget(buttons)
    def _preview(self): self.preview.setStyleSheet(f"background:{self.color};border:1px solid #7b8794;")
    def pick_color(self):
        c=QColorDialog.getColor(QColor(self.color),self,TEXT[self.lang]["font_color"])
        if c.isValid(): self.color=c.name(); self._preview()

class LunaText(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings=QSettings("Goldisoft","LunaText")
        self.lang=self.settings.value("language","de")
        if self.lang not in TEXT:self.lang="de"
        self.theme=self.settings.value("theme","dark")
        self.setMinimumSize(760,520)
        self.tabs=QTabWidget(); self.tabs.setTabsClosable(True); self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab); self.tabs.currentChanged.connect(self.update_status)
        # The tab widget is installed exactly once, inside central_shell
        # in _build_search(). Installing it here and replacing it there
        # destroys/reparents the original central widget on Qt.
        self.toolbar=QToolBar(); self.toolbar.setMovable(False); self.addToolBar(self.toolbar)
        self.status=QStatusBar(); self.setStatusBar(self.status)
        self._build_actions(); self._build_menus(); self._build_search()
        self.apply_theme(self.theme); self.translate()
        size=self.settings.value("window_size")
        if self.settings.value("remember_window_size",True,type=bool) and size:self.resize(size)
        else:self.resize(1000,700)
        self.new_file()
    def tr(self,k):return TEXT[self.lang].get(k,k)
    def _action(self,key,slot,shortcut=None):
        a=QAction(self.tr(key),self)
        if shortcut:a.setShortcut(QKeySequence(shortcut))
        a.triggered.connect(slot); return a
    def _build_actions(self):
        self.actions={}
        specs=[("new",self.new_file,"Ctrl+N"),("open",self.open_file,"Ctrl+O"),("save",self.save_file,"Ctrl+S"),
        ("saveas",self.save_as,"Ctrl+Shift+S"),("close",lambda:self.close_tab(self.tabs.currentIndex()),"Ctrl+W"),
        ("undo",lambda:self.editor() and self.editor().undo(),"Ctrl+Z"),("redo",lambda:self.editor() and self.editor().redo(),"Ctrl+Shift+Z"),
        ("cut",lambda:self.editor() and self.editor().cut(),"Ctrl+X"),("copy",lambda:self.editor() and self.editor().copy(),"Ctrl+C"),
        ("paste",lambda:self.editor() and self.editor().paste(),"Ctrl+V"),("select",lambda:self.editor() and self.editor().selectAll(),"Ctrl+A"),
        ("find",self.show_find,"Ctrl+F"),("replace",self.show_replace,"Ctrl+H")]
        for k,fn,sc in specs:self.actions[k]=self._action(k,fn,sc)
        self.save_tool=self.actions["save"]; self.find_tool=self.actions["find"]
    def _build_menus(self):
        bar=self.menuBar()
        self.file_menu=bar.addMenu(""); self.edit_menu=bar.addMenu(""); self.view_menu=bar.addMenu("")
        self.lang_menu=bar.addMenu(""); self.settings_menu=bar.addMenu(""); self.help_menu=bar.addMenu("")
        self.file_keys=["new","open","save","saveas","close","quit"]
        self.edit_keys=["undo","redo","cut","copy","paste","select","find","replace"]
        self.file_actions={}
        for k in self.file_keys:
            a=self._action(k,self.close if k=="quit" else (QApplication.quit if k=="quit" else (lambda key=k:self.actions[key].trigger())))
            if k=="quit":self.file_actions[k]=a
            else:self.file_actions[k]=self.actions[k]
        self.toolbar.addAction(self.actions["new"]);self.toolbar.addAction(self.actions["open"]);self.toolbar.addAction(self.actions["save"])
        self.toolbar.addSeparator();self.toolbar.addAction(self.actions["find"])
        self.toolbar_toggle=QAction("",self)
        self.toolbar_toggle.setCheckable(True)
        self.toolbar_toggle.setChecked(True)
        self.toolbar_toggle.toggled.connect(self.toolbar.setVisible)
        self.status_toggle=QAction("",self)
        self.status_toggle.setCheckable(True)
        self.status_toggle.setChecked(True)
        self.status_toggle.toggled.connect(self.statusBar().setVisible)
        self.light_action=QAction("",self,checkable=True);self.light_action.triggered.connect(lambda:self.apply_theme("light"))
        self.dark_action=QAction("",self,checkable=True);self.dark_action.triggered.connect(lambda:self.apply_theme("dark"))
        self.de_action=QAction("",self);self.de_action.triggered.connect(lambda:self.set_language("de"))
        self.en_action=QAction("",self);self.en_action.triggered.connect(lambda:self.set_language("en"))
        self.settings_action=QAction("",self);self.settings_action.triggered.connect(self.open_settings)
        self.about_action=QAction("",self);self.about_action.triggered.connect(lambda:QMessageBox.about(self,self.tr("about"),self.tr("about_text")))
        for key in ("new","open","save","saveas","close"):
            self.file_menu.addAction(self.actions[key])
        self.file_menu.addSeparator(); self.file_menu.addAction(self.file_actions["quit"])
        for key in ("undo","redo","cut","copy","paste","select","find","replace"):
            self.edit_menu.addAction(self.actions[key])
        self.view_menu.addAction(self.toolbar_toggle); self.view_menu.addAction(self.status_toggle)
        self.view_menu.addSeparator(); self.view_menu.addAction(self.light_action); self.view_menu.addAction(self.dark_action)
        self.lang_menu.addAction(self.de_action); self.lang_menu.addAction(self.en_action)
        self.settings_menu.addAction(self.settings_action)
        self.help_menu.addAction(self.about_action)
    def _build_search(self):
        self.search_panel=QWidget(); row=QHBoxLayout(self.search_panel);row.setContentsMargins(6,5,6,5)
        self.find_edit=QLineEdit();self.replace_edit=QLineEdit()
        self.next_button=QPushButton();self.replace_button=QPushButton();self.all_button=QPushButton();self.hide_button=QPushButton()
        for w in (self.find_edit,self.replace_edit,self.next_button,self.replace_button,self.all_button,self.hide_button):row.addWidget(w)
        self.central_shell=QWidget(); lay=QVBoxLayout(self.central_shell);lay.setContentsMargins(0,0,0,0);lay.setSpacing(0)
        self.setCentralWidget(self.central_shell);lay.addWidget(self.tabs,1);lay.addWidget(self.search_panel);self.search_panel.hide()
        self.next_button.clicked.connect(self.find_text);self.replace_button.clicked.connect(self.replace_one);self.all_button.clicked.connect(self.replace_all);self.hide_button.clicked.connect(self.search_panel.hide)
    def editor(self):return self.tabs.currentWidget()
    def new_file(self):
        ed=Editor();ed.file_path=None
        ed.document().modificationChanged.connect(lambda _=False,e=ed:self.refresh_tab(e))
        ed.cursorPositionChanged.connect(self.update_status)
        ed.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu);ed.customContextMenuRequested.connect(lambda p,e=ed:self.context_menu(e,p))
        self._style_editor(ed);idx=self.tabs.addTab(ed,self.tr("untitled"));self.tabs.setCurrentIndex(idx);self.refresh_tab(ed)
    def _effective_editor_color(self):
        # Migrate the old theme's default text color when switching themes.
        # Otherwise a saved white default from dark mode remains white on
        # the light editor background.
        color=str(self.settings.value(
            "editor_font_color",
            "#ffffff" if self.theme=="dark" else "#20252b")).lower()
        if self.theme=="light" and color=="#ffffff":
            color="#20252b"
            self.settings.setValue("editor_font_color",color)
        elif self.theme=="dark" and color=="#20252b":
            color="#ffffff"
            self.settings.setValue("editor_font_color",color)
        return color

    def _style_editor(self,ed):
        color=self._effective_editor_color()
        ed.set_editor_style(self.theme,int(self.settings.value("editor_font_size",10)),color)
    def refresh_tab(self,ed):
        i=self.tabs.indexOf(ed)
        if i<0:return
        path=getattr(ed,"file_path",None);name=Path(path).name if path else self.tr("untitled")
        if ed.document().isModified():name+=" *"
        self.tabs.setTabText(i,name);self.tabs.setTabToolTip(i,path or name)
        if ed is self.editor():self.setWindowTitle(f"LunaText {VERSION} — {name}")
    def open_path(self,path):
        path=str(Path(path).expanduser().resolve())
        for i in range(self.tabs.count()):
            e=self.tabs.widget(i)
            if getattr(e,"file_path",None)==path:self.tabs.setCurrentWidget(e);return
        try:data=Path(path).read_text(encoding="utf-8")
        except Exception as ex:QMessageBox.critical(self,self.tr("error"),self.tr("open_error").format(err=ex));return
        self.new_file()
        ed=self.editor()
        # Load into the QTextDocument explicitly and verify the actual content.
        ed.document().setPlainText(data)
        if ed.toPlainText()!=data:
            ed.setPlainText(data)
        ed.file_path=path
        self._style_editor(ed)
        font_size=int(self.settings.value("editor_font_size",10))
        ed.document().setDefaultFont(QFont("DejaVu Sans Mono",font_size))
        # Reapply an explicit character foreground after loading the file.
        ed.set_editor_style(self.theme,font_size,
            self.settings.value("editor_font_color","#ffffff" if self.theme=="dark" else "#20252b"))
        ed.document().setModified(False)
        c=ed.textCursor()
        c.movePosition(QTextCursor.MoveOperation.Start)
        ed.setTextCursor(c)
        ed.horizontalScrollBar().setValue(0)
        ed.verticalScrollBar().setValue(0)
        ed.ensureCursorVisible()
        ed.setVisible(True)
        ed.viewport().update()
        self.refresh_tab(ed)
        self.update_status()
    def _make_file_dialog(self, title, save=False, initial=""):
        dialog=QFileDialog(self,title)
        # Do not use the desktop-native dialog: its button captions are
        # supplied by the desktop environment and may remain English.
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog,True)
        dialog.setAcceptMode(
            QFileDialog.AcceptMode.AcceptSave if save
            else QFileDialog.AcceptMode.AcceptOpen)
        dialog.setFileMode(
            QFileDialog.FileMode.AnyFile if save
            else QFileDialog.FileMode.ExistingFile)
        dialog.setNameFilters([self.tr("textfiles"),self.tr("allfiles")])
        labels=QFileDialog.DialogLabel
        dialog.setLabelText(labels.Accept,"Speichern" if save and self.lang=="de" else
                            "Save" if save else "Öffnen" if self.lang=="de" else "Open")
        dialog.setLabelText(labels.Reject,"Abbrechen" if self.lang=="de" else "Cancel")
        dialog.setLabelText(labels.LookIn,"Suchen in:" if self.lang=="de" else "Look in:")
        dialog.setLabelText(labels.FileName,"Dateiname:" if self.lang=="de" else "File name:")
        dialog.setLabelText(labels.FileType,"Dateityp:" if self.lang=="de" else "File type:")
        if initial:
            dialog.selectFile(initial)
        return dialog

    def open_file(self):
        dialog=self._make_file_dialog(self.tr("open"))
        if dialog.exec()==QDialog.DialogCode.Accepted:
            files=dialog.selectedFiles()
            if files:self.open_path(files[0])
    def save_file(self):
        e=self.editor()
        if not e:return False
        p=getattr(e,"file_path",None)
        return self.save_as() if not p else self._write(e,p)
    def save_as(self):
        e=self.editor()
        if not e:return False
        dialog=self._make_file_dialog(
            self.tr("saveas"),save=True,
            initial=getattr(e,"file_path",None) or "")
        if dialog.exec()!=QDialog.DialogCode.Accepted:return False
        files=dialog.selectedFiles()
        if not files:return False
        p=files[0]
        if self._write(e,p):e.file_path=p;self.refresh_tab(e);return True
        return False
    def _write(self,e,p):
        try:Path(p).write_text(e.toPlainText(),encoding="utf-8");e.document().setModified(False);self.refresh_tab(e);return True
        except Exception as ex:QMessageBox.critical(self,self.tr("error"),self.tr("save_error").format(err=ex));return False
    def close_tab(self,i):
        if i<0 or i>=self.tabs.count():return
        e=self.tabs.widget(i)
        if e.document().isModified():
            name=Path(getattr(e,"file_path",self.tr("untitled"))).name
            prompt=QMessageBox(self)
            prompt.setIcon(QMessageBox.Icon.Question)
            prompt.setWindowTitle(self.tr("save_title"))
            prompt.setText(self.tr("saveprompt").format(name=name))
            save_button=prompt.addButton(
                "Speichern" if self.lang=="de" else "Save",
                QMessageBox.ButtonRole.AcceptRole)
            discard_button=prompt.addButton(
                "Ohne Speichern schließen" if self.lang=="de" else "Close without Saving",
                QMessageBox.ButtonRole.DestructiveRole)
            cancel_button=prompt.addButton(
                "Abbrechen" if self.lang=="de" else "Cancel",
                QMessageBox.ButtonRole.RejectRole)
            prompt.setDefaultButton(save_button)
            prompt.exec()
            clicked=prompt.clickedButton()
            ans=(QMessageBox.StandardButton.Save if clicked is save_button else
                 QMessageBox.StandardButton.Discard if clicked is discard_button else
                 QMessageBox.StandardButton.Cancel)
            if ans==QMessageBox.StandardButton.Cancel:return
            if ans==QMessageBox.StandardButton.Save:
                self.tabs.setCurrentIndex(i)
                if not self.save_file():return
        self.tabs.removeTab(i);e.deleteLater()
        if self.tabs.count()==0:self.new_file()
    def context_menu(self,e,pos):
        m=QMenu(self);c=e.textCursor()
        for key,fn in [("undo",e.undo),("redo",e.redo)]:m.addAction(self.tr(key),fn)
        m.addSeparator()
        for key,fn in [("cut",e.cut),("copy",e.copy),("paste",e.paste),("select",e.selectAll)]:m.addAction(self.tr(key),fn)
        m.addSeparator();m.addAction(self.tr("find"),self.show_find);m.exec(e.mapToGlobal(pos))
    def show_find(self):
        self.search_panel.show();self.replace_edit.hide();self.replace_button.hide();self.all_button.hide();self.find_edit.setFocus()
    def show_replace(self):
        self.search_panel.show();self.replace_edit.show();self.replace_button.show();self.all_button.show();self.find_edit.setFocus()
    def find_text(self):
        e=self.editor();needle=self.find_edit.text()
        if e and needle and not e.find(needle):
            c=e.textCursor();c.movePosition(QTextCursor.MoveOperation.Start);e.setTextCursor(c)
            if not e.find(needle):QMessageBox.information(self,self.tr("find"),self.tr("not_found"))
    def replace_one(self):
        e=self.editor()
        if not e:return
        if e.textCursor().hasSelection() and e.textCursor().selectedText()==self.find_edit.text():e.insertPlainText(self.replace_edit.text())
        self.find_text()
    def replace_all(self):
        e=self.editor();needle=self.find_edit.text()
        if not e or not needle:return
        old=e.toPlainText();count=old.count(needle)
        if count:e.setPlainText(old.replace(needle,self.replace_edit.text()));e.document().setModified(True);self.status.showMessage(str(count),3000)
        else:QMessageBox.information(self,self.tr("find"),self.tr("not_found"))
    def update_status(self,*_):
        e=self.editor()
        if not e:return
        c=e.textCursor();p=getattr(e,"file_path",None)
        try:n=os.path.getsize(p) if p and os.path.isfile(p) else 0
        except OSError:n=0
        size=f"{n} B" if n<1024 else (f"{n/1024:.1f} KB" if n<1048576 else f"{n/1048576:.2f} MB")
        self.status.showMessage(f'{self.tr("line")} {c.blockNumber()+1}  |  {self.tr("column")} {c.positionInBlock()+1}  |  {self.tr("file_size")}: {size}  |  UTF-8')
    def apply_theme(self,theme):
        self.theme=theme;light=theme=="light"
        bg,fg,panel,edge=("#f2f5f8","#243447","#e4edf5","#9bbbd5") if light else ("#20252b","#e5e9ef","#111d2a","#176da8")
        self.setStyleSheet(f"""
        QMainWindow{{background:{bg};color:{fg};}}
        QMenuBar,QToolBar,QStatusBar{{background:{panel};color:{fg};border:0;border-bottom:1px solid {edge};spacing:5px;padding:4px;}}
        QMenuBar::item{{padding:6px 10px;}} QMenu{{background:{bg};color:{fg};border:1px solid {edge};}}
        QMenu::item:selected{{background:{'#c8e5fb' if light else '#1269a8'};}}
        QTabWidget::pane{{border:1px solid {edge};}} QTabBar::tab{{background:{panel};color:{fg};padding:8px 14px;border:1px solid {edge};}}
        QTabBar::tab:selected{{background:{bg};border-top:3px solid {'#168bd2' if light else '#20a5ff'};}}
        QPushButton,QToolButton{{background:{'#d6e9f7' if light else '#17466a'};color:{'#173d5c' if light else '#f3f8ff'};border:1px solid {edge};padding:6px 10px;}}
        QLineEdit{{background:{'#ffffff' if light else '#151c24'};color:{fg};border:1px solid {edge};padding:6px;}}
        """)
        self.settings.setValue("theme",theme)
        for i in range(self.tabs.count()):self._style_editor(self.tabs.widget(i))
        self.light_action.setChecked(light);self.dark_action.setChecked(not light)
    def open_settings(self):
        self._effective_editor_color()
        dlg=SettingsDialog(self,self.lang,self.theme,self.settings)
        if dlg.exec()==QDialog.DialogCode.Accepted:
            self.settings.setValue("remember_window_size",dlg.remember.isChecked())
            self.settings.setValue("editor_font_size",dlg.size.value())
            self.settings.setValue("editor_font_color",dlg.color)
            for i in range(self.tabs.count()):self._style_editor(self.tabs.widget(i))
    def set_language(self,lang):
        self.lang=lang;self.settings.setValue("language",lang);self.translate()
    def translate(self):
        t=self.tr
        self.file_menu.setTitle(t("file"));self.edit_menu.setTitle(t("edit"));self.view_menu.setTitle(t("view"))
        self.lang_menu.setTitle(t("language"));self.settings_menu.setTitle(t("settings"));self.help_menu.setTitle(t("help"))
        for k,a in self.actions.items():a.setText(t(k))
        for k,a in self.file_actions.items():
            if k=="quit":a.setText(t("quit"))
        self.toolbar_toggle.setText(t("toolbar"));self.status_toggle.setText(t("statusbar"))
        self.light_action.setText(t("light"));self.dark_action.setText(t("dark"))
        self.de_action.setText(t("german"));self.en_action.setText(t("english"))
        self.settings_action.setText(t("settings_title"));self.about_action.setText(t("about"))
        self.find_edit.setPlaceholderText(t("find_hint"));self.replace_edit.setPlaceholderText(t("replace_hint"))
        self.next_button.setText(t("next"));self.replace_button.setText(t("replace"));self.all_button.setText(t("replace")+" all");self.hide_button.setText(t("close_find"))
        for i in range(self.tabs.count()):self.refresh_tab(self.tabs.widget(i))
        self.update_status()
    def closeEvent(self,event):
        if self.settings.value("remember_window_size",True,type=bool):self.settings.setValue("window_size",self.size())
        for i in range(self.tabs.count()-1,-1,-1):
            e=self.tabs.widget(i)
            if e.document().isModified():
                self.tabs.setCurrentIndex(i);name=Path(getattr(e,"file_path",self.tr("untitled"))).name
                prompt=QMessageBox(self)
                prompt.setIcon(QMessageBox.Icon.Question)
                prompt.setWindowTitle(self.tr("save_title"))
                prompt.setText(self.tr("saveprompt").format(name=name))
                save_button=prompt.addButton(
                    "Speichern" if self.lang=="de" else "Save",
                    QMessageBox.ButtonRole.AcceptRole)
                discard_button=prompt.addButton(
                    "Ohne Speichern schließen" if self.lang=="de" else "Close without Saving",
                    QMessageBox.ButtonRole.DestructiveRole)
                cancel_button=prompt.addButton(
                    "Abbrechen" if self.lang=="de" else "Cancel",
                    QMessageBox.ButtonRole.RejectRole)
                prompt.setDefaultButton(save_button)
                prompt.exec()
                clicked=prompt.clickedButton()
                if clicked is cancel_button:event.ignore();return
                if clicked is save_button and not self.save_file():event.ignore();return
        event.accept()

def main():
    app=QApplication(sys.argv);app.setStyle("Fusion");app.setApplicationName("LunaText");app.setOrganizationName("Goldisoft")
    name="Goldisoft_LunaText_0_1"
    requested=[str(Path(a).expanduser().resolve()) for a in sys.argv[1:] if not a.startswith("-") and Path(a).expanduser().is_file()]
    client=QLocalSocket();client.connectToServer(name)
    if client.waitForConnected(350):
        client.write(json.dumps(requested).encode());client.flush();client.waitForBytesWritten(1000);return 0
    QLocalServer.removeServer(name);server=QLocalServer()
    if not server.listen(name):
        retry=QLocalSocket();retry.connectToServer(name)
        if retry.waitForConnected(1000):retry.write(json.dumps(requested).encode());retry.flush();return 0
    win=LunaText()
    def accept():
        while server.hasPendingConnections():
            conn=server.nextPendingConnection()
            def receive(c=conn):
                try:
                    for p in json.loads(bytes(c.readAll()).decode()):
                        if os.path.isfile(p):win.open_path(p)
                except Exception as ex:QMessageBox.critical(win,"LunaText",str(ex))
                c.disconnectFromServer()
            conn.readyRead.connect(receive)
    server.newConnection.connect(accept)
    for p in requested:win.open_path(p)
    win.show();return app.exec()
if __name__=="__main__":raise SystemExit(main())
