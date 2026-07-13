import sys
from PyQt6.QtWidgets import QApplication, QTableWidget, QTableWidgetItem, QAbstractItemView
from PyQt6.QtCore import Qt

app = QApplication(sys.argv)
t = QTableWidget(3, 3)
t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
t.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
t.setFocusPolicy(Qt.FocusPolicy.NoFocus)

t.setStyleSheet("""
    QTableWidget::item:selected {
        background-color: #dbeafe;
        color: #0f172a;
    }
""")

for r in range(3):
    for c in range(3):
        t.setItem(r, c, QTableWidgetItem(f"R{r}C{c}"))

def on_click(r, c):
    print(f"Clicked {r},{c}. Selected items: {len(t.selectedItems())}")

def on_dbl(r, c):
    print(f"Double clicked {r},{c}")

t.cellClicked.connect(on_click)
t.cellDoubleClicked.connect(on_dbl)

t.show()
# sys.exit(app.exec())
print("Test table configured")
