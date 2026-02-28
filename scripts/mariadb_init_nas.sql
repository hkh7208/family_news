CREATE DATABASE IF NOT EXISTS `family_news`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'family_news'@'%'
  IDENTIFIED BY 'change_me_nas';

GRANT ALL PRIVILEGES ON `family_news`.* TO 'family_news'@'%';

FLUSH PRIVILEGES;