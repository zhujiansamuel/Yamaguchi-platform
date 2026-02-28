<?php

namespace app\common\model;

use think\Db;
use think\Model;

/**
 * 会員モデル
 * @method static mixed getByUsername($str) ユーザー名でユーザーを検索
 * @method static mixed getByNickname($str) ニックネームでユーザーを検索
 * @method static mixed getByMobile($str) 携帯番号でユーザーを検索
 * @method static mixed getByEmail($str) メールアドレスでユーザーを検索
 */
class User extends Model
{

    // 自動タイムスタンプ書き込みを有効にする
    protected $autoWriteTimestamp = 'int';
    // タイムスタンプフィールド名を定義
    protected $createTime = 'createtime';
    protected $updateTime = 'updatetime';
    // 追加属性
    protected $append = [
        'url',
    ];

    /**
     * 個人情報を取得URL
     * @param string $value
     * @param array  $data
     * @return string
     */
    public function getUrlAttr($value, $data)
    {
        return "/u/" . $data['id'];
    }

    /**
     * アバターを取得
     * @param string $value
     * @param array  $data
     * @return string
     */
    public function getAvatarAttr($value, $data)
    {
        if($value){
            return getDomainName($value,'avatar');
        }
        return $value;
    }

    /**
     * 会員のグループを取得
     */
    public function getGroupAttr($value, $data)
    {
        return UserGroup::get($data['group_id']);
    }

    /**
     * 認証フィールドの配列値を取得
     * @param string $value
     * @param array  $data
     * @return  object
     */
    public function getVerificationAttr($value, $data)
    {
        $value = array_filter((array)json_decode($value, true));
        $value = array_merge(['email' => 0, 'mobile' => 0], $value);
        return (object)$value;
    }

    /**
     * 認証フィールドを設定
     * @param mixed $value
     * @return string
     */
    public function setVerificationAttr($value)
    {
        $value = is_object($value) || is_array($value) ? json_encode($value) : $value;
        return $value;
    }

    /**
     * 会員残高を変更
     * @param int    $money   残高
     * @param int    $user_id 会員ID
     * @param string $memo    備考
     */
    public static function money($money, $user_id, $memo)
    {
        Db::startTrans();
        try {
            $user = self::lock(true)->find($user_id);
            if ($user && $money != 0) {
                $before = $user->money;
                //$after = $user->money + $money;
                $after = function_exists('bcadd') ? bcadd($user->money, $money, 2) : $user->money + $money;
                //会員情報を更新
                $user->save(['money' => $after]);
                //ログに書き込む
                MoneyLog::create(['user_id' => $user_id, 'money' => $money, 'before' => $before, 'after' => $after, 'memo' => $memo]);
            }
            Db::commit();
        } catch (\Exception $e) {
            Db::rollback();
        }
    }

    /**
     * 会員ポイントを変更
     * @param int    $score   ポイント
     * @param int    $user_id 会員ID
     * @param string $memo    備考
     */
    public static function score($score, $user_id, $memo)
    {
        Db::startTrans();
        try {
            $user = self::lock(true)->find($user_id);
            if ($user && $score != 0) {
                $before = $user->score;
                $after = $user->score + $score;
                $level = self::nextlevel($after);
                //会員情報を更新
                $user->save(['score' => $after, 'level' => $level]);
                //ログに書き込む
                ScoreLog::create(['user_id' => $user_id, 'score' => $score, 'before' => $before, 'after' => $after, 'memo' => $memo]);
            }
            Db::commit();
        } catch (\Exception $e) {
            Db::rollback();
        }
    }

    /**
     * ポイントに応じてランクを取得
     * @param int $score ポイント
     * @return int
     */
    public static function nextlevel($score = 0)
    {
        $lv = array(1 => 0, 2 => 30, 3 => 100, 4 => 500, 5 => 1000, 6 => 2000, 7 => 3000, 8 => 5000, 9 => 8000, 10 => 10000);
        $level = 1;
        foreach ($lv as $key => $value) {
            if ($score >= $value) {
                $level = $key;
            }
        }
        return $level;
    }
}
