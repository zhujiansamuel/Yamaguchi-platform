<?php

namespace app\admin\controller\auth;

use app\admin\model\AuthGroup;
use app\admin\model\AuthGroupAccess;
use app\common\controller\Backend;
use fast\Random;
use fast\Tree;
use think\Db;
use think\Validate;

/**
 * 管理者管理
 *
 * @icon   fa fa-users
 * @remark 1人の管理者は複数のロールグループを持つことができます,左側メニューは管理者が所持する権限に基づいて生成されます
 */
class Admin extends Backend
{

    /**
     * @var \app\admin\model\Admin
     */
    protected $model = null;
    protected $selectpageFields = 'id,username,nickname,avatar';
    protected $searchFields = 'id,username,nickname';
    protected $childrenGroupIds = [];
    protected $childrenAdminIds = [];

    public function _initialize()
    {
        parent::_initialize();
        $this->model = model('Admin');

        $this->childrenAdminIds = $this->auth->getChildrenAdminIds($this->auth->isSuperAdmin());
        $this->childrenGroupIds = $this->auth->getChildrenGroupIds($this->auth->isSuperAdmin());

        $groupList = collection(AuthGroup::where('id', 'in', $this->childrenGroupIds)->select())->toArray();

        Tree::instance()->init($groupList);
        $groupdata = [];
        if ($this->auth->isSuperAdmin()) {
            $result = Tree::instance()->getTreeList(Tree::instance()->getTreeArray(0));
            foreach ($result as $k => $v) {
                $groupdata[$v['id']] = $v['name'];
            }
        } else {
            $result = [];
            $groups = $this->auth->getGroups();
            foreach ($groups as $m => $n) {
                $childlist = Tree::instance()->getTreeList(Tree::instance()->getTreeArray($n['id']));
                $temp = [];
                foreach ($childlist as $k => $v) {
                    $temp[$v['id']] = $v['name'];
                }
                $result[__($n['name'])] = $temp;
            }
            $groupdata = $result;
        }

        $this->view->assign('groupdata', $groupdata);
        $this->assignconfig("admin", ['id' => $this->auth->id]);
    }

    /**
     * 表示
     */
    public function index()
    {
        //フィルターメソッドを設定
        $this->request->filter(['strip_tags', 'trim']);
        if ($this->request->isAjax()) {
            //送信元がSelectpage，の場合は、次に転送するSelectpage
            if ($this->request->request('keyField')) {
                return $this->selectpage();
            }
            $childrenGroupIds = $this->childrenGroupIds;
            $groupName = AuthGroup::where('id', 'in', $childrenGroupIds)
                ->column('id,name');
            $authGroupList = AuthGroupAccess::where('group_id', 'in', $childrenGroupIds)
                ->field('uid,group_id')
                ->select();

            $adminGroupName = [];
            foreach ($authGroupList as $k => $v) {
                if (isset($groupName[$v['group_id']])) {
                    $adminGroupName[$v['uid']][$v['group_id']] = $groupName[$v['group_id']];
                }
            }
            $groups = $this->auth->getGroups();
            foreach ($groups as $m => $n) {
                $adminGroupName[$this->auth->id][$n['id']] = $n['name'];
            }
            list($where, $sort, $order, $offset, $limit) = $this->buildparams();

            $list = $this->model
                ->where($where)
                ->where('id', 'in', $this->childrenAdminIds)
                ->field(['password', 'salt', 'token'], true)
                ->order($sort, $order)
                ->paginate($limit);

            foreach ($list as $k => &$v) {
                $groups = isset($adminGroupName[$v['id']]) ? $adminGroupName[$v['id']] : [];
                $v['groups'] = implode(',', array_keys($groups));
                $v['groups_text'] = implode(',', array_values($groups));
            }
            unset($v);
            $result = array("total" => $list->total(), "rows" => $list->items());

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
            $params = $this->request->post("row/a");
            if ($params) {
                Db::startTrans();
                try {
                    if (!Validate::is($params['password'], '\S{6,30}')) {
                        exception(__("Please input correct password"));
                    }
                    $params['salt'] = Random::alnum();
                    $params['password'] = $this->auth->getEncryptPassword($params['password'], $params['salt']);
                    $params['avatar'] = '/assets/img/avatar.png'; //新規管理者のデフォルトアバターを設定。
                    $result = $this->model->validate('Admin.add')->save($params);
                    if ($result === false) {
                        exception($this->model->getError());
                    }
                    $group = $this->request->post("group/a");

                    //許可されていないグループをフィルタリング,権限の越権を防ぐ
                    $group = array_intersect($this->childrenGroupIds, $group);
                    if (!$group) {
                        exception(__('The parent group exceeds permission limit'));
                    }

                    $dataset = [];
                    foreach ($group as $value) {
                        $dataset[] = ['uid' => $this->model->id, 'group_id' => $value];
                    }
                    model('AuthGroupAccess')->saveAll($dataset);
                    Db::commit();
                } catch (\Exception $e) {
                    Db::rollback();
                    $this->error($e->getMessage());
                }
                $this->success();
            }
            $this->error(__('Parameter %s can not be empty', ''));
        }
        return $this->view->fetch();
    }

