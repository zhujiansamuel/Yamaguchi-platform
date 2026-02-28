<?php

declare(strict_types=1);

namespace Yansongda\Pay\Plugin\Alipay\User;

use Closure;
use Yansongda\Pay\Contract\PluginInterface;
use Yansongda\Pay\Direction\ResponseDirection;
use Yansongda\Pay\Logger;
use Yansongda\Pay\Rocket;

/**
 * @see https://opendocs.alipay.com/open/02fkan?ref=api&scene=35
 */
class AgreementPageSignPlugin implements PluginInterface
{
    public function assembly(Rocket $rocket, Closure $next): Rocket
    {
        Logger::debug('[alipay][AgreementPageSignPlugin] プラグインの読み込みを開始', ['rocket' => $rocket]);

        $rocket->setDirection(ResponseDirection::class)
            ->mergePayload([
                'method' => 'alipay.user.agreement.page.sign',
                'biz_content' => array_merge(
                    ['product_code' => 'CYCLE_PAY_AUTH'],
                    $rocket->getParams()
                ),
            ])
        ;

        Logger::info('[alipay][AgreementPageSignPlugin] プラグインの読み込み完了', ['rocket' => $rocket]);

        return $next($rocket);
    }
}
