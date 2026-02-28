#pragma once
#include <QWidget>
#include <QProcess>

QT_BEGIN_NAMESPACE
namespace Ui { class Widget; }
QT_END_NAMESPACE

class Widget : public QWidget {
    Q_OBJECT
public:
    explicit Widget(QWidget *parent = nullptr);
    ~Widget();

private slots:
    void onChooseFolder();      // 「フィルタを選択」
    void onChooseExcel();       // 「excelを選択」
    void onRenameClicked();     // 「名前を変更」

    // Python 进程输出/结束
    void onProcReadyStdout();
    void onProcReadyStderr();
    void onProcFinished(int exitCode, QProcess::ExitStatus st);

private:
    Ui::Widget *ui;
    QString m_folder;   // 选中的文件夹
    QString m_excel;    // 选中的 excel 文件
    QProcess *m_proc{nullptr};

    void initUiDefaults();
    void logOk(const QString&);
    void logErr(const QString&);
    void setIdle();
    void setProgress(int percent, const QString &msg = {});

    QString pythonExecutable() const;
    QString pythonScriptPath() const;
};
