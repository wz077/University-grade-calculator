import os
import json
import csv
import datetime
import requests
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel, QLineEdit, QMessageBox, QMainWindow
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap
import random
from PyQt5.QtGui import QDoubleValidator
import uuid
from PyQt5.QtWidgets import QTabWidget, QInputDialog


def get_base_dir():
    """Folder used for files we WRITE and want to persist across runs
    (session.json, grade_data_*.json). When frozen into an exe, this is
    the folder the .exe itself lives in — not the temp extraction folder,
    which PyInstaller wipes every time the program closes."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))


def get_resource_path(filename):
    """Folder used for bundled READ-ONLY resources (styles.qss, icon, etc).
    When frozen, PyInstaller extracts these to a temp folder pointed to by
    sys._MEIPASS. When running as a normal .py script, just use the script's
    own folder."""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)


STYLE_FILE = get_resource_path("styles.qss")
SESSION_FILE = os.path.join(get_base_dir(), "session.json")

class SubjectTab(QWidget):
        
    
    def __init__(self, tab_id, parent=None):
        super().__init__(parent)
        self.tab_id = tab_id
        self.main_window = parent
        self.data_file = self.data_file_for(tab_id)
        self.init_ui()
        self.load_data()

            
    def data_file_for(self, tab_id):
        return os.path.join(get_base_dir(), f"grade_data_{tab_id}.json")

    def init_ui(self):
        
        layout = QVBoxLayout()
        self.setLayout(layout)

        subject_name_row = QHBoxLayout()
        title_row = QHBoxLayout()
        goal_row = QHBoxLayout()
        remaining_grade_percentage_row = QHBoxLayout()
        ass_title_row = QHBoxLayout()
        
        calc_grade_row = QHBoxLayout()
        result_row = QVBoxLayout()

        # Column widths shared between the header row and every assessment row.
        NAME_WIDTH = 200
        MARK_WIDTH = 100
        MAXMARK_WIDTH = 100
        WEIGHT_WIDTH = 100
        COLUMN_SPACING = 20
        LEFT_MARGIN = 15
        NUM_ASSESSMENT_ROWS = 8

        self.title = QLabel()
        self.title.setText("University Grade Calculator")
        title_font = QFont("Ariel", 18)
        title_font.setBold(True)
        self.title.setFont(title_font)
        self.title.setContentsMargins(LEFT_MARGIN, 10, 0, 0)
        self.title.setObjectName("title")
        
        title_row.addWidget(self.title)
        layout.addLayout(title_row)
        

        self.subject_name_label = QLabel("Enter Subject Name: ")
        self.subject_name_label.setObjectName("fieldLabel")
        goal_label_font = QFont("Arial", 13)
        goal_label_font.setBold(True)
        self.subject_name_label.setFont(goal_label_font)
        
        self.subject_name_input = QLineEdit()
        self.subject_name_input.setPlaceholderText("E.g: COMP1511")
        self.subject_name_input.setFont(QFont("Arial", 13))
        self.subject_name_input.setFixedWidth(200)
            
        
        subject_name_row.addWidget(self.subject_name_label)
        subject_name_row.addWidget(self.subject_name_input)
        subject_name_row.addStretch()
        subject_name_row.setContentsMargins(LEFT_MARGIN, 7, 0, 0)
        layout.addLayout(subject_name_row)
        

        # --- Goal grade ---
        self.goal_label = QLabel("Enter your goal grade: ")
        self.goal_label.setObjectName("fieldLabel")
        goal_label_font = QFont("Arial", 13)
        goal_label_font.setBold(True)
        self.goal_label.setFont(goal_label_font)
        self.goal_input = QLineEdit()
        self.goal_input.setValidator(QDoubleValidator(0.0, 999999.0, 10))
        self.goal_input.setPlaceholderText("E.g: 85")
        self.goal_input.setFont(QFont("Arial", 13))
        self.goal_input.setFixedWidth(100)

        goal_row.addWidget(self.goal_label)
        goal_row.addWidget(self.goal_input)
        goal_row.addStretch()
        goal_row.setContentsMargins(LEFT_MARGIN, 7, 0, 0)
        layout.addLayout(goal_row)
        
        self.ungraded_label = QLabel("Enter Ungraded Percentage: ")
        self.ungraded_label.setObjectName("fieldLabel")
        self.ungraded_label.setFont(goal_label_font)
        self.ungraded_input = QLineEdit()
        self.ungraded_input.setValidator(QDoubleValidator(0.0, 999999.0, 10))
        self.ungraded_input.setPlaceholderText("E.g: 20")
        self.ungraded_input.setFont(QFont("Arial", 13))
        self.ungraded_input.setFixedWidth(100)
    
        remaining_grade_percentage_row.addWidget(self.ungraded_label)
        remaining_grade_percentage_row.addWidget(self.ungraded_input)
        remaining_grade_percentage_row.addStretch()
        remaining_grade_percentage_row.setContentsMargins(LEFT_MARGIN, 7, 0, 0)
        layout.addLayout(remaining_grade_percentage_row)

        # --- Column headers ---
        self.assNames = QLabel("Assessment Name")
        self.assNames.setObjectName("columnHeader")
        self.assNames.setFont(QFont("Arial", 13))
        self.assNames.setFixedWidth(NAME_WIDTH)

        self.assMarks = QLabel("Marks")
        self.assMarks.setObjectName("columnHeader")
        self.assMarks.setFont(QFont("Arial", 13))
        self.assMarks.setFixedWidth(MARK_WIDTH)

        self.assMaxMarks = QLabel("Max Marks")
        self.assMaxMarks.setObjectName("columnHeader")
        self.assMaxMarks.setFont(QFont("Arial", 13))
        self.assMaxMarks.setFixedWidth(MAXMARK_WIDTH)

        self.assWeight = QLabel("Weighting")
        self.assWeight.setObjectName("columnHeader")
        self.assWeight.setFont(QFont("Arial", 13))
        self.assWeight.setFixedWidth(WEIGHT_WIDTH)

        ass_title_row.addWidget(self.assNames)
        ass_title_row.addWidget(self.assMarks)
        ass_title_row.addWidget(self.assMaxMarks)
        ass_title_row.addWidget(self.assWeight)
        ass_title_row.addStretch()
        ass_title_row.setSpacing(COLUMN_SPACING)
        ass_title_row.setContentsMargins(LEFT_MARGIN, 20, 0, 0)
        layout.addLayout(ass_title_row)

        # Each row's inputs are stored in these lists (index 0 = row 1, etc.)
    
        self.ass_name_inputs = []
        self.ass_mark_inputs = []
        self.ass_maxmark_inputs = []
        self.ass_weight_inputs = []

        for i in range(1, NUM_ASSESSMENT_ROWS + 1):
            ass_row = QHBoxLayout()

            name_input = QLineEdit()
            if i == 1:
                name_input.setPlaceholderText(f"E.g. Assessment {i}")
            name_input.setFont(QFont("Arial", 12))
            name_input.setFixedWidth(NAME_WIDTH)

            mark_input = QLineEdit()
            mark_input.setValidator(QDoubleValidator(0.0, 999999.0, 10))
            if i == 1:
                mark_input.setPlaceholderText("E.g. 70")
            mark_input.setFont(QFont("Arial", 12))
            mark_input.setFixedWidth(MARK_WIDTH)

            maxmark_input = QLineEdit()
            maxmark_input.setValidator(QDoubleValidator(0.0, 999999.0, 10))
            if i == 1:
                maxmark_input.setPlaceholderText("E.g. 100")
            maxmark_input.setFont(QFont("Arial", 12))
            maxmark_input.setFixedWidth(MAXMARK_WIDTH)

            weight_input = QLineEdit()
            weight_input.setValidator(QDoubleValidator(0.0, 999999.0, 10))
            if i == 1:
                weight_input.setPlaceholderText("E.g. 20%")
            weight_input.setFont(QFont("Arial", 12))
            weight_input.setFixedWidth(WEIGHT_WIDTH)

            ass_row.addWidget(name_input)
            ass_row.addWidget(mark_input)
            ass_row.addWidget(maxmark_input)
            ass_row.addWidget(weight_input)
            ass_row.addStretch()
            ass_row.setSpacing(COLUMN_SPACING)
            ass_row.setContentsMargins(LEFT_MARGIN, 6, 0, 0)
            layout.addLayout(ass_row)

            self.ass_name_inputs.append(name_input)
            self.ass_mark_inputs.append(mark_input)
            self.ass_maxmark_inputs.append(maxmark_input)
            self.ass_weight_inputs.append(weight_input)
            
        self.calcButton = QPushButton("Calculate Grade")
        self.calcButton.setObjectName("calcButton")
        self.calcButton.setFont(QFont("Arial", 12, QFont.Bold))
        self.calcButton.setFixedWidth(562)
        self.calcButton.setFixedHeight(35)
        self.calcButton.clicked.connect(self.calc_grade)
        calc_grade_row.addWidget(self.calcButton)
        calc_grade_row.setContentsMargins(0, 20, 6, 0)
        layout.addLayout(calc_grade_row)
        
        
        self.mode0__pre_result = QLabel("")
        self.mode0__pre_result.setObjectName("resultPreamble")
        self.mode0__pre_result.setFont(QFont("Ariel", 12))
        self.mode0__pre_result.setAlignment(Qt.AlignCenter)
        result_row.addWidget(self.mode0__pre_result)
        
        self.mode0__result = QLabel("")
        self.mode0__result.setObjectName("resultValue")
        mode0__result_font = QFont("Ariel", 20)
        mode0__result_font.setBold(True)
        self.mode0__result.setFont(mode0__result_font)
        self.mode0__result.setAlignment(Qt.AlignCenter)
        
        
        result_row.setContentsMargins(0, 20, 0, 0)
        result_row.addWidget(self.mode0__result)
        
        self.mode0__result_as_grade = QLabel("")
        self.mode0__result_as_grade.setObjectName("resultGrade")
        mode0__result_as_grade_font = QFont("Ariel", 14)
        mode0__result_as_grade_font.setBold(True)
        self.mode0__result_as_grade.setFont(mode0__result_as_grade_font)
        self.mode0__result_as_grade.setAlignment(Qt.AlignCenter)
        result_row.addWidget(self.mode0__result_as_grade)
        
        
        layout.addLayout(result_row)
        
        
        
        layout.addStretch()
        
    def mark_to_percent(self, mark, maxmark):
        mark_percent = float((float(mark)/float(maxmark)) * 100)
        return mark_percent
        
    def calc_grade(self):
        
        tab_index = self.main_window.tabs.indexOf(self)
        new_name = self.subject_name_input.text().strip()
        if new_name:
            self.main_window.tabs.setTabText(tab_index, new_name)
        
        check = self.goal_input.text()
        ungraded = self.ungraded_input.text()
        
        if not check and not ungraded:
            mode = 0
                
        else:
            if not ungraded:
                QMessageBox.warning(self, "Missing Input", "Please enter ungraded percentage (the weight of ungraded assessments)")
                mode = 2
            elif not check:
                QMessageBox.warning(self, "Missing Input", "Please enter your goal grade")
                mode = 2
            else:
                mode = 1
            
        if mode == 0:
            
            total = float(0)
            total_weightings = float(0)
            
            for i in range(0, 8):
                
                mark = self.ass_mark_inputs[i].text()
                max_mark = self.ass_maxmark_inputs[i].text()
                weighting = self.ass_weight_inputs[i].text()
                if not mark and not max_mark and not weighting :
                    break
                
                if not mark or not max_mark or not weighting:
                    QMessageBox.warning(self, "Input Error", "Missing input fields!")
                    return
                
                
                total_weightings = total_weightings + float(weighting)
                
                weighting_float = float(weighting)/100
                
                percent_mark = self.mark_to_percent(mark, max_mark)
                
                total = total + (percent_mark * weighting_float)
            
            if total == 0 or total_weightings == 0:
                QMessageBox.warning(self, "Input Error", "Please enter in your grades")
                return
            
            total = (total/total_weightings) * 100
                    
            print(round(total, 2))
            
            self.mode0__pre_result.setText("Your weighted Grade is")
            result_text = str(round(total, 2))
            self.mode0__result.setText(result_text)
            
            grade_str = self.mark_to_grade(total)
            self.mode0__result_as_grade.setText(grade_str)
            
            self.save_data()
            return total
                
            
        elif mode == 1:
            goal = float(self.goal_input.text())
            ungraded = float(self.ungraded_input.text())
            marked_weightings = float(0)
            total = float(0)
            
            for i in range(0, 8):
                            
                mark = self.ass_mark_inputs[i].text()
                max_mark = self.ass_maxmark_inputs[i].text()
                weighting = self.ass_weight_inputs[i].text()
                
                if not mark and not max_mark and not weighting :
                     break
                            
                if not mark or not max_mark or not weighting:
                    QMessageBox.warning(self, "Input Error", "Missing input fields!")
                    return
                
                marked_weightings = marked_weightings + float(weighting)
                
                weighting_float = float(weighting)/100
                
                percent_mark = self.mark_to_percent(mark, max_mark)
                
                total = total + (percent_mark * weighting_float)
                
            
            
            total_weightings = marked_weightings + ungraded
            goal_with_total_weight = (goal/100)*total_weightings
            mark_gap = goal_with_total_weight - total
            required_mark = mark_gap/(ungraded/100)
            
            
            print(f"Need this much more: {required_mark}")
            
            
            self.mode0__pre_result.setText("You Need:")
            
            if required_mark < 0:
                required_mark = 0
                
            result_text = str(round(required_mark, 2))
                
            self.mode0__result.setText(f"{result_text}")
            
            grade = self.mark_to_grade(goal)
            if required_mark != 0:
                self.mode0__result_as_grade.setText(f"To achieve your goal of {goal}")
            else:
                self.mode0__result_as_grade.setText(f"You are guaranteed to hit your goal of {goal}")
            
            self.save_data()
            return total
        
        elif mode == 2:
            return
            
            
            
            
            
             
        
    def mark_to_grade(self, mark):
        if mark >= 85:
            return "High Distinction (HD)"
        elif mark >= 75 and mark < 85:
            return "Distinction (D)"
        elif mark >= 65 and mark < 75:
            return "Credit (CR)"
        elif mark >= 50 and mark < 65:
            return "Pass (P)"
        elif mark < 50:
            return "Fail (FL)"
        else:
            return "ERROR"
        
    def gather_data(self):
        assessments = []
        for i in range(8):
            assessments.append({
              "name": self.ass_name_inputs[i].text(),
              "mark": self.ass_mark_inputs[i].text(),
              "maxmark": self.ass_maxmark_inputs[i].text(),
              "weight": self.ass_weight_inputs[i].text(),
            })
        
        return {
            "goal_grade": self.goal_input.text(),
            "ungraded_percentage": self.ungraded_input.text(),
            "assessments": assessments,
        }    
        
    def save_data(self):
        data = self.gather_data()
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            
    def load_data(self):
        if not os.path.exists(self.data_file):
            return
        
        with open(self.data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        self.goal_input.setText(data.get("goal_grade", ""))
        self.ungraded_input.setText(data.get("ungraded_percentage", ""))
        
        assessments = data.get("assessments", [])
        for i in range(8):
            if i < len(assessments):
                row = assessments[i]
                self.ass_name_inputs[i].setText(row.get("name", ""))
                self.ass_mark_inputs[i].setText(row.get("mark", ""))
                self.ass_maxmark_inputs[i].setText(row.get("maxmark", ""))
                self.ass_weight_inputs[i].setText(row.get("weight", ""))
                
    def delete_data_file(self):
        if os.path.exists(self.data_file):
            os.remove(self.data_file)
                
#    def closeEvent(self, event):
#        self.save_data()
#        event.accept()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(300, 120, 700, 900)
        self.setFixedSize(620, 915)
        self.setWindowTitle("University Grade Calculator")
        
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tabs)
        
        self.add_tab_button = QPushButton("+")
        self.add_tab_button.setObjectName("addTabButton")
        self.add_tab_button.setFixedSize(28, 28)
        self.add_tab_button.clicked.connect(lambda: self.add_tab())
        
        corner_container = QWidget()
        corner_layout = QHBoxLayout(corner_container)
        corner_layout.setContentsMargins(0, 4, 10, 4)
        corner_layout.addWidget(self.add_tab_button)
        
        self.tabs.setCornerWidget(corner_container, Qt.TopRightCorner)
        
        
        self.load_stylesheet()
        self.load_session()
        
    def load_stylesheet(self):
        if not os.path.exists(STYLE_FILE):
            return
        with open(STYLE_FILE, "r", encoding="utf-8") as f:
            self.setStyleSheet(f.read())
            
    def add_tab(self, tab_id=None, title=None):
        if tab_id is None:
            tab_id = uuid.uuid4().hex[:8]
        tab = SubjectTab(tab_id, parent=self)
        label = title or f"Subject {self.tabs.count() + 1}"
        self.tabs.addTab(tab, label)
        return tab
    

    def close_tab(self, index):
        widget = self.tabs.widget(index)
        if widget is None:
            return
        
        reply = QMessageBox.question(
            self,
            "Close Tab",
            f"Close '{self.tabs.tabText(index)}'?, This will permanent delete its saved data.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        widget.delete_data_file()
        self.tabs.removeTab(index)
        widget.deleteLater()
        
        if self.tabs.count() == 0:
            self.add_tab()
            
    def gather_session(self):
        tabs_info = []
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            tabs_info.append({
                "tab_id": widget.tab_id,
                "title": self.tabs.tabText(i),
            })
        return {"tabs": tabs_info}
    
    def save_session(self):
        session = self.gather_session()
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(session, f, indent=2)
            
    def load_session(self):
        if not os.path.exists(SESSION_FILE):
            self.add_tab()
            return
        
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            session = json.load(f)
            
        tabs_info = session.get("tabs", [])
        if not tabs_info:
            self.add_tab()
            return
        
        for entry in tabs_info:
            self.add_tab(tab_id=entry.get("tab_id"), title=entry.get("title"))
            
    
            
            
    def closeEvent(self, event):
        for i in range(self.tabs.count()):
            self.tabs.widget(i).save_data()
        self.save_session()
        event.accept()
        
    

            
            
        
        
    



def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()