#include <QApplication>
#include "widget.h"

int main(int argc, char *argv[]) {
    QApplication app(argc, argv);
    Widget w;
    w.setWindowTitle(QStringLiteral("名前変更ツール"));
    // 你的 Widget.ui 是 758x682，这里可以不设，Qt 会按 ui 默认大小
    w.show();
    return app.exec();
}