    /**
     * 編集
     */
    public function edit($ids = null)
    {
        $row = $this->model->get(['id' => $ids]);
        if (!$row) {
            $this->error(__('No Results were found'));
        }
        if (!in_array($row->id, $this->childrenAdminIds)) {
            $this->error(__('You have no permission'));
        }
        if ($this->request->isPost()) {
            $this->token();
            $params = $this->request->post("row/a");
            if ($params) {
                Db::startTrans();
                try {
                    if ($params['password']) {
                        if (!Validate::is($params['password'], '\S{6,30}')) {
                            exception(__("Please input correct password"));
                        }
                        $params['salt'] = Random::alnum();
                        $params['password'] = $this->auth->getEncryptPassword($params['password'], $params['salt']);
                    } else {
                        unset($params['password'], $params['salt']);
                    }
                    //ここではusernameとemail一意性チェックを行う必要があります
                    $adminValidate = \think\Loader::validate('Admin');
                    $adminValidate->rule([
                        'username' => 'require|regex:\w{3,30}|unique:admin,username,' . $row->id,
                        'email'    => 'require|email|unique:admin,email,' . $row->id,
                        'mobile'   => 'regex:1[3-9]\d{9}|unique:admin,mobile,' . $row->id,
                        'password' => 'regex:\S{32}',
                    ]);
                    $result = $row->validate('Admin.edit')->save($params);
                    if ($result === false) {
                        exception($row->getError());
                    }

                    // 先にすべての権限を削除
                    model('AuthGroupAccess')->where('uid', $row->id)->delete();

                    $group = $this->request->post("group/a");

                    // 許可されていないグループをフィルタリング,権限の越権を防ぐ
                    $group = array_intersect($this->childrenGroupIds, $group);
                    if (!$group) {
                        exception(__('The parent group exceeds permission limit'));
                    }

                    $dataset = [];
                    foreach ($group as $value) {
                        $dataset[] = ['uid' => $row->id, 'group_id' => $value];
                    }
                    model('AuthGroupAccess')->saveAll($dataset);
                    Db::commit();
                } catch (\Exception $e) {
                    Db::rollback();
                    $this->error($e->getMessage());
                }
                $this->success();
            }
            $this->error(__('Parameter %s can not be empty', ''));
        }
        $grouplist = $this->auth->getGroups($row['id']);
        $groupids = [];
        foreach ($grouplist as $k => $v) {
            $groupids[] = $v['id'];
        }
        $this->view->assign("row", $row);
        $this->view->assign("groupids", $groupids);
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
            $ids = array_intersect($this->childrenAdminIds, array_filter(explode(',', $ids)));
            // 越権による管理者削除を避ける
            $childrenGroupIds = $this->childrenGroupIds;
            $adminList = $this->model->where('id', 'in', $ids)->where('id', 'in', function ($query) use ($childrenGroupIds) {
                $query->name('auth_group_access')->where('group_id', 'in', $childrenGroupIds)->field('uid');
            })->select();
            if ($adminList) {
                $deleteIds = [];
                foreach ($adminList as $k => $v) {
                    $deleteIds[] = $v->id;
                }
                $deleteIds = array_values(array_diff($deleteIds, [$this->auth->id]));
                if ($deleteIds) {
                    Db::startTrans();
                    try {
                        $this->model->destroy($deleteIds);
                        model('AuthGroupAccess')->where('uid', 'in', $deleteIds)->delete();
                        Db::commit();
                    } catch (\Exception $e) {
                        Db::rollback();
                        $this->error($e->getMessage());
                    }
                    $this->success();
                }
                $this->error(__('No rows were deleted'));
            }
        }
        $this->error(__('You have no permission'));
    }

    /**
     * 一括更新
     * @internal
     */
    public function multi($ids = "")
    {
        // 管理者は一括操作を禁止
        $this->error();
    }

    /**
     * ドロップダウン検索
     */
    public function selectpage()
    {
        $this->dataLimit = 'auth';
        $this->dataLimitField = 'id';
        return parent::selectpage();
    }
}
