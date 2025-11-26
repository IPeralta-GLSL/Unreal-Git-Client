from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication
import sys
import os

app = QApplication(sys.argv)

if os.path.exists("ui/Icons/git-branch.svg"):
    pixmap = QPixmap("ui/Icons/git-branch.svg")
    if not pixmap.isNull():
        pixmap.save("ui/Icons/git-branch.ico", "ICO")
        print("Successfully converted ui/Icons/git-branch.svg to ui/Icons/git-branch.ico")
    else:
        print("Failed to load ui/Icons/git-branch.svg")
else:
    print("ui/Icons/git-branch.svg not found")