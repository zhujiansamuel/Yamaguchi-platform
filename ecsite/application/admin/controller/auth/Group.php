<?php

namespace app\admin\controller\auth;

use app\admin\model\AuthGroup;
use app\common\controller\Backend;
use fast\Tree;
use think\Db;
use think\Exception;

/**
 * ロールグループ
 *
 * @icon   fa fa-group
 * @remark ロールグループは複数設定できます,ロールには上下関係の階層があります,子ロールがロールグループと管理者の権限を持つ場合、自分のグループ配下のロールグループや管理者を派生させることができます
 */
class Group extends Backend
{

    /**
     * @var \app\admin\model\AuthGroup
     */
    protected $model = null;
    //現在ログイン中の管理者の全ての子グループ
    protected $childrenGroupIds = [];
    //現在のグループの一覧データ
    protected $grouplist = [];
    protected $groupdata = [];
    //権限チェックが不要なメソッド
    protected $noNeedRight = ['roletree'];

    public function _initialize()
    {
        parent::_initialize();
        $this->model = model('AuthGroup');

        $this->childrenGroupIds = $this->auth->getChildrenGroupIds(true);

        $groupList = collection(AuthGroup::where('id', 'in', $this->childrenGroupIds)->select())->toArray();

        Tree::instance()->init($groupList);
        $groupList = [];
        if ($this->auth->isSuperAdmin()) {
            $groupList = Tree::instance()->getTreeList(Tree::instance()->getTreeArray(0));
        } else {
            $groups = $this->auth->getGroups();
            $groupIds = [];
            foreach ($groups as $m => $n) {
                if (in_array($n['id'], $groupIds) || in_array($n['pid'], $groupIds)) {
                    continue;
                }
                $groupList = array_merge($groupList, Tree::instance()->getTreeList(Tree::instance()->getTreeArray($n['pid'])));
                foreach ($groupList as $index => $item) {
                    $groupIds[] = $item['id'];
                }
            }
        }
        $groupName = [];
        foreach ($groupList as $k => $v) {
            $groupName[$v['id']] = $v['name'];
        }

        $this->grouplist = $groupList;
        $this->groupdata = $groupName;
        $this->assignconfig("admin", ['id' => $this->auth->id, 'group_ids' => $this->auth->getGroupIds()]);

        $this->view->assign('groupdata', $this->groupdata);
    }

    /**
     * 表示
     */
    public function index()
    {
        if ($this->request->isAjax()) {
            $list = $this->grouplist;
            $total = count($list);
            $result = array("total" => $total, "rows" => $list);

            return json($result);
        }
        return $this->view->fetch();
    }

    /**
     * 追加
     */
    public function add()
    {
        if ($this->request->isPost()) {
            $this->token();
            $params = $this->request->post("row/a", [], 'strip_tags');
            $params['rules'] = explode(',', $params['rules']);
            if (!in_array($params['pid'], $this->childrenGroupIds)) {
                $this->error(__('The parent group exceeds permission limit'));
            }
            $parentmodel = model("AuthGroup")->get($params['pid']);
            if (!$parentmodel) {
                $this->error(__('The parent group can not found'));
            }
            // 親レベルのルールノード
            $parentrules = explode(',', $parentmodel->rules);
            // 現在のグループのルールノード
            $currentrules = $this->auth->getRuleIds();
            $rules = $params['rules'];
            // 親グループがスーパー管理者でない場合は、ルールノードをフィルタリングする必要があります,親グループの権限を超えることはできません
            $rules = in_array('*', $parentrules) ? $rules : array_intersect($parentrules, $rules);
            // 現在のグループがスーパー管理者でない場合は、ルールノードをフィルタリングする必要があります,現在のグループの権限を超えることはできません
            $rules = in_array('*', $currentrules) ? $rules : array_intersect($currentrules, $rules);
            $params['rules'] = implode(',', $rules);
            if ($params) {
                $this->model->create($params);
                $this->success();
            }
            $this->error();
        }
        return $this->view->fetch();
    }

    /**
     * 編集
     */
    public function edit($ids = null)
    {
        if (!in_array($ids, $this->childrenGroupIds)) {
            $this->error(__('You have no permission'));
        }
        $row = $this->model->get(['id' => $ids]);
        if (!$row) {
            $this->error(__('No Results were found'));
        }
        if ($this->request->isPost()) {
            $this->token();
            $params = $this->request->post("row/a", [], 'strip_tags');
            //親ノードを権限外のノードにすることはできません
            if (!in_array($params['pid'], $this->childrenGroupIds)) {
                $this->error(__('The parent group exceeds permission limit'));
            }
            // 親ノードをその自身の子ノードまたは自分自身にすることはできません
            if (in_array($params['pid'], Tree::instance()->getChildrenIds($row->id, true))) {
                $this->error(__('The parent group can not be its own child or itself'));
            }
            $params['rules'] = explode(',', $params['rules']);

            $parentmodel = model("AuthGroup")->get($params['pid']);
            if (!$parentmodel) {
                $this->error(__('The parent group can not found'));
            }
            // 親レベルのルールノード
            $parentrules = explode(',', $parentmodel->rules);
            // 現在のグループのルールノード
            $currentrules = $this->auth->getRuleIds();
            $rules = $params['rules'];
            // 親グループがスーパー管理者でない場合は、ルールノードをフィルタリングする必要があります,親グループの権限を超えることはできません
            $rules = in_array('*', $parentrules) ? $rules : array_intersect($parentrules, $rules);
            // 現在のグループがスーパー管理者でない場合は、ルールノードをフィルタリングする必要があります,現在のグループの権限を超えることはできません
            $rules = in_array('*', $currentrules) ? $rules : array_intersect($currentrules, $rules);
            $params['rules'] = implode(',', $rules);
            if ($params) {
                Db::startTrans();
                try {
                    $row->save($params);
                    $children_auth_groups = model("AuthGroup")->all(['id' => ['in', implode(',', (Tree::instance()->getChildrenIds($row->id)))]]);
                    $childparams = [];
                    foreach ($children_auth_groups as $key => $children_auth_group) {
                        $childparams[$key]['id'] = $children_auth_group->id;
                        $childparams[$key]['rules'] = implode(',', array_intersect(explode(',', $children_auth_group->rules), $rules));
                    }
                    model("AuthGroup")->saveAll($childparams);
                    Db::commit();
                    $this->success();
                } catch (Exception $e) {
                    Db::rollback();
                    $this->error($e->getMessage());
                }
            }
            $this->error();
            return;
        }
        $this->view->assign("row", $row);
        return $this->view->fetch();
    }

