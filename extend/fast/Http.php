<?php

namespace fast;

/**
 * Http リクエストクラス
 */
class Http
{

    /**
     * 1件のPOSTリクエスト
     * @param string $url     リクエストURL
     * @param array  $params  リクエストパラメータ
     * @param array  $options 拡張パラメータ
     * @return mixed|string
     */
    public static function post($url, $params = [], $options = [])
    {
        $req = self::sendRequest($url, $params, 'POST', $options);
        return $req['ret'] ? $req['msg'] : '';
    }

    /**
     * 1件のGETリクエスト
     * @param string $url     リクエストURL
     * @param array  $params  リクエストパラメータ
     * @param array  $options 拡張パラメータ
     * @return mixed|string
     */
    public static function get($url, $params = [], $options = [])
    {
        $req = self::sendRequest($url, $params, 'GET', $options);
        return $req['ret'] ? $req['msg'] : '';
    }

    /**
     * CURL送信Requestリクエスト,を含むPOSTとREQUEST
     * @param string $url     リクエスト先のリンク
     * @param mixed  $params  送信するパラメータ
     * @param string $method  リクエストメソッド
     * @param mixed  $options CURLのパラメータ
     * @return array
     */
    public static function sendRequest($url, $params = [], $method = 'POST', $options = [])
    {
        $method = strtoupper($method);
        $protocol = substr($url, 0, 5);
        $query_string = is_array($params) ? http_build_query($params) : $params;

        $ch = curl_init();
        $defaults = [];
        if ('GET' == $method) {
            $geturl = $query_string ? $url . (stripos($url, "?") !== false ? "&" : "?") . $query_string : $url;
            $defaults[CURLOPT_URL] = $geturl;
        } else {
            $defaults[CURLOPT_URL] = $url;
            if ($method == 'POST') {
                $defaults[CURLOPT_POST] = 1;
            } else {
                $defaults[CURLOPT_CUSTOMREQUEST] = $method;
            }
            $defaults[CURLOPT_POSTFIELDS] = is_array($params) && count(array_filter($params, 'is_array')) > 0 ? $query_string : $params;
        }

        $defaults[CURLOPT_HEADER] = false;
        $defaults[CURLOPT_USERAGENT] = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.98 Safari/537.36";
        $defaults[CURLOPT_FOLLOWLOCATION] = true;
        $defaults[CURLOPT_RETURNTRANSFER] = true;
        $defaults[CURLOPT_CONNECTTIMEOUT] = 10;
        $defaults[CURLOPT_TIMEOUT] = 10;

        // disable 100-continue
        curl_setopt($ch, CURLOPT_HTTPHEADER, array('Expect:'));

        if ('https' == $protocol) {
            $defaults[CURLOPT_SSL_VERIFYPEER] = false;
            $defaults[CURLOPT_SSL_VERIFYHOST] = false;
        }

        curl_setopt_array($ch, (array)$options + $defaults);

        $ret = curl_exec($ch);
        $err = curl_error($ch);

        if (false === $ret || !empty($err)) {
            $errno = curl_errno($ch);
            $info = curl_getinfo($ch);
            curl_close($ch);
            return [
                'ret'   => false,
                'errno' => $errno,
                'msg'   => $err,
                'info'  => $info,
            ];
        }
        curl_close($ch);
        return [
            'ret' => true,
            'msg' => $ret,
        ];
    }

    /**
     * 非同期でリクエストを送信
     * @param string $url    リクエスト先のリンク
     * @param mixed  $params リクエストのパラメータ
     * @param string $method リクエストメソッド
     * @return boolean TRUE
     */
    public static function sendAsyncRequest($url, $params = [], $method = 'POST')
    {
        $method = strtoupper($method);
        $method = $method == 'POST' ? 'POST' : 'GET';
        //送信パラメータを構築
        if (is_array($params)) {
            $post_params = [];
            foreach ($params as $k => &$v) {
                if (is_array($v)) {
                    $v = implode(',', $v);
                }
                $post_params[] = $k . '=' . urlencode($v);
            }
            $post_string = implode('&', $post_params);
        } else {
            $post_string = $params;
        }
        $parts = parse_url($url);
        //クエリパラメータを構築
        if ($method == 'GET' && $post_string) {
            $parts['query'] = isset($parts['query']) ? $parts['query'] . '&' . $post_string : $post_string;
            $post_string = '';
        }
        $parts['query'] = isset($parts['query']) && $parts['query'] ? '?' . $parts['query'] : '';
        //送信socketリクエスト,接続ハンドルを取得
        $fp = fsockopen($parts['host'], $parts['port'] ?? 80, $errno, $errstr, 10);
        if (!$fp) {
            return false;
        }
        //タイムアウト時間を設定
        stream_set_timeout($fp, 10);
        $out = "{$method} {$parts['path']}{$parts['query']} HTTP/1.1\r\n";
        $out .= "Host: {$parts['host']}\r\n";
        $out .= "Content-Type: application/x-www-form-urlencoded\r\n";
        $out .= "Content-Length: " . strlen($post_string) . "\r\n";
        $out .= "Connection: Close\r\n\r\n";
        if ($post_string !== '') {
            $out .= $post_string;
        }
        fwrite($fp, $out);
        //サーバーからのレスポンス結果を気にしない
        //echo fread($fp, 1024);
        fclose($fp);
        return true;
    }

    /**
     * ファイルをクライアントに送信
     * @param string $file
     * @param bool   $delaftersend
     * @param bool   $exitaftersend
     */
    public static function sendToBrowser($file, $delaftersend = true, $exitaftersend = true)
    {
        if (file_exists($file) && is_readable($file)) {
            header('Content-Description: File Transfer');
            header('Content-Type: application/octet-stream');
            header('Content-Disposition: attachment;filename = ' . basename($file));
            header('Content-Transfer-Encoding: binary');
            header('Expires: 0');
            header('Cache-Control: must-revalidate, post-check = 0, pre-check = 0');
            header('Pragma: public');
            header('Content-Length: ' . filesize($file));
            ob_clean();
            flush();
            readfile($file);
            if ($delaftersend) {
                unlink($file);
            }
            if ($exitaftersend) {
                exit;
            }
        }
    }
}
