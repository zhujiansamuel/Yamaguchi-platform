-- 个人/法人双轨会员资料 - 数据库迁移
--
-- 执行方式 1（推荐）: 使用项目配置自动执行
--   cd /home/xs942548/mobile-zone.jp/public_html
--   chmod +x data/migrations/run_migration.sh
--   ./data/migrations/run_migration.sh
--
-- 执行方式 2: 手动指定参数（从 .env 获取 database/username/password）
--   mysql -h 127.0.0.1 -P 3306 -u 用户名 -p 数据库名 < data/migrations/personal_corporate_profile.sql
--
-- 执行方式 3: 使用 ThinkPHP 配置（application/database.php）
--   mysql -h $(grep hostname .env | cut -d= -f2) -P $(grep hostport .env | cut -d= -f2) -u $(grep username .env | cut -d= -f2) -p$(grep password .env | cut -d= -f2) $(grep database .env | cut -d= -f2) < data/migrations/personal_corporate_profile.sql
--

-- 1. fa_user 表新增字段 (若报 column exists 可跳过已存在的)
ALTER TABLE `fa_user` ADD COLUMN `profile_type_locked` tinyint(1) unsigned NOT NULL DEFAULT 0 COMMENT '类型锁定:0未锁定1已锁定';
ALTER TABLE `fa_user` ADD COLUMN `corporate_name` varchar(100) DEFAULT '' COMMENT '会社名';
ALTER TABLE `fa_user` ADD COLUMN `corporate_szb_1` int(10) unsigned NOT NULL DEFAULT 0 COMMENT '担当者本人確認書類种别';
ALTER TABLE `fa_user` ADD COLUMN `corporate_szb_image_1` text COMMENT '本人確認書類图片URL';
ALTER TABLE `fa_user` ADD COLUMN `corporate_szb_image_2` text COMMENT '適格請求書图片URL';
ALTER TABLE `fa_user` ADD COLUMN `corporate_szb_image_3` text COMMENT '名刺图片URL';

-- 2. 已有用户迁移: persion_type 已设则锁定
UPDATE `fa_user` SET `profile_type_locked` = 1 WHERE `persion_type` IN (1, 2);

-- 3. corporate_szb_1 category 数据 (基于个人書類)
INSERT INTO `fa_category` (`pid`, `type`, `name`, `nickname`, `flag`, `image`, `keywords`, `description`, `diyname`, `createtime`, `updatetime`, `weigh`, `status`) VALUES
(0, 'corporate_szb_1', '運転免許証のコピー', '', '', '', '', '', '', UNIX_TIMESTAMP(), UNIX_TIMESTAMP(), 100, 'normal'),
(0, 'corporate_szb_1', '個人番号カード', '', '', '', '', '', '', UNIX_TIMESTAMP(), UNIX_TIMESTAMP(), 99, 'normal'),
(0, 'corporate_szb_1', 'パスポート写し(写真面＋住所面)', '', '', '', '', '', '', UNIX_TIMESTAMP(), UNIX_TIMESTAMP(), 98, 'normal'),
(0, 'corporate_szb_1', '在留カード', '', '', '', '', '', '', UNIX_TIMESTAMP(), UNIX_TIMESTAMP(), 97, 'normal'),
(0, 'corporate_szb_1', 'その他', '', '', '', '', '', '', UNIX_TIMESTAMP(), UNIX_TIMESTAMP(), 96, 'normal');
