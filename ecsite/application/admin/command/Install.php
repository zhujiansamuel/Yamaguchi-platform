<?php

namespace app\admin\command;

use fast\Random;
use PDO;
use think\Config;
use think\console\Command;
use think\console\Input;
use think\console\input\Option;
use think\console\Output;
use think\Db;
use think\Exception;
use think\Lang;
use think\Request;
use think\View;

class Install extends Command
{

    /**
     * 最低PHPバージョン
     * @var string
     */
    protected $minPhpVersion = '7.4.0';

    protected $model = null;
    /**
     * @var \think\View ビュークラスインスタンス
     */
    protected $view;

    /**
     * @var \think\Request Request インスタンス
     */
    protected $request;

    protected function configure()
    {
        $config = Config::get('database');
        $this
            ->setName('install')
            ->addOption('hostname', 'a', Option::VALUE_OPTIONAL, 'mysql hostname', $config['hostname'])
            ->addOption('hostport', 'o', Option::VALUE_OPTIONAL, 'mysql hostport', $config['hostport'])
            ->addOption('database', 'd', Option::VALUE_OPTIONAL, 'mysql database', $config['database'])
            ->addOption('prefix', 'r', Option::VALUE_OPTIONAL, 'table prefix', $config['prefix'])
            ->addOption('username', 'u', Option::VALUE_OPTIONAL, 'mysql username', $config['username'])
            ->addOption('password', 'p', Option::VALUE_OPTIONAL, 'mysql password', $config['password'])
            ->addOption('force', 'f', Option::VALUE_OPTIONAL, 'force override', false)
            ->setDescription('New installation of FastAdmin');
    }

    /**
     * コマンドラインインストール
     */
    protected function execute(Input $input, Output $output)
    {
        define('INSTALL_PATH', APP_PATH . 'admin' . DS . 'command' . DS . 'Install' . DS);
        // 上書きインストール
        $force = $input->getOption('force');
        $hostname = $input->getOption('hostname');
        $hostport = $input->getOption('hostport');
        $database = $input->getOption('database');
        $prefix = $input->getOption('prefix');
        $username = $input->getOption('username');
        $password = $input->getOption('password');

        $installLockFile = INSTALL_PATH . "install.lock";
        if (is_file($installLockFile) && !$force) {
            throw new Exception("\nFastAdmin already installed!\nIf you need to reinstall again, use the parameter --force=true ");
        }

        $adminUsername = 'admin';
        $adminPassword = Random::alnum(10);
        $adminEmail = 'admin@admin.com';
        $siteName = __('My Website');

        $adminName = $this->installation($hostname, $hostport, $database, $username, $password, $prefix, $adminUsername, $adminPassword, $adminEmail, $siteName);
        if ($adminName) {
            $output->highlight("Admin url:https://www.example.com/{$adminName}");
        }

        $output->highlight("Admin username:{$adminUsername}");
        $output->highlight("Admin password:{$adminPassword}");

        \think\Cache::rm('__menu__');

        $output->info("Install Successed!");
    }

    /**
     * PCPC 版インストール
     */
    public function index()
    {
        $this->view = View::instance(array_merge(Config::get('template'), ['tpl_cache' => false]));
        $this->request = Request::instance();

        define('INSTALL_PATH', APP_PATH . 'admin' . DS . 'command' . DS . 'Install' . DS);

        $lang = $this->request->langset();
        $lang = preg_match("/^([a-zA-Z\-_]{2,10})\$/i", $lang) ? $lang : 'zh-cn';

        if (!$lang || in_array($lang, ['zh-cn', 'zh-hans-cn'])) {
            Lang::load(INSTALL_PATH . 'zh-cn.php');
        }

        $installLockFile = INSTALL_PATH . "install.lock";

        if (is_file($installLockFile)) {
            echo __('The system has been installed. If you need to reinstall, please remove %s first', 'install.lock');
            exit;
        }
        $output = function ($code, $msg, $url = null, $data = null) {
            return json(['code' => $code, 'msg' => $msg, 'url' => $url, 'data' => $data]);
        };

        if ($this->request->isPost()) {
            $mysqlHostname = $this->request->post('mysqlHostname', '127.0.0.1');
            $mysqlHostport = $this->request->post('mysqlHostport', '3306');
            $hostArr = explode(':', $mysqlHostname);
            if (count($hostArr) > 1) {
                $mysqlHostname = $hostArr[0];
                $mysqlHostport = $hostArr[1];
            }
            $mysqlUsername = $this->request->post('mysqlUsername', 'root');
            $mysqlPassword = $this->request->post('mysqlPassword', '');
            $mysqlDatabase = $this->request->post('mysqlDatabase', '');
            $mysqlPrefix = $this->request->post('mysqlPrefix', 'fa_');
            $adminUsername = $this->request->post('adminUsername', 'admin');
            $adminPassword = $this->request->post('adminPassword', '');
            $adminPasswordConfirmation = $this->request->post('adminPasswordConfirmation', '');
            $adminEmail = $this->request->post('adminEmail', 'admin@admin.com');
            $siteName = $this->request->post('siteName', __('My Website'));

            if ($adminPassword !== $adminPasswordConfirmation) {
                return $output(0, __('The two passwords you entered did not match'));
            }

            $adminName = '';
            try {
                $adminName = $this->installation($mysqlHostname, $mysqlHostport, $mysqlDatabase, $mysqlUsername, $mysqlPassword, $mysqlPrefix, $adminUsername, $adminPassword, $adminEmail, $siteName);
            } catch (\PDOException $e) {
                throw new Exception($e->getMessage());
            } catch (\Exception $e) {
                return $output(0, $e->getMessage());
            }
            return $output(1, __('Install Successed'), null, ['adminName' => $adminName]);
        }
        $errInfo = '';
        try {
            $this->checkenv();
        } catch (\Exception $e) {
            $errInfo = $e->getMessage();
        }
        return $this->view->fetch(INSTALL_PATH . "install.html", ['errInfo' => $errInfo]);
    }

