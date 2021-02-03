/*
Navicat MySQL Data Transfer

Source Server         : my_computer
Source Server Version : 80020
Source Host           : localhost:3306
Source Database       : oms

Target Server Type    : MYSQL
Target Server Version : 80020
File Encoding         : 65001

Date: 2021-02-03 15:56:29
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for accs_order
-- ----------------------------
DROP TABLE IF EXISTS `accs_order`;
CREATE TABLE `accs_order` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(20) NOT NULL,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `comments` longtext,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `accs_order_number` varchar(128) DEFAULT NULL,
  `sku` varchar(128) DEFAULT NULL,
  `quantity` int NOT NULL,
  `order_date` datetime(6) DEFAULT NULL,
  `shipping_date` datetime(6) DEFAULT NULL,
  `qc_date` datetime(6) DEFAULT NULL,
  `pick_date` datetime(6) DEFAULT NULL,
  `ship_date` datetime(6) DEFAULT NULL,
  `assign_date` datetime(6) DEFAULT NULL,
  `close_date` datetime(6) DEFAULT NULL,
  `hold_date` datetime(6) DEFAULT NULL,
  `warehouse` varchar(40) DEFAULT NULL,
  `location` varchar(40) DEFAULT NULL,
  `status` varchar(20) DEFAULT NULL,
  `order_number` varchar(128) DEFAULT NULL,
  `last_status` varchar(128) DEFAULT NULL,
  `name` varchar(128) DEFAULT NULL,
  `base_entity` varchar(128) DEFAULT NULL,
  `base_type` varchar(20) NOT NULL,
  `is_rx_have` tinyint(1) NOT NULL,
  `pack_date` datetime(6) DEFAULT NULL,
  `repick_quantity` int DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for all_attribute_values
-- ----------------------------
DROP TABLE IF EXISTS `all_attribute_values`;
CREATE TABLE `all_attribute_values` (
  `sub_name` varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT '',
  `id` int NOT NULL,
  `name` varchar(20) DEFAULT NULL,
  `code` varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `type` varchar(20) DEFAULT NULL,
  `sub_type` varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for attrgroup
-- ----------------------------
DROP TABLE IF EXISTS `attrgroup`;
CREATE TABLE `attrgroup` (
  `attr_group_id` int NOT NULL,
  `create_time` datetime(6) NOT NULL,
  `update_time` datetime(6) NOT NULL,
  `group_name` varchar(50) NOT NULL,
  PRIMARY KEY (`attr_group_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Table structure for attrvalue
-- ----------------------------
DROP TABLE IF EXISTS `attrvalue`;
CREATE TABLE `attrvalue` (
  `attr_value_id` int NOT NULL,
  `create_time` datetime(6) NOT NULL,
  `update_time` datetime(6) NOT NULL,
  `attr_value_code` varchar(30) NOT NULL,
  `attr_value_name` varchar(30) NOT NULL,
  PRIMARY KEY (`attr_value_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Table structure for auth_group
-- ----------------------------
DROP TABLE IF EXISTS `auth_group`;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(80) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=30 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for auth_group_permissions
-- ----------------------------
DROP TABLE IF EXISTS `auth_group_permissions`;
CREATE TABLE `auth_group_permissions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=602 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for auth_permission
-- ----------------------------
DROP TABLE IF EXISTS `auth_permission`;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=602 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for auth_user
-- ----------------------------
DROP TABLE IF EXISTS `auth_user`;
CREATE TABLE `auth_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(30) NOT NULL,
  `last_name` varchar(30) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=103 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for auth_user_groups
-- ----------------------------
DROP TABLE IF EXISTS `auth_user_groups`;
CREATE TABLE `auth_user_groups` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`),
  CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=343 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for auth_user_user_permissions
-- ----------------------------
DROP TABLE IF EXISTS `auth_user_user_permissions`;
CREATE TABLE `auth_user_user_permissions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2259 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for comment_comment
-- ----------------------------
DROP TABLE IF EXISTS `comment_comment`;
CREATE TABLE `comment_comment` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `type` varchar(20) NOT NULL,
  `biz_type` varchar(20) DEFAULT NULL,
  `biz_id` varchar(128) DEFAULT NULL,
  `comments` longtext,
  `status` varchar(20) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `assign_id` varchar(128) DEFAULT NULL,
  `assign_name` varchar(128) DEFAULT NULL,
  `parent_entity_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `comment_comment_parent_entity_id_21290104_fk_comment_comment_id` (`parent_entity_id`),
  CONSTRAINT `comment_comment_parent_entity_id_21290104_fk_comment_comment_id` FOREIGN KEY (`parent_entity_id`) REFERENCES `comment_comment` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=90 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for customer_account_log
-- ----------------------------
DROP TABLE IF EXISTS `customer_account_log`;
CREATE TABLE `customer_account_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `customer_email` varchar(128) NOT NULL DEFAULT '',
  `old_customer_email` varchar(128) DEFAULT NULL,
  `comments` longtext,
  `is_pwd` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_entity_id` int DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=65 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for django_admin_log
-- ----------------------------
DROP TABLE IF EXISTS `django_admin_log`;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13139 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for django_content_type
-- ----------------------------
DROP TABLE IF EXISTS `django_content_type`;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=159 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for django_migrations
-- ----------------------------
DROP TABLE IF EXISTS `django_migrations`;
CREATE TABLE `django_migrations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=128 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for django_session
-- ----------------------------
DROP TABLE IF EXISTS `django_session`;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for frame_vca
-- ----------------------------
DROP TABLE IF EXISTS `frame_vca`;
CREATE TABLE `frame_vca` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `type` varchar(20) NOT NULL,
  `product_type` varchar(15) NOT NULL,
  `sku` varchar(40) DEFAULT NULL,
  `name` varchar(128) NOT NULL,
  `base_price` decimal(10,2) NOT NULL,
  `sku_specs` varchar(128) DEFAULT NULL,
  `file_path` varchar(128) DEFAULT NULL,
  `property_list` longtext,
  `is_activate_vca_id` int NOT NULL,
  `parent_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `sku` (`sku`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Table structure for merchandising_api_request_log
-- ----------------------------
DROP TABLE IF EXISTS `merchandising_api_request_log`;
CREATE TABLE `merchandising_api_request_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(20) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for merchandising_product
-- ----------------------------
DROP TABLE IF EXISTS `merchandising_product`;
CREATE TABLE `merchandising_product` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `type` varchar(20) NOT NULL,
  `parent_id` int NOT NULL,
  `category_id` int NOT NULL,
  `category_name` varchar(128) DEFAULT NULL,
  `product_id` int NOT NULL,
  `sku` varchar(128) DEFAULT NULL,
  `frame_sku` varchar(128) DEFAULT NULL,
  `name` varchar(128) DEFAULT NULL,
  `image_url` varchar(128) DEFAULT NULL,
  `shape` varchar(128) DEFAULT NULL,
  `material` varchar(128) DEFAULT NULL,
  `bridge` varchar(128) DEFAULT NULL,
  `temple_length` varchar(128) DEFAULT NULL,
  `width` varchar(128) DEFAULT NULL,
  `weight` varchar(128) DEFAULT NULL,
  `quantity` int NOT NULL,
  `position` int NOT NULL,
  `is_in_stock` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Table structure for merchandising_product_parent
-- ----------------------------
DROP TABLE IF EXISTS `merchandising_product_parent`;
CREATE TABLE `merchandising_product_parent` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `type` varchar(20) NOT NULL,
  `category_id` int NOT NULL,
  `product_id` int NOT NULL,
  `category_name` varchar(128) DEFAULT NULL,
  `sku` varchar(128) DEFAULT NULL,
  `name` varchar(128) DEFAULT NULL,
  `position` int NOT NULL,
  `is_in_stock` tinyint(1) NOT NULL,
  `entity_created_at` varchar(128) DEFAULT NULL,
  `entity_updated_at` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Table structure for mrp_job_archived
-- ----------------------------
DROP TABLE IF EXISTS `mrp_job_archived`;
CREATE TABLE `mrp_job_archived` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `order_number` varchar(128) DEFAULT NULL,
  `entity_id` varchar(128) DEFAULT NULL,
  `lab_number` varchar(128) DEFAULT NULL,
  `status` varchar(128) DEFAULT NULL,
  `frame` varchar(128) DEFAULT NULL,
  `lens_sku` varchar(128) DEFAULT NULL,
  `type` varchar(20) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for mrp_job_log
-- ----------------------------
DROP TABLE IF EXISTS `mrp_job_log`;
CREATE TABLE `mrp_job_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `type` varchar(20) NOT NULL,
  `last_entity_id` int NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for mrp_job_tracking
-- ----------------------------
DROP TABLE IF EXISTS `mrp_job_tracking`;
CREATE TABLE `mrp_job_tracking` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `order_number` varchar(128) DEFAULT NULL,
  `entity_id` varchar(128) DEFAULT NULL,
  `lab_number` varchar(128) DEFAULT NULL,
  `status` varchar(128) DEFAULT NULL,
  `frame` varchar(128) DEFAULT NULL,
  `lens_sku` varchar(128) DEFAULT NULL,
  `type` varchar(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `entity_id` (`entity_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for oms_action
-- ----------------------------
DROP TABLE IF EXISTS `oms_action`;
CREATE TABLE `oms_action` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(20) NOT NULL,
  `key` varchar(128) DEFAULT NULL,
  `value` varchar(128) DEFAULT NULL,
  `object_type` varchar(40) DEFAULT NULL,
  `description` varchar(512) DEFAULT NULL,
  `help` longtext,
  `group` int NOT NULL,
  `sequence` int NOT NULL,
  `create_at` datetime(6) NOT NULL,
  `update_at` datetime(6) NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for oms_black_list
-- ----------------------------
DROP TABLE IF EXISTS `oms_black_list`;
CREATE TABLE `oms_black_list` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(20) NOT NULL,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `customer_name` varchar(128) DEFAULT NULL,
  `firstname` varchar(128) DEFAULT NULL,
  `lastname` varchar(128) DEFAULT NULL,
  `phone` varchar(128) DEFAULT NULL,
  `email` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for oms_blue_glasses
-- ----------------------------
DROP TABLE IF EXISTS `oms_blue_glasses`;
CREATE TABLE `oms_blue_glasses` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(20) NOT NULL,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `frame` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for oms_construction_voucher
-- ----------------------------
DROP TABLE IF EXISTS `oms_construction_voucher`;
CREATE TABLE `oms_construction_voucher` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `type` varchar(20) NOT NULL,
  `laborder_id` int NOT NULL,
  `lab_number` varchar(128) DEFAULT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `print_times` int NOT NULL,
  `request_notes_entity_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `laborder_id` (`laborder_id`),
  UNIQUE KEY `oms_construction_voucher_lab_number_76c61ab3_uniq` (`lab_number`),
  KEY `oms_construction_vou_request_notes_entity_7dff78fc_fk_oms_labor` (`request_notes_entity_id`),
  CONSTRAINT `oms_construction_vou_request_notes_entity_7dff78fc_fk_oms_labor` FOREIGN KEY (`request_notes_entity_id`) REFERENCES `oms_laborder_request_notes_line` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for oms_construction_voucher_finish_glasses
-- ----------------------------
DROP TABLE IF EXISTS `oms_construction_voucher_finish_glasses`;
CREATE TABLE `oms_construction_voucher_finish_glasses` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `laborder_id` int NOT NULL,
  `lab_number` varchar(128) DEFAULT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `print_times` int NOT NULL,
  `type` varchar(20) NOT NULL,
  `request_notes_entity_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `laborder_id` (`laborder_id`),
  UNIQUE KEY `lab_number` (`lab_number`),
  KEY `oms_construction_vou_request_notes_entity_2038330c_fk_oms_labor` (`request_notes_entity_id`),
  CONSTRAINT `oms_construction_vou_request_notes_entity_2038330c_fk_oms_labor` FOREIGN KEY (`request_notes_entity_id`) REFERENCES `oms_laborder_request_notes_line` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for oms_customeraccountlog
-- ----------------------------
DROP TABLE IF EXISTS `oms_customeraccountlog`;
CREATE TABLE `oms_customeraccountlog` (
  `id` int NOT NULL AUTO_INCREMENT,
  `is_pwd` tinyint(1) NOT NULL,
  `customer_email` varchar(128) DEFAULT NULL,
  `old_customer_email` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `created_at` datetime(6) DEFAULT NULL,
  `updated_at` datetime(6) DEFAULT NULL,
  `user_entity_id` int DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Table structure for oms_factory
-- ----------------------------
DROP TABLE IF EXISTS `oms_factory`;
CREATE TABLE `oms_factory` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `type` varchar(20) NOT NULL,
  `factory_id` varchar(64) DEFAULT NULL,
  `factory_name` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `oms_factory_factory_id_7ab45382_uniq` (`factory_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for oms_generatelog
-- ----------------------------
DROP TABLE IF EXISTS `oms_generatelog`;
CREATE TABLE `oms_generatelog` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(20) NOT NULL,
  `last_entity` int NOT NULL,
  `current_entity` int NOT NULL,
  `sequence` int NOT NULL,
  `create_at` datetime(6) NOT NULL,
  `update_at` datetime(6) NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for oms_hold_cancel_request
-- ----------------------------
DROP TABLE IF EXISTS `oms_hold_cancel_request`;
CREATE TABLE `oms_hold_cancel_request` (
  `id` int NOT NULL AUTO_INCREMENT,
  `is_handle` tinyint(1) NOT NULL,
  `handle_result` varchar(20) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `lab_number` varchar(128) DEFAULT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `order_status_now` varchar(20) DEFAULT NULL,
  `order_status_future` varchar(20) DEFAULT NULL,
  `reason` varchar(4096) DEFAULT NULL,
  `reply` varchar(4096) DEFAULT NULL,
  `reply_username` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for oms_holidaysetting
-- ----------------------------
DROP TABLE IF EXISTS `oms_holidaysetting`;
CREATE TABLE `oms_holidaysetting` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(20) NOT NULL,
  `country_id` varchar(20) DEFAULT NULL,
  `holiday_date` date DEFAULT NULL,
  `sequence` int NOT NULL,
  `create_at` datetime(6) NOT NULL,
  `update_at` datetime(6) NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for oms_laborder
-- ----------------------------
DROP TABLE IF EXISTS `oms_laborder`;
CREATE TABLE `oms_laborder` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(20) NOT NULL,
  `chanel` varchar(128) DEFAULT NULL,
  `is_vip` tinyint(1) NOT NULL,
  `ship_direction` varchar(40) NOT NULL,
  `lab_number` varchar(128) DEFAULT NULL,
  `order_date` date DEFAULT NULL,
  `comments` longtext,
  `frame` varchar(128) DEFAULT NULL,
  `name` varchar(512) DEFAULT NULL,
  `size` varchar(40) DEFAULT NULL,
  `quantity` int NOT NULL,
  `lens_sku` varchar(128) DEFAULT NULL,
  `lens_name` varchar(512) DEFAULT NULL,
  `coating_sku` varchar(128) DEFAULT NULL,
  `coating_name` varchar(512) DEFAULT NULL,
  `tint_sku` varchar(128) DEFAULT NULL,
  `tint_name` varchar(512) DEFAULT NULL,
  `od_sph` decimal(5,2) NOT NULL,
  `od_cyl` decimal(5,2) NOT NULL,
  `od_axis` decimal(5,0) NOT NULL,
  `os_sph` decimal(5,2) NOT NULL,
  `os_cyl` decimal(5,2) NOT NULL,
  `os_axis` decimal(5,0) NOT NULL,
  `pd` decimal(5,1) NOT NULL,
  `is_singgle_pd` tinyint(1) NOT NULL,
  `od_pd` decimal(5,1) NOT NULL,
  `os_pd` decimal(5,1) NOT NULL,
  `od_add` decimal(5,2) NOT NULL,
  `os_add` decimal(5,2) NOT NULL,
  `od_prism` decimal(5,2) NOT NULL,
  `od_base` varchar(40) DEFAULT NULL,
  `os_prism` decimal(5,2) NOT NULL,
  `os_base` varchar(40) DEFAULT NULL,
  `sequence` int NOT NULL,
  `create_at` datetime(6) NOT NULL,
  `update_at` datetime(6) NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `prescription_id` varchar(40) DEFAULT NULL,
  `prescription_name` varchar(128) DEFAULT NULL,
  `prescription_type` varchar(128) DEFAULT NULL,
  `used_for` varchar(40) DEFAULT NULL,
  `carriers` varchar(128) DEFAULT NULL,
  `estimated_time` date DEFAULT NULL,
  `final_time` datetime(6) DEFAULT NULL,
  `shipping_number` varchar(128) DEFAULT NULL,
  `status` varchar(128) DEFAULT NULL,
  `promised_date` datetime(6) DEFAULT NULL,
  `qty_ordered` int NOT NULL,
  `targeted_date` datetime(6) DEFAULT NULL,
  `act_lens_name` varchar(512) DEFAULT NULL,
  `act_lens_sku` varchar(128) DEFAULT NULL,
  `base_entity` varchar(128) DEFAULT NULL,
  `change_reason` varchar(128) DEFAULT NULL,
  `estimated_date` datetime(6) DEFAULT NULL,
  `estimated_ship_date` datetime(6) DEFAULT NULL,
  `has_remake_orders` tinyint(1) NOT NULL,
  `is_remake_order` tinyint(1) NOT NULL,
  `lens_delivery_time` datetime(6) DEFAULT NULL,
  `order_datetime` datetime(6) DEFAULT NULL,
  `production_days_1` decimal(5,1) NOT NULL,
  `set_time_1` decimal(5,1) NOT NULL,
  `c128_path` varchar(100) DEFAULT NULL,
  `c39_path` varchar(100) DEFAULT NULL,
  `dia_1` decimal(10,2) NOT NULL,
  `dia_2` decimal(10,2) NOT NULL,
  `qr_path` varchar(100) DEFAULT NULL,
  `pupils_position` int NOT NULL,
  `pupils_position_name` varchar(255) DEFAULT NULL,
  `profile_id` varchar(128) DEFAULT NULL,
  `profile_name` varchar(255) DEFAULT NULL,
  `profile_prescription_id` varchar(128) DEFAULT NULL,
  `asmbl_seght` int NOT NULL,
  `lens_height` int NOT NULL,
  `lens_seght` int NOT NULL,
  `vendor` varchar(128) DEFAULT NULL,
  `comments_inner` longtext,
  `comments_ship` longtext,
  `order_number` varchar(128) DEFAULT NULL,
  `pal_design_name` varchar(512) DEFAULT NULL,
  `pal_design_sku` varchar(128) DEFAULT NULL,
  `progressive_type` varchar(128) DEFAULT NULL,
  `workshop` varchar(128) DEFAULT NULL,
  `act_ship_direction` varchar(40) NOT NULL,
  `color` varchar(512) DEFAULT NULL,
  `frame_type` varchar(40) DEFAULT '',
  `is_glasses_return` tinyint(1) NOT NULL,
  `current_status` varchar(128) DEFAULT NULL,
  `is_ai_checked` tinyint(1) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `bridge` int NOT NULL,
  `lens_width` int NOT NULL,
  `temple_length` int NOT NULL,
  `lab_seg_height` varchar(64) DEFAULT NULL,
  `special_handling` varchar(512) DEFAULT NULL,
  `assemble_height` varchar(32) DEFAULT NULL,
  `special_handling_name` varchar(512) DEFAULT NULL,
  `special_handling_sku` varchar(128) DEFAULT NULL,
  `sub_mirrors_height` varchar(16) DEFAULT NULL,
  `hours_of_purchase` int NOT NULL,
  `level_of_purchase` int NOT NULL,
  `is_lens_order_created` tinyint(1) NOT NULL,
  `vendor_order_reference` varchar(128) NOT NULL,
  `channel` varchar(32) DEFAULT NULL,
  `od_base1` varchar(40) DEFAULT NULL,
  `od_prism1` decimal(5,2) DEFAULT NULL,
  `os_base1` varchar(40) DEFAULT NULL,
  `os_prism1` decimal(5,2) DEFAULT NULL,
  `is_has_nose_pad` tinyint(1) DEFAULT NULL,
  `is_sync` tinyint(1) NOT NULL,
  `image` varchar(1024) DEFAULT NULL,
  `thumbnail` varchar(1024) DEFAULT NULL,
  `category_id` varchar(128) DEFAULT NULL,
  `clipon_qty` int NOT NULL,
  `coatings` varchar(32) NOT NULL,
  `tracking_number` varchar(1024) DEFAULT NULL,
  `cur_progress` varchar(1024) DEFAULT NULL,
  `overdue_reasons` longtext,
  `is_generated_production_report` tinyint(1) NOT NULL,
  `is_production_change` tinyint(1) NOT NULL,
  `order_type` varchar(32) NOT NULL,
  `delivered_at` datetime(6) DEFAULT NULL,
  `locker_number` varchar(128) DEFAULT NULL,
  `tag` varchar(128) DEFAULT NULL,
  `tracking_code` varchar(128) DEFAULT NULL,
  `vendor_order_status_code` varchar(36) DEFAULT NULL,
  `vendor_order_status_updated_at` varchar(36) DEFAULT NULL,
  `vendor_order_status_value` varchar(20) DEFAULT NULL,
  `priority` int NOT NULL,
  `exclude_days` varchar(128) DEFAULT NULL,
  `exclude_time` varchar(128) DEFAULT NULL,
  `weight` decimal(5,2) DEFAULT '0.00',
  `gross_weight` decimal(5,2) DEFAULT '0.00',
  `weight_create_at` datetime(6) DEFAULT NULL,
  `operator_id` int DEFAULT '0',
  `operator_name` varchar(128) DEFAULT '',
  PRIMARY KEY (`id`),
  UNIQUE KEY `lab_number` (`lab_number`),
  KEY `idx_isync` (`is_sync`),
  KEY `idx_base_entity` (`base_entity`),
  KEY `idx_oms_laborder` (`status`,`is_enabled`,`create_at`),
  KEY `idx_oms_laborder02` (`is_enabled`,`create_at`),
  KEY `idx_order_number` (`order_number`)
) ENGINE=InnoDB AUTO_INCREMENT=286105 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for oms_laborder_purchase_order
-- ----------------------------
DROP TABLE IF EXISTS `oms_laborder_purchase_order`;
CREATE TABLE `oms_laborder_purchase_order` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `type` varchar(20) NOT NULL,
  `count` int NOT NULL,
  `vendor` varchar(128) DEFAULT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8300 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for oms_laborder_purchase_order_line
-- ----------------------------
DROP TABLE IF EXISTS `oms_laborder_purchase_order_line`;
CREATE TABLE `oms_laborder_purchase_order_line` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `type` varchar(20) NOT NULL,
  `laborder_id` int NOT NULL,
  `frame` varchar(128) DEFAULT NULL,
  `lab_number` varchar(128) DEFAULT NULL,
  `quantity` int NOT NULL,
  `lens_type` varchar(20) DEFAULT NULL,
  `order_date` datetime(6) DEFAULT NULL,
  `order_created_date` datetime(6) DEFAULT NULL,
  `laborder_entity_id` int DEFAULT NULL,
  `lpo_id` int DEFAULT NULL,
  `purchase_type` varchar(20) DEFAULT NULL,
  `is_set_hours_of_purchase` tinyint(1) NOT NULL,
  `vendor_order_reference` varchar(128) NOT NULL,
  `comments` varchar(1024) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `laborder_id` (`laborder_id`),
  UNIQUE KEY `lab_number` (`lab_number`),
  KEY `oms_laborder_purchas_laborder_entity_id_c456d8b9_fk_oms_labor` (`laborder_entity_id`),
  KEY `oms_laborder_purchas_lpo_id_7e0f37ed_fk_oms_labor` (`lpo_id`),
  CONSTRAINT `oms_laborder_purchas_laborder_entity_id_c456d8b9_fk_oms_labor` FOREIGN KEY (`laborder_entity_id`) REFERENCES `oms_laborder` (`id`),
  CONSTRAINT `oms_laborder_purchas_lpo_id_7e0f37ed_fk_oms_labor` FOREIGN KEY (`lpo_id`) REFERENCES `oms_laborder_purchase_order` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=245042 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for oms_laborder_qualitycontrol
-- ----------------------------
DROP TABLE IF EXISTS `oms_laborder_qualitycontrol`;
CREATE TABLE `oms_laborder_qualitycontrol` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `type` varchar(20) NOT NULL,
  `comments` longtext,
  `laborder_entity_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `oms_laborder_quality_laborder_entity_id_e5b03d2d_fk_oms_labor` (`laborder_entity_id`),
  CONSTRAINT `oms_laborder_quality_laborder_entity_id_e5b03d2d_fk_oms_labor` FOREIGN KEY (`laborder_entity_id`) REFERENCES `oms_laborder` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for oms_laborder_request_notes
-- ----------------------------
DROP TABLE IF EXISTS `oms_laborder_request_notes`;
CREATE TABLE `oms_laborder_request_notes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `type` varchar(20) NOT NULL,
  `laborder_id` int NOT NULL,
  `lab_number` varchar(128) DEFAULT NULL,
  `count` int NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `vendor` varchar(128) DEFAULT NULL,
  `warehouse_code` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `laborder_id` (`laborder_id`)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for oms_laborder_request_notes_line
-- ----------------------------
DROP TABLE IF EXISTS `oms_laborder_request_notes_line`;
CREATE TABLE `oms_laborder_request_notes_line` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `type` varchar(20) NOT NULL,
  `laborder_id` int NOT NULL,
  `index` int NOT NULL,
  `frame` varchar(128) DEFAULT NULL,
  `lab_number` varchar(128) DEFAULT NULL,
  `quantity` int NOT NULL,
  `lens_type` varchar(20) DEFAULT NULL,
  `order_date` datetime(6) DEFAULT NULL,
  `order_created_date` datetime(6) DEFAULT NULL,
  `laborder_entity_id` int DEFAULT NULL,
  `lrn_id` int DEFAULT NULL,
  `location` varchar(128) DEFAULT NULL,
  `vendor` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `oms_laborder_request_notes_line_laborder_id_fd3b3e33_uniq` (`laborder_id`),
  UNIQUE KEY `oms_laborder_request_notes_line_lab_number_f5d91f8f_uniq` (`lab_number`),
  KEY `oms_laborder_request_laborder_entity_id_fcff21e8_fk_oms_labor` (`laborder_entity_id`),
  KEY `oms_laborder_request_lrn_id_33fb755b_fk_oms_labor` (`lrn_id`),
  CONSTRAINT `oms_laborder_request_laborder_entity_id_fcff21e8_fk_oms_labor` FOREIGN KEY (`laborder_entity_id`) REFERENCES `oms_laborder` (`id`),
  CONSTRAINT `oms_laborder_request_lrn_id_33fb755b_fk_oms_labor` FOREIGN KEY (`lrn_id`) REFERENCES `oms_laborder_request_notes` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for oms_labproduct
-- ----------------------------
DROP TABLE IF EXISTS `oms_labproduct`;
CREATE TABLE `oms_labproduct` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(20) NOT NULL,
  `product_id` varchar(128) DEFAULT NULL,
  `sku` varchar(128) DEFAULT NULL,
  `name` varchar(1024) DEFAULT NULL,
  `sequence` int NOT NULL,
  `create_at` datetime(6) NOT NULL,
  `update_at` datetime(6) NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `index` varchar(40) NOT NULL,
  `is_rx_lab` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `sku` (`sku`)
) ENGINE=InnoDB AUTO_INCREMENT=177 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for oms_objecttype
-- ----------------------------
DROP TABLE IF EXISTS `oms_objecttype`;
CREATE TABLE `oms_objecttype` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(20) NOT NULL,
  `object_type` varchar(128) NOT NULL,
  `description` varchar(512) DEFAULT NULL,
  `sequence` int NOT NULL,
  `create_at` datetime(6) NOT NULL,
  `update_at` datetime(6) NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for oms_operationlog
-- ----------------------------
DROP TABLE IF EXISTS `oms_operationlog`;
CREATE TABLE `oms_operationlog` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(20) NOT NULL,
  `object_type` varchar(128) NOT NULL,
  `object_entity` varchar(128) NOT NULL,
  `action` varchar(128) DEFAULT NULL,
  `new_value` longtext,
  `user_entity_id` int DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `sequence` int NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `comments` longtext,
  `content` longtext,
  `fields` varchar(40) DEFAULT NULL,
  `is_async` tinyint(1) NOT NULL,
  `origin_value` longtext,
  `doc_number` varchar(512) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `oms_operationlog_user_entity_id_d6e55cac` (`user_entity_id`),
  CONSTRAINT `oms_operationlog_user_entity_id_d6e55cac_fk_auth_user_id` FOREIGN KEY (`user_entity_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=198 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for oms_orderactivity
-- ----------------------------
DROP TABLE IF EXISTS `oms_orderactivity`;
CREATE TABLE `oms_orderactivity` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(20) NOT NULL DEFAULT '',
  `object_type` varchar(128) NOT NULL DEFAULT '',
  `object_entity` varchar(128) NOT NULL DEFAULT '',
  `order_number` varchar(128) DEFAULT NULL,
  `action` varchar(128) DEFAULT NULL,
  `user_entity` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` longtext,
  `is_async` tinyint(1) NOT NULL,
  `sequence` int NOT NULL,
  `create_at` datetime(6) NOT NULL,
  `update_at` datetime(6) NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `status` varchar(128) DEFAULT NULL,
  `is_send` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=93 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for oms_orderaddtional
-- ----------------------------
DROP TABLE IF EXISTS `oms_orderaddtional`;
CREATE TABLE `oms_orderaddtional` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `type` varchar(20) NOT NULL,
  `mg_id` int NOT NULL,
  `order_entity` int NOT NULL,
  `order_item_entity` int NOT NULL,
  `instruction` varchar(4000) DEFAULT NULL,
  `mg_created_at` datetime(6) DEFAULT NULL,
  `mg_updated_at` datetime(6) DEFAULT NULL,
  `is_used` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for oms_ordertracking
-- ----------------------------
DROP TABLE IF EXISTS `oms_ordertracking`;
CREATE TABLE `oms_ordertracking` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(20) NOT NULL,
  `order_number` varchar(128) NOT NULL,
  `sku` varchar(128) DEFAULT NULL,
  `order_date` datetime(6) DEFAULT NULL,
  `remark` varchar(1024) DEFAULT NULL,
  `sequence` int NOT NULL,
  `create_at` datetime(6) NOT NULL,
  `update_at` datetime(6) NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `user_entity` int DEFAULT NULL,
  `lab_order_entity` int NOT NULL,
  `action` varchar(128) DEFAULT NULL,
  `action_value` varchar(128) DEFAULT NULL,
  `username` varchar(128) DEFAULT NULL,
  `is_sync` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `oms_ordertracking_lab_order_entity_id_41e78736_fk_oms_labor` (`lab_order_entity`),
  CONSTRAINT `oms_ordertracking_lab_order_entity_id_41e78736_fk_oms_labor` FOREIGN KEY (`lab_order_entity`) REFERENCES `oms_laborder` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=186 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for oms_ordertrackingreport
-- ----------------------------
DROP TABLE IF EXISTS `oms_ordertrackingreport`;
CREATE TABLE `oms_ordertrackingreport` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(20) NOT NULL,
  `lab_order_number` varchar(128) NOT NULL,
  `sku` varchar(128) DEFAULT NULL,
  `order_date` datetime(6) DEFAULT NULL,
  `print_date` datetime(6) DEFAULT NULL,
  `frame_outbound` datetime(6) DEFAULT NULL,
  `add_hardened` datetime(6) DEFAULT NULL,
  `coating` datetime(6) DEFAULT NULL,
  `tint` datetime(6) DEFAULT NULL,
  `lens_receive` datetime(6) DEFAULT NULL,
  `assembling` datetime(6) DEFAULT NULL,
  `initial_inspection` datetime(6) DEFAULT NULL,
  `shaping` datetime(6) DEFAULT NULL,
  `purging` datetime(6) DEFAULT NULL,
  `final_inspection` datetime(6) DEFAULT NULL,
  `order_match` datetime(6) DEFAULT NULL,
  `package` datetime(6) DEFAULT NULL,
  `shipping` datetime(6) DEFAULT NULL,
  `carriers` varchar(128) DEFAULT NULL,
  `shipping_number` varchar(128) DEFAULT NULL,
  `estimated_time` datetime(6) DEFAULT NULL,
  `final_time` datetime(6) DEFAULT NULL,
  `remark` varchar(40) DEFAULT NULL,
  `sequence` int NOT NULL,
  `create_at` datetime(6) NOT NULL,
  `update_at` datetime(6) NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `lab_order_entity_id` int DEFAULT NULL,
  `rx_lab` datetime(6) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `lab_order_number` (`lab_order_number`)
) ENGINE=InnoDB AUTO_INCREMENT=27241 DEFAULT CHARSET=latin1;

-- ----------------------------
-- Table structure for oms_ordertrackingreportcs
-- ----------------------------
DROP TABLE IF EXISTS `oms_ordertrackingreportcs`;
CREATE TABLE `oms_ordertrackingreportcs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(20) NOT NULL,
  `order_number` varchar(128) DEFAULT NULL,
  `sku` varchar(128) DEFAULT NULL,
  `order_date` datetime(6) DEFAULT NULL,
  `cs_status` varchar(40) DEFAULT NULL,
  `estimated_time` datetime(6) DEFAULT NULL,
  `final_time` datetime(6) DEFAULT NULL,
  `carriers` varchar(128) DEFAULT NULL,
  `shipping_number` varchar(128) DEFAULT NULL,
  `remark` varchar(4000) DEFAULT NULL,
  `sequence` int NOT NULL,
  `create_at` datetime(6) NOT NULL,
  `update_at` datetime(6) NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `pgorder_number` varchar(128) DEFAULT NULL,
  `shipping_method` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `order_number` (`order_number`)
) ENGINE=InnoDB AUTO_INCREMENT=29699 DEFAULT CHARSET=latin1;

-- ----------------------------
-- Table structure for oms_ordertracking_80824
-- ----------------------------
DROP TABLE IF EXISTS `oms_ordertracking_80824`;
CREATE TABLE `oms_ordertracking_80824` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(20) NOT NULL,
  `order_number` varchar(128) NOT NULL,
  `sku` varchar(128) DEFAULT NULL,
  `order_date` datetime(6) DEFAULT NULL,
  `remark` varchar(40) DEFAULT NULL,
  `sequence` int NOT NULL,
  `create_at` datetime(6) NOT NULL,
  `update_at` datetime(6) NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `user_entity_id` int DEFAULT NULL,
  `lab_order_entity_id` int DEFAULT NULL,
  `action` varchar(40) DEFAULT NULL,
  `action_value` varchar(40) DEFAULT NULL,
  `username` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `oms_ordertracking_lab_order_entity_id_41e78736_fk_oms_labor` (`lab_order_entity_id`),
  CONSTRAINT `oms_ordertracking_80824_ibfk_1` FOREIGN KEY (`lab_order_entity_id`) REFERENCES `oms_laborder` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for oms_pgorder
-- ----------------------------
DROP TABLE IF EXISTS `oms_pgorder`;
CREATE TABLE `oms_pgorder` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(20) NOT NULL,
  `chanel` varchar(128) DEFAULT NULL,
  `is_vip` tinyint(1) NOT NULL,
  `ship_direction` varchar(40) NOT NULL,
  `customer_id` varchar(128) DEFAULT NULL,
  `order_number` varchar(128) DEFAULT NULL,
  `order_create_at` datetime(6) DEFAULT NULL,
  `order_date` date DEFAULT NULL,
  `order_datetime` datetime(6) DEFAULT NULL,
  `subtotal` decimal(10,2) NOT NULL,
  `grand_total` decimal(10,2) NOT NULL,
  `total_paid` decimal(10,2) NOT NULL,
  `shipping_and_handling` decimal(10,2) NOT NULL,
  `base_discount_amount_order` decimal(10,2) NOT NULL,
  `total_qty_ordered` decimal(10,2) NOT NULL,
  `status` varchar(128) DEFAULT NULL,
  `customer_name` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `firstname` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `lastname` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `postcode` varchar(10) DEFAULT NULL,
  `street` varchar(512) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `city` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `region` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `country_id` varchar(128) DEFAULT NULL,
  `email` varchar(128) DEFAULT NULL,
  `shipping_method` varchar(128) NOT NULL,
  `shipping_description` varchar(40) DEFAULT NULL,
  `estimated_ship_date` datetime(6) DEFAULT NULL,
  `estimated_date` datetime(6) DEFAULT NULL,
  `final_date` datetime(6) DEFAULT NULL,
  `targeted_ship_date` datetime(6) DEFAULT NULL,
  `promised_ship_date` datetime(6) DEFAULT NULL,
  `is_inlab` tinyint(1) NOT NULL,
  `is_shiped_api` tinyint(1) NOT NULL,
  `comments` longtext CHARACTER SET utf8 COLLATE utf8_general_ci,
  `sequence` int NOT NULL,
  `create_at` datetime(6) NOT NULL,
  `update_at` datetime(6) NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `phone` varchar(128) DEFAULT NULL,
  `base_entity` varchar(128) DEFAULT NULL,
  `is_required_return_lable` tinyint(1) NOT NULL,
  `billing_address_id` varchar(128) DEFAULT NULL,
  `shipping_address_id` varchar(128) DEFAULT NULL,
  `status_control` varchar(128) DEFAULT NULL,
  `instruction` longtext CHARACTER SET utf8 COLLATE utf8_general_ci,
  `is_inst` tinyint(1) NOT NULL,
  `coupon_code` varchar(255) DEFAULT NULL,
  `coupon_rule_name` varchar(255) DEFAULT NULL,
  `is_issue_addr` tinyint(1) NOT NULL,
  `web_created_at` datetime(6) DEFAULT NULL,
  `web_updated_at` datetime(6) DEFAULT NULL,
  `web_status` varchar(128) DEFAULT NULL,
  `is_verified_addr` tinyint(1) NOT NULL,
  `relation_add_date` datetime(6) DEFAULT NULL,
  `relation_checked` tinyint(1) NOT NULL,
  `relation_email` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT '',
  `relation_phone` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT '',
  `street2` varchar(512) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT '',
  `address_verify_status` int NOT NULL,
  `reorder_number` varchar(1024) DEFAULT NULL,
  `send_invoic_info` longtext NOT NULL,
  `is_generated_report_efficiency` tinyint(1) NOT NULL DEFAULT '0',
  `has_warranty` int DEFAULT '0',
  `row_total_without_warranty` decimal(12,4) NOT NULL,
  `warranty` decimal(12,4) NOT NULL,
  `tag` varchar(128) DEFAULT NULL,
  `is_remake_order` tinyint(1) NOT NULL,
  `origin_order_entity` varchar(128) DEFAULT NULL,
  `origin_order_number` varchar(128) DEFAULT NULL,
  `priority` tinyint(1) NOT NULL,
  `lab_status` varchar(128) DEFAULT NULL,
  `delivered_at` datetime(6) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `oms_pgorder_order_number_9d57ad19_uniq` (`order_number`)
) ENGINE=InnoDB AUTO_INCREMENT=729 DEFAULT CHARSET=latin1;

-- ----------------------------
-- Table structure for oms_pgorderitem
-- ----------------------------
DROP TABLE IF EXISTS `oms_pgorderitem`;
CREATE TABLE `oms_pgorderitem` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(20) NOT NULL,
  `chanel` varchar(128) DEFAULT NULL,
  `is_vip` tinyint(1) NOT NULL,
  `order_number` varchar(128) DEFAULT NULL,
  `order_date` date DEFAULT NULL,
  `lab_order_number` varchar(128) DEFAULT NULL,
  `comments` longtext,
  `frame` varchar(128) DEFAULT NULL,
  `name` varchar(512) DEFAULT NULL,
  `size` varchar(40) DEFAULT NULL,
  `quantity` int NOT NULL,
  `lens_sku` varchar(128) DEFAULT NULL,
  `lens_name` varchar(512) DEFAULT NULL,
  `coating_sku` varchar(128) DEFAULT NULL,
  `coating_name` varchar(512) DEFAULT NULL,
  `tint_sku` varchar(128) DEFAULT NULL,
  `tint_name` varchar(512) DEFAULT NULL,
  `profile_prescription_id` varchar(128) DEFAULT NULL,
  `od_sph` decimal(5,2) NOT NULL,
  `od_cyl` decimal(5,2) NOT NULL,
  `od_axis` decimal(5,0) NOT NULL,
  `os_sph` decimal(5,2) NOT NULL,
  `os_cyl` decimal(5,2) NOT NULL,
  `os_axis` decimal(5,0) NOT NULL,
  `pd` decimal(5,1) NOT NULL,
  `is_singgle_pd` tinyint(1) NOT NULL,
  `od_pd` decimal(5,1) NOT NULL,
  `os_pd` decimal(5,1) NOT NULL,
  `od_add` decimal(5,2) NOT NULL,
  `os_add` decimal(5,2) NOT NULL,
  `od_prism` decimal(5,2) NOT NULL,
  `od_base` varchar(40) DEFAULT NULL,
  `os_prism` decimal(5,2) NOT NULL,
  `os_base` varchar(40) DEFAULT NULL,
  `sequence` int NOT NULL,
  `create_at` datetime(6) NOT NULL,
  `update_at` datetime(6) NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `lab_order_entity_id` int DEFAULT NULL,
  `product_index` int NOT NULL,
  `order_create_at` datetime(6) DEFAULT NULL,
  `ship_direction` varchar(40) NOT NULL,
  `bridge` int NOT NULL,
  `city` varchar(60) DEFAULT NULL,
  `country` varchar(20) NOT NULL,
  `lens_width` int NOT NULL,
  `region` varchar(60) DEFAULT NULL,
  `shipping_description` varchar(40) DEFAULT NULL,
  `shipping_method` varchar(128) DEFAULT NULL,
  `temple_length` int NOT NULL,
  `prescription_id` varchar(40) DEFAULT NULL,
  `prescription_name` varchar(128) DEFAULT NULL,
  `prescription_type` varchar(128) DEFAULT NULL,
  `used_for` varchar(40) DEFAULT NULL,
  `is_shiped_api` tinyint(1) NOT NULL,
  `qty_ordered` int NOT NULL,
  `base_discount_amount_item` decimal(10,2) NOT NULL,
  `estimated_date` datetime(6) DEFAULT NULL,
  `estimated_ship_date` datetime(6) DEFAULT NULL,
  `final_date` datetime(6) DEFAULT NULL,
  `order_datetime` datetime(6) DEFAULT NULL,
  `original_price` decimal(10,2) NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `promised_ship_date` datetime(6) DEFAULT NULL,
  `targeted_ship_date` datetime(6) DEFAULT NULL,
  `pg_order_entity_id` int DEFAULT NULL,
  `status` varchar(128) DEFAULT NULL,
  `item_id` varchar(128) DEFAULT NULL,
  `product_id` varchar(128) DEFAULT NULL,
  `image` varchar(1024) DEFAULT NULL,
  `lens_height` int NOT NULL,
  `thumbnail` varchar(1024) DEFAULT NULL,
  `instruction` longtext,
  `profile_id` varchar(128) DEFAULT NULL,
  `order_image_urls` varchar(4000) DEFAULT NULL,
  `pupils_position` int NOT NULL,
  `pupils_position_name` varchar(255) DEFAULT NULL,
  `profile_name` varchar(255) DEFAULT NULL,
  `asmbl_seght` int NOT NULL,
  `lens_seght` int NOT NULL,
  `comments_inner` longtext,
  `comments_ship` longtext,
  `dia_1` decimal(10,2) DEFAULT '0.00',
  `dia_2` decimal(10,2) DEFAULT '0.00',
  `pal_design_name` varchar(512) DEFAULT NULL,
  `pal_design_sku` varchar(128) DEFAULT NULL,
  `progressive_type` varchar(128) DEFAULT NULL,
  `color` varchar(512) DEFAULT NULL,
  `frame_type` varchar(512) DEFAULT NULL,
  `lab_seg_height` varchar(64) DEFAULT NULL,
  `special_handling` varchar(512) DEFAULT NULL,
  `assemble_height` varchar(32) DEFAULT NULL,
  `special_handling_name` varchar(512) DEFAULT NULL,
  `special_handling_sku` varchar(128) DEFAULT NULL,
  `sub_mirrors_height` varchar(16) DEFAULT NULL,
  `channel` varchar(32) DEFAULT NULL,
  `od_base1` varchar(40) DEFAULT NULL,
  `od_prism1` decimal(5,2) DEFAULT NULL,
  `os_base1` varchar(40) DEFAULT NULL,
  `os_prism1` decimal(5,2) DEFAULT NULL,
  `is_has_nose_pad` tinyint(1) DEFAULT NULL,
  `is_has_imgs` tinyint(1) NOT NULL,
  `is_sync` tinyint(1) NOT NULL,
  `clipon_qty` int NOT NULL,
  `coatings` varchar(32) NOT NULL,
  `row_total_without_warranty` decimal(12,4) NOT NULL,
  `warranty` decimal(12,4) NOT NULL,
  `has_warranty` int DEFAULT NULL,
  `is_nonPrescription` int DEFAULT NULL,
  `product_options` longtext NOT NULL,
  `order_type` varchar(128) DEFAULT NULL,
  `delivered_at` datetime(6) DEFAULT NULL,
  `tag` varchar(128) DEFAULT NULL,
  `attribute_set_id` varchar(128) DEFAULT NULL,
  `attribute_set_name` varchar(128) DEFAULT NULL,
  `type_id` varchar(128) DEFAULT NULL,
  `priority` int DEFAULT NULL,
  `lab_status` varchar(128) DEFAULT '',
  PRIMARY KEY (`id`),
  KEY `oms_pgorder_lab_order_entity_id_4713db14_fk_oms_laborder_id` (`lab_order_entity_id`),
  KEY `oms_pgorderitem_pg_order_entity_id_ce4d45c3_fk_oms_pgorder_id` (`pg_order_entity_id`),
  CONSTRAINT `oms_pgorder_lab_order_entity_id_4713db14_fk_oms_laborder_id` FOREIGN KEY (`lab_order_entity_id`) REFERENCES `oms_laborder` (`id`),
  CONSTRAINT `oms_pgorderitem_pg_order_entity_id_ce4d45c3_fk_oms_pgorder_id` FOREIGN KEY (`pg_order_entity_id`) REFERENCES `oms_pgorder` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1195 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for oms_pgorder_invoice
-- ----------------------------
DROP TABLE IF EXISTS `oms_pgorder_invoice`;
CREATE TABLE `oms_pgorder_invoice` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(20) NOT NULL,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `pg_order_entity_id` varchar(128) DEFAULT NULL,
  `order_number` varchar(128) DEFAULT NULL,
  `inv_amount` decimal(10,2) NOT NULL,
  `status` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `inv_type` varchar(512) DEFAULT NULL,
  `ticket_no` varchar(128) DEFAULT NULL,
  `invoice_id` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Table structure for oms_pgproduct
-- ----------------------------
DROP TABLE IF EXISTS `oms_pgproduct`;
CREATE TABLE `oms_pgproduct` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(20) NOT NULL,
  `product_id` varchar(128) DEFAULT NULL,
  `sku` varchar(128) DEFAULT NULL,
  `name` varchar(1024) DEFAULT NULL,
  `sequence` int NOT NULL,
  `create_at` datetime(6) NOT NULL,
  `update_at` datetime(6) NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `lab_product_id` int DEFAULT NULL,
  `index` varchar(40) NOT NULL,
  `is_rx_lab` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `sku` (`sku`),
  KEY `oms_pgproduct_lab_product_id_10955619_fk_oms_labproduct_id` (`lab_product_id`),
  CONSTRAINT `oms_pgproduct_lab_product_id_10955619_fk_oms_labproduct_id` FOREIGN KEY (`lab_product_id`) REFERENCES `oms_labproduct` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=225 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for oms_producttype
-- ----------------------------
DROP TABLE IF EXISTS `oms_producttype`;
CREATE TABLE `oms_producttype` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(20) NOT NULL,
  `code` varchar(128) DEFAULT NULL,
  `name` varchar(512) DEFAULT NULL,
  `description` varchar(512) DEFAULT NULL,
  `sequence` int NOT NULL,
  `create_at` datetime(6) NOT NULL,
  `update_at` datetime(6) NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for oms_received_glasses
-- ----------------------------
DROP TABLE IF EXISTS `oms_received_glasses`;
CREATE TABLE `oms_received_glasses` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `lab_order_entity` varchar(128) DEFAULT NULL,
  `lab_number` varchar(128) DEFAULT NULL,
  `status` varchar(128) DEFAULT NULL,
  `base_entity` varchar(128) DEFAULT NULL,
  `type` varchar(20) NOT NULL,
  `comments` longtext,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=79564 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for oms_sendcomment
-- ----------------------------
DROP TABLE IF EXISTS `oms_sendcomment`;
CREATE TABLE `oms_sendcomment` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `type` varchar(20) NOT NULL,
  `key` varchar(128) DEFAULT NULL,
  `value` longtext,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for oms_shipment
-- ----------------------------
DROP TABLE IF EXISTS `oms_shipment`;
CREATE TABLE `oms_shipment` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(20) NOT NULL,
  `carrierNumber` varchar(30) NOT NULL,
  `remark` varchar(1000) DEFAULT NULL,
  `carrier` varchar(40) NOT NULL,
  `sequence` int NOT NULL,
  `create_at` datetime(6) NOT NULL,
  `update_at` datetime(6) NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `carrierNumber` (`carrierNumber`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for oms_shipping
-- ----------------------------
DROP TABLE IF EXISTS `oms_shipping`;
CREATE TABLE `oms_shipping` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(20) NOT NULL,
  `order_id` varchar(128) NOT NULL,
  `lab_order_id` varchar(4000) NOT NULL,
  `create_date` date DEFAULT NULL,
  `first_name` varchar(128) NOT NULL,
  `last_name` varchar(128) DEFAULT NULL,
  `postcode` varchar(20) NOT NULL,
  `street` varchar(1024) NOT NULL,
  `city` varchar(60) NOT NULL,
  `region` varchar(60) NOT NULL,
  `country_id` varchar(20) NOT NULL,
  `telephone` varchar(20) DEFAULT NULL,
  `comment` longtext,
  `sequence` int NOT NULL,
  `create_at` datetime(6) NOT NULL,
  `update_at` datetime(6) NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `order_id` (`order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for pg_order_remake
-- ----------------------------
DROP TABLE IF EXISTS `pg_order_remake`;
CREATE TABLE `pg_order_remake` (
  `id` int NOT NULL AUTO_INCREMENT,
  `order_number` varchar(128) DEFAULT NULL,
  `item_id` varchar(128) DEFAULT NULL,
  `remake_order` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `created_at` datetime(6) DEFAULT NULL,
  `updated_at` datetime(6) DEFAULT NULL,
  `user_id` int DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=390 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Table structure for pg_order_remake1
-- ----------------------------
DROP TABLE IF EXISTS `pg_order_remake1`;
CREATE TABLE `pg_order_remake1` (
  `id` int NOT NULL AUTO_INCREMENT,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `pg_order_entity_id` varchar(128) DEFAULT NULL,
  `order_number` varchar(128) DEFAULT NULL,
  `inv_amount` decimal(10,2) NOT NULL,
  `status` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `inv_type` varchar(512) DEFAULT NULL,
  `ticket_no` varchar(128) DEFAULT NULL,
  `invoice_id` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Table structure for pg_order_remake_cart
-- ----------------------------
DROP TABLE IF EXISTS `pg_order_remake_cart`;
CREATE TABLE `pg_order_remake_cart` (
  `id` int NOT NULL AUTO_INCREMENT,
  `order_number` varchar(128) DEFAULT NULL,
  `item_id` varchar(128) DEFAULT NULL,
  `items_count` int DEFAULT NULL,
  `remake_order` varchar(128) DEFAULT NULL,
  `profile_id` varchar(128) DEFAULT NULL,
  `is_norx` tinyint(1) DEFAULT NULL,
  `profile_prescription_id` varchar(128) DEFAULT NULL,
  `glasses_prescription_id` varchar(128) DEFAULT NULL,
  `item_options` text,
  `profile_prescription_options` text,
  `glasses_prescription_options` text,
  `is_remake` tinyint(1) DEFAULT NULL,
  `user_id` int DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `created_at` datetime(6) DEFAULT NULL,
  `updated_at` datetime(6) DEFAULT NULL,
  `original_is_norx` tinyint(1) DEFAULT NULL,
  `original_profile_prescription_id` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=186 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Table structure for purchase_po_receipt
-- ----------------------------
DROP TABLE IF EXISTS `purchase_po_receipt`;
CREATE TABLE `purchase_po_receipt` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(20) DEFAULT 'BAMO',
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `receipt_date` varchar(128) DEFAULT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `sku` varchar(128) DEFAULT NULL,
  `unit` varchar(128) DEFAULT NULL,
  `sent_qty` varchar(128) DEFAULT '0',
  `receipt_qty` varchar(128) DEFAULT '0',
  `stock_qty` varchar(128) DEFAULT '0',
  `qc_qty` varchar(128) DEFAULT '0',
  `base_entity` varchar(128) NOT NULL,
  `po_number` varchar(128) DEFAULT NULL,
  `pay_number` varchar(128) DEFAULT NULL,
  `contract_number` varchar(128) DEFAULT NULL,
  `qc_status` varchar(128) DEFAULT 'NEW',
  `stock_status` varchar(128) DEFAULT 'NEW',
  `check_status` varchar(128) DEFAULT 'NEW',
  `pay_status` varchar(128) DEFAULT 'NEW',
  `pay_type` varchar(128) DEFAULT 'NEW',
  `count_user` varchar(128) NOT NULL,
  `doc_number` varchar(128) DEFAULT NULL,
  `vendor` varchar(128) DEFAULT NULL,
  `order_type` varchar(128) DEFAULT NULL,
  `qc_image` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=105 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for purchase_qc_record
-- ----------------------------
DROP TABLE IF EXISTS `purchase_qc_record`;
CREATE TABLE `purchase_qc_record` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(20) NOT NULL,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `sku` varchar(128) DEFAULT NULL,
  `unit` varchar(128) DEFAULT NULL,
  `sent_qty` varchar(128) DEFAULT NULL,
  `receipt_qty` varchar(128) DEFAULT NULL,
  `stock_qty` varchar(128) DEFAULT NULL,
  `qc_qty` varchar(128) DEFAULT NULL,
  `base_entity` varchar(128) NOT NULL,
  `po_number` varchar(128) DEFAULT NULL,
  `pay_number` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `contract_number` varchar(128) DEFAULT NULL,
  `pay_status` varchar(128) DEFAULT NULL,
  `check_status` varchar(128) DEFAULT NULL,
  `stock_status` varchar(128) DEFAULT NULL,
  `qc_status` varchar(128) DEFAULT NULL,
  `pay_type` varchar(128) DEFAULT NULL,
  `count_user` varchar(128) DEFAULT 'NEW',
  `doc_number` varchar(128) DEFAULT NULL,
  `vendor` varchar(128) DEFAULT NULL,
  `receipt_date` varchar(128) DEFAULT NULL,
  `qc_date` varchar(128) DEFAULT NULL,
  `good_qty` varchar(128) DEFAULT '0',
  `bad_qty` varchar(128) DEFAULT '0',
  `performance_bad_qty` varchar(128) DEFAULT '0',
  `structure_bad_qty` varchar(128) DEFAULT '0',
  `appearance_bad_qty` varchar(128) DEFAULT '0',
  `other_bad_qty` varchar(128) DEFAULT '0',
  `performance_bad_reason` varchar(128) DEFAULT NULL,
  `structure_bad_reason` varchar(128) DEFAULT NULL,
  `appearance_bad_reason` varchar(128) DEFAULT NULL,
  `other_bad_reason` varchar(128) DEFAULT NULL,
  `qc_image` varchar(512) DEFAULT NULL,
  `qc_sort` varchar(128) DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=284 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for purchase_statement_lab_order_lens_daily
-- ----------------------------
DROP TABLE IF EXISTS `purchase_statement_lab_order_lens_daily`;
CREATE TABLE `purchase_statement_lab_order_lens_daily` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `doc_type` varchar(20) NOT NULL,
  `doc_number` varchar(40) DEFAULT NULL,
  `status` varchar(40) NOT NULL,
  `base_entity` varchar(128) DEFAULT NULL,
  `type` varchar(20) NOT NULL,
  `order_number` varchar(128) DEFAULT NULL,
  `vendor` varchar(128) DEFAULT NULL,
  `workshop` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `order_number` (`order_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for purchase_statement_lab_order_lens_daily_line
-- ----------------------------
DROP TABLE IF EXISTS `purchase_statement_lab_order_lens_daily_line`;
CREATE TABLE `purchase_statement_lab_order_lens_daily_line` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `doc_type` varchar(20) NOT NULL,
  `doc_number` varchar(40) DEFAULT NULL,
  `status` varchar(40) NOT NULL,
  `base_entity` varchar(128) DEFAULT NULL,
  `type` varchar(20) NOT NULL,
  `pg_order_entity_id` varchar(128) DEFAULT NULL,
  `order_number` varchar(128) DEFAULT NULL,
  `lab_order_entity_id` varchar(128) DEFAULT NULL,
  `lab_number` varchar(128) DEFAULT NULL,
  `order_date` date DEFAULT NULL,
  `frame` varchar(128) DEFAULT NULL,
  `name` varchar(512) DEFAULT NULL,
  `quantity` int NOT NULL,
  `lens_sku` varchar(128) DEFAULT NULL,
  `lens_name` varchar(512) DEFAULT NULL,
  `coating_sku` varchar(128) DEFAULT NULL,
  `coating_name` varchar(512) DEFAULT NULL,
  `tint_sku` varchar(128) DEFAULT NULL,
  `tint_name` varchar(512) DEFAULT NULL,
  `pal_design_sku` varchar(128) DEFAULT NULL,
  `pal_design_name` varchar(512) DEFAULT NULL,
  `vendor` varchar(128) DEFAULT NULL,
  `workshop` varchar(128) DEFAULT NULL,
  `parent_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `purchase_statement_l_parent_id_f9528857_fk_purchase_` (`parent_id`),
  CONSTRAINT `purchase_statement_l_parent_id_f9528857_fk_purchase_` FOREIGN KEY (`parent_id`) REFERENCES `purchase_statement_lab_order_lens_daily` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for purchase_supplier
-- ----------------------------
DROP TABLE IF EXISTS `purchase_supplier`;
CREATE TABLE `purchase_supplier` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(20) NOT NULL,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `supplier_code` varchar(128) DEFAULT NULL,
  `supplier_name` varchar(128) DEFAULT NULL,
  `linkman` varchar(128) DEFAULT NULL,
  `telephone_number` varchar(128) DEFAULT NULL,
  `address` varchar(512) DEFAULT NULL,
  `supplier_type` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `supplier_code` (`supplier_code`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for qc_frame_reason
-- ----------------------------
DROP TABLE IF EXISTS `qc_frame_reason`;
CREATE TABLE `qc_frame_reason` (
  `id` int NOT NULL AUTO_INCREMENT,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `reason_code` varchar(128) DEFAULT NULL,
  `reason_name` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Table structure for qc_glasses_final_appearance_visual
-- ----------------------------
DROP TABLE IF EXISTS `qc_glasses_final_appearance_visual`;
CREATE TABLE `qc_glasses_final_appearance_visual` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `type` varchar(20) NOT NULL,
  `is_frame` tinyint(1) NOT NULL,
  `is_parts` tinyint(1) NOT NULL,
  `is_lens` tinyint(1) NOT NULL,
  `is_assembling` tinyint(1) NOT NULL,
  `is_plastic` tinyint(1) NOT NULL,
  `lab_number` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;

-- ----------------------------
-- Table structure for qc_glasses_final_inspection
-- ----------------------------
DROP TABLE IF EXISTS `qc_glasses_final_inspection`;
CREATE TABLE `qc_glasses_final_inspection` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `laborder_id` int NOT NULL,
  `lab_number` varchar(128) DEFAULT NULL,
  `type` varchar(20) NOT NULL,
  `laborder_entity_id` int DEFAULT NULL,
  `prescripiton_actual_entity_id` int DEFAULT NULL,
  `is_qualified` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `qc_glasses_final_inspection_laborder_id_4c53999b_uniq` (`laborder_id`),
  KEY `qc_glasses_final_ins_prescripiton_actual__33b7ea31_fk_qc_prescr` (`prescripiton_actual_entity_id`),
  KEY `qc_glasses_final_inspection_laborder_entity_id_a1589eb6` (`laborder_entity_id`),
  CONSTRAINT `qc_glasses_final_ins_laborder_entity_id_a1589eb6_fk_oms_labor` FOREIGN KEY (`laborder_entity_id`) REFERENCES `oms_laborder` (`id`),
  CONSTRAINT `qc_glasses_final_ins_prescripiton_actual__33b7ea31_fk_qc_prescr` FOREIGN KEY (`prescripiton_actual_entity_id`) REFERENCES `qc_prescripiton_actual` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for qc_glasses_final_inspection_log
-- ----------------------------
DROP TABLE IF EXISTS `qc_glasses_final_inspection_log`;
CREATE TABLE `qc_glasses_final_inspection_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `laborder_id` int NOT NULL,
  `lab_number` varchar(128) DEFAULT NULL,
  `type` varchar(20) NOT NULL,
  `reason_code` varchar(20) DEFAULT NULL,
  `reason` varchar(512) DEFAULT NULL,
  `laborder_entity_id` int DEFAULT NULL,
  `prescripiton_actual_entity_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `qc_glasses_final_ins_laborder_entity_id_1109e551_fk_oms_labor` (`laborder_entity_id`),
  KEY `qc_glasses_final_ins_prescripiton_actual__409e26c2_fk_qc_prescr` (`prescripiton_actual_entity_id`),
  CONSTRAINT `qc_glasses_final_ins_laborder_entity_id_1109e551_fk_oms_labor` FOREIGN KEY (`laborder_entity_id`) REFERENCES `oms_laborder` (`id`),
  CONSTRAINT `qc_glasses_final_ins_prescripiton_actual__409e26c2_fk_qc_prescr` FOREIGN KEY (`prescripiton_actual_entity_id`) REFERENCES `qc_prescripiton_actual` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for qc_glasses_final_inspection_technique
-- ----------------------------
DROP TABLE IF EXISTS `qc_glasses_final_inspection_technique`;
CREATE TABLE `qc_glasses_final_inspection_technique` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `lab_number` varchar(128) DEFAULT NULL,
  `type` varchar(20) NOT NULL,
  `laborder_id` int NOT NULL,
  `pd` decimal(5,1) DEFAULT NULL,
  `is_singgle_pd` tinyint(1) NOT NULL,
  `od_pd` decimal(5,1) DEFAULT NULL,
  `os_pd` decimal(5,1) DEFAULT NULL,
  `blue_blocker` tinyint(1) NOT NULL,
  `polarized` tinyint(1) NOT NULL,
  `light_responsive` tinyint(1) NOT NULL,
  `light_responsive_color` varchar(40) DEFAULT NULL,
  `co` tinyint(1) NOT NULL,
  `tint` tinyint(1) NOT NULL,
  `is_qualified` tinyint(1) NOT NULL,
  `laborder_entity_id` int DEFAULT NULL,
  `asmbl_seght` int DEFAULT '0',
  `is_gradient` tinyint(1) NOT NULL DEFAULT '0',
  `od_base` decimal(5,2) DEFAULT '0.00',
  `od_prism` decimal(5,2) DEFAULT '0.00',
  `os_base` decimal(5,2) DEFAULT '0.00',
  `os_prism` decimal(5,2) DEFAULT '0.00',
  `tint_deepness` decimal(5,0) DEFAULT '0',
  `od_base1` decimal(5,2) DEFAULT '0.00',
  `od_prism1` decimal(5,2) DEFAULT '0.00',
  `os_base1` decimal(5,2) DEFAULT '0.00',
  `os_prism1` decimal(5,2) DEFAULT '0.00',
  `is_d_thin` tinyint(1) NOT NULL,
  `od_asmbl_seght` int DEFAULT NULL,
  `os_asmbl_seght` int DEFAULT NULL,
  `assembler_id` int DEFAULT NULL,
  `clipon_qty` int NOT NULL,
  `coatings` varchar(32) NOT NULL,
  `is_near_light` tinyint(1) NOT NULL,
  `is_polishing` tinyint(1) NOT NULL,
  `is_special_handling` tinyint(1) NOT NULL,
  `od_sub_mirrors_height` int DEFAULT NULL,
  `od_tint_deepness` decimal(5,0) DEFAULT NULL,
  `os_sub_mirrors_height` int DEFAULT NULL,
  `os_tint_deepness` decimal(5,0) DEFAULT NULL,
  `npd` decimal(5,1) DEFAULT NULL,
  `od_npd` decimal(5,1) DEFAULT NULL,
  `os_npd` decimal(5,1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `laborder_id` (`laborder_id`),
  KEY `qc_glasses_final_ins_laborder_entity_id_fbbb147d_fk_oms_labor` (`laborder_entity_id`),
  CONSTRAINT `qc_glasses_final_ins_laborder_entity_id_fbbb147d_fk_oms_labor` FOREIGN KEY (`laborder_entity_id`) REFERENCES `oms_laborder` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=77899 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for qc_glasses_final_inspection_visual
-- ----------------------------
DROP TABLE IF EXISTS `qc_glasses_final_inspection_visual`;
CREATE TABLE `qc_glasses_final_inspection_visual` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `type` varchar(20) NOT NULL,
  `laborder_id` int NOT NULL,
  `lab_number` varchar(128) DEFAULT NULL,
  `is_qualified` tinyint(1) NOT NULL,
  `laborder_entity_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `laborder_id` (`laborder_id`),
  KEY `qc_glasses_final_ins_laborder_entity_id_5f82e18f_fk_oms_labor` (`laborder_entity_id`),
  CONSTRAINT `qc_glasses_final_ins_laborder_entity_id_5f82e18f_fk_oms_labor` FOREIGN KEY (`laborder_entity_id`) REFERENCES `oms_laborder` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for qc_glasses_return
-- ----------------------------
DROP TABLE IF EXISTS `qc_glasses_return`;
CREATE TABLE `qc_glasses_return` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `lab_order_entity` varchar(128) DEFAULT NULL,
  `lab_number` varchar(128) DEFAULT NULL,
  `status` varchar(128) DEFAULT NULL,
  `base_entity` varchar(128) DEFAULT NULL,
  `type` varchar(20) NOT NULL,
  `comments` longtext,
  `is_qualified` tinyint(1) NOT NULL,
  `reason_code` varchar(20) DEFAULT NULL,
  `reason` varchar(512) DEFAULT NULL,
  `lens_return` varchar(20) DEFAULT NULL,
  `lens_return_qty` int NOT NULL,
  `idei_frame` varchar(20) DEFAULT NULL,
  `idei_lens_l` varchar(20) DEFAULT NULL,
  `idei_lens_r` varchar(20) DEFAULT NULL,
  `assembler_id` varchar(20) NOT NULL,
  `assembler_user_code` varchar(20) NOT NULL,
  `assembler_user_name` varchar(20) NOT NULL,
  `doc_type` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2016 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for qc_glasses_unqualified_items
-- ----------------------------
DROP TABLE IF EXISTS `qc_glasses_unqualified_items`;
CREATE TABLE `qc_glasses_unqualified_items` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(20) NOT NULL,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `item_id` int NOT NULL,
  `item_name` varchar(128) DEFAULT NULL,
  `appearance_id` int NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- ----------------------------
-- Table structure for qc_glasses_unqualified_items_config
-- ----------------------------
DROP TABLE IF EXISTS `qc_glasses_unqualified_items_config`;
CREATE TABLE `qc_glasses_unqualified_items_config` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(20) NOT NULL,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `item_name` varchar(128) DEFAULT NULL,
  `item_type` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- ----------------------------
-- Table structure for qc_laborder_accessories
-- ----------------------------
DROP TABLE IF EXISTS `qc_laborder_accessories`;
CREATE TABLE `qc_laborder_accessories` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `type` varchar(20) NOT NULL,
  `laborder_entity_id` varchar(128) DEFAULT NULL,
  `lab_number` varchar(128) DEFAULT NULL,
  `tag` varchar(256) DEFAULT NULL,
  `key` varchar(256) DEFAULT NULL,
  `base_url` varchar(1024) DEFAULT NULL,
  `object_url` varchar(128) DEFAULT NULL,
  `accessories_type` varchar(20) DEFAULT NULL,
  `qc_created_at` varchar(128) DEFAULT NULL,
  `qc_updated_at` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=15554 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for qc_lens_collection
-- ----------------------------
DROP TABLE IF EXISTS `qc_lens_collection`;
CREATE TABLE `qc_lens_collection` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `laborder_id` int NOT NULL,
  `lab_number` varchar(128) DEFAULT NULL,
  `type` varchar(20) NOT NULL,
  `laborder_entity_id` int DEFAULT NULL,
  `pc_entity_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `qc_lens_collection_laborder_entity_id_00d019c3_fk_oms_labor` (`laborder_entity_id`),
  KEY `qc_lens_collection_pc_entity_id_d662ebd2_fk_qc_prelim` (`pc_entity_id`),
  CONSTRAINT `qc_lens_collection_laborder_entity_id_00d019c3_fk_oms_labor` FOREIGN KEY (`laborder_entity_id`) REFERENCES `oms_laborder` (`id`),
  CONSTRAINT `qc_lens_collection_pc_entity_id_d662ebd2_fk_qc_prelim` FOREIGN KEY (`pc_entity_id`) REFERENCES `qc_preliminary_checking` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=52263 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for qc_lens_reason
-- ----------------------------
DROP TABLE IF EXISTS `qc_lens_reason`;
CREATE TABLE `qc_lens_reason` (
  `id` int NOT NULL AUTO_INCREMENT,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `reason_code` varchar(128) DEFAULT NULL,
  `reason_name` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for qc_lens_registration
-- ----------------------------
DROP TABLE IF EXISTS `qc_lens_registration`;
CREATE TABLE `qc_lens_registration` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `laborder_id` int NOT NULL,
  `lab_number` varchar(128) DEFAULT NULL,
  `type` varchar(20) NOT NULL,
  `laborder_entity_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `qc_lens_registration_laborder_entity_id_15f6f12f_fk_oms_labor` (`laborder_entity_id`),
  CONSTRAINT `qc_lens_registration_laborder_entity_id_15f6f12f_fk_oms_labor` FOREIGN KEY (`laborder_entity_id`) REFERENCES `oms_laborder` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=179887 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for qc_lens_return
-- ----------------------------
DROP TABLE IF EXISTS `qc_lens_return`;
CREATE TABLE `qc_lens_return` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `laborder_id` int NOT NULL,
  `lab_number` varchar(128) DEFAULT NULL,
  `type` varchar(20) NOT NULL,
  `reason` varchar(512) DEFAULT NULL,
  `laborder_entity_id` int DEFAULT NULL,
  `pc_entity_id` int DEFAULT NULL,
  `reason_code` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `qc_lens_return_laborder_entity_id_7a024c14_fk_oms_laborder_id` (`laborder_entity_id`),
  KEY `qc_lens_return_pc_entity_id_3670369d_fk_qc_prelim` (`pc_entity_id`),
  CONSTRAINT `qc_lens_return_laborder_entity_id_7a024c14_fk_oms_laborder_id` FOREIGN KEY (`laborder_entity_id`) REFERENCES `oms_laborder` (`id`),
  CONSTRAINT `qc_lens_return_pc_entity_id_3670369d_fk_qc_prelim` FOREIGN KEY (`pc_entity_id`) REFERENCES `qc_preliminary_checking` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5186 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for qc_preliminary_checking
-- ----------------------------
DROP TABLE IF EXISTS `qc_preliminary_checking`;
CREATE TABLE `qc_preliminary_checking` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `laborder_id` int NOT NULL,
  `lab_number` varchar(128) DEFAULT NULL,
  `type` varchar(20) NOT NULL,
  `laborder_entity_id` int DEFAULT NULL,
  `prescripiton_actual_entity_id` int DEFAULT NULL,
  `is_qualified` tinyint(1) NOT NULL,
  `reason` varchar(512) DEFAULT NULL,
  `reason_code` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `qc_preliminary_check_laborder_entity_id_95522043_fk_oms_labor` (`laborder_entity_id`),
  KEY `qc_preliminary_check_prescripiton_actual__81de4467_fk_qc_prescr` (`prescripiton_actual_entity_id`),
  CONSTRAINT `qc_preliminary_check_laborder_entity_id_95522043_fk_oms_labor` FOREIGN KEY (`laborder_entity_id`) REFERENCES `oms_laborder` (`id`),
  CONSTRAINT `qc_preliminary_check_prescripiton_actual__81de4467_fk_qc_prescr` FOREIGN KEY (`prescripiton_actual_entity_id`) REFERENCES `qc_prescripiton_actual` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=53627 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for qc_prescripiton_actual
-- ----------------------------
DROP TABLE IF EXISTS `qc_prescripiton_actual`;
CREATE TABLE `qc_prescripiton_actual` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `profile_id` varchar(128) DEFAULT NULL,
  `profile_name` varchar(255) DEFAULT NULL,
  `profile_prescription_id` varchar(128) DEFAULT NULL,
  `prescription_id` varchar(40) DEFAULT NULL,
  `prescription_name` varchar(128) DEFAULT NULL,
  `prescription_type` varchar(128) DEFAULT NULL,
  `od_sph` decimal(5,2) NOT NULL,
  `od_cyl` decimal(5,2) NOT NULL,
  `od_axis` decimal(5,0) NOT NULL,
  `os_sph` decimal(5,2) NOT NULL,
  `os_cyl` decimal(5,2) NOT NULL,
  `os_axis` decimal(5,0) NOT NULL,
  `pd` decimal(5,1) NOT NULL,
  `is_singgle_pd` tinyint(1) NOT NULL,
  `od_pd` decimal(5,1) NOT NULL,
  `os_pd` decimal(5,1) NOT NULL,
  `od_add` decimal(5,2) NOT NULL,
  `os_add` decimal(5,2) NOT NULL,
  `od_prism` decimal(5,2) DEFAULT NULL,
  `od_base` varchar(40) DEFAULT NULL,
  `os_prism` decimal(5,2) DEFAULT NULL,
  `os_base` varchar(40) DEFAULT NULL,
  `used_for` varchar(40) DEFAULT NULL,
  `type` varchar(20) NOT NULL,
  `od_base1` varchar(40) DEFAULT NULL,
  `od_prism1` decimal(5,2) DEFAULT '0.00',
  `os_base1` varchar(40) DEFAULT NULL,
  `os_prism1` decimal(5,2) DEFAULT '0.00',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=92905 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for ra_entity
-- ----------------------------
DROP TABLE IF EXISTS `ra_entity`;
CREATE TABLE `ra_entity` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `type` varchar(20) NOT NULL,
  `base_entity` int NOT NULL,
  `base_type` varchar(20) NOT NULL,
  `state` varchar(20) DEFAULT NULL,
  `status` varchar(20) DEFAULT NULL,
  `ra_type` varchar(20) DEFAULT NULL,
  `label_id` varchar(128) DEFAULT NULL,
  `order_number` varchar(128) DEFAULT NULL,
  `order_number_part` varchar(128) DEFAULT NULL,
  `customer_name` varchar(128) DEFAULT NULL,
  `ticket_id` varchar(128) DEFAULT NULL,
  `ticket_id_part` varchar(128) DEFAULT NULL,
  `tracking_code` varchar(256) DEFAULT NULL,
  `quantity` int NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `transaction_id` varchar(256) DEFAULT NULL,
  `warehouse_code` varchar(128) DEFAULT NULL,
  `warehouse_name` varchar(128) DEFAULT NULL,
  `is_label` tinyint(1) NOT NULL,
  `is_stock` tinyint(1) NOT NULL,
  `is_refund` tinyint(1) NOT NULL,
  `label_at` datetime(6) DEFAULT NULL,
  `stock_at` datetime(6) DEFAULT NULL,
  `refund_at` datetime(6) DEFAULT NULL,
  `closed_at` datetime(6) DEFAULT NULL,
  `completed_at` datetime(6) DEFAULT NULL,
  `approved_at` datetime(6) DEFAULT NULL,
  `canceled_at` datetime(6) DEFAULT NULL,
  `is_approved` tinyint(1) NOT NULL,
  `email_to` varchar(256) DEFAULT NULL,
  `location` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=33 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Table structure for ra_item
-- ----------------------------
DROP TABLE IF EXISTS `ra_item`;
CREATE TABLE `ra_item` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `type` varchar(20) NOT NULL,
  `base_entity` int NOT NULL,
  `frame` varchar(128) DEFAULT NULL,
  `quantity` int NOT NULL,
  `price` decimal(10,2) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=24 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Table structure for ra_log
-- ----------------------------
DROP TABLE IF EXISTS `ra_log`;
CREATE TABLE `ra_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `type` varchar(20) NOT NULL,
  `base_entity` int NOT NULL,
  `base_type` varchar(20) NOT NULL,
  `action` varchar(128) DEFAULT NULL,
  `action_value` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=85 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Table structure for report_assembling_lab_orders
-- ----------------------------
DROP TABLE IF EXISTS `report_assembling_lab_orders`;
CREATE TABLE `report_assembling_lab_orders` (
  `lab_number` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `create_at` datetime(6) NOT NULL,
  `status` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `vendor` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `workshop` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `frame` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `quantity` int NOT NULL,
  `act_lens_sku` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `act_lens_name` varchar(512) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `order_date` date DEFAULT NULL,
  `get_purchase_date` datetime(6) DEFAULT NULL,
  `hours_of_purchase` bigint DEFAULT NULL,
  `level_of_purchase` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- ----------------------------
-- Table structure for report_customize_report
-- ----------------------------
DROP TABLE IF EXISTS `report_customize_report`;
CREATE TABLE `report_customize_report` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(20) NOT NULL,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `index` int NOT NULL,
  `group` varchar(128) DEFAULT NULL,
  `code` varchar(128) NOT NULL,
  `name` varchar(512) DEFAULT NULL,
  `parameters_sample` longtext,
  `is_need_parameters` tinyint(1) NOT NULL,
  `sql_script` longtext,
  `comments` longtext,
  PRIMARY KEY (`id`),
  UNIQUE KEY `report_customize_report_code_4d7e1e3e_uniq` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=53 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for report_customize_report_200613
-- ----------------------------
DROP TABLE IF EXISTS `report_customize_report_200613`;
CREATE TABLE `report_customize_report_200613` (
  `id` int NOT NULL DEFAULT '0',
  `type` varchar(20) NOT NULL,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `index` int NOT NULL,
  `group` varchar(128) DEFAULT NULL,
  `code` varchar(128) NOT NULL,
  `name` varchar(512) DEFAULT NULL,
  `parameters_sample` longtext,
  `is_need_parameters` tinyint(1) NOT NULL,
  `sql_script` longtext,
  `comments` longtext
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for report_customize_report_query_history
-- ----------------------------
DROP TABLE IF EXISTS `report_customize_report_query_history`;
CREATE TABLE `report_customize_report_query_history` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(20) NOT NULL,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `code` varchar(128) NOT NULL,
  `name` varchar(512) DEFAULT NULL,
  `event_type` varchar(128) DEFAULT NULL,
  `sql_script` longtext,
  `results_count` int NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2441 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for secondattr
-- ----------------------------
DROP TABLE IF EXISTS `secondattr`;
CREATE TABLE `secondattr` (
  `second_attr_id` int NOT NULL,
  `create_time` datetime(6) NOT NULL,
  `update_time` datetime(6) NOT NULL,
  `attr_name` varchar(20) NOT NULL,
  `second_all_attr_id_id` int NOT NULL,
  PRIMARY KEY (`second_attr_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Table structure for shipment_collection_glasses
-- ----------------------------
DROP TABLE IF EXISTS `shipment_collection_glasses`;
CREATE TABLE `shipment_collection_glasses` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `user_name` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `order_number` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `lab_order_entity` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `lab_number` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `status` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `base_entity` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `type` varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `comments` longtext CHARACTER SET utf8 COLLATE utf8_general_ci,
  `send_from` varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `send_to` varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `collection_number` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=35522 DEFAULT CHARSET=utf8 ROW_FORMAT=COMPACT;

-- ----------------------------
-- Table structure for shipment_pre_delivery
-- ----------------------------
DROP TABLE IF EXISTS `shipment_pre_delivery`;
CREATE TABLE `shipment_pre_delivery` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `type` varchar(20) NOT NULL,
  `status` varchar(40) NOT NULL,
  `e_count` int NOT NULL,
  `express_count` int NOT NULL,
  `other_count` int NOT NULL,
  `w_count` int NOT NULL,
  `is_combine` tinyint(1) NOT NULL,
  `shipping_method` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1415 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for shipment_pre_delivery_line
-- ----------------------------
DROP TABLE IF EXISTS `shipment_pre_delivery_line`;
CREATE TABLE `shipment_pre_delivery_line` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `type` varchar(20) NOT NULL,
  `is_picked` tinyint(1) NOT NULL,
  `lab_order_entity_id` int DEFAULT NULL,
  `pg_order_entity_id` int DEFAULT NULL,
  `pre_delivery_entity_id` int DEFAULT NULL,
  `ship_region` varchar(20) NOT NULL,
  `is_post` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `shipment_pre_deliver_lab_order_entity_id_ea9da633_fk_oms_labor` (`lab_order_entity_id`),
  KEY `shipment_pre_deliver_pg_order_entity_id_e1afc83b_fk_oms_pgord` (`pg_order_entity_id`),
  KEY `shipment_pre_deliver_pre_delivery_entity__3165fb60_fk_shipment_` (`pre_delivery_entity_id`),
  CONSTRAINT `shipment_pre_deliver_lab_order_entity_id_ea9da633_fk_oms_labor` FOREIGN KEY (`lab_order_entity_id`) REFERENCES `oms_laborder` (`id`),
  CONSTRAINT `shipment_pre_deliver_pg_order_entity_id_e1afc83b_fk_oms_pgord` FOREIGN KEY (`pg_order_entity_id`) REFERENCES `oms_pgorder` (`id`),
  CONSTRAINT `shipment_pre_deliver_pre_delivery_entity__3165fb60_fk_shipment_` FOREIGN KEY (`pre_delivery_entity_id`) REFERENCES `shipment_pre_delivery` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=298670 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for sku
-- ----------------------------
DROP TABLE IF EXISTS `sku`;
CREATE TABLE `sku` (
  `sku_id` int NOT NULL AUTO_INCREMENT,
  `create_time` datetime(6) NOT NULL,
  `update_time` datetime(6) NOT NULL,
  `sku_num` varchar(30) NOT NULL,
  `sku_value` varchar(255) NOT NULL,
  `sku_price` varchar(20) NOT NULL,
  `sku_stock` varchar(20) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `sku_status` int NOT NULL,
  PRIMARY KEY (`sku_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Table structure for spu
-- ----------------------------
DROP TABLE IF EXISTS `spu`;
CREATE TABLE `spu` (
  `id` int NOT NULL AUTO_INCREMENT,
  `spu_name` varchar(20) DEFAULT NULL,
  `spu_value` varchar(50) DEFAULT NULL,
  `spu_type` varchar(50) DEFAULT NULL,
  `create_time` datetime(6) NOT NULL,
  `update_time` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Table structure for vender_lens_specmap
-- ----------------------------
DROP TABLE IF EXISTS `vender_lens_specmap`;
CREATE TABLE `vender_lens_specmap` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `user_name` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `comments` varchar(512) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `inner_code` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `inner_name` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `vendor` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `outer_code` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `outer_name` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `technology_type` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `active` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8 ROW_FORMAT=COMPACT;

-- ----------------------------
-- Table structure for vendor_wc_order_status
-- ----------------------------
DROP TABLE IF EXISTS `vendor_wc_order_status`;
CREATE TABLE `vendor_wc_order_status` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `order_number` varchar(128) DEFAULT NULL,
  `reference_code` varchar(128) DEFAULT NULL,
  `reference_code_2` varchar(128) DEFAULT NULL,
  `status_code` varchar(36) DEFAULT NULL,
  `status_value` varchar(20) DEFAULT NULL,
  `status_updated_at` varchar(36) DEFAULT NULL,
  `is_sync` tinyint(1) NOT NULL,
  `type` varchar(20) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=77176 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for vendor_wxorderstatus
-- ----------------------------
DROP TABLE IF EXISTS `vendor_wxorderstatus`;
CREATE TABLE `vendor_wxorderstatus` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `order_number` varchar(128) DEFAULT NULL,
  `reference_code` varchar(128) DEFAULT NULL,
  `reference_code_2` varchar(128) DEFAULT NULL,
  `status_code` varchar(36) DEFAULT NULL,
  `status_value` varchar(20) DEFAULT NULL,
  `status_updated_at` varchar(36) DEFAULT NULL,
  `is_sync` tinyint(1) NOT NULL,
  `type` varchar(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `id` (`id`) USING BTREE,
  KEY `order_number` (`order_number`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=43759 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Table structure for wms_channel
-- ----------------------------
DROP TABLE IF EXISTS `wms_channel`;
CREATE TABLE `wms_channel` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `type` varchar(20) NOT NULL,
  `code` varchar(40) NOT NULL,
  `name` varchar(256) NOT NULL,
  `location` varchar(512) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for wms_customer_flatrate
-- ----------------------------
DROP TABLE IF EXISTS `wms_customer_flatrate`;
CREATE TABLE `wms_customer_flatrate` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) CHARACTER SET latin1 COLLATE latin1_swedish_ci DEFAULT NULL,
  `user_name` varchar(128) CHARACTER SET latin1 COLLATE latin1_swedish_ci DEFAULT NULL,
  `comments` varchar(512) CHARACTER SET latin1 COLLATE latin1_swedish_ci DEFAULT NULL,
  `type` varchar(20) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `name` varchar(256) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=latin1 ROW_FORMAT=COMPACT;

-- ----------------------------
-- Table structure for wms_inventory_delivery
-- ----------------------------
DROP TABLE IF EXISTS `wms_inventory_delivery`;
CREATE TABLE `wms_inventory_delivery` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `type` varchar(20) NOT NULL,
  `sku` varchar(40) DEFAULT NULL,
  `name` varchar(128) NOT NULL,
  `quantity` decimal(10,0) NOT NULL,
  `base_entity` varchar(128) DEFAULT NULL,
  `doc_number` varchar(40) DEFAULT NULL,
  `doc_type` varchar(20) NOT NULL,
  `status` varchar(128) DEFAULT NULL,
  `warehouse_id` int DEFAULT NULL,
  `lab_number` varchar(128) DEFAULT NULL,
  `warehouse_code` varchar(40) DEFAULT NULL,
  `warehouse_name` varchar(256) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `wms_inventory_delivery_warehouse_id_5555c761_fk_wms_warehouse_id` (`warehouse_id`),
  CONSTRAINT `wms_inventory_delivery_warehouse_id_5555c761_fk_wms_warehouse_id` FOREIGN KEY (`warehouse_id`) REFERENCES `wms_warehouse` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=269650 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for wms_inventory_delivery_lens
-- ----------------------------
DROP TABLE IF EXISTS `wms_inventory_delivery_lens`;
CREATE TABLE `wms_inventory_delivery_lens` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `user_name` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `comments` varchar(512) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `doc_type` varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `doc_number` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `status` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `base_entity` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `type` varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `sku` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `name` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `quantity` decimal(10,0) NOT NULL,
  `warehouse_code` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `warehouse_name` varchar(256) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `warehouse_id` int DEFAULT NULL,
  `base_sku` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `lab_number` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `add` decimal(5,2) NOT NULL,
  `cyl` decimal(5,2) NOT NULL,
  `luminosity_type` varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `sph` decimal(5,2) NOT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `wms_inventory_delive_warehouse_id_b47ad926_fk_wms_wareh` (`warehouse_id`) USING BTREE,
  CONSTRAINT `wms_inventory_delive_warehouse_id_b47ad926_fk_wms_wareh` FOREIGN KEY (`warehouse_id`) REFERENCES `wms_warehouse` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=141830 DEFAULT CHARSET=utf8 ROW_FORMAT=COMPACT;

-- ----------------------------
-- Table structure for wms_inventory_receipt
-- ----------------------------
DROP TABLE IF EXISTS `wms_inventory_receipt`;
CREATE TABLE `wms_inventory_receipt` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `type` varchar(20) NOT NULL,
  `sku` varchar(40) DEFAULT NULL,
  `name` varchar(128) NOT NULL,
  `quantity` decimal(10,0) NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `base_entity` varchar(128) DEFAULT NULL,
  `doc_number` varchar(40) DEFAULT NULL,
  `doc_type` varchar(20) NOT NULL,
  `status` varchar(128) DEFAULT NULL,
  `warehouse_id` int DEFAULT NULL,
  `lab_number` varchar(128) DEFAULT NULL,
  `warehouse_code` varchar(40) DEFAULT NULL,
  `warehouse_name` varchar(256) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `wms_inventory_receipt_warehouse_id_4c0ef550_fk_wms_warehouse_id` (`warehouse_id`),
  CONSTRAINT `wms_inventory_receipt_warehouse_id_4c0ef550_fk_wms_warehouse_id` FOREIGN KEY (`warehouse_id`) REFERENCES `wms_warehouse` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=23448 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for wms_inventory_receipt_lens
-- ----------------------------
DROP TABLE IF EXISTS `wms_inventory_receipt_lens`;
CREATE TABLE `wms_inventory_receipt_lens` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `user_name` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `comments` varchar(512) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `doc_type` varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `doc_number` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `status` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `base_entity` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `type` varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `sku` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `name` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `quantity` decimal(10,0) NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `warehouse_code` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `warehouse_name` varchar(256) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `warehouse_id` int DEFAULT NULL,
  `base_sku` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `lab_number` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `add` decimal(5,2) NOT NULL,
  `cyl` decimal(5,2) NOT NULL,
  `luminosity_type` varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `sph` decimal(5,2) NOT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `wms_inventory_receip_warehouse_id_10cba73f_fk_wms_wareh` (`warehouse_id`) USING BTREE,
  CONSTRAINT `wms_inventory_receip_warehouse_id_10cba73f_fk_wms_wareh` FOREIGN KEY (`warehouse_id`) REFERENCES `wms_warehouse` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=15349 DEFAULT CHARSET=utf8 ROW_FORMAT=COMPACT;

-- ----------------------------
-- Table structure for wms_inventory_struct
-- ----------------------------
DROP TABLE IF EXISTS `wms_inventory_struct`;
CREATE TABLE `wms_inventory_struct` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `type` varchar(20) NOT NULL,
  `sku` varchar(40) DEFAULT NULL,
  `name` varchar(128) NOT NULL,
  `quantity` decimal(10,0) NOT NULL,
  `web_kids_quantity` decimal(10,0) NOT NULL,
  `web_men_quantity` decimal(10,0) NOT NULL,
  `web_women_quantity` decimal(10,0) NOT NULL,
  `web_kids_is_in_stock` tinyint(1) NOT NULL,
  `web_men_is_in_stock` tinyint(1) NOT NULL,
  `web_women_is_in_stock` tinyint(1) NOT NULL,
  `status` varchar(40) NOT NULL,
  `estimate_replenishment_date` date DEFAULT NULL,
  `retired` tinyint(1) NOT NULL,
  `location` varchar(128) DEFAULT NULL,
  `lock_quantity` decimal(10,0) DEFAULT '0',
  `reserve_quantity` decimal(10,0) DEFAULT '0',
  `ch_quantity` decimal(10,0) NOT NULL,
  `oms_web_diff` decimal(10,0) NOT NULL,
  `web_quantity` decimal(10,0) NOT NULL,
  `web_status` varchar(40) NOT NULL,
  `init_reserve_quantity` decimal(10,0) DEFAULT '0',
  `al_quantity` decimal(10,0) NOT NULL,
  `last_in_stock` varchar(128) NOT NULL,
  `last_in_stock_date` varchar(128) NOT NULL,
  `last_out_of_stock` varchar(128) NOT NULL,
  `last_out_of_stock_date` varchar(128) NOT NULL,
  `last_retired` varchar(128) NOT NULL,
  `last_retired_date` varchar(128) NOT NULL,
  `last_sign` varchar(128) NOT NULL,
  `last_sign_date` varchar(128) NOT NULL,
  `no_sale_quantity` decimal(10,0) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `sku` (`sku`)
) ENGINE=InnoDB AUTO_INCREMENT=2877 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for wms_inventory_struct_lens
-- ----------------------------
DROP TABLE IF EXISTS `wms_inventory_struct_lens`;
CREATE TABLE `wms_inventory_struct_lens` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `sku` varchar(40) DEFAULT NULL,
  `base_sku` varchar(40) DEFAULT NULL,
  `name` varchar(128) NOT NULL,
  `entity_id` varchar(20) DEFAULT NULL,
  `reference_code` varchar(128) DEFAULT NULL,
  `luminosity_type` varchar(20) DEFAULT NULL,
  `sph` decimal(5,2) NOT NULL,
  `cyl` decimal(5,2) NOT NULL,
  `add` decimal(5,2) NOT NULL,
  `diameter` int NOT NULL,
  `coating` varchar(20) NOT NULL,
  `quantity` int DEFAULT NULL,
  `location` varchar(128) DEFAULT NULL,
  `batch_number` varchar(20) DEFAULT NULL,
  `type` varchar(20) NOT NULL,
  `coating_color` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `entity_id` (`entity_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4284 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for wms_inventory_struct_lens_batch
-- ----------------------------
DROP TABLE IF EXISTS `wms_inventory_struct_lens_batch`;
CREATE TABLE `wms_inventory_struct_lens_batch` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `sku` varchar(40) DEFAULT NULL,
  `base_sku` varchar(40) DEFAULT NULL,
  `name` varchar(128) NOT NULL,
  `reference_code` varchar(128) DEFAULT NULL,
  `luminosity_type` varchar(20) DEFAULT NULL,
  `sph` decimal(5,2) NOT NULL,
  `cyl` decimal(5,2) NOT NULL,
  `add` decimal(5,2) NOT NULL,
  `diameter` int NOT NULL,
  `coating` varchar(20) NOT NULL,
  `quantity` int DEFAULT NULL,
  `location` varchar(128) DEFAULT NULL,
  `batch_number` varchar(20) DEFAULT NULL,
  `type` varchar(20) NOT NULL,
  `entity_id` varchar(20) DEFAULT NULL,
  `warehouse_code` varchar(40) DEFAULT NULL,
  `warehouse_name` varchar(256) DEFAULT NULL,
  `coating_color` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8961 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for wms_inventory_struct_warehouse
-- ----------------------------
DROP TABLE IF EXISTS `wms_inventory_struct_warehouse`;
CREATE TABLE `wms_inventory_struct_warehouse` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `name` varchar(128) NOT NULL,
  `quantity` decimal(10,0) NOT NULL,
  `type` varchar(20) NOT NULL,
  `sku` varchar(40) DEFAULT NULL,
  `warehouse_code` varchar(40) NOT NULL,
  `warehouse_name` varchar(256) NOT NULL,
  `location` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5895 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for wms_lockers_config
-- ----------------------------
DROP TABLE IF EXISTS `wms_lockers_config`;
CREATE TABLE `wms_lockers_config` (
  `id` int NOT NULL AUTO_INCREMENT,
  `glasses_max_limit` int NOT NULL,
  `lockers_max_limit` int NOT NULL,
  `storage_location` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `is_vender` tinyint(1) NOT NULL,
  `lockers_min_limit` int NOT NULL,
  `ship_direction` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8 ROW_FORMAT=COMPACT;

-- ----------------------------
-- Table structure for wms_lockers_item
-- ----------------------------
DROP TABLE IF EXISTS `wms_lockers_item`;
CREATE TABLE `wms_lockers_item` (
  `id` int NOT NULL AUTO_INCREMENT,
  `lab_number` varchar(1024) NOT NULL,
  `order_number` varchar(1024) NOT NULL,
  `vendor` varchar(1024) NOT NULL,
  `storage_location` varchar(128) DEFAULT NULL,
  `locker_num` varchar(128) DEFAULT NULL,
  `create_at` datetime(6) NOT NULL,
  `username` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=97241 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for wms_product_frame
-- ----------------------------
DROP TABLE IF EXISTS `wms_product_frame`;
CREATE TABLE `wms_product_frame` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `product_type` varchar(15) NOT NULL,
  `sku` varchar(40) DEFAULT NULL,
  `name` varchar(128) NOT NULL,
  `type` varchar(20) NOT NULL,
  `frame_type` varchar(20) NOT NULL,
  `fe` decimal(10,2) NOT NULL,
  `fh` decimal(10,2) NOT NULL,
  `fb` decimal(10,2) NOT NULL,
  `ed` decimal(10,2) NOT NULL,
  `ct` decimal(10,2) NOT NULL,
  `parent_id` int DEFAULT NULL,
  `base_price` decimal(10,2) NOT NULL,
  `web_created_at` datetime(6) DEFAULT NULL,
  `image` varchar(1024) DEFAULT NULL,
  `thumbnail` varchar(1024) DEFAULT NULL,
  `sku_specs` varchar(128) DEFAULT NULL,
  `dbl` decimal(10,2) NOT NULL DEFAULT '0.00',
  `etyp` varchar(128) DEFAULT '',
  `file_path` varchar(128) DEFAULT '',
  `fmat` varchar(128) DEFAULT '',
  `fsha` varchar(128) DEFAULT '',
  `is_activate_vca_id` int NOT NULL DEFAULT '0',
  `l_a` decimal(10,2) NOT NULL DEFAULT '0.00',
  `l_b` decimal(10,2) NOT NULL DEFAULT '0.00',
  `l_circ` decimal(10,2) NOT NULL DEFAULT '0.00',
  `l_ed` decimal(10,2) NOT NULL DEFAULT '0.00',
  `l_ed_axis` decimal(10,2) NOT NULL DEFAULT '0.00',
  `l_fcrv` decimal(10,2) NOT NULL DEFAULT '0.00',
  `l_ztilt` decimal(10,2) NOT NULL DEFAULT '0.00',
  `product_num` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT '',
  `property_list` longtext,
  `r_a` decimal(10,2) NOT NULL DEFAULT '0.00',
  `r_b` decimal(10,2) NOT NULL DEFAULT '0.00',
  `r_circ` decimal(10,2) NOT NULL DEFAULT '0.00',
  `r_ed` decimal(10,2) NOT NULL DEFAULT '0.00',
  `r_ed_axis` decimal(10,2) NOT NULL DEFAULT '0.00',
  `r_fcrv` decimal(10,2) NOT NULL DEFAULT '0.00',
  `r_ztilt` decimal(10,2) NOT NULL DEFAULT '0.00',
  `temple` decimal(10,2) NOT NULL DEFAULT '0.00',
  `frame_width` decimal(10,2) NOT NULL DEFAULT '0.00',
  `is_nose_pad` int NOT NULL DEFAULT '0',
  `is_color_changing` int NOT NULL DEFAULT '0',
  `is_has_spring_hinges` int NOT NULL DEFAULT '0',
  `attribute_set` int NOT NULL DEFAULT '0',
  `is_variability` int NOT NULL DEFAULT '0',
  `is_already_synchronous` int NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `sku` (`sku`),
  KEY `wms_product_frame_parent_id_6db0b022_fk_wms_product_frame_id` (`parent_id`),
  CONSTRAINT `wms_product_frame_parent_id_6db0b022_fk_wms_product_frame_id` FOREIGN KEY (`parent_id`) REFERENCES `wms_product_frame` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2883 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for wms_product_lens
-- ----------------------------
DROP TABLE IF EXISTS `wms_product_lens`;
CREATE TABLE `wms_product_lens` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `user_name` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `comments` varchar(512) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `product_type` varchar(15) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `sku` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `name` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `type` varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `index` varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `parent_id` int DEFAULT NULL,
  `base_price` decimal(10,2) NOT NULL,
  `base_sku` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `brand` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `lens_type` varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `material` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `quantity` int NOT NULL,
  `series` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `coating` varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `diameter` int DEFAULT NULL,
  `grade` varchar(10) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `price` decimal(10,2) DEFAULT NULL,
  `vendor_code` varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `vendor_name` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `coating_color` varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `luminosity_type` varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `sku_specs` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `sku` (`sku`) USING BTREE,
  KEY `wms_product_lens_parent_id_b7d3fb70_fk_wms_product_lens_id` (`parent_id`) USING BTREE,
  CONSTRAINT `wms_product_lens_parent_id_b7d3fb70_fk_wms_product_lens_id` FOREIGN KEY (`parent_id`) REFERENCES `wms_product_lens` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8 ROW_FORMAT=COMPACT;

-- ----------------------------
-- Table structure for wms_warehouse
-- ----------------------------
DROP TABLE IF EXISTS `wms_warehouse`;
CREATE TABLE `wms_warehouse` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) DEFAULT NULL,
  `user_name` varchar(128) DEFAULT NULL,
  `comments` varchar(512) DEFAULT NULL,
  `type` varchar(20) NOT NULL,
  `code` varchar(40) NOT NULL,
  `name` varchar(256) NOT NULL,
  `location` varchar(512) NOT NULL,
  `used_to` varchar(15) NOT NULL,
  `is_sale` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=34 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for workshop_assembled
-- ----------------------------
DROP TABLE IF EXISTS `workshop_assembled`;
CREATE TABLE `workshop_assembled` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sequence` int NOT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `user_name` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `lab_order_entity` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `lab_number` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `status` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `base_entity` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `type` varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `comments` longtext CHARACTER SET utf8 COLLATE utf8_general_ci,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8 ROW_FORMAT=COMPACT;

-- ----------------------------
-- Table structure for workshop_assembler
-- ----------------------------
DROP TABLE IF EXISTS `workshop_assembler`;
CREATE TABLE `workshop_assembler` (
  `id` int NOT NULL AUTO_INCREMENT,
  `is_enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `user_code` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `user_name` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `department` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8 ROW_FORMAT=COMPACT;
