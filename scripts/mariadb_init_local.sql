CREATE DATABASE IF NOT EXISTS `family_news`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'family_news'@'localhost'
  IDENTIFIED BY 'change_me_local';

CREATE USER IF NOT EXISTS 'family_news'@'127.0.0.1'
  IDENTIFIED BY 'change_me_local';

GRANT ALL PRIVILEGES ON `family_news`.* TO 'family_news'@'localhost';
GRANT ALL PRIVILEGES ON `family_news`.* TO 'family_news'@'127.0.0.1';

FLUSH PRIVILEGES;