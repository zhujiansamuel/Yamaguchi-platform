<?php

namespace app\common\library;

use think\Config;
use Tx\Mailer;
use Tx\Mailer\Exceptions\CodeException;
use Tx\Mailer\Exceptions\SendException;

class Email
{

    /**
     * シングルトンオブジェクト
     */
    protected static $instance;

    /**
     * phpmailerオブジェクト
     */
    protected $mail = null;

    /**
     * エラー内容
     */
    protected $error = '';

    /**
     * メールデータ（mail()フォールバック用）
     */
    protected $toAddresses = [];
    protected $fromEmail = '';
    protected $fromName = '';
    protected $subjectText = '';
    protected $bodyText = '';

    /**
     * SMTP初期化が成功したかどうか
     */
    protected $smtpReady = false;

    /**
     * デフォルト設定
     */
    public $options = [
        'charset'   => 'utf-8', //エンコード形式
        'debug'     => false, //デバッグモード
        'mail_type' => 0, //ステータス
    ];

    /**
     * 初期化
     * @access public
     * @param array $options パラメーター
     * @return Email
     */
    public static function instance($options = [])
    {
        if (is_null(self::$instance)) {
            self::$instance = new static($options);
        }

        return self::$instance;
    }

    /**
     * コンストラクタ
     * @param array $options
     */
    public function __construct($options = [])
    {
        if ($config = Config::get('site')) {
            $this->options = array_merge($this->options, $config);
        }
        $this->options = array_merge($this->options, $options);

        try {
            $secureArr = [0 => '', 1 => 'tls', 2 => 'ssl'];
            $secure = $secureArr[$this->options['mail_verify_type']] ?? '';

            $logger = isset($this->options['debug']) && $this->options['debug'] ? new Log : null;
            $this->mail = new Mailer($logger);
            $this->mail->setServer($this->options['mail_smtp_host'], $this->options['mail_smtp_port'], $secure);
            $this->mail->setAuth($this->options['mail_from'], $this->options['mail_smtp_pass']);
            $this->smtpReady = true;
        } catch (\Exception $e) {
            \think\Log::error('[Email] SMTP初期化失敗: ' . $e->getMessage());
            $this->smtpReady = false;
        }

        //送信者を設定
        $this->fromEmail = $this->options['mail_from'];
        $this->fromName = $this->options['mail_smtp_user'];
        if ($this->smtpReady) {
            $this->mail->setFrom($this->fromName, $this->fromEmail);
        }
    }

    /**
     * メール件名を設定
     * @param string $subject メール件名
     * @return $this
     */
    public function subject($subject)
    {
        $this->subjectText = $subject;
        if ($this->smtpReady) {
            $this->mail->setSubject($subject);
        }
        return $this;
    }

    /**
     * 送信者を設定
     * @param string $email 送信元メールアドレス
     * @param string $name  送信者名
     * @return $this
     */
    public function from($email, $name = '')
    {
        $this->fromEmail = $email;
        $this->fromName = $name;
        if ($this->smtpReady) {
            $this->mail->setFrom($name, $email);
        }
        return $this;
    }

    /**
     * 受信者を設定
     * @param mixed $email 受信者,多个受信者以,で区切る
     * @return $this
     */
    public function to($email)
    {
        $emailArr = $this->buildAddress($email);
        $this->toAddresses = $emailArr;
        if ($this->smtpReady) {
            foreach ($emailArr as $address => $name) {
                $this->mail->addTo($name, $address);
            }
        }

        return $this;
    }

    /**
     * Cc を設定
     * @param mixed  $email 受信者,多个受信者以,で区切る
     * @param string $name  受信者名
     * @return Email
     */
    public function cc($email, $name = '')
    {
        $emailArr = $this->buildAddress($email);
        if (count($emailArr) == 1 && $name) {
            $emailArr[key($emailArr)] = $name;
        }
        if ($this->smtpReady) {
            foreach ($emailArr as $address => $name) {
                $this->mail->addCC($name, $address);
            }
        }
        return $this;
    }

    /**
     * Bcc を設定
     * @param mixed  $email 受信者,多个受信者以,で区切る
     * @param string $name  受信者名
     * @return Email
     */
    public function bcc($email, $name = '')
    {
        $emailArr = $this->buildAddress($email);
        if (count($emailArr) == 1 && $name) {
            $emailArr[key($emailArr)] = $name;
        }
        if ($this->smtpReady) {
            foreach ($emailArr as $address => $name) {
                $this->mail->addBCC($name, $address);
            }
        }
        return $this;
    }