    /**
     * 削除
     */
    public function del($ids = "")
    {
        if (!$this->request->isPost()) {
            $this->error(__("Invalid parameters"));
        }
        $ids = $ids ? $ids : $this->request->post("ids");
        if ($ids) {
            $ids = explode(',', $ids);
            $grouplist = $this->auth->getGroups();
            $group_ids = array_map(function ($group) {
                return $group['id'];
            }, $grouplist);
            // 現在の管理者が所属するグループを除外
            $ids = array_diff($ids, $group_ids);

            // 各グループが削除可能かを順に判定
            $grouplist = $this->model->where('id', 'in', $ids)->select();
            $groupaccessmodel = model('AuthGroupAccess');
            foreach ($grouplist as $k => $v) {
                // 現在のグループ配下に管理者が存在します
                $groupone = $groupaccessmodel->get(['group_id' => $v['id']]);
                if ($groupone) {
                    $ids = array_diff($ids, [$v['id']]);
                    continue;
                }
                // 現在のグループ配下に子グループが存在します
                $groupone = $this->model->get(['pid' => $v['id']]);
                if ($groupone) {
                    $ids = array_diff($ids, [$v['id']]);
                    continue;
                }
            }
            if (!$ids) {
                $this->error(__('You can not delete group that contain child group and administrators'));
            }
            $count = $this->model->where('id', 'in', $ids)->delete();
            if ($count) {
                $this->success();
            }
        }
        $this->error();
    }

    /**
     * 一括更新
     * @internal
     */
    public function multi($ids = "")
    {
        // グループは一括操作を禁止します
        $this->error();
    }

    /**
     * ロール権限ツリーを読み込む
     *
     * @internal
     */
    public function roletree()
    {
        $this->loadlang('auth/group');

        $model = model('AuthGroup');
        $id = $this->request->post("id");
        $pid = $this->request->post("pid");
        $parentGroupModel = $model->get($pid);
        $currentGroupModel = null;
        if ($id) {
            $currentGroupModel = $model->get($id);
        }
        if (($pid || $parentGroupModel) && (!$id || $currentGroupModel)) {
            $id = $id ? $id : null;
            $ruleList = collection(model('AuthRule')->order('weigh', 'desc')->order('id', 'asc')->select())->toArray();
            //親ロールのすべてのノード一覧を読み込む
            $parentRuleList = [];
            if (in_array('*', explode(',', $parentGroupModel->rules))) {
                $parentRuleList = $ruleList;
            } else {
                $parentRuleIds = explode(',', $parentGroupModel->rules);
                foreach ($ruleList as $k => $v) {
                    if (in_array($v['id'], $parentRuleIds)) {
                        $parentRuleList[] = $v;
                    }
                }
            }

            $ruleTree = new Tree();
            $groupTree = new Tree();
            //現在有効なすべてのルール一覧
            $ruleTree->init($parentRuleList);
            //ロールグループ一覧
            $groupTree->init(collection(model('AuthGroup')->where('id', 'in', $this->childrenGroupIds)->select())->toArray());

            //現在のロール配下のルールを読み込むIDIDのコレクション
            $adminRuleIds = $this->auth->getRuleIds();
            //スーパー管理者かどうか
            $superadmin = $this->auth->isSuperAdmin();
            //現在所持しているルールIDIDのコレクション
            $currentRuleIds = $id ? explode(',', $currentGroupModel->rules) : [];

            if (!$id || !in_array($pid, $this->childrenGroupIds) || !in_array($pid, $groupTree->getChildrenIds($id, true))) {
                $parentRuleList = $ruleTree->getTreeList($ruleTree->getTreeArray(0), 'name');
                $hasChildrens = [];
                foreach ($parentRuleList as $k => $v) {
                    if ($v['haschild']) {
                        $hasChildrens[] = $v['id'];
                    }
                }
                $parentRuleIds = array_map(function ($item) {
                    return $item['id'];
                }, $parentRuleList);
                $nodeList = [];
                foreach ($parentRuleList as $k => $v) {
                    if (!$superadmin && !in_array($v['id'], $adminRuleIds)) {
                        continue;
                    }
                    if ($v['pid'] && !in_array($v['pid'], $parentRuleIds)) {
                        continue;
                    }
                    $state = array('selected' => in_array($v['id'], $currentRuleIds) && !in_array($v['id'], $hasChildrens));
                    $nodeList[] = array('id' => $v['id'], 'parent' => $v['pid'] ? $v['pid'] : '#', 'text' => __($v['title']), 'type' => 'menu', 'state' => $state);
                }
                $this->success('', null, $nodeList);
            } else {
                $this->error(__('Can not change the parent to child'));
            }
        } else {
            $this->error(__('Group not found'));
        }
    }
}
