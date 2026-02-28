<?php

namespace app\index\controller;

use think\Controller;

/**
 * 模板编辑器 - 独立控制器
 */
class TemplateEditor extends Controller
{
    /**
     * 编辑器主页面
     */
    public function index()
    {
        // 禁用模板布局
        $this->view->engine->layout(false);
        $this->view->assign('title', '買取申込書模板编辑器');
        return $this->view->fetch();
    }

    /**
     * 获取模板内容
     */
    public function get_template()
    {
        $template_file = APP_PATH . 'index/view/index/ylindex.html';
        if (file_exists($template_file)) {
            $content = file_get_contents($template_file);
            return json(['code' => 1, 'data' => $content]);
        } else {
            return json(['code' => 0, 'msg' => '模板文件不存在']);
        }
    }

    /**
     * 保存模板内容
     */
    public function save_template()
    {
        if ($this->request->isPost()) {
            $content = $this->request->post('content');
            if (empty($content)) {
                return json(['code' => 0, 'msg' => '内容不能为空']);
            }

            $template_file = APP_PATH . 'index/view/index/ylindex.html';

            // 备份原文件
            $backup_file = APP_PATH . 'index/view/index/ylindex.html.backup.' . date('YmdHis');
            if (file_exists($template_file)) {
                copy($template_file, $backup_file);
            }

            // 保存新内容
            if (file_put_contents($template_file, $content)) {
                return json(['code' => 1, 'msg' => '保存成功', 'backup' => basename($backup_file)]);
            } else {
                return json(['code' => 0, 'msg' => '保存失败']);
            }
        }
        return json(['code' => 0, 'msg' => '非法请求']);
    }
}
