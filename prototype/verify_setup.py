import sys
from PySide6.QtWidgets import QApplication, QLabel

def main():
    app = QApplication(sys.argv)
    label = QLabel('Hello PySide6!')
    label.resize(200, 100)
    label.show()
    # For CI/automated testing we won't run exec()
    print('PySide6 Setup Verified')

if __name__ == '__main__':
    main()
