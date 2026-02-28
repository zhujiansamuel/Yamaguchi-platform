#include "widget.h"
#include "ui_Widget.h"

#include <QtWidgets>
#include <QStandardPaths>
#include <QCoreApplication>
#include <QDir>

Widget::Widget(QWidget *parent)
    : QWidget(parent), ui(new Ui::Widget) {
    ui->setupUi(this);
    initUiDefaults();

    // 对应 .ui 里的对象名
    connect(ui->pushButton,   &QPushButton::clicked, this, &Widget::onChooseFolder); // フィルタを選択
    connect(ui->pushButton_2, &QPushButton::clicked, this, &Widget::onChooseExcel);  // excelを選択
    connect(ui->pushButton_3, &QPushButton::clicked, this, &Widget::onRenameClicked);// 名前を変更
}

Widget::~Widget() {
    if (m_proc) {
        m_proc->kill();
        m_proc->deleteLater();
    }
    delete ui;
}

void Widget::initUiDefaults() {
    ui->comboBox->clear();
    ui->comboBox->addItem(QStringLiteral("PDF"));
    ui->comboBox->setCurrentIndex(0);

    setIdle();
    ui->textBrowser->clear();
    ui->textBrowser_2->clear();
}

void Widget::setIdle() {
    ui->progressBar->setRange(0, 100);
    ui->progressBar->setValue(0);
    ui->label_5->setText(QStringLiteral("進捗"));
}

void Widget::setProgress(int percent, const QString &msg) {
    ui->progressBar->setValue(qBound(0, percent, 100));
    if (!msg.isEmpty()) {
        ui->label_5->setText(
            QStringLiteral("進捗: %1%  %2").arg(percent).arg(msg)
            );
    } else {
        ui->label_5->setText(
            QStringLiteral("進捗: %1%").arg(percent)
            );
    }
}

void Widget::logOk(const QString &s) {
    ui->textBrowser_2->append("✅ " + s);
}
void Widget::logErr(const QString &s) {
    ui->textBrowser->append("❌ " + s);
}

void Widget::onChooseFolder() {
    const QString startDir = m_folder.isEmpty() ? QDir::homePath() : m_folder;
    const QString dir = QFileDialog::getExistingDirectory(
        this, QStringLiteral("フォルダを選択"),
        startDir,
        QFileDialog::ShowDirsOnly | QFileDialog::DontResolveSymlinks
        );
    if (!dir.isEmpty()) {
        m_folder = dir;
        logOk(QStringLiteral("フォルダを選択: %1").arg(dir));
    }
}

void Widget::onChooseExcel() {
    const QString startDir = m_excel.isEmpty()
    ? (m_folder.isEmpty() ? QDir::homePath() : m_folder)
    : QFileInfo(m_excel).absolutePath();

    const QString file = QFileDialog::getOpenFileName(
        this, QStringLiteral("Excel を選択"),
        startDir,
        QStringLiteral("Excel files (*.xlsx *.xlsm *.xls);;All files (*.*)")
        );
    if (!file.isEmpty()) {
        m_excel = file;
        logOk(QStringLiteral("Excel を選択: %1").arg(file));
    }
}

QString Widget::pythonExecutable() const {
#if defined(Q_OS_MAC)
    QString py = QStandardPaths::findExecutable("python3");
    if (py.isEmpty())
        py = QStandardPaths::findExecutable("python");
#else
    QString py = QStandardPaths::findExecutable("python3");
    if (py.isEmpty())
        py = QStandardPaths::findExecutable("python");
#endif
    return py;
}

QString Widget::pythonScriptPath() const {
    // 我们在 CMake 里把脚本拷贝到了可执行所在目录的 scripts/ 目录下
    QDir dir(QCoreApplication::applicationDirPath());
    return dir.filePath("scripts/rename_by_excel.py");
}

void Widget::onRenameClicked() {
    if (m_folder.isEmpty()) {
        logErr(QStringLiteral("フォルダが未選択です。"));
        return;
    }
    if (m_excel.isEmpty()) {
        logErr(QStringLiteral("Excel ファイルが未選択です。"));
        return;
    }

    const QString py = pythonExecutable();
    if (py.isEmpty()) {
        logErr(QStringLiteral("Python 実行ファイルが見つかりません（python3 / python）。"));
        QMessageBox::warning(this, tr("エラー"),
                             tr("Python が見つかりませんでした。ターミナルから python3 が実行できるか確認してください。"));
        return;
    }

    const QString script = pythonScriptPath();
    if (!QFileInfo::exists(script)) {
        logErr(QStringLiteral("Python スクリプトが見つかりません: %1").arg(script));
        QMessageBox::warning(this, tr("エラー"),
                             tr("Python スクリプトが見つかりませんでした:\n%1").arg(script));
        return;
    }

    // 如果上一次还在跑，先杀掉
    if (m_proc) {
        m_proc->kill();
        m_proc->deleteLater();
        m_proc = nullptr;
    }

    m_proc = new QProcess(this);
    m_proc->setProcessChannelMode(QProcess::SeparateChannels);

    connect(m_proc, &QProcess::readyReadStandardOutput,
            this, &Widget::onProcReadyStdout);
    connect(m_proc, &QProcess::readyReadStandardError,
            this, &Widget::onProcReadyStderr);
    connect(m_proc,
            QOverload<int, QProcess::ExitStatus>::of(&QProcess::finished),
            this,
            &Widget::onProcFinished);

    QStringList args;
    args << script
         << "--folder" << m_folder
         << "--excel"  << m_excel
         << "--filter" << ui->comboBox->currentText();
    // 如果想先测试不真实改名，可在这里加上 "--dry-run"
    // args << "--dry-run";

    logOk(QStringLiteral("処理開始: %1 %2").arg(py, args.join(' ')));
    setProgress(0, QStringLiteral("処理開始"));

    m_proc->start(py, args);
    if (!m_proc->waitForStarted()) {
        logErr(QStringLiteral("Python プロセスを起動できませんでした。"));
        m_proc->deleteLater();
        m_proc = nullptr;
    }
}

void Widget::onProcReadyStdout() {
    const QString out = QString::fromUtf8(m_proc->readAllStandardOutput());
    const auto lines = out.split('\n', Qt::SkipEmptyParts);
    for (const QString &line : lines) {
        // 解析类似 "PROGRESS 35 メッセージ..." 的行
        if (line.startsWith("PROGRESS ")) {
            const auto parts = line.split(' ');
            if (parts.size() >= 2) {
                bool ok = false;
                int p = parts[1].toInt(&ok);
                if (ok) {
                    QString msg = line.mid(QString("PROGRESS ").size() + parts[1].size()).trimmed();
                    setProgress(p, msg);
                    continue;
                }
            }
        }
        logOk(line);
    }
}

void Widget::onProcReadyStderr() {
    const QString err = QString::fromUtf8(m_proc->readAllStandardError());
    const auto lines = err.split('\n', Qt::SkipEmptyParts);
    for (const QString &line : lines) {
        logErr(line);
    }
}

void Widget::onProcFinished(int exitCode, QProcess::ExitStatus st) {
    if (st == QProcess::NormalExit && exitCode == 0) {
        setProgress(100, QStringLiteral("完了"));
        logOk(QStringLiteral("処理が正常終了しました。"));
    } else {
        logErr(QStringLiteral("処理が異常終了しました。exit=%1").arg(exitCode));
    }
}
