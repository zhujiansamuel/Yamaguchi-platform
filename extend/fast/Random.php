<?php

namespace fast;

/**
 * ランダム生成クラス
 */
class Random
{

    /**
     * 数字と英字を生成
     *
     * @param int $len 長さ
     * @return string
     */
    public static function alnum(int $len = 6): string
    {
        return self::build('alnum', $len);
    }

    /**
     * 英字のみ生成
     *
     * @param int $len 長さ
     * @return string
     */
    public static function alpha(int $len = 6): string
    {
        return self::build('alpha', $len);
    }

    /**
     * 指定した長さのランダムな数字を生成
     *
     * @param int $len 長さ
     * @return string
     */
    public static function numeric(int $len = 4): string
    {
        return self::build('numeric', $len);
    }

    /**
     * 指定した長さの0ランダム数字
     *
     * @param int $len 長さ
     * @return string
     */
    public static function nozero(int $len = 4): string
    {
        return self::build('nozero', $len);
    }

    /**
     * 実用的な乱数生成
     * @param string $type タイプ alpha/alnum/numeric/nozero/unique/md5/encrypt/sha1
     * @param int    $len  長さ
     * @return string
     */
    public static function build(string $type = 'alnum', int $len = 8): string
    {
        switch ($type) {
            case 'alpha':
            case 'alnum':
            case 'numeric':
            case 'nozero':
                switch ($type) {
                    case 'alpha':
                        $pool = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
                        break;
                    case 'alnum':
                        $pool = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
                        break;
                    case 'numeric':
                        $pool = '0123456789';
                        break;
                    case 'nozero':
                        $pool = '123456789';
                        break;
                }
                return substr(str_shuffle(str_repeat($pool, ceil($len / strlen($pool)))), 0, $len);
            case 'unique':
            case 'md5':
                return md5(uniqid(mt_rand()));
            case 'encrypt':
            case 'sha1':
                return sha1(uniqid(mt_rand(), true));
        }
    }

    /**
     * グローバル一意識別子を取得
     * @return string
     */
    public static function uuid(): string
    {
        return sprintf(
            '%04x%04x-%04x-%04x-%04x-%04x%04x%04x',
            mt_rand(0, 0xffff),
            mt_rand(0, 0xffff),
            mt_rand(0, 0xffff),
            mt_rand(0, 0x0fff) | 0x4000,
            mt_rand(0, 0x3fff) | 0x8000,
            mt_rand(0, 0xffff),
            mt_rand(0, 0xffff),
            mt_rand(0, 0xffff)
        );
    }
}
