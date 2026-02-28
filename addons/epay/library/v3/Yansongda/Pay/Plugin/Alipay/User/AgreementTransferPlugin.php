<?php

declare(strict_types=1);

namespace Yansongda\Pay\Plugin\Alipay\User;

use Closure;
use Yansongda\Pay\Contract\PluginInterface;
use Yansongda\Pay\Logger;
use Yansongda\Pay\Rocket;

/**
 * @see https://opendocs.alipay.com/open/02fkar?ref=api
 */
class AgreementTransferPlugin implements PluginInterface
{
    public function assembly(Rocket $rocket, Closure $next): Rocket
    {
        Logger::debug('[alipay][AgreementTransferPlugin] プラグインの読み込みを開始', ['rocket' => $rocket]);

        $rocket->mergePayload([
            'method' => 'alipay.user.agreement.transfer',
            'biz_content' => array_merge(
                ['target_product_code' => 'CYCLE_PAY_AUTH_P'],
                $rocket->getParams()
            ),
        ]);

        Logger::info('[alipay][AgreementTransferPlugin] プラグインの読み込み完了', ['rocket' => $rocket]);

        return $next($rocket);
    }
}