    /**
     * インストールを実行
     */
    protected function installation($mysqlHostname, $mysqlHostport, $mysqlDatabase, $mysqlUsername, $mysqlPassword, $mysqlPrefix, $adminUsername, $adminPassword, $adminEmail = null, $siteName = null)
    {
        $this->checkenv();

        if ($mysqlDatabase == '') {
            throw new Exception(__('Please input correct database'));
        }
        if (!preg_match("/^\w{3,12}$/", $adminUsername)) {
            throw new Exception(__('Please input correct username'));
        }
        if (!preg_match("/^[\S]{6,16}$/", $adminPassword)) {
            throw new Exception(__('Please input correct password'));
        }
        $weakPasswordArr = ['123456', '12345678', '123456789', '654321', '111111', '000000', 'password', 'qwerty', 'abc123', '1qaz2wsx'];
        if (in_array($adminPassword, $weakPasswordArr)) {
            throw new Exception(__('Password is too weak'));
        }
        if ($siteName == '' || preg_match("/fast" . "admin/i", $siteName)) {
            throw new Exception(__('Please input correct website'));
        }

        $sql = file_get_contents(INSTALL_PATH . 'fastadmin.sql');

        $sql = str_replace("`fa_", "`{$mysqlPrefix}", $sql);

        // まず自動でデータベースを作成できるか試行
        $config = Config::get('database');
        try {
            $pdo = new PDO("{$config['type']}:host={$mysqlHostname}" . ($mysqlHostport ? ";port={$mysqlHostport}" : ''), $mysqlUsername, $mysqlPassword);
            $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
            $pdo->query("CREATE DATABASE IF NOT EXISTS `{$mysqlDatabase}` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;");

            // 接続installinstall コマンドで指定されたデータベースに接続
            $instance = Db::connect([
                'type'     => "{$config['type']}",
                'hostname' => "{$mysqlHostname}",
                'hostport' => "{$mysqlHostport}",
                'database' => "{$mysqlDatabase}",
                'username' => "{$mysqlUsername}",
                'password' => "{$mysqlPassword}",
                'prefix'   => "{$mysqlPrefix}",
            ]);

            // 一度クエリを実行SQL,接続が正常かどうかを判定
            $instance->execute("SELECT 1");

            // ネイティブPDOオブジェクトを呼び出して一括クエリを実行
            $instance->getPdo()->exec($sql);
        } catch (\PDOException $e) {
            throw new Exception($e->getMessage());
        }
        // バックエンドエントリーファイル
        $adminFile = ROOT_PATH . 'public' . DS . 'admin.php';

        // データベース設定ファイル
        $envSampleFile = ROOT_PATH . '.env.sample';
        $envFile = ROOT_PATH . '.env';
        if (!file_exists($envFile)) {
            if (!copy($envSampleFile, $envFile)) {
                throw new Exception(__('Failed to copy %s to %s', '.env.sample', '.env'));
            }
        }

        $envText = @file_get_contents($envFile);

        $callback = function ($matches) use ($mysqlHostname, $mysqlHostport, $mysqlUsername, $mysqlPassword, $mysqlDatabase, $mysqlPrefix) {
            $field = "mysql" . ucfirst($matches[1]);
            $replace = $$field;
            return "{$matches[1]} = {$replace}";
        };
        $envText = preg_replace_callback("/(hostname|database|username|password|hostport|prefix)\s*=\s*(.*)/", $callback, $envText);

        // データベース設定を書き込めるかどうかを検査
        $result = @file_put_contents($envFile, $envText);
        if (!$result) {
            throw new Exception(__('The current permissions are insufficient to write the file %s', '.env'));
        }

        // 新しい設定Tokenランダムキーkey
        $oldTokenKey = config('token.key');
        $newTokenKey = \fast\Random::alnum(32);
        $coreConfigFile = CONF_PATH . 'config.php';
        $coreConfigText = @file_get_contents($coreConfigFile);
        $coreConfigText = preg_replace("/'key'(\s+)=>(\s+)'{$oldTokenKey}'/", "'key'\$1=>\$2'{$newTokenKey}'", $coreConfigText);

        $result = @file_put_contents($coreConfigFile, $coreConfigText);
        if (!$result) {
            throw new Exception(__('The current permissions are insufficient to write the file %s', 'application/config.php'));
        }

        $avatar = '/assets/img/avatar.png';
        // デフォルト管理者パスワードを変更
        $adminPassword = $adminPassword ? $adminPassword : Random::alnum(8);
        $adminEmail = $adminEmail ? $adminEmail : "admin@admin.com";
        $newSalt = substr(md5(uniqid(true)), 0, 6);
        $newPassword = md5(md5($adminPassword) . $newSalt);
        $data = ['username' => $adminUsername, 'email' => $adminEmail, 'avatar' => $avatar, 'password' => $newPassword, 'salt' => $newSalt];
        $instance->name('admin')->where('username', 'admin')->update($data);

        // フロントエンドのデフォルトユーザーパスワードを変更,ランダム生成
        $newSalt = substr(md5(uniqid(true)), 0, 6);
        $newPassword = md5(md5(Random::alnum(8)) . $newSalt);
        $instance->name('user')->where('username', 'admin')->update(['avatar' => $avatar, 'password' => $newPassword, 'salt' => $newSalt]);

        // 管理画面のエントリを変更
        $adminName = '';
        if (is_file($adminFile)) {
            $adminName = Random::alpha(10) . '.php';
            rename($adminFile, ROOT_PATH . 'public' . DS . $adminName);
        }

        //サイト名を変更
        if ($siteName != config('site.name')) {
            $instance->name('config')->where('name', 'name')->update(['value' => $siteName]);
            $siteConfigFile = CONF_PATH . 'extra' . DS . 'site.php';
            $siteConfig = include $siteConfigFile;
            $configList = $instance->name("config")->select();
            foreach ($configList as $k => $value) {
                if (in_array($value['type'], ['selects', 'checkbox', 'images', 'files'])) {
                    $value['value'] = is_array($value['value']) ? $value['value'] : explode(',', $value['value']);
                }
                if ($value['type'] == 'array') {
                    $value['value'] = (array)json_decode($value['value'], true);
                }
                $siteConfig[$value['name']] = $value['value'];
            }
            $siteConfig['name'] = $siteName;
            file_put_contents($siteConfigFile, '<?php' . "\n\nreturn " . var_export_short($siteConfig) . ";\n");
        }

        $installLockFile = INSTALL_PATH . "install.lock";
        //正常に書き込めるかをチェックlockファイル
        $result = @file_put_contents($installLockFile, 1);
        if (!$result) {
            throw new Exception(__('The current permissions are insufficient to write the file %s', 'application/admin/command/Install/install.lock'));
        }

        try {
            //インストールスクリプトを削除
            @unlink(ROOT_PATH . 'public' . DS . 'install.php');
        } catch (\Exception $e) {

        }

        return $adminName;
    }

    /**
     * 環境をチェック
     */
    protected function checkenv()
    {
        // ディレクトリが存在するかをチェック
        $checkDirs = [
            'thinkphp',
            'vendor',
            'public' . DS . 'assets' . DS . 'libs'
        ];

        //データベース設定ファイル
        $dbConfigFile = APP_PATH . 'database.php';

        if (version_compare(PHP_VERSION, $this->minPhpVersion, '<')) {
            throw new Exception(__("The current PHP %s is too low, please use PHP %s or higher", PHP_VERSION, $this->minPhpVersion));
        }
        if (!extension_loaded("PDO")) {
            throw new Exception(__("PDO is not currently installed and cannot be installed"));
        }
        if (!is_really_writable($dbConfigFile)) {
            throw new Exception(__('The current permissions are insufficient to write the configuration file application/database.php'));
        }
        foreach ($checkDirs as $k => $v) {
            if (!is_dir(ROOT_PATH . $v)) {
                throw new Exception(__('Please go to the official website to download the full package or resource package and try to install'));
                break;
            }
        }
        return true;
    }
}
