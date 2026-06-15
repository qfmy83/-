-- ============================================================
-- 文件: 01_create_databases.sql
-- 说明: 创建 Hive 数据库（ODS/DWD/DWS/ADS 四层数仓）
-- 使用: hive -f sql/01_create_databases.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS ods COMMENT '原始数据层 - Operational Data Store';
CREATE DATABASE IF NOT EXISTS dwd COMMENT '明细数据层 - Data Warehouse Detail';
CREATE DATABASE IF NOT EXISTS dws COMMENT '汇总数据层 - Data Warehouse Summary';
CREATE DATABASE IF NOT EXISTS ads COMMENT '应用数据层 - Application Data Store';

SHOW DATABASES;
