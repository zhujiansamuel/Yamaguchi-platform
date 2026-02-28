<?php

declare(strict_types=1);

namespace Yansongda\Pay\Plugin\Alipay\Fund;

use Closure;
use Yansongda\Pay\Contract\PluginInterface;
use Yansongda\Pay\Logger;
use Yansongda\Pay\Rocket;

/**
 * @see https://opendocs.alipay.com/open/02byuo?scene=common
 */
class TransUniTransferPlugin implements PluginInterface
{
    public function assembly(Rocket $rocket, Closure $next): Rocket
    {
        Logger::debug('[alipay][TransUniTransferPlugin] プラグインの読み込みを開始', ['rocket' => $rocket]);

        $rocket->mergePayload([
            'method' => 'alipay.fund.trans.uni.transfer',
            'biz_content' => array_merge(
                [
                    'biz_scene' => 'DIRECT_TRANSFER',
                    'product_code' => 'TRANS_ACCOUNT_NO_PWD',
                ],
                $rocket->getParams(),
            ),
        ]);

        Logger::info('[alipay][TransUniTransferPlugin] プラグインの読み込み完了', ['rocket' => $rocket]);

        return $next($rocket);
    }
}