    /**
     * メール本文を設定
     * @param string  $body   メール下部
     * @param boolean $ishtml かどうかHTML形式
     * @return $this
     */
    public function message($body, $ishtml = true)
    {
        $this->bodyText = $body;
        if ($this->smtpReady) {
            $this->mail->setBody($body);
        }
        return $this;
    }

    /**
     * 添付ファイルを追加
     * @param string $path 添付ファイルパス
     * @param string $name 添付ファイル名
     * @return Email
     */
    public function attachment($path, $name = '')
    {
        if ($this->smtpReady) {
            $this->mail->addAttachment($name, $path);
        }
        return $this;
    }

    /**
     * ビルドEmailアドレス
     * @param mixed $emails Emailデータ
     * @return array
     */
    protected function buildAddress($emails)
    {
        if (!is_array($emails)) {
            $emails = array_flip(explode(',', str_replace(";", ",", $emails)));
            foreach ($emails as $key => $value) {
                $emails[$key] = strstr($key, '@', true);
            }
        }
        return $emails;
    }

    /**
     * 最後に発生したエラーを取得
     * @return string
     */
    public function getError()
    {
        return $this->error;
    }

    /**
     * エラーを設定
     * @param string $error メッセージ情報
     */
    protected function setError($error)
    {
        $this->error = $error;
    }

    /**
     * PHP mail()関数でメール送信（フォールバック）
     * @return boolean
     */
    protected function sendByPhpMail()
    {
        try {
            if (empty($this->toAddresses)) {
                $this->setError('宛先が設定されていません');
                return false;
            }

            $to = implode(',', array_keys($this->toAddresses));
            $subject = mb_encode_mimeheader($this->subjectText, 'UTF-8');
            $body = $this->bodyText;

            $headers = [];
            $headers[] = 'MIME-Version: 1.0';
            $headers[] = 'Content-type: text/html; charset=UTF-8';
            if ($this->fromName) {
                $headers[] = 'From: ' . mb_encode_mimeheader($this->fromName, 'UTF-8') . ' <' . $this->fromEmail . '>';
            } else {
                $headers[] = 'From: ' . $this->fromEmail;
            }
            $headers[] = 'X-Mailer: PHP/' . phpversion();

            $result = @mail($to, $subject, $body, implode("\r\n", $headers), '-f' . $this->fromEmail);

            if (!$result) {
                $this->setError('PHP mail()関数の送信に失敗しました');
            }
            return $result;
        } catch (\Exception $e) {
            $this->setError('mail()例外: ' . $e->getMessage());
            \think\Log::error('[Email] mail()フォールバック失敗: ' . $e->getMessage());
            return false;
        }
    }

    /**
     * メール送信
     * @return boolean
     */
    public function send()
    {
        $result = false;
        if (in_array($this->options['mail_type'], [1, 2])) {
            // SMTP送信を試行
            if ($this->smtpReady) {
                try {
                    $result = $this->mail->send();
                } catch (SendException $e) {
                    $this->setError($e->getCode() . $e->getMessage());
                } catch (CodeException $e) {
                    preg_match_all("/Expected: (\d+)\, Got: (\d+)( \| (.*))?\$/i", $e->getMessage(), $matches);
                    $code = $matches[2][0] ?? 0;
                    $message = isset($matches[2][0]) && isset($matches[4][0]) ? $matches[4][0] : $e->getMessage();
                    $message = mb_convert_encoding($message, 'UTF-8', 'GBK,GB2312,BIG5');
                    $this->setError($message);
                } catch (\Exception $e) {
                    $this->setError($e->getMessage());
                }

                $this->setError($result ? '' : $this->getError());
            } else {
                $this->setError('SMTP初期化に失敗しました');
            }

            // SMTP送信失敗時、PHP mail()関数でフォールバック
            if (!$result) {
                $smtpError = $this->getError();
                \think\Log::warning('[Email] SMTP送信失敗 (' . $smtpError . ')、mail()でリトライします');

                $mailResult = $this->sendByPhpMail();
                if ($mailResult) {
                    \think\Log::info('[Email] mail()フォールバックで送信成功');
                    $this->setError('');
                    return true;
                } else {
                    $mailError = $this->getError();
                    $this->setError('SMTP: ' . $smtpError . ' / mail(): ' . $mailError);
                    \think\Log::error('[Email] 全送信方法が失敗: SMTP=' . $smtpError . ', mail()=' . $mailError);
                }
            }
        } else {
            //メール機能は無効になっています
            $this->setError(__('Mail already closed'));
        }
        return $result;
    }

}
