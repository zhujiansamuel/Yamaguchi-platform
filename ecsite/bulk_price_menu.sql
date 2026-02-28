-- 批量价格管理菜单添加SQL
-- 执行此SQL可将批量价格管理菜单添加到后台管理系统

-- 首先获取商品管理的ID（假设商品管理的name是'goods'）
-- 然后插入批量价格管理菜单项

INSERT INTO `fa_auth_rule` (`pid`, `name`, `title`, `type`, `status`, `condition`, `menu`, `weigh`, `icon`, `remark`, `ismenu`, `createtime`, `updatetime`)
SELECT
    `id` as pid,
    'goods/bulkprice' as name,
    '批量价格管理' as title,
    'menu' as type,
    'normal' as status,
    '' as `condition`,
    '{"type":"button","icon":"fa fa-money","color":""}' as menu,
    0 as weigh,
    'fa fa-money' as icon,
    '批量管理所有商品价格' as remark,
    1 as ismenu,
    UNIX_TIMESTAMP() as createtime,
    UNIX_TIMESTAMP() as updatetime
FROM `fa_auth_rule`
WHERE `name` = 'goods'
LIMIT 1;

-- 添加批量更新接口权限（不显示在菜单中）
INSERT INTO `fa_auth_rule` (`pid`, `name`, `title`, `type`, `status`, `condition`, `menu`, `weigh`, `icon`, `remark`, `ismenu`, `createtime`, `updatetime`)
SELECT
    `id` as pid,
    'goods/bulkupdate' as name,
    '批量更新价格接口' as title,
    'file' as type,
    'normal' as status,
    '' as `condition`,
    '' as menu,
    0 as weigh,
    '' as icon,
    '批量更新商品价格的API接口' as remark,
    0 as ismenu,
    UNIX_TIMESTAMP() as createtime,
    UNIX_TIMESTAMP() as updatetime
FROM `fa_auth_rule`
WHERE `name` = 'goods'
LIMIT 1;
