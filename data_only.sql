--
-- PostgreSQL database dump
--

-- Dumped from database version 14.17 (Homebrew)
-- Dumped by pg_dump version 14.17 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: pma_user
--

INSERT INTO public.users VALUES (9, 'liuq', 'pbkdf2:sha256:260000$dhaoKgs4gyRsSHZ1$b983e3ece7a926184d18a9068520d6f2c7faab3bc89bec71699ccb820731a6a7', NULL, NULL, 'liuq@evertac.net', '086-18918602455', NULL, false, '绩效经理', NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO public.users VALUES (10, 'zhaoyb', 'pbkdf2:sha256:260000$AV5NgfdIWdDTG4Uz$0e944b10f97bc6aa752c805d1f6fd84b247361e617a063132d6152d3e15e4c23', NULL, NULL, 'zhaoyb@evertac.net', '086-13636393979', NULL, false, '产品经理', NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO public.users VALUES (11, 'wanggang', 'pbkdf2:sha256:260000$a0WYvnl692CI4BAe$54651eced32adad3b1aed7d32ef959639f38b10ec1d8f701e29f09a4748ee14a', NULL, NULL, 'wanggang@evertac', '086-17521028583', NULL, false, '产品经理', NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO public.users VALUES (14, 'yangjj', 'pbkdf2:sha256:260000$9bwy4J5uCb2wyaub$363f11cb3c898111023923eccfe6b4969b89135cd4ce1c367050766352ce6847', NULL, NULL, 'yangjj@evertac.net', '086-13482779221', NULL, false, '销售经理', NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO public.users VALUES (15, 'lihuawei', 'pbkdf2:sha256:260000$fAiBwFx1PndurDCD$c138635b000b703a8ddadb02153469ab6b51659b508afd5fc4989a38e80fcd4a', NULL, NULL, 'lihuawei@evertac.net', '086-15601873096', NULL, false, '销售经理', NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO public.users VALUES (16, 'fanjing', 'pbkdf2:sha256:260000$COZaYSr1sfsejbsE$2db58d066601e9be70bdfaafc5ba2e66d30c47429862eb39c7e72e0d8f7dd9d1', NULL, NULL, 'fanjing@evertac.net', '086-13851869911', NULL, false, '销售经理', NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO public.users VALUES (17, 'zhouyj', 'pbkdf2:sha256:260000$MA0Tbf0LrCEcVHrQ$d5d3478c2cb21173532b2c00da189d813a232dff485f1ce77d5456b25e8a72de', NULL, NULL, 'zhouyj@evertac.net', '086-18923456355', NULL, false, '销售经理', NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO public.users VALUES (12, 'liuwei', 'pbkdf2:sha256:260000$gc28A7zTeStjtV6I$d38327eef9cca6212899853cfdc1e462a3b7489fed0358ad3a322201b8387b4d', '刘威', 'None', 'liuwei@evertac.net', '086-13361800535', 'None', false, 'solution_manager', NULL, NULL, NULL, NULL, false, NULL, NULL);
INSERT INTO public.users VALUES (5, 'admin', 'pbkdf2:sha256:260000$Mp3tpvbN3C9EOGx5$f02b46fae1e3f94c8c85647c0d8e2fb5cee35165b6a2dc826d6b14b0b73cc842', '系统管理员', 'bdb5e493', 'james.ni@evertacsolutions.com', '13003258568', '', false, 'admin', NULL, NULL, NULL, NULL, true, NULL, NULL);
INSERT INTO public.users VALUES (4, 'Vivian', 'pbkdf2:sha256:260000$DRioDDjduS4azHSv$e969f06f62a21b5815eb7aed15a8ffd11e79249de4b2f1017399638beecd2900', '张琰', 'bdb5e493', 'vivian@evertac.net', '086-15692111122', '财务部', true, 'finace_director', NULL, NULL, NULL, NULL, true, NULL, NULL);
INSERT INTO public.users VALUES (7, 'xuhao', 'pbkdf2:sha256:260000$q4uzHvR8BRv1tmCd$0ccbb08405d8b0ffaed35cfd3153d3e9477d85bbcbe7a594e00f3b5401be4cb6', '徐昊', 'bdb5e493', 'xuhao@evertac.net', '086-13818736483', '服务部', true, 'service_manager', NULL, NULL, NULL, NULL, true, NULL, NULL);
INSERT INTO public.users VALUES (20, 'shengyh', 'pbkdf2:sha256:260000$OMn2qRBq1vCdz4W5$6482ded407fe55b2957a51a4a04c222f416040e7308c4d8d11815dd58bae68bc', '盛雅华', '和源通信（上海）股份有限公司', 'shengyh@evertac.net', '086-15800471445', '服务部', false, 'customer_sales', NULL, NULL, NULL, NULL, true, NULL, NULL);
INSERT INTO public.users VALUES (19, 'linwengguan', 'pbkdf2:sha256:260000$7pmMCRJ0kQuEcDuQ$a7d651389ee561933e13b5a564597ff503e031eb64ce618d1d4010f1bf1acfce', '林文冠', '和源通信（上海）股份有限公司', 'linwenguan@evertac', '086-13816388363', '销售部', false, 'channel_manager	', NULL, NULL, NULL, NULL, false, NULL, NULL);
INSERT INTO public.users VALUES (13, 'gxh', 'pbkdf2:sha256:260000$GWtgPFkMaT1YsjHO$19045ba8d9618167c054adda359e848acc81f996e1391bf627963d4868fa6300', '郭小会', '和源通信（上海）股份有限公司', 'gxh@evertac.net', '086-15692111506', '销售部', true, 'sales_director', NULL, NULL, NULL, NULL, false, NULL, NULL);
INSERT INTO public.users VALUES (18, 'tonglei', 'pbkdf2:sha256:260000$IqkHzI2IutavTbb1$824c80ff1cfe6d50bbcd9369f472477fd270d5840760ca3315abd13a13446b9c', '童蕾', '和源通信（上海）股份有限公司', 'tonglei@evertac.net', '086-13801862575', '', false, 'customer_sales', NULL, NULL, NULL, NULL, false, NULL, NULL);
INSERT INTO public.users VALUES (6, 'NIJIE', 'scrypt:32768:8:1$wF4049I0IIhGJAX4$bfbee0e0d2e4ad1f49722be4a0265eb71382e0b157e48eb00e78e8f18be9224331ba6a31fb141cf1d0c9ccb2b12ef213be3c4b6743a3c92dcd362d91e4256c30', '倪捷', '和源通信（上海）股份有限公司', 'james111@evertac.net', '086-13003258568', '', false, 'ceo', NULL, NULL, NULL, NULL, true, NULL, NULL);


--
-- Data for Name: companies; Type: TABLE DATA; Schema: public; Owner: pma_user
--

INSERT INTO public.companies VALUES (4, '25D15006', '上海安装第九分公司', '中国', '上海市', '上海1号', '建筑业', '系统集成商', '活跃', '2025-04-15 09:52:33.912968', '2025-04-26 09:17:58.294798', '', false, 5);
INSERT INTO public.companies VALUES (5, '25D15007', '上海航网瑞可', '中国', '上海市', '为何之间的', '制造业', '经销商', '活跃', '2025-04-15 09:53:18.618823', '2025-04-26 09:18:19.916832', '', false, 5);
INSERT INTO public.companies VALUES (6, '25D18008', '武汉倪捷测试', '中国', '北京市', '请问', '制造业', '用户', '活跃', '2025-04-18 14:58:12.624882', '2025-04-26 09:18:27.123223', '', false, 6);
INSERT INTO public.companies VALUES (9, '25D06002', '苏中达科智能工程有限公司西安分公司', '', '西安', '西安', '', '系统集成商', '活跃', '2025-04-06 00:00:00', '2025-04-27 06:39:59.605098', '', false, 13);
INSERT INTO public.companies VALUES (10, '24B21001', '西安悦泰科技有限责任公司', '', '西安', '西安南三环', '', '系统集成商', '活跃', '2024-02-21 13:45:29', '2025-04-27 06:39:59.60989', '', false, 13);
INSERT INTO public.companies VALUES (11, '25D27001', '北京沃利帕森工程技术有限公司上海分公司', '中国', '上海', '上海闵行', NULL, '设计院及顾问', '活跃', '2025-03-29 00:00:00', '2025-04-27 07:54:10.628176', NULL, false, 13);
INSERT INTO public.companies VALUES (12, '25D27002', '华东建筑设计研究院有限公司', '中国', '上海', '黄浦区世博滨江大道北座', NULL, '设计院及顾问', '活跃', '2024-12-28 17:33:26', '2025-04-27 07:54:10.633716', NULL, false, 13);
INSERT INTO public.companies VALUES (13, '25D27003', '上海机场(集团)有限公司', '中国', '上海', '上海浦东', NULL, '用户', '活跃', '2025-03-22 00:00:00', '2025-04-27 07:54:10.635886', NULL, false, 13);
INSERT INTO public.companies VALUES (14, '25D27004', '北京中加集成智能系统工程有限公司', '中国', '北京', '北京西城区外大街271号', NULL, '系统集成商', '活跃', '2024-12-28 16:43:35', '2025-04-27 07:54:10.638053', NULL, false, 13);
INSERT INTO public.companies VALUES (15, '25D27005', '上海临港经济发展（集团）有限公司', '中国', '上海', '上海临港', NULL, '用户', '活跃', '2025-03-19 00:00:00', '2025-04-27 07:54:10.640057', NULL, false, 13);
INSERT INTO public.companies VALUES (16, '25D27006', '安徽数安桥数据科技有限公司', '中国', '成都', '成都', NULL, '系统集成商', '活跃', '2025-03-14 00:00:00', '2025-04-27 07:54:10.641735', NULL, false, 13);
INSERT INTO public.companies VALUES (17, '25D27007', '上海竞拓数码信息技术有限公司', '中国', '上海', '上海浦东', NULL, '系统集成商', '活跃', '2025-03-14 00:00:00', '2025-04-27 07:54:10.643511', NULL, false, 13);
INSERT INTO public.companies VALUES (18, '25D27008', '上海市安装工程集团的限公司', '中国', '上海', '上海曲阳路930号', NULL, '系统集成商', '活跃', '2025-03-12 00:00:00', '2025-04-27 07:54:10.64519', NULL, false, 13);
INSERT INTO public.companies VALUES (19, '25D27009', '广州省建筑设计研究院', '中国', '广州', '广州越秀', NULL, '设计院及顾问', '活跃', '2025-03-07 00:00:00', '2025-04-27 07:54:10.646918', NULL, false, 13);
INSERT INTO public.companies VALUES (20, '25D27010', '民航机场成都电子工程设计有限责任公司', '中国', '成都', '成都市二环路南二癹17号', NULL, '设计院及顾问', '活跃', '2024-02-21 12:04:43.999', '2025-04-27 07:54:10.648472', NULL, false, 13);
INSERT INTO public.companies VALUES (21, '25D27011', '广州希耐特船舶科技有限公司', '中国', '广州', '广州', NULL, '合作伙伴', '活跃', '2025-03-07 00:00:00', '2025-04-27 07:54:10.650009', NULL, false, 13);
INSERT INTO public.companies VALUES (22, '25D27012', '山西云时代技术有限公司', '中国', '太原', '太原', NULL, '系统集成商', '活跃', '2025-03-05 00:00:00', '2025-04-27 07:54:10.65175', NULL, false, 13);
INSERT INTO public.companies VALUES (23, '25D27013', '中国中铁二院', '中国', '成都', '成都', NULL, '设计院及顾问', '活跃', '2025-03-01 00:00:00', '2025-04-27 07:54:10.653358', NULL, false, 13);
INSERT INTO public.companies VALUES (24, '25D27014', '北京建筑设计研究院成都分院', '中国', '成都', '成都', NULL, '设计院及顾问', '活跃', '2025-03-01 00:00:00', '2025-04-27 07:54:10.655099', NULL, false, 13);
INSERT INTO public.companies VALUES (25, '25D27015', '信息产业电子第十一设计院科技工程股份有限公司', '中国', '成都', '成都市成华区双林路251号', NULL, '设计院及顾问', '活跃', '2024-02-21 14:45:40.999', '2025-04-27 07:54:10.656676', NULL, false, 13);
INSERT INTO public.companies VALUES (26, '25D27016', '上海霹迪梯通讯科技有限公司', '中国', '上海', '上海曹杨汇融大厦1107', NULL, '合作伙伴', '活跃', '2025-02-22 00:00:00', '2025-04-27 07:54:10.658084', NULL, false, 13);
INSERT INTO public.companies VALUES (27, '25D27017', '北京京航安机场工程有限公司', '中国', NULL, '北京市平谷区林荫北街13号信息大厦1002-39室', NULL, '系统集成商', '活跃', '2024-02-20 00:00:00', '2025-04-27 07:54:10.659354', NULL, false, 13);
INSERT INTO public.companies VALUES (28, '25D27018', '重庆大鹏鸟科技有限公司', '中国', '重庆', '重庆渝中区临江路19号', NULL, '经销商', '活跃', '2024-12-31 15:27:02.999', '2025-04-27 07:54:10.660675', NULL, false, 13);
INSERT INTO public.companies VALUES (29, '25D27019', '中国中钢股份有限公司', '中国', '北京', '北京市海淀区海淀大街8号', NULL, '系统集成商', '活跃', '2025-01-19 09:42:38', '2025-04-27 07:54:10.661925', NULL, false, 13);
INSERT INTO public.companies VALUES (30, '25D27020', '上海远菁工程项目管理有限公司', '中国', '上海', '上海宝山区逸仙路2816号', NULL, '设计院及顾问', '活跃', '2025-01-04 09:45:02', '2025-04-27 07:54:10.663752', NULL, false, 13);
INSERT INTO public.companies VALUES (31, '25D27021', '合肥兴和通讯设备有限公司', '中国', '合肥', '安徽合肥包河区巢湖南路89号', NULL, '经销商', '活跃', '2024-12-28 17:00:48.999', '2025-04-27 07:54:10.665194', NULL, false, 13);
INSERT INTO public.companies VALUES (32, '25D27022', '四川中科航建信息技术有限公司', '中国', '成都', '武侯区天益街38号理想中心2-701室', NULL, '系统集成商', '活跃', '2024-11-16 11:54:10', '2025-04-27 07:54:10.666463', NULL, false, 13);
INSERT INTO public.companies VALUES (33, '25D27023', '上海福玛通信信息科技有限公司', '中国', '上海', '上海市浦东新区秀浦路800弄35号901室', NULL, '经销商', '活跃', '2024-11-16 11:39:28', '2025-04-27 07:54:10.667644', NULL, false, 13);
INSERT INTO public.companies VALUES (34, '25D27024', '广州宇洪智能技术有限公司', '中国', '广州', '广州市天河区软件路11号402室', NULL, '经销商', '活跃', '2024-11-02 10:41:24', '2025-04-27 07:54:10.66923', NULL, false, 13);
INSERT INTO public.companies VALUES (35, '25D27025', '上海慧腾信息科技有限公司', '中国', NULL, '普陀区同普路1175弄14号309室', NULL, '设计院及顾问', '活跃', '2024-11-02 09:51:44.999', '2025-04-27 07:54:10.670575', NULL, false, 13);
INSERT INTO public.companies VALUES (36, '25D27026', '深圳市麦驰物联股份有限公司上海分公司', '中国', '上海', '上海浦发广场E座', NULL, '设计院及顾问', '活跃', '2024-10-31 11:43:53', '2025-04-27 07:54:10.671831', NULL, false, 13);
INSERT INTO public.companies VALUES (37, '25D27027', '中科院成都信息技术有限公司', '中国', '成都', '成都', NULL, '系统集成商', '活跃', '2024-10-20 22:08:32', '2025-04-27 07:54:10.67297', NULL, false, 13);
INSERT INTO public.companies VALUES (38, '25D27028', '四川省建筑设计研究院有限公司', '中国', '成都', '成都', NULL, '设计院及顾问', '活跃', '2024-10-20 21:49:53', '2025-04-27 07:54:10.674357', NULL, false, 13);
INSERT INTO public.companies VALUES (39, '25D27029', '四川倍智数能信息工程有限公司', '中国', '成都', '成都天华一路99号', NULL, '系统集成商', '活跃', '2024-10-20 15:25:25', '2025-04-27 07:54:10.675585', NULL, false, 13);
INSERT INTO public.companies VALUES (40, '25D27030', '青岛中亿海电子科技有限公司', '中国', '青岛', '青岛漳州二路9号', NULL, '经销商', '活跃', '2024-09-30 13:39:46', '2025-04-27 07:54:10.676723', NULL, false, 13);
INSERT INTO public.companies VALUES (41, '25D27031', '同济大学建筑设计研究院(集团)有限公司', '中国', NULL, '上海市杨浦区四平路1230号', NULL, '设计院及顾问', '活跃', '2024-09-28 16:13:39', '2025-04-27 07:54:10.677848', NULL, false, 13);
INSERT INTO public.companies VALUES (42, '25D27032', '天津比信科技有限公司', '中国', '天津', '金航大厦1-1-102室', NULL, '经销商', '活跃', '2024-09-28 15:54:58', '2025-04-27 07:54:10.678944', NULL, false, 13);
INSERT INTO public.companies VALUES (43, '25D27033', '西安瑞林达通信技术有限公司', '中国', '西安', '西安市灞桥区高科绿水东城四期', NULL, '经销商', '活跃', '2024-09-28 15:52:05', '2025-04-27 07:54:10.68016', NULL, false, 13);
INSERT INTO public.companies VALUES (44, '25D27034', '北京朗易通科技有限公司', '中国', '北京', '北京海淀区交大东路66号', NULL, '经销商', '活跃', '2024-09-28 14:13:27', '2025-04-27 07:54:10.681237', NULL, false, 13);
INSERT INTO public.companies VALUES (45, '25D27035', '成都市天皓科技有限公司', '中国', '成都', '成都金牛区一环路北三段100号', NULL, '经销商', '活跃', '2024-09-28 10:54:37', '2025-04-27 07:54:10.682339', NULL, false, 13);
INSERT INTO public.companies VALUES (46, '25D27036', '武汉意丰科技有限公司', '中国', '武汉', '武汉洪山区文化大道555号', NULL, '系统集成商', '活跃', '2024-09-28 10:31:24', '2025-04-27 07:54:10.683622', NULL, false, 13);
INSERT INTO public.companies VALUES (47, '25D27037', '上海积塔半导体有限公司', '中国', '上海', '上海临港', NULL, '用户', '活跃', '2024-09-28 10:00:49', '2025-04-27 07:54:10.684797', NULL, false, 13);
INSERT INTO public.companies VALUES (48, '25D27038', '四川三创联和信息技术服务有限公司', '中国', '成都', '成都高新区天府大道中段530号1栋19楼1903', NULL, '系统集成商', '活跃', '2024-09-17 10:37:45', '2025-04-27 07:54:10.686116', NULL, false, 13);
INSERT INTO public.companies VALUES (49, '25D27039', '湖南悟意信息技术有限公司', '中国', '长沙', '长沙雨花区香丽名苑3栋', NULL, '系统集成商', '活跃', '2024-09-11 15:20:13', '2025-04-27 07:54:10.68758', NULL, false, 13);
INSERT INTO public.companies VALUES (50, '25D27040', '中建四局智控与数字科技事业部', '中国', '深圳市', '深圳', NULL, '系统集成商', '活跃', '2024-09-10 13:24:35', '2025-04-27 07:54:10.68873', NULL, false, 13);
INSERT INTO public.companies VALUES (51, '25D27041', '上海鑫桉信息工程有限公司', '中国', '上海', '上海市奉贤中路629', NULL, '经销商', '活跃', '2024-08-31 11:52:40', '2025-04-27 07:54:10.690036', NULL, false, 13);
INSERT INTO public.companies VALUES (52, '25D27042', '四川中资世纪科技有限公司', '上海', '上海', '成都市成华区成华大道二段298号', NULL, '经销商', '活跃', '2024-08-02 10:58:49', '2025-04-27 07:54:10.691203', NULL, false, 13);
INSERT INTO public.companies VALUES (53, '25D27043', '华虹半导体（上海）有限公司', '上海', '上海', '上海市浦东新区康桥', NULL, '用户', '活跃', '2024-07-18 15:23:27', '2025-04-27 07:54:10.692254', NULL, false, 13);
INSERT INTO public.companies VALUES (54, '25D27044', '四川天启智源科技有限公司', '中国', '成都', '成都', NULL, '系统集成商', '活跃', '2024-07-15 09:57:31', '2025-04-27 07:54:10.693232', NULL, false, 13);
INSERT INTO public.companies VALUES (55, '25D27045', '上海瀚网智能科技有限公司', '中国', '上海', '上海嘉定区双单路86弄', NULL, '经销商', '活跃', '2024-06-22 12:57:14', '2025-04-27 07:54:10.694369', NULL, false, 13);
INSERT INTO public.companies VALUES (56, '25D27046', '苏州商普智能科技有限公司', '中国', '苏州', '江苏昆山g-a发区中冶累庭4号楼', NULL, '系统集成商', '活跃', '2024-06-22 12:27:55', '2025-04-27 07:54:10.695391', NULL, false, 13);
INSERT INTO public.companies VALUES (57, '25D27047', '吉林市天达伟业科贸有限公司', '中国', '吉林', '吉林南京街181号', NULL, '系统集成商', '活跃', '2024-06-13 16:32:54', '2025-04-27 07:54:10.696691', NULL, false, 13);
INSERT INTO public.companies VALUES (58, '25D27048', '上海电科智能系统股份有限公司', '中国', '上海', '上海武宁路505号', NULL, '系统集成商', '活跃', '2024-05-25 10:00:17', '2025-04-27 07:54:10.697728', NULL, false, 13);
INSERT INTO public.companies VALUES (59, '25D27049', '金盛投资发展有限公司', '中国', '澳门', NULL, NULL, '系统集成商', '活跃', '2024-05-24 21:56:02', '2025-04-27 07:54:10.698683', NULL, false, 13);
INSERT INTO public.companies VALUES (60, '25D27050', '太通建设有限公司', '中国', '北京', '北京市城庙城299号', NULL, '系统集成商', '活跃', '2024-04-24 08:53:40', '2025-04-27 07:54:10.699654', NULL, false, 13);
INSERT INTO public.companies VALUES (61, '25D27051', '陕西无线电通信服务中心', '中国', '西安', '西安新城国际大厦A1103', NULL, '经销商', '活跃', '2024-04-24 08:38:43.999', '2025-04-27 07:54:10.700687', NULL, false, 13);
INSERT INTO public.companies VALUES (62, '25D27052', '青岛青咨工程咨询有限公司', '中国', '青岛市', '青岛', NULL, '设计院及顾问', '活跃', '2024-04-14 09:36:21', '2025-04-27 07:54:10.701777', NULL, false, 13);
INSERT INTO public.companies VALUES (63, '25D27053', '青岛智联慧通电子科技有限公司', '中国', '青岛市', '青岛瑞海北路11号', NULL, '经销商', '活跃', '2024-04-14 09:35:59', '2025-04-27 07:54:10.702889', NULL, false, 13);
INSERT INTO public.companies VALUES (64, '25D27054', '上海艾亿智能科技有限公司', '中国', '上海', '上海奉贤区海坤路1号', NULL, '经销商', '活跃', '2024-03-28 09:04:57', '2025-04-27 07:54:10.703906', NULL, false, 13);
INSERT INTO public.companies VALUES (65, '25D27055', '四川三创联和技术服务有限公司', '中国', '成都', '四川成都天府大道中段530号', NULL, '设计院及顾问', '活跃', '2024-03-18 16:08:26', '2025-04-27 07:54:10.70487', NULL, false, 13);
INSERT INTO public.companies VALUES (66, '25D27056', '英威达尼龙化工（中国）有限公司', '中国', '上海', '上海金山天华路88号', NULL, '用户', '活跃', '2024-03-18 14:25:37', '2025-04-27 07:54:10.705797', NULL, false, 13);
INSERT INTO public.companies VALUES (67, '25D27057', '中国中元国际工程有限公司', '中国', '北京', '北京海淀区西三环北路5号', NULL, '设计院及顾问', '活跃', '2024-03-18 13:41:37.999', '2025-04-27 07:54:10.70692', NULL, false, 13);
INSERT INTO public.companies VALUES (68, '25D27058', '上海市政工程设计研究总院（集团）有限公司', '中国', '上海', '上海杨浦区中山北二路901号', NULL, '设计院及顾问', '活跃', '2024-03-14 19:13:10', '2025-04-27 07:54:10.707952', NULL, false, 13);
INSERT INTO public.companies VALUES (69, '25D27059', '湖南安众智能科技有限公司', '中国', '长沙', '长沙市雨花区人民路9号', NULL, '系统集成商', '活跃', '2024-03-14 18:29:21', '2025-04-27 07:54:10.708916', NULL, false, 13);
INSERT INTO public.companies VALUES (70, '25D27060', '中国航空规划设计院', '中国', '北京', NULL, NULL, '设计院及顾问', '活跃', '2024-03-10 15:36:33', '2025-04-27 07:54:10.709841', NULL, false, 13);
INSERT INTO public.companies VALUES (71, '25D27061', '长沙市规划设计院有限责任公司', '中国', '长沙市', '长沙芙蓉区', NULL, '设计院及顾问', '活跃', '2024-03-10 00:00:00', '2025-04-27 07:54:10.710801', NULL, false, 13);
INSERT INTO public.companies VALUES (72, '25D27062', '重庆君知鹏科技有限公司', '中国', '重庆', '重庆市南岸区海棠溪街道交院大道66号', NULL, '经销商', '活跃', '2024-03-09 14:26:45.999', '2025-04-27 07:54:10.711831', NULL, false, 13);
INSERT INTO public.companies VALUES (73, '25D27063', '上海延华智能科技（集团）股份有限公司', '中国', '上海', '上海市西康路1255号普陀科技大厦6楼', NULL, '设计院及顾问', '活跃', '2024-03-01 13:07:06', '2025-04-27 07:54:10.712962', NULL, false, 13);
INSERT INTO public.companies VALUES (74, '25D27064', '上海天华建筑设计有限公司武汉公分公司', '中国', '武汉', NULL, NULL, '设计院及顾问', '活跃', '2024-03-01 11:24:07', '2025-04-27 07:54:10.713959', NULL, false, 13);
INSERT INTO public.companies VALUES (75, '25D27065', '润建股份有限公司', '中国', '广州', NULL, NULL, '系统集成商', '活跃', '2024-02-27 19:41:07', '2025-04-27 07:54:10.714924', NULL, false, 13);
INSERT INTO public.companies VALUES (76, '25D27066', '上海申通地铁集团有限公司', '中国', '上海', '上海衡山路12号', NULL, '设计院及顾问', '活跃', '2024-02-22 21:15:22', '2025-04-27 07:54:10.715925', NULL, false, 13);
INSERT INTO public.companies VALUES (77, '25D27067', '杰创智能科技股份有限公司', '中国', '广州', '广州黄浦区瑞详路88号', NULL, '系统集成商', '活跃', '2024-02-22 21:07:35', '2025-04-27 07:54:10.71691', NULL, false, 13);
INSERT INTO public.companies VALUES (78, '25D27068', '深圳达实智能股份有限公司', '中国', '深圳市', '深圳市南山区高新技术村W1栋A座五楼', NULL, '系统集成商', '活跃', '2024-02-22 00:00:00', '2025-04-27 07:54:10.718027', NULL, false, 13);
INSERT INTO public.companies VALUES (79, '25D27069', '天津中海地产有限公司', '中国', NULL, '河东区海河东路518号', NULL, '用户', '活跃', '2024-02-22 00:00:00', '2025-04-27 07:54:10.71921', NULL, false, 13);
INSERT INTO public.companies VALUES (80, '25D27070', '上海邮电设计咨询研究院有限公司', '中国', NULL, '上海市杨浦区国康路38号3号楼', NULL, '设计院及顾问', '活跃', '2024-02-22 00:00:00', '2025-04-27 07:54:10.720198', NULL, false, 13);
INSERT INTO public.companies VALUES (81, '25D27071', '华东建筑设计研究院有限公司重庆西南中心', '中国', NULL, '市渝中区华盛路10号14层1#', NULL, '设计院及顾问', '活跃', '2024-02-22 00:00:00', '2025-04-27 07:54:10.72122', NULL, false, 13);
INSERT INTO public.companies VALUES (82, '25D27072', '巴马丹拿建筑设计咨询(上海)有限公司', '中国', NULL, '上海市长宁区遵义路100号虹桥南丰城B座31楼', NULL, '设计院及顾问', '活跃', '2024-02-22 00:00:00', '2025-04-27 07:54:10.722197', NULL, false, 13);
INSERT INTO public.companies VALUES (83, '25D27073', '中国建筑西南设计研究院有限公司', '中国', '洛阳市', '成都市花圃北路14号', NULL, '设计院及顾问', '活跃', '2024-02-22 00:00:00', '2025-04-27 07:54:10.723199', NULL, false, 13);
INSERT INTO public.companies VALUES (84, '25D27074', '江苏中业信息科技有限公司', '中国', '苏州', NULL, NULL, '系统集成商', '活跃', '2024-02-21 15:41:15', '2025-04-27 07:54:10.724169', NULL, false, 13);
INSERT INTO public.companies VALUES (85, '25D27075', '上海瑞康通信科技有限公司', '中国', '上海', '嘉定区双单路86弄4号楼4层', NULL, '分销商', '活跃', '2024-02-21 15:36:42', '2025-04-27 07:54:10.725124', NULL, false, 13);
INSERT INTO public.companies VALUES (86, '25D27076', '上海淳泊信息科技有限公司', '中国', '上海', '闵行区立跃路2795号', NULL, '分销商', '活跃', '2024-02-21 15:32:11', '2025-04-27 07:54:10.726099', NULL, false, 13);
INSERT INTO public.companies VALUES (87, '25D27077', '中国海螺创业控股有限公司', '中国', '上海', '嘉定区天祝路海螺总部大楼', NULL, '用户', '活跃', '2024-02-21 15:14:01', '2025-04-27 07:54:10.727076', NULL, false, 13);
INSERT INTO public.companies VALUES (88, '25D27078', '安徽长飞先进半导体有限公司', '中国', '芜湖', '芜湖市利民东路82号', NULL, '用户', '活跃', '2024-02-21 15:02:50.999', '2025-04-27 07:54:10.728113', NULL, false, 13);
INSERT INTO public.companies VALUES (89, '25D27079', '福淳智能科技(四川)有限公司', '中国', '成都', '成都高新区新程大道78号', NULL, '经销商', '活跃', '2024-02-21 14:50:19', '2025-04-27 07:54:10.729205', NULL, false, 13);
INSERT INTO public.companies VALUES (90, '25D27080', '上海博望电子科技有限公司', '中国', '上海', '上海杨浦区逸仙路205号1915室', NULL, '系统集成商', '活跃', '2024-02-21 14:40:31', '2025-04-27 07:54:10.730198', NULL, false, 13);
INSERT INTO public.companies VALUES (91, '25D27081', '合肥新桥国际机场有限公司', '中国', '合肥', NULL, NULL, '用户', '活跃', '2024-02-21 13:48:02', '2025-04-27 07:54:10.731141', NULL, false, 13);
INSERT INTO public.companies VALUES (92, '25D27082', '民航成都电子技术有限责任公司', '中国', '成都', '四川省新津工业园区新材料产业功能区新材28路南侧', NULL, '系统集成商', '活跃', '2024-02-21 11:55:52', '2025-04-27 07:54:10.732105', NULL, false, 13);
INSERT INTO public.companies VALUES (93, '25D27083', '中国移动通信集团陕西有限公司西安分公司', '中国', '西安', NULL, NULL, '系统集成商', '活跃', '2024-02-21 10:15:37', '2025-04-27 07:54:10.733226', NULL, false, 13);
INSERT INTO public.companies VALUES (94, '25D27084', '北京中电电子工程咨询公司', '中国', '北京', '北京市海淀区万寿路27号院内', NULL, '设计院及顾问', '活跃', '2024-02-20 00:00:00', '2025-04-27 07:54:10.734423', NULL, false, 13);
INSERT INTO public.companies VALUES (95, '25D27085', '华虹半导体(无锡)有限公司', '中国', '无锡市', '无锡市新吴区新洲路28号', NULL, '用户', '活跃', '2024-02-20 00:00:00', '2025-04-27 07:54:10.73559', NULL, false, 13);
INSERT INTO public.companies VALUES (96, '25D27086', '中芯国际集成电路制造（绍兴）有限公司', '中国', '浦东新区', '张江路18号', NULL, '用户', '活跃', '2024-02-20 00:00:00', '2025-04-27 07:54:10.736664', NULL, false, 13);
INSERT INTO public.companies VALUES (97, '25D27087', '上海延华智能科技(集团)股份有限公司', '中国', '普陀区', '西康路1255号普陀科技大厦7楼', NULL, '系统集成商', '活跃', '2024-02-20 00:00:00', '2025-04-27 07:54:10.737659', NULL, false, 13);
INSERT INTO public.companies VALUES (98, '25D27088', '武汉新芯集成电路制造有限公司', '中国', '武汉市', '武汉市东湖开发区高新四路18号', NULL, '用户', '活跃', '2024-02-20 00:00:00', '2025-04-27 07:54:10.738816', NULL, false, 13);
INSERT INTO public.companies VALUES (99, '25D27089', '中芯集成电路制造(绍兴)有限公司', '中国', '绍兴市', '稠州路', NULL, '用户', '活跃', '2024-02-20 00:00:00', '2025-04-27 07:54:10.739883', NULL, false, 13);
INSERT INTO public.companies VALUES (100, '25D27090', '长江存储科技有限责任公司', '中国', '武汉市', '武汉市东湖开发区关东科技工业园华光大道18号7018室', NULL, '用户', '活跃', '2024-02-20 00:00:00', '2025-04-27 07:54:10.741023', NULL, false, 13);
INSERT INTO public.companies VALUES (101, '25D27091', '广州粤芯半导体技术有限公司', '中国', NULL, '广州市萝岗知识城', NULL, '用户', '活跃', '2024-02-20 00:00:00', '2025-04-27 07:54:10.742052', NULL, false, 13);
INSERT INTO public.companies VALUES (102, '25D27092', '深圳华大基因股份有限公司', '中国', '深圳市', '盐田区洪安三街21号华大综合园7栋7层-14层', NULL, '用户', '活跃', '2024-02-20 00:00:00', '2025-04-27 07:54:10.743008', NULL, false, 13);
INSERT INTO public.companies VALUES (103, '25D27093', '上海华携实业发展有限公司', '中国', '上海', '上海市金山区张堰镇松金公路2758号10幢A1217室', NULL, '系统集成商', '活跃', '2024-02-20 00:00:00', '2025-04-27 07:54:10.743983', NULL, false, 13);


--
-- Data for Name: contacts; Type: TABLE DATA; Schema: public; Owner: pma_user
--

INSERT INTO public.contacts VALUES (4, 6, '泽骧', '的', '额', '的', '', true, '2025-04-18 15:12:14.269242', '2025-04-18 15:27:57.979039', '', 5);
INSERT INTO public.contacts VALUES (5, 4, '大庄', '', '', '', '', false, '2025-04-27 06:37:04.737359', '2025-04-27 06:37:04.73737', '', 5);
INSERT INTO public.contacts VALUES (6, 10, '张晓龙', '采购部门', '经理', '', '', false, '2025-04-06 00:00:00', '2025-04-27 08:15:01.467261', NULL, 13);
INSERT INTO public.contacts VALUES (7, 61, '张士彦', '业务部门', '总经理', '', '', false, '2025-04-06 00:00:00', '2025-04-27 08:15:01.470371', NULL, 13);
INSERT INTO public.contacts VALUES (8, 9, '马年伟', '工程部门', '经理', '', '', false, '2025-04-06 00:00:00', '2025-04-27 08:15:01.472122', NULL, 13);
INSERT INTO public.contacts VALUES (9, 35, '孙晓文', '设计部门', '技术经理', '', '', false, '2024-02-22 00:00:00', '2025-04-27 08:15:01.473349', NULL, 13);
INSERT INTO public.contacts VALUES (10, 11, '张伟伟', '设计部门', '经理', '', '', false, '2025-03-29 00:00:00', '2025-04-27 08:15:01.475129', NULL, 13);
INSERT INTO public.contacts VALUES (11, 36, '孙月红', '设计部门', '经理', '', '', false, '2025-03-29 00:00:00', '2025-04-27 08:15:01.476329', NULL, 13);
INSERT INTO public.contacts VALUES (12, 13, '顾婷婷', '工程部门', '负责人', '', '', false, '2025-03-22 00:00:00', '2025-04-27 08:15:01.477506', NULL, 13);
INSERT INTO public.contacts VALUES (13, 15, '朱秀兰', '业务部门', '经理', '', '', false, '2025-03-19 00:00:00', '2025-04-27 08:15:01.478708', NULL, 13);
INSERT INTO public.contacts VALUES (14, 17, '曹雪芹', '工程部门', '经理', '', '', false, '2025-03-14 00:00:00', '2025-04-27 08:15:01.480292', NULL, 13);
INSERT INTO public.contacts VALUES (15, 20, '黄小兵', '设计部门', '经理', '', '', false, '2025-03-14 00:00:00', '2025-04-27 08:15:01.481403', NULL, 13);
INSERT INTO public.contacts VALUES (16, 16, '俞工', '业务部门', '经理', '', '', false, '2025-03-14 00:00:00', '2025-04-27 08:15:01.48256', NULL, 13);
INSERT INTO public.contacts VALUES (17, 18, '应寅', '工程部门', '经理', '', '', false, '2025-03-12 00:00:00', '2025-04-27 08:15:01.483587', NULL, 13);
INSERT INTO public.contacts VALUES (18, 21, '易利鹏', '业务部门', '总经理', '', '', false, '2025-03-07 00:00:00', '2025-04-27 08:15:01.484586', NULL, 13);
INSERT INTO public.contacts VALUES (19, 20, '李小将', '设计部门', '技术经理', '', '', false, '2025-03-07 00:00:00', '2025-04-27 08:15:01.48563', NULL, 13);
INSERT INTO public.contacts VALUES (20, 19, '黄宇清', '设计部门', '总工', '', '', false, '2025-03-07 00:00:00', '2025-04-27 08:15:01.486976', NULL, 13);
INSERT INTO public.contacts VALUES (21, 14, '孟凡丽', '业务部门', '经理', '13817757566', '', false, '2024-12-28 16:43:35', '2025-04-27 08:15:01.488486', NULL, 13);
INSERT INTO public.contacts VALUES (22, 22, '王文', '民航智能中心', '经理', '', '', false, '2025-03-05 00:00:00', '2025-04-27 08:15:01.489774', NULL, 13);
INSERT INTO public.contacts VALUES (23, 24, '张莉', '设计部门', '经理', '', '', false, '2025-03-01 00:00:00', '2025-04-27 08:15:01.490779', NULL, 13);
INSERT INTO public.contacts VALUES (24, 20, '王巍', '设计部门', '总经理', '', '', false, '2025-03-01 00:00:00', '2025-04-27 08:15:01.491765', NULL, 13);
INSERT INTO public.contacts VALUES (25, 23, '程智源', '设计部门', '设计经理', '', '', false, '2025-03-01 00:00:00', '2025-04-27 08:15:01.492708', NULL, 13);
INSERT INTO public.contacts VALUES (26, 26, '庹伟', '业务部门', '经理', '', '', false, '2025-02-22 00:00:00', '2025-04-27 08:15:01.493649', NULL, 13);
INSERT INTO public.contacts VALUES (27, 25, '王兵', '工程部门', '经理', '', '', false, '2025-02-22 00:00:00', '2025-04-27 08:15:01.49455', NULL, 13);
INSERT INTO public.contacts VALUES (28, 12, '陈元骏', '设计部门', '弱电主任工程师', '', '', false, '2025-02-20 00:00:00', '2025-04-27 08:15:01.495483', NULL, 13);
INSERT INTO public.contacts VALUES (29, 12, '吴文芳', '设计部门', '弱电主任工程师', '', '', false, '2024-12-28 17:09:46.999', '2025-04-27 08:15:01.496449', NULL, 13);
INSERT INTO public.contacts VALUES (30, 12, '王小安', '设计部门', '设计经理', '', '', false, '2024-12-28 17:08:50', '2025-04-27 08:15:01.497313', NULL, 13);
INSERT INTO public.contacts VALUES (31, 27, '朱君丽', '业务部门', '经理', '', '', false, '2025-02-20 00:00:00', '2025-04-27 08:15:01.498152', NULL, 13);
INSERT INTO public.contacts VALUES (32, 20, '叶中贵', '设计部门', '弱电主任工程师', '', '', false, '2025-02-15 00:00:00', '2025-04-27 08:15:01.499024', NULL, 13);
INSERT INTO public.contacts VALUES (33, 25, '施君', '设计部门', '经理', '', '', false, '2025-02-08 00:00:00', '2025-04-27 08:15:01.499875', NULL, 13);
INSERT INTO public.contacts VALUES (34, 28, '唐明勇', '业务部门', '经理', '', '', false, '2025-02-08 00:00:00', '2025-04-27 08:15:01.500714', NULL, 13);
INSERT INTO public.contacts VALUES (35, 30, '马林波', '业务部门', '经理', '', '', false, '2025-01-04 09:44:50', '2025-04-27 08:15:01.501521', NULL, 13);
INSERT INTO public.contacts VALUES (36, 28, '谭超洋', '业务部门', '经理', '', '', false, '2024-12-31 15:27:02.999', '2025-04-27 08:15:01.502402', NULL, 13);
INSERT INTO public.contacts VALUES (37, 12, '徐珣', '设计部门', '弱电主任工程师', '', '', false, '2024-12-28 17:31:39', '2025-04-27 08:15:01.503541', NULL, 13);
INSERT INTO public.contacts VALUES (38, 31, '尤力', '总经理', '总经理', '18130051105', '', false, '2024-12-28 17:00:48.999', '2025-04-27 08:15:01.504489', NULL, 13);
INSERT INTO public.contacts VALUES (39, 32, '孙佳梅', '业务部门', '经理', '13086651575', '', false, '2024-11-16 11:53:55', '2025-04-27 08:15:01.505316', NULL, 13);
INSERT INTO public.contacts VALUES (40, 33, '付言新', '业务部门', '总经理', '', '', false, '2024-11-16 11:39:22', '2025-04-27 08:15:01.506116', NULL, 13);
INSERT INTO public.contacts VALUES (41, 34, '裴小印', '业务部门', '经理', '15013037131', '', false, '2024-11-02 10:41:24', '2025-04-27 08:15:01.506948', NULL, 13);
INSERT INTO public.contacts VALUES (42, 36, '孙方正', '设计部门', '总经理', '', '', false, '2024-10-31 11:43:53', '2025-04-27 08:15:01.507728', NULL, 13);
INSERT INTO public.contacts VALUES (43, 37, '张伟', '业务部门', '经理', '', '', false, '2024-10-20 22:08:24', '2025-04-27 08:15:01.508522', NULL, 13);
INSERT INTO public.contacts VALUES (44, 38, '杨松', '设计部门', '设计经理', '', '', false, '2024-10-20 21:49:53', '2025-04-27 08:15:01.509355', NULL, 13);
INSERT INTO public.contacts VALUES (45, 39, '贺鹤明', '业务部门', '经理', '', '', false, '2024-10-20 15:25:25', '2025-04-27 08:15:01.510404', NULL, 13);
INSERT INTO public.contacts VALUES (46, 40, '李京芳', '业务部门', '经理', '', '', false, '2024-09-30 13:39:46', '2025-04-27 08:15:01.511275', NULL, 13);
INSERT INTO public.contacts VALUES (47, 41, '唐平', '设计部门', '弱电主任工程师', '', '', false, '2024-09-28 16:13:39', '2025-04-27 08:15:01.512085', NULL, 13);
INSERT INTO public.contacts VALUES (48, 42, '张群', '业务部门', '总经理', '', '', false, '2024-09-28 15:54:58', '2025-04-27 08:15:01.512917', NULL, 13);
INSERT INTO public.contacts VALUES (49, 43, '邹茹飞', '业务部门', '总经理', '', '', false, '2024-09-28 15:52:05', '2025-04-27 08:15:01.513734', NULL, 13);
INSERT INTO public.contacts VALUES (50, 44, '王斌', '业务部门', '总经理', '13601362550', '', false, '2024-09-28 14:13:27', '2025-04-27 08:15:01.514509', NULL, 13);
INSERT INTO public.contacts VALUES (51, 45, '李瑞', '业务部门', '总经理', '', '', false, '2024-09-28 10:54:37', '2025-04-27 08:15:01.515341', NULL, 13);
INSERT INTO public.contacts VALUES (52, 46, '宋登', '工程部门', '经理', '', '', false, '2024-09-28 10:31:24', '2025-04-27 08:15:01.516207', NULL, 13);
INSERT INTO public.contacts VALUES (53, 47, '夏鑫', '信息设备部', '经理', '', '', false, '2024-09-28 10:00:49', '2025-04-27 08:15:01.517012', NULL, 13);
INSERT INTO public.contacts VALUES (54, 48, '汪总', '业务部门', '经理', '', '', false, '2024-09-17 10:37:45', '2025-04-27 08:15:01.517775', NULL, 13);
INSERT INTO public.contacts VALUES (55, 49, '于来权', '业务部门', '经理', '15308403622', '', false, '2024-09-11 15:20:13', '2025-04-27 08:15:01.51852', NULL, 13);
INSERT INTO public.contacts VALUES (56, 51, '祁桢', '业务部门', '经理', '15800577707', '', false, '2024-08-31 11:52:40', '2025-04-27 08:15:01.519398', NULL, 13);
INSERT INTO public.contacts VALUES (57, 52, '刘贵东', '业务部门', '经理', '18983808184', '', false, '2024-08-02 10:58:49', '2025-04-27 08:15:01.52042', NULL, 13);
INSERT INTO public.contacts VALUES (58, 53, '冯跃', '信息设备部', '经理', '', '', false, '2024-07-18 15:23:27', '2025-04-27 08:15:01.521279', NULL, 13);
INSERT INTO public.contacts VALUES (59, 57, '张永泽', '业务部门', '经理', '13904403832', '', false, '2024-06-13 16:26:11', '2025-04-27 08:15:01.522163', NULL, 13);
INSERT INTO public.contacts VALUES (60, 62, '万伟民', '设计部门', '经理', '15345428848', '', false, '2024-04-13 23:57:27', '2025-04-27 08:15:01.522952', NULL, 13);
INSERT INTO public.contacts VALUES (61, 63, '李永杰', '业务部门', '总经理', '13285329285', '', false, '2024-04-13 23:53:13', '2025-04-27 08:15:01.523697', NULL, 13);
INSERT INTO public.contacts VALUES (62, 64, '梅小好', '业务部门', '经理', '', '', false, '2024-03-28 09:04:58', '2025-04-27 08:15:01.524577', NULL, 13);
INSERT INTO public.contacts VALUES (63, 66, '曹高余', '信息设备部', '经理', '18116017977', '', false, '2024-03-18 14:25:38', '2025-04-27 08:15:01.525469', NULL, 13);
INSERT INTO public.contacts VALUES (64, 67, '时姗姗', '设计部门', '经理', '13691001868', '', false, '2024-03-18 13:41:39', '2025-04-27 08:15:01.526461', NULL, 13);
INSERT INTO public.contacts VALUES (65, 33, '邹飞', '', '', '', '', false, '2024-03-18 00:00:00', '2025-04-27 08:15:01.527524', NULL, 13);
INSERT INTO public.contacts VALUES (66, 68, '郑翔', '设计部门', '经理', '17749714586', '', false, '2024-03-14 19:13:04.999', '2025-04-27 08:15:01.528545', NULL, 13);
INSERT INTO public.contacts VALUES (67, 69, '杨刚', '业务部门', '经理', '18670046866', '', false, '2024-03-14 18:29:21', '2025-04-27 08:15:01.529495', NULL, 13);
INSERT INTO public.contacts VALUES (68, 70, '朱岩旭', ' 民航智能中心', '技术经理', '18610783499', '', false, '2024-03-10 15:36:34', '2025-04-27 08:15:01.530364', NULL, 13);
INSERT INTO public.contacts VALUES (69, 71, '许良赛', '', '', '', '', false, '2024-03-10 00:00:00', '2025-04-27 08:15:01.531184', NULL, 13);
INSERT INTO public.contacts VALUES (70, 73, '蔡伟', '设计部门', '经理', '13817139998', '', false, '2024-03-01 13:07:07', '2025-04-27 08:15:01.532164', NULL, 13);
INSERT INTO public.contacts VALUES (71, 77, '凌剑传', '设计部门', '经理', '13824439019', '', false, '2024-02-22 21:07:35', '2025-04-27 08:15:01.532951', NULL, 13);
INSERT INTO public.contacts VALUES (72, 12, '余杰', '设计部门', '经理', '13501990647', '', false, '2024-02-22 13:09:07', '2025-04-27 08:15:01.533702', NULL, 13);
INSERT INTO public.contacts VALUES (73, 72, '宋崇高', '业务部门', '经理', '13996286755', '', false, '2024-02-22 12:26:03', '2025-04-27 08:15:01.534442', NULL, 13);
INSERT INTO public.contacts VALUES (74, 78, '田飞', '设计部门', '负责人', '', '', false, '2024-02-22 00:00:00', '2025-04-27 08:15:01.535141', NULL, 13);
INSERT INTO public.contacts VALUES (75, 78, '彭建肖', '', '设计经理', '', '', false, '2024-02-22 00:00:00', '2025-04-27 08:15:01.535929', NULL, 13);
INSERT INTO public.contacts VALUES (76, 78, '谢晓云', '', '', '', '', false, '2024-02-22 00:00:00', '2025-04-27 08:15:01.536791', NULL, 13);
INSERT INTO public.contacts VALUES (77, 78, '李新鑫', '', '采购总监', '', '', false, '2024-02-22 00:00:00', '2025-04-27 08:15:01.537828', NULL, 13);
INSERT INTO public.contacts VALUES (78, 78, '孙启超', '', '销售经理', '', '', false, '2024-02-22 00:00:00', '2025-04-27 08:15:01.539127', NULL, 13);
INSERT INTO public.contacts VALUES (79, 78, '刘良栾', '', '项目经理', '', '', false, '2024-02-22 00:00:00', '2025-04-27 08:15:01.540119', NULL, 13);
INSERT INTO public.contacts VALUES (80, 78, '张明', '', '商务经理', '', '', false, '2024-02-22 00:00:00', '2025-04-27 08:15:01.540999', NULL, 13);
INSERT INTO public.contacts VALUES (81, 78, '王康', '', '技术经理', '', '', false, '2024-02-22 00:00:00', '2025-04-27 08:15:01.541737', NULL, 13);
INSERT INTO public.contacts VALUES (82, 78, '李进保', '', '工程师', '', '', false, '2024-02-22 00:00:00', '2025-04-27 08:15:01.542489', NULL, 13);
INSERT INTO public.contacts VALUES (83, 78, '李振辉', '', '项目经理', '', '', false, '2024-02-22 00:00:00', '2025-04-27 08:15:01.543211', NULL, 13);
INSERT INTO public.contacts VALUES (84, 78, '安建月', '', '副总工', '', '', false, '2024-02-22 00:00:00', '2025-04-27 08:15:01.544185', NULL, 13);
INSERT INTO public.contacts VALUES (85, 78, '张韬', '', '项目经理', '', '', false, '2024-02-22 00:00:00', '2025-04-27 08:15:01.545188', NULL, 13);
INSERT INTO public.contacts VALUES (86, 35, '严俊松', '', '商务副总（采购）', '', '', false, '2024-02-22 00:00:00', '2025-04-27 08:15:01.546025', NULL, 13);
INSERT INTO public.contacts VALUES (87, 80, '顾浩', '', '网络规划咨询研究院院长', '', 'guh001@126.com', false, '2024-02-22 00:00:00', '2025-04-27 08:15:01.546715', NULL, 13);
INSERT INTO public.contacts VALUES (88, 80, '方雅雯', '', '设计师', '', '', false, '2024-02-22 00:00:00', '2025-04-27 08:15:01.547408', NULL, 13);
INSERT INTO public.contacts VALUES (89, 41, '谢文黎', '', '弱电主任工程师', '', '', false, '2024-02-22 00:00:00', '2025-04-27 08:15:01.548102', NULL, 13);
INSERT INTO public.contacts VALUES (90, 41, '王昌', '', '弱电主任工程师（组长）', '', '', false, '2024-02-22 00:00:00', '2025-04-27 08:15:01.548827', NULL, 13);
INSERT INTO public.contacts VALUES (91, 41, '施国平', '', '普通工程师', '', '', false, '2024-02-22 00:00:00', '2025-04-27 08:15:01.54952', NULL, 13);
INSERT INTO public.contacts VALUES (92, 41, '张深', '', '普通工程师', '', '', false, '2024-02-22 00:00:00', '2025-04-27 08:15:01.550237', NULL, 13);
INSERT INTO public.contacts VALUES (93, 41, '宛紫晶', '', '普通工程师', '', '', false, '2024-02-22 00:00:00', '2025-04-27 08:15:01.550989', NULL, 13);
INSERT INTO public.contacts VALUES (94, 41, '包顺强', '', '组长', '', '', false, '2024-02-22 00:00:00', '2025-04-27 08:15:01.551767', NULL, 13);
INSERT INTO public.contacts VALUES (95, 41, '尤文捷', '设计部门', '设计师', '', '', false, '2024-02-22 00:00:00', '2025-04-27 08:15:01.552539', NULL, 13);
INSERT INTO public.contacts VALUES (96, 81, '廖凯峰', '', '弱电主任工程师', '', '', false, '2024-02-22 00:00:00', '2025-04-27 08:15:01.553282', NULL, 13);
INSERT INTO public.contacts VALUES (97, 82, '钱成忠', '', '弱电主任工程师', '', '', false, '2024-02-22 00:00:00', '2025-04-27 08:15:01.554031', NULL, 13);
INSERT INTO public.contacts VALUES (98, 34, '李莉', '总经办', '总经理', '', '', false, '2024-02-22 00:00:00', '2025-04-27 08:15:01.554748', NULL, 13);
INSERT INTO public.contacts VALUES (99, 83, '邱小勇', '', '', '', '', false, '2024-02-22 00:00:00', '2025-04-27 08:15:01.5555', NULL, 13);
INSERT INTO public.contacts VALUES (100, 83, '熊泽祝', '设计部门', '总工', '', '', false, '2024-02-22 00:00:00', '2025-04-27 08:15:01.556215', NULL, 13);
INSERT INTO public.contacts VALUES (101, 83, '李佳莉', '设计部门', '技术经理', '', '', false, '2024-02-22 00:00:00', '2025-04-27 08:15:01.556877', NULL, 13);
INSERT INTO public.contacts VALUES (102, 83, '余海威', '18623100394', '技术经理', '', '', false, '2024-02-22 00:00:00', '2025-04-27 08:15:01.557559', NULL, 13);
INSERT INTO public.contacts VALUES (103, 85, '李冬', '业务部门', '总经理', '13585572944', '', false, '2024-02-21 15:36:42', '2025-04-27 08:15:01.55825', NULL, 13);
INSERT INTO public.contacts VALUES (104, 86, '邹飞', '销售部门', '总经理', '18221857788', '', false, '2024-02-21 15:32:11', '2025-04-27 08:15:01.558921', NULL, 13);
INSERT INTO public.contacts VALUES (105, 87, '张权玉', '工程部门', '经理', '13023198881', '', false, '2024-02-21 15:14:02', '2025-04-27 08:15:01.559668', NULL, 13);
INSERT INTO public.contacts VALUES (106, 88, '谭理', '信息设备部', '经理', '15921538269', '', false, '2024-02-21 15:02:52', '2025-04-27 08:15:01.560414', NULL, 13);
INSERT INTO public.contacts VALUES (107, 89, '邹娟', '业务部门', '经理', '17208290989', '', false, '2024-02-21 14:50:19', '2025-04-27 08:15:01.56114', NULL, 13);
INSERT INTO public.contacts VALUES (108, 25, '陈霆斌', '设计部门', '经理', '18980991113', '', false, '2024-02-21 14:45:42', '2025-04-27 08:15:01.561862', NULL, 13);
INSERT INTO public.contacts VALUES (109, 90, '程斌', '业务部门', '经理', '17765115659', '', false, '2024-02-21 14:40:32', '2025-04-27 08:15:01.56268', NULL, 13);
INSERT INTO public.contacts VALUES (110, 92, '陈旭东', '采购部门', '经理', '13518181739', '', false, '2024-02-21 11:55:50', '2025-04-27 08:15:01.56352', NULL, 13);
INSERT INTO public.contacts VALUES (111, 20, '余沛霖', '设计部门', '技术经理', '18628333765', '', false, '2024-02-21 11:52:16', '2025-04-27 08:15:01.56434', NULL, 13);
INSERT INTO public.contacts VALUES (112, 94, '胡萍', '', '', '', '', false, '2024-02-20 00:00:00', '2025-04-27 08:15:01.565082', NULL, 13);
INSERT INTO public.contacts VALUES (113, 94, '王辉', '', '总经理', '', '', false, '2024-02-20 00:00:00', '2025-04-27 08:15:01.565825', NULL, 13);
INSERT INTO public.contacts VALUES (114, 95, '陶亮', '', 'ESH部长', '', '', false, '2024-02-20 00:00:00', '2025-04-27 08:15:01.566555', NULL, 13);
INSERT INTO public.contacts VALUES (115, 96, '杨孝桥', '', '环安工程师', '', '', false, '2024-02-20 00:00:00', '2025-04-27 08:15:01.567284', NULL, 13);
INSERT INTO public.contacts VALUES (116, 96, '刘询', '', '环安经理', '', '', false, '2024-02-20 00:00:00', '2025-04-27 08:15:01.567955', NULL, 13);
INSERT INTO public.contacts VALUES (117, 97, '田亚辉', '', '设计经理', '', '', false, '2024-02-20 00:00:00', '2025-04-27 08:15:01.568643', NULL, 13);
INSERT INTO public.contacts VALUES (118, 97, '薛珈', '', '采购', '', '', false, '2024-02-20 00:00:00', '2025-04-27 08:15:01.569497', NULL, 13);
INSERT INTO public.contacts VALUES (119, 97, '周吉', '', '采购', '', '', false, '2024-02-20 00:00:00', '2025-04-27 08:15:01.570281', NULL, 13);
INSERT INTO public.contacts VALUES (120, 97, '吴晓珉', '', '采购', '', '', false, '2024-02-20 00:00:00', '2025-04-27 08:15:01.57099', NULL, 13);
INSERT INTO public.contacts VALUES (121, 97, '王磊', '', '技术', '', '', false, '2024-02-20 00:00:00', '2025-04-27 08:15:01.571717', NULL, 13);
INSERT INTO public.contacts VALUES (122, 97, '朱海燕', '', '合约经理', '', '', false, '2024-02-20 00:00:00', '2025-04-27 08:15:01.572439', NULL, 13);
INSERT INTO public.contacts VALUES (123, 97, '杨黎晶', '', '合约', '', '', false, '2024-02-20 00:00:00', '2025-04-27 08:15:01.573097', NULL, 13);
INSERT INTO public.contacts VALUES (124, 97, '顾云凯', '', '设计经理', '', '', false, '2024-02-20 00:00:00', '2025-04-27 08:15:01.573783', NULL, 13);
INSERT INTO public.contacts VALUES (125, 98, '诸力', '', '环安经理', '', '', false, '2024-02-20 00:00:00', '2025-04-27 08:15:01.574465', NULL, 13);
INSERT INTO public.contacts VALUES (126, 99, '赵奇', '', '', '', '', false, '2024-02-20 00:00:00', '2025-04-27 08:15:01.575137', NULL, 13);
INSERT INTO public.contacts VALUES (127, 100, '王羽东', '', '环安经理', '', '', false, '2024-02-20 00:00:00', '2025-04-27 08:15:01.575944', NULL, 13);
INSERT INTO public.contacts VALUES (128, 100, '陆大鼎', '', '环安经理', '', '', false, '2024-02-20 00:00:00', '2025-04-27 08:15:01.576809', NULL, 13);
INSERT INTO public.contacts VALUES (129, 101, '刘津佑', '', '部长', '', '', false, '2024-02-20 00:00:00', '2025-04-27 08:15:01.577725', NULL, 13);
INSERT INTO public.contacts VALUES (130, 102, '黄总', '', '弱电经理', '', '', false, '2024-02-20 00:00:00', '2025-04-27 08:15:01.578537', NULL, 13);
INSERT INTO public.contacts VALUES (131, 27, '胡俊凯', '', '采购', '', '', false, '2024-02-20 00:00:00', '2025-04-27 08:15:01.579254', NULL, 13);
INSERT INTO public.contacts VALUES (132, 27, '曹轶男', '', '采购', '', '', false, '2024-02-20 00:00:00', '2025-04-27 08:15:01.579959', NULL, 13);
INSERT INTO public.contacts VALUES (133, 27, '贾总', '', '事业部经理', '', '', false, '2024-02-20 00:00:00', '2025-04-27 08:15:01.580635', NULL, 13);
INSERT INTO public.contacts VALUES (134, 27, '徐述勤', '', '', '13910774801', '', false, '2024-02-20 00:00:00', '2025-04-27 08:15:01.58129', NULL, 13);
INSERT INTO public.contacts VALUES (135, 103, '秦磊', '', '', '', '', false, '2024-02-20 00:00:00', '2025-04-27 08:15:01.58202', NULL, 13);


--
-- Data for Name: projects; Type: TABLE DATA; Schema: public; Owner: pma_user
--

INSERT INTO public.projects VALUES (1, '项目测试123', '2025-04-19', 'channel_follow', '销售', '入围', '', '', '', '', '', '失败', '', 'CPJ202504-002', '2025-04-24', 13196000, NULL, NULL, '2025-04-15 10:00:45.952779', '2025-04-22 07:57:55', 5);
INSERT INTO public.projects VALUES (2, '第二个测试项目', '2025-04-16', 'sales_focus', '销售', '入围', '上海中心物业公司分公司', '', '', '', '上海安装第九分公司', '发现', '', 'SPJ202504-001', '2025-04-18', 25000, NULL, NULL, '2025-04-16 01:54:43.52487', '2025-04-22 07:58:40', 5);
INSERT INTO public.projects VALUES (5, '上海半导体场改造', '2025-04-19', 'channel_follow', '销售', '入围', '', '', '', '', '', '品牌植入', '', 'CPJ202504-003', '2025-04-19', 48142, NULL, NULL, NULL, '2025-04-22 08:48:14', 6);
INSERT INTO public.projects VALUES (6, '半导体中心修改名称', '2025-04-19', 'channel_follow', '销售', '围标', '上海中心物业公司分公司', '北京都市设计院', '上海航网瑞可', '上海建工集团', '上海安装第九分公司', '品牌植入', '', 'CPJ202504-001', '2025-04-19', 0, NULL, NULL, NULL, '2025-04-22 06:51:14', 7);
INSERT INTO public.projects VALUES (7, '中古广场项目', '2025-04-22', 'sales_focus', '经销商', '入围', '', '北京都市设计院', '', '', '上海安装第九分公司', '发现', '', 'SPJ202504-002', '2025-04-23', 0, NULL, NULL, NULL, NULL, 6);
INSERT INTO public.projects VALUES (8, '郑州机场配套工程', '2025-01-11', '销售重点', '市场', '不确定', NULL, NULL, NULL, NULL, '山西云时代技术有限公司', '中标', '2025/4/26 13:29:13 郭小会
【当前阶段】：改变成   中标
【当前阶段情况说明】：添加   山西云时代已中标

2025/4/26 13:28:23 郭小会
【系统集成商】：添加   山西云时代技术有限公司

2025/1/18 09:27:53 郭小会
【完善价格】 421273
2025/1/11 郭小会
【阶段变更】发现->品牌植入
类型改变为销售重点 
2025/4/26 13:29:29 郭小会
【品牌情况】：改变成   入围

', 'SPJ202501-002', '2025-04-26', 0, NULL, NULL, '2025-01-11 00:00:00', '2025-04-28 00:15:13.877898', 13);
INSERT INTO public.projects VALUES (9, '太原武宿国际机场三期停车楼项目', '2025-03-04', '销售重点', '市场', '入围', NULL, NULL, NULL, NULL, '山西云时代技术有限公司', '中标', '2025/4/26 郭小会
「王文」 山西云时代技术有限公司  针对新提供的招标文件，调整好清单报价给到王文，待其确认。项目是采用800M定制化产品，和赵沟通好产品需求，初步对产品成本进行评估报价，待客户明确回复采用我司产品后，再进行定制化处理
2025/3/4 13:27:56 郭小会
【完善价格】 124171
2025/3/4 13:25:05 郭小会
【系统集成商】：添加   山西云时代技术有限公司
【授权编号】：添加   HY-SPJ202503-001
【类型】：添加   销售重点

', 'SPJ202503-001', '2025-04-26', 0, NULL, NULL, '2025-03-04 00:00:00', '2025-04-28 00:15:13.880547', 13);
INSERT INTO public.projects VALUES (10, '西安咸阳机场南北过夜楼', '2025-04-08', '渠道跟进', '销售', '入围', NULL, NULL, NULL, NULL, '西安悦泰科技有限责任公司', '招标前', '2025/4/21 23:39:36 郭小会
【完善价格】 253534
2025/4/8 14:34:36 郭小会
【授权编号】：添加   HY-CPJ202504-008

2025/4/8 13:54:23 郭小会
提交报备
2025/4/5 11:52:39 郭小会
【完善价格】 236742
2025/4/5 11:19:23 郭小会
【系统集成商】：添加   西安悦泰科技有限责任公司

2025/4/5 郭小会
「张晓龙」 西安悦泰科技有限责任公司  项目已完成设计，北京顾问放在天馈品牌，悦泰前期参与询价，拜访悦泰采购经理，介绍公司的情况和产品优势，了解项目具体情况
', 'CPJ202504-008', '2025-04-21', 0, NULL, NULL, '2025-04-08 00:00:00', '2025-04-28 00:15:13.882313', 13);
INSERT INTO public.projects VALUES (11, '文山州妇女儿童医院', '2025-04-21', '销售重点', '销售', '不确定', NULL, NULL, NULL, NULL, NULL, '品牌植入', '2025/4/21 23:26:14 郭小会
【授权编号】：添加   HY-SPJ202504-003
【类型】：添加   销售重点

2025/4/20 08:36:10 郭小会
【完善价格】 257186
2025/4/20 08:34:54 郭小会
【完善价格】 200826
2025/4/20 08:27:17 郭小会
【完善价格】 265263
', 'SPJ202504-003', '2025-04-21', 0, NULL, NULL, '2025-04-21 00:00:00', '2025-04-28 00:15:13.883877', 13);
INSERT INTO public.projects VALUES (12, '太保家园成都国际颐养社区项目', '2024-08-22', '渠道跟进', '经销商', '入围', NULL, NULL, '成都市天皓科技有限公司', NULL, NULL, '中标', '2025/4/14 14:16:31 郭小会
申请项目批价
2025/4/14 14:11:17 郭小会
【完善价格】 69706
2025/4/11 14:56:21 郭小会
【完善价格】 159320
2025/3/8 10:04:04 郭小会
【出货时间预测】：改变成   2025年二季度

2024/9/27 郭小会
【阶段变更】招标中->中标

2024/8/22 12:15:13 郭小会
【消息】「」成都天皓科技报备，协调淳泊进行配合，分布产品和源品牌入围，现在推动天皓科技说服总包采用全和源产品，提供相关产品资料
', 'CPJ202408-010', '2025-04-14', 0, NULL, NULL, '2024-08-22 00:00:00', '2025-04-28 00:15:13.8864', 13);
INSERT INTO public.projects VALUES (13, '海南新能源汽车体验中心国际赛车场(一期)', '2025-02-19', '销售重点', '销售', '不确定', NULL, '华东建筑设计研究院有限公司', NULL, NULL, NULL, '品牌植入', '2025/4/11 郭小会
「王小安」 华东建筑设计研究院有限公司  和王总沟通最近配合他们三院的项目情况，组织下周和他们组和黄他们组聚餐活动，加强合作，海南新能源汽车项目预算还没有最终确定，目前我们系统还在保留，有些系统已砍掉。待情况明确后，业主负责人明朗后，安排我们对接
2025/3/18 17:19:28 郭小会
【完善价格】 515277
2025/2/19 09:04:40 郭小会
【设计院及顾问】：添加   华东建筑设计研究院有限公司
【类型】：添加   销售重点

2025/2/19 08:57:35 郭小会
【授权编号】：添加   HY-SPJ202501-007

', 'SPJ202501-007', '2025-04-11', 0, NULL, NULL, '2025-02-19 00:00:00', '2025-04-28 00:15:13.889312', 13);
INSERT INTO public.projects VALUES (14, '合肥新桥机场配套用房（综合楼和货运楼）', '2025-01-03', '销售重点', '销售', '入围', '合肥新桥国际机场有限公司', '上海远菁工程项目管理有限公司', '合肥兴和通讯设备有限公司', NULL, '南京禄口国际机场空港科技有限公司6', '招标中', '2025/4/10 17:09:26 郭小会
【当前阶段】：改变成   招标中
【当前阶段情况说明】：添加   项目品牌延用航站楼部分品牌，此次设计了解到是安徽省院的设计，没有完全参考航站楼的设计

2025/4/10 17:06:58 郭小会
【经销商】：添加   合肥兴和通讯设备有限公司
【系统集成商】：添加   南京禄口国际机场空港科技有限公司6

2025/4/10 郭小会
「付强」 南京禄口国际机场空港科技有限公司6  和付工沟通货运楼招标文件中的问题，原清单的缺失的设备，付工建议我们先列出来，他们和商务沟通投标策略
2025/4/10 郭小会
「尤力」 合肥兴和通讯设备有限公司  和尤总沟通货运楼投标参与的集成商情况，商务投标的策略
2025/1/3 郭小会
类型改变为销售重点 
2025/1/3 09:34:31 郭小会
【完善价格】 117440
', 'SPJ202501-001', '2025-04-10', 0, NULL, NULL, '2025-01-03 00:00:00', '2025-04-28 00:15:13.891298', 13);
INSERT INTO public.projects VALUES (24, '库尔勒华美胜地项目', '2024-09-29', '渠道跟进', '经销商', '入围', NULL, NULL, '青岛中亿海电子科技有限公司', NULL, NULL, '转移', '2025/3/25 14:29:40 郭小会
【当前阶段】：改变成   转移
【当前阶段情况说明】：添加   此项目中亿海配合的集成的未中标，宇洪配合的万安中标，项目转移给周裔锦

2024/9/29 13:51:03 郭小会
【完善价格】 87040
', 'CPJ202409-013', '2025-03-25', 0, NULL, NULL, '2024-09-29 00:00:00', '2025-04-28 00:15:13.903311', 13);
INSERT INTO public.projects VALUES (25, '青岛芯恩一期和二期系统整合', '2025-03-18', '渠道跟进', '市场', '入围', NULL, NULL, NULL, NULL, '上海竞拓数码信息技术有限公司', '招标中', '2025/3/18 17:04:33 郭小会
【授权编号】：添加   HY-CPJ202503-008

', 'CPJ202503-008', '2025-03-18', 0, NULL, NULL, '2025-03-18 00:00:00', '2025-04-28 00:15:13.904104', 13);
INSERT INTO public.projects VALUES (26, '成都音乐文创总部基地', '2025-03-18', '渠道跟进', '市场', '入围', NULL, NULL, '福淳智能科技(四川)有限公司', NULL, '安徽数安桥数据科技有限公司', '招标中', '2025/3/18 17:03:55 郭小会
【授权编号】：添加   HY-CPJ202503-007

', 'CPJ202503-007', '2025-03-18', 0, NULL, NULL, '2025-03-18 00:00:00', '2025-04-28 00:15:13.904916', 13);
INSERT INTO public.projects VALUES (15, '康桥二期集成电路生产线厂房及配套设施建设项目', '2024-01-31', '销售重点', '销售', '入围', '华虹半导体（上海）有限公司', '信息产业电子第十一设计院科技工程股份有限公司', '上海福玛通信信息科技有限公司', NULL, '北京中加集成智能系统工程有限公司', '中标', '2025/4/10 16:58:52 郭小会
【完善价格】 2141633
2025/4/9 12:01:32 郭小会
【完善价格】 2199233
2025/4/9 郭小会
「孟凡丽」 北京中加集成智能系统工程有限公司  和孟总他们沟通深化方案的问题，有几栋楼本次建设是毛坯，和业主沟通协商后，从本次清单中去掉，采用简单的临时系统，核对好深化的清单给集成商进行确认
2025/3/8 10:05:05 郭小会
【出货时间预测】：添加   2025年二季度

2025/2/24 17:08:40 郭小会
【完善价格】 2539508
2025/2/21 17:28:19 杨俊杰
【当前阶段】：改变成   转移
【当前阶段情况说明】：添加   该项目由郭总负责

2025/2/21 16:33:27 杨俊杰
【完善价格】 2019670
2025/2/7 09:10:58 郭小会
【直接用户】：添加   华虹半导体（上海）有限公司

2024/12/27 郭小会
【阶段变更】招标中->中标

2024/11/1 杨俊杰
【阶段变更】招标中->中标

2024/9/20 17:11:28 杨俊杰
【完善价格】 2019731
2024/9/14 郭小会
【阶段变更】品牌植入->招标中

2024/7/17 15:23:47 郭小会
【消息】「」通过博望程总介绍，和二期业主冯总对接，沟通需求，帮助业主出预算、推荐品牌
2024/6/15 09:06:43 郭小会
【消息】「」带刘威去一期现场勘查，和一期业主交流沟通现在存在的问题 以及二期的需求
2024/3/17 14:26:47 郭小会
博望电子在帮业主进行初设计，博望已发我们品算牌提给业主
2024/2/20 15:06:27 郭小会
设计方改变为  信息产业电子第十一设计院科技工程股份有限公司 类型改变为  销售重点 集成商改变为  上海博望电子科技有限公司    
2023/11/1 郭小会
1、配合陈总提供品牌资料，做品牌入围
', 'SPJ202401-003', '2025-04-10', 0, NULL, NULL, '2024-01-31 00:00:00', '2025-04-28 00:15:13.893002', 13);
INSERT INTO public.projects VALUES (16, '合肥新桥机场二期新建', '2023-11-02', '销售重点', '销售', '入围', NULL, '民航机场成都电子工程设计有限责任公司', '合肥兴和通讯设备有限公司', NULL, '北京京航安机场工程有限公司', '中标', '2025/4/10 郭小会
「尤力」 合肥兴和通讯设备有限公司  和尤总沟通目前合肥机场的最新情况，尤总已推动业主在会议上明确提出系统方案确定过程中需要现场提供设备，搭建平台进行测试，也通知到集成商，尤总了解到集成商的中标价格和竞争对手的报价，和尤总商量好报价策略，和尤总调整报价发给总包，看总包反应
2024/8/24 11:14:20 郭小会
【消息】「合肥兴和通讯设备有限公司」和设计院沟通了解到总包这边针对无线对讲系统还没有开始深化设计，没有提交任何资料，设计院会对方案进行把控，要求提交的方案完全满足招标要求；尤总也进一步和用户进行了沟通，用户也会坚持按招标要求来实施
2024/5/25 10:25:28 郭小会
【消息】「」代理商尤总已安排运营部门的负责人张总参观我们新换数字光端机，介绍了我们光端机的优势和特点，我们一起整理了我们这次投标的系统以及产品亮点，下周尤总和张总详细介绍一下，试图了解新的指挥部的负责人，准备接触影响指挥部的负责人
2024/4/24 14:52:01 郭小会
【消息】「」已了解到北京京航安中标，出乎意料，之前业主和设计院了解到内定的是西安悦泰，近期想办法确认京航安是否用的我司品牌进行投标
【阶段变更】中标->招标中
2024/5/18 10:41:19 郭小会
【消息】「」合肥出差，和代理商尤总沟通针对合肥机场项目接下来的策略，计划在合肥机场搭建平台，增强业主对我司产品的认可；拜访民航电子设计单位的现场项目经理易总，介绍我们公司的产品和合肥机场我们系统的情况，影响其关注我们系统中存在的问题
2024/5/12 09:58:51 郭小会
【消息】「」合肥机场通过代理商以及设计院的关系，了解到京航安传输设备采用了中兴高达进行投标，近期要整理相关信息和代理商一起想办法推动更换我司品牌
2024/4/13 09:37:17 郭小会
配合沈阳汇通、云南机场、京航安几家公司授权及投标文件制作
2024/4/6 20:54:37 郭小会
协调尤总配合北京中航弱电、南京禄口、云南机场、新疆网信几家集成商投标
2024/3/28 07:42:51 郭小会
【阶段变更】
项目进入投标阶段，和合肥兴和一起配合集成商投标，目前找到了西安悦泰、京航安两家集成商
2024/2/20 14:05:02 郭小会
围标状况改变为   入围 设计方改变为  民航机场成都电子工程设计有限责任公司 经销商改变为   合肥兴和通讯设备有限公司 用户改变为   合肥新桥国际机场有限公司 类型改变为  渠道管理    
已从设计院方面把我们的品牌推上去了，兴和的尤总也将我司品牌推给业主，配合兴和进行前期方案报价
', 'SPJ202311-002', '2025-04-10', 0, NULL, NULL, '2023-11-02 00:00:00', '2025-04-28 00:15:13.893919', 13);
INSERT INTO public.projects VALUES (17, '上海浦东国际机场四期扩建工程', '2024-02-21', '销售重点', '市场', '不确定 ', '上海机场(集团)有限公司', '华东建筑设计研究院有限公司', NULL, NULL, '上海市安装工程集团的限公司', '品牌植入', '2025/4/5 郭小会
「吴文芳」 华东建筑设计研究院有限公司  和吴老师沟通浦东机场四期的最新情况，现在浦东机场四期项目招标在小木桥路进行，公开招标，甚至不可以推荐品牌，看不清楚后面如何操作。吴老师建议待前面的安防标招好了后，看指挥部是如何操作的，我们的对讲系统招标计划在今年年底和明年年初。
2025/3/21 13:55:50 郭小会
【直接用户】：添加   上海机场(集团)有限公司

2025/3/11 14:08:52 郭小会
【系统集成商】：添加   上海市安装工程集团的限公司

2024/5/25 10:30:31 郭小会
【消息】「」浦东机场四期停车楼部分图纸已完成初步深化，交给华东院，近期再跟进时，了解最新进展以及业主的情况，徐昊给到业主顾婷婷近期也准备接触了解情况
2024/4/24 10:38:31 郭小会
【消息】「」建工通过上安九分反馈浦东机场四期建筑会采用新材料，可能信号屏蔽加强，对所有通信系统会有影响 ，要求相关通信厂家去嘉兴搭建的临时模型区域去测试评估，已协调安排可以杨和赵去现场测试，后续出具评估报告
2024/4/24 10:35:02 郭小会
【消息】「」浦东机场四期项目启动深化设计，带刘威参加华东院关于项目中停车楼部分的深化设计要求，本次深化设计主要是用于建筑招标，根据深化设计图纸，造价公司评估管材用量
2024/2/23 09:12:39 郭小会
面价金额改变为   10171807    
2024/2/21 郭小会
配合华东院吴老师进行前期设计规划，本次设计范围包括T3航站楼、南北车库和交通中心，系统包含消防对讲和公安对讲，边防对讲独立建设
', 'SPJ202402-002', '2025-04-05', 0, NULL, NULL, '2024-02-21 00:00:00', '2025-04-28 00:15:13.895232', 13);
INSERT INTO public.projects VALUES (18, '西安泰信大厦', '2023-07-24', '渠道跟进', '代理商', '入围', NULL, NULL, NULL, NULL, NULL, '搁置', '2025/4/5 郭小会
「邹茹飞」 西安瑞林达通信技术有限公司  西安泰信大厦项目资金有问题，项目搁置。和邹总介绍我们公司的产品优势，寻找合作点
2025/3/25 14:05:54 郭小会
【当前阶段】：改变成   搁置
【当前阶段情况说明】：添加   项目资金有问题，搁置了
【类型】：改变成   渠道跟进

2024/3/9 15:31:38 郭小会
项目投标后，总包一直未确定，代理商在跟进着
2023/11/1 郭小会
代理商报备，西安瑞林达
', 'CPJ202307-002', '2025-04-05', 0, NULL, NULL, '2023-07-24 00:00:00', '2025-04-28 00:15:13.896521', 13);
INSERT INTO public.projects VALUES (19, '西安咸阳国际机场三期扩建工程下穿通道项目', '2024-06-09', '销售重点', '经销商', '入围', NULL, NULL, '陕西无线电通信服务中心', NULL, NULL, '签约', '2025/4/5 郭小会
「张士彦」 陕西无线电通信服务中心  拜访陕西无线电张总，了解西安咸阳机场项目系统试用期的情况，后续安排系统最终联调和软件升级。针对张总他们化工业务的情况进行了深入的沟通和交流，介绍我们行业产品的优势，寻求行业项目的合作。
2025/1/3 16:44:50 郭小会
【完善价格】 72562
2024/8/24 11:05:09 郭小会
【消息】「」下穿通道陕西无线电已和对方确定合同意向，设备已向分司下单，并支付了预付款。本周配合陕西无线电提交资料，陕西无线电和总包走个投标流程
【阶段变更】中标->签约
2024/6/9 郭小会
下穿通道中标商原采用的是中原的产品，考虑到将来要接入到我们的系统，陕西无线电张总他们和指挥部及总包在做相应的沟通，要求光纤直入站变更为和源通信产品，目前在直审批变更流程
', 'SPJ202406-001', '2025-04-05', 0, NULL, NULL, '2024-06-09 00:00:00', '2025-04-28 00:15:13.89759', 13);
INSERT INTO public.projects VALUES (20, '润友科技（临港）总部大楼', '2023-07-25', '渠道跟进', '销售', '不确定', NULL, '上海延华智能科技（集团）股份有限公司', NULL, NULL, NULL, '失败', '2025/3/25 15:20:51 郭小会
【当前阶段】：改变成   失败
【当前阶段情况说明】：添加   此项目资金有问题，改成毛坯交付，无线对讲系统取消
【类型】：添加   渠道跟进

2024/12/31 郭小会
类型改变为 
', 'CPJ202307-003', '2025-03-25', 0, NULL, NULL, '2023-07-25 00:00:00', '2025-04-28 00:15:13.899036', 13);
INSERT INTO public.projects VALUES (21, '京东合作伙伴大厦', '2023-08-29', '渠道跟进', '代理商', '入围', NULL, NULL, '广州宇洪智能技术有限公司', NULL, NULL, '失败', '2025/3/25 15:19:06 郭小会
【当前阶段】：改变成   失败
【当前阶段情况说明】：添加   代理商配合的总包未中标
【类型】：改变成   渠道跟进

2024/9/7 22:19:25 郭小会
【消息】「」厦门万安已中标，宇洪在配合跟进
【阶段变更】招投标->中标
2023/11/1 郭小会
1、集成商投标，配合代理商提供资料
2、当前清单待敦力提供
3、待技术提供规定模板的清单
4、品牌和源、威升、京信，宇洪配合万安投标
', 'CPJ202308-001', '2025-03-25', 0, NULL, NULL, '2023-08-29 00:00:00', '2025-04-28 00:15:13.900344', 13);
INSERT INTO public.projects VALUES (22, '湖南绿之韵酒店项目', '2024-09-10', '渠道跟进', '销售', '不确定', NULL, NULL, '福淳智能科技(四川)有限公司', NULL, '湖南悟意信息技术有限公司', '失败', '2025/3/25 14:37:59 郭小会
【当前阶段】：改变成   失败
【当前阶段情况说明】：添加   代理商配合的集成商未中标
【类型】：改变成   渠道跟进

2024/11/30 郭小会
【阶段变更】招标前->招标中
类型改变为渠道管理 
45626 邹娟
【阶段变更】招标前->招标中
类型改变为渠道管理 
2024/9/10 18:36:43 郭小会
【完善价格】 118106
45545.7754976852 邹娟
【完善价格】 118106
', 'CPJ202409-005', '2025-03-25', 0, NULL, NULL, '2024-09-10 00:00:00', '2025-04-28 00:15:13.901352', 13);
INSERT INTO public.projects VALUES (23, '西部股权投资基金基地弱电工程项目', '2024-09-09', '渠道跟进', '经销商', '入围', NULL, NULL, '上海福玛通信信息科技有限公司', NULL, '中建四局智控与数字科技事业部', '失败', '2025/3/25 14:31:52 郭小会
【当前阶段】：改变成   失败
【当前阶段情况说明】：添加   代理商关系不到位，项目失败

2024/9/9 13:34:43 郭小会
【消息】「」福玛报备，配合集成商
【阶段变更】招标中->中标
45544.565775463 邹飞
【消息】「」福玛报备，配合集成商
【阶段变更】招标中->中标
', 'CPJ202409-003', '2025-03-25', 0, NULL, NULL, '2024-09-09 00:00:00', '2025-04-28 00:15:13.902281', 13);
INSERT INTO public.projects VALUES (27, '成都高投高新区福田站TOD片区综合开发项目', '2024-07-14', '渠道跟进', '经销商', '入围', NULL, '四川省建筑设计研究院有限公司', '福淳智能科技(四川)有限公司', NULL, '四川倍智数能信息工程有限公司', '招标前', '2025/3/3 10:24:27 郭小会
【出货时间预测】：改变成   2025年二季度

2025/2/7 09:12:40 郭小会
【系统集成商】：添加   四川倍智数能信息工程有限公司
【类型】：改变成   渠道跟进

45695.3837962963 邹娟
【系统集成商】：添加   四川倍智数能信息工程有限公司
【类型】：改变成   渠道跟进

2024/11/29 郭小会
类型改变为渠道管理 
45625 邹娟
类型改变为渠道管理 
2024/10/19 21:44:56 郭小会
【完善价格】 984824
45584.9062037037 邹娟
【完善价格】 984824
2024/7/14 郭小会
邹娟拜访四川省院，了解到成都高投高新区福田站TOD片区综合开发项目省院在设计，项目是EPC的，总包成都高投，内定的集成商是成都倍智，和邹娟沟通后，安排接触倍智进一步了解情况，计划8月中旬安排省院交流
45487 邹娟
邹娟拜访四川省院，了解到成都高投高新区福田站TOD片区综合开发项目省院在设计，项目是EPC的，总包成都高投，内定的集成商是成都倍智，和邹娟沟通后，安排接触倍智进一步了解情况，计划8月中旬安排省院交流
', 'CPJ202407-005', '2025-03-03', 0, NULL, NULL, '2024-07-14 00:00:00', '2025-04-28 00:15:13.905844', 13);
INSERT INTO public.projects VALUES (28, '南昌昌北机场三期扩建工程', '2025-02-14', '销售重点', '销售', '不确定', NULL, '民航机场成都电子工程设计有限责任公司', NULL, NULL, NULL, '品牌植入', '2025/2/14 10:53:45 郭小会
【设计院及顾问】：添加   民航机场成都电子工程设计有限责任公司
【类型】：添加   销售重点

2025/2/14 10:49:46 郭小会
【授权编号】：添加   HY-SPJ202501-005

', 'SPJ202501-005', '2025-02-14', 0, NULL, NULL, '2025-02-14 00:00:00', '2025-04-28 00:15:13.906729', 13);
INSERT INTO public.projects VALUES (29, '阿联酋料场', '2025-01-18', '销售重点', '销售', '入围', NULL, NULL, '上海福玛通信信息科技有限公司', NULL, '中国中钢股份有限公司', '招标前', '2025/2/7 09:01:25 郭小会
【完善价格】 1069048
2025/1/18 09:51:34 郭小会
【完善价格】 975738
2025/1/18 郭小会
类型改变为销售重点 
', 'SPJ202501-003', '2025-02-07', 0, NULL, NULL, '2025-01-18 00:00:00', '2025-04-28 00:15:13.907599', 13);
INSERT INTO public.projects VALUES (30, '西安咸阳国际机场三期扩建工程口岸货运区项目', '2023-07-03', '销售重点', '销售', '入围', NULL, '民航机场成都电子工程设计有限责任公司', '陕西无线电通信服务中心', NULL, '民航成都电子技术有限责任公司', '签约', '2025/1/3 16:36:13 郭小会
【完善价格】 51958
2024/7/14 09:25:15 郭小会
【消息】「」安排设备交付，设备已交付到陕西无线电，协调好航站楼坏的设备替换问题
2024/6/30 07:44:21 郭小会
【消息】「」预付款已付，交给董禕处理
【阶段变更】中标->签约
2024/6/15 09:09:23 郭小会
【消息】「」催收预付款，和供应链协调好了订货问题
2024/6/9 09:58:22 郭小会
【消息】「」西安咸阳机场口岸货站楼区域的光端直放站，陕西无线电已配合总包完成变更，我们双合约已签定
2024/4/23 08:32:33 郭小会
【消息】「」代理商张总已通过业主找到相应的集成商，进行对接，集成商现场天线和器件已安装完成，张总和集成商进行沟通洽谈，光端机采用和源品牌接入到机场系统，已在走品牌变更流程，统计光端机2近5远
2024/3/8 13:28:00 郭小会
总包这边之前选用的中原的设备，代理商张总和总包在沟通确认采用和源的光端设备，接入到航站楼
2024/2/20 12:09:16 郭小会
设计方改变为  民航机场成都电子工程设计有限责任公司 出货时间预测改变为  2024-04-30 当前阶段改变为   中标 类型改变为  销售重点    
和陕西无线电沟通询价问题，进行价格保护
2023/11/1 郭小会
1、项目投标
2、需确认代理商
', 'SPJ202307-001', '2025-01-03', 0, NULL, NULL, '2023-07-03 00:00:00', '2025-04-28 00:15:13.908643', 13);
INSERT INTO public.projects VALUES (31, '芜湖长飞半导体项目', '2023-11-02', '销售重点', '销售', '入围', '安徽长飞先进半导体有限公司', NULL, NULL, NULL, NULL, '签约', '2025/1/3 15:47:12 郭小会
【完善价格】 430000
2025/1/3 15:42:36 郭小会
【完善价格】 427000
2025/1/3 15:35:47 郭小会
【完善价格】 389000
2025/1/3 15:16:49 郭小会
【完善价格】 158507
2024/8/24 11:03:53 郭小会
【消息】「」沟通跟进预付款，预付款上周五已到帐
跟进记录 郭小会
【阶段变更】中标->签约
2024/7/14 09:26:57 郭小会
【消息】「」和业主沟通投标中的问题，采购从市场上寻了多家价格进行对比，想重新招标，业主IT负责人从中协调，调整报价，现在基本可以确定我们中标了，下周提交相关资质资料和商谈合同细节
【阶段变更】招标中->中标
2024/6/15 09:19:26 郭小会
【消息】「」现场和业主沟通其公司内部情况和相应节点，和业主合约部门进行商务沟通和谈判
【阶段变更】招标前->招标中
2024/6/9 09:32:23 郭小会
【消息】「」和业主沟通方案和报价问题，下周采购邀请三家去现场谈判，协调福玛和淳泊下周出差，现场谈判
2024/5/30 22:24:03 郭小会
【消息】「」业主打算自己招标，由IT部门负责招标工作，和业主沟通好入围三家供应商进行投标，IT负责人将其推荐 给采购，选择福玛、淳泊入围 ，计划我们公司中标，分包给淳泊，由淳泊负责实施交付
【阶段变更】品牌植入->招标前
2024/5/18 10:55:19 郭小会
【消息】「」配合长飞业主IT负责人提交方案汇报的的PPT,提交招标技术规格书
2024/2/21 12:43:38 郭小会
用户改变为   安徽长飞先进半导体有限公司 类型改变为  销售重点    
根据业主的需求，将方案和预算提交上去，等待业主内部上会讨论
', 'SPJ202311-001', '2025-01-03', 0, NULL, NULL, '2023-11-02 00:00:00', '2025-04-28 00:15:13.909578', 13);
INSERT INTO public.projects VALUES (32, '浦东机场四期配套能源中心', '2024-12-27', '销售重点', '销售', '不确定', NULL, '华东建筑设计研究院有限公司', NULL, NULL, NULL, '品牌植入', '2024/12/30 郭小会
类型改变为 
', 'SPJ202412-005', '2024-12-30', 0, NULL, NULL, '2024-12-27 00:00:00', '2025-04-28 00:15:13.910716', 13);
INSERT INTO public.projects VALUES (47, '茂名中央公园', '2023-04-14', '渠道跟进', '销售', '入围 ', NULL, '上海邮电设计咨询研究院有限公司', '广州宇洪智能技术有限公司', NULL, '杰创智能科技股份有限公司', '招投标', '2024/2/21 21:08:22 郭小会
集成商改变为  杰创智能科技股份有限公司    
代理商配合集成沟通方案和报价，总承包还未确定弱电分包
2024/2/21 20:54:57 郭小会
设计方改变为  上海邮电设计咨询研究院有限公司 分销商改编为   上海瑞康 经销商改变为   广州宇洪智能技术有限公司 类型改变为  渠道管理    
2023/11/1 郭小会
1、项目初设
2、品牌已入围 ，大总包开始询价，安排宇洪对接
', 'CPJ202304-002', '2024-02-21', 0, NULL, NULL, '2023-04-14 00:00:00', '2025-04-28 00:15:13.926183', 13);
INSERT INTO public.projects VALUES (48, '北京中芯京城二期12英寸芯片生产线厂房建设项目', '2025-04-25', '销售重点', '销售', '入围', NULL, NULL, NULL, NULL, '北京航天星桥科技股份有限公司', '品牌植入', '2025/4/25 19:07:38 范敬
【授权编号】：添加   HY-SPJ202504-001

2025/4/24 范敬
「马经理」 北京航天星桥科技股份有限公司  项目目前正处于前期方案清单配置中，土建已在施工中，预计三季度进行智能化招标，项目计划明年一季度结束。
2025/4/17 09:28:23 范敬
提交报备
', 'SPJ202504-001', '2025-04-25', 0, NULL, NULL, '2025-04-25 00:00:00', '2025-04-28 00:21:56.893154', 16);
INSERT INTO public.projects VALUES (33, '湖南长沙机场改扩建工程', '2022-11-07', '销售重点', '销售', '入围', NULL, '民航机场成都电子工程设计有限责任公司', NULL, NULL, '四川中科航建信息技术有限公司', '签约', '2024/11/30 郭小会
【阶段变更】中标->签约

2024/7/14 09:34:01 郭小会
【消息】「」带董禕去现场，现场勘察，和总包对接，了解项目的实际进度和节点，近期开始启动设备材料报审工作，预计8月初ITC的前端设备要进厂。和总包沟通线缆的问题，核好价重新进行报价，线缆厂家不能变，型号变化提交申请，问题不大
2024/6/21 13:05:53 郭小会
【消息】「」和李冬一起整理好合同初稿发给四川中航建，进行沟通跟进
2024/6/9 09:55:43 郭小会
【消息】「」和李冬一起去成都对接四川中航建的相关领导，项目由代理商签约和相关价格及付款进行了沟通，下周和李冬一起商定相关合约条款后再和总包进一步沟通
2024/5/12 09:56:38 郭小会
【消息】「」长沙机场深化方案调整的相关图纸进行了提交，和李冬沟通长沙机场的合作方式，双方达成一致，接下来可以进一步推进和总包的商务谈判
2024/4/23 08:55:10 郭小会
【消息】「」组织相关人员参加长沙机场深化设计成果汇报，根据为业主和总包方的意见进行深化设计方案调整
2024/4/13 09:46:09 郭小会
对接新的分包负责人，了解其公司的情况，进行初步的商务洽谈
2024/3/8 13:49:38 郭小会
总包已确定我们系统的分包单位四川中科航建，拿到联系方式，尽快对接
2024/3/8 13:48:21 郭小会
配合总包沟通汇报本次方案的亮点，安排技术整理相关文件，提交给总包
2024/2/20 15:44:48 郭小会
设计方改变为  民航机场成都电子工程设计有限责任公司 类型改变为  销售重点 集成商改变为  民航成都电子技术有限责任公司    
配合总包进行方案调整和深化设计，针对调研需求，进行清单报价变更申请
2023/11/1 郭小会
1、项目前期配合设计院和业主进行了方案植入，近期会招投标，目前招采中心有对外进行询价，重庆畅博在配合
2、李冬下周出差长沙进一步了解情况
3、需确认产品清单
4、项目需求调研已结束，下一步需要根据需求调整方安案给总包进行确认
5、配合总包进行方案深化
', 'SPJ202211-001', '2024-11-30', 0, NULL, NULL, '2022-11-07 00:00:00', '2025-04-28 00:15:13.912197', 13);
INSERT INTO public.projects VALUES (34, '成都市彭州全名健身中心', '2024-09-12', '渠道跟进', '经销商', '不确定', NULL, '中国建筑西南设计研究院有限公司', '福淳智能科技(四川)有限公司', NULL, NULL, '招标前', '2024/11/30 郭小会
类型改变为渠道管理 
45626 邹娟
类型改变为渠道管理 
', 'CPJ202409-006', '2024-11-30', 0, NULL, NULL, '2024-09-12 00:00:00', '2025-04-28 00:15:13.913505', 13);
INSERT INTO public.projects VALUES (35, '玉佛寺二期', '2024-09-27', '销售重点', '销售', '入围', NULL, '同济大学建筑设计研究院(集团)有限公司', NULL, NULL, NULL, '品牌植入', '2024/11/15 22:06:21 郭小会
【完善价格】 1479510
', 'SPJ202409-012', '2024-11-15', 0, NULL, NULL, '2024-09-27 00:00:00', '2025-04-28 00:15:13.914813', 13);
INSERT INTO public.projects VALUES (36, '芯浦天英项目', '2024-09-27', '渠道跟进', '经销商', '入围', NULL, '信息产业电子第十一设计院科技工程股份有限公司', '上海福玛通信信息科技有限公司', NULL, NULL, '品牌植入', NULL, 'CPJ202409-010', '2024-11-15', 0, NULL, NULL, '2024-09-27 00:00:00', '2025-04-28 00:15:13.915791', 13);
INSERT INTO public.projects VALUES (37, '万科左岸项目', '2024-11-15', '销售重点', '销售', '不确定', NULL, '深圳市麦驰物联股份有限公司上海分公司', NULL, NULL, NULL, '发现', NULL, 'SPJ202411-011', '2024-11-15', 0, NULL, NULL, '2024-11-15 00:00:00', '2025-04-28 00:15:13.916936', 13);
INSERT INTO public.projects VALUES (38, '嘉兴湖畔酒店', '2024-11-01', '销售重点', '销售', '不确定', NULL, '上海慧腾信息科技有限公司', NULL, NULL, NULL, '品牌植入', '2024/11/1 09:59:42 郭小会
【完善价格】 324173
', 'SPJ202411-004', '2024-11-01', 0, NULL, NULL, '2024-11-01 00:00:00', '2025-04-28 00:15:13.918153', 13);
INSERT INTO public.projects VALUES (39, '上海久茂置业发展有限公司久事中心项目', '2024-10-30', '销售重点', '销售', '不确定', NULL, '深圳市麦驰物联股份有限公司上海分公司', NULL, NULL, NULL, '发现', NULL, 'SPJ202410-005', '2024-10-30', 0, NULL, NULL, '2024-10-30 00:00:00', '2025-04-28 00:15:13.919182', 13);
INSERT INTO public.projects VALUES (40, '长沙机场改扩建配套地下遂道工程', '2024-07-14', '销售重点', '销售', '不确定', NULL, '上海市政工程设计研究总院（集团）有限公司', NULL, NULL, '湖南安众智能科技有限公司', '招标前', '2024/9/27 郭小会
【阶段变更】招标中->招标前

2024/7/14 郭小会
湖南长规院许总介绍安众的杨总，参与长沙机场地下隧道项目，给安众杨总介绍我们公司的情况，可以尝试合作
', 'SPJ202407-002', '2024-09-27', 0, NULL, NULL, '2024-07-14 00:00:00', '2025-04-28 00:15:13.920109', 13);
INSERT INTO public.projects VALUES (41, '合肥新桥机场一期合路平台改造', '2024-08-24', '销售重点', '经销商', '入围', NULL, NULL, '合肥兴和通讯设备有限公司', NULL, NULL, '签约', '2024/8/30 11:36:31 郭小会
【消息】「」合肥兴和已从公司拿货，消掉公司库存
【阶段变更】中标->签约
2024/8/24 11:12:05 郭小会
【消息】「」合肥兴和就本次机场对讲系统出现问题，推动合肥机场一期对讲系统更换合路平台，实现逐步替换和源产品，加强用户对和源产品的了解
', 'SPJ202408-006', '2024-08-30', 0, NULL, NULL, '2024-08-24 00:00:00', '2025-04-28 00:15:13.92099', 13);
INSERT INTO public.projects VALUES (42, '成都一带一路大厦', '2022-11-27', '销售重点', '销售', '入围', NULL, '中国建筑西南设计研究院有限公司', NULL, NULL, NULL, '品牌植入', '2024/5/12 10:08:44 郭小会
【消息】「」项目近期重启了，业主内部要设计单位进行系统重新审报，和延华的蔡总沟通后，配合蔡总准备相关的PPT汇报文件，修改技术规格
2023/11/1 郭小会
1、此项目西南院设计，延华是顾问，方案和品牌已植入，招标时间还没有确定
', 'SPJ202211-007', '2024-05-12', 0, NULL, NULL, '2022-11-27 00:00:00', '2025-04-28 00:15:13.92196', 13);
INSERT INTO public.projects VALUES (43, '内蒙古国际会议中心项目', '2024-04-16', '销售重点', '销售', NULL, NULL, '华东建筑设计研究院有限公司', NULL, NULL, NULL, '发现', '2024/4/16 郭小会
配合华东院王总提交对讲系统规划方案，王总整合后做总体汇报
', 'SPJ202404-001', '2024-04-16', 0, NULL, NULL, '2024-04-16 00:00:00', '2025-04-28 00:15:13.922832', 13);
INSERT INTO public.projects VALUES (44, '合肥新桥机场一期改造', '2023-04-19', '销售重点', '代理商', '入围', NULL, '民航机场成都电子工程设计有限责任公司', '合肥兴和通讯设备有限公司', NULL, NULL, '签约', '2024/4/12 23:36:32 郭小会
【阶段变更】
2024/2/20 14:57:42 郭小会
当前阶段改变为   中标 面价金额改变为   120834 用户改变为       
2024/2/20 13:49:35 郭小会
设计方改变为  民航机场成都电子工程设计有限责任公司 出货时间预测改变为  2024-04-30 用户改变为   合肥新桥国际机场有限公司 类型改变为  渠道管理    
已确定本次改造替换我们最新的数字光端机，一近两远，订单已确定，货已下。借用库存模拟光端机临时现场使用
2023/11/1 郭小会
合肥新桥机场一期业主现场通信去年出现过应急通信问题，武总他们在配合业主进行升级改造。配合其提供相关资料和报价
', 'SPJ202304-001', '2024-04-12', 0, NULL, NULL, '2023-04-19 00:00:00', '2025-04-28 00:15:13.923624', 13);
INSERT INTO public.projects VALUES (45, '西安咸阳国际机场三期扩建工程', '2023-02-14', '销售重点', '销售', '入围', NULL, '民航机场成都电子工程设计有限责任公司', '陕西无线电服务中心', NULL, '中国移动通信集团陕西有限公司西安分公司', '签约', '2024/3/17 14:19:05 郭小会
【阶段变更】
2024/2/20 12:05:31 郭小会
设计方改变为  民航机场成都电子工程设计有限责任公司 出货时间预测改变为  2024-04-30 当前阶段改变为   中标 类型改变为  销售重点 集成商改变为  中国移动通信集团陕西有限公司西安分公司    
沟通、安排项目深化，核成本，推动合约流程
2023/11/1 郭小会
前期设计
', 'SPJ202302-001', '2024-03-17', 0, NULL, NULL, '2023-02-14 00:00:00', '2025-04-28 00:15:13.924429', 13);
INSERT INTO public.projects VALUES (46, '河南省确山县人民医院新区医院建设项目', '2023-06-09', '渠道跟进', '销售', '入围', NULL, NULL, '河南天际达实业有限公司', NULL, '浪朝软件科技有限公司', '招投标', '2023/11/1 郭小会
1、集成商投标，暂时还没有消息，需要继续跟进
', 'CPJ202306-002', '2024-03-06', 0, NULL, NULL, '2023-06-09 00:00:00', '2025-04-28 00:15:13.925316', 13);
INSERT INTO public.projects VALUES (64, '无锡奥林匹克体育产业中心二期项目', '2024-09-13', '销售重点', '销售', '入围', NULL, NULL, '敦力(南京)科技有限公司', NULL, '南京聚立科技股份有限公司', '签约', '2025/4/2 09:39:29 范敬
[阶段变更] ->签约
2025/3/25 16:23:25 范敬
【完善价格】 403944
2025/3/25 15:35:25 范敬
【完善价格】 712203
2025/2/21 14:51:34 范敬
【完善价格】 719722
2024/11/20 12:36:31 范敬
【完善价格】 1065122
2024/9/13 15:57:41 范敬
【完善价格】 1520896
', 'SPJ202409-004', '2025-04-02', 0, NULL, NULL, '2024-09-13 00:00:00', '2025-04-28 00:21:56.920965', 16);
INSERT INTO public.projects VALUES (49, '龙舟计划二期--增补', '2025-04-25', '渠道跟进', '渠道', '入围', NULL, NULL, '北京联航迅达通信技术有限公司', NULL, '北京航天星桥科技股份有限公司', '中标', '2025/4/25 14:49:15 范敬
申请项目批价
2025/4/25 14:48:14 范敬
【授权编号】：添加   HY-CPJ202504-028

2025/4/25 范敬
「王超」 北京联航迅达通信技术有限公司  该部分对讲机已启动批价流程
2025/4/22 范敬
「马经理」 北京航天星桥科技股份有限公司  该部分对讲机已返回工厂调整功率。
2025/4/17 09:15:39 范敬
提交报备
2025/4/16 09:23:11 范敬
【完善价格】 58652
', 'CPJ202504-028', '2025-04-25', 0, NULL, NULL, '2025-04-25 00:00:00', '2025-04-28 00:21:56.897979', 16);
INSERT INTO public.projects VALUES (50, '北京新首钢园东南区1612-(774-779-784)地块项目', '2024-02-28', '销售重点', '销售', '入围', NULL, NULL, '北京联航迅达通信技术有限公司', NULL, '中建三局智能技术有限公司', '签约', '2025/4/25 范敬
「吴会从」 中建三局智能技术有限公司  拜访了项目部吴总，沟通了后续项目实施中的问题；包括软件部署等问题。
2025/4/22 范敬
「吴会从」 中建三局智能技术有限公司  拜访了项目部吴总，沟通了后续项目实施中的问题；包括软件部署等问题。
2024/8/31 15:23:11 范敬
【阶段变更】中标->签约

2024/8/18 14:14:38 范敬
【消息】「」与代理商沟通批价事宜
2024/7/20 14:22:50 范敬
【消息】「」779地块计划2025年6月完工
2024/7/18 07:49:05 范敬
【一致行动人】「」:  经销商联航迅达中标，进入合同签订阶段。784、774地块年底完工。
2024/7/12 范敬
【提案采纳】「」:  本项目基本确定和源提供的方案；未中标单位已收到消息；中标通知书暂未发出。
2024/7/5 10:46:01 范敬
【消息】「」第一轮投标结束，进入第二轮投标。二轮投标单位：北京联航迅达、雄安雄然、瀚网（共三家）；投标品牌：全部和源。
2024/6/29 12:09:38 范敬
【消息】「」该项目已于2024年6月25日完成招标资格预审，目前共有5家入围：淳泊、福玛、联航迅达、瀚网、雄安雄然电子；7月1日第一轮投标截止。
2024/6/22 12:15:28 范敬
【消息】「」本周集成商开始进行供应商招标工作，现已安排4-5家供应商报名进行资格预审，报名工作6.25中午结束。
2024/6/11 10:48:59 范敬
【阶段变更】品牌植入->中标
2024/6/9 13:15:13 范敬
【提案】「」:  配合集成商完成招采前的询价工作
2024/5/31 21:34:30 范敬
【提案】「」:  配合业主方要求做了系统优化
2024/4/20 11:02:02 范敬
沟通了最新的项目进展，774地块今年10月计划完工，779地块计划明年上半年完工。
2024/4/15 17:00:34 范敬
「提案」  :  更新了新的配置清单
2024/3/22 14:06:07 范敬
「提案」  :  向总包提交了新方案及报价
', 'SPJ202402-004', '2025-04-25', 0, NULL, NULL, '2024-02-28 00:00:00', '2025-04-28 00:21:56.899865', 16);
INSERT INTO public.projects VALUES (51, '中国民生银行金融科技研发中心项目', '2023-11-20', '销售重点', '销售', '入围', NULL, '中元国际工程设计研究院有限公司', '敦力(南京)科技有限公司', NULL, NULL, '品牌植入', '2025/4/24 范敬
「钱澄雨」 中元国际工程设计研究院有限公司  沟通了该项目的推进情况，目前该项目已从原落地合肥变更为福州；同时沟通了目前其负责的贵州项目。
2024/7/29 10:12:48 范敬
【消息】「」指导代理商敦力进行图纸和方案设计
2024/7/18 07:47:30 范敬
【消息】「」进入施工图设计阶段
2023/11/1 范敬
「阶段变更」
1、配合设计院规划技术参数要求，提出推荐品牌；
2、设计院出图阶段；
', 'SPJ202311-004', '2025-04-24', 0, NULL, NULL, '2023-11-20 00:00:00', '2025-04-28 00:21:56.901849', 16);
INSERT INTO public.projects VALUES (52, '雄安国贸中心', '2025-03-07', '渠道跟进', NULL, '入围', NULL, '北京博易基业工程顾问有限公司', NULL, NULL, NULL, '品牌植入', '2025/4/24 范敬
「田亚欧」 北京博易基业工程顾问有限公司  目前该项目的43#楼正在招标中，已有至少2家公司与我们进行了联系；项目投标截止时间为5月6日。
2025/4/10 范敬
「田亚欧」 北京博易基业工程顾问有限公司  沟通项目系统技术文件的细节要求
2025/4/9 范敬
「田亚欧」 北京博易基业工程顾问有限公司  沟通项目系统技术文件的细节要求
2025/3/7 14:25:16 范敬
【授权编号】：添加   HY-CPJ202503-002
【类型】：添加   渠道跟进

', 'CPJ202503-002', '2025-04-24', 0, NULL, NULL, '2025-03-07 00:00:00', '2025-04-28 00:21:56.903645', 16);
INSERT INTO public.projects VALUES (53, '天津中芯国际-改造项目', '2024-12-21', '渠道跟进', '销售', '入围', NULL, NULL, '天津比信科技股份有限公司', NULL, NULL, '品牌植入', '2025/4/23 范敬
「张群」 天津比信科技股份有限公司  对该项目进行了沟通，目前项目处于停滞阶段。
2025/2/25 15:24:56 范敬
【完善价格】 362013
2025/1/3 范敬
类型改变为渠道跟进 
', 'CPJ202412-010', '2025-04-23', 0, NULL, NULL, '2024-12-21 00:00:00', '2025-04-28 00:21:56.905264', 16);
INSERT INTO public.projects VALUES (54, '北京新首钢园东南区1612-(775-778--769-783-786)地块项目', '2024-04-28', '销售重点', '销售', '入围', NULL, NULL, '北京联航迅达通信技术有限公司', NULL, '中建电子工程有限公司-北京分公司', '签约', '2025/4/23 范敬
「冯子煜」 中建电子工程有限公司-北京分公司  沟通项目实施情况，协助经销商沟通了合同回款事宜。
2024/12/7 范敬
【阶段变更】中标->签约

2024/12/5 11:39:04 范敬
【完善价格】 703335
2024/12/5 11:38:09 范敬
【完善价格】 679263
2024/12/4 15:12:03 范敬
【完善价格】 1002335
2024/12/4 15:10:10 范敬
【完善价格】 1004381
2024/9/7 14:09:58 范敬
【消息】「」集成商计划中秋节前启动招采的招投标工作；9月份完成采购招标工作。
2024/8/31 15:31:41 范敬
【消息】「」目前正在做招采前期准备工作，安排代理商及配合单位入库。
2024/8/18 14:15:32 范敬
【消息】「」与集成商沟通招采计划时间
2024/7/20 14:24:07 范敬
【消息】「」769地块计划竣工时间11月底；
775地块计划竣工时间12月底；
778地块没进场施工，估计要明年开始。
2024/7/18 07:51:40 范敬
【提案】「」:  等待业主变更流程批复，进行招标。
2024/6/29 12:06:40 范敬
【消息】「」该项目的目前等待774-779地块招标的结果，确定品牌进行采购招标。
2024/6/19 17:21:45 范敬
【提案】「」:  整个项目划分为775-778-769地块和774-779地块两个标段，本项目只包含775-778-769地块的天馈、传输及对讲机产品。
2024/6/11 11:59:33 范敬
【消息】「」目前只保留775-778-769三个地块的内容，与774-779地块合用一个系统。
【阶段变更】品牌植入->中标
2024/5/17 13:34:27 范敬
【提案】「」:  根据项目要求调整方案。
2024/4/28 10:09:00 范敬
【提案】「」:  根据要求，配合集成商提交方案
【阶段变更】品牌植入->
', 'SPJ202404-004', '2025-04-23', 0, NULL, NULL, '2024-04-28 00:00:00', '2025-04-28 00:21:56.906725', 16);
INSERT INTO public.projects VALUES (55, '北京新首钢园东南区1612-(769)地块项目-调整增补', '2025-03-07', '销售重点', '销售', '入围', NULL, NULL, '上海淳泊信息科技有限公司', NULL, '中建电子工程有限公司-北京分公司', '品牌植入', '2025/4/23 范敬
「冯子煜」 中建电子工程有限公司-北京分公司  沟通了该地块系统调整问题，经沟通增加了软件平台管理系统；后续需协助进行批价审价。
2025/3/7 14:27:30 范敬
【授权编号】：添加   HY-SPJ202502-001
【类型】：添加   销售重点

', 'SPJ202502-001', '2025-04-23', 0, NULL, NULL, '2025-03-07 00:00:00', '2025-04-28 00:21:56.908442', 16);
INSERT INTO public.projects VALUES (56, '雄安国贸中心项目43#楼精装修工程及弱电智能化工程', '2025-04-19', '渠道跟进', '销售', '入围', NULL, NULL, NULL, NULL, '中辉至诚北京建设工程有限公司', '招标中', '2025/4/19 08:38:04 范敬
【完善价格】 62376
2025/4/19 08:37:18 范敬
【系统集成商】：添加   中辉至诚北京建设工程有限公司
【授权编号】：添加   申请报备

2025/4/19 08:06:53 范敬
【完善价格】 62376
2025/4/19 07:58:35 范敬
提交报备
2025/4/19 范敬
「罗布」 中辉至诚北京建设工程有限公司  配合集成商完成招标清单报价
', '申请报备', '2025-04-19', 0, NULL, NULL, '2025-04-19 00:00:00', '2025-04-28 00:21:56.910001', 16);
INSERT INTO public.projects VALUES (65, '国家会议中心二期配套项目（酒店项目）', '2025-03-25', '渠道跟进', '销售', NULL, NULL, NULL, NULL, NULL, '北京时代凌宇科技股份有限公司', '中标', '2025/4/2 09:20:33 范敬
【分销商】：添加   上海淳泊
【类型】：添加   渠道跟进

2025/3/25 15:16:30 范敬
【授权编号】：添加   HY-CPJ202503-022

', 'CPJ202503-022', '2025-04-02', 0, NULL, NULL, '2025-03-25 00:00:00', '2025-04-28 00:21:56.922183', 16);
INSERT INTO public.projects VALUES (90, '徐州市睢宁县医院院区智能化工程项目', '2024-05-09', '渠道跟进', '销售', '入围', NULL, '南京市建筑设计研究院有限责任公司', '敦力(南京)科技有限公司', NULL, NULL, '品牌植入', '2024/5/9 范敬
配合设计院完成方案清单设计
2024/5/9 花伟
配合设计院完成方案清单设计
', 'CPJ202405-003', '2024-12-13', 0, NULL, NULL, '2024-05-09 00:00:00', '2025-04-28 00:21:56.949324', 16);
INSERT INTO public.projects VALUES (272, '广州纺织博览中心', '2025-02-13', '渠道跟进', '销售', '入围', NULL, NULL, '广州洪昇智能科技有限公司', NULL, NULL, '招标前', '2025/2/13 10:18:24 周裔锦
【授权编号】：添加   HY-CPJ202502-007

', 'CPJ202502-007', '2025-02-13', 0, NULL, NULL, '2025-02-13 00:00:00', '2025-04-28 01:02:05.001517', 17);
INSERT INTO public.projects VALUES (57, '南京惠民路隧道项目', '2022-11-08', '销售重点', '销售', '入围', NULL, '苏交科集团股份有限公司南京设计中心', '敦力(南京)科技有限公司', NULL, '北京瑞华赢科技发展股份有限公司', '中标', '2025/4/17 范敬
「郭金亮」 北京瑞华赢科技发展股份有限公司  配合集成商完成询价工作
2025/4/11 范敬
「郭金亮」 北京瑞华赢科技发展股份有限公司  沟通项目目前推进情况，配合准备相关资料；项目负责人透露目前已有海能达代理商通过相关人员介绍在接触项目部。
2025/2/21 11:24:11 范敬
【当前阶段】：改变成   中标
【系统集成商】：添加   北京瑞华赢科技发展股份有限公司
【当前阶段情况说明】：添加   机电分包单位已中标。

2024/7/20 14:19:29 范敬
【消息】「」目前主体结构基本结束，计划2024年四季度开始机电招标，计划2025年完工。土建总包单位：中铁四局。
2023/11/1 范敬
「阶段变更」
项目设计已结束，目前项目在审图阶段；按和源品牌设计。
该项目EPC总承包，已进入总包预算询价中。后期会采用专业分包模式。
', 'SPJ202211-004', '2025-04-17', 0, NULL, NULL, '2022-11-08 00:00:00', '2025-04-28 00:21:56.911617', 16);
INSERT INTO public.projects VALUES (58, '无锡奥林匹克体育产业中心一期项目', '2024-04-28', '销售重点', '销售', '入围', NULL, NULL, '敦力(南京)科技有限公司', NULL, '南京聚立科技股份有限公司', '签约', '2025/4/16 范敬
「花伟」 敦力(南京)科技有限公司  指导代理商技术进行项目图纸深化。
2025/4/14 范敬
「花伟」 敦力(南京)科技有限公司  督促支付该项目软件订单款项
2025/4/10 范敬
「花伟」 敦力(南京)科技有限公司  督促代理商完成软件项目的订单签署机付款。
2025/4/2 09:26:42 范敬
[阶段变更] ->签约
2025/4/2 范敬
「花伟」 敦力(南京)科技有限公司  启动并与公司完成了项目软件的直接订单工作
2025/4/1 范敬
「花伟」 敦力(南京)科技有限公司  补充了相关品牌报审资料
2025/3/25 16:21:29 范敬
【完善价格】 171020
2025/3/25 15:31:45 范敬
【完善价格】 421171
2025/3/24 11:56:16 范敬
【完善价格】 293985
2025/2/21 14:45:31 范敬
【完善价格】 291433
2024/12/1 范敬
【出现困难】与施工单位推荐的海能达+侨讯竞争；我们有技术优势，但价格没有竞争力。

2024/11/20 12:31:15 范敬
【完善价格】 345379
2024/9/13 15:13:14 范敬
【完善价格】 452964
2024/8/18 13:47:47 范敬
【消息】「」目前已和中标集成商建立沟通关系，该项目处于一期管线阶段，后续将进入设备招采阶段。
【阶段变更】品牌植入->中标
2024/4/28 11:24:56 范敬
【消息】「」包含一场两馆（体育场、体育馆和游泳馆）及配套商业与全民健身中心，目前为“一场两馆”及中央地库区域。
2024/4/28 范敬
【提案】:  配合集成商出清单及方案
', 'SPJ202404-005', '2025-04-16', 0, NULL, NULL, '2024-04-28 00:00:00', '2025-04-28 00:21:56.913235', 16);
INSERT INTO public.projects VALUES (59, '桑田科学岛科创中心项目东片区实验室项目（实验楼、地库及能源中心）', '2025-01-07', '销售重点', '销售', '入围', NULL, NULL, NULL, NULL, '江苏瀚远科技股份有限公司', '中标', '2025/4/15 范敬
「姚强」 江苏瀚远科技股份有限公司  沟通项目进展，目前刚刚进场施工，主要集中在桥架管线，系统品牌基本计划在5月中旬确定。目前苏州2家产品商已和他们有所接触；苏州中瀚（孙建忠）已报出非常低的价格；但瀚远目前没有采纳中瀚。
2025/3/24 13:13:10 范敬
【出货时间预测】：添加   2025年二季度

2025/3/22 10:02:56 范敬
【当前阶段】：改变成   中标
【系统集成商】：添加   江苏瀚远科技股份有限公司
【当前阶段情况说明】：改变成   已完成招标，中标单位已公示。

2025/2/25 15:20:53 范敬
【完善价格】 1955362
2025/1/7 08:50:48 范敬
【授权编号】：添加   HY-SPJ202412-006
【类型】：添加   销售重点

', 'SPJ202412-006', '2025-04-15', 0, NULL, NULL, '2025-01-07 00:00:00', '2025-04-28 00:21:56.914476', 16);
INSERT INTO public.projects VALUES (60, '南京建宁西路过江隧道项目', '2022-11-08', '销售重点', '销售', '入围', NULL, '苏交科集团股份有限公司南京设计中心', '敦力(南京)科技有限公司', NULL, '南京中建安装集团', '招标中', '2025/4/14 范敬
「陈华」 敦力(南京)科技有限公司  约见拜访项目机电总包方项目经理（总），沟通项目合作事宜。目前海能达通过南京广电公司在参与该项目，现在争取除350M公安系统外的系统。
2024/9/28 范敬
【阶段变更】品牌植入->招标中

2024/7/20 14:12:52 范敬
【消息】「」项目现阶段处于土建结构施工阶段，争取年底完成隧道土建工作；计划2025年转入配套工程的招投标和施工，计划争取2025年底建成。土建总包方中铁十四局。
2023/11/1 范敬
「阶段变更」
项目已设计完成，目前审图阶段，按和源品牌设计。
', 'SPJ202211-003', '2025-04-14', 0, NULL, NULL, '2022-11-08 00:00:00', '2025-04-28 00:21:56.915824', 16);
INSERT INTO public.projects VALUES (61, '四川农村商业联合银行股份有限公司黄舣数
据中心机房', '2025-03-29', '销售重点', '渠道', '入围', NULL, '中国建筑设计研究院有限公司', '敦力(南京)科技有限公司', NULL, NULL, '品牌植入', '2025/4/12 09:17:52 范敬
【完善价格】 229911
2025/4/2 09:34:11 范敬
【品牌情况】：添加   入围
【类型】：添加   销售重点

2025/3/29 07:58:58 范敬
【授权编号】：添加   HY-SPJ202503-003

2025/3/24 13:20:07 范敬
【经销商】：添加   敦力(南京)科技有限公司

2025/3/22 10:13:48 范敬
【分销商】：添加   上海淳泊

2025/3/22 10:13:26 范敬
【设计院及顾问】：添加   中国建筑设计研究院有限公司

', 'SPJ202503-003', '2025-04-12', 0, NULL, NULL, '2025-03-29 00:00:00', '2025-04-28 00:21:56.917085', 16);
INSERT INTO public.projects VALUES (62, '苏州工业园区银科产业投资有限公司桑田科学岛科创中心（DK20230518地块）项目', '2025-03-29', '销售重点', '销售', '入围', NULL, NULL, '敦力(南京)科技有限公司', NULL, '江苏瀚远科技股份有限公司', '搁置', '2025/4/10 范敬
「花伟」 敦力(南京)科技有限公司  与相关集成商沟通，项目目前具体情况
2025/4/2 范敬
「花伟」 敦力(南京)科技有限公司  与集成商做了初步沟通
2025/3/29 08:18:33 范敬
【授权编号】：添加   HY-SPJ202503-002
【类型】：添加   销售重点

2025/3/29 07:59:56 范敬
【授权编号】：添加   HY-SPJ202503-002
【类型】：添加   销售重点

', 'SPJ202503-002', '2025-04-10', 0, NULL, NULL, '2025-03-29 00:00:00', '2025-04-28 00:21:56.918335', 16);
INSERT INTO public.projects VALUES (63, '华泰证券股份有限公司华泰证券研发及培训中心项目', '2025-02-20', '销售重点', '销售', NULL, '华泰证券股份有限公司', '中通服咨询设计研究院有限公司', '敦力(南京)科技有限公司', NULL, NULL, '品牌植入', '2025/4/10 范敬
「赵婧」 中通服咨询设计研究院有限公司  与设计工程师沟通推荐品牌事宜，目前推荐品牌如下：
信道机和对讲机：摩托罗拉，海能达，和源通信；
信号中继（近、远端直放站）及天馈（天线、功分耦合器）分布：福玛通信、淳泊、和源通信；
线缆：中天、亨鑫、德通；
2025/2/20 16:41:50 范敬
【直接用户】：添加   华泰证券股份有限公司

2025/2/20 16:31:25 范敬
【授权编号】：添加   HY-SPJ202501-006
【类型】：添加   销售重点

', 'SPJ202501-006', '2025-04-10', 0, NULL, NULL, '2025-02-20 00:00:00', '2025-04-28 00:21:56.919628', 16);
INSERT INTO public.projects VALUES (167, '长兴镇38-07地块', '2025-04-21', '渠道跟进', '渠道', '入围', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '上海数码通系统集成有限公司', '招标中', '2025/4/25 14:29:03 杨俊杰
【完善价格】 157618
2025/4/21 11:52:09 杨俊杰
【授权编号】：添加   HY-CPJ202504-025

2025/4/18 17:09:26 杨俊杰
提交报备
', 'CPJ202504-025', '2025-04-25', 0, NULL, NULL, '2025-04-21 00:00:00', '2025-04-28 01:00:52.277283', 14);
INSERT INTO public.projects VALUES (66, '上海市松江区巨人科技园B楼项目弱电智能化投标项目', '2023-04-20', '渠道跟进', '代理商', '入围', NULL, NULL, '敦力(南京)科技有限公司', NULL, '苏州朗捷通智能科技有限公司', '签约', '2025/3/31 范敬
「花伟」 敦力(南京)科技有限公司  完成批价流程
2025/3/28 11:00:33 范敬
[阶段变更] ->签约
2025/3/20 13:52:20 李博
【设计院及顾问】：改变成   浙江省建筑设计院
【当前阶段情况说明】：添加   目前设计阶段，项目刚刚土建阶段，持续跟踪中

2025/2/14 17:34:56 范敬
【出货时间预测】：添加   2025年一季度3月份

2025/2/14 17:34:56 花伟
【出货时间预测】：添加   2025年一季度3月份

2025/2/14 17:23:19 范敬
【完善价格】 86873
2025/2/14 17:23:19 花伟
【完善价格】 86873
2025/1/3 范敬
类型改变为渠道跟进 
2025/1/3 花伟
类型改变为渠道跟进 
45642 李博
类型改变为销售重点 
2024/12/16 李华伟
类型改变为销售重点 
45635 李博
类型改变为渠道管理 
2024/12/9 李华伟
类型改变为渠道管理 
45408 李博
「拜访」:  接触了EPC分包四川本宇建设，目前他们在确认整体方案和预算品牌，目前接触下来让我们配合出一稿预算，后续跟进情况。
2024/4/26 李华伟
「拜访」:  接触了EPC分包四川本宇建设，目前他们在确认整体方案和预算品牌，目前接触下来让我们配合出一稿预算，后续跟进情况。
', 'CPJ202404-006', '2025-03-31', 0, NULL, NULL, '2023-04-20 00:00:00', '2025-04-28 00:21:56.923383', 16);
INSERT INTO public.projects VALUES (67, '上海静安太保家园', '2024-03-27', '渠道跟进', '经销商', '入围', NULL, NULL, '敦力(南京)科技有限公司', NULL, '泽宇科技工程有限公司', '签约', '2025/3/31 范敬
「花伟」 敦力(南京)科技有限公司  完成批价流程
2025/3/29 08:23:40 范敬
[阶段变更] ->签约
2025/3/25 16:12:03 范敬
【完善价格】 117016
2025/2/14 17:36:25 范敬
【出货时间预测】：添加   2025年一季度3月份

2025/2/14 17:36:25 花伟
【出货时间预测】：添加   2025年一季度3月份

2025/1/14 12:07:52 范敬
【完善价格】 232024
2025/1/14 12:07:52 花伟
【完善价格】 232024
2024/12/1 范敬
【阶段变更】招标前->中标

2024/12/1 花伟
【阶段变更】招标前->中标

2024/7/11 16:43:05 范敬
【提案】「」:  经销商已配合集成商投标，结果未出。
2024/7/11 16:43:05 花伟
【提案】「」:  经销商已配合集成商投标，结果未出。
2024/3/27 15:10:19 范敬
「提案」  :  配合代理商完成招标前的项目清单及预算
2024/3/27 15:10:19 花伟
「提案」  :  配合代理商完成招标前的项目清单及预算
', 'CPJ202403-010', '2025-03-31', 0, NULL, NULL, '2024-03-27 00:00:00', '2025-04-28 00:21:56.924792', 16);
INSERT INTO public.projects VALUES (68, '南京江北新金融中心一期项目DFG地块弱电智能化工程', '2024-12-01', '销售重点', '销售', '入围', NULL, '华东建筑设计研究院有限公司', '敦力(南京)科技有限公司', NULL, '中国江苏国际经济技术合作有限公司', '中标', '2025/3/24 13:14:01 范敬
【出货时间预测】：添加   2025年三季度

2025/2/14 09:25:58 范敬
【完善价格】 1506548
2025/1/6 14:44:12 范敬
【当前阶段】：改变成   中标
【当前阶段情况说明】：添加   目前中标公示已结束，集成商正在与业主沟通中

2024/12/7 19:08:17 范敬
【完善价格】 1257796
', 'SPJ202412-001', '2025-03-24', 0, NULL, NULL, '2024-12-01 00:00:00', '2025-04-28 00:21:56.926197', 16);
INSERT INTO public.projects VALUES (69, '桑田科学岛科创中心项目东片区实验室项目（行政楼）', '2024-11-16', '销售重点', '销售', '入围', NULL, NULL, '敦力(南京)科技有限公司', NULL, '苏州宏凡信息科技有限公司', '中标', '2025/3/24 13:12:35 范敬
【出货时间预测】：添加   2025年二季度

2024/11/16 范敬
【出现困难】需要与苏州地产品牌：邦耀电子和苏州中瀚两个品牌PK；

2024/11/16 17:46:23 范敬
【完善价格】 184100
', 'SPJ202411-012', '2025-03-24', 0, NULL, NULL, '2024-11-16 00:00:00', '2025-04-28 00:21:56.927371', 16);
INSERT INTO public.projects VALUES (70, '荡口古镇太师府酒店建设项目智能化工程', '2024-01-11', '渠道跟进', '集成商', '入围', NULL, NULL, '敦力(南京)科技有限公司', NULL, '天威虎建设集团有限公司', '签约', '2025/3/14 16:08:56 范敬
[阶段变更] ->签约
2025/3/10 15:42:05 范敬
【完善价格】 202248
2025/3/10 14:51:53 范敬
【完善价格】 200808
2025/3/10 14:49:00 范敬
【完善价格】 114408
2025/3/7 14:31:20 范敬
【完善价格】 244452
2025/2/19 11:25:13 花伟
【完善价格】 96450
2025/2/14 17:38:04 范敬
【出货时间预测】：添加   2025年一季度3月份

2025/2/14 17:38:04 花伟
【出货时间预测】：添加   2025年一季度3月份

2024/7/14 09:55:15 范敬
【消息】「」等待集成商通知商务谈判
2024/7/14 09:55:15 花伟
【消息】「」等待集成商通知商务谈判
2024/6/19 17:16:41 范敬
【提案】「」:  与集成商技术经理、采购经理沟通确定了方案与清单
2024/6/19 17:16:41 花伟
【提案】「」:  与集成商技术经理、采购经理沟通确定了方案与清单
2024/6/11 12:17:01 范敬
【阶段变更】招投标->中标
2024/6/11 12:17:01 花伟
【阶段变更】招投标->中标
2024/3/15 15:20:51 范敬
「拜访」  :  汇同南京代理商（敦力）约见预中标集成商（天威虎）沟通项目后续合作事宜。
2024/3/15 15:20:51 花伟
「拜访」  :  汇同南京代理商（敦力）约见预中标集成商（天威虎）沟通项目后续合作事宜。
2023/11/1 范敬
「阶段变更」
1、配合集成商投标；
2023/11/1 花伟
「阶段变更」
1、配合集成商投标；
', 'CPJ202401-006', '2025-03-14', 0, NULL, NULL, '2024-01-11 00:00:00', '2025-04-28 00:21:56.928583', 16);
INSERT INTO public.projects VALUES (71, '中江国际集团公司总部新办公园区', '2024-03-15', '销售重点', '销售', '入围', NULL, '中国江苏国际经济技术合作集团有限公司建筑设计院', NULL, NULL, NULL, '失败', '2025/3/14 14:52:22 范敬
【当前阶段】：改变成   失败
【当前阶段情况说明】：添加   因投资资金减少，取消该系统。

2024/6/9 13:07:04 范敬
【提案】「」:  目前已完成园区A栋自用办公楼的初步图纸设计，选用MA12定位功能
2024/4/25 14:44:25 范敬
「消息」「」配合业主及设计方前期设计
2024/4/25 14:44:06 范敬
「阶段变更」品牌植入->发现
2024/3/15 范敬
「拜访」  :  约见业主建设部门相关技术负责人，了解项目情况同时介绍公司及产品，提出项目解决方案。
', 'SPJ202403-001', '2025-03-14', 0, NULL, NULL, '2024-03-15 00:00:00', '2025-04-28 00:21:56.929658', 16);
INSERT INTO public.projects VALUES (72, '国家会展中心(北区)厨房工程项目（天津）', '2025-02-11', '渠道跟进', '销售', '入围', NULL, NULL, '天津比信科技股份有限公司', NULL, '清华同方股份有限公司同方智慧建筑与园区公司', '招标中', '2025/2/28 08:51:20 范敬
【当前阶段】：改变成   招标中
【系统集成商】：改变成   清华同方股份有限公司同方智慧建筑与园区公司
【当前阶段情况说明】：改变成   项目已进入招投标阶段，目前总包方及业主方意向性中标方为清华同方。

2025/2/14 09:12:01 范敬
【完善价格】 476420
2025/2/11 09:28:45 范敬
【授权编号】：添加   HY-CPJ202502-005
【类型】：添加   渠道跟进

', 'CPJ202502-005', '2025-02-28', 0, NULL, NULL, '2025-02-11 00:00:00', '2025-04-28 00:21:56.930741', 16);
INSERT INTO public.projects VALUES (89, '中原高铁港数字展贸城', '2024-12-07', '渠道跟进', '经销商', '入围', '河南空港建设发展有限公司', '同济大学建筑设计研究院（集团）有限公司', '敦力(南京)科技有限公司', NULL, NULL, '品牌植入', '2024/12/21 19:35:52 范敬
【完善价格】 720113
2024/12/21 19:35:52 花伟
【完善价格】 720113
2024/12/16 范敬
类型改变为渠道管理 
2024/12/16 花伟
类型改变为渠道管理 
', 'CPJ202412-003', '2024-12-21', 0, NULL, NULL, '2024-12-07 00:00:00', '2025-04-28 00:21:56.948405', 16);
INSERT INTO public.projects VALUES (73, '南京市鼓楼区2019G61地块项目（中信泰富江苏总部）', '2022-12-28', '渠道跟进', '销售', '入围', NULL, '南京长江都市建筑设计院', '敦力(南京)科技有限公司', NULL, '南京熊猫信息产业有限公司', '中标', '2025/2/25 15:39:17 范敬
【当前阶段】：改变成   中标

2025/2/25 15:11:14 范敬
【系统集成商】：添加   南京熊猫信息产业有限公司
【当前阶段情况说明】：添加   目前智能化中标单位已进场

2023/11/1 范敬
「阶段变更」
项目现在处于设计阶段（具体设计师：吴玥群）
2023/11/1 花伟
「阶段变更」
项目现在处于设计阶段（具体设计师：吴玥群）
', 'CPJ202212-004', '2025-02-25', 0, NULL, NULL, '2022-12-28 00:00:00', '2025-04-28 00:21:56.931784', 16);
INSERT INTO public.projects VALUES (74, '阳澄湖健康颐养酒店', '2023-06-30', '渠道跟进', '销售', '入围', NULL, NULL, '苏州邦耀电子', NULL, NULL, '品牌植入', '2025/2/25 15:32:06 范敬
【完善价格】 272060
2023/11/1 范敬
「阶段变更」
配合集成商修改调整方案
', 'CPJ202306-004', '2025-02-25', 0, NULL, NULL, '2023-06-30 00:00:00', '2025-04-28 00:21:56.932868', 16);
INSERT INTO public.projects VALUES (75, '武汉阳逻国际冷链产业园区项目', '2023-09-05', '渠道跟进', '销售', '不确定', NULL, NULL, NULL, NULL, NULL, '品牌植入', '2025/2/25 15:29:07 范敬
【完善价格】 153598
2023/11/1 范敬
「阶段变更」
配合方案设计，品牌植入
', 'CPJ202309-003', '2025-02-25', 0, NULL, NULL, '2023-09-05 00:00:00', '2025-04-28 00:21:56.933992', 16);
INSERT INTO public.projects VALUES (76, '无锡国家软件园五期项目', '2023-09-05', '渠道跟进', '销售', '不确定', NULL, NULL, '敦力(南京)科技有限公司', NULL, NULL, '品牌植入', '2025/2/25 15:26:36 范敬
【完善价格】 374246
2023/11/1 范敬
「阶段变更」
前期配合设计品牌植入
2023/11/1 花伟
「阶段变更」
前期配合设计品牌植入
', 'CPJ202309-004', '2025-02-25', 0, NULL, NULL, '2023-09-05 00:00:00', '2025-04-28 00:21:56.935051', 16);
INSERT INTO public.projects VALUES (77, '青少年体育发展中心智能化工程', '2024-10-23', '渠道跟进', '销售', '入围', NULL, NULL, '敦力(南京)科技有限公司', NULL, '南京东大智能化系统有限公司', '品牌植入', '2025/2/25 15:18:54 范敬
【完善价格】 169599
2024/10/24 10:33:39 范敬
【完善价格】 169601
2024/10/24 10:33:39 花伟
【完善价格】 169601
', 'CPJ202410-013', '2025-02-25', 0, NULL, NULL, '2024-10-23 00:00:00', '2025-04-28 00:21:56.936048', 16);
INSERT INTO public.projects VALUES (78, '麒麟科创园3-3地块2号楼智能化工程', '2024-11-16', '渠道跟进', '经销商', '入围', NULL, NULL, '敦力(南京)科技有限公司', NULL, '盛云科技有限公司南京分公司', '招标前', '2025/2/25 15:16:06 范敬
【完善价格】 193868
2024/11/16 17:15:56 范敬
【完善价格】 193872
', 'CPJ202411-007', '2025-02-25', 0, NULL, NULL, '2024-11-16 00:00:00', '2025-04-28 00:21:56.937092', 16);
INSERT INTO public.projects VALUES (79, '江山汇项目 D 地块弱电智能化工程项目', '2024-05-17', '渠道跟进', '经销商', '入围', NULL, NULL, '敦力(南京)科技有限公司', NULL, NULL, '品牌植入', '2025/2/25 14:45:12 范敬
【完善价格】 205651
2024/9/21 16:12:56 范敬
【完善价格】 205653
2024/9/21 16:12:56 花伟
【完善价格】 205653
2024/5/17 范敬
【提案】:  配合集成商出设计、方案及清单
2024/5/17 花伟
【提案】:  配合集成商出设计、方案及清单
', 'CPJ202405-006', '2025-02-25', 0, NULL, NULL, '2024-05-17 00:00:00', '2025-04-28 00:21:56.938126', 16);
INSERT INTO public.projects VALUES (80, 'MY07 Dragonfly 总包项目', '2024-12-21', '渠道跟进', '经销商', '入围', NULL, NULL, '敦力(南京)科技有限公司', NULL, NULL, '品牌植入', '2025/2/25 14:23:51 范敬
【完善价格】 524616
2025/1/3 范敬
类型改变为渠道跟进 
2025/1/3 花伟
类型改变为渠道跟进 
', 'CPJ202412-008', '2025-02-25', 0, NULL, NULL, '2024-12-21 00:00:00', '2025-04-28 00:21:56.939156', 16);
INSERT INTO public.projects VALUES (81, '南京建宁西路隧道东延段项目', '2022-11-08', '销售重点', '销售', '入围', NULL, '苏交科集团股份有限公司南京设计中心', '敦力(南京)科技有限公司', NULL, NULL, '招标前', '2025/2/21 11:59:49 范敬
【当前阶段】：改变成   招标前
【当前阶段情况说明】：添加   目前机电分包意向性中标人已确定，但还未进场。

2024/7/20 14:09:31 范敬
【消息】「」项目目前还处于土建阶段，预计2024年底土建结构完成；计划2025年机电开始招标，计划2025年底建成。目前土建总包，一标段：中铁十二局；二标段：中建三局；三标段：中建八局；四标段：中铁上海工程局集团有限公司。
2023/11/1 范敬
「阶段变更」
项目初步设计已完成，按和源品牌设计。
', 'SPJ202211-005', '2025-02-21', 0, NULL, NULL, '2022-11-08 00:00:00', '2025-04-28 00:21:56.940102', 16);
INSERT INTO public.projects VALUES (82, '苏州漕湖商务中心项目', '2022-11-08', '销售重点', '销售', '入围', NULL, NULL, '敦力(南京)科技有限公司', NULL, '尚高科技有限公司', '搁置', '2025/2/21 11:55:16 范敬
【当前阶段】：改变成   搁置
【当前阶段情况说明】：添加   处于暂停状态，业主在走内部流程

2024/6/29 11:06:21 范敬
【消息】「」预计三季度项目会进入启动
2024/6/9 12:38:16 范敬
【提案】「」:  与集成商沟通了项目后续招标清单，根据需求建议采用MA12天线及配置清单。
2023/11/1 范敬
「阶段变更」
1、项目整体为EPC方式，目前集成商已通过业主成为意向中标方。项目整体设计由集成商负责，目前已完成系统整体设计（按和源产品），品牌推荐为和源。
2、目前方案已经过技防办评审，进入编标阶段。
', 'SPJ202211-002', '2025-02-21', 0, NULL, NULL, '2022-11-08 00:00:00', '2025-04-28 00:21:56.941311', 16);
INSERT INTO public.projects VALUES (83, '温州国际博览中心', '2022-11-08', '销售重点', '销售', '入围', NULL, NULL, NULL, NULL, NULL, '搁置', '2025/2/21 10:58:46 范敬
【当前阶段】：改变成   搁置
【当前阶段情况说明】：添加   项目因资金问题，暂时处于停工阶段。

2023/11/1 范敬
「阶段变更」
1、项目已设计完成，目前推荐品牌海能达、科立讯、和源通信。现阶段已配合咨询公司编制预算。甲方具体负责弱电的还没有问到。
2、目前设计院正在根据甲方要求调整智能化整体设计方案。

', 'SPJ202211-006', '2025-02-21', 0, NULL, NULL, '2022-11-08 00:00:00', '2025-04-28 00:21:56.942459', 16);
INSERT INTO public.projects VALUES (84, '兴化天宝皇冠酒店智能化项目', '2025-02-11', '渠道跟进', '渠道', '入围', NULL, NULL, '敦力(南京)科技有限公司', NULL, '苏州中亿丰科技有限公司', '品牌植入', '2025/2/11 10:17:54 范敬
【授权编号】：添加   HY-CPJ202502-006

2025/2/11 10:17:54 花伟
【授权编号】：添加   HY-CPJ202502-006

', 'CPJ202502-006', '2025-02-11', 0, NULL, NULL, '2025-02-11 00:00:00', '2025-04-28 00:21:56.943494', 16);
INSERT INTO public.projects VALUES (85, '白下都市工业园项目', '2025-02-07', '渠道跟进', '经销商', '入围', NULL, NULL, '敦力(南京)科技有限公司', NULL, '朗高科技有限公司', '品牌植入', '2025/2/7 14:01:11 范敬
【系统集成商】：改变成   朗高科技有限公司
【授权编号】：添加   HY-CPJ202501-013
【类型】：添加   渠道跟进

2025/2/7 14:01:11 花伟
【系统集成商】：改变成   朗高科技有限公司
【授权编号】：添加   HY-CPJ202501-013
【类型】：添加   渠道跟进

', 'CPJ202501-013', '2025-02-07', 0, NULL, NULL, '2025-02-07 00:00:00', '2025-04-28 00:21:56.944477', 16);
INSERT INTO public.projects VALUES (86, '天津梅江国际会展中心（改建）', '2024-11-09', '销售重点', '经销商', NULL, NULL, NULL, '北京联航迅达通信技术有限公司', NULL, '中建八局-华北分公司', '发现', '2025/1/12 19:33:01 范敬
【当前阶段情况说明】：添加   原渠道来源填写有误

', 'SPJ202411-008', '2025-01-12', 0, NULL, NULL, '2024-11-09 00:00:00', '2025-04-28 00:21:56.945386', 16);
INSERT INTO public.projects VALUES (87, '深圳乐高乐园度假区项目', '2025-01-07', '销售重点', '销售', '不确定', NULL, NULL, NULL, NULL, NULL, '搁置 ', '2025/1/7 08:52:46 范敬
【授权编号】：改变成   HY-SPJ202211-008
【类型】：添加   销售重点

', 'SPJ202211-008', '2025-01-07', 0, NULL, NULL, '2025-01-07 00:00:00', '2025-04-28 00:21:56.946294', 16);
INSERT INTO public.projects VALUES (88, '芜湖梦溪科创走廊一期项目', '2024-11-09', '渠道跟进', '经销商', '入围', NULL, NULL, '敦力(南京)科技有限公司', NULL, '江苏锐泽思通信技术有限公司', '失败', '2024/12/28 范敬
【阶段变更】招标中->失败

2024/12/7 范敬
【阶段变更】招标前->招标中

2024/12/1 范敬
【阶段变更】品牌植入->招标前

2024/11/9 09:56:49 范敬
【完善价格】 852209
', 'CPJ202411-003', '2024-12-28', 0, NULL, NULL, '2024-11-09 00:00:00', '2025-04-28 00:21:56.947421', 16);
INSERT INTO public.projects VALUES (91, '北京颐缇港二期627地块项目', '2024-08-31', '销售重点', '销售', '不确定', NULL, NULL, '北京联航迅达通信技术有限公司', NULL, '北京国隆信达通信技术有限公司', '品牌植入', '2024/12/9 范敬
【阶段变更】中标->品牌植入

2024/9/7 10:47:41 范敬
【消息】「」目前设计的技术标准设计院及顾问公司参考的和源产品参数，经了解目前业主方没有目前品牌要求；集成商正在找不同品牌厂家询价。
', 'SPJ202408-009', '2024-12-09', 0, NULL, NULL, '2024-08-31 00:00:00', '2025-04-28 00:21:56.950272', 16);
INSERT INTO public.projects VALUES (92, '连云港花果山总部研发中心', '2023-07-19', '渠道跟进', '销售', '入围', NULL, NULL, '敦力(南京)科技有限公司', NULL, '朗高科技有限公司', '招标中', '2024/12/7 范敬
【阶段变更】招标前->招标中

2024/12/7 花伟
【阶段变更】招标前->招标中

2024/7/18 07:45:49 范敬
【消息】「」项目进入招投标准备阶段
2024/7/18 07:45:49 花伟
【消息】「」项目进入招投标准备阶段
2024/7/18 07:45:29 范敬
【阶段变更】品牌植入->招标前
2024/7/18 07:45:29 花伟
【阶段变更】品牌植入->招标前
2023/11/1 范敬
「阶段变更」
前期规划设计标已通过，东大院中标设计。讨论后期平面图、系统图、清单、品牌等合作事宜
2023/11/1 花伟
「阶段变更」
前期规划设计标已通过，东大院中标设计。讨论后期平面图、系统图、清单、品牌等合作事宜
', 'CPJ202307-001', '2024-12-07', 0, NULL, NULL, '2023-07-19 00:00:00', '2025-04-28 00:21:56.951188', 16);
INSERT INTO public.projects VALUES (93, '安吉“两山”未来科技城文化艺术中心项目', '2023-09-05', '渠道跟进', '销售', '入围', NULL, NULL, '敦力(南京)科技有限公司', NULL, '朗高科技有限公司', '品牌植入', '2023/11/1 范敬
「阶段变更」
前期设计，品牌植入
2023/11/1 花伟
「阶段变更」
前期设计，品牌植入
', 'CPJ202309-001', '2024-10-19', 0, NULL, NULL, '2023-09-05 00:00:00', '2025-04-28 00:21:56.95207', 16);
INSERT INTO public.projects VALUES (94, '南通炜赋华邑酒店项目', '2023-06-06', '渠道跟进', '销售', '入围', NULL, NULL, '敦力(南京)科技有限公司', NULL, '南通盛云电子科技有限公司', '招标前', '2024/6/29 11:16:45 范敬
【消息】「」项目预计7月开始招标
【阶段变更】品牌植入->招标前
2023/11/1 范敬
「阶段变更」
1、系统设计、品牌植入，
2、本周与相关人员碰面，目前进入品牌入围阶段，计划24年1月前完成装修方招标工作，智能化包含在装修标段内，目前有13家入围单位；
', 'CPJ202306-001', '2024-10-19', 0, NULL, NULL, '2023-06-06 00:00:00', '2025-04-28 00:21:56.952908', 16);
INSERT INTO public.projects VALUES (95, '南京悦柳酒店', '2022-11-08', '渠道跟进', '销售', '围标', NULL, NULL, '敦力(南京)科技有限公司', NULL, '盛云科技有限公司南京分公司', '招标前', '2024/6/29 11:19:38 范敬
【消息】「」该项目总包单位已进场，智能化系统已进入招标准备阶段。
【阶段变更】品牌植入->招标前
2023/11/1 范敬
「阶段变更」
1、项目由集成商负责前期设计，品牌围标。
2、已进入招标代理机构编制预算中。
3、该项目预计11月会进入招投标阶段。
4、已和郭总所发“中策项目信息”核对。
', 'CPJ202211-002', '2024-10-19', 0, NULL, NULL, '2022-11-08 00:00:00', '2025-04-28 00:21:56.953767', 16);
INSERT INTO public.projects VALUES (96, '常州建科股份大楼', '2023-12-25', '销售重点', '销售', '入围', NULL, '南京长江都市建筑设计院', '敦力(南京)科技有限公司', NULL, NULL, '品牌植入', '2023/11/1 范敬
「阶段变更」
1、配合设计院完成初步设计图纸，
', 'SPJ202312-002', '2024-10-19', 0, NULL, NULL, '2023-12-25 00:00:00', '2025-04-28 00:21:56.95471', 16);
INSERT INTO public.projects VALUES (97, '江阴澄星广场及大厦办公区域智能化项目', '2024-08-09', '渠道跟进', '销售', '入围', NULL, NULL, '敦力(南京)科技有限公司', NULL, '江苏智威信息工程有限公司', '招标前', '2024/8/23 15:08:14 范敬
类型改变为  渠道跟进 
', 'CPJ202408-004', '2024-09-07', 0, NULL, NULL, '2024-08-09 00:00:00', '2025-04-28 00:21:56.955674', 16);
INSERT INTO public.projects VALUES (98, '无锡锡东新城高铁商务区地下车行通道工程', '2023-04-23', '渠道跟进', '销售', '入围', NULL, '中邮建技术有限公司无锡分公司', '敦力(南京)科技有限公司', NULL, '中邮建技术有限公司无锡分公司', '签约', '2024/7/20 14:25:47 范敬
【消息】「」代理商已提交批价申请
2024/6/22 12:20:23 范敬
【消息】「」具体商务谈判中，等待集成商与总包单位合同流程。
2024/6/19 18:03:57 范敬
【提案采纳】「」:  清单确定，进入商务谈判流程
【阶段变更】中标->签约
2024/6/11 10:50:18 范敬
【消息】「」因集成商合同未签，下单延迟到6月
2024/6/11 10:49:37 范敬
【阶段变更】招投标->中标
2023/11/1 范敬
「阶段变更」
1、目前配合前期系统清单配置、品牌推荐及预算
2、清单中有特殊频段产品
3、10月18日已通过集成商与业主见面，目前根据项目实际情况设计方案后期会有变动，详细要求下周业主会给到集成商。
4、目前新技术要求调整已发出，预计本周末或下周初可收到总包方发出的方案；
5、按照集成商最终确定的方案（因业主资金减少取消了部分功能及施工界面调整，主机因统一要求调整为摩托罗拉）；调整完成了清单。
', 'CPJ202304-007', '2024-08-09', 0, NULL, NULL, '2023-04-23 00:00:00', '2025-04-28 00:21:56.956554', 16);
INSERT INTO public.projects VALUES (99, '杭州阿里巴巴总部西溪七期', '2024-07-29', '渠道跟进', '销售', '入围', NULL, '南京长江都市建筑设计院', '敦力(南京)科技有限公司', NULL, NULL, '品牌植入', '2024/7/29 范敬
配合设计院完成初步设计
2024/7/29 花伟
配合设计院完成初步设计
', 'CPJ202407-011', '2024-07-29', 0, NULL, NULL, '2024-07-29 00:00:00', '2025-04-28 00:21:56.957581', 16);
INSERT INTO public.projects VALUES (100, '长春瑯珀凯越甄选酒店', '2023-11-01', '渠道跟进', '销售', '确定', NULL, '吉林省济远建设有限公司', '北京联航迅达通信技术有限公司', NULL, '吉林省济远建设有限公司', '品牌植入', '2024/7/18 08:11:28 范敬
【消息】「」目前没有新进展
2023/11/1 范敬
「阶段变更」
1、配合出清单、图纸；
', 'CPJ202311-001', '2024-07-18', 0, NULL, NULL, '2023-11-01 00:00:00', '2025-04-28 00:21:56.958815', 16);
INSERT INTO public.projects VALUES (101, '芜湖第四人民医院（安定医院）', '2024-07-05', '销售重点', '销售', '入围', NULL, '东南大学建筑设计研究院', NULL, NULL, NULL, '品牌植入', '2024/7/5 范敬
【提案】:  配合设计院在做前期方案规划初设。
', 'SPJ202407-001', '2024-07-18', 0, NULL, NULL, '2024-07-05 00:00:00', '2025-04-28 00:21:56.960006', 16);
INSERT INTO public.projects VALUES (102, '集创北方总部暨显示驱动芯片设计和先进测试基地项目', '2023-05-18', '渠道跟进', '销售', '入围', NULL, NULL, '北京联航迅达通信技术有限公司', NULL, '北京泰豪智能工程有限公司', '招标前', '2024/7/18 07:58:02 范敬
【提案】「」:  正在编标中，预计8月底或9月初进入招标。
【阶段变更】品牌植入->招标前
2023/11/1 范敬
「阶段变更」
配合集成商出方案和配置
', 'CPJ202305-001', '2024-07-18', 0, NULL, NULL, '2023-05-18 00:00:00', '2025-04-28 00:21:56.961017', 16);
INSERT INTO public.projects VALUES (103, '江宁九龙湖国际企业总部园二期项目', '2023-03-09', '渠道跟进', '销售', '入围', NULL, '华东建筑设计研究院有限公司', '敦力(南京)科技有限公司', NULL, NULL, '品牌植入', '2023/11/1 范敬
「阶段变更」
目前处于项目前期规划设计
2023/11/1 花伟
「阶段变更」
目前处于项目前期规划设计
', 'CPJ202303-002', '2024-07-11', 0, NULL, NULL, '2023-03-09 00:00:00', '2025-04-28 00:21:56.961889', 16);
INSERT INTO public.projects VALUES (104, '安徽黄山市徽州体育馆', '2023-09-05', '渠道跟进', '经销商', '入围', NULL, NULL, '敦力(南京)科技有限公司', NULL, NULL, '品牌植入', '2023/11/1 范敬
「阶段变更」
前期设计，品牌植入
2023/11/1 花伟
「阶段变更」
前期设计，品牌植入
', 'CPJ202309-002', '2024-07-11', 0, NULL, NULL, '2023-09-05 00:00:00', '2025-04-28 00:21:56.962886', 16);
INSERT INTO public.projects VALUES (199, '张江创新药基地B03C-02&B03K-03', '2024-01-29', '渠道跟进', '销售', '围标', '上海张江国信安地产有限公司', NULL, '上海福玛通信信息科技有限公司', NULL, '上海派汇网络科技有限公司', '中标', '2025/4/10 13:59:46 杨俊杰
【出货时间预测】：改变成   2025年三季度
【直接用户】：改变成   庄彦「上海张江国信安地产有限公司」
【当前阶段情况说明】：改变成   经沟通了解，集成商派汇与总包仪电有关智能化合同还在签订，目前他们还没进场实施，待进场后也是先启动管线桥架预埋工作，但项目按照用户交付计划在今年底要完成，所以预计今年三季度会启动设备采购

2025/4/10 杨俊杰
「范佳顺」 上海派汇网络科技有限公司  经沟通了解，集成商派汇与总包仪电有关智能化合同还在签订，目前他们还没进场实施，待进场后也是先启动管线桥架预埋工作，但项目按照用户交付计划在今年底要完成，所以预计今年三季度会启动设备采购
2025/3/19 16:30:41 李冬
【出货时间预测】：改变成   上海张江国信安地产有限公司「2025年二季度」
【当前阶段】：改变成   转移
【当前阶段情况说明】：添加   项目转移到其他代理商

2025/2/25 11:05:49 杨俊杰
【直接用户】：改变成   庄彦「上海张江国信安地产有限公司」

2025/2/21 13:09:23 杨俊杰
【分销商】：改变成   上海淳泊
【经销商】：改变成   陈刘祥「上海福玛通信信息科技有限公司」
【直接用户】：改变成   庄彦「上海张江国信安地产有限公司」
【当前阶段情况说明】：改变成   复核项目中标情况。通过渠道与派汇网络负责人范佳顺沟通了解，张江创新药基地分为B03C-02和B03K-03两个地块。他们跟踪的是B03K-03，另一个B03C-02是益邦中标。其中B03K-03实际中标单位为仪电鑫森，现阶段他们在与仪电鑫森洽谈智能化分包商务合同。项目现场实施计划今年3，4月份做管线预埋，无线对讲系统天馈实施最快也要到5月份。现阶段计划复核深化方案，确认实施清单，跟踪渠道推进项目采购进度

2025/2/17 14:42:59 杨俊杰
【直接用户】：改变成   庄彦「上海张江国信安地产有限公司」
【当前阶段情况说明】：添加   该项目分为两个地块，张江创新药基B03K-03中标单位上海仪电，智能化分包负责派汇网络。现阶段福玛在跟进。目前仅了解到项目今年会启动，但具体时间还需要确认。只能询价复核项目实施方案，确认项目采购清单，推进洽谈商务价格

45653 李冬
【阶段变更】招投标->中标

2024/12/27 杨俊杰
【阶段变更】招投标->中标

45371.6763425926 李冬
近期跟进通过渠道了解投标结果
2024/3/20 16:13:56 杨俊杰
近期跟进通过渠道了解投标结果
45342.6328935185 李冬
经销商改变为   上海瀚网智能科技有限公司 用户改变为   上海张江国信安地产有限公司    
配合戴卓莹与孙明显招标设计，与戴卓莹沟通了解甲方直接大总包招标，弱电基本内定益邦，挂靠在大总包下面。益邦贾雪凤询价，提供清单报价
2024/2/20 15:11:22 杨俊杰
经销商改变为   上海瀚网智能科技有限公司 用户改变为   上海张江国信安地产有限公司    
配合戴卓莹与孙明显招标设计，与戴卓莹沟通了解甲方直接大总包招标，弱电基本内定益邦，挂靠在大总包下面。益邦贾雪凤询价，提供清单报价
45342.6287268518 李冬
集成商改变为  上海益邦智能技术股份有限公司    
2024/2/20 15:05:22 杨俊杰
集成商改变为  上海益邦智能技术股份有限公司    
45342.6247800926 李冬
设计方改变为      
2024/2/20 14:59:41 杨俊杰
设计方改变为      
45342.6222337963 李冬
围标状况改变为   围标 分销商改编为   上海瑞康 类型改变为  渠道管理    
2024/2/20 14:56:01 杨俊杰
围标状况改变为   围标 分销商改编为   上海瑞康 类型改变为  渠道管理    
45231 李冬
该项目瀚网报备，经了解集成商上海益邦询价，品牌和源入围
2023/11/1 杨俊杰
该项目瀚网报备，经了解集成商上海益邦询价，品牌和源入围
', 'CPJ202401-011', '2025-04-10', 0, NULL, NULL, '2024-01-29 00:00:00', '2025-04-28 01:00:52.321152', 14);
INSERT INTO public.projects VALUES (105, '南京燕子矶新城医院工程', '2023-01-30', '销售重点', '销售', '入围', NULL, '东南大学建筑设计研究院', '敦力(南京)科技有限公司', NULL, NULL, '招标前', '2024/7/5 10:41:56 范敬
【阶段变更】品牌植入->招标前
2024/7/5 10:32:56 范敬
【提案】「」:  与设计方及预算编制方进行了方案沟通，在清单参数编制中设置了M11馈电型天线参数要求，主机推荐品牌：摩托、海能达、和源；天馈系统品牌：和源、淳泊、瀚网
2023/11/1 范敬
「阶段变更」
施工图图纸深化设计阶段
', 'SPJ202301-001', '2024-07-05', 0, NULL, NULL, '2023-01-30 00:00:00', '2025-04-28 00:21:56.964264', 16);
INSERT INTO public.projects VALUES (106, '阿里江苏总部园区B地块', '2022-11-08', '渠道跟进', '销售', '入围', NULL, '南京长江都市建筑设计院', '敦力(南京)科技有限公司', NULL, NULL, '招标中', '2024/4/25 14:18:11 范敬
「阶段变更」招标中->品牌植入
2024/4/25 14:18:11 花伟
「阶段变更」招标中->品牌植入
2023/11/1 范敬
「阶段变更」
1、项目设计中，目前和源通信产品配合设计。
2、本周拜访了业主在项目上的负责人，目前对于对讲系统的政策主机品牌为摩托罗拉唯一指定，其他不做指定；集成商为2021年选中集成商库中选择；
2023/11/1 花伟
「阶段变更」
1、项目设计中，目前和源通信产品配合设计。
2、本周拜访了业主在项目上的负责人，目前对于对讲系统的政策主机品牌为摩托罗拉唯一指定，其他不做指定；集成商为2021年选中集成商库中选择；
', 'CPJ202211-003', '2024-06-24', 0, NULL, NULL, '2022-11-08 00:00:00', '2025-04-28 00:21:56.965541', 16);
INSERT INTO public.projects VALUES (107, '南通昱景希尔顿酒店', '2023-11-29', '渠道跟进', '销售', '入围', NULL, NULL, '敦力(南京)科技有限公司', NULL, '苏州朗捷通智能科技有限公司', '签约', '2024/6/9 13:09:41 范敬
【阶段变更】中标->签约
2024/5/29 14:20:28 范敬
【阶段变更】签约->中标
2024/5/28 14:33:34 范敬
【提案采纳】「」:  已签约
【阶段变更】中标->签约
2023/11/1 范敬
「阶段变更」
1、该项目目前集成商苏州朗捷通智能科技有限公司中标，据了解该项目只对中继台及对讲机有品牌要求（摩托罗拉、建伍），天馈系统未有要求；目前正在通过关系找到业主，看有无可能进行品牌调整修改；
2、目前有较多供应商正在报价，等待业主选择。
3、正在进行第二轮报价。
', 'CPJ202311-006', '2024-06-09', 0, NULL, NULL, '2023-11-29 00:00:00', '2025-04-28 00:21:56.966635', 16);
INSERT INTO public.projects VALUES (108, '阿里江苏总部园区C地块项目', '2023-03-27', '渠道跟进', '销售', '入围', NULL, '南京长江都市建筑设计院', '敦力(南京)科技有限公司', NULL, NULL, '品牌植入', '2023/11/1 范敬
「阶段变更」
1、配合设计院初步设计，品牌(技术)植入
2、本周拜访了业主在项目上的负责人，目前对于对讲系统的政策主机品牌为摩托罗拉唯一指定，其他不做指定；集成商为2021年选中集成商库中选择；
2023/11/1 花伟
「阶段变更」
1、配合设计院初步设计，品牌(技术)植入
2、本周拜访了业主在项目上的负责人，目前对于对讲系统的政策主机品牌为摩托罗拉唯一指定，其他不做指定；集成商为2021年选中集成商库中选择；
', 'CPJ202303-004', '2024-05-04', 0, NULL, NULL, '2023-03-27 00:00:00', '2025-04-28 00:21:56.967702', 16);
INSERT INTO public.projects VALUES (109, '江苏省中医院牛首山分院一期项目智能化系统工程', '2022-11-08', '渠道跟进', '销售', '入围', NULL, NULL, '敦力(南京)科技有限公司', NULL, '朗高科技有限公司', '签约', '2024/4/30 19:59:02 范敬
[阶段变更] ->签约
2024/4/25 14:06:02 范敬
「阶段变更」签约->中标
2023/11/1 范敬
「阶段变更」
1、项目整体为EPC方式，目前集成商已中标进场施工。项目现阶段处于管线预埋阶段；品牌已入围。项目后期会交于代理商跟踪。
2、经销商需要低于41%折的价格，并且账期很长；信道机对讲机其他院区是用摩托的，所以可能性不大；总包给的工期为项目12份结束。
3、因资金问题采购时间延迟，预计2024年2月，目前集成商给出的采购价约为面价的40%折，账期无预付，到货后6个月支付货款；如果可以的话预计2024年1月可以批价；
4、因集成商调整，对系统清单做了调整；
', 'CPJ202211-004', '2024-04-30', 0, NULL, NULL, '2022-11-08 00:00:00', '2025-04-28 00:21:56.968657', 16);
INSERT INTO public.projects VALUES (110, '苏州工业园区20200118地块智能化项目', '2023-01-04', '渠道跟进', '销售', '入围', NULL, NULL, '苏州邦耀电子科技有限公司', NULL, NULL, '签约', '2024/4/21 19:59:17 范敬
[阶段变更] ->签约
2024/4/12 15:49:24 范敬
「阶段变更」
2023/11/1 范敬
「阶段变更」
1、招投标询价阶段
2、下周一确认清单和预测时间
3、下周集成商开始询价，代理商需要公司渠道予以关注此时，做好价格保护。
4、代理商目前正在与集成商商务谈判及合同流程，但需要协调先行提供部分产品（天线、功分耦合器）；
5、目前已协调分销商先行借货40套天线及功分耦合器；
6、苏州代理商（邦耀）提供最终深化清单；
7、批价沟通中；
8、代理商提交相关资料，对项目申请特价；
', 'CPJ202301-002', '2024-04-21', 0, NULL, NULL, '2023-01-04 00:00:00', '2025-04-28 00:21:56.969936', 16);
INSERT INTO public.projects VALUES (111, '青岛市山东路立交地下空间', '2022-11-08', '渠道跟进', '销售', '入围', NULL, NULL, NULL, NULL, NULL, '品牌植入', '2023/11/1 范敬
「阶段变更」
配合设计院完成设计，按和源品牌推荐。
', 'CPJ202211-005', '2024-03-01', 0, NULL, NULL, '2022-11-08 00:00:00', '2025-04-28 00:21:56.971024', 16);
INSERT INTO public.projects VALUES (112, '山东青岛创意文化综合体建设项目', '2022-11-08', '渠道跟进', '销售', '入围', NULL, NULL, NULL, NULL, '上海宝冶集团有限公司', '品牌植入', '2023/11/1 范敬
「阶段变更」
项目为EPC项目，目前与中标方宝冶项目部安装经理联系沟通此项目。
', 'CPJ202211-006', '2024-03-01', 0, NULL, NULL, '2022-11-08 00:00:00', '2025-04-28 00:21:56.972096', 16);
INSERT INTO public.projects VALUES (113, '浙中新能源汽车城市广场', '2023-04-18', '渠道跟进', '销售', '入围', NULL, NULL, NULL, NULL, NULL, '品牌植入', '2023/11/1 范敬
「阶段变更」
配合设计院进行项目初期设计
', 'CPJ202304-004', '2024-03-01', 0, NULL, NULL, '2023-04-18 00:00:00', '2025-04-28 00:21:56.973232', 16);
INSERT INTO public.projects VALUES (114, '上海打浦桥社区文化活动中心', '2023-03-30', '渠道跟进', '代理商', '入围', NULL, NULL, '苏州邦耀电子', NULL, NULL, '品牌植入', '2023/11/1 范敬
「阶段变更」
配合集成商进行方案设计及品牌植入
', 'CPJ202303-006', '2024-03-01', 0, NULL, NULL, '2023-03-30 00:00:00', '2025-04-28 00:21:56.974343', 16);
INSERT INTO public.projects VALUES (115, '东台市金融广场', '2023-04-19', '渠道跟进', '销售', '入围', NULL, NULL, '上海福玛通信信息科技有限公司', NULL, NULL, '品牌植入', '2023/11/1 范敬
「阶段变更」
1、配合项目系统设计、预算及品牌
2、该项目目前已和分销商沟通，有淳泊进行配合跟踪；
45231 邹飞
「阶段变更」
1、配合项目系统设计、预算及品牌
2、该项目目前已和分销商沟通，有淳泊进行配合跟踪；
', 'CPJ202304-006', '2024-03-01', 0, NULL, NULL, '2023-04-19 00:00:00', '2025-04-28 00:21:56.975562', 16);
INSERT INTO public.projects VALUES (116, '江苏省妇幼保健院总部项目', '2022-11-09', '渠道跟进', '销售', '不确定', NULL, NULL, '敦力(南京)科技有限公司', NULL, NULL, '品牌植入', '2023/11/1 范敬
「阶段变更」
1、EPC项目，目前大总包已招标完毕。
2、目前北京院在进行智能化设计。
2023/11/1 花伟
「阶段变更」
1、EPC项目，目前大总包已招标完毕。
2、目前北京院在进行智能化设计。
', 'CPJ202211-007', '2024-02-29', 0, NULL, NULL, '2022-11-09 00:00:00', '2025-04-28 00:21:56.976419', 16);
INSERT INTO public.projects VALUES (117, '江苏太仓市东亭路南延新建工程（朝阳路-桴亭路）', '2025-04-21', '销售重点', '销售', '入围', NULL, '杭州北控科技有限公司', '浙江航博智能工程有限公司', NULL, NULL, '品牌植入', '2025/4/25 18:37:37 李华伟
【授权编号】：改变成   HY-SPJ202504-002
【类型】：改变成   销售重点

2025/4/21 14:32:59 李华伟
【授权编号】：添加   HY-CPJ202504-023
【类型】：添加   渠道跟进

2025/4/14 15:49:06 李华伟
【设计院及顾问】：添加   杭州北控科技有限公司

', 'SPJ202504-002', '2025-04-25', 0, NULL, NULL, '2025-04-21 00:00:00', '2025-04-28 00:59:09.656229', 15);
INSERT INTO public.projects VALUES (118, '杭州博览会议中心二期', '2023-12-01', '销售重点', '销售', '入围', NULL, '华东建筑设计研究院有限公司', '浙江航博智能工程有限公司', NULL, '浙江微风智能科技有限公司', '中标', '2025/4/25 18:29:00 李华伟
【出货时间预测】：改变成   2025年5月20

2025/4/25 李华伟
「田经理」 浙江微风智能科技有限公司  预计5月签约合同，推动现场采购下单，博物馆有部分天线取消，价格层面一直在谈判让我们给与支持，虽然品牌用了我们但是价格相差中标成本价格有15个点的区间。
2025/3/24 10:59:04 李华伟
【出货时间预测】：改变成   2025年二季度

2025/3/24 09:55:41 李华伟
【完善价格】 1025244
2025/3/21 16:01:31 李华伟
【完善价格】 978924
2025/3/21 15:46:05 李华伟
【完善价格】 892340
2025/2/17 14:38:29 李华伟
【当前阶段情况说明】：添加   目前在做桥架，样板层天线代理商提供给现场确认，预计3-4月份进行穿线，近期会安排拜访客户采购确认合同事宜。

2025/1/17 11:11:22 李华伟
【出货时间预测】：添加   2025年一季度

2024/8/26 10:51:23 李华伟
【拜访】「」:  本周同李波拜访微风，实际科大讯飞分包微风来做，分包管理费比较高，后面会有深化和价格问题。然后安排代理商航博先把采购层面关系做扎实。预计年后三四月份穿线。
2024/8/16 14:25:06 李华伟
【阶段变更】招标中->中标

跟进记录 李华伟
【阶段变更】品牌植入->招标中
2024/4/29 15:31:10 李华伟
【一致行动人】「」:  通过代理商李波认识介绍集成商采购和技术，一同对接分工。
2024/3/15 13:58:51 李华伟
「拜访」  :  目前品牌华东院给到微风，微风这边已经接洽上，围标品牌他们没有意见，表示价格不能虚高不然他们反而被动，绑定关键人合作。下周关注品牌情况。
2024/2/21 12:45:50 李华伟
集成商改变为  浙江微风智能科技有限公司    
2024/2/21 12:45:34 李华伟
设计方改变为  华东建筑设计研究院有限公司 类型改变为  销售重点    
2023/11/1 李华伟
前期设计配合目前华东院出图，当地集成商微风智能参与设计。
', 'SPJ202312-001', '2025-04-25', 0, NULL, NULL, '2023-12-01 00:00:00', '2025-04-28 00:59:09.662529', 15);
INSERT INTO public.projects VALUES (119, '静安假日酒店', '2024-05-17', '渠道跟进', '经销商', '围标', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '上海奂源工程设备有限公司', '中标', '2025/4/25 18:28:07 李华伟
【出货时间预测】：改变成   2025-05-23

2025/4/6 09:36:30 李华伟
【完善价格】 190200
2025/3/24 10:00:35 李华伟
【出货时间预测】：改变成   2025年二季度

2025/2/17 14:39:39 李华伟
【当前阶段情况说明】：添加   代理商反馈合同预计2月底-3月签约，现场还没提起采购流程，价格基本已经初步确认。

45674.4659837963 李冬
【出货时间预测】：添加   2025年一季度

2025/1/17 11:11:01 李华伟
【出货时间预测】：添加   2025年一季度

45596.7189236111 李冬
【完善价格】 202700
2024/10/31 17:15:15 李华伟
【完善价格】 202700
45443.6553935185 李冬
【阶段变更】招标前->中标
2024/5/31 15:43:46 李华伟
【阶段变更】招标前->中标
45429 李冬
【提案】: 瀚网配合集成商设计，植入围标品牌。预计即将招标，集成商操作此项目，几率较大。
2024/5/17 李华伟
【提案】: 瀚网配合集成商设计，植入围标品牌。预计即将招标，集成商操作此项目，几率较大。
', 'CPJ202405-007', '2025-04-25', 0, NULL, NULL, '2024-05-17 00:00:00', '2025-04-28 00:59:09.665095', 15);
INSERT INTO public.projects VALUES (120, '海宁经开智创园', '2025-02-17', '渠道跟进', '渠道', '入围', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '华维星电技术有限公司', '签约', '2025/4/21 15:06:19 李华伟
[阶段变更] ->签约
2025/3/24 10:00:14 李华伟
【出货时间预测】：改变成   2025年二季度

2025/3/10 14:49:30 李华伟
【出货时间预测】：添加   2025年一季度
【当前阶段】：改变成   中标

2025/3/10 10:00:05 李华伟
【完善价格】 213627
2025/2/25 16:29:25 李冬
【授权编号】：添加   HY-CPJ202502-010
【类型】：添加   渠道跟进

2025/2/17 13:30:15 李华伟
【完善价格】 151017
2025/2/17 12:54:10 李华伟
【当前阶段】：添加   招标中
【授权编号】：添加   HY-CPJ202502-010
【类型】：添加   渠道跟进

', 'CPJ202502-010', '2025-04-21', 0, NULL, NULL, '2025-02-17 00:00:00', '2025-04-28 00:59:09.66767', 15);
INSERT INTO public.projects VALUES (121, '三亚太古里（国际免税城三期）', '2025-04-14', '渠道跟进', '渠道', '围标', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '上海文讯电子有限公司', '品牌植入', '2025/4/21 14:34:51 李华伟
【完善价格】 153238
2025/4/14 15:43:15 李华伟
【授权编号】：添加   HY-CPJ202412-006

2025/4/11 14:07:20 李华伟
提交报备
2025/4/11 14:06:46 李华伟
【当前阶段】：添加   品牌植入
【系统集成商】：添加   上海文讯电子有限公司
【当前阶段情况说明】：添加   代理商瑞康报备配合文讯植入和源天馈品牌围标，预计下半年招标。

2025/2/25 16:16:15 李冬
【授权编号】：添加   HY-CPJ202412-006
【类型】：添加   渠道跟进

', 'CPJ202412-006', '2025-04-21', 0, NULL, NULL, '2025-04-14 00:00:00', '2025-04-28 00:59:09.669635', 15);
INSERT INTO public.projects VALUES (122, '金华双龙洞凯悦酒店', '2025-04-21', '渠道跟进', '渠道', '入围', NULL, NULL, '浙江航博智能工程有限公司', NULL, NULL, '品牌植入', '2025/4/21 14:32:29 李华伟
【授权编号】：添加   HY-CPJ202504-022
【类型】：添加   渠道跟进

2025/4/18 14:07:15 李博
【授权编号】：添加   HY-CPJ202504-022

2025/4/18 13:24:25 李华伟
【当前阶段】：添加   品牌植入

2025/4/18 13:12:44 李华伟
【完善价格】 267910
', 'CPJ202504-022', '2025-04-21', 0, NULL, NULL, '2025-04-21 00:00:00', '2025-04-28 00:59:09.671127', 15);
INSERT INTO public.projects VALUES (123, '崇明长兴38-07地块商业项目', '2025-04-14', '渠道跟进', '销售', '入围', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '上海双桥信息有限公司', '招标中', '2025/4/14 15:44:08 李华伟
【授权编号】：添加   HY-CPJ202504-011

2025/4/11 14:07:55 李华伟
提交报备
2025/4/11 14:07:41 李华伟
提交报备
2025/4/11 13:48:10 李华伟
【完善价格】 121378
2025/4/11 13:46:48 李华伟
【完善价格】 687496
2025/4/11 李华伟
「」 上海双桥信息有限公司  配合客户设计植入和源对讲机全品牌，目前已经招标，代理商配合书柏、早田、铭洪投标。
', 'CPJ202504-011', '2025-04-14', 0, NULL, NULL, '2025-04-14 00:00:00', '2025-04-28 00:59:09.672978', 15);
INSERT INTO public.projects VALUES (124, '张家浜楔形绿地C1B-02地块办工', '2025-04-14', '渠道跟进', '渠道', '入围', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '上海壹杰信息技术有限公司', '招标中', '2025/4/14 15:43:39 李华伟
【授权编号】：添加   HY-CPJ202504-012

2025/4/11 14:07:33 李华伟
提交报备
2025/4/11 13:49:04 李华伟
【完善价格】 179289
', 'CPJ202504-012', '2025-04-14', 0, NULL, NULL, '2025-04-14 00:00:00', '2025-04-28 00:59:09.674377', 15);
INSERT INTO public.projects VALUES (125, '厦门士兰微8英寸SiC功率器件芯片制造生产线', '2025-03-10', '销售重点', '渠道', '不确定', '厦门士兰集科微电子有限公司', NULL, '上海瀚网智能科技有限公司', NULL, NULL, '发现', '2025/4/14 14:20:02 李华伟
【授权编号】：改变成   HY-SPJ202503-005
【类型】：改变成   销售重点

2025/3/10 09:51:17 李华伟
【授权编号】：添加   HY-CPJ202503-005
【类型】：添加   渠道跟进

2025/3/3 10:54:02 李华伟
【当前阶段】：添加   发现

', 'SPJ202503-005', '2025-04-14', 0, NULL, NULL, '2025-03-10 00:00:00', '2025-04-28 00:59:09.675746', 15);
INSERT INTO public.projects VALUES (137, '临港西岛金融中心商办部分', '2024-11-18', '渠道跟进', '经销商', '入围', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '上海源和智能科技股份有限公司', '转移', '2025/2/16 13:02:32 李华伟
【当前阶段】：改变成   转移

2025/2/16 13:02:13 李华伟
【当前阶段情况说明】：改变成   中标后转移销售杨俊杰已经批价

2025/1/6 11:34:34 李华伟
【当前阶段情况说明】：添加   销售杨俊杰已经批价

2024/11/25 李华伟
【困难解决】

2024/11/25 李华伟
【出现困难】重复建立了项目，此机会做失效。

2024/11/18 15:53:20 李华伟
【完善价格】 340823
', 'CPJ202411-008', '2025-02-16', 0, NULL, NULL, '2024-11-18 00:00:00', '2025-04-28 00:59:09.690967', 15);
INSERT INTO public.projects VALUES (292, '漳州军用机场', '2024-10-08', '销售重点', '系统集成商', '不确定', NULL, NULL, NULL, NULL, '厦门纵横集团科技股份有限公司', '发现', NULL, 'SPJ202410-002', '2024-10-08', 0, NULL, NULL, '2024-10-08 00:00:00', '2025-04-28 01:02:05.01968', 17);
INSERT INTO public.projects VALUES (126, '集成电路设计产业园3C-10地块', '2024-05-11', '渠道跟进', '经销商', '入围', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '同方股份有限公司-上海光大会展分公司', '中标', '2025/3/24 10:00:55 李华伟
【出货时间预测】：改变成   2025年四季度

2025/2/17 14:37:16 李华伟
【当前阶段情况说明】：添加   据代理商反馈，现场进度预计在8月份左右进场穿线，目前在做桥架。品牌资料报审已经完成。安排代理商7月份左右跟进客户合同谈判确认。

45674.4749884259 李冬
【完善价格】 348300
2025/1/17 11:23:59 李华伟
【完善价格】 348300
45674.4653587963 李冬
【完善价格】 312942
2025/1/17 11:10:07 李华伟
【完善价格】 312942
45429.5617824074 李冬
【阶段变更】招标中->中标
2024/5/17 13:28:58 李华伟
【阶段变更】招标中->中标
45423 李冬
【拜访】:  代理商配合客户投标，品牌入围。
2024/5/11 李华伟
【拜访】:  代理商配合客户投标，品牌入围。
', 'CPJ202405-004', '2025-03-24', 0, NULL, NULL, '2024-05-11 00:00:00', '2025-04-28 00:59:09.676952', 15);
INSERT INTO public.projects VALUES (127, '金桥南区WH4A-1金谷通用厂房项目实验室专业分包工程7#8#楼', '2025-03-17', '渠道跟进', '渠道', '入围', NULL, NULL, '上海福玛通信信息科技有限公司', NULL, '中电科数字技术股份有限公司', '招标中', '2025/3/17 15:34:35 李华伟
【当前阶段】：添加   招标中
【授权编号】：添加   HY-CPJ202503-005
【类型】：添加   渠道跟进

', 'CPJ202503-005', '2025-03-17', 0, NULL, NULL, '2025-03-17 00:00:00', '2025-04-28 00:59:09.678132', 15);
INSERT INTO public.projects VALUES (128, '嘉兴圆通货运机场', '2025-03-10', '渠道跟进', '销售', '入围', NULL, '浙江省建筑设计院', '浙江航博智能工程有限公司', NULL, NULL, '发现', '2025/3/10 09:52:29 李华伟
【授权编号】：改变成   HY-CPJ202404-007
【类型】：改变成   渠道跟进

', 'CPJ202404-007', '2025-03-10', 0, NULL, NULL, '2025-03-10 00:00:00', '2025-04-28 00:59:09.679273', 15);
INSERT INTO public.projects VALUES (129, '嘉兴圆通货运机场', '2024-04-26', '销售重点', '销售', '入围', NULL, '浙江省建筑设计院', '浙江航博智能工程有限公司', NULL, NULL, '发现', '2025/3/3 13:51:04 李华伟
【完善价格】 31608
2024/4/26 李华伟
「拜访」:  接触到设计院和业主，配合设计方案，预计下半年招标，业主预算不多，按照3套系统建设，后续预算出来跟业主在确认是否合理。
', 'SPJ202404-002', '2025-03-03', 0, NULL, NULL, '2024-04-26 00:00:00', '2025-04-28 00:59:09.680508', 15);
INSERT INTO public.projects VALUES (130, '静安工人文化宫', '2025-01-06', '渠道跟进', '经销商', '入围', NULL, '华东建筑设计研究院有限公司', '上海瀚网智能科技有限公司', NULL, '同方股份有限公司-上海光大会展分公司', '中标', '2025/3/3 13:32:51 李华伟
【出货时间预测】：改变成   2025年三季度

2025/2/21 16:09:02 杨俊杰
【当前阶段】：改变成   转移

2025/2/21 16:08:51 杨俊杰
【当前阶段】：改变成   中标

2025/2/21 16:07:43 杨俊杰
【当前阶段】：改变成   转移
【当前阶段情况说明】：添加   该项目销售负责人改为李华伟，有李华伟配合渠道跟进

45699.5797685185 李冬
【完善价格】 46322
2025/2/11 13:54:52 李华伟
【完善价格】 46322
45674.4665509259 李冬
【出货时间预测】：添加   2025年一季度

2025/1/17 11:11:50 李华伟
【出货时间预测】：添加   2025年一季度

45663.5790509259 李冬
【授权编号】：改变成   HY-CPJ202401-007
【类型】：添加   渠道跟进

2025/1/6 13:53:50 李华伟
【授权编号】：改变成   HY-CPJ202401-007
【类型】：添加   渠道跟进

45597 李冬
【阶段变更】招标中->中标

2024/11/1 杨俊杰
【阶段变更】招标中->中标

45416.5425694444 李冬
【阶段变更】招标前->招标中
2024/5/4 13:01:18 杨俊杰
【阶段变更】招标前->招标中
45377.7035648148 李冬
该项目与华东院陈允强沟通了解项目计划3月底4月初挂网招标，弱电智能化基本锁定九谷，安排渠道跟进集成商投标。
2024/3/26 16:53:08 杨俊杰
该项目与华东院陈允强沟通了解项目计划3月底4月初挂网招标，弱电智能化基本锁定九谷，安排渠道跟进集成商投标。
45362.4933217593 李冬
该项目华东院负责智能化设计，但业主引荐九谷参与配其中，技术规格书和品牌直接由九谷负责，渠道配合
2024/3/11 11:50:23 杨俊杰
该项目华东院负责智能化设计，但业主引荐九谷参与配其中，技术规格书和品牌直接由九谷负责，渠道配合
45362.4920717593 李冬
「阶段变更」
2024/3/11 11:48:35 杨俊杰
「阶段变更」
45231 李冬
该项目华东院陈允强告知他们负责智能化设计，但业主引荐了上海九谷配套他们做招标文件。计划跟进了解项目设计进度，植入招标品牌，了解招标时间
2023/11/1 杨俊杰
该项目华东院陈允强告知他们负责智能化设计，但业主引荐了上海九谷配套他们做招标文件。计划跟进了解项目设计进度，植入招标品牌，了解招标时间
', 'CPJ202401-007', '2025-03-03', 0, NULL, NULL, '2025-01-06 00:00:00', '2025-04-28 00:59:09.681972', 15);
INSERT INTO public.projects VALUES (131, '无锡锡山映月湖生态数字文体产业中心', '2025-02-24', '销售重点', '经销商', '入围', NULL, '悉地国际设计顾问(深圳)有限公司上海分公司', '上海瀚网智能科技有限公司', NULL, NULL, '品牌植入', '2025/2/24 13:28:51 李华伟
【授权编号】：改变成   HY-SPJ202405-002
【类型】：改变成   销售重点

2025/2/17 22:08:37 周裔锦
【完善价格】 527349
2025/2/13 10:20:22 周裔锦
【授权编号】：添加   HY-SPJ202405-002
【类型】：添加   销售重点

2025/1/11 15:55:33 杨俊杰
【授权编号】：添加   HY-SPJ202405-002

', 'SPJ202405-002', '2025-02-24', 0, NULL, NULL, '2025-02-24 00:00:00', '2025-04-28 00:59:09.683677', 15);
INSERT INTO public.projects VALUES (132, '湖州西凤漾智创湾', '2025-02-24', '销售重点', '销售', '入围', NULL, '浙江省建筑设计院', '浙江航博智能工程有限公司', NULL, NULL, '品牌植入', '2025/2/24 13:27:59 李华伟
【授权编号】：改变成   HY-SPJ-202404-007
【类型】：改变成   销售重点

', 'SPJ-202404-007', '2025-02-24', 0, NULL, NULL, '2025-02-24 00:00:00', '2025-04-28 00:59:09.685217', 15);
INSERT INTO public.projects VALUES (133, '曼氏（中国）香精香料厂房', '2023-02-27', '渠道跟进', '销售', '入围', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '上海信业智能科技股份有限公司', '失败', '2025/2/17 16:06:05 李华伟
【当前阶段】：改变成   失败

2025/1/11 14:35:52 李华伟
【当前阶段情况说明】：添加   跟进的代理商反馈客户最终没有谈拢改造项目，甲方找了其他分包单位。

2024/12/30 李华伟
【阶段变更】品牌植入->搁置
类型改变为渠道跟进 
2024/2/21 13:06:55 李华伟
分销商改编为   上海瑞康 经销商改变为   上海瀚网智能科技有限公司 类型改变为  渠道管理    
2023/11/1 李华伟
项目改造设计，安排公司技术对接设计和代理商配合。
', 'CPJ202302-003', '2025-02-17', 0, NULL, NULL, '2023-02-27 00:00:00', '2025-04-28 00:59:09.686397', 15);
INSERT INTO public.projects VALUES (134, '前滩210203地块（商业）', '2022-11-25', '渠道跟进', '销售', '入围', NULL, '上海凯通实业有限公司', '上海淳泊信息科技有限公司', NULL, '上海凯通实业有限公司', '中标', '2025/2/17 16:04:59 李华伟
【完善价格】 225000
2024/2/21 13:06:34 李华伟
分销商改编为   上海淳泊  类型改变为  渠道跟进     
45343.5462268519 邹飞
分销商改编为   上海淳泊  类型改变为  渠道跟进     
2023/11/1 李华伟
1、品牌入围，配合凯通电信行余投标。
2、目前凯通老板徐总反馈系统业主指定了原来的地块品牌亦朗。淳泊还在沟通看是否有机会。
45231 邹飞
1、品牌入围，配合凯通电信行余投标。
2、目前凯通老板徐总反馈系统业主指定了原来的地块品牌亦朗。淳泊还在沟通看是否有机会。
', 'CPJ202211-015', '2025-02-17', 0, NULL, NULL, '2022-11-25 00:00:00', '2025-04-28 00:59:09.687563', 15);
INSERT INTO public.projects VALUES (135, '上海市皮肤病医院科研综合楼', '2024-03-15', '渠道跟进', '销售', '入围', NULL, NULL, '上海福玛通信信息科技有限公司', NULL, '上海行余信息技术有限公司', '品牌植入', '2025/2/17 16:02:05 李华伟
【完善价格】 165569
2024/3/15 15:16:19 李华伟
「阶段变更」
「提案」  :  配合集成商设计方案和品牌推荐，目前是按照我们的品牌来植入，后续复核确认。
45366.6363310185 邹飞
「阶段变更」
「提案」  :  配合集成商设计方案和品牌推荐，目前是按照我们的品牌来植入，后续复核确认。
2024/3/15 李华伟
「拜访」  :  
45366 邹飞
「拜访」  :  
', 'CPJ202403-005', '2025-02-17', 0, NULL, NULL, '2024-03-15 00:00:00', '2025-04-28 00:59:09.688676', 15);
INSERT INTO public.projects VALUES (136, '董家渡18-01地块', '2024-07-26', '渠道跟进', '经销商', '入围', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '上海东元信息科技发展有限公司', '招标中', '2025/2/17 16:00:08 李华伟
【完善价格】 72982
', 'CPJ202407-010', '2025-02-17', 0, NULL, NULL, '2024-07-26 00:00:00', '2025-04-28 00:59:09.689836', 15);
INSERT INTO public.projects VALUES (153, '哔哩哔哩上海总部大楼', '2024-09-14', '销售重点', '销售', '入围', NULL, '思迈建筑咨询(上海)有限公司', NULL, NULL, NULL, '品牌植入', '2024/9/18 11:43:42 李华伟
【完善价格】 421627
', 'SPJ202409-008', '2024-09-24', 0, NULL, NULL, '2024-09-14 00:00:00', '2025-04-28 00:59:09.707412', 15);
INSERT INTO public.projects VALUES (138, '三林楔形绿地39号、40号、41号、42号、43号、44 号地块', '2025-01-17', '渠道跟进', '经销商', '入围', NULL, NULL, '上海福玛通信信息科技有限公司', NULL, '上海行余信息技术有限公司', '招标中', '2025/1/17 11:49:46 李华伟
【完善价格】 207824
45674.4928935185 邹飞
【完善价格】 207824
2025/1/17 11:46:41 李华伟
【完善价格】 197182
45674.4907523148 邹飞
【完善价格】 197182
2025/1/17 11:20:19 李华伟
【授权编号】：添加   HY-CPJ202501-10
【类型】：添加   渠道跟进

45674.4724421296 邹飞
【授权编号】：添加   HY-CPJ202501-10
【类型】：添加   渠道跟进

', 'CPJ202501-10', '2025-01-17', 0, NULL, NULL, '2025-01-17 00:00:00', '2025-04-28 00:59:09.692065', 15);
INSERT INTO public.projects VALUES (139, '洋泾西区EO8-4、E10-2、E12-1地块', '2024-09-29', '渠道跟进', '经销商', '入围', NULL, 'AECOM', '上海福玛通信信息科技有限公司', NULL, '上海行余信息技术有限公司', '中标', '2025/1/17 11:16:28 李华伟
【出货时间预测】：改变成   2025年三季度

45674.4697685185 邹飞
【出货时间预测】：改变成   2025年三季度

2024/10/10 李华伟
【阶段变更】招标中->中标

45575 邹飞
【阶段变更】招标中->中标

2024/10/10 13:56:39 李华伟
【完善价格】 238818
45575.5810069444 邹飞
【完善价格】 238818
2024/10/10 13:56:23 李华伟
【完善价格】 272898
45575.5808217593 邹飞
【完善价格】 272898
', 'CPJ202409-014', '2025-01-17', 0, NULL, NULL, '2024-09-29 00:00:00', '2025-04-28 00:59:09.693103', 15);
INSERT INTO public.projects VALUES (140, '上海曙光医院肝病中心', '2022-12-27', '渠道跟进', '销售', '围标', NULL, '悉地国际设计顾问(深圳)有限公司上海分公司', '上海瀚网智能科技有限公司', NULL, NULL, '失败', '2024/12/30 李华伟
【出现困难】系统取消
类型改变为渠道跟进 
2024/2/21 13:01:55 李华伟
类型改变为  渠道跟进     
2023/11/1 李华伟
项目配合设计，植入和源设备，预计年后招标。
', 'CPJ202212-003', '2024-12-30', 0, NULL, NULL, '2022-12-27 00:00:00', '2025-04-28 00:59:09.69415', 15);
INSERT INTO public.projects VALUES (141, '深圳蛇口颐养康复医疗中心', '2024-06-14', '渠道跟进', '经销商', '入围', NULL, NULL, '浙江航博智能工程有限公司', NULL, '浙大网新系统工程有限公司', '失败', '2024/12/30 李华伟
【阶段变更】招标中->失败

2024/6/14 李华伟
【提案】:  航博配合浙大网新投标，品牌入围。
', 'CPJ202406-005', '2024-12-30', 0, NULL, NULL, '2024-06-14 00:00:00', '2025-04-28 00:59:09.695178', 15);
INSERT INTO public.projects VALUES (142, '市北高新技术服务业园区N070501单元21-02地块商办', '2022-12-05', '渠道跟进', '经销商', '入围', NULL, NULL, '上海瀚网智能科技有限公司', NULL, NULL, '失败', '2024/12/30 李华伟
【阶段变更】招标中->失败
类型改变为渠道跟进 
2024/5/13 10:22:42 李华伟
【阶段变更】品牌植入->招标中
2024/3/15 14:30:35 李华伟
「拜访」  :
2024/2/21 13:01:37 李华伟
类型改变为  渠道跟进     
2023/11/1 李华伟
前期扩粗阶段，项目酒店办公各一套系统
', 'CPJ202212-001', '2024-12-30', 0, NULL, NULL, '2022-12-05 00:00:00', '2025-04-28 00:59:09.696197', 15);
INSERT INTO public.projects VALUES (143, '上海市第一人民医院南部院区二期', '2024-03-21', '渠道跟进', '经销商', '入围', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '上海天跃科技股份有限公司', '失败', '2024/12/30 李华伟
【阶段变更】品牌植入->失败
类型改变为渠道跟进 
2024/3/21 12:11:45 李华伟
「提案」  :  瀚网配合集成商设计方案植入，目前品牌推荐过去，后续确认品牌是否敲定。
2024/3/21 12:07:24 李华伟
「阶段变更」
', 'CPJ202403-007', '2024-12-30', 0, NULL, NULL, '2024-03-21 00:00:00', '2025-04-28 00:59:09.697209', 15);
INSERT INTO public.projects VALUES (144, '嘉兴诺德智联中心', '2024-06-07', '渠道跟进', '经销商', '入围', NULL, '浙江省建筑设计院', '浙江航博智能工程有限公司', NULL, '浙江东冠信息技术有限公司', '失败', '2024/12/30 李华伟
【阶段变更】招标前->失败

', 'CPJ202406-002', '2024-12-30', 0, NULL, NULL, '2024-06-07 00:00:00', '2025-04-28 00:59:09.698207', 15);
INSERT INTO public.projects VALUES (145, '浦东机场假日酒店', '2023-10-23', '渠道跟进', '销售', '入围', NULL, '上海德恳设计咨询顾问有限公司', '上海瀚网智能科技有限公司', NULL, '上海信业智能科技股份有限公司', '失败', '2024/12/16 李华伟
【出现困难】中标方信业退出，由于资金全垫资，业主找了南京一家公司信息打听不到。

2024/2/21 12:50:48 李华伟
围标状况改变为   入围 设计方改变为  上海德恳设计咨询顾问有限公司 分销商改编为   上海瑞康 经销商改变为   上海瀚网智能科技有限公司 类型改变为  渠道管理 集成商改变为  上海信业智能科技股份有限公司    
2023/11/1 李华伟
目前品牌配合植入和源、中兴、海能达。预计23年底左右招标。
', 'CPJ202310-003', '2024-12-16', 0, NULL, NULL, '2023-10-23 00:00:00', '2025-04-28 00:59:09.699678', 15);
INSERT INTO public.projects VALUES (146, '上海前海人寿金融中心', '2024-11-04', '渠道跟进', '经销商', '入围', NULL, NULL, '上海福玛通信信息科技有限公司', NULL, '上海书柏智能科技有限公司', '签约', '2024/11/14 李华伟
【阶段变更】中标->签约

2024/11/14 11:42:43 李华伟
【完善价格】 49409
2024/11/4 15:08:19 李华伟
【完善价格】 108664
', 'CPJ202411-002', '2024-11-14', 0, NULL, NULL, '2024-11-04 00:00:00', '2025-04-28 00:59:09.700876', 15);
INSERT INTO public.projects VALUES (147, '上海惠柏新材研发总部大楼', '2024-11-01', '销售重点', '销售', '入围', NULL, NULL, NULL, NULL, '上海书柏智能科技有限公司', '品牌植入', '2024/11/1 16:38:58 李华伟
【完善价格】 130256
', 'SPJ202411-005', '2024-11-01', 0, NULL, NULL, '2024-11-01 00:00:00', '2025-04-28 00:59:09.701799', 15);
INSERT INTO public.projects VALUES (148, '川沙C06-04地块', '2024-10-10', '渠道跟进', '经销商', '入围', NULL, NULL, '上海福玛通信信息科技有限公司', NULL, '上海凯通实业有限公司', '签约', '2024/10/25 李华伟
【阶段变更】中标->签约

2024/10/21 11:06:59 李华伟
【完善价格】 81067
2024/10/21 李华伟
【阶段变更】招标中->中标

2024/10/18 15:34:25 李华伟
【完善价格】 90883
2024/10/10 14:00:35 李华伟
【完善价格】 102119
', 'CPJ202410-003', '2024-10-25', 0, NULL, NULL, '2024-10-10 00:00:00', '2025-04-28 00:59:09.702775', 15);
INSERT INTO public.projects VALUES (149, '盐城郁金香希尔顿', '2024-09-24', '渠道跟进', '经销商', '入围', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '上海金槐智能科技有限公司', '签约', '2024/9/29 李华伟
【阶段变更】中标->签约

2024/9/24 李华伟
类型改变为渠道跟进 
2024/9/24 李华伟
【出现困难】项目为升级质保后的改造，原系统天馈为其他品牌保留，关于对讲机和主机进行更新替换。

2024/9/24 14:14:56 李华伟
【完善价格】 67150
', 'CPJ202409-008', '2024-09-29', 0, NULL, NULL, '2024-09-24 00:00:00', '2025-04-28 00:59:09.70373', 15);
INSERT INTO public.projects VALUES (150, '金桥地铁上盖j09-04、05、06、07地块', '2024-09-09', '销售重点', '销售', '入围', NULL, '厦门万安智能有限公司', NULL, NULL, NULL, '发现', '2024/9/24 13:49:51 李华伟
【完善价格】 421627
', 'SPJ202409-003', '2024-09-24', 0, NULL, NULL, '2024-09-09 00:00:00', '2025-04-28 00:59:09.704668', 15);
INSERT INTO public.projects VALUES (151, '杭州西站北广场金钥匙', '2024-02-21', '销售重点', '销售', '入围', NULL, '厦门万安智能有限公司', '浙江航博智能工程有限公司', NULL, NULL, '品牌植入', '2024/5/11 21:19:51 李华伟
【拜访】「厦门万安智能有限公司」:  目前方案配合设计院和业主已经确认下来，等待业主审核整个项目的预算情况。品牌是由设计院推荐业主进行审核，跟进业主关系，看能否进行合作。
2024/3/15 15:04:46 李华伟
「阶段变更」
2024/3/15 13:21:20 李华伟
「提案」  :  目前方案按照2套系统，品牌这块设计院目前已经确认，后续需要邀约业主进行沟通，目前业主有意向要参观上海中心项目已经在确认时间。
2024/2/21 李华伟
目前厦门万安负责设计方案，初步对接上设计配合，后续跟进对方方案的设计和业主信息，找到业主。
', 'SPJ202402-001', '2024-09-24', 0, NULL, NULL, '2024-02-21 00:00:00', '2025-04-28 00:59:09.705586', 15);
INSERT INTO public.projects VALUES (152, '中国五冶集团有限公司五冶集团临港总部基地', '2024-08-26', '销售重点', '销售', '入围', NULL, NULL, NULL, NULL, NULL, '发现', NULL, 'SPJ202408-007', '2024-09-24', 0, NULL, NULL, '2024-08-26 00:00:00', '2025-04-28 00:59:09.706493', 15);
INSERT INTO public.projects VALUES (154, '上海长宁区天山路街道113街坊34丘E2-03地块办公铁狮门', '2023-04-27', '渠道跟进', '销售', '入围', NULL, '迈进工程设计咨询(上海)有限公司', '上海福玛通信信息科技有限公司', NULL, '上海灵一建筑配套工程有限公司', '中标', '2024/3/25 15:03:09 李华伟
「阶段变更」
「拜访」  :  目前上海福玛配合中建八局中标，刚进场，预计进场在9月份左右。
45376.6271875 邹飞
「阶段变更」
「拜访」  :  目前上海福玛配合中建八局中标，刚进场，预计进场在9月份左右。
2024/2/21 12:52:31 李华伟
设计方改变为  迈进工程设计咨询(上海)有限公司 类型改变为  渠道跟进     
45343.5364699074 邹飞
设计方改变为  迈进工程设计咨询(上海)有限公司 类型改变为  渠道跟进     
2023/11/1 李华伟
目前品牌入围，瀚网配合投标。
45231 邹飞
目前品牌入围，瀚网配合投标。
', 'CPJ202304-010', '2024-09-20', 0, NULL, NULL, '2023-04-27 00:00:00', '2025-04-28 00:59:09.708284', 15);
INSERT INTO public.projects VALUES (155, '上海瑞明星产业化及研发中心', '2024-09-14', '销售重点', '销售', '围标', NULL, NULL, NULL, NULL, '北京真视通科技有限公司', '品牌植入', '2024/9/18 11:27:55 李华伟
【完善价格】 115210
2024/9/18 11:27:06 李华伟
【完善价格】 106530
', 'SPJ202409-009', '2024-09-18', 0, NULL, NULL, '2024-09-14 00:00:00', '2025-04-28 00:59:09.709188', 15);
INSERT INTO public.projects VALUES (156, '前滩媒体城08-01&13-01', '2023-10-23', '渠道跟进', '销售', '无要求', NULL, '华东建筑设计研究院有限公司', '上海鑫桉信息工程有限公司', NULL, '上海擎天电子科技有限公司', '签约', '2024/9/6 14:30:23 李华伟
【阶段变更】中标->签约

2024/2/21 12:51:54 李华伟
设计方改变为  华东建筑设计研究院有限公司 分销商改编为   上海淳泊  类型改变为  渠道跟进     
2023/11/1 李华伟
品牌入围和源尚岛亦郎，擎天中标鑫桉在跟进。关注进度以及深化清单。
', 'CPJ202310-001', '2024-09-06', 0, NULL, NULL, '2023-10-23 00:00:00', '2025-04-28 00:59:09.710071', 15);
INSERT INTO public.projects VALUES (157, '上海波克中心', '2023-03-09', '渠道跟进', '代理商', '入围', NULL, NULL, '上海鑫桉信息工程有限公司', NULL, '上海擎天电子科技有限公司', '中标', '2024/2/21 13:05:03 李华伟
分销商改编为   上海淳泊  经销商改变为   上海鑫桉信息工程有限公司    
2024/2/21 13:03:36 李华伟
类型改变为  渠道跟进     
2023/11/1 李华伟
品牌入围，代理商瀚网配合书柏，鑫桉配合上海擎天投标。
', 'CPJ202303-003', '2024-08-16', 0, NULL, NULL, '2023-03-09 00:00:00', '2025-04-28 00:59:09.71103', 15);
INSERT INTO public.projects VALUES (158, '舟山东港养生馆', '2024-06-07', '渠道跟进', '经销商', '入围', NULL, NULL, '浙江航博智能工程有限公司', NULL, '浙江建工设备安装有限公司', '签约', '2024/7/15 14:15:30 李华伟
【阶段变更】中标->签约
2024/6/7 李华伟
【提案采纳】:  品牌入围，目前航博配合分包在深化，预计下个月进场。
', 'CPJ202406-001', '2024-07-15', 0, NULL, NULL, '2024-06-07 00:00:00', '2025-04-28 00:59:09.711933', 15);
INSERT INTO public.projects VALUES (159, '陆家嘴昌邑路梅园社区', '2024-01-10', '渠道跟进', '销售', '入围', NULL, '上海德恳设计咨询顾问有限公司', '上海福玛通信信息科技有限公司', NULL, NULL, '品牌植入', '2024/3/15 14:00:58 李华伟
「提案」  上海德恳设计咨询顾问有限公司:  目前设计方案推的全和源产品和平台，品牌已经提交上去，后续跟进确认。
45366.5840046296 邹飞
「提案」  上海德恳设计咨询顾问有限公司:  目前设计方案推的全和源产品和平台，品牌已经提交上去，后续跟进确认。
2024/2/21 12:38:08 李华伟
设计方改变为  上海德恳设计咨询顾问有限公司 类型改变为  渠道管理 集成商改变为      
45343.5264814815 邹飞
设计方改变为  上海德恳设计咨询顾问有限公司 类型改变为  渠道管理 集成商改变为      
2023/11/1 李华伟
目前配合德恳前期设计，计划植入和源对讲机品牌。
45231 邹飞
目前配合德恳前期设计，计划植入和源对讲机品牌。
', 'CPJ202401-003', '2024-07-08', 0, NULL, NULL, '2024-01-10 00:00:00', '2025-04-28 00:59:09.712848', 15);
INSERT INTO public.projects VALUES (160, '前滩E08-E10-E12', '2023-01-03', '渠道跟进', '销售', '入围', NULL, '上海凯通实业有限公司', '上海福玛通信信息科技有限公司', NULL, '上海凯通实业有限公司', '招标中', '2024/3/15 14:25:16 李华伟
「阶段变更」
45366.6008796296 邹飞
「阶段变更」
2024/2/21 13:05:25 李华伟
经销商改变为   上海福玛通信信息科技有限公司 类型改变为  渠道管理    
45343.5454282407 邹飞
经销商改变为   上海福玛通信信息科技有限公司 类型改变为  渠道管理    
2023/11/1 李华伟
配合集成商设计，预计年后招标。
45231 邹飞
配合集成商设计，预计年后招标。
', 'CPJ202301-001', '2024-06-29', 0, NULL, NULL, '2023-01-03 00:00:00', '2025-04-28 00:59:09.713752', 15);
INSERT INTO public.projects VALUES (161, '张江56-01希尔顿酒店', '2023-03-27', '渠道跟进', '销售', '入围', NULL, NULL, '上海淳泊信息科技有限公司', NULL, '上海凯通实业有限公司', '签约', '2024/5/17 13:04:52 李华伟
【阶段变更】中标->签约
2024/2/21 12:55:19 李华伟
分销商改编为   上海淳泊  类型改变为  渠道跟进     
2023/11/1 李华伟
品牌入围和源亦朗欣民，淳泊配合投标。
', 'CPJ202303-005', '2024-05-17', 0, NULL, NULL, '2023-03-27 00:00:00', '2025-04-28 00:59:09.71463', 15);
INSERT INTO public.projects VALUES (162, '前滩54号地块', '2022-11-25', '渠道跟进', '销售', '入围', NULL, '上海凯通实业有限公司', '上海淳泊信息科技有限公司', NULL, '上海行余信息技术有限公司', '签约', '2024/5/17 13:05:07 李华伟
【阶段变更】招投标->签约
2024/2/21 13:05:52 李华伟
分销商改编为   上海淳泊  类型改变为  渠道跟进     
2023/11/1 李华伟
品牌入围，配合凯通电信行余投标。
', 'CPJ202211-013', '2024-05-17', 0, NULL, NULL, '2022-11-25 00:00:00', '2025-04-28 00:59:09.715866', 15);
INSERT INTO public.projects VALUES (163, '上海光通信有限公司集成电路厂房', '2023-04-06', '渠道跟进', '销售', '入围', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '上海书柏智能科技有限公司', '签约', '2024/4/30 17:26:02 李华伟
[阶段变更] ->签约
2024/4/26 13:32:01 李华伟
「阶段变更」签约->中标
2024/2/21 13:03:20 李华伟
分销商改编为   上海瑞康 类型改变为  渠道跟进     
2023/11/1 李华伟
配合永峻、书柏投标，品牌围标。
项目配合未中标，杨俊杰配合客户上海谌亚中标其他代理商在对接。
', 'CPJ202304-001', '2024-04-30', 0, NULL, NULL, '2023-04-06 00:00:00', '2025-04-28 00:59:09.717023', 15);
INSERT INTO public.projects VALUES (164, '嘉兴云帆大厦', '2024-03-21', '渠道跟进', '经销商', '入围', NULL, NULL, '浙江航博智能工程有限公司', NULL, '浙江众诚智能', '签约', '2024/4/1 10:53:49 李华伟
【完善价格】 57982
2024/4/1 09:34:18 李华伟
「阶段变更」
2024/3/21 李华伟
「提案采纳」  :  品牌天馈无要求，目前航博配合投标的客户中标，在确认商务价格阶段。预计月底前签约。
2024/3/1 17:25:56 李华伟
[阶段变更] ->签约
', 'CPJ202403-006', '2024-04-20', 0, NULL, NULL, '2024-03-21 00:00:00', '2025-04-28 00:59:09.717949', 15);
INSERT INTO public.projects VALUES (165, '上海御桥12C-18地块', '2024-03-29', '渠道跟进', '系统集成商', '入围', NULL, NULL, '上海福玛通信信息科技有限公司', NULL, '上海行余信息技术有限公司', '品牌植入', NULL, 'CPJ202403-013', '2024-03-29', 0, NULL, NULL, '2024-03-29 00:00:00', '2025-04-28 00:59:09.718829', 15);
INSERT INTO public.projects VALUES (166, '御桥10A02地块', '2022-11-25', '渠道跟进', '销售', '入围', NULL, NULL, '上海福玛通信信息科技有限公司', NULL, '上海行余信息技术有限公司', '签约', '2024/3/1 17:30:19 李华伟
[阶段变更] ->签约
2024/2/26 14:01:55 李华伟
当前阶段改变为   签约    
2024/2/21 12:56:11 李华伟
分销商改编为   上海淳泊  面价金额改变为   239084 类型改变为  渠道管理    
2023/11/1 李华伟
品牌入围，代理商配合凯通行余投标。2023.7.31 李华伟提供信息  已中标
', 'CPJ202211-014', '2024-03-01', 0, NULL, NULL, '2022-11-25 00:00:00', '2025-04-28 00:59:09.719698', 15);
INSERT INTO public.projects VALUES (168, '永寿路88号（新黄浦酒店公寓）', '2025-04-21', '渠道跟进', '渠道', '入围', NULL, NULL, '上海福玛通信信息科技有限公司', NULL, '上海云思智慧信息技术有限公司', '招标中', '2025/4/25 13:47:22 杨俊杰
【完善价格】 128362
2025/4/23 杨俊杰
「刘宗怡」 上海云思智慧信息技术有限公司  渠道报备，云思参与此业务投标，品牌虽然未入围，但可以使用同档次，云思咨询价格合适后，还是会考虑知名品牌
2025/4/21 14:33:31 杨俊杰
【授权编号】：添加   HY-CPJ202504-027

2025/4/21 11:54:26 杨俊杰
提交报备
', 'CPJ202504-027', '2025-04-25', 0, NULL, NULL, '2025-04-21 00:00:00', '2025-04-28 01:00:52.279524', 14);
INSERT INTO public.projects VALUES (169, '上海名人苑', '2024-08-07', '渠道跟进', '经销商', '入围', NULL, NULL, '上海福玛通信信息科技有限公司', NULL, '上海秋煜电力工程有限公司', '签约', '2025/4/25 12:42:39 杨俊杰
[阶段变更] ->签约
2025/4/21 14:27:18 杨俊杰
申请项目批价
2025/4/21 14:26:07 杨俊杰
【完善价格】 456293
2025/4/21 14:22:34 杨俊杰
【完善价格】 455377
2025/4/21 杨俊杰
「冯一」 上海秋煜电力工程有限公司  跟踪渠道，确认商务合同已经确认，发起渠道业务批价确认
2025/4/18 邹飞
「冯一」 上海秋煜电力工程有限公司  预计下周先供货10#楼天馈部分的材料
2025/4/11 邹飞
「冯一」 上海秋煜电力工程有限公司  现场部分已具备施工条件，预计5月份启动
2025/2/21 13:30:42 杨俊杰
【出货时间预测】：添加   2025年二季度
【当前阶段情况说明】：添加   该项目跟进确认，现场实施具备施工条件，项目现场负责人计划3月份提交采购计划。待项目现场提交采购计划后，会组织供应商与他们商务负责人洽谈价格机合约。现阶段与项目现场复核确认深化方案，商务方面因与现场达成合作意向，品牌已经提交确认

2024/12/6 杨俊杰
【阶段变更】失败->中标

45632 邹飞
【阶段变更】失败->中标

2024/12/6 杨俊杰
【阶段变更】中标->失败

45632 邹飞
【阶段变更】中标->失败

2024/8/30 12:40:08 杨俊杰
【消息】「」该项目帮助渠道与弱电分包单位推进信道机及对讲机替换为全和源产品，目前说服弱电单位现场负责人，提供产品资料及样品，给予项目现场，让项目现场提交资料报验，等待结果，预计9月份会有结果。商务进度按弱电分包现场负责人计划今年底会有部分区域启动穿线
45534.5278703704 邹飞
【消息】「」该项目帮助渠道与弱电分包单位推进信道机及对讲机替换为全和源产品，目前说服弱电单位现场负责人，提供产品资料及样品，给予项目现场，让项目现场提交资料报验，等待结果，预计9月份会有结果。商务进度按弱电分包现场负责人计划今年底会有部分区域启动穿线
2024/8/18 13:36:31 杨俊杰
【消息】「」该项目与渠道沟通了解，中标单位上海秋煜在内部复核成本，比选价格，目前主要与率衍在PK价格，但福玛与现场负责人商务关系有过合作，通过信道机、对讲机品牌由摩托罗拉替换为和源策略，现阶段还在沟通调整整体报价，推进锁定和源品牌
45522.567025463 邹飞
【消息】「」该项目与渠道沟通了解，中标单位上海秋煜在内部复核成本，比选价格，目前主要与率衍在PK价格，但福玛与现场负责人商务关系有过合作，通过信道机、对讲机品牌由摩托罗拉替换为和源策略，现阶段还在沟通调整整体报价，推进锁定和源品牌
2024/7/4 杨俊杰
该项目渠道报备，福玛付言新的客户中标，和源品牌入围，项目实施预计要明年一季度，目前在方案深化配套，并推进采用全系列和源产品
45477 邹飞
该项目渠道报备，福玛付言新的客户中标，和源品牌入围，项目实施预计要明年一季度，目前在方案深化配套，并推进采用全系列和源产品
', 'CPJ202408-002', '2025-04-25', 0, NULL, NULL, '2024-08-07 00:00:00', '2025-04-28 01:00:52.28161', 14);
INSERT INTO public.projects VALUES (170, '御桥12C-18地块', '2025-04-18', '渠道跟进', '渠道', '入围', NULL, NULL, '上海福玛通信信息科技有限公司', NULL, '上海鼎时智能化设备工程有限公司', '签约', '2025/4/25 12:42:32 杨俊杰
[阶段变更] ->签约
2025/4/21 14:35:57 杨俊杰
申请项目批价
2025/4/18 17:02:27 杨俊杰
【授权编号】：添加   HY-CPJ202401-005

2025/4/14 21:02:53 杨俊杰
提交报备
2025/4/14 21:02:32 杨俊杰
提交报备
2025/4/13 16:06:14 杨俊杰
提交报备
2025/4/13 15:54:34 杨俊杰
【完善价格】 81095
2024/2/21 12:29:51 李华伟
类型改变为  渠道跟进     
45343.5207291667 邹飞
类型改变为  渠道跟进     
2023/11/1 李华伟
品牌入围，目前代理商淳泊配合行余凯通投标，后续跟进投标结果。
45231 邹飞
品牌入围，目前代理商淳泊配合行余凯通投标，后续跟进投标结果。
', 'CPJ202401-005', '2025-04-25', 0, NULL, NULL, '2025-04-18 00:00:00', '2025-04-28 01:00:52.283818', 14);
INSERT INTO public.projects VALUES (171, '张家浜绿地C1B-02和C1C-01地块', '2025-03-07', '渠道跟进', '销售', '围标', NULL, '卓展工程顾问(北京)有限公司-上海分公司', '上海艾亿智能科技有限公司', NULL, NULL, '招标中', '2025/4/24 杨俊杰
「梅小好」 上海艾亿智能科技有限公司  张家浜业务招标，目前询价仅壹杰和九分及九分分包单位，与梅小好沟通复核情况。经了解基本确认壹杰中标C1B-02地块，而九分会中标C1C-01地块，但九分即使中标还是通过另外一家采购，关系基本都是另外一家在处理
2025/4/13 15:24:01 杨俊杰
【当前阶段】：改变成   招标中
【当前阶段情况说明】：改变成   该项目招标，李华伟配套壹杰，通过招标资料了解招标品牌，基站设备未入围，仅传输设备围标，为和源、瀚网及福玛

2025/4/10 13:30:50 杨俊杰
【当前阶段】：改变成   招标前
【当前阶段情况说明】：添加   该项目预计二季度招标，目前已知潜在参与集成商：信业、中建电子、益邦及万安，品牌初步确认为可控范围，待项目招标，复核招标品牌，了解具体参与集成商信息，跟进配合投标

2025/4/10 杨俊杰
「梅小好」 上海艾亿智能科技有限公司  与梅小好沟通反馈有集成商挂靠九分资质，通过初步复核品牌的确可控，但参与集成商通过九分关系了解到并没有参考招标品牌，用的是浙江尧起，将次情况让梅小好复核集成商信息，判断用户除了品牌招标在可控范围内以外，是否有能力可以掌控集成商。项目预计二季度招标，潜在参与集成商：信业、中建电子、益邦及万安都有可能参与，待项目正式招标，了解参与集成商具体情况
2025/3/7 11:31:43 杨俊杰
【授权编号】：改变成   HY-CPJ202408-018
【类型】：改变成   渠道跟进

2025/2/21 16:35:09 杨俊杰
【完善价格】 477632
2024/12/27 杨俊杰
类型改变为渠道跟进 
2024/9/20 16:48:18 杨俊杰
【完善价格】 490551
', 'CPJ202408-018', '2025-04-24', 0, NULL, NULL, '2025-03-07 00:00:00', '2025-04-28 01:00:52.285707', 14);
INSERT INTO public.projects VALUES (172, '上海浦东东站', '2023-10-17', '销售重点', '销售', '入围', NULL, '华东建筑设计研究院有限公司', '上海艾亿智能科技有限公司', NULL, '上海市安装工程集团有限公司-第九分公司', '中标', '2025/4/22 杨俊杰
「龚俊瑜」 上海市安装工程集团有限公司-第九分公司  拜访龚俊瑜和滕思宇，赠送茶叶慰问客户。跟进浦东东站地下标段业务，目前了解浦东东站地下标段近期上安内部会初步确认系统供应商，按龚总给与价格进行调整，先稳定上安，后续继续跟进了解目前上安这边的情况。同时龚俊瑜告知E2商务区最终价格和邹飞那边已经确认，由于他们合同还没下来，让我们提前配合
2025/4/18 杨俊杰
「丁愉豪」 上海市安装工程集团有限公司-第九分公司  拜访丁愉豪，经了解无线对讲中标价格不含税为270万，这个价格是四建安装中标价格，等于智能化分包的话四建安装还要收取管理费。按现在九分内部想法是各系统有关技术要求及价格确认，然后再内部讨论，调整报价后跟进九分龚俊瑜，拜访梁栋之，表示给予支持，稳定九分关系
2025/4/16 杨俊杰
「黄辰赟」 华东建筑设计研究院有限公司  拜访黄辰贇，跟进浦东东站地下标段情况。复核上安九分反馈情况，基本一致，待上安提交方案及品牌，尤其品牌方面让其把关。至于用户方面，经了解从申通地铁掉过来李继栋后续负责，但没有联系方式，看是否有需要去提前接触
2025/4/13 15:24:30 杨俊杰
【系统集成商】：改变成   上海市安装工程集团有限公司-第九分公司

2025/4/8 杨俊杰
「梁晓君」 上海市安装工程集团有限公司-第九分公司  浦东东站地下及空铁联运基本确认上安九分负责智能化实施及设备采购，项目现场张东伟负责，与张东伟初步建立沟通，今年他们主要计划是项目整体实施方案深化，与业主确认，具体进场实施要到明年
2025/2/25 11:21:40 杨俊杰
【经销商】：添加   上海艾亿智能科技有限公司

2025/2/21 17:15:01 杨俊杰
【完善价格】 4978015
2025/2/21 14:03:26 杨俊杰
【系统集成商】：改变成   上海建工四建集团有限公司
【当前阶段情况说明】：改变成   浦东东站分为地上、地下分开招标，其中地上部分经了解对讲系统在信息包内，中标单位：通号，由于招标形式按铁路要求，没有品牌限定，现阶段还未找到有关负责人。地下部分中标单位：建工四建安装，品牌为摩托罗拉、中兴高达、和源通信。现阶段计划跟进建工四建安装，找到智能化专业主要负责人，通过技术招标要求，及借用合作伙伴艾亿智能与用户关系，锁定品牌，从而在建立地上部分合作

2025/2/21 13:54:28 杨俊杰
【当前阶段情况说明】：添加   拜访建工四建安装投标部赵展鹏，经沟通由于年前刚宣布中标结果，原定中铁由于个别资质原因由他们中标，现阶段他们可能与甲方合同还未最终签订，由于他们原先主要以机电业务为主，智能化可能会分包，具体需要与他们经营部负责人沟通了解。同时上安九分询价，经了解他们可能会作为智能化分包，按上安九分反馈目前建工四建给予的无线对讲系统预算和当时我们投标报价对比差了230万，让我们先按清单复核，调整优惠一版价格。计划后续通过赵展鹏引荐，了解项目中标情况。

2024/12/27 杨俊杰
【阶段变更】招标中->中标

2024/12/6 杨俊杰
【阶段变更】品牌植入->招标中

2024/5/20 15:30:01 杨俊杰
【消息】「」与华东院及上安重新复核设计方案，据了解地上、地下部分预算已经批复，且地下施工图已经提交给予用户，除非外部因素，否则设计院不太好再做修改，地上部分预计本月提交确认。目前建设方东方枢纽还未了解到具体负责人，按华东院黄辰赟的意思，东方枢纽先等铁道部确认后可能才会有所动作
2024/3/20 16:19:02 杨俊杰
施工图设计初版基本完成，与黄辰赟沟通了解目前没有任何消息。上安在提前询价，进一步跟进了解项目后续情况
2023/11/1 杨俊杰
该项目高铁站台内由国铁下属中铁设计院负责，站台外由华东院负责，另外还有个隧道由隧道院负责，目前配合华东院提交初设方案，用于项目预算审批。整个项目地下部分由上海市政府审批预算，地上站台内由北京负责审批预算，10月底11月初地上、地下预算审批确认后就会启动施工图设计，计划要求今年底完成施工图设计。目前业主没有具象负责人，有关品牌方面还需确认由谁发起，由谁确认
', 'SPJ202310-001', '2025-04-22', 0, NULL, NULL, '2023-10-17 00:00:00', '2025-04-28 01:00:52.287239', 14);
INSERT INTO public.projects VALUES (173, '舜宇12英寸透明衬底晶圆AR眼镜微纳光学产品', '2025-03-13', '销售重点', '销售', '入围', '舜宇奥来微纳光学（上海）有限公司', NULL, '上海瀚网智能科技有限公司', NULL, '苏州工业园区汉威控制系统工程有限公司', '中标', '2025/4/21 13:14:46 杨俊杰
申请项目批价
2025/4/21 13:13:58 杨俊杰
【完善价格】 47586
2025/4/21 13:09:37 杨俊杰
【完善价格】 37710
2025/4/21 杨俊杰
「柴经理」 苏州工业园区汉威控制系统工程有限公司  跟踪渠道，确认商务合同已经确认，发起渠道业务批价确认
2025/4/13 15:36:31 杨俊杰
【完善价格】 47611
2025/3/29 12:54:56 杨俊杰
【出货时间预测】：改变成   2025年二季度

2025/3/13 14:05:14 杨俊杰
【出货时间预测】：改变成   舜宇奥来微纳光学（上海）有限公司「2025年二季度」
【授权编号】：添加   HY-SPJ202502-002
【类型】：添加   销售重点

', 'SPJ202502-002', '2025-04-21', 0, NULL, NULL, '2025-03-13 00:00:00', '2025-04-28 01:00:52.288724', 14);
INSERT INTO public.projects VALUES (174, '新世代产业园', '2025-04-21', '渠道跟进', '渠道', '入围', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '上海东大金智信息系统有限公司', '招标中', '2025/4/21 11:51:47 杨俊杰
【授权编号】：添加   HY-CPJ202504-026

2025/4/18 17:11:05 杨俊杰
提交报备
', 'CPJ202504-026', '2025-04-21', 0, NULL, NULL, '2025-04-21 00:00:00', '2025-04-28 01:00:52.29042', 14);
INSERT INTO public.projects VALUES (175, '杨浦区定海社区G1-2地块（定海138街坊）', '2025-04-21', '渠道跟进', '渠道', '入围', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '上海万坤实业发展有限公司', '招标中', '2025/4/21 11:51:27 杨俊杰
【当前阶段】：改变成   招标中

2025/4/21 11:51:16 杨俊杰
【授权编号】：添加   HY-CPJ202504-024

2025/4/18 17:06:14 杨俊杰
提交报备
', 'CPJ202504-024', '2025-04-21', 0, NULL, NULL, '2025-04-21 00:00:00', '2025-04-28 01:00:52.291844', 14);
INSERT INTO public.projects VALUES (176, '松江区俊普智造中心改造', '2025-04-18', '渠道跟进', '渠道', '入围', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '上海跃燕弱电工程有限公司', '招标中', '2025/4/18 17:03:28 杨俊杰
【分销商】：添加   上海瑞康
【授权编号】：添加   HY-CPJ202504-014

2025/4/13 16:05:39 杨俊杰
提交报备
2025/4/13 16:03:21 杨俊杰
【完善价格】 80097
', 'CPJ202504-014', '2025-04-18', 0, NULL, NULL, '2025-04-18 00:00:00', '2025-04-28 01:00:52.293234', 14);
INSERT INTO public.projects VALUES (177, '上海金山枫泾臻品之选酒店', '2025-04-18', '渠道跟进', '渠道', '入围', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '上海电信科技发展有限公司', '招标中', '2025/4/18 17:03:01 杨俊杰
【分销商】：添加   上海瑞康

2025/4/18 17:02:51 杨俊杰
【授权编号】：添加   HY-CPJ202504-013

2025/4/13 16:06:01 杨俊杰
提交报备
2025/4/13 15:58:09 杨俊杰
【完善价格】 18904
', 'CPJ202504-013', '2025-04-18', 0, NULL, NULL, '2025-04-18 00:00:00', '2025-04-28 01:00:52.294742', 14);
INSERT INTO public.projects VALUES (178, '上海党校', '2025-02-08', '销售重点', '销售', '入围', NULL, '上海现代建筑设计研究院有限公司', NULL, NULL, '上海仪电鑫森科技发展有限公司', '品牌植入', '2025/4/18 杨俊杰
「闻锋」 上海现代建筑设计研究院有限公司  拜访闻锋，沟通上海党校，目前还在方案阔粗，用户希望搭建上层平台，所以找了3家，华为、联通及仪电鑫森，待方案阔粗好了之后才会启动智能化设计。至于915项目，经沟通确认，仪电鑫森已经报了和源的品牌，但因为项目特殊性，所以进度比较慢
2025/4/13 15:05:41 杨俊杰
【系统集成商】：添加   上海仪电鑫森科技发展有限公司

2025/2/8 11:08:29 杨俊杰
【授权编号】：添加   HY-SPJ202501-004
【类型】：添加   销售重点

2025/2/6 14:26:42 杨俊杰
【完善价格】 422224
2025/2/6 11:51:36 杨俊杰
【设计院及顾问】：改变成   闻锋「上海现代建筑设计研究院有限公司」
【当前阶段】：添加   品牌植入

', 'SPJ202501-004', '2025-04-18', 0, NULL, NULL, '2025-02-08 00:00:00', '2025-04-28 01:00:52.296231', 14);
INSERT INTO public.projects VALUES (179, '上海龙旗项目', '2024-01-15', '渠道跟进', '销售', '入围', '上海龙旗科技股份有限公司', '卓展工程顾问(北京)有限公司-上海分公司', '上海瀚网智能科技有限公司', NULL, '上海云赛智联科技有限公司', '中标', '2025/4/18 杨俊杰
「周杰」 上海云赛智联科技有限公司  帮助渠道拜访周杰，了解到他们中标，项目进度比较着急，他们原先是由沅亢郭鹏配合，用的科立讯，按周杰意思主要还是在于价格，重新分析设备成本，提供清单报价，在给予跟进
2025/4/13 15:08:52 杨俊杰
【分销商】：添加   上海瑞康
【经销商】：添加   上海瀚网智能科技有限公司
【系统集成商】：添加   上海云赛智联科技有限公司

2025/4/10 15:03:33 杨俊杰
【当前阶段】：改变成   中标
【当前阶段情况说明】：改变成   该项目云赛智联中标，他们是通过用户IT部门负责人关系最后进入，低价中标，经了解他们投标当时选用科立讯，提供清单报价，通过用户及顾问看是否能够扭转局势，从而拉回与集成商谈判在平等条件下

2025/4/10 10:40:01 李冬
【完善价格】 438705
2025/4/10 09:51:23 李冬
【当前阶段】：改变成   中标
【当前阶段情况说明】：改变成   云赛中标，品牌和源，瀚网，科立讯

2025/4/10 09:41:30 李冬
【经销商】：添加   上海瀚网智能科技有限公司
【系统集成商】：改变成   上海云赛智联信息科技有限公司

2025/4/10 李冬
「倪刚」 上海云赛智联信息科技有限公司  向几家配合过得集成商打听了中标情况，得知云赛中标，最后向销售证实云赛确定中标。目前和集成商沟通。目前品牌和源瀚网科立讯，存在不确定因素。希望和源可以在业主那边把品牌把控。
2025/4/9 杨俊杰
「李霄云」 卓展工程顾问(北京)有限公司-上海分公司  拜访卓展李霄云，反馈九星城项目，了解龙旗项目及新增业务情况。有关龙旗该项目，得到反馈云赛智联中标，他们是通过用户IT部门负责人关系最后进入，低价中标，经了解他们投标当时选用科立讯。后续计划通过用户及顾问看是否能够扭转局势，从而拉回与集成商谈判在平等条件下
2025/3/13 14:37:01 杨俊杰
【直接用户】：添加   上海龙旗科技股份有限公司
【当前阶段情况说明】：添加   该项目经了解投标还未有最终结果，主要是云思和云赛在最后竞争

2025/2/27 09:21:08 李冬
【系统集成商】：添加   上海延华智能科技（集团）股份有限公司

2025/2/25 14:56:46 李冬
【授权编号】：添加   HY-CPJ202401-008
【类型】：添加   渠道跟进

2025/2/21 17:19:42 杨俊杰
【完善价格】 1029081
2024/12/27 杨俊杰
类型改变为销售重点 
2024/12/6 杨俊杰
【阶段变更】品牌植入->招标中

2024/5/20 15:23:19 杨俊杰
【消息】「」该项目与机电顾问卓展李霄云沟通，项目即将启动智能化施工图设计，初步达成合作意向，后续推进业务技术配套，植入核心产品
2024/2/26 17:33:14 杨俊杰
设计方改变为  卓展工程顾问「北京」有限公司-上海分公司    
2024/2/26 17:32:58 杨俊杰
类型改变为  销售重点    
2024/2/26 12:03:37 杨俊杰
面价金额改变为   660081    
该项目卓展史伟杰告知，目前他们仅提供业主一版项目概算，图纸设计由于设计院还未全部完成，所以还没定稿，设计院负责机电设计，他们负责弱电智能化，现阶段还不确定设计进度，一直在催促设计院完成图纸设计
2023/11/1 杨俊杰
该项目卓展李霄云负责智能化设计，咨询我们配套设计方案。计划跟进了解项目设计进度，确认设计方案，推动招标品牌入围
', 'CPJ202401-008', '2025-04-18', 0, NULL, NULL, '2024-01-15 00:00:00', '2025-04-28 01:00:52.297629', 14);
INSERT INTO public.projects VALUES (180, '华虹张江工厂配套用房', '2024-08-08', '渠道跟进', '经销商', '入围', '上海华虹(集团)有限公司 ', '上海华虹智联信息科技有限公司', '上海瀚网智能科技有限公司', NULL, '上海华虹智联信息科技有限公司', '中标', '2025/4/18 杨俊杰
「周心一」 上海华虹智联信息科技有限公司  与采购周心一及项目经理确认最终方案及价格，渠道配合提供最终报价，待采购确认后，发起合约商务流程
2025/4/7 17:25:45 李冬
【当前阶段】：改变成   重复

2025/4/3 23:48:29 李冬
【分销商】：添加   上海瑞康

2025/2/21 16:38:59 杨俊杰
【完善价格】 148069
2025/2/21 15:15:04 杨俊杰
【出货时间预测】：添加   2025年二季度
【分销商】：添加   上海瑞康

45704.657349537 李冬
【当前阶段】：改变成   中标
【当前阶段情况说明】：添加   该项目华虹计通中标，品牌入围，主要与凌越竞争。现阶段华虹计通采购三方询价，分别找到瑞康和凌越。拜访业主负责人王炜，希望通过业务合作锁定系统品牌

2025/2/16 15:46:35 杨俊杰
【当前阶段】：改变成   中标
【当前阶段情况说明】：添加   该项目华虹计通中标，品牌入围，主要与凌越竞争。现阶段华虹计通采购三方询价，分别找到瑞康和凌越。拜访业主负责人王炜，希望通过业务合作锁定系统品牌

45704.6564236111 李冬
【直接用户】：添加   上海华虹(集团)有限公司 

2025/2/16 15:45:15 杨俊杰
【直接用户】：添加   上海华虹(集团)有限公司 

45653 李冬
类型改变为渠道跟进 
2024/12/27 杨俊杰
类型改变为渠道跟进 
45653 李冬
类型改变为销售重点 
2024/12/27 杨俊杰
类型改变为销售重点 
45597 李冬
【阶段变更】品牌植入->招标中

2024/11/1 杨俊杰
【阶段变更】品牌植入->招标中

45540.5734027778 李冬
【消息】「」该项目设计院反馈图纸设计已经完成，等待招标，品牌由业主指定，在跟踪确认。设计院反馈无线对讲概算50万+，项目一共7万方。
2024/9/5 13:45:42 杨俊杰
【消息】「」该项目设计院反馈图纸设计已经完成，等待招标，品牌由业主指定，在跟踪确认。设计院反馈无线对讲概算50万+，项目一共7万方。
', 'CPJ202408-003', '2025-04-18', 0, NULL, NULL, '2024-08-08 00:00:00', '2025-04-28 01:00:52.299115', 14);
INSERT INTO public.projects VALUES (181, '上实北外滩480米', '2023-10-17', '销售重点', '销售', '入围', NULL, '华东建筑设计研究院有限公司', NULL, NULL, '上海市安装工程集团有限公司-第九分公司', '品牌植入', '2025/4/16 杨俊杰
「黄辰赟」 华东建筑设计研究院有限公司  拜访黄辰贇，沟通了解目前北外滩91号地块，业主计划本月底完成商办部分招标图设计，下月确认观光区域，业主有想法计划弱电也在今年完成招标。有关品牌方面目前负责的暖通业主刘工，因智能化不太了解，加上性格问题，所以不太会插手品牌，所以很有可能会结合多方意见，主要是华东院和WSP。华东院内部可能参与的有张晓波和黄辰贇及毛晶轶。目前计划先把整体方案进行复核，待方案确认后结合概算统一来看。至于品牌上，做好各方关系，确保品牌入围同时能争取有利情况
2025/4/14 杨俊杰
「毛晶轶」 华东建筑设计研究院有限公司  与毛晶轶沟通，了解有关业主及品牌情况。按毛晶轶反馈目前业主那边不用太过担心，基本都会听他的，让我们先去和黄辰贇沟通，给予黄辰贇一版品牌建议，待黄辰贇确认后他这边会去看是否合理
2025/4/10 13:18:13 杨俊杰
【设计院及顾问】：改变成   华东建筑设计研究院有限公司

2024/9/5 12:48:09 杨俊杰
【消息】「」该项目目前配合黄辰赟提供图纸设计，项目属于施工图报审阶段，地下室部分经沟通了解图纸审核通过，地上部分开始启动。黄辰赟仅负责地上商业裙房部分，其余的由周天文和毛晶轶共同完成。现在他们内部也比较混乱，主负责交给王小安，按黄辰赟意思她会带着我们去和王小安沟通，看下一步如何推进
2024/3/15 16:39:08 杨俊杰
目前地下室配套菁峰参与设计，据了解是黄辰赟委托上安，上安再委托菁峰，提供地下室点位图和系统图，项目分为商业和酒店两套系统
2023/11/1 杨俊杰
该项目机电顾问为WSP，整个项目PM团队由华东院负责，弱电负责人为张晓波，同时业主聘请了专家，其中包括瞿二然，项目深化设计目前初步订地下部分由华东院黄辰赟负责，地上部分由李欣负责。需要了解施工图启动时间，推动施工图深化设计。
', 'SPJ202310-002', '2025-04-16', 0, NULL, NULL, '2023-10-17 00:00:00', '2025-04-28 01:00:52.300538', 14);
INSERT INTO public.projects VALUES (182, '虹桥机场东片区T1南地块', '2024-01-15', '销售重点', '销售', '围标', NULL, '华东建筑设计研究院有限公司', '上海瀚网智能科技有限公司', NULL, '上海电信科技发展有限公司', '中标', '2025/4/15 杨俊杰
「余杰」 华东建筑设计研究院有限公司  拜访余杰，沟通了解现在他调整到建筑三所，原先项目主要在负责的就是虹桥商务区项目及南京江北地上、地下，至于虹桥商务区项目现场进度比较缓慢，还有一栋建筑结构未封顶，桥架由总包完成，预估智能化今年下半年肯定会启动，至于电信方面通过了解的确各系统都没有完全去配合，可能还是因为现场进度原因
2025/2/21 17:15:33 杨俊杰
【完善价格】 531170
2025/1/8 12:02:39 杨俊杰
【出货时间预测】：添加   2025年三季度
【当前阶段】：改变成   中标
【分销商】：添加   上海瑞康
【经销商】：添加   上海瀚网智能科技有限公司

2025/1/6 14:18:59 杨俊杰
【当前阶段情况说明】：添加   该项目通过设计院告知上海电信中标，当时上海瀚网报备，通过上海瀚网与电信复核确认中标结果。同时瀚网与电信沟通过程中希望我们价格调整，与瀚网商议共同拜访集成商，沟通后再根据情况考虑如何调整报价

2025/1/6 14:16:38 杨俊杰
【系统集成商】：改变成   上海电信科技发展有限公司

2024/12/27 杨俊杰
类型改变为销售重点 
2024/12/2 杨俊杰
【阶段变更】品牌植入->招标中

2024/3/26 17:10:25 杨俊杰
该项目与华东院余杰沟通了解4月初提交招标图设计确认，随后就启动招标文件，项目预计6月份招标，待招标前他会找云思李坚沟通。目前与余杰基本达成合作，提供全系列品牌，他会帮助我们推动锁定。计划待招标资料配套完成后，复核招标品牌，并提前安排对接云思销售负责人李坚。
2023/11/1 杨俊杰
该项目与华东院余杰沟通了解智能化设计进度提前，预计春节前后就要完成招标图设计，项目由临空负责建设，分为商业和办公，办公由临空自己负责后期运营，商业计划外包运营
', 'SPJ202401-001', '2025-04-15', 0, NULL, NULL, '2024-01-15 00:00:00', '2025-04-28 01:00:52.30187', 14);
INSERT INTO public.projects VALUES (183, '上海工业博览会', '2025-01-11', '销售重点', '销售', '入围', NULL, '华东建筑设计研究院有限公司', NULL, NULL, NULL, '品牌植入', '2025/4/15 杨俊杰
「韩翌」 华东建筑设计研究院有限公司  拜访韩翌，目前他们调整到建筑一所，主要在忙着配合建筑一所参与投标，结构上调整意味着以后建筑一所业务一旦拿下，智能化业务基本都会在他和殷平手上负责，除非忙不过来后才有可能会转移到其他部门。至于工业博览会项目，因为进度原因还是比较慢，现在在等精装图出来后才会启动智能化施工图，业主方面现在还没具体负责人，侧边了解是原先国展业主负责人
2025/1/11 15:54:50 杨俊杰
【授权编号】：添加   HY-SPJ202408-010

', 'SPJ202408-010', '2025-04-15', 0, NULL, NULL, '2025-01-11 00:00:00', '2025-04-28 01:00:52.303242', 14);
INSERT INTO public.projects VALUES (184, '深圳中信金融中心', '2025-03-13', '渠道跟进', '销售', '入围', NULL, '华东建筑设计研究院有限公司', NULL, NULL, NULL, '品牌植入', '2025/4/13 15:49:52 杨俊杰
【完善价格】 706126
2025/3/13 14:07:40 杨俊杰
【授权编号】：添加   HY-CPJ202502-017
【类型】：添加   渠道跟进

', 'CPJ202502-017', '2025-04-13', 0, NULL, NULL, '2025-03-13 00:00:00', '2025-04-28 01:00:52.304572', 14);
INSERT INTO public.projects VALUES (209, '金桥地铁上盖J09-04、05、06、07地块', '2025-03-13', '渠道跟进', '销售', '入围', NULL, '上海世茂物联网科技有限公司', NULL, NULL, NULL, '品牌植入', '2025/3/13 14:05:41 杨俊杰
【授权编号】：添加   HY-CPJ202502-020
【类型】：添加   渠道跟进

', 'CPJ202502-020', '2025-03-13', 0, NULL, NULL, '2025-03-13 00:00:00', '2025-04-28 01:00:52.330947', 14);
INSERT INTO public.projects VALUES (185, '市政九珑汇', '2025-03-29', '渠道跟进', '渠道', '入围', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '江西盈石信息工程有限公司', '招标中', '2025/4/13 15:46:15 杨俊杰
【完善价格】 145766
2025/4/10 10:52:12 李冬
【完善价格】 95077
2025/3/29 12:51:11 杨俊杰
【授权编号】：添加   HY-CPJ202503-011
【类型】：添加   渠道跟进

2025/3/17 17:31:53 李冬
【授权编号】：添加   HY-CPJ202503-011
【类型】：添加   渠道跟进

', 'CPJ202503-011', '2025-04-13', 0, NULL, NULL, '2025-03-29 00:00:00', '2025-04-28 01:00:52.305731', 14);
INSERT INTO public.projects VALUES (186, '临港新片区数字文化装备产业总部基地', '2025-03-29', '渠道跟进', '渠道', '入围', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '上海东大金智信息系统有限公司', '招标前', '2025/4/13 15:42:37 杨俊杰
【完善价格】 293347
2025/4/10 10:43:20 李冬
【当前阶段】：改变成   失败
【当前阶段情况说明】：改变成   渠道报备，沟通梳理了解配合东大报价，用于项目招标前概算统计
客户反馈没有中标，具体中标单位未知

2025/4/10 李冬
「李兵」 上海东大金智信息系统有限公司  客户反馈没有中标，具体中标单位未知
2025/3/29 12:51:55 杨俊杰
【授权编号】：添加   HY-CPJ202503-016
【类型】：添加   渠道跟进

2025/3/21 11:52:17 李冬
【授权编号】：添加   HY-CPJ202503-016
【类型】：添加   渠道跟进

2025/3/21 11:25:01 李冬
【完善价格】 184764
2025/3/21 11:14:36 李冬
【分销商】：添加   上海瑞康

2025/3/21 11:10:11 李冬
【完善价格】 192254
', 'CPJ202503-016', '2025-04-13', 0, NULL, NULL, '2025-03-29 00:00:00', '2025-04-28 01:00:52.306886', 14);
INSERT INTO public.projects VALUES (187, '滴水湖地铁站', '2025-03-29', '渠道跟进', '渠道', '入围', NULL, NULL, '上海福玛通信信息科技有限公司', NULL, '上海电科智能系统股份有限公司', '中标', '2025/4/13 15:38:57 杨俊杰
【完善价格】 101134
2025/3/29 12:53:17 杨俊杰
【出货时间预测】：添加   2025年二季度
【当前阶段】：改变成   中标
【分销商】：添加   上海淳泊
【授权编号】：添加   HY-CPJ202503-015
【当前阶段情况说明】：改变成   该项目电科智能中标，已经进场，在等待与总包合同，商务预计5月份启动
【类型】：添加   渠道跟进

', 'CPJ202503-015', '2025-04-13', 0, NULL, NULL, '2025-03-29 00:00:00', '2025-04-28 01:00:52.308019', 14);
INSERT INTO public.projects VALUES (188, '沈阳市沈河区金廊22-1', '2025-03-29', '渠道跟进', '渠道', '入围', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '上海东大金智信息系统有限公司', '招标中', '2025/4/13 15:33:44 杨俊杰
【完善价格】 252498
2025/4/13 15:12:47 杨俊杰
【当前阶段】：改变成   招标中

2025/4/13 15:12:32 杨俊杰
【当前阶段】：改变成   失败
【当前阶段情况说明】：改变成   渠道反馈，配合集成商未中标

2025/4/10 10:42:07 李冬
【当前阶段】：改变成   失败
【当前阶段情况说明】：改变成   渠道报备，配合东大参与项目投标，品牌入围，主要竞争品牌:锐河、畅博、英智源
客户投标，跟踪结果，客户反馈没有中标，具体中标单位未知

2025/4/10 李冬
「李兵」 上海东大金智信息系统有限公司  客户反馈没有中标，具体中标单位未知
2025/3/29 12:50:40 杨俊杰
【授权编号】：添加   HY-CPJ202503-017
【类型】：添加   渠道跟进

2025/3/21 11:52:32 李冬
【授权编号】：添加   HY-CPJ202503-017
【类型】：添加   渠道跟进

2025/3/21 11:18:02 李冬
【完善价格】 188131
2025/3/21 11:14:26 李冬
【分销商】：添加   上海瑞康

', 'CPJ202503-017', '2025-04-13', 0, NULL, NULL, '2025-03-29 00:00:00', '2025-04-28 01:00:52.309162', 14);
INSERT INTO public.projects VALUES (189, '浙江横店喜来登业', '2025-03-13', '渠道跟进', '渠道', '围标', NULL, NULL, '上海艾亿智能科技有限公司', NULL, NULL, '招标中', '2025/4/13 15:28:29 杨俊杰
【完善价格】 171215
2025/4/13 15:21:57 杨俊杰
【当前阶段】：改变成   招标中
【分销商】：添加   上海瑞康
【当前阶段情况说明】：改变成   该项目招标，经核实品牌的确如艾亿梅小好反馈一致。现阶段范敬区域代理商在配合参与投标，给与指导价格

2025/3/13 14:07:05 杨俊杰
【授权编号】：添加   HY-CPJ202502-016
【类型】：添加   渠道跟进

', 'CPJ202502-016', '2025-04-13', 0, NULL, NULL, '2025-03-13 00:00:00', '2025-04-28 01:00:52.310291', 14);
INSERT INTO public.projects VALUES (190, '海口医院', '2025-03-07', '渠道跟进', '销售', '入围', NULL, '上海菁峰设计咨询有限公司', NULL, NULL, NULL, '失败', '2025/4/13 15:20:12 杨俊杰
【当前阶段】：改变成   失败
【当前阶段情况说明】：添加   未有集成商询价，找不到相关人员

2025/3/7 11:32:58 杨俊杰
【授权编号】：改变成   HY-CPJ202411-020
【类型】：改变成   渠道跟进

2024/11/1 15:38:49 杨俊杰
【完善价格】 261189
2024/11/1 15:38:40 杨俊杰
【完善价格】 209202
2024/11/1 15:34:12 杨俊杰
【完善价格】 207869
', 'CPJ202411-020', '2025-04-13', 0, NULL, NULL, '2025-03-07 00:00:00', '2025-04-28 01:00:52.311576', 14);
INSERT INTO public.projects VALUES (191, '港城广场', '2025-03-07', '渠道跟进', '销售', '入围', NULL, '上海现代建筑设计研究院有限公司', NULL, NULL, NULL, '搁置', '2025/4/13 15:19:10 杨俊杰
【设计院及顾问】：改变成   闻锋「上海现代建筑设计研究院有限公司」

2025/3/7 11:30:44 杨俊杰
【授权编号】：改变成   HY-CPJ202308-003
【类型】：改变成   渠道跟进

2025/2/21 15:52:23 杨俊杰
【当前阶段】：改变成   搁置
【当前阶段情况说明】：添加   该项目属于三期，因为资金问题，二期实施进度就有所搁置

2024/12/27 杨俊杰
类型改变为销售重点 
2024/12/6 杨俊杰
类型改变为渠道跟进 
2024/6/24 16:47:28 杨俊杰
【消息】「」该项目属于三期，原先二期代理商福玛已经推进落地，但了解项目实施进度缓慢，业主资金存在问题。三期与闻峰沟通目前没有任何消息，智能化设计完成，具体招标时间不确定，大概率还是原先二期弱电分包单位
2023/11/1 杨俊杰
上海院闻峰负责智能化设计，配套提供设计方案
', 'CPJ202308-003', '2025-04-13', 0, NULL, NULL, '2025-03-07 00:00:00', '2025-04-28 01:00:52.312834', 14);
INSERT INTO public.projects VALUES (192, '华亭宾馆改造', '2024-04-20', '渠道跟进', '销售', '入围', NULL, '上海菁峰设计咨询有限公司', '上海福玛通信信息科技有限公司', NULL, '上海吉拓网络技术有限公司', '失败', '2025/4/13 15:17:51 杨俊杰
【当前阶段】：改变成   失败
【当前阶段情况说明】：改变成   经确认，用户由于预算问题，取消无线对讲系统

2025/2/21 17:13:32 杨俊杰
【完善价格】 206391
2025/2/21 14:24:06 杨俊杰
【当前阶段情况说明】：改变成   与设计确认，原来项目还未正式招标，只是吉托与甲方商务关系较深，基本内定他们，现阶段弱电单位与甲方在盘算智能化招标，同时甲方由于改造，进度比较着急，提前让弱电单位进场配合。按设计反馈智能化招标预计3，4月份，等待招标结果出来之后基本马上就会启动设备采购

2025/2/21 14:13:13 杨俊杰
【出货时间预测】：添加   2025年二季度
【当前阶段情况说明】：添加   该项目经沟通了解项目刚复工，按之前施工计划3月份就应该要启动设备进场，但现在商务推进过程始终没有回应，与现场联系后，对方反馈近期在忙其他的事情，说是到3月份在联系。计划继续跟进，判断是施工进度缓慢导致客户不着急，还是有其他竞争品牌在，利用设计关系也侧边了解情况

2024/12/6 杨俊杰
类型改变为渠道跟进 
45632 邹飞
类型改变为渠道跟进 
2024/12/6 杨俊杰
【阶段变更】招标前->中标

45632 邹飞
【阶段变更】招标前->中标

2024/5/7 12:38:22 杨俊杰
【消息】「」该项目黄攀反馈品牌已经提交给到运作方，项目即将招标，弱电单位可能内定。待项目招标时他会安排我们与弱电单位沟通
45419.5266435185 邹飞
【消息】「」该项目黄攀反馈品牌已经提交给到运作方，项目即将招标，弱电单位可能内定。待项目招标时他会安排我们与弱电单位沟通
2024/5/4 12:37:53 杨俊杰
【阶段变更】品牌植入->招标前
45416.5263078704 邹飞
【阶段变更】品牌植入->招标前
2024/4/20 杨俊杰
配套黄攀提供方案设计及概算报价，推荐全系列和源产品
45402 邹飞
配套黄攀提供方案设计及概算报价，推荐全系列和源产品
', 'CPJ202404-005', '2025-04-13', 0, NULL, NULL, '2024-04-20 00:00:00', '2025-04-28 01:00:52.313893', 14);
INSERT INTO public.projects VALUES (193, '上海东方枢纽国际商务合作区综合查验场工程（E3南）', '2024-11-26', '渠道跟进', '销售', '入围', NULL, '华东建筑设计研究院有限公司', '上海福玛通信信息科技有限公司', NULL, '上海市安装工程集团有限公司-第九分公司', '品牌植入', '2025/4/13 15:09:36 杨俊杰
【分销商】：添加   上海淳泊

2025/4/3 23:26:16 邹飞
【分销商】：添加   上海淳泊

2025/2/21 16:25:38 杨俊杰
【完善价格】 282640
2024/12/27 杨俊杰
类型改变为渠道跟进 
45653 邹飞
类型改变为渠道跟进 
2024/12/6 杨俊杰
类型改变为渠道管理 
45632 邹飞
类型改变为渠道管理 
2024/11/27 12:15:28 杨俊杰
【完善价格】 282642
45623.5107407407 邹飞
【完善价格】 282642
', 'CPJ202411-013', '2025-04-13', 0, NULL, NULL, '2024-11-26 00:00:00', '2025-04-28 01:00:52.314901', 14);
INSERT INTO public.projects VALUES (194, '上海空铁联运', '2024-10-24', '销售重点', '销售', '入围', NULL, '华东建筑设计研究院有限公司', '上海艾亿智能科技有限公司', NULL, '上海市安装工程集团有限公司-第九分公司', '中标', '2025/4/13 15:07:05 杨俊杰
【分销商】：添加   上海瑞康
【系统集成商】：改变成   上海市安装工程集团有限公司-第九分公司

2025/2/21 13:59:37 杨俊杰
【系统集成商】：改变成   上海建工四建集团有限公司

2025/2/21 13:57:15 杨俊杰
【经销商】：添加   上海艾亿智能科技有限公司

2025/2/21 13:57:01 杨俊杰
【系统集成商】：改变成   上海市安装工程集团有限公司-第四分公司
【当前阶段情况说明】：添加   该项目与浦东东站地下同时招标，招标范围包括装饰、机电和智能化，招标结果公布建工四建安装中标。按招标情况判断项目后续与浦东东站地下一致，计划和建工四建安装跟进确认

2024/12/27 杨俊杰
【阶段变更】招标中->中标

2024/12/6 杨俊杰
【阶段变更】品牌植入->招标中
类型改变为销售重点 
2024/10/24 15:57:16 杨俊杰
【完善价格】 153335
', 'SPJ202410-004', '2025-04-13', 0, NULL, NULL, '2024-10-24 00:00:00', '2025-04-28 01:00:52.315921', 14);
INSERT INTO public.projects VALUES (195, '虹桥商务区核心区基础设施配套项目二期', '2024-11-11', '渠道跟进', '经销商', '入围', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '上海建工二建集团有限公司', '失败', '2025/4/13 15:01:54 杨俊杰
【当前阶段情况说明】：改变成   该项目与渠道复核他们跟踪集成商未中标，实际中标单位没有了解到

2025/4/13 15:01:07 杨俊杰
【当前阶段】：改变成   失败
【分销商】：添加   上海瑞康
【当前阶段情况说明】：添加     该项目与渠道复核他们跟踪集成商未中标，实际中标单位没有了解到

2025/4/4 00:13:01 李冬
【完善价格】 184620
2025/4/4 00:11:26 李冬
【面价金额】：改变成   159293

2025/4/4 00:11:09 李冬
【完善价格】 184620
2025/4/3 23:51:04 李冬
【分销商】：添加   上海瑞康

45607.6955324074 李冬
【完善价格】 159293
2024/11/11 16:41:34 杨俊杰
【完善价格】 159293
', 'CPJ202411-005', '2025-04-13', 0, NULL, NULL, '2024-11-11 00:00:00', '2025-04-28 01:00:52.316989', 14);
INSERT INTO public.projects VALUES (196, '城投研究院检测基地建设「XC1-0017单元09街坊09-07号地块 」', '2024-02-20', '渠道跟进', '经销商', '入围', NULL, '上海菁峰设计咨询有限公司', '上海瀚网智能科技有限公司', NULL, NULL, '失败', '2025/4/13 14:59:34 杨俊杰
【当前阶段】：改变成   失败
【当前阶段情况说明】：添加   该项目与渠道复核他们跟踪集成商未中标，实际中标单位没有了解到

2025/3/19 16:31:21 李冬
【当前阶段】：改变成   失败
【当前阶段情况说明】：添加   配合集成商未中标

45589 李冬
类型改变为渠道跟进 
2024/10/24 杨俊杰
类型改变为渠道跟进 
45343.4819791667 李冬
面价金额改变为   194301    
2024/2/21 11:34:03 杨俊杰
面价金额改变为   194301    
45342 李冬
配合菁峰朱逸飞参与项目投标，沟通了解该项目他们帮助上安九分配合建工五建联合投标
2024/2/20 杨俊杰
配合菁峰朱逸飞参与项目投标，沟通了解该项目他们帮助上安九分配合建工五建联合投标
', 'CPJ202402-001', '2025-04-13', 0, NULL, NULL, '2024-02-20 00:00:00', '2025-04-28 01:00:52.318087', 14);
INSERT INTO public.projects VALUES (197, '黄浦区广场社区C010102单元064-01、065-01地块「嘉里金陵东路」', '2025-01-11', '渠道跟进', '经销商', '入围', NULL, '科进柏城咨询有限公司-上海分公司', '上海瀚网智能科技有限公司', NULL, '上海永天科技股份有限公司', '中标', '2025/4/13 14:57:00 杨俊杰
【当前阶段】：改变成   中标
【分销商】：添加   上海瑞康
【经销商】：改变成   上海瀚网智能科技有限公司
【系统集成商】：改变成   上海永天科技股份有限公司
【当前阶段情况说明】：改变成   该项目经了解上海永天中标，目前采购在询价，瀚网张国东在跟进。初步了解通过系统品牌，主要与烈龙在竞争，而永天原先主要合作对象是徐小青，项目方案上没有好的手段，只能通过低价竞争
【类型】：添加   渠道跟进

2025/1/11 15:53:52 杨俊杰
【授权编号】：添加   HY-CPJ202410-009

2025/1/8 12:12:28 杨俊杰
【完善价格】 699054
2025/1/8 11:48:50 杨俊杰
【经销商】：添加   上海福玛通信信息科技有限公司
【系统集成商】：添加   上海申源电子工程技术设备有限公司
【当前阶段情况说明】：添加   该项目渠道福玛陈刘祥报备，配合申源电子参与项目投标。项目入围，主要与烈龙竞争

2024/12/27 杨俊杰
【阶段变更】招标中->失败

2024/12/2 杨俊杰
【阶段变更】->招标中
类型改变为渠道跟进 
2024/12/2 杨俊杰
【阶段变更】品牌植入->
类型改变为 
2024/10/18 10:08:04 杨俊杰
【完善价格】 42304
2024/4/7 杨俊杰
该项目配合柏诚吴恺翔参与招标图设计，项目分为多个地块，本次先启动64和65两个地块，每个地块分为商办和住宅2个业态，有独立运维团队。需要了解设计阶段，邀约业主，推进业务合作，了解招标时间及参与集成商情况
', 'CPJ202410-009', '2025-04-13', 0, NULL, NULL, '2025-01-11 00:00:00', '2025-04-28 01:00:52.319137', 14);
INSERT INTO public.projects VALUES (198, '国际商务合作区E2联检及商务酒店综合体(1366-E2)', '2025-03-07', '渠道跟进', '经销商', '围标', NULL, NULL, '上海福玛通信信息科技有限公司', NULL, '上海市安装工程集团有限公司-第九分公司', '招标中', '2025/4/10 14:22:39 杨俊杰
【出货时间预测】：添加   2025年二季度
【当前阶段】：改变成   招标中
【分销商】：添加   上海淳泊
【经销商】：添加   上海福玛通信信息科技有限公司
【当前阶段情况说明】：添加   该项目分为联检及酒店两个部分，其中联检目前上安九分参与建工平台投标，预计5-6月份完成投标，并与总包建工合同签订，酒店预计本月底启动投标，预计合同签订时间与联检相差不会太多。现场反馈项目实施进度较急，联检及酒店需要提前协助，把天馈有关隐蔽工程提前完成。现阶段深化方案基本确认，价格与上安采购有过初步沟通和确认，代理商在跟进并提前配合执行

2025/4/9 杨俊杰
「张东伟」 上海市安装工程集团有限公司-第九分公司  该项目分为联检及酒店两个部分，其中联检目前上安九分参与建工平台投标，预计5-6月份完成投标，并与总包建工合同签订，酒店预计本月底启动投标，预计合同签订时间与联检相差不会太多。现场反馈项目实施进度较急，联检及酒店需要提前协助，把天馈有关隐蔽工程提前完成。现阶段深化方案基本确认，价格与上安采购有过初步沟通和确认，代理商在跟进并提前配合执行
2025/3/7 11:32:12 杨俊杰
【授权编号】：改变成   HY-CPJ202406-017
【类型】：改变成   渠道跟进

2025/2/21 17:11:13 杨俊杰
【完善价格】 383859
2024/12/27 杨俊杰
类型改变为渠道跟进 
2024/12/6 杨俊杰
类型改变为渠道管理 
2024/6/17 杨俊杰
渠道陈刘祥反馈该项目上安参与项目设计，配套提供设计方案，并与上安沟通他们已经帮助提交系统品牌，主设备为摩托罗拉、海能达及和源，天馈分布为和源、瀚网及淳泊。经了解设计院为华东院，张航负责智能化设计。计划通过张航了解项目情况，跟踪招标品牌
', 'CPJ202406-017', '2025-04-10', 0, NULL, NULL, '2025-03-07 00:00:00', '2025-04-28 01:00:52.320166', 14);
INSERT INTO public.projects VALUES (200, '龙阳路04地块', '2025-03-13', '渠道跟进', '渠道', '入围', NULL, '奥雅纳工程咨询(上海)有限公司', '上海艾亿智能科技有限公司', NULL, NULL, '品牌植入', '2025/4/10 13:36:43 杨俊杰
【完善价格】 1284277
2025/4/10 杨俊杰
「梅小好」 上海艾亿智能科技有限公司  与梅小好沟通反馈有集成商挂靠九分资质，通过初步复核品牌的确可控，但参与集成商通过九分关系了解到并没有参考招标品牌，用的是浙江尧起，将次情况让梅小好复核集成商信息，判断用户除了品牌招标在可控范围内以外，是否有能力可以掌控集成商。项目预计二季度招标，潜在参与集成商：信业、中建电子、益邦及万安都有可能参与，待项目正式招标，了解参与集成商具体情况
2025/3/13 14:08:22 杨俊杰
【授权编号】：添加   HY-CPJ202502-018
【类型】：添加   渠道跟进

', 'CPJ202502-018', '2025-04-10', 0, NULL, NULL, '2025-03-13 00:00:00', '2025-04-28 01:00:52.322208', 14);
INSERT INTO public.projects VALUES (201, '浦江永久实验室', '2024-05-20', '渠道跟进', '销售', '围标', NULL, '同济大学建筑设计研究院（集团）有限公司', '上海瀚网智能科技有限公司', NULL, '上海奔逸智能科技有限公司', '中标', '2025/4/8 杨俊杰
「徐良健」 上海奔逸智能科技有限公司  与代理商一同拜访奔逸总经理徐良健，沟通浦江永久实验室，判断代理商与集成商商务合作关系。目前项目建筑结构部分还未封顶，现场仅在做管线预埋，设备进场预计在今年三季度，整体交付要到明年。商务方面给与总价控制范围，基本双方合作没有太大问题
2025/3/28 15:52:32 李冬
【面价金额】：改变成   855371

2025/2/28 14:41:59 杨俊杰
【出货时间预测】：添加   2025年四季度

45704.6501967593 李冬
【设计院及顾问】：改变成   唐平「同济大学建筑设计研究院（集团）有限公司」

2025/2/16 15:36:17 杨俊杰
【设计院及顾问】：改变成   唐平「同济大学建筑设计研究院（集团）有限公司」

45653 李冬
类型改变为销售重点 
2024/12/27 杨俊杰
类型改变为销售重点 
45632 李冬
类型改变为渠道管理 
2024/12/6 杨俊杰
类型改变为渠道管理 
45555.6786458333 李冬
【完善价格】 1169105
2024/9/20 16:17:15 杨俊杰
【完善价格】 1169105
45534.5502314815 李冬
【阶段变更】招标前->中标

2024/8/30 13:12:20 杨俊杰
【阶段变更】招标前->中标

45534.5495486111 李冬
【消息】「」该项目渠道反馈华融以上安九分的身份中标，目前在对外询价复核成本，项目进度还早，土建还未完成，项目预计明年才会启动设备采购
2024/8/30 13:11:21 杨俊杰
【消息】「」该项目渠道反馈华融以上安九分的身份中标，目前在对外询价复核成本，项目进度还早，土建还未完成，项目预计明年才会启动设备采购
45441.640462963 李冬
【消息】「」与渠道沟通了解项目基本上安中标，项目负责人余智飞，另外上安提到业主引荐一家弱电单位华融，我们的系统由他们负责采购
2024/5/29 15:22:16 杨俊杰
【消息】「」与渠道沟通了解项目基本上安中标，项目负责人余智飞，另外上安提到业主引荐一家弱电单位华融，我们的系统由他们负责采购
45432 李冬
与上安梁晓君沟通了解品牌目前按我们所推动的方向，和源围标，主设备品牌入围，项目预计本月底下月初招标，弱电参与单位按上安反馈他们全部掌控
2024/5/20 杨俊杰
与上安梁晓君沟通了解品牌目前按我们所推动的方向，和源围标，主设备品牌入围，项目预计本月底下月初招标，弱电参与单位按上安反馈他们全部掌控
', 'CPJ202405-009', '2025-04-08', 0, NULL, NULL, '2024-05-20 00:00:00', '2025-04-28 01:00:52.323166', 14);
INSERT INTO public.projects VALUES (202, '华兴新城项目8-01地块', '2024-06-20', '渠道跟进', '经销商', '围标', NULL, NULL, '上海艾亿智能科技有限公司', NULL, '上海银欣高新技术发展股份有限公司', '中标', '2025/3/29 13:00:23 杨俊杰
【出货时间预测】：改变成   2025年四季度

2025/2/21 17:12:25 杨俊杰
【完善价格】 450368
2025/2/21 15:16:34 杨俊杰
【出货时间预测】：改变成   2025年二季度

2024/9/20 杨俊杰
【阶段变更】招标中->中标

2024/6/20 14:02:54 杨俊杰
【消息】「」该项目梅小好作为合作伙伴，与业主建立合作，植入招标品牌。奥雅纳作为机电顾问，智能化设计由江森负责，项目招标，品牌入围，经合作伙伴梅小好反馈项目预计有6-7家报名参与,目前已配合两家在参与项目投标
', 'CPJ202406-009', '2025-03-29', 0, NULL, NULL, '2024-06-20 00:00:00', '2025-04-28 01:00:52.324139', 14);
INSERT INTO public.projects VALUES (203, '虹口区117街坊HK366-01地块
新建学校项目（不含桩基）', '2024-08-20', '渠道跟进', '销售', '围标', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '上海仪电鑫森科技发展有限公司', '中标', '2025/3/29 12:58:06 杨俊杰
【出货时间预测】：改变成   2026年一季度

2025/2/28 14:43:54 杨俊杰
【出货时间预测】：改变成   2025年三季度

2025/2/21 16:37:48 杨俊杰
【完善价格】 176058
45555.6761342593 李冬
【完善价格】 180358
2024/9/20 16:13:38 杨俊杰
【完善价格】 180358
45555.6737037037 李冬
【完善价格】 176034
2024/9/20 16:10:08 杨俊杰
【完善价格】 176034
45540.5781018519 李冬
【消息】「」该项目渠道反馈目前在配合仪电鑫森初步深化，深化方案需大总包及设计院确认。项目整体进度较早，现在还在打桩，项目计划2026年9月开学，预计明年弱电才会启动施工
类型改变为  渠道跟进 
2024/9/5 13:52:28 杨俊杰
【消息】「」该项目渠道反馈目前在配合仪电鑫森初步深化，深化方案需大总包及设计院确认。项目整体进度较早，现在还在打桩，项目计划2026年9月开学，预计明年弱电才会启动施工
类型改变为  渠道跟进 
45540.5775 李冬
类型改变为  销售重点 
2024/9/5 13:51:36 杨俊杰
类型改变为  销售重点 
45534.5524189815 李冬
【消息】「」该项目渠道反馈仪电鑫森中标，但项目进度较早，还在土建阶段，他们与仪电鑫森沟通确认设备采购需要到明年
【阶段变更】招标中->中标
2024/8/30 13:15:29 杨俊杰
【消息】「」该项目渠道反馈仪电鑫森中标，但项目进度较早，还在土建阶段，他们与仪电鑫森沟通确认设备采购需要到明年
【阶段变更】招标中->中标
45441.6149189815 李冬
【消息】「」与渠道建议对讲机品牌替换为和源，经确认目前品牌已经替换成功，将摩托罗拉、海能达、建伍改为和源、瀚网及福玛。项目于下月开标，基本仪电鑫森中标
2024/5/29 14:45:29 杨俊杰
【消息】「」与渠道建议对讲机品牌替换为和源，经确认目前品牌已经替换成功，将摩托罗拉、海能达、建伍改为和源、瀚网及福玛。项目于下月开标，基本仪电鑫森中标
45436 李冬
渠道反馈该项目仪电鑫森范荃报备，配合清单报价，品牌按其所述为摩托、建伍及海能达，与其沟通建议替换为和源
2024/5/24 杨俊杰
渠道反馈该项目仪电鑫森范荃报备，配合清单报价，品牌按其所述为摩托、建伍及海能达，与其沟通建议替换为和源
', 'CPJ202408-009', '2025-03-29', 0, NULL, NULL, '2024-08-20 00:00:00', '2025-04-28 01:00:52.325073', 14);
INSERT INTO public.projects VALUES (204, '张江人工智能岛', '2022-11-10', '渠道跟进', '销售', '围标', NULL, '上海现代建筑设计研究院有限公司', '上海瀚网智能科技有限公司', NULL, '上海壹杰信息技术有限公司', '中标', '2025/3/29 12:57:11 杨俊杰
【设计院及顾问】：改变成   上海现代建筑设计研究院有限公司

2025/2/28 14:50:48 杨俊杰
【出货时间预测】：添加   2025年四季度

2025/2/21 16:36:50 杨俊杰
【完善价格】 1273122
45653 李冬
类型改变为销售重点 
2024/12/27 杨俊杰
类型改变为销售重点 
45555.6808680556 李冬
【完善价格】 1283599
2024/9/20 16:20:27 杨俊杰
【完善价格】 1283599
45534.5383912037 李冬
【消息】「」该项目进度缓慢，目前渠道在跟进配套深化方案，按集成商反馈项目要到明年才会启动，与渠道商议推进主设备品牌由摩托罗拉替换为和源
2024/8/30 12:55:17 杨俊杰
【消息】「」该项目进度缓慢，目前渠道在跟进配套深化方案，按集成商反馈项目要到明年才会启动，与渠道商议推进主设备品牌由摩托罗拉替换为和源
45419.5715162037 李冬
【消息】「」该项目渠道瑞康反馈他通过奂源现场的关系了解到无线对讲系统中标价格含施工200万+，目前还没决定系统到底如何分配
2024/5/7 13:42:59 杨俊杰
【消息】「」该项目渠道瑞康反馈他通过奂源现场的关系了解到无线对讲系统中标价格含施工200万+，目前还没决定系统到底如何分配
45362.5043634259 李冬
该项目据业主反馈壹杰中标，经了解壹杰与另外两家计划共同消化，目前具体如何分配还未定夺
2024/3/11 12:06:17 杨俊杰
该项目据业主反馈壹杰中标，经了解壹杰与另外两家计划共同消化，目前具体如何分配还未定夺
45362.5021990741 李冬
「阶段变更」
2024/3/11 12:03:10 杨俊杰
「阶段变更」
45231 李冬
项目为办公园区，建筑面积6.6万方，业主方为张江国信安，庄彦负责智能化设计，设计单位：上海院，负责图纸设计，机电顾问：奥雅纳，负责招标技术要求和品牌推荐
2023/11/1 杨俊杰
项目为办公园区，建筑面积6.6万方，业主方为张江国信安，庄彦负责智能化设计，设计单位：上海院，负责图纸设计，机电顾问：奥雅纳，负责招标技术要求和品牌推荐
', 'CPJ202211-008', '2025-03-29', 0, NULL, NULL, '2022-11-10 00:00:00', '2025-04-28 01:00:52.326033', 14);
INSERT INTO public.projects VALUES (205, '上海嘉定集成电路研发中心增补', '2025-02-28', '渠道跟进', '渠道', '入围', NULL, NULL, '上海福玛通信信息科技有限公司', NULL, '上海谌亚智能化系统有限公司', '签约', '2025/3/29 12:56:14 杨俊杰
[阶段变更] ->签约
2025/3/4 11:31:06 杨俊杰
【完善价格】 117500
2025/2/28 13:40:11 杨俊杰
【完善价格】 142501
2025/2/28 13:37:16 杨俊杰
【授权编号】：添加   HY-CPJ202502-012
【类型】：添加   渠道跟进

', 'CPJ202502-012', '2025-03-29', 0, NULL, NULL, '2025-02-28 00:00:00', '2025-04-28 01:00:52.327005', 14);
INSERT INTO public.projects VALUES (206, '济南市黄冈路穿黄隧道', '2025-03-29', '渠道跟进', '销售', '入围', NULL, '上海市政工程设计研究总院（集团）有限公司', NULL, NULL, NULL, '品牌植入', '2025/3/29 12:50:13 杨俊杰
【授权编号】：添加   HY-CPJ202503-018
【类型】：添加   渠道跟进

', 'CPJ202503-018', '2025-03-29', 0, NULL, NULL, '2025-03-29 00:00:00', '2025-04-28 01:00:52.328002', 14);
INSERT INTO public.projects VALUES (207, '上海东站站前区A3-01地块', '2025-03-13', '渠道跟进', '销售', '入围', NULL, '上海现代建筑设计研究院有限公司', '上海艾亿智能科技有限公司', NULL, NULL, '品牌植入', '2025/3/21 11:01:47 杨俊杰
【设计院及顾问】：添加   上海现代建筑设计研究院有限公司

2025/3/13 14:08:03 杨俊杰
【授权编号】：添加   HY-CPJ202502-019
【类型】：添加   渠道跟进

', 'CPJ202502-019', '2025-03-21', 0, NULL, NULL, '2025-03-13 00:00:00', '2025-04-28 01:00:52.32898', 14);
INSERT INTO public.projects VALUES (208, '马来西亚万国数据中心', '2025-03-05', '渠道跟进', '渠道', '入围', NULL, NULL, '上海福玛通信信息科技有限公司', NULL, NULL, '签约', '2025/3/14 14:03:15 杨俊杰
[阶段变更] ->签约
2025/3/5 15:01:59 杨俊杰
【授权编号】：添加   HY-CPJ202503-001

', 'CPJ202503-001', '2025-03-14', 0, NULL, NULL, '2025-03-05 00:00:00', '2025-04-28 01:00:52.329961', 14);
INSERT INTO public.projects VALUES (210, '国际旅游度假区北片区01-06地块', '2025-03-07', '渠道跟进', '销售', '入围', NULL, '华东建筑设计研究院有限公司', NULL, NULL, NULL, '品牌植入', '2025/3/7 11:32:39 杨俊杰
【授权编号】：改变成   HY-CPJ202405-015
【类型】：改变成   渠道跟进

', 'CPJ202405-015', '2025-03-07', 0, NULL, NULL, '2025-03-07 00:00:00', '2025-04-28 01:00:52.33186', 14);
INSERT INTO public.projects VALUES (211, '开封火车站前综合交通枢纽工程勘查设计商业', '2025-03-07', '渠道跟进', '销售', '入围', NULL, '上海市政工程设计研究总院（集团）有限公司', NULL, NULL, NULL, '品牌植入', '2025/3/7 11:31:09 杨俊杰
【授权编号】：改变成   HY-CPJ202408-017
【类型】：改变成   渠道跟进

', 'CPJ202408-017', '2025-03-07', 0, NULL, NULL, '2025-03-07 00:00:00', '2025-04-28 01:00:52.33275', 14);
INSERT INTO public.projects VALUES (212, '上海福瑞科技有限公司', '2025-01-08', '渠道跟进', '经销商', '入围', NULL, '信息产业电子第十一设计研究院科技工程
股份有限公司-上海分公司', '上海瀚网智能科技有限公司', NULL, '上海宝通汎球电子有限公司', '中标', '2025/2/28 14:42:37 杨俊杰
【出货时间预测】：添加   2025年二季度

2025/2/28 13:41:48 邹飞
【授权编号】：添加   HY-CPJ202501-004
【类型】：添加   渠道跟进

2025/2/21 16:21:31 杨俊杰
【完善价格】 185886
2025/2/21 16:20:47 杨俊杰
【完善价格】 199249
45694.5170949074 李冬
【当前阶段情况说明】：改变成   该项目宝通中标，原先霆锋计算机计划与他们合作，但由于中标价格较低，所以交还给宝通，由他们自己负责采购。现阶段宝通在复核成本，找到李冬进行报价，经了解李冬原先与宝通有过业务合作

2025/2/6 12:24:37 杨俊杰
【当前阶段情况说明】：改变成   该项目宝通中标，原先霆锋计算机计划与他们合作，但由于中标价格较低，所以交还给宝通，由他们自己负责采购。现阶段宝通在复核成本，找到李冬进行报价，经了解李冬原先与宝通有过业务合作

45694.5154861111 李冬
【当前阶段】：改变成   中标
【分销商】：改变成   上海瑞康
【经销商】：改变成   上海瀚网智能科技有限公司

2025/2/6 12:22:18 杨俊杰
【当前阶段】：改变成   中标
【分销商】：改变成   上海瑞康
【经销商】：改变成   上海瀚网智能科技有限公司

2025/1/17 11:43:23 李华伟
【完善价格】 200942
2025/1/11 14:33:34 李华伟
【授权编号】：改变成   HY-CPJ202501-004
【类型】：添加   渠道跟进

45665.4812962963 李冬
【设计院及顾问】：添加   信息产业电子第十一设计研究院科技工程
股份有限公司-上海分公司
【分销商】：添加   上海淳泊
【当前阶段情况说明】：改变成   该项目渠道福玛陈刘祥报备，配合霆锋林昌麒参与项目投标，经了解无线对讲系统没有品牌设定，他们以宝通汎球身份参与投标
【类型】：添加   渠道跟进

2025/1/8 11:33:04 杨俊杰
【设计院及顾问】：添加   信息产业电子第十一设计研究院科技工程
股份有限公司-上海分公司
【分销商】：添加   上海淳泊
【当前阶段情况说明】：改变成   该项目渠道福玛陈刘祥报备，配合霆锋林昌麒参与项目投标，经了解无线对讲系统没有品牌设定，他们以宝通汎球身份参与投标
【类型】：添加   渠道跟进

45665.4808796296 李冬
【授权编号】：改变成   HY-CPJ202501-004

2025/1/8 11:32:28 杨俊杰
【授权编号】：改变成   HY-CPJ202501-004

', 'CPJ202501-004', '2025-02-28', 0, NULL, NULL, '2025-01-08 00:00:00', '2025-04-28 01:00:52.333643', 14);
INSERT INTO public.projects VALUES (213, '国际体操馆', '2023-10-30', '渠道跟进', '经销商', '入围', NULL, '上海维瓴智能科技有限公司', '上海瀚网智能科技有限公司', NULL, '上海仪电鑫森科技发展有限公司', '中标', '2025/2/28 14:41:16 杨俊杰
【出货时间预测】：添加   2025年四季度

45534.5436574074 李冬
【消息】「」该项目渠道反馈仪电鑫森中标，但项目进度比较慢，建筑还未完成，项目实际启动预计需要到明年
2024/8/30 13:02:52 杨俊杰
【消息】「」该项目渠道反馈仪电鑫森中标，但项目进度比较慢，建筑还未完成，项目实际启动预计需要到明年
45450.5319791667 李冬
【消息】「」该项目仪电鑫森中标，但经了解项目建筑还在实施过程，明确弱电智能化要明年才会启动
2024/6/7 12:46:03 杨俊杰
【消息】「」该项目仪电鑫森中标，但经了解项目建筑还在实施过程，明确弱电智能化要明年才会启动
45419.5486458333 李冬
【消息】「」渠道反馈仪电鑫森宋振兴告知目前合同还在双签过程，具体时间还无法确定，主要因为总包管理费收取标准太高，还在洽谈过程中
2024/5/7 13:10:03 杨俊杰
【消息】「」渠道反馈仪电鑫森宋振兴告知目前合同还在双签过程，具体时间还无法确定，主要因为总包管理费收取标准太高，还在洽谈过程中
45416.5466782407 李冬
【阶段变更】品牌植入->中标
2024/5/4 13:07:13 杨俊杰
【阶段变更】品牌植入->中标
45231 李冬
该项目维瓴通过业主提前拿到设计资料，提前安排渠道技术配套，复核设计资料，并给予招标清单及报价概算。通过维瓴了解品牌负责情况，推动植入和源全系列产品。
2023/11/1 杨俊杰
该项目维瓴通过业主提前拿到设计资料，提前安排渠道技术配套，复核设计资料，并给予招标清单及报价概算。通过维瓴了解品牌负责情况，推动植入和源全系列产品。
', 'CPJ202310-004', '2025-02-28', 0, NULL, NULL, '2023-10-30 00:00:00', '2025-04-28 01:00:52.334696', 14);
INSERT INTO public.projects VALUES (214, '浦东东站能源中心', '2024-09-24', '销售重点', '销售', '入围', NULL, '华东建筑设计研究院有限公司', NULL, NULL, NULL, '失败', '2025/2/28 14:18:37 杨俊杰
【当前阶段】：改变成   失败
【当前阶段情况说明】：添加   该项目与黄辰贇沟通了解，项目体量较小，用户取消无线对讲系统，原先是因为考虑东站人员到了能源中心能够保持对讲机通信，但现在用户实际并不需要

2024/12/27 杨俊杰
类型改变为销售重点 
2024/9/24 15:42:01 杨俊杰
【完善价格】 93962
', 'SPJ202409-011', '2025-02-28', 0, NULL, NULL, '2024-09-24 00:00:00', '2025-04-28 01:00:52.335741', 14);
INSERT INTO public.projects VALUES (215, '虹桥天合光能总部', '2024-01-15', '销售重点', '销售', '入围', '天合光能股份有限公司', '华东建筑设计研究院有限公司', NULL, NULL, NULL, '品牌植入', '2025/2/21 17:07:22 杨俊杰
【完善价格】 587550
2024/12/27 杨俊杰
类型改变为销售重点 
2024/7/4 14:33:20 杨俊杰
【消息】「」该项目配合华东院周天文设计，计划植入全系列和源产品。招标文件及品牌预计9-10月份启动
【阶段变更】发现->品牌植入
2024/3/20 16:18:00 杨俊杰
该项目华东院周天文负责智能化专项，项目整体为12万方，分为六栋建筑，与虹桥希尔顿为同一个业主负责。目前再平台搭建，项目预计6月份启动招标图设计。需要跟进推动设计配套，推动消防系统、平台服务方案和全系列品牌入围
2024/3/20 16:15:29 杨俊杰
「阶段变更」
2023/11/1 杨俊杰
该项目与华东院周天文沟通了解现在还在方案汇报，预计春节后启动图纸设计，此项目与虹桥希尔顿的业主为同一个
', 'SPJ202401-002', '2025-02-21', 0, NULL, NULL, '2024-01-15 00:00:00', '2025-04-28 01:00:52.336761', 14);
INSERT INTO public.projects VALUES (216, '开封火车站前综合交通枢纽工程勘查设计商业', '2024-08-07', '销售重点', '销售', '入围', NULL, '上海市政工程设计研究总院（集团）有限公司', NULL, NULL, NULL, '品牌植入', '2025/2/21 16:39:51 杨俊杰
【完善价格】 181283
2024/12/27 杨俊杰
类型改变为销售重点 
2024/12/6 杨俊杰
【阶段变更】招标中->品牌植入

', 'SPJ202408-001', '2025-02-21', 0, NULL, NULL, '2024-08-07 00:00:00', '2025-04-28 01:00:52.33762', 14);
INSERT INTO public.projects VALUES (217, '嘉定区嘉定新城主城区JDC11201单元26-04地块', '2024-10-08', '渠道跟进', '经销商', '入围', NULL, NULL, '上海艾亿智能科技有限公司', NULL, '上海电器科学研究所集团有限公司', '招标中', '2025/2/21 16:29:49 杨俊杰
【完善价格】 137091
2024/10/8 13:04:07 杨俊杰
【完善价格】 140961
', 'CPJ202410-002', '2025-02-21', 0, NULL, NULL, '2024-10-08 00:00:00', '2025-04-28 01:00:52.338535', 14);
INSERT INTO public.projects VALUES (218, '北京西路1399号信达大厦', '2024-11-26', '销售重点', '销售', '入围', NULL, '上海现代建筑设计研究院有限公司', NULL, NULL, NULL, '品牌植入', '2025/2/21 16:23:56 杨俊杰
【完善价格】 285403
2024/12/27 14:18:21 杨俊杰
【完善价格】 285405
2024/12/27 杨俊杰
类型改变为销售重点 
', 'SPJ202411-013', '2025-02-21', 0, NULL, NULL, '2024-11-26 00:00:00', '2025-04-28 01:00:52.339394', 14);
INSERT INTO public.projects VALUES (219, '九星城项目', '2022-11-14', '渠道跟进', '销售', '围标', NULL, '卓展工程顾问(北京)有限公司-上海分公司', '上海福玛通信信息科技有限公司', NULL, '上海蓝极星智能科技有限公司', '中标', '2025/2/21 15:02:33 杨俊杰
【出货时间预测】：添加   2025年二季度
【系统集成商】：改变成   宋治军「上海蓝极星智能科技有限公司」
【当前阶段情况说明】：添加   该项目分为三个标段，其中一标段中标单位：江苏金鼎，二标段中标单位：蓝极星（景文同安拆分的专做智能化），三标段中标单位：中邮建，品牌为天馈入围，和源通信，瀚网及威升。目前二标段在渠道付言新引荐下与蓝极星负责人宋总有过沟通，借用付言新与宋治军关系，初步达成合作意向，提交推进品牌锁定。一、三标段由于公开招标，中标单位投了超低价格，一直没有任何消息。同时通过蓝极星及其他渠道了解，苏州中瀚和杨顺凯在合作，以苏州威升名义在与我们竞争，通过蓝极星宋治军了解价格很低，同时三标段有个圆信询价至李冬，经了解在此之前就是有人用威升再配合。与卓展李霄云了解，业主还是希望各个标段品牌同一，目前再配合付言新提供各个标段接口要求统一说明。计划先推进二标段锁定品牌后在跟进一三标段，看商务如何报价。项目原定计划延迟至今年底，预计二标段2季度，3季度才会落实商务

2024/12/27 杨俊杰
类型改变为渠道跟进 
45653 邹飞
类型改变为渠道跟进 
2024/10/8 杨俊杰
【阶段变更】招标中->中标

45573 邹飞
【阶段变更】招标中->中标

2024/9/5 12:53:06 杨俊杰
【消息】「」本项目正式招标，目前拆分为三个标段，其中一，三标段为公开招标，渠道及我们都在配合，而二标段在集成商上有一定限制要求，所以仅7家参与，主要是上安。所有标段都是本月开标，核心抓住二标段机房部分，其余都需接入至二标段
【阶段变更】招标前->招标中
45540.536875 邹飞
【消息】「」本项目正式招标，目前拆分为三个标段，其中一，三标段为公开招标，渠道及我们都在配合，而二标段在集成商上有一定限制要求，所以仅7家参与，主要是上安。所有标段都是本月开标，核心抓住二标段机房部分，其余都需接入至二标段
【阶段变更】招标前->招标中
2024/3/20 16:42:24 杨俊杰
「阶段变更」
45371.6961111111 邹飞
「阶段变更」
2023/11/1 杨俊杰
前期方案阶段前期设计，配套设计方案
45231 邹飞
前期方案阶段前期设计，配套设计方案
', 'CPJ202211-009', '2025-02-21', 0, NULL, NULL, '2022-11-14 00:00:00', '2025-04-28 01:00:52.340251', 14);
INSERT INTO public.projects VALUES (220, '五粮液技术研究中心', '2025-02-10', '渠道跟进', '销售', '入围', NULL, '华东建筑设计研究院有限公司', NULL, NULL, NULL, '品牌植入', '2025/2/10 11:03:48 杨俊杰
【授权编号】：添加   HY-CPJ202502-004
【类型】：添加   渠道跟进

', 'CPJ202502-004', '2025-02-10', 0, NULL, NULL, '2025-02-10 00:00:00', '2025-04-28 01:00:52.34115', 14);
INSERT INTO public.projects VALUES (221, '南大104-02、105-01、02、106-01', '2025-01-06', '销售重点', '销售', '入围', '上海临港经济发展（集团）有限公司', '华东建筑设计研究院有限公司', NULL, NULL, NULL, '品牌植入', '2025/2/6 12:08:41 杨俊杰
【设计院及顾问】：改变成   周天文「华东建筑设计研究院有限公司」
【直接用户】：改变成   张小宁「上海临港经济发展（集团）有限公司」

2025/1/6 16:08:38 杨俊杰
【授权编号】：添加   HY-SPJ202411-015
【类型】：添加   销售重点

', 'SPJ202411-015', '2025-02-06', 0, NULL, NULL, '2025-01-06 00:00:00', '2025-04-28 01:00:52.34203', 14);
INSERT INTO public.projects VALUES (222, '徐汇区华泾镇XHPO-0001单元D5D-1地块', '2025-01-11', '销售重点', '销售', '入围', NULL, '华东建筑设计研究院有限公司', NULL, NULL, NULL, '品牌植入', '2025/1/11 15:56:20 杨俊杰
【授权编号】：添加   HY-SPJ202406-004

', 'SPJ202406-004', '2025-01-11', 0, NULL, NULL, '2025-01-11 00:00:00', '2025-04-28 01:00:52.342911', 14);
INSERT INTO public.projects VALUES (223, '苏州工业园区20230499地块', '2024-06-20', '销售重点', '销售', '入围', NULL, '科进柏城咨询有限公司-上海分公司', NULL, NULL, NULL, '品牌植入', '2024/12/27 杨俊杰
类型改变为销售重点 
2024/11/11 16:02:40 杨俊杰
【完善价格】 745483
2024/6/20 杨俊杰
该项目配合华东院陈未参与设计配套，项目分为两个地块，陈未是负责其中一个，另一个由毛晶轶负责，总体设计负责人为王小安。经了解甲方有自己品牌库，和源入围，主要与中瀚竞争
', 'SPJ202406-003', '2024-12-27', 0, NULL, NULL, '2024-06-20 00:00:00', '2025-04-28 01:00:52.343772', 14);
INSERT INTO public.projects VALUES (224, '联影智慧医疗园', '2022-12-12', '渠道跟进', '销售', '围标', NULL, NULL, '上海鑫桉信息工程有限公司', NULL, '上海云思智慧信息技术有限公司', '签约', '2024/12/27 杨俊杰
【阶段变更】中标->签约

2024/8/30 12:43:14 杨俊杰
【消息】「」该项目配套云思推进信道机及对讲机锁定和源品牌，按云思现场反馈现阶段在和业主确认方案和所选品牌，并和云思商议在锁定品牌的情况，增补对讲机数量
2024/8/18 12:46:00 杨俊杰
【消息】「」云思中标，项目经理已经进场，目前主要在深化方案确认，渠道福玛在跟进对接。商务方面根据云思内部业务流程，需根据投标报价优惠一轮价格给到销售，商务方面根据现场沟通反馈的实施进度，预计今年年底会发起采购流程
跟进记录 杨俊杰
【阶段变更】招标中->中标
2024/3/20 16:38:36 杨俊杰
「阶段变更」
该项目招标，渠道配合提供投标
2023/11/1 杨俊杰
项目位于长宁临空，总建设面积约17万平方米。云思与建筑合作，负责智能化设计
', 'CPJ202212-002', '2024-12-27', 0, NULL, NULL, '2022-12-12 00:00:00', '2025-04-28 01:00:52.344756', 14);
INSERT INTO public.projects VALUES (225, '前滩华尔道夫', '2023-09-18', '渠道跟进', '销售', '入围', NULL, '沈麦韦(上海)商务咨询有限公司', NULL, NULL, '苏州朗捷通智能科技有限公司', '失败', '2024/12/27 杨俊杰
【阶段变更】招投标->失败

2023/11/1 杨俊杰
该项目招标，品牌入围，亦朗在内，参与集成商：上海凯通、上海行余
该项目为陆家嘴开发建设，声美华作为项目顾问，目前根据酒馆要求，结合项目预算，设计为常规系统
', 'CPJ202309-005', '2024-12-27', 0, NULL, NULL, '2023-09-18 00:00:00', '2025-04-28 01:00:52.345682', 14);
INSERT INTO public.projects VALUES (226, '国际旅游度假区北片区01-06地块', '2024-05-24', '销售重点', '销售', '入围', NULL, '华东建筑设计研究院有限公司', NULL, NULL, NULL, '品牌植入', '2024/12/27 杨俊杰
类型改变为销售重点 
2024/5/24 杨俊杰
该项目华东院李源报备，配合提供初步设计。项目精装还未确定，目前图纸设计目的用于施工图报审，获取施工许可证
', 'SPJ202405-001', '2024-12-27', 0, NULL, NULL, '2024-05-24 00:00:00', '2025-04-28 01:00:52.346557', 14);
INSERT INTO public.projects VALUES (227, '谈家渡苏河坊', '2023-02-28', '销售重点', '销售', '入围', NULL, '华东建筑设计研究院有限公司', NULL, NULL, NULL, '发现', '2024/12/27 杨俊杰
类型改变为销售重点 
2024/3/20 16:41:07 杨俊杰
「阶段变更」
2023/11/1 杨俊杰
该项目华东院反馈上海报业退出，由兴业银行接手，现阶段重新汇报智能化方案，跟进了解项目设计进度
', 'SPJ202302-002', '2024-12-27', 0, NULL, NULL, '2023-02-28 00:00:00', '2025-04-28 01:00:52.347446', 14);
INSERT INTO public.projects VALUES (228, '重庆协和医院', '2024-11-26', '渠道跟进', '经销商', '入围', NULL, NULL, '北京佰沃信通科技有限公司', NULL, '中国建筑第八工程局有限公司', '签约', '2024/12/6 杨俊杰
【阶段变更】中标->签约

2024/11/29 16:11:48 杨俊杰
【完善价格】 531084
2024/11/26 15:30:51 杨俊杰
【完善价格】 521946
', 'CPJ202411-012', '2024-12-06', 0, NULL, NULL, '2024-11-26 00:00:00', '2025-04-28 01:00:52.348306', 14);
INSERT INTO public.projects VALUES (229, '浦东东站地道工程', '2024-02-26', '销售重点', '销售', '围标', NULL, '上海市政工程设计研究总院（集团）有限公司', NULL, NULL, NULL, '品牌植入', '2024/3/20 16:00:18 杨俊杰
市政院王微微反馈施工图已经送审，下一阶段进入招标前准备，但这部分由招标代理完成，按她所述招标代理会咨询他们建议，与其沟通是否可以引荐招标代理，锁定和源品牌，并提供技术要求
2024/2/26 12:04:15 杨俊杰
面价金额改变为   1215837    
2024/2/26 11:03:47 杨俊杰
设计方改变为  上海市政工程设计研究总院「集团」有限公司    
该项目市政院王微微负责设计，项目分为站东路和站前路两条隧道，配套参与项目设计
', 'SPJ202402-003', '2024-10-24', 0, NULL, NULL, '2024-02-26 00:00:00', '2025-04-28 01:00:52.349117', 14);
INSERT INTO public.projects VALUES (230, '松江站服务中心', '2024-08-20', '销售重点', '销售', '围标', NULL, NULL, '无', NULL, '中铁二局建设有限公司', '签约', '2024/9/21 15:54:18 杨俊杰
[阶段变更] ->签约
2024/9/5 13:50:16 杨俊杰
【消息】「」该项目中铁二局内部告知我们中标，现场进度较急，计划今年12月份交付运营。现阶段需要通过盛建国与三吉电子对接，并与中铁二局商议商务付款
【阶段变更】招标中->中标
2024/8/20 12:24:54 杨俊杰
【消息】「」该项目盛建国介绍，他利用公安和消防的关系把控整个业务。现阶段中铁二局挂网招标，一共三家参与，我们、三吉和瀚网，等待中标公布结果。与现场沟通了解已经具备实施条件，就等招标完成后商务确定就需要启动设备供货
', 'SPJ202408-003', '2024-09-21', 0, NULL, NULL, '2024-08-20 00:00:00', '2025-04-28 01:00:52.349935', 14);
INSERT INTO public.projects VALUES (231, '深圳市星河智善科技有限公司集采', '2025-03-25', '渠道跟进', '渠道', '入围', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '深圳市星河智善科技有限公司', '中标', '2025/4/25 16:31:24 周裔锦
【当前阶段】：改变成   中标

2025/4/25 16:30:49 周裔锦
【当前阶段情况说明】：改变成   业主介绍，最快5月份会有部分产品采购。

2025/4/25 14:58:07 周裔锦
【出货时间预测】：添加   2025年二季度5月份
【当前阶段情况说明】：改变成   科技介绍，最快5月份会有部分产品采购。

2025/3/25 21:52:33 周裔锦
【当前阶段情况说明】：改变成   本次参与集采品牌：英智源、侨讯、京昊丰科、和源。以邀标形式招标，目前还在议价中。

2025/3/25 21:52:00 周裔锦
【当前阶段】：改变成   招标中
【授权编号】：添加   HY-CPJ202503-025
【类型】：添加   渠道跟进

2025/2/22 02:28:26 周裔锦
【完善价格】 2215227
2025/2/22 02:16:00 周裔锦
【系统集成商】：添加   深圳市星河智善科技有限公司

', 'CPJ202503-025', '2025-04-25', 0, NULL, NULL, '2025-03-25 00:00:00', '2025-04-28 01:02:04.944885', 17);
INSERT INTO public.projects VALUES (232, '广州鼎信科技有限公司室内无线对讲及巡更系统运维设备采购项目', '2025-04-25', '渠道跟进', '渠道', '不确定', '广州鼎信科技有限公司', NULL, '上海瀚网智能科技有限公司', NULL, NULL, '品牌植入', '2025/4/25 15:00:02 周裔锦
【直接用户】：添加   广州鼎信科技有限公司

2025/4/25 11:28:59 周裔锦
【授权编号】：添加   HY-CPJ202504-036
【类型】：添加   渠道跟进

2025/4/25 10:52:25 周裔锦
【完善价格】 273631
2025/4/25 10:45:00 周裔锦
【当前阶段情况说明】：改变成   广州鼎信科技有限公司生产厂区内使用，由他们自己内部采购和施工。

2025/4/23 周裔锦
「秦家俊」 广州鼎信科技有限公司  秦经理介绍，老板暂时叫停了我们系统，觉得报价高。项目目前在走管线，约了秦经理后续拜访，与技术当面核对配置，了解秦经理是否有个人述求。
', 'CPJ202504-036', '2025-04-25', 0, NULL, NULL, '2025-04-25 00:00:00', '2025-04-28 01:02:04.948582', 17);
INSERT INTO public.projects VALUES (233, '西丽综合交通枢纽工程', '2025-04-25', '渠道跟进', '销售', '不确定', NULL, '深圳市建筑设计研究总院有限公司', '上海瀚网智能科技有限公司', NULL, NULL, '发现', '2025/4/25 11:29:38 周裔锦
【授权编号】：添加   HY-CPJ202504-037
【类型】：添加   渠道跟进

2025/3/25 21:56:35 周裔锦
【当前阶段】：添加   发现
【分销商】：添加   上海瑞康
【当前阶段情况说明】：添加   设计院介绍，目前在做智能化整体设计，还没有到施工图。

2025/2/28 17:05:58 周裔锦
【设计院及顾问】：添加   深圳市建筑设计研究总院有限公司

', 'CPJ202504-037', '2025-04-25', 0, NULL, NULL, '2025-04-25 00:00:00', '2025-04-28 01:02:04.951575', 17);
INSERT INTO public.projects VALUES (234, '广州珠江科技创新园五星级酒店及酒店式公寓项目', '2025-04-25', '渠道跟进', '渠道', '入围', NULL, NULL, '广州洪昇智能科技有限公司', NULL, NULL, '品牌植入', '2025/4/25 11:13:01 周裔锦
【授权编号】：添加   HY-CPJ202504-035
【类型】：添加   渠道跟进

', 'CPJ202504-035', '2025-04-25', 0, NULL, NULL, '2025-04-25 00:00:00', '2025-04-28 01:02:04.953541', 17);
INSERT INTO public.projects VALUES (235, '河套深港科技创新合作区东翼-1项目', '2025-01-10', '渠道跟进', '销售', '不确定', NULL, '香港华艺设计顾问（深圳）有限公司', '上海瀚网智能科技有限公司', NULL, '深圳达实智能股份有限公司', '招标前', '2025/4/24 周裔锦
「徐道锦」 深圳达实智能股份有限公司  东翼-1项目已经配合售前过配置清单，目前有：达实、金证、智宇、英飞拓、万安、北电正光已询价。
本项目有可能最后采取抽签形式，暂时没有办法准确评估哪一家比较稳妥中标。
2025/4/11 14:29:18 周裔锦
【系统集成商】：添加   深圳达实智能股份有限公司
【当前阶段情况说明】：添加   公建项目，没有品牌要求，26号开标。当前需要找到参与集成商配合投标。

2025/4/7 10:47:11 周裔锦
【完善价格】 455261
2025/2/25 16:24:26 李冬
【授权编号】：添加   HY-CPJ202501-007
【类型】：添加   渠道跟进

2025/1/10 17:03:00 周裔锦
【授权编号】：添加   HY-CPJ202501-007
【类型】：添加   渠道跟进

2025/1/3 周裔锦
类型改变为 
', 'CPJ202501-007', '2025-04-24', 0, NULL, NULL, '2025-01-10 00:00:00', '2025-04-28 01:02:04.955256', 17);
INSERT INTO public.projects VALUES (236, '海灏生物创新港', '2025-03-21', '渠道跟进', '渠道', '入围', NULL, '广东省建筑设计研究院有限公司', '上海瀚网智能科技有限公司', NULL, '广东宏景科技股份有限公司', '中标', '2025/4/23 17:01:36 周裔锦
【完善价格】 122873
2025/4/23 16:59:58 周裔锦
申请项目批价
2025/4/23 13:58:05 周裔锦
申请项目批价
2025/4/23 13:51:41 周裔锦
【完善价格】 30517
2025/4/23 13:43:46 周裔锦
申请项目批价
2025/4/23 13:28:27 周裔锦
【完善价格】 26277
2025/4/17 周裔锦
「张经理」 广东宏景科技股份有限公司  张经理给出指导价格，我方配合做了调整。代理商已经提交企业资料，对方审核没有问题，下周可以签合同。
其余的项目暂时都没有进展。
2025/4/11 09:03:07 李冬
【授权编号】：添加   HY-CPJ202503-013
【类型】：添加   渠道跟进

2025/4/11 09:02:10 李冬
【系统集成商】：改变成   广东宏景科技股份有限公司

2025/4/10 16:31:20 李冬
【当前阶段情况说明】：改变成   配合集成商中标，跟进项目情况.

2025/4/10 16:27:50 李冬
【完善价格】 120979
2025/4/10 16:24:02 李冬
【品牌情况】：添加   入围
【当前阶段】：添加   中标
【分销商】：添加   上海瑞康
【经销商】：添加   上海瀚网智能科技有限公司
【系统集成商】：添加   广州宏景房地产开发有限公司
【当前阶段情况说明】：添加   配合集成商中标，跟进项目情况

2025/3/26 19:49:59 周裔锦
【完善价格】 118633
2025/3/24 10:50:00 周裔锦
【出货时间预测】：改变成   2025年二季度4月份

2025/3/21 13:45:13 周裔锦
【当前阶段】：添加   中标
【授权编号】：添加   HY-CPJ202503-013
【当前阶段情况说明】：添加   宏景已经中标，目前跟技术已经确认了参数，采购确认品牌没有问题就给业主报审，最快本月底签采购合同。
【类型】：添加   渠道跟进

', 'CPJ202503-013', '2025-04-23', 0, NULL, NULL, '2025-03-21 00:00:00', '2025-04-28 01:02:04.956779', 17);
INSERT INTO public.projects VALUES (237, '招商银行深圳总部大厦（增补）', '2025-04-23', '渠道跟进', '渠道', '入围', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '深圳达实智能股份有限公司', '中标', '2025/4/23 16:47:08 周裔锦
申请项目批价
2025/4/23 16:45:58 周裔锦
申请项目批价
2025/4/23 16:12:02 周裔锦
【授权编号】：添加   HY-CPJ202504-034
【类型】：添加   渠道跟进

2025/4/23 13:24:06 周裔锦
【完善价格】 118512
', 'CPJ202504-034', '2025-04-23', 0, NULL, NULL, '2025-04-23 00:00:00', '2025-04-28 01:02:04.959201', 17);
INSERT INTO public.projects VALUES (238, '长沙橘州诺雅酒店项目', '2025-03-21', '渠道跟进', '渠道', '入围', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '深圳市旗云智能科技有限公司', '中标', '2025/4/23 周裔锦
「张坤成」 深圳市旗云智能科技有限公司  张总说我们需要跟瑞斯通比价，竞品（科立讯、海能达、瑞斯通）希望我们尽力配合价格。
当前已经报了一版常规价格给采购，接下来还要找张总争取议价机会。
2025/4/11 09:03:40 李冬
【授权编号】：添加   HY-CPJ202503-014
【类型】：添加   渠道跟进

2025/4/10 16:49:37 李冬
【完善价格】 75632
2025/3/21 13:46:54 周裔锦
【当前阶段】：添加   中标
【授权编号】：添加   HY-CPJ202503-014
【当前阶段情况说明】：添加   集成商已经中标，目前长沙当地的技术负责深化，张坤成让我们和技术紧密配合
【类型】：添加   渠道跟进

', 'CPJ202503-014', '2025-04-23', 0, NULL, NULL, '2025-03-21 00:00:00', '2025-04-28 01:02:04.960917', 17);
INSERT INTO public.projects VALUES (239, '罗湖妇幼保健院智能化项目', '2025-04-11', '渠道跟进', '渠道', '不确定', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '深圳市电信工程有限公司', '中标', '2025/4/22 周裔锦
「林嘉豪」 深圳市电信工程有限公司  林总介绍了负责本项目的项目经理对接，胡经理说他这边已经根据我们给的资料了解过了我们品牌，他们现在一个一个系统在过，暂时还没有过到无线对讲系统，等到了再通知我们参与线上竞价。
项目经理在本环节占有选择权，需要进一步做深项目经理的工作。
2025/4/15 周裔锦
「林嘉豪」 深圳市电信工程有限公司  林经理介绍，已经将我们品牌补录进罗湖妇幼的招标名单，等通知到线上招标。
2025/4/11 11:30:43 周裔锦
【完善价格】 85597
2025/4/11 11:11:38 周裔锦
【授权编号】：添加   HY-CPJ202504-003
【类型】：添加   渠道跟进

2025/4/11 09:28:13 李冬
【授权编号】：添加   HY-CPJ202504-003
【类型】：添加   渠道跟进

2025/4/11 09:27:04 李冬
【完善价格】 90631
2025/4/9 周裔锦
「林嘉豪」 深圳市电信工程有限公司  配合梳理清单，以及报价。接下来等通知在平台邀标。没有回复报价的情况，到时候招标会给一个上限价格。
2025/4/2 周裔锦
「林嘉豪」 深圳市电信工程有限公司  林总介绍当前有罗湖妇幼项目，之前已经询过两轮价格，如果价格合适就直接使用。
新皇岗口岸联检大楼项目，他们也会去参与，跟进这个项目的时间比较长，而且比较深，如果没有意外，他们的优势比较大。
', 'CPJ202504-003', '2025-04-22', 0, NULL, NULL, '2025-04-11 00:00:00', '2025-04-28 01:02:04.962494', 17);
INSERT INTO public.projects VALUES (240, '新皇岗口岸联检大楼', '2024-07-19', '销售重点', '销售', '不确定', NULL, '厦门万安智能有限公司深圳分公司', '上海瀚网智能科技有限公司', NULL, NULL, '品牌植入', '2025/4/21 周裔锦
「方奕广」 厦门万安智能有限公司深圳分公司  交流蓝牙信标巡检方案，方经理介绍业主希望打卡能有声音反馈，不然信息不闭环，不知道能不能打上，从而给工作造成不便。
2025/4/16 周裔锦
「方奕广」 厦门万安智能有限公司深圳分公司  和方经理重新核对招标技术文档，他介绍地下室的摄像头是内置蓝牙的，业主出于成本考虑，也避免重复建设。提到蓝牙巡检能否使用摄像头里的蓝牙信号，以及蓝牙打卡的时候，能否在对讲机上有打上卡的提示音。我们最好出具一份关于蓝牙信标巡检的技术方案。
目前已经让刘威在配合整理。
2025/4/10 周裔锦
「方奕广」 厦门万安智能有限公司深圳分公司  方总反馈，业主方不同意把软件部分在技术参数里体现出来，所以需要想方法变通一下。调整后的频段以及对讲机含蓝牙功能基本没有问题。
2025/4/1 周裔锦
「方奕广」 厦门万安智能有限公司深圳分公司  方工介绍，项目调整为5月招标。上周已经把含有我们调整后的初版技术文档提交给代建方，最快节后回来会有结果。
2025/2/16 19:44:33 周裔锦
【设计院及顾问】：改变成   厦门万安智能有限公司深圳分公司
【经销商】：添加   上海瀚网智能科技有限公司

', 'SPJ202407-003', '2025-04-21', 0, NULL, NULL, '2024-07-19 00:00:00', '2025-04-28 01:02:04.963976', 17);
INSERT INTO public.projects VALUES (241, '深圳职业技术学院深汕校区项目', '2025-04-18', '渠道跟进', '渠道', '不确定', NULL, '华阳国际设计集团', '上海瀚网智能科技有限公司', NULL, NULL, '发现', '2025/4/18 16:06:15 周裔锦
【设计院及顾问】：添加   华阳国际设计集团

2025/4/18 12:05:04 周裔锦
【授权编号】：添加   HY-CPJ202504-020
【类型】：添加   渠道跟进

2025/4/16 周裔锦
「焦培荣」 华阳国际设计集团  焦总介绍，本项目分四个单位配合设计，分别是华阳、华东、浙江院、北京院。他们这边到时候让我们配合，最好去找剩下的三个院沟通，大家也希望尽量做到统一，避免后续的扯皮。
', 'CPJ202504-020', '2025-04-18', 0, NULL, NULL, '2025-04-18 00:00:00', '2025-04-28 01:02:04.965559', 17);
INSERT INTO public.projects VALUES (242, '哔哩哔哩新世代产业园项目', '2025-04-14', '渠道跟进', '渠道', '不确定', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '深圳达实智能股份有限公司', '招标前', '2025/4/18 15:23:16 周裔锦
【完善价格】 1200960
2025/4/18 周裔锦
「帅进」 深圳达实智能股份有限公司  帅总要求尽快梳理出本项目的配置，要求尽量精准，本项目对成本比较关注。具体招标时间还没有定下来。
目前已经梳理出来了配置和成本清单。
2025/4/14 10:53:59 周裔锦
【授权编号】：添加   HY-CPJ202503-034
【类型】：添加   渠道跟进

2025/4/14 花伟
「花伟」 敦力(南京)科技有限公司  B站的项目提供集成商投标时的报价，等待最终的中标单位。
2025/4/3 14:55:55 花伟
【经销商】：添加   花伟「敦力(南京)科技有限公司」
【授权编号】：添加   HY-CPJ202503-034
【类型】：添加   渠道跟进

', 'CPJ202503-034', '2025-04-18', 0, NULL, NULL, '2025-04-14 00:00:00', '2025-04-28 01:02:04.966953', 17);
INSERT INTO public.projects VALUES (243, '珠海市九洲港客运站场及配套设施项目客运港区域智能化工程', '2025-04-18', '渠道跟进', '销售', '不确定', NULL, NULL, '广州洪昇智能科技有限公司', NULL, NULL, '招标前', '2025/4/18 12:04:19 周裔锦
【授权编号】：添加   HY-CPJ202504-019
【类型】：添加   渠道跟进

2025/4/7 17:41:37 周裔锦
【完善价格】 205591
2025/4/7 16:55:38 周裔锦
【当前阶段】：添加   招标前
【当前阶段情况说明】：添加   投标前报价。

2025/4/7 16:51:02 周裔锦
【系统集成商】：添加   珠海华发数智技术有限公司

', 'CPJ202504-019', '2025-04-18', 0, NULL, NULL, '2025-04-18 00:00:00', '2025-04-28 01:02:04.968392', 17);
INSERT INTO public.projects VALUES (244, '机场东车辆段上盖物业开发项目', '2025-04-18', '渠道跟进', '销售', '不确定', NULL, '香港华艺设计顾问（深圳）有限公司', '上海瀚网智能科技有限公司', NULL, '深圳达实智能股份有限公司', '发现', '2025/4/18 12:03:30 周裔锦
【授权编号】：添加   HY-CPJ202504-018
【类型】：添加   渠道跟进

2025/4/17 周裔锦
「何雁」 香港华艺设计顾问（深圳）有限公司  何总介绍，深铁置业让他们配合出设计规范，这个工作大概会在5-6月启动，到时候需要将我们上海做的无线对讲行业规范梳理出核心关键，给到他们。
河套项目还在做土建设计，智能化还远。
2025/3/28 16:40:35 周裔锦
【系统集成商】：改变成   深圳达实智能股份有限公司

2025/3/25 21:57:11 周裔锦
【当前阶段】：添加   发现

2025/2/28 16:28:54 周裔锦
【系统集成商】：添加   深圳市燕翔云天科技有限公司

2025/2/14 19:49:09 周裔锦
【设计院及顾问】：添加   香港华艺设计顾问（深圳）有限公司
【当前阶段情况说明】：添加   深圳壹创国际负责总包设计，华艺负责智能化设计，何雁介绍本项目属于地铁，地铁项目可能不会定品牌，最好跟总包或者智能化分包配合。

', 'CPJ202504-018', '2025-04-18', 0, NULL, NULL, '2025-04-18 00:00:00', '2025-04-28 01:02:04.969719', 17);
INSERT INTO public.projects VALUES (245, '宝龙生物药创新发展先导区（二期）项目', '2025-04-18', '渠道跟进', '渠道', '不确定', NULL, NULL, NULL, NULL, NULL, '发现', '2025/4/18 12:01:17 周裔锦
【授权编号】：添加   HY-CPJ202504-017
【类型】：添加   渠道跟进

', 'CPJ202504-017', '2025-04-18', 0, NULL, NULL, '2025-04-18 00:00:00', '2025-04-28 01:02:04.971084', 17);
INSERT INTO public.projects VALUES (246, 'TCL华星光电技术有限公司（中韩合资）TCL华星光电高世代面板产业配套项目（含装配式）', '2025-04-18', '渠道跟进', '销售', '不确定', 'TCL建设管理（深圳）有限公司', NULL, '上海瀚网智能科技有限公司', NULL, NULL, '发现', '2025/4/18 12:00:29 周裔锦
【授权编号】：添加   HY-CPJ202504-016
【类型】：添加   渠道跟进

2025/4/16 周裔锦
「王如郑」 TCL建设管理（深圳）有限公司  王经理，介绍项目上近期出了安全问题，所有人员都在做安全管理规范学习，需要改下周到公司去找关键人做品牌入库工作。
2025/4/11 12:45:58 周裔锦
【直接用户】：添加   TCL建设管理（深圳）有限公司

2025/4/9 周裔锦
「王如郑」 TCL建设管理（深圳）有限公司  王经理介绍，他们有自己的品牌库，要对接设计院建议先做品牌入库工作，避免浪费时间。了解了入库流程以及关键人联系方式，建议下周再联系拜访。
', 'CPJ202504-016', '2025-04-18', 0, NULL, NULL, '2025-04-18 00:00:00', '2025-04-28 01:02:04.972439', 17);
INSERT INTO public.projects VALUES (247, '粤海云港城', '2025-04-18', '渠道跟进', '渠道', '入围', NULL, NULL, NULL, NULL, '广州鑫宇视通科技有限公司', '招标前', '2025/4/18 11:59:46 周裔锦
【系统集成商】：添加   广州鑫宇视通科技有限公司
【授权编号】：添加   HY-CPJ202504-021
【类型】：添加   渠道跟进

2025/4/18 11:48:21 周裔锦
【完善价格】 859965
2025/4/18 11:25:46 周裔锦
【完善价格】 13580
', 'CPJ202504-021', '2025-04-18', 0, NULL, NULL, '2025-04-18 00:00:00', '2025-04-28 01:02:04.973835', 17);
INSERT INTO public.projects VALUES (271, '广州黄埔暹岗社区旧村改造项目二期复建区住宅智能化工程', '2025-02-13', '渠道跟进', '销售', '入围', NULL, NULL, '广州洪昇智能科技有限公司', NULL, NULL, '招标前', '2025/2/13 10:19:31 周裔锦
【授权编号】：添加   HY-CPJ202502-008
【类型】：添加   渠道跟进

', 'CPJ202502-008', '2025-02-13', 0, NULL, NULL, '2025-02-13 00:00:00', '2025-04-28 01:02:05.000561', 17);
INSERT INTO public.projects VALUES (248, '深圳国际综合部物流枢纽中心', '2024-08-30', '销售重点', '销售', '不确定', '深圳市深国铁路物流发展有限公司', '广东省电信规划设计院有限公司', '上海瀚网智能科技有限公司', NULL, NULL, '品牌植入', '2025/4/18 09:29:04 周裔锦
【完善价格】 2787052
2025/4/11 11:52:29 周裔锦
【完善价格】 2626909
2025/4/11 11:39:24 周裔锦
【完善价格】 55605
2025/4/8 周裔锦
「肖阳陵」 深圳市深国铁路物流发展有限公司  张兴配合一同拜访，现场根据客户点位图配置清单，整个系统报价暂定在390万，暂定为4组通话需求。如果业主方要求使用B1线缆，或者线缆套管，价格会增加。
将深圳万睿的销售经理李应介绍给业主，李应做过深国际的项目，他表示有一定把握能操盘下来。
当前配合设计方给出方案的工作已经取得业主方认可，加上系统预算不占比过大，设计院透露业主把无线对讲系统作为智能化的重点系统，但目前还是有运营商来推公网对讲，所以需要推动尽快上会争取拍板建设，解除后顾之忧。
2025/4/3 周裔锦
「肖阳陵」 深圳市深国铁路物流发展有限公司  本周设计院还没有把按照我方给我设计规则出的点位图，下周再约，到时候和设计院一起过点位图。
2025/3/24 10:51:41 周裔锦
【分销商】：添加   上海瑞康

2025/3/24 10:51:27 周裔锦
【当前阶段】：改变成   品牌植入
【当前阶段情况说明】：改变成   目前项目已经由省院中标设计，业主方已同意先设计，后再根据整体成本讨论是否保留建设。

2025/3/8 10:46:33 周裔锦
【当前阶段】：改变成   发现

2025/3/8 10:46:22 周裔锦
【设计院及顾问】：改变成   广东省电信规划设计院有限公司

2025/2/28 17:55:53 周裔锦
【设计院及顾问】：添加   广东省建筑设计研究院有限公司
【当前阶段】：改变成   品牌植入
【经销商】：添加   上海瀚网智能科技有限公司
【当前阶段情况说明】：改变成   目前项目已经由省院中标设计。

2025/2/21 13:29:42 周裔锦
【当前阶段】：改变成   发现
【当前阶段情况说明】：添加   设计招标阶段，属于项目发现。

', 'SPJ202408-008', '2025-04-18', 0, NULL, NULL, '2024-08-30 00:00:00', '2025-04-28 01:02:04.975629', 17);
INSERT INTO public.projects VALUES (249, '粤芯半导体集成电路厂改造', '2025-04-14', '渠道跟进', '渠道', '入围', NULL, NULL, '广州宇洪科技股份有限公司', NULL, NULL, '中标', '2025/4/14 09:50:06 周裔锦
【授权编号】：添加   HY-CPJ202412-017
【类型】：添加   渠道跟进

2025/4/14 09:49:16 周裔锦
【当前阶段】：添加   中标
【当前阶段情况说明】：添加   业主已经确定集成商。

2025/3/25 21:49:19 周裔锦
【当前阶段】：添加   发现
【授权编号】：添加   HY-CPJ202412-017
【当前阶段情况说明】：添加   设计院介绍项目尚未进入施工图设计。
【类型】：添加   渠道跟进

2025/3/25 13:42:01 周裔锦
【完善价格】 37878
', 'CPJ202412-017', '2025-04-14', 0, NULL, NULL, '2025-04-14 00:00:00', '2025-04-28 01:02:04.977211', 17);
INSERT INTO public.projects VALUES (250, '中信金融中心项目', '2025-04-11', '渠道跟进', '渠道', '不确定', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '中建三局智能技术有限公司深圳分公司', '中标', '2025/4/11 11:13:02 周裔锦
【授权编号】：添加   HY-CPJ202504-002
【类型】：添加   渠道跟进

', 'CPJ202504-002', '2025-04-11', 0, NULL, NULL, '2025-04-11 00:00:00', '2025-04-28 01:02:04.978419', 17);
INSERT INTO public.projects VALUES (251, '润世华大厦智能化工程', '2025-04-11', '渠道跟进', '渠道', '不确定', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '深圳达实智能股份有限公司', '招标前', '2025/4/11 11:12:22 周裔锦
【授权编号】：添加   HY-CPJ202504-004
【类型】：添加   渠道跟进

2025/4/11 09:17:46 李冬
【授权编号】：添加   HY-CPJ202504-004
【类型】：添加   渠道跟进

2025/4/11 09:17:00 李冬
【完善价格】 114655
2025/4/8 周裔锦
「帅进」 深圳达实智能股份有限公司  本项目招标授权资料提报。本项目的中标概率较大。
2025/4/6 10:16:10 周裔锦
【完善价格】 108606
2025/4/1 周裔锦
「帅进」 深圳达实智能股份有限公司  帅总介绍本项目下周投标，需要下周一前出厂家授权文件。中继台和对讲机有品牌要求，我们配合天馈部分。
', 'CPJ202504-004', '2025-04-11', 0, NULL, NULL, '2025-04-11 00:00:00', '2025-04-28 01:02:04.979588', 17);
INSERT INTO public.projects VALUES (252, '宝安区中医院扩建工程（二期）智能化工程', '2025-04-11', '渠道跟进', '渠道', '不确定', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '深圳达实智能股份有限公司', '中标', '2025/4/11 11:11:01 周裔锦
【授权编号】：添加   HY-CPJ202504-006
【类型】：添加   渠道跟进

2025/4/11 09:11:48 李冬
【授权编号】：添加   HY-CPJ202504-006
【类型】：添加   渠道跟进

2025/4/10 17:39:40 李冬
【完善价格】 131529
2025/4/10 17:36:27 李冬
【当前阶段】：添加   中标
【当前阶段情况说明】：添加   集成商中标，配合下一步深化

2025/4/6 10:05:42 周裔锦
【完善价格】 123548
2025/4/3 周裔锦
「李莹」 深圳达实智能股份有限公司  李工介绍本项已经中标，当时用的是昊天配合投标，和源报价合适可以配合变更，目前还没到品牌确认阶段。预计最快第三季度会涉及到我们系统的采购。
', 'CPJ202504-006', '2025-04-11', 0, NULL, NULL, '2025-04-11 00:00:00', '2025-04-28 01:02:04.98083', 17);
INSERT INTO public.projects VALUES (253, '骏景北商业地块', '2024-11-10', '渠道跟进', '销售', '入围', NULL, NULL, '广州宇洪科技股份有限公司', NULL, '深圳中电瑞达智能技术有限公司', '中标', '2025/3/31 周裔锦
「邹莉」 深圳中电瑞达智能技术有限公司  邹经理介绍，虽然我们配合投标，但他们的中标价格比较低，本周会进行品牌报审前询价沟通。
已通知宇洪，本项目涉及竞品：海能达、上海曙腾。
2025/3/24 10:54:10 周裔锦
【出货时间预测】：添加   2025年二季度6月份

2025/1/3 周裔锦
【阶段变更】招标中->中标
类型改变为渠道跟进 
2024/11/29 周裔锦
【阶段变更】招标前->招标中

2024/11/19 10:47:14 周裔锦
【完善价格】 117392
', 'CPJ202411-004', '2025-03-31', 0, NULL, NULL, '2024-11-10 00:00:00', '2025-04-28 01:02:04.981971', 17);
INSERT INTO public.projects VALUES (254, '招商银行深圳总部大厦', '2025-03-07', '渠道跟进', '销售', '入围', NULL, NULL, '广州宇洪智能技术有限公司', NULL, '深圳达实智能股份有限公司', '签约', '2025/3/29 13:36:12 周裔锦
[阶段变更] ->签约
2025/3/20 21:31:52 周裔锦
【完善价格】 420877
2025/3/20 13:18:14 周裔锦
【完善价格】 539389
2025/3/20 12:34:24 周裔锦
【完善价格】 539390
2025/3/14 16:28:05 周裔锦
【完善价格】 573345
2025/3/7 01:15:34 周裔锦
【授权编号】：改变成   HY-CPJ202409-022
【类型】：改变成   渠道跟进

', 'CPJ202409-022', '2025-03-29', 0, NULL, NULL, '2025-03-07 00:00:00', '2025-04-28 01:02:04.983062', 17);
INSERT INTO public.projects VALUES (255, '湖北交投实业大厦', '2025-03-28', '渠道跟进', '渠道', '入围', NULL, NULL, '广州宇洪科技股份有限公司', NULL, '武汉烽火信息集成技术有限公司', '中标', '2025/3/28 17:34:55 周裔锦
【系统集成商】：添加   武汉烽火信息集成技术有限公司

2025/3/28 17:11:56 周裔锦
【授权编号】：添加   HY-CPJ202306-003
【类型】：添加   渠道跟进

2025/3/3 10:27:01 郭小会
【当前阶段】：改变成   转移
【当前阶段情况说明】：添加   此项目宇洪在跟进，转移到南区销售周裔锦那边
【类型】：改变成   渠道跟进

2024/11/23 郭小会
【阶段变更】品牌植入->中标

2024/3/8 13:32:24 郭小会
安排宇洪的李小飞去对接潜在的集成商
2024/2/29 11:24:21 郭小会
和天华设计杨经理确认，品牌这块去年和业主沟通完后，业主坚持对讲机要用摩托罗拉的。
2023/11/1 郭小会
项目前期设计
', 'CPJ202306-003', '2025-03-28', 0, NULL, NULL, '2025-03-28 00:00:00', '2025-04-28 01:02:04.984237', 17);
INSERT INTO public.projects VALUES (256, '恒力集团深圳湾超级总部基地', '2025-03-25', '渠道跟进', '渠道', '入围', NULL, NULL, '上海瀚网智能科技有限公司', NULL, NULL, '招标中', '2025/3/25 21:45:34 周裔锦
【授权编号】：添加   HY-CPJ202503-024
【类型】：添加   渠道跟进

', 'CPJ202503-024', '2025-03-25', 0, NULL, NULL, '2025-03-25 00:00:00', '2025-04-28 01:02:04.985311', 17);
INSERT INTO public.projects VALUES (257, '名创优品项目', '2024-08-09', '渠道跟进', '销售', '入围', NULL, NULL, '广州宇洪科技股份有限公司', NULL, '厦门万安智能有限公司', '中标', '2025/3/24 10:53:17 周裔锦
【出货时间预测】：添加   2025年二季度6月份

2024/12/6 周裔锦
【阶段变更】招标中->中标

2024/11/29 周裔锦
【出现困难】宇洪和瀚网都有各自配合的集成商参与投标。

', 'CPJ202408-005', '2025-03-24', 0, NULL, NULL, '2024-08-09 00:00:00', '2025-04-28 01:02:04.986388', 17);
INSERT INTO public.projects VALUES (258, '羊城晚报', '2024-07-05', '渠道跟进', '销售', '入围', NULL, NULL, '广州宇洪智能技术有限公司', NULL, '中建三局智能技术有限公司', '中标', '2025/3/24 10:52:56 周裔锦
【出货时间预测】：添加   2025年二季度6月份

2025/1/3 周裔锦
【阶段变更】招标中->中标

2024/11/29 周裔锦
【阶段变更】招标前->招标中

2024/10/27 周裔锦
【出现困难】三局智能已中标，预计明年5/6月份在云筑网招标。

2024/7/5 16:10:15 庄海鑫
【提案】「」:  配合集成商对配置进行确定
', 'CPJ202407-004', '2025-03-24', 0, NULL, NULL, '2024-07-05 00:00:00', '2025-04-28 01:02:04.987408', 17);
INSERT INTO public.projects VALUES (259, '大唐三亚总部基地办公楼项目', '2025-01-10', '渠道跟进', '销售', '不确定', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '深圳市万睿智能科技有限公司', '品牌植入', '2025/3/7 00:04:00 周裔锦
【完善价格】 238478
45667.703900463 李冬
【分销商】：添加   上海瑞康
【经销商】：添加   上海瀚网智能科技有限公司
【授权编号】：添加   HY-CPJ202501-005
【类型】：添加   渠道跟进

2025/1/10 16:53:37 周裔锦
【分销商】：添加   上海瑞康
【经销商】：添加   上海瀚网智能科技有限公司
【授权编号】：添加   HY-CPJ202501-005
【类型】：添加   渠道跟进

', 'CPJ202501-005', '2025-03-07', 0, NULL, NULL, '2025-01-10 00:00:00', '2025-04-28 01:02:04.98847', 17);
INSERT INTO public.projects VALUES (260, '深圳歌剧院项目', '2024-11-10', '销售重点', '销售', '入围', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '中建科工集团有限公司', '中标', '2025/2/28 16:53:25 周裔锦
【当前阶段】：改变成   中标

2025/2/28 16:53:13 周裔锦
【经销商】：添加   上海瀚网智能科技有限公司
【系统集成商】：添加   中建科工集团有限公司
【当前阶段情况说明】：添加   中建科工已中总包。项目尚在挖基坑。

2024/11/19 11:27:56 周裔锦
【完善价格】 1413480
', 'SPJ202411-009', '2025-02-28', 0, NULL, NULL, '2024-11-10 00:00:00', '2025-04-28 01:02:04.989488', 17);
INSERT INTO public.projects VALUES (261, '增城区牛仔服装智能制造示范基地', '2024-10-18', '渠道跟进', '经销商', '入围', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '广东恒信安电子有限公司', '招标前', '2025/2/26 17:49:42 周裔锦
【完善价格】 99399
', 'CPJ202410-011', '2025-02-26', 0, NULL, NULL, '2024-10-18 00:00:00', '2025-04-28 01:02:04.990644', 17);
INSERT INTO public.projects VALUES (262, '深圳市创新金融总部基地', '2025-02-23', '渠道跟进', '销售', '不确定', NULL, NULL, '深圳市深嘉创达科技有限公司', NULL, NULL, '发现', '2025/2/23 21:57:31 周裔锦
【当前阶段】：改变成   发现
【当前阶段情况说明】：添加   由于尚无清单，改为发现阶段。

2025/2/23 21:56:14 周裔锦
【授权编号】：改变成   HY-CPJ202412-021
【类型】：改变成   渠道跟进

', 'CPJ202412-021', '2025-02-23', 0, NULL, NULL, '2025-02-23 00:00:00', '2025-04-28 01:02:04.991777', 17);
INSERT INTO public.projects VALUES (263, '深圳机场教育基地建设项目智能化工程', '2025-02-23', '渠道跟进', '经销商', '不确定', NULL, NULL, '深圳市深嘉创达科技有限公司', NULL, '深圳达实智能股份有限公司', '中标', '2025/2/23 21:54:49 周裔锦
【系统集成商】：添加   深圳达实智能股份有限公司

2025/2/23 21:54:13 周裔锦
【授权编号】：改变成   HY-CPJ202409-020
【类型】：改变成   渠道跟进

', 'CPJ202409-020', '2025-02-23', 0, NULL, NULL, '2025-02-23 00:00:00', '2025-04-28 01:02:04.992888', 17);
INSERT INTO public.projects VALUES (264, '香港科技大学（广州）二期', '2024-10-18', '销售重点', '销售', '不确定', NULL, '华南理工大学建筑设计研究院', '上海瀚网智能科技有限公司', NULL, NULL, '发现', '2025/2/21 13:28:40 周裔锦
【当前阶段】：改变成   发现
【当前阶段情况说明】：添加   项目施工图尚未出来，属于发现阶段。

2024/11/29 周裔锦
【阶段变更】发现->品牌植入

', 'SPJ202410-003', '2025-02-21', 0, NULL, NULL, '2024-10-18 00:00:00', '2025-04-28 01:02:04.99396', 17);
INSERT INTO public.projects VALUES (265, '广州大学城校区新建学生宿舍工程', '2024-12-06', '销售重点', '销售', '不确定', NULL, '华南理工大学建筑设计研究院', NULL, NULL, NULL, '发现', '2025/2/21 13:27:55 周裔锦
【当前阶段】：改变成   发现
【当前阶段情况说明】：添加   智能化施工图尚未出来，属于发现阶段。

', 'SPJ202412-002', '2025-02-21', 0, NULL, NULL, '2024-12-06 00:00:00', '2025-04-28 01:02:04.994961', 17);
INSERT INTO public.projects VALUES (266, '国深博物馆项目', '2024-11-29', '销售重点', '销售', '不确定', NULL, '华南理工大学建筑设计研究院', NULL, NULL, NULL, '发现', '2025/2/21 13:26:36 周裔锦
【当前阶段】：改变成   发现
【当前阶段情况说明】：添加   项目属于土建总包招标阶段，智能化部分尚未招标。

', 'SPJ202411-014', '2025-02-21', 0, NULL, NULL, '2024-11-29 00:00:00', '2025-04-28 01:02:04.995997', 17);
INSERT INTO public.projects VALUES (267, '河套深港科技创新合作区协同创新区（皇岗口岸片区协同创新区）', '2025-02-13', '销售重点', '销售', '不确定', NULL, '香港华艺设计顾问（深圳）有限公司', NULL, NULL, NULL, '发现', '2025/2/21 13:24:22 周裔锦
【当前阶段】：改变成   发现
【当前阶段情况说明】：添加   由于项目刚中设计部，智能化设计尚未启动，改为发现阶段。

2025/2/13 10:22:03 周裔锦
【授权编号】：改变成   HY-SPJ202412-004
【类型】：添加   销售重点

2024/12/30 郭小会
类型改变为 
', 'SPJ202412-004', '2025-02-21', 0, NULL, NULL, '2025-02-13 00:00:00', '2025-04-28 01:02:04.996963', 17);
INSERT INTO public.projects VALUES (268, '招商银行深圳总部大厦', '2024-09-27', '销售重点', '销售', '入围', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '深圳达实智能股份有限公司', '中标', '2025/2/21 13:19:47 周裔锦
【出货时间预测】：改变成   2025年一季度3月份

2025/2/8 16:02:04 周裔锦
【出货时间预测】：改变成   2025年一季度2月份

2024/10/10 20:18:46 周裔锦
【完善价格】 564206
2024/10/8 周裔锦
【阶段变更】->中标

2024/9/6 17:35:20 庄海鑫
【阶段变更】中标->签约

2023/11/1 庄海鑫
1、项目位于深圳，由深圳达实集成商提供的项目，项目处于招投标阶段。
2、目前深圳金证股份、润信科技、达实、上海云思、同方股份完成参与投标
3、项目达实已中标，使用我司品牌投标。
4、集成商项目经理和深化设计负责人已确定
', 'SPJ202409-013', '2025-02-21', 0, NULL, NULL, '2024-09-27 00:00:00', '2025-04-28 01:02:04.997847', 17);
INSERT INTO public.projects VALUES (269, '深圳国际交流中心一期', '2025-01-10', '渠道跟进', '销售', '入围', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '深圳市和一实业有限公司', '中标', '2025/2/17 22:16:44 周裔锦
【完善价格】 602329
45667.7046064815 李冬
【授权编号】：改变成   HY-CPJ202501-008
【类型】：添加   渠道跟进

2025/1/10 16:54:38 周裔锦
【授权编号】：改变成   HY-CPJ202501-008
【类型】：添加   渠道跟进

', 'CPJ202501-008', '2025-02-17', 0, NULL, NULL, '2025-01-10 00:00:00', '2025-04-28 01:02:04.998759', 17);
INSERT INTO public.projects VALUES (270, '佛山平安中心建设项目', '2024-09-13', '销售重点', '系统集成商', '入围', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '中通服咨询设计研究院有限公司', '中标', '2025/2/14 16:02:16 周裔锦
【系统集成商】：改变成   中通服咨询设计研究院有限公司

2025/2/10 17:40:20 周裔锦
【当前阶段】：改变成   中标
【当前阶段情况说明】：改变成   中通服已中标，目前在核对采购成本。

2024/10/27 周裔锦
【出现困难】投标结果还没有出来。

2024/10/27 周裔锦
【出现困难】三局智能说投标时竞争太激烈，最后没有中标。

2024/10/9 18:14:05 周裔锦
【完善价格】 331156
2024/10/8 周裔锦
【阶段变更】招标前->招标中

2024/9/13 周裔锦
【出现困难】本项目配合三局智能和中通服两家报价投标，当前让瀚网张兴配合三局智能报价，我已按照中通服清单报价358968元。

', 'SPJ202409-005', '2025-02-14', 0, NULL, NULL, '2024-09-13 00:00:00', '2025-04-28 01:02:04.999658', 17);
INSERT INTO public.projects VALUES (273, '深圳湾超级总部基地C塔项目', '2024-09-13', '销售重点', '经销商', '不确定', NULL, '深圳市建筑设计研究总院有限公司', '上海瀚网智能科技有限公司', NULL, NULL, '品牌植入', '2025/1/3 09:40:51 周裔锦
【完善价格】 1089433
2024/12/15 周裔锦
类型改变为销售重点 
2024/9/13 周裔锦
【出现困难】当前配合设计院做方案，业主需求不清晰，还需要进一步了解确定预算和需求。
类型改变为渠道管理 
', 'SPJ202409-006', '2025-01-03', 0, NULL, NULL, '2024-09-13 00:00:00', '2025-04-28 01:02:05.002469', 17);
INSERT INTO public.projects VALUES (274, '深圳机场教育基地建设项目智能化工程', '2024-09-13', '销售重点', '经销商', '不确定', NULL, NULL, '深圳市深嘉创达科技有限公司', NULL, NULL, '中标', '2024/12/16 周裔锦
类型改变为销售重点 
2024/12/16 周裔锦
【阶段变更】招标中->中标
类型改变为渠道管理 
2024/12/2 周裔锦
类型改变为渠道管理 
2024/11/29 周裔锦
【阶段变更】招标前->招标中

2024/11/19 15:23:32 周裔锦
【完善价格】 145902
2024/9/13 周裔锦
类型改变为渠道跟进 
', 'SPJ202409-007', '2024-12-16', 0, NULL, NULL, '2024-09-13 00:00:00', '2025-04-28 01:02:05.003378', 17);
INSERT INTO public.projects VALUES (275, '新皇岗口岸联检大楼工程', '2024-10-08', '销售重点', '销售', '不确定', NULL, '厦门万安智能有限公司深圳分公司', '上海瀚网智能科技有限公司', NULL, NULL, '失败', '2024/12/16 周裔锦
【阶段变更】品牌植入->失败

', 'SPJ202410-001', '2024-12-16', 0, NULL, NULL, '2024-10-08 00:00:00', '2025-04-28 01:02:05.004319', 17);
INSERT INTO public.projects VALUES (276, '琶洲算谷', '2024-04-30', '销售重点', '销售', '入围', NULL, '广东省建筑设计研究院有限公司', '广州宇洪智能技术有限公司', NULL, NULL, '招标前', '2024/12/15 周裔锦
类型改变为销售重点 
2024/11/29 周裔锦
【阶段变更】中标->招标前

2024/11/22 周裔锦
【出现困难】中建三局二安公司已经中标，目前文工在核对图纸，等核对完成后让我们配合深化。

2024/9/6 17:27:21 庄海鑫
【阶段变更】品牌植入->失败

2024/4/30 庄海鑫
【提案】:  根据项目情况推荐对讲+巡更的方案
', 'SPJ202404-006', '2024-12-15', 0, NULL, NULL, '2024-04-30 00:00:00', '2025-04-28 01:02:05.005201', 17);
INSERT INTO public.projects VALUES (277, '深圳市创新金融总部基地', '2024-12-12', '销售重点', '销售', '不确定', NULL, NULL, '深圳市深嘉创达科技有限公司', NULL, NULL, '招标前', NULL, 'SPJ202412-003', '2024-12-12', 0, NULL, NULL, '2024-12-12 00:00:00', '2025-04-28 01:02:05.006142', 17);
INSERT INTO public.projects VALUES (278, '新疆库尔勒万丽万怡酒店', '2024-11-22', '渠道跟进', '经销商', '入围', NULL, NULL, '广州宇洪科技股份有限公司', NULL, NULL, '中标', '2024/11/22 16:10:09 周裔锦
【完善价格】 23990
', 'CPJ202411-010', '2024-11-29', 0, NULL, NULL, '2024-11-22 00:00:00', '2025-04-28 01:02:05.007387', 17);
INSERT INTO public.projects VALUES (279, '东部中心广深科技创新项目', '2024-08-09', '渠道跟进', '经销商', '入围', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '汕头市晖信电器科技有限公司', '招标前', '2024/11/29 庄海鑫
【阶段变更】品牌植入->招标前

', 'CPJ202408-007', '2024-11-29', 0, NULL, NULL, '2024-08-09 00:00:00', '2025-04-28 01:02:05.00851', 17);
INSERT INTO public.projects VALUES (280, '佛山市禅城区华侨城绿景东路南侧、华祥路北侧、规划十四路东侧地块项目', '2024-11-29', '渠道跟进', '经销商', '入围', NULL, NULL, '广州宇洪科技股份有限公司', NULL, NULL, '招标前', '2024/11/29 12:59:32 周裔锦
【完善价格】 64246
', 'CPJ202411-015', '2024-11-29', 0, NULL, NULL, '2024-11-29 00:00:00', '2025-04-28 01:02:05.00947', 17);
INSERT INTO public.projects VALUES (281, '中集集团前海总部', '2024-11-08', '销售重点', '销售', '不确定', NULL, '筑博设计集团股份有限公司', NULL, NULL, NULL, '发现', '2024/11/8 周裔锦
【出现困难】设计院介绍，目前项目在做土建设计，智能化部分要稍后，下回介绍智能化的同事来对接配合设计无线对讲系统。

', 'SPJ202411-007', '2024-11-08', 0, NULL, NULL, '2024-11-08 00:00:00', '2025-04-28 01:02:05.010418', 17);
INSERT INTO public.projects VALUES (282, '深圳市龙华区博雅学校项目', '2024-11-01', '销售重点', '销售', '不确定', NULL, '深圳市建筑设计研究总院有限公司', NULL, NULL, NULL, '发现', NULL, 'SPJ202411-001', '2024-11-01', 0, NULL, NULL, '2024-11-01 00:00:00', '2025-04-28 01:02:05.011322', 17);
INSERT INTO public.projects VALUES (283, '深圳市体育中心配套酒店项目', '2024-11-01', '销售重点', '销售', '不确定', NULL, '深圳市建筑设计研究总院有限公司', NULL, NULL, NULL, '发现', NULL, 'SPJ202411-002', '2024-11-01', 0, NULL, NULL, '2024-11-01 00:00:00', '2025-04-28 01:02:05.012196', 17);
INSERT INTO public.projects VALUES (284, '前海深港创新产业园', '2024-11-01', '销售重点', '销售', '不确定', NULL, '奥意建筑工程设计有限公司', NULL, NULL, NULL, '发现', NULL, 'SPJ202411-003', '2024-11-01', 0, NULL, NULL, '2024-11-01 00:00:00', '2025-04-28 01:02:05.01303', 17);
INSERT INTO public.projects VALUES (285, '上海黄浦江南自延伸段WS3单元xh130E街坊', '2024-08-09', '渠道跟进', '经销商', '入围', NULL, NULL, '广州宇洪科技股份有限公司', NULL, '厦门万安智能有限公司', '招标中', '2024/10/27 周裔锦
【出现困难】裴小印说同事在跟进中，要跟同事同步后反馈给我最新结果。

', 'CPJ202408-006', '2024-10-27', 0, NULL, NULL, '2024-08-09 00:00:00', '2025-04-28 01:02:05.013861', 17);
INSERT INTO public.projects VALUES (286, '淀山湖喜来登、雅乐轩项目', '2023-11-22', '渠道跟进', '代理商', '入围', NULL, NULL, '上海瀚网智能科技有限公司', NULL, '深圳达实智能股份有限公司', '签约', '2024/10/27 周裔锦
【出现困难】张兴说本项目还在待签约状态，最快四季度能下来。

2024/7/1 10:49:02 庄海鑫
【阶段变更】中标->签约
2023/11/1 庄海鑫
1、目前项目已由深圳达智能中标，进行询价阶段。
2、代理商已寄样给到达实
', 'CPJ202311-005', '2024-10-27', 0, NULL, NULL, '2023-11-22 00:00:00', '2025-04-28 01:02:05.01473', 17);
INSERT INTO public.projects VALUES (287, '铁汉生态广场', '2024-03-03', '渠道跟进', '销售', '不确定 ', NULL, '机械工业部深圳设计研究院有限公司', NULL, NULL, NULL, '品牌植入', '2024/10/27 周裔锦
【出现困难】张兴没有跟进，表内联系人：丁瑞斌和程龙没有联系电话。

2024/3/3 17:41:13 庄海鑫
【提案】  :  项目处于品牌植入阶段，配合设计院完成无线对讲系统部分的设计
', 'CPJ202403-002', '2024-10-27', 0, NULL, NULL, '2024-03-03 00:00:00', '2025-04-28 01:02:05.015521', 17);
INSERT INTO public.projects VALUES (288, '南方电网大湾区数字产业基地项目', '2024-08-18', '销售重点', '销售', '不确定', NULL, '广东南方电信规划咨询设计院有限公司 ', NULL, NULL, '鼎熙国讯科技有限公司', '发现', '2024/10/9 周裔锦
类型改变为销售重点 
2024/10/8 周裔锦
【阶段变更】品牌植入->发现

2024/8/23 15:43:03 周裔锦
【出现困难】本次拜访鼎熙国讯，业主方南网大数据公司了解到，本项目会在下一阶段把无线对讲这一块定下来，品牌推荐主要由专家推荐，专家是由系统随机抽取的。个人判断需要从总包方和设计院深入做工作，总包有一定的建议权，以及设计院能配合提专业的技术要求。

2024/8/18 13:30:41 周裔锦
【阶段变更】发现->品牌植入

2024/8/18 11:22:51 周裔锦
【出现困难】本项目采用EPC模式承建，后期运营方为“中国移动”，智能化总包为“鼎熙国讯”，设计方为“广东南方电信设计院”。已拜访总包和设计院，初步沟通得知，专网无线对讲系统可能没有在前期智能化设计里，后面可能会让运营方从运营费用里面出资建设，或者要跟业主沟通本系统是否要划到本次项目内建设。

', 'SPJ202408-002', '2024-10-09', 0, NULL, NULL, '2024-08-18 00:00:00', '2025-04-28 01:02:05.016368', 17);
INSERT INTO public.projects VALUES (289, '厦门嘉丽广场', '2024-09-27', '渠道跟进', '经销商', '不确定', NULL, NULL, '广州宇洪科技股份有限公司', NULL, '广东省工业设备安装有限公司', '招标中', '2024/10/9 17:08:15 周裔锦
【完善价格】 164492
2024/10/9 16:51:43 周裔锦
【完善价格】 152365
2024/10/8 周裔锦
【阶段变更】->招标中

', 'CPJ202409-012', '2024-10-09', 0, NULL, NULL, '2024-09-27 00:00:00', '2025-04-28 01:02:05.017166', 17);
INSERT INTO public.projects VALUES (290, '茂名南站综合交通枢纽配套工程一期', '2024-08-23', '销售重点', '销售', '不确定', NULL, NULL, NULL, NULL, '中冶交通建设集团有限公司', '发现', '2024/10/8 周裔锦
【阶段变更】品牌植入->发现

', 'SPJ202408-004', '2024-10-08', 0, NULL, NULL, '2024-08-23 00:00:00', '2025-04-28 01:02:05.018023', 17);
INSERT INTO public.projects VALUES (291, '华发冰雪世界项目', '2024-09-20', '销售重点', '销售', '不确定', NULL, '珠海华发实业股份有限公司', NULL, NULL, NULL, '发现', '2024/10/8 周裔锦
【阶段变更】品牌植入->发现

', 'SPJ202409-010', '2024-10-08', 0, NULL, NULL, '2024-09-20 00:00:00', '2025-04-28 01:02:05.018842', 17);
INSERT INTO public.projects VALUES (293, '厦门翔安新机场项目', '2024-09-27', '销售重点', '销售', '不确定', NULL, NULL, NULL, NULL, '厦门纵横集团科技股份有限公司', '发现', '2024/10/8 周裔锦
【阶段变更】品牌植入->发现

2024/9/27 周裔锦
【阶段变更】->品牌植入

', 'SPJ202409-014', '2024-10-08', 0, NULL, NULL, '2024-09-27 00:00:00', '2025-04-28 01:02:05.020487', 17);
INSERT INTO public.projects VALUES (294, '厦门天马第6代柔性AM-OLED生产线项目', '2024-09-27', '销售重点', '销售', '不确定', NULL, NULL, NULL, NULL, '厦门中智达信息科技有限公司', '发现', '2024/10/8 周裔锦
【阶段变更】品牌植入->发现

', 'SPJ202409-015', '2024-10-08', 0, NULL, NULL, '2024-09-27 00:00:00', '2025-04-28 01:02:05.021274', 17);
INSERT INTO public.projects VALUES (295, '宝华和平工业园总包项目', '2024-09-06', '销售重点', '销售', '不确定', NULL, '麦驰设计研究院', NULL, NULL, NULL, '品牌植入', '2024/9/6 14:21:43 周裔锦
【出现困难】当前项目已经设计完成，专网没有定品牌，估计20万金额。智能化总包不一定参与。

', 'SPJ202409-002', '2024-09-06', 0, NULL, NULL, '2024-09-06 00:00:00', '2025-04-28 01:02:05.022058', 17);
INSERT INTO public.projects VALUES (296, '佛山季华项目', '2024-07-19', '渠道跟进', '销售', '入围', NULL, NULL, '广州宇洪智能技术有限公司', NULL, '广州网远信息技术有限公司', '招标前', NULL, 'CPJ202407-009', '2024-07-19', 0, NULL, NULL, '2024-07-19 00:00:00', '2025-04-28 01:02:05.022828', 17);
INSERT INTO public.projects VALUES (297, '科思创E188区域材料增补', '2025-04-18', '业务机会', '销售', '入围', '科思创聚合物(中国)有限公司', NULL, NULL, NULL, NULL, '中标', '2025/4/18 10:26:11 徐昊
【授权编号】：添加   HY-APJ-202503-007

2025/4/2 10:13:50 方玲
【授权编号】：添加   HY-APJ-202503-007

2025/3/28 11:20:16 徐昊
【面价金额】：添加   2705.22

2025/3/28 11:19:27 徐昊
【当前阶段情况说明】：改变成   已完成合约签订并且供货

2025/3/17 09:44:25 方玲
【完善价格】 2706
', 'APJ-202503-007', '2025-04-18', 0, NULL, NULL, '2025-04-18 00:00:00', '2025-04-28 01:03:17.888703', 7);
INSERT INTO public.projects VALUES (298, '中芯南方高精度智能人员定位需求', '2025-04-02', '业务机会', '销售', '不确定', '中芯南方集成电路制造有限公司', NULL, NULL, NULL, NULL, '发现', '2025/4/14 徐昊
「马振邦」 中芯南方集成电路制造有限公司  和供应商根据上海厂和南方厂FAB区域的平面图后，向业主提出了方案和方案相关的终端形式，与业主分析了目前方案和终端的利弊，业主已接收提出的方案和终端的形式，业主方表示将在中芯南方内部进行方案讨论，后续继续跟踪；
2025/4/11 徐昊
「马振邦」 中芯南方集成电路制造有限公司  与供应商根据与业主确认的中芯南方/中芯上海厂的FAB三个区域的平面图，提出可行的硬件方案，选择高精度UWB及有源定位终端的方案，确定可提供的两种终端维护模式与业主下周进一步沟通；
2025/4/10 徐昊
「马振邦」 中芯南方集成电路制造有限公司  在中芯南方现场召开会议，与业主沟通高精度智能人员定位方案，本次沟通完全针对中芯南方与上海厂三个互通的fab区域的建筑结构，连廊通道互相关系等等，根据区域的入口/人员值守工况等等一一讨论定位的需求和终端的形式并且明确了软件功能的要求，会后会再和供应商沟通提出的有源终端的工作形式和呈现形式，然后再与业主沟通；
2025/4/7 徐昊
「马振邦」 中芯南方集成电路制造有限公司  与供应商沟通定位需求芯片厂的实际场景，根据芯片厂FAB区域的特殊流程，防护服防护装备消杀通道等等，筛选可行性，与业主方进一步商讨；
2025/4/2 13:22:31 徐昊
【授权编号】：添加   HY-APJ-202502-006

2025/4/1 徐昊
「马振邦」 中芯南方集成电路制造有限公司  与业主进一步确定以FAB区域为定位人员统计项目目标区域，结合进入FAB的人员工作流程（进入区域闸机/穿特定的防护服/通过特定消毒区域/指定离开通道）等特定场景特定流程特定区域来商榷定位基站和终端的形式；根据与业主沟通的信息与供应商联系，约定下周一供应商至公司沟通；
2025/3/28 11:17:36 徐昊
【面价金额】：添加   500000

2025/2/28 10:48:42 徐昊
【品牌情况】：添加   不确定
【当前阶段】：添加   发现

', 'APJ-202502-006', '2025-04-14', 0, NULL, NULL, '2025-04-02 00:00:00', '2025-04-28 01:03:17.893041', 7);
INSERT INTO public.projects VALUES (299, '中芯国际（深圳）厂FAB6二层三层CUB地下一层信号增补', '2025-04-02', '业务机会', '销售', '入围', '中芯国际集成电路制造(深圳)有限公司', NULL, NULL, NULL, NULL, '发现', '2025/4/11 11:12:28 徐昊
【完善价格】 74529
2025/4/10 徐昊
「石维」 中芯国际集成电路制造(深圳)有限公司  与深圳中芯国际ERC负责人沟通改造方案与2025系统维护测试两个方案的最终确认，对方根据方案报价向采购部门正式提出采购申请，预算通过后制作PO单；
2025/4/2 13:34:43 徐昊
【授权编号】：添加   HY-APJ-202503-012

2025/3/28 11:21:29 徐昊
【面价金额】：添加   120000

2025/3/20 10:21:13 徐昊
【当前阶段】：添加   发现

', 'APJ-202503-012', '2025-04-11', 0, NULL, NULL, '2025-04-02 00:00:00', '2025-04-28 01:03:17.896791', 7);
INSERT INTO public.projects VALUES (300, '深圳中芯国际无线对讲系统2025年系统维护检测', '2025-04-02', '业务机会', NULL, '入围', '中芯国际集成电路制造(深圳)有限公司', NULL, NULL, NULL, NULL, '发现', '2025/4/11 10:46:10 徐昊
【完善价格】 0
2025/4/2 13:42:17 徐昊
【当前阶段】：添加   发现
【授权编号】：添加   HY-APJ-202503-015

2025/3/28 11:21:57 徐昊
【面价金额】：添加   13000

', 'APJ-202503-015', '2025-04-11', 0, NULL, NULL, '2025-04-02 00:00:00', '2025-04-28 01:03:17.899338', 7);
INSERT INTO public.projects VALUES (301, '科思创193区域信号增补', '2025-04-02', '业务机会', '销售', '入围', '科思创聚合物(中国)有限公司', NULL, NULL, NULL, NULL, '发现', '2025/4/11 10:37:00 徐昊
【完善价格】 10337
2025/4/8 徐昊
「吴天杰」 科思创聚合物(中国)有限公司  沟通B193区域的实施方案，业主提出在是否能在B193一楼CCR控制室增加一副天线，复核设计图纸进行确认，方案其他业主已认可；
2025/4/3 徐昊
「吴天杰」 科思创聚合物(中国)有限公司  设计师已经完成B193区域的信号覆盖的方案和清单，商务在填写好清单价格后发给客户确认；
2025/4/2 13:30:31 徐昊
【授权编号】：添加   HY-APJ-202502-007

2025/2/28 10:47:10 徐昊
【当前阶段情况说明】：改变成   193区域茶水间信号较差，通话有断续，在提供茶水间信号增补的方案后，业主方表示由于193未做过室内信号覆盖，以前主要依靠室外信号的延申，所以希望这次能够把该楼宇做室内信号覆盖，已经安排设计师对193楼宇进行室内信号覆盖提供增补方案和清单，然后提交给业主

', 'APJ-202502-007', '2025-04-11', 0, NULL, NULL, '2025-04-02 00:00:00', '2025-04-28 01:03:17.901457', 7);
INSERT INTO public.projects VALUES (302, '浦东机场卫星厅无线对讲系统维护', '2025-04-02', '业务机会', '销售', '入围', '上海国际机场股份有限公司', NULL, NULL, NULL, NULL, '招标前', '2025/4/2 13:36:15 徐昊
【授权编号】：添加   HY-APJ-202503-013

2025/3/28 11:17:54 徐昊
【面价金额】：添加   800000

2025/3/20 10:08:21 徐昊
【当前阶段】：添加   招标前

', 'APJ-202503-013', '2025-04-02', 0, NULL, NULL, '2025-04-02 00:00:00', '2025-04-28 01:03:17.903643', 7);
INSERT INTO public.projects VALUES (305, '四川农村商业联合银行股份有限公司黄舣数 据中心机房', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '品牌植入', NULL, NULL, NULL, 0, NULL, NULL, '2025-04-11 00:00:00', '2025-04-30 00:00:00', 16);


--
-- Data for Name: actions; Type: TABLE DATA; Schema: public; Owner: pma_user
--

INSERT INTO public.actions VALUES (2, '2025-05-03', 13, 15, 221, '拜访沟通了南大项目上的品牌入围情况，品牌目前还未成功放入等待业主的会议确定', '2025-05-03 04:03:17.832507', 5);
INSERT INTO public.actions VALUES (3, '2025-05-03', 13, 15, 221, '拜访沟通了南大项目上的品牌入围情况，品牌目前还未成功放入等待业主的会议确定', '2025-05-03 04:18:49.75359', 5);
INSERT INTO public.actions VALUES (4, '2025-05-03', 13, 15, 221, '等待', '2025-05-03 04:19:34.14551', 5);
INSERT INTO public.actions VALUES (5, '2025-05-03', 13, 15, 221, '等待额', '2025-05-03 04:20:37.650003', 5);
INSERT INTO public.actions VALUES (6, '2025-05-03', 13, 15, 221, '测试进展', '2025-05-03 04:25:29.900877', 5);
INSERT INTO public.actions VALUES (7, '2025-05-03', 13, 15, 221, '测试', '2025-05-03 04:25:55.488062', 5);
INSERT INTO public.actions VALUES (8, '2025-05-03', 13, 15, 221, '更新品牌', '2025-05-03 07:58:49.445335', 5);
INSERT INTO public.actions VALUES (1, '2025-05-04', 13, 15, 221, '测试行动力', '2025-05-04 06:36:39.721444', 5);
INSERT INTO public.actions VALUES (9, '2025-05-04', 13, 15, 221, '继续测试', '2025-05-04 06:48:11.130517', 5);


--
-- Data for Name: affiliations; Type: TABLE DATA; Schema: public; Owner: pma_user
--

INSERT INTO public.affiliations VALUES (1, 20, 7, 1746419531.824926);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: pma_user
--



--
-- Data for Name: data_affiliations; Type: TABLE DATA; Schema: public; Owner: pma_user
--

INSERT INTO public.data_affiliations VALUES (1, 6, 4, 1744986414.278543);
INSERT INTO public.data_affiliations VALUES (2, 20, 7, 1746419531.824926);


--
-- Data for Name: product_categories; Type: TABLE DATA; Schema: public; Owner: pma_user
--

INSERT INTO public.product_categories VALUES (1, '基站', 'B', '核心交换层设备', '2025-04-22 23:21:42.420247', '2025-04-25 09:48:46.435854');
INSERT INTO public.product_categories VALUES (2, '合路平台', 'M', '', '2025-04-24 07:46:40.759023', '2025-04-25 09:49:25.406365');
INSERT INTO public.product_categories VALUES (3, '直放站', 'O', '', '2025-04-24 07:49:44.922729', '2025-04-25 09:49:33.407422');
INSERT INTO public.product_categories VALUES (4, '对讲机', 'R', '', '2025-04-22 23:36:12.707747', '2025-04-25 09:48:59.182939');
INSERT INTO public.product_categories VALUES (6, '功率/耦合器', 'S', '', '2025-04-24 23:33:16.087046', '2025-04-25 09:50:23.605273');
INSERT INTO public.product_categories VALUES (7, '天线', 'A', '', '2025-04-24 23:33:33.804228', '2025-04-25 09:50:30.187875');
INSERT INTO public.product_categories VALUES (8, '应用', 'L', '', '2025-04-24 23:33:46.820829', '2025-04-25 09:50:42.521192');
INSERT INTO public.product_categories VALUES (10, '配件', 'Y', '', '2025-04-24 23:34:20.205585', '2025-04-25 09:50:55.676612');


--
-- Data for Name: product_regions; Type: TABLE DATA; Schema: public; Owner: pma_user
--

INSERT INTO public.product_regions VALUES (1, '中国', 'A', '', '2025-04-24 13:10:26.789192');
INSERT INTO public.product_regions VALUES (2, '亚太', 'B', '', '2025-04-24 13:10:42.347967');
INSERT INTO public.product_regions VALUES (3, '欧洲', 'C', NULL, '2025-04-26 07:07:59.903453');
INSERT INTO public.product_regions VALUES (4, '北美', 'D', NULL, '2025-04-26 07:07:59.903759');
INSERT INTO public.product_regions VALUES (5, '南美', 'E', NULL, '2025-04-26 07:07:59.903792');
INSERT INTO public.product_regions VALUES (6, '中东', 'F', NULL, '2025-04-26 07:07:59.903815');
INSERT INTO public.product_regions VALUES (7, '非洲', 'G', NULL, '2025-04-26 07:07:59.903834');
INSERT INTO public.product_regions VALUES (8, '大洋洲', 'H', NULL, '2025-04-26 07:07:59.90385');


--
-- Data for Name: product_subcategories; Type: TABLE DATA; Schema: public; Owner: pma_user
--

INSERT INTO public.product_subcategories VALUES (1, 1, '消防救援对讲通信基站', 'I', '', 4, '2025-04-23 14:04:52.359072', '2025-04-25 13:03:05.491484');
INSERT INTO public.product_subcategories VALUES (2, 1, '常规数字基站', 'G', '', 2, '2025-04-23 00:43:11.930733', '2025-04-25 13:02:53.627153');
INSERT INTO public.product_subcategories VALUES (3, 1, '智能集群基站', 'H', '', 3, '2025-04-24 12:04:20.734878', '2025-04-25 13:02:53.627507');
INSERT INTO public.product_subcategories VALUES (4, 1, '数字智能信道机', 'D', '', 1, '2025-04-24 23:36:16.496589', '2025-04-25 13:02:53.626478');
INSERT INTO public.product_subcategories VALUES (5, 1, '信道机虚拟集群功能许可', 'C', '', 8, '2025-04-24 23:36:49.636312', '2025-04-25 13:03:18.168673');
INSERT INTO public.product_subcategories VALUES (6, 1, '虚拟集群服务器主机', '1', '', 6, '2025-04-24 23:36:58.811911', '2025-04-25 13:03:19.699711');
INSERT INTO public.product_subcategories VALUES (7, 1, '虚拟集群服务', 'E', '', 7, '2025-04-24 23:37:06.652735', '2025-04-25 13:03:19.699974');
INSERT INTO public.product_subcategories VALUES (8, 1, '广播多频点调频处理器', 'F', '', 5, '2025-04-24 23:37:20.290849', '2025-04-25 13:03:19.699142');
INSERT INTO public.product_subcategories VALUES (9, 2, '定向耦合合路器', 'A', '', 7, '2025-04-24 23:40:29.814626', '2025-04-25 07:40:29.814633');
INSERT INTO public.product_subcategories VALUES (10, 2, '分路器', 'B', '', 4, '2025-04-24 23:40:41.642009', '2025-04-25 07:40:41.642015');
INSERT INTO public.product_subcategories VALUES (11, 2, '多信道分合路器', 'C', '', 6, '2025-04-24 23:40:59.102466', '2025-04-25 07:40:59.102473');
INSERT INTO public.product_subcategories VALUES (12, 2, '信号剥离矩阵', 'D', '', 3, '2025-04-24 23:54:12.355449', '2025-04-25 07:54:12.355451');
INSERT INTO public.product_subcategories VALUES (13, 3, '常规射频直放站', 'A', '', 1, '2025-04-24 23:59:58.231543', '2025-04-25 12:54:25.207024');
INSERT INTO public.product_subcategories VALUES (14, 3, '智能光纤近端机', 'B', '', 5, '2025-04-25 00:00:04.335942', '2025-04-25 08:17:55.381762');
INSERT INTO public.product_subcategories VALUES (15, 2, '下行信号剥离器', 'E', '', 2, '2025-04-25 00:16:29.016775', '2025-04-25 08:16:29.016783');
INSERT INTO public.product_subcategories VALUES (16, 2, '上行信号剥离器', 'F', '', 1, '2025-04-25 00:16:55.163424', '2025-04-25 08:16:55.163427');
INSERT INTO public.product_subcategories VALUES (17, 2, '双工器', 'G', '', 5, '2025-04-25 00:17:11.658209', '2025-04-25 08:17:11.658212');
INSERT INTO public.product_subcategories VALUES (18, 2, '系统合路器', 'H', '', 8, '2025-04-25 00:17:20.953839', '2025-04-25 08:17:20.953844');
INSERT INTO public.product_subcategories VALUES (19, 2, '系统合路器 | 供电', 'I', '', 9, '2025-04-25 00:17:29.078049', '2025-04-25 08:17:29.078055');
INSERT INTO public.product_subcategories VALUES (20, 3, '智能光纤远端直放站', 'C', '', 6, '2025-04-25 00:18:02.140578', '2025-04-25 08:18:02.140585');
INSERT INTO public.product_subcategories VALUES (21, 3, '数字智能光纤近端机', 'D', '', 2, '2025-04-25 00:18:10.874507', '2025-04-26 10:28:10.74907');
INSERT INTO public.product_subcategories VALUES (22, 3, '数字智能光纤', 'E', '', 4, '2025-04-25 00:18:18.555414', '2025-04-26 10:28:01.177677');
INSERT INTO public.product_subcategories VALUES (23, 3, '数字智能光纤交织型远端直放站', 'F', '', 3, '2025-04-25 00:18:26.749583', '2025-04-26 10:28:10.74971');
INSERT INTO public.product_subcategories VALUES (24, 3, '馈电模组', 'G', '', 8, '2025-04-25 00:18:35.586307', '2025-04-26 11:26:18.027559');
INSERT INTO public.product_subcategories VALUES (25, 6, '定向耦合器', 'A', '', 3, '2025-04-25 00:36:50.161537', '2025-04-25 08:36:50.161545');
INSERT INTO public.product_subcategories VALUES (26, 6, '功率分配器', 'B', '', 1, '2025-04-25 00:36:57.786156', '2025-04-25 08:36:57.786162');
INSERT INTO public.product_subcategories VALUES (27, 6, '功率分配器', 'C', '', 2, '2025-04-25 00:37:08.360849', '2025-04-25 08:37:08.360853');
INSERT INTO public.product_subcategories VALUES (28, 6, '馈电功率分配器', 'D', '', 4, '2025-04-25 00:37:49.828753', '2025-04-25 08:37:49.828759');
INSERT INTO public.product_subcategories VALUES (29, 6, '馈电定向耦合器', 'E', '', 5, '2025-04-25 00:38:00.368274', '2025-04-25 08:38:00.36828');
INSERT INTO public.product_subcategories VALUES (30, 7, '室内全向吸顶天线', 'A', '', 1, '2025-04-25 00:38:18.705562', '2025-04-25 08:38:18.705569');
INSERT INTO public.product_subcategories VALUES (31, 7, '超薄室内全向吸顶天线', 'B', '', 7, '2025-04-25 00:38:26.623988', '2025-04-25 08:38:26.623994');
INSERT INTO public.product_subcategories VALUES (32, 7, '智能室内全向吸顶天线', 'C', '', 5, '2025-04-25 00:38:50.089886', '2025-04-25 08:38:50.089892');
INSERT INTO public.product_subcategories VALUES (33, 7, '智能室内蓝牙全向吸顶天线', 'D', '', 6, '2025-04-25 00:39:10.918878', '2025-04-25 08:39:10.918884');
INSERT INTO public.product_subcategories VALUES (34, 7, '室外定向板状天线', 'E', '', 4, '2025-04-25 00:39:18.454577', '2025-04-25 08:39:18.454583');
INSERT INTO public.product_subcategories VALUES (35, 7, '室外全向玻璃钢天线', 'F', '', 2, '2025-04-25 00:39:27.419476', '2025-04-25 08:39:27.419479');
INSERT INTO public.product_subcategories VALUES (36, 7, '室外八木定向天线', 'G', '', 3, '2025-04-25 00:39:38.820347', '2025-04-25 08:39:38.820349');
INSERT INTO public.product_subcategories VALUES (37, 7, '防爆型高防护全向天线', 'H', '', 8, '2025-04-25 00:39:46.887715', '2025-04-25 08:39:46.887721');
INSERT INTO public.product_subcategories VALUES (38, 4, 'DMR常规对讲机', 'G', '', 1, '2025-04-25 00:40:18.125842', '2025-04-25 09:54:16.257293');
INSERT INTO public.product_subcategories VALUES (39, 4, 'DMR智能对讲机', 'D', '', 2, '2025-04-25 00:40:26.330632', '2025-04-25 09:54:35.551401');
INSERT INTO public.product_subcategories VALUES (40, 4, '常规锂电池板', 'C', '', 4, '2025-04-25 00:40:36.17181', '2025-04-25 08:40:36.171816');
INSERT INTO public.product_subcategories VALUES (41, 4, '智能锂电池板', 'S', '', 7, '2025-04-25 00:40:43.687131', '2025-04-25 09:54:54.369159');
INSERT INTO public.product_subcategories VALUES (42, 4, '智能多联充电器', 'E', '', 5, '2025-04-25 00:40:53.825266', '2025-04-25 08:40:53.82527');
INSERT INTO public.product_subcategories VALUES (43, 4, '智能多联充电栈', 'F', '', 6, '2025-04-25 00:41:03.504495', '2025-04-25 08:41:03.504505');
INSERT INTO public.product_subcategories VALUES (44, 4, '多联充电柜', 'B', '', 3, '2025-04-25 00:41:09.771136', '2025-04-25 09:55:17.908559');
INSERT INTO public.product_subcategories VALUES (45, 8, '网关服务器主机', 'A', '', 7, '2025-04-25 00:41:48.804359', '2025-04-25 08:41:48.804366');
INSERT INTO public.product_subcategories VALUES (46, 8, '网讯网关服务 软件', 'B', '', 12, '2025-04-25 00:42:00.62644', '2025-04-25 08:42:00.626446');
INSERT INTO public.product_subcategories VALUES (47, 8, '平台服务器主机', 'C', '', 4, '2025-04-25 00:42:08.637057', '2025-04-25 08:42:08.637062');
INSERT INTO public.product_subcategories VALUES (48, 8, '网讯平台服务 软件', 'D', '', 10, '2025-04-25 00:42:16.832686', '2025-04-25 08:42:16.832693');
INSERT INTO public.product_subcategories VALUES (49, 8, '系统工作台', 'E', '', 6, '2025-04-25 00:42:24.612347', '2025-04-25 08:42:24.612353');
INSERT INTO public.product_subcategories VALUES (50, 8, '网讯平台在线巡检功能', 'F', '', 9, '2025-04-25 00:42:31.633327', '2025-04-25 08:42:31.633333');
INSERT INTO public.product_subcategories VALUES (51, 8, '网讯平台人员分布功能', 'G', '', 8, '2025-04-25 00:42:38.607732', '2025-04-25 08:42:38.607739');
INSERT INTO public.product_subcategories VALUES (52, 8, '网讯平台终端录音功能', 'H', '', 11, '2025-04-25 00:42:47.051361', '2025-04-25 08:42:47.051366');
INSERT INTO public.product_subcategories VALUES (53, 8, '运维工具包', 'I', '', 14, '2025-04-25 00:42:56.050105', '2025-04-25 08:42:56.050112');
INSERT INTO public.product_subcategories VALUES (54, 8, '消防救援通信系统资源管理', 'J', '', 5, '2025-04-25 00:43:02.403363', '2025-04-25 08:43:02.403369');
INSERT INTO public.product_subcategories VALUES (55, 8, '信道机接入许可', 'K', '', 2, '2025-04-25 00:43:09.774004', '2025-04-25 08:43:09.774011');
INSERT INTO public.product_subcategories VALUES (56, 8, '远端站接入许可', 'L', '', 15, '2025-04-25 00:43:15.775442', '2025-04-25 08:43:15.775448');
INSERT INTO public.product_subcategories VALUES (57, 8, '对讲机终端接入许可', 'M', '', 3, '2025-04-25 00:43:21.474339', '2025-04-25 08:43:21.474345');
INSERT INTO public.product_subcategories VALUES (58, 8, '蓝牙定位信标+许可证', 'N', '', 13, '2025-04-25 00:43:27.392745', '2025-04-25 08:43:27.392751');
INSERT INTO public.product_subcategories VALUES (59, 8, 'MOTOROLA 信道服务软件', 'O', '', 1, '2025-04-25 00:43:33.973843', '2025-04-25 08:43:33.973848');
INSERT INTO public.product_subcategories VALUES (60, 3, '防爆光纤远端直放站', 'X', '', 7, '2025-04-26 03:26:10.330364', '2025-04-26 11:26:18.026789');


--
-- Data for Name: dev_products; Type: TABLE DATA; Schema: public; Owner: pma_user
--

INSERT INTO public.dev_products VALUES (1, 3, 13, 1, 'E-BDA410B-LT', 'E-BDA410B-LT', '研发中', '套', NULL, '研发一款采用全新的壁挂机箱和内置10W放大模块的 同轴电缆放大器，具备和2W放大器一样的功能', 'uploads/products/b1553cd3be894d7bb3d3202f2fd9272c_Screenshot_2025-04-26_at_09.36.01.png', '2025-04-26 01:35:27.145947', '2025-04-26 05:35:56.955025', NULL, 5, 'OAA2NH71');
INSERT INTO public.dev_products VALUES (2, 3, 13, 1, 'E-BDA410B-LT', 'E-BDA410B-LT', '研发中', '套', NULL, '', 'uploads/products/4092462f90944a37a4ef32654ac1c745_Screenshot_2025-04-26_at_09.36.01.png', '2025-04-26 02:04:11.235883', '2025-04-26 05:35:56.955735', NULL, 5, 'OAARN0KA');
INSERT INTO public.dev_products VALUES (3, 3, 20, 1, 'RFT-BDA410 LT/M', 'RFT-BDA410 LT/M', '研发中', '套', NULL, '', 'uploads/products/475f89d4939541ff80695c10dfdaee04_Screenshot_2025-04-26_at_09.36.01.png', '2025-04-26 03:10:38.83065', '2025-04-26 05:35:56.956344', NULL, 5, 'OCAA4R71');
INSERT INTO public.dev_products VALUES (4, 3, 13, 1, 'E-BDA400B LT', 'E-BDA400B LT', '研发中', '', NULL, '', NULL, '2025-04-26 05:35:30.182401', '2025-04-26 05:35:30.182407', NULL, 5, 'OAARPI9X');
INSERT INTO public.dev_products VALUES (5, 3, 13, 1, 'E-BDA400B LT', 'E-BDA400B LT', '研发中', '', NULL, '', NULL, '2025-04-26 06:19:33.620345', '2025-04-26 06:19:33.620354', NULL, 5, 'OAANAAAA');


--
-- Data for Name: dev_product_specs; Type: TABLE DATA; Schema: public; Owner: pma_user
--

INSERT INTO public.dev_product_specs VALUES (1, 1, '工作频率', '412-416MHz（下行）/ 402-406MHz（上行）', 'A');
INSERT INTO public.dev_product_specs VALUES (2, 1, '最大输出功率', '40±1dBm', NULL);
INSERT INTO public.dev_product_specs VALUES (3, 1, '上下行增益', '50±2dB', 'A');
INSERT INTO public.dev_product_specs VALUES (4, 1, '增益调节范围', '0-30dB', 'A');
INSERT INTO public.dev_product_specs VALUES (5, 1, '增益调节步进', '1dB', 'A');
INSERT INTO public.dev_product_specs VALUES (6, 1, '噪声系数', '≤6', 'A');
INSERT INTO public.dev_product_specs VALUES (7, 1, '时延', '≤5 us', 'A');
INSERT INTO public.dev_product_specs VALUES (8, 1, '带内波动', '≤3dB', 'A');
INSERT INTO public.dev_product_specs VALUES (9, 1, '上下行隔离度', '≥75dB', 'A');
INSERT INTO public.dev_product_specs VALUES (10, 1, '驻波比', '≤1.5', 'A');
INSERT INTO public.dev_product_specs VALUES (11, 1, '安装方式', '室内外 壁挂', '室');
INSERT INTO public.dev_product_specs VALUES (12, 1, '防护等级', 'IP65', 'I');
INSERT INTO public.dev_product_specs VALUES (13, 1, '工作带宽', '4MHz', 'M');
INSERT INTO public.dev_product_specs VALUES (14, 2, '工作频率', '420-424MHz（下行）/ 410-414MHz（上行）', 'N');
INSERT INTO public.dev_product_specs VALUES (15, 2, '最大输出功率', '40±1dBm', NULL);
INSERT INTO public.dev_product_specs VALUES (16, 2, '上下行增益', '50±2dB', 'A');
INSERT INTO public.dev_product_specs VALUES (17, 2, '增益调节范围', '0-30dB', 'A');
INSERT INTO public.dev_product_specs VALUES (18, 2, '增益调节步进', '1dB', 'A');
INSERT INTO public.dev_product_specs VALUES (19, 2, '噪声系数', '≤6', 'A');
INSERT INTO public.dev_product_specs VALUES (20, 2, '时延', '≤5 us', 'A');
INSERT INTO public.dev_product_specs VALUES (21, 2, '带内波动', '≤3dB', 'A');
INSERT INTO public.dev_product_specs VALUES (22, 2, '上下行隔离度', '≥75dB', 'A');
INSERT INTO public.dev_product_specs VALUES (23, 2, '驻波比', '≤1.5', 'A');
INSERT INTO public.dev_product_specs VALUES (24, 2, '安装方式', '室内外 壁挂', '室');
INSERT INTO public.dev_product_specs VALUES (25, 2, '防护等级', 'IP65', 'I');
INSERT INTO public.dev_product_specs VALUES (26, 2, '工作带宽', '4MHz', 'M');
INSERT INTO public.dev_product_specs VALUES (27, 2, '工作频率', '420-424MHz（下行）/ 410-414MHz（上行）', 'N');
INSERT INTO public.dev_product_specs VALUES (28, 2, '最大输出功率', '40±1dBm', NULL);
INSERT INTO public.dev_product_specs VALUES (29, 2, '上下行增益', '50±2dB', 'A');
INSERT INTO public.dev_product_specs VALUES (30, 2, '增益调节范围', '0-30dB', 'A');
INSERT INTO public.dev_product_specs VALUES (31, 2, '增益调节步进', '1dB', 'A');
INSERT INTO public.dev_product_specs VALUES (32, 2, '噪声系数', '≤6', 'A');
INSERT INTO public.dev_product_specs VALUES (33, 2, '时延', '≤5 us', 'A');
INSERT INTO public.dev_product_specs VALUES (34, 2, '带内波动', '≤3dB', 'A');
INSERT INTO public.dev_product_specs VALUES (35, 2, '上下行隔离度', '≥75dB', 'A');
INSERT INTO public.dev_product_specs VALUES (36, 2, '驻波比', '≤1.5', 'A');
INSERT INTO public.dev_product_specs VALUES (37, 2, '安装方式', '室内外 壁挂', '室');
INSERT INTO public.dev_product_specs VALUES (38, 2, '防护等级', 'IP65', 'I');
INSERT INTO public.dev_product_specs VALUES (39, 2, '工作带宽', '4MHz', 'M');
INSERT INTO public.dev_product_specs VALUES (40, 3, '工作频率', '420-424MHz（下行） / 410-414MHz（上行）', 'A');
INSERT INTO public.dev_product_specs VALUES (41, 3, '最大输出功率', '40±1dBm', 'A');
INSERT INTO public.dev_product_specs VALUES (42, 3, '增益调节范围', '0-30dB', 'A');
INSERT INTO public.dev_product_specs VALUES (43, 3, '增益调节步进', '1dB', 'A');
INSERT INTO public.dev_product_specs VALUES (44, 3, '噪声系数', '≤6', 'A');
INSERT INTO public.dev_product_specs VALUES (45, 3, '时延', '≤5 us', 'A');
INSERT INTO public.dev_product_specs VALUES (46, 3, '带内波动', '≤3dB', 'A');
INSERT INTO public.dev_product_specs VALUES (47, 3, '上下行隔离度', '≥75dB', 'A');
INSERT INTO public.dev_product_specs VALUES (48, 3, '驻波比', '≤1.5', 'A');
INSERT INTO public.dev_product_specs VALUES (49, 3, '安装方式', '壁挂 室外', '壁');
INSERT INTO public.dev_product_specs VALUES (50, 3, '防护等级', 'IP65', 'I');
INSERT INTO public.dev_product_specs VALUES (51, 3, '上下行增益', '50±2dB', 'A');
INSERT INTO public.dev_product_specs VALUES (52, 3, '光口数量', '≥1', NULL);
INSERT INTO public.dev_product_specs VALUES (53, 3, '带宽', '4MHz', 'F');
INSERT INTO public.dev_product_specs VALUES (54, 4, '工作频率', '412-416MHz（下行）/ 402-406MHz（上行）', 'A');
INSERT INTO public.dev_product_specs VALUES (55, 4, '最大输出功率', '10W （40±1dBm）', 'A');
INSERT INTO public.dev_product_specs VALUES (56, 4, '上下行增益', '50±2dB', 'A');
INSERT INTO public.dev_product_specs VALUES (57, 4, '增益调节范围', '0-30dB', 'A');
INSERT INTO public.dev_product_specs VALUES (58, 4, '增益调节步进', '1dB', 'A');
INSERT INTO public.dev_product_specs VALUES (59, 4, '工作频率', '412-416MHz（下行）/ 402-406MHz（上行）', 'A');
INSERT INTO public.dev_product_specs VALUES (60, 4, '最大输出功率', '10W （40±1dBm）', 'A');
INSERT INTO public.dev_product_specs VALUES (61, 4, '上下行增益', '50±2dB', 'A');
INSERT INTO public.dev_product_specs VALUES (62, 4, '增益调节范围', '0-30dB', 'A');
INSERT INTO public.dev_product_specs VALUES (63, 4, '增益调节步进', '1dB', 'A');
INSERT INTO public.dev_product_specs VALUES (64, 5, '工作频率', '420-424MHz（下行）/ 410-414MHz（上行）', 'N');
INSERT INTO public.dev_product_specs VALUES (65, 5, '最大输出功率', '10W （40±1dBm）', 'A');
INSERT INTO public.dev_product_specs VALUES (66, 5, '上下行增益', '50±2dB', 'A');
INSERT INTO public.dev_product_specs VALUES (67, 5, '增益调节范围', '0-30dB', 'A');
INSERT INTO public.dev_product_specs VALUES (68, 5, '增益调节步进', '1dB', 'A');
INSERT INTO public.dev_product_specs VALUES (69, 5, '噪声系数', '≤6', 'A');
INSERT INTO public.dev_product_specs VALUES (70, 5, '工作频率', '420-424MHz（下行）/ 410-414MHz（上行）', 'N');
INSERT INTO public.dev_product_specs VALUES (71, 5, '最大输出功率', '10W （40±1dBm）', 'A');
INSERT INTO public.dev_product_specs VALUES (72, 5, '上下行增益', '50±2dB', 'A');
INSERT INTO public.dev_product_specs VALUES (73, 5, '增益调节范围', '0-30dB', 'A');
INSERT INTO public.dev_product_specs VALUES (74, 5, '增益调节步进', '1dB', 'A');
INSERT INTO public.dev_product_specs VALUES (75, 5, '噪声系数', '≤6', 'A');


--
-- Data for Name: dictionaries; Type: TABLE DATA; Schema: public; Owner: pma_user
--

INSERT INTO public.dictionaries VALUES (1, 'role', 'admin', '系统管理员', true, 10, 1745667318.529633, 1745723213.991283);
INSERT INTO public.dictionaries VALUES (2, 'role', 'user', '普通用户', true, 20, 1745716772.6006558, 1745716772.600658);
INSERT INTO public.dictionaries VALUES (10, 'role', 'dealer', '代理商', true, 100, 1745716772.6010182, 1745716772.6010182);
INSERT INTO public.dictionaries VALUES (13, 'role', 'solution_manager', '解决方案经理', true, 130, 1745716772.6038039, 1745716963.2245371);
INSERT INTO public.dictionaries VALUES (14, 'role', 'sales_director', '营销总监', true, 140, 1745716772.604226, 1745717015.457986);
INSERT INTO public.dictionaries VALUES (17, 'role', 'product_manager', '产品经理', true, 170, 1745716772.6054158, 1745717037.573678);
INSERT INTO public.dictionaries VALUES (19, 'role', 'channel_manager	', '渠道经理', true, 190, 1745716772.60614, 1745717049.3889668);
INSERT INTO public.dictionaries VALUES (20, 'role', 'service_manager', '服务经理', true, 200, 1745716772.606497, 1745717151.156446);
INSERT INTO public.dictionaries VALUES (21, 'role', 'finace_director', '财务总监', true, 210, 1745716772.606807, 1746440593.9798028);
INSERT INTO public.dictionaries VALUES (18, 'role', 'customer_sales', '客户销售', true, 180, 1745716772.605782, 1746440605.527481);
INSERT INTO public.dictionaries VALUES (16, 'role', 'sales_manager', '销售经理', true, 160, 1745716772.6050391, 1746440616.621388);
INSERT INTO public.dictionaries VALUES (24, 'department', 'sales_dep', '销售部', true, 10, 1746443555.595523, 1746443555.595524);
INSERT INTO public.dictionaries VALUES (25, 'department', 'rd_dep', '产品和解决方案部', true, 20, 1746443615.569504, 1746443615.569506);
INSERT INTO public.dictionaries VALUES (26, 'department', 'service_dep', '服务部', true, 30, 1746443643.629589, 1746443643.629589);
INSERT INTO public.dictionaries VALUES (27, 'company', 'evertacsh_company', '和源通信（上海）股份有限公司', true, 10, 1746443714.853514, 1746443714.853515);
INSERT INTO public.dictionaries VALUES (12, 'role', 'business_admin', '商务助理', true, 120, 1745716772.603283, 1746443802.069152);
INSERT INTO public.dictionaries VALUES (28, 'role', 'ceo', '总经理', true, 220, 1746443836.45206, 1746443836.452061);


--
-- Data for Name: permissions; Type: TABLE DATA; Schema: public; Owner: pma_user
--

INSERT INTO public.permissions VALUES (1, 5, 'project', true, true, true, true);
INSERT INTO public.permissions VALUES (2, 5, 'customer', true, true, true, true);
INSERT INTO public.permissions VALUES (3, 5, 'quotation', true, true, true, true);
INSERT INTO public.permissions VALUES (4, 5, 'product', true, true, true, true);
INSERT INTO public.permissions VALUES (5, 5, 'user', true, true, true, true);
INSERT INTO public.permissions VALUES (6, 5, 'permission', true, true, true, true);
INSERT INTO public.permissions VALUES (13, 7, 'project', true, true, true, true);
INSERT INTO public.permissions VALUES (14, 7, 'customer', true, true, true, true);
INSERT INTO public.permissions VALUES (15, 7, 'quotation', true, true, true, true);
INSERT INTO public.permissions VALUES (16, 7, 'product', true, false, false, false);
INSERT INTO public.permissions VALUES (17, 7, 'user', false, false, false, false);
INSERT INTO public.permissions VALUES (18, 7, 'permission', false, false, false, false);
INSERT INTO public.permissions VALUES (38, 20, 'project', true, true, true, true);
INSERT INTO public.permissions VALUES (39, 20, 'customer', true, true, true, true);
INSERT INTO public.permissions VALUES (40, 20, 'quotation', true, true, true, true);
INSERT INTO public.permissions VALUES (41, 20, 'product', true, false, false, false);
INSERT INTO public.permissions VALUES (42, 20, 'product_code', false, false, false, false);
INSERT INTO public.permissions VALUES (43, 20, 'user', false, false, false, false);
INSERT INTO public.permissions VALUES (44, 20, 'permission', false, false, false, false);
INSERT INTO public.permissions VALUES (52, 6, 'project', true, true, true, true);
INSERT INTO public.permissions VALUES (53, 6, 'customer', true, true, true, true);
INSERT INTO public.permissions VALUES (54, 6, 'quotation', true, true, true, true);
INSERT INTO public.permissions VALUES (55, 6, 'product', true, true, true, true);
INSERT INTO public.permissions VALUES (56, 6, 'product_code', true, true, true, true);
INSERT INTO public.permissions VALUES (57, 6, 'user', false, false, false, false);
INSERT INTO public.permissions VALUES (58, 6, 'permission', false, false, false, false);


--
-- Data for Name: product_code_fields; Type: TABLE DATA; Schema: public; Owner: pma_user
--

INSERT INTO public.product_code_fields VALUES (1, 1, '频率范围', NULL, '', 'spec', 1, 1, true, true, '2025-04-24 13:03:54.647207', '2025-04-24 21:03:54.647217');
INSERT INTO public.product_code_fields VALUES (2, 1, '带宽', NULL, '', 'spec', 2, 1, true, true, '2025-04-24 13:04:21.945066', '2025-04-24 21:04:21.945069');
INSERT INTO public.product_code_fields VALUES (3, 2, '频率范围', NULL, '', 'spec', 1, 1, true, true, '2025-04-24 13:04:55.357523', '2025-04-24 21:04:55.357534');
INSERT INTO public.product_code_fields VALUES (4, 2, '带宽', NULL, '', 'spec', 2, 1, true, true, '2025-04-24 13:05:06.343133', '2025-04-24 21:05:06.343143');
INSERT INTO public.product_code_fields VALUES (5, 1, '中国', 'A', '', 'origin_location', 1, 1, true, true, '2025-04-24 16:04:57.516746', '2025-04-25 00:07:57.333313');
INSERT INTO public.product_code_fields VALUES (6, 1, '亚太', 'B', '', 'origin_location', 1, 1, true, true, '2025-04-24 16:05:25.270888', '2025-04-25 00:05:25.275092');
INSERT INTO public.product_code_fields VALUES (8, 3, '频率范围', NULL, '', 'spec', 1, 1, true, true, '2025-04-24 16:19:24.672162', '2025-04-25 00:19:24.672169');
INSERT INTO public.product_code_fields VALUES (9, 3, '越南', 'C', '', 'origin_location', 1, 1, true, true, '2025-04-24 16:29:11.015821', '2025-04-25 00:29:11.019415');
INSERT INTO public.product_code_fields VALUES (10, 2, '颜色', NULL, '', 'spec', 3, 1, true, true, '2025-04-24 16:30:00.658174', '2025-04-25 00:30:00.65818');
INSERT INTO public.product_code_fields VALUES (11, 4, '频率范围', NULL, '', 'spec', 1, 1, true, true, '2025-04-25 05:07:12.816972', '2025-04-25 13:13:07.301201');
INSERT INTO public.product_code_fields VALUES (12, 4, '带宽', NULL, '', 'spec', 2, 1, true, true, '2025-04-25 05:13:33.315139', '2025-04-25 13:13:33.315149');
INSERT INTO public.product_code_fields VALUES (13, 4, '功率', NULL, '从产品 Mark1000 MAX 自动添加的规格字段', 'spec', 3, 1, false, true, '2025-04-25 10:32:13.676155', '2025-04-25 18:32:13.676159');
INSERT INTO public.product_code_fields VALUES (14, 16, '频率范围', NULL, '从产品 R-EVDC-BLST-U 自动添加的规格字段', 'spec', 1, 1, false, true, '2025-04-25 13:51:56.17179', '2025-04-25 21:51:56.1718');
INSERT INTO public.product_code_fields VALUES (15, 4, '阻抗', NULL, '', 'spec', 4, 1, true, true, '2025-04-25 23:58:31.339286', '2025-04-26 07:58:31.339291');
INSERT INTO public.product_code_fields VALUES (16, 4, '电源类型', NULL, '', 'spec', 5, 1, true, true, '2025-04-25 23:58:42.621219', '2025-04-26 07:58:42.621227');
INSERT INTO public.product_code_fields VALUES (17, 13, '工作频率', NULL, '从产品 E-BDA410B-LT 自动添加的规格字段', 'spec', 0, 1, true, true, '2025-04-26 01:35:27.152086', '2025-04-26 11:04:14.472249');
INSERT INTO public.product_code_fields VALUES (18, 13, '最大输出功率', NULL, '从产品 E-BDA410B-LT 自动添加的规格字段', 'spec', 1, 1, true, true, '2025-04-26 01:35:27.15482', '2025-04-26 11:04:14.47293');
INSERT INTO public.product_code_fields VALUES (19, 13, '上下行增益', NULL, '从产品 E-BDA410B-LT 自动添加的规格字段', 'spec', 2, 1, true, true, '2025-04-26 01:35:27.155789', '2025-04-26 11:04:14.473233');
INSERT INTO public.product_code_fields VALUES (20, 13, '增益调节范围', NULL, '从产品 E-BDA410B-LT 自动添加的规格字段', 'spec', 4, 1, false, false, '2025-04-26 01:35:27.15664', '2025-04-26 11:04:14.473663');
INSERT INTO public.product_code_fields VALUES (21, 13, '增益调节步进', NULL, '从产品 E-BDA410B-LT 自动添加的规格字段', 'spec', 5, 1, false, false, '2025-04-26 01:35:27.157521', '2025-04-26 11:04:14.473848');
INSERT INTO public.product_code_fields VALUES (22, 13, '噪声系数', NULL, '从产品 E-BDA410B-LT 自动添加的规格字段', 'spec', 6, 1, false, false, '2025-04-26 01:35:27.158359', '2025-04-26 11:04:14.47404');
INSERT INTO public.product_code_fields VALUES (23, 13, '时延', NULL, '从产品 E-BDA410B-LT 自动添加的规格字段', 'spec', 7, 1, false, false, '2025-04-26 01:35:27.159167', '2025-04-26 11:04:14.474246');
INSERT INTO public.product_code_fields VALUES (24, 13, '带内波动', NULL, '从产品 E-BDA410B-LT 自动添加的规格字段', 'spec', 8, 1, false, false, '2025-04-26 01:35:27.16021', '2025-04-26 11:04:14.474426');
INSERT INTO public.product_code_fields VALUES (25, 13, '上下行隔离度', NULL, '从产品 E-BDA410B-LT 自动添加的规格字段', 'spec', 9, 1, false, false, '2025-04-26 01:35:27.162642', '2025-04-26 11:04:14.474604');
INSERT INTO public.product_code_fields VALUES (26, 13, '驻波比', NULL, '从产品 E-BDA410B-LT 自动添加的规格字段', 'spec', 10, 1, false, false, '2025-04-26 01:35:27.164105', '2025-04-26 11:04:14.474778');
INSERT INTO public.product_code_fields VALUES (27, 13, '安装方式', NULL, '从产品 E-BDA410B-LT 自动添加的规格字段', 'spec', 12, 1, true, true, '2025-04-26 01:35:27.165595', '2025-04-26 11:04:14.475446');
INSERT INTO public.product_code_fields VALUES (28, 13, '防护等级', NULL, '从产品 E-BDA410B-LT 自动添加的规格字段', 'spec', 11, 1, false, false, '2025-04-26 01:35:27.166878', '2025-04-26 11:04:14.475253');
INSERT INTO public.product_code_fields VALUES (29, 13, '工作带宽', NULL, '', 'spec', 3, 1, true, true, '2025-04-26 01:39:44.034071', '2025-04-26 11:04:14.473475');
INSERT INTO public.product_code_fields VALUES (30, 20, '工作频率', NULL, '', 'spec', 0, 1, true, true, '2025-04-26 02:13:26.25419', '2025-04-26 11:14:23.559732');
INSERT INTO public.product_code_fields VALUES (31, 20, '最大输出功率', NULL, '', 'spec', 1, 1, true, true, '2025-04-26 02:13:47.2431', '2025-04-26 11:14:23.560384');
INSERT INTO public.product_code_fields VALUES (32, 20, '增益调节范围', NULL, '', 'spec', 6, 1, false, false, '2025-04-26 02:14:03.887624', '2025-04-26 11:14:23.561495');
INSERT INTO public.product_code_fields VALUES (33, 20, '增益调节步进', NULL, '', 'spec', 7, 1, true, false, '2025-04-26 02:14:20.347429', '2025-04-26 11:14:23.561687');
INSERT INTO public.product_code_fields VALUES (34, 20, '噪声系数', NULL, '', 'spec', 8, 1, false, false, '2025-04-26 02:14:54.630395', '2025-04-26 11:14:23.561891');
INSERT INTO public.product_code_fields VALUES (35, 20, '时延', NULL, '', 'spec', 9, 1, false, false, '2025-04-26 02:19:55.576082', '2025-04-26 11:14:23.562084');
INSERT INTO public.product_code_fields VALUES (36, 20, '带内波动', NULL, '', 'spec', 10, 1, false, false, '2025-04-26 02:22:51.869022', '2025-04-26 11:14:23.562278');
INSERT INTO public.product_code_fields VALUES (37, 20, '上下行隔离度', NULL, '', 'spec', 11, 1, false, false, '2025-04-26 02:23:36.18269', '2025-04-26 11:14:23.562446');
INSERT INTO public.product_code_fields VALUES (38, 20, '驻波比', NULL, '', 'spec', 12, 1, false, false, '2025-04-26 02:23:48.633014', '2025-04-26 11:14:23.562621');
INSERT INTO public.product_code_fields VALUES (39, 20, '安装方式', NULL, '', 'spec', 4, 1, true, true, '2025-04-26 02:24:04.999174', '2025-04-26 11:14:29.897417');
INSERT INTO public.product_code_fields VALUES (40, 20, '防护等级', NULL, '', 'spec', 13, 1, false, false, '2025-04-26 02:24:20.281865', '2025-04-26 11:14:23.562791');
INSERT INTO public.product_code_fields VALUES (41, 20, '上下行增益', NULL, '', 'spec', 5, 1, true, false, '2025-04-26 02:25:40.380485', '2025-04-26 11:14:23.561298');
INSERT INTO public.product_code_fields VALUES (42, 20, '光口数量', NULL, '从产品 RFT-BDA410 LT/M 自动添加的规格字段', 'spec', 3, 1, false, true, '2025-04-26 03:10:38.84042', '2025-04-26 11:14:23.560886');
INSERT INTO public.product_code_fields VALUES (43, 20, '带宽', NULL, '', 'spec', 2, 1, true, true, '2025-04-26 03:12:50.918148', '2025-04-26 11:14:23.560636');
INSERT INTO public.product_code_fields VALUES (44, 60, '工作频率', NULL, '', 'spec', 1, 1, true, true, '2025-04-26 03:26:44.269755', '2025-04-26 11:26:44.269774');


--
-- Data for Name: product_code_field_options; Type: TABLE DATA; Schema: public; Owner: pma_user
--

INSERT INTO public.product_code_field_options VALUES (1, 5, '中国', 'A', '自动生成的销售区域编码: 中国', true, 0, '2025-04-24 16:04:57.521844', '2025-04-25 00:07:57.336829');
INSERT INTO public.product_code_field_options VALUES (2, 6, '亚太', 'B', '自动生成的销售区域编码: 亚太', true, 0, '2025-04-24 16:05:25.275686', '2025-04-25 00:05:25.275689');
INSERT INTO public.product_code_field_options VALUES (4, 8, '150-170MHz', 'L', '', true, 0, '2025-04-24 16:19:37.975551', '2025-04-25 00:19:37.975559');
INSERT INTO public.product_code_field_options VALUES (5, 9, '越南', 'C', '自动生成的销售区域编码: 越南', true, 0, '2025-04-24 16:29:11.019841', '2025-04-25 00:29:11.019843');
INSERT INTO public.product_code_field_options VALUES (6, 1, '150MHZ', 'J', '', true, 0, '2025-04-24 23:22:49.52391', '2025-04-25 07:22:49.523918');
INSERT INTO public.product_code_field_options VALUES (7, 1, '350MHz', 'R', '', true, 0, '2025-04-24 23:23:02.866403', '2025-04-25 07:23:02.86641');
INSERT INTO public.product_code_field_options VALUES (8, 2, '12.5KHz', 'X', '', true, 0, '2025-04-24 23:23:39.933158', '2025-04-25 07:23:39.933169');
INSERT INTO public.product_code_field_options VALUES (9, 11, '150MHz-170MHz', 'I', '', true, 0, '2025-04-25 05:08:00.668728', '2025-04-25 13:08:00.668735');
INSERT INTO public.product_code_field_options VALUES (10, 11, '350MHz-370MHz', 'A', '从产品 Mark1000 MAX 自动添加的指标', true, 1, '2025-04-25 05:08:42.179287', '2025-04-25 13:08:42.179296');
INSERT INTO public.product_code_field_options VALUES (11, 11, '400-450MHz', 'B', '从产品 Mark1000 MAX 自动添加的指标', true, 2, '2025-04-25 05:11:44.545207', '2025-04-25 13:11:44.545215');
INSERT INTO public.product_code_field_options VALUES (12, 11, '800MHz-890MHz', 'C', '从产品 Mark1000 MAX 自动添加的指标', true, 3, '2025-04-25 09:16:50.615312', '2025-04-25 17:16:50.615323');
INSERT INTO public.product_code_field_options VALUES (13, 12, '25MHz', 'A', '从产品 Mark1000 MAX 自动添加的指标', true, 1, '2025-04-25 09:20:06.256423', '2025-04-25 17:20:06.256431');
INSERT INTO public.product_code_field_options VALUES (14, 13, '25', '1', '从产品 Mark1000 MAX 自动添加的规格值', true, 1, '2025-04-25 10:32:13.677906', '2025-04-25 18:32:13.677909');
INSERT INTO public.product_code_field_options VALUES (15, 14, '150-170MHz', 'A', '从产品 R-EVDC-BLST-U 自动添加的规格值', true, 1, '2025-04-25 13:51:56.17399', '2025-04-25 21:51:56.173992');
INSERT INTO public.product_code_field_options VALUES (16, 3, '12500MHz', 'A', '从产品 Mark3000BS 自动添加的指标', true, 1, '2025-04-25 15:57:08.488471', '2025-04-25 23:57:08.488483');
INSERT INTO public.product_code_field_options VALUES (17, 15, '50欧姆', 'L', '', true, 0, '2025-04-25 23:58:56.032705', '2025-04-26 07:58:56.032712');
INSERT INTO public.product_code_field_options VALUES (18, 16, '220V欧标', 'Q', '', true, 0, '2025-04-25 23:59:12.618438', '2025-04-26 07:59:12.618447');
INSERT INTO public.product_code_field_options VALUES (19, 17, '412-416MHz（下行）/ 402-406MHz（上行）', 'A', '从产品 E-BDA410B-LT 自动添加的规格值', true, 1, '2025-04-26 01:35:27.154118', '2025-04-26 09:35:27.154121');
INSERT INTO public.product_code_field_options VALUES (20, 18, '10W （40±1dBm）', 'A', '从产品 E-BDA410B-LT 自动添加的规格值', true, 1, '2025-04-26 01:35:27.15538', '2025-04-26 11:44:33.223697');
INSERT INTO public.product_code_field_options VALUES (21, 19, '50±2dB', 'A', '从产品 E-BDA410B-LT 自动添加的规格值', true, 1, '2025-04-26 01:35:27.156259', '2025-04-26 09:35:27.15626');
INSERT INTO public.product_code_field_options VALUES (22, 20, '0-30dB', 'A', '从产品 E-BDA410B-LT 自动添加的规格值', true, 1, '2025-04-26 01:35:27.157106', '2025-04-26 09:35:27.157107');
INSERT INTO public.product_code_field_options VALUES (23, 21, '1dB', 'A', '从产品 E-BDA410B-LT 自动添加的规格值', true, 1, '2025-04-26 01:35:27.15799', '2025-04-26 09:35:27.157991');
INSERT INTO public.product_code_field_options VALUES (24, 22, '≤6', 'A', '从产品 E-BDA410B-LT 自动添加的规格值', true, 1, '2025-04-26 01:35:27.158795', '2025-04-26 09:35:27.158796');
INSERT INTO public.product_code_field_options VALUES (25, 23, '≤5 us', 'A', '从产品 E-BDA410B-LT 自动添加的规格值', true, 1, '2025-04-26 01:35:27.15964', '2025-04-26 09:35:27.15964');
INSERT INTO public.product_code_field_options VALUES (26, 24, '≤3dB', 'A', '从产品 E-BDA410B-LT 自动添加的规格值', true, 1, '2025-04-26 01:35:27.161212', '2025-04-26 09:35:27.161214');
INSERT INTO public.product_code_field_options VALUES (27, 25, '≥75dB', 'A', '从产品 E-BDA410B-LT 自动添加的规格值', true, 1, '2025-04-26 01:35:27.163617', '2025-04-26 09:35:27.163618');
INSERT INTO public.product_code_field_options VALUES (28, 26, '≤1.5', 'A', '从产品 E-BDA410B-LT 自动添加的规格值', true, 1, '2025-04-26 01:35:27.164727', '2025-04-26 09:35:27.16473');
INSERT INTO public.product_code_field_options VALUES (29, 27, '室内外 壁挂', '室', '从产品 E-BDA410B-LT 自动添加的规格值', true, 1, '2025-04-26 01:35:27.16615', '2025-04-26 09:35:27.166151');
INSERT INTO public.product_code_field_options VALUES (30, 28, 'IP65', 'I', '从产品 E-BDA410B-LT 自动添加的规格值', true, 1, '2025-04-26 01:35:27.167939', '2025-04-26 09:35:27.16794');
INSERT INTO public.product_code_field_options VALUES (31, 29, '4MHz', 'M', '', true, 0, '2025-04-26 01:40:00.500847', '2025-04-26 09:40:00.500855');
INSERT INTO public.product_code_field_options VALUES (32, 17, '420-424MHz（下行）/ 410-414MHz（上行）', 'N', '', true, 0, '2025-04-26 02:00:38.035383', '2025-04-26 10:00:38.035386');
INSERT INTO public.product_code_field_options VALUES (33, 30, '420-424MHz（下行） / 410-414MHz（上行）', 'A', '从产品 RFT-BDA410 LT/M 自动添加的指标', true, 1, '2025-04-26 03:07:12.683679', '2025-04-26 11:07:12.683687');
INSERT INTO public.product_code_field_options VALUES (34, 41, '50±2dB', 'A', '从产品 RFT-BDA410 LT/M 自动添加的指标', true, 1, '2025-04-26 03:09:29.997055', '2025-04-26 11:09:29.997065');
INSERT INTO public.product_code_field_options VALUES (35, 40, 'IP65', 'I', '从产品 RFT-BDA410 LT/M 自动添加的指标', true, 1, '2025-04-26 03:09:31.260702', '2025-04-26 11:09:31.260709');
INSERT INTO public.product_code_field_options VALUES (36, 39, '壁挂 室外', '壁', '从产品 RFT-BDA410 LT/M 自动添加的指标', true, 1, '2025-04-26 03:09:32.296944', '2025-04-26 11:09:32.296951');
INSERT INTO public.product_code_field_options VALUES (37, 38, '≤1.5', 'A', '从产品 RFT-BDA410 LT/M 自动添加的指标', true, 1, '2025-04-26 03:09:33.508577', '2025-04-26 11:09:33.508586');
INSERT INTO public.product_code_field_options VALUES (38, 37, '≥75dB', 'A', '从产品 RFT-BDA410 LT/M 自动添加的指标', true, 1, '2025-04-26 03:09:34.02539', '2025-04-26 11:09:34.025404');
INSERT INTO public.product_code_field_options VALUES (39, 36, '≤3dB', 'A', '从产品 RFT-BDA410 LT/M 自动添加的指标', true, 1, '2025-04-26 03:09:35.294243', '2025-04-26 11:09:35.294251');
INSERT INTO public.product_code_field_options VALUES (40, 35, '≤5 us', 'A', '从产品 RFT-BDA410 LT/M 自动添加的指标', true, 1, '2025-04-26 03:09:35.909568', '2025-04-26 11:09:35.909572');
INSERT INTO public.product_code_field_options VALUES (41, 33, '1dB', 'A', '从产品 RFT-BDA410 LT/M 自动添加的指标', true, 1, '2025-04-26 03:09:37.584573', '2025-04-26 11:09:37.584581');
INSERT INTO public.product_code_field_options VALUES (42, 34, '≤6', 'A', '从产品 RFT-BDA410 LT/M 自动添加的指标', true, 1, '2025-04-26 03:09:38.613985', '2025-04-26 11:09:38.613993');
INSERT INTO public.product_code_field_options VALUES (43, 32, '0-30dB', 'A', '从产品 RFT-BDA410 LT/M 自动添加的指标', true, 1, '2025-04-26 03:09:39.695985', '2025-04-26 11:09:39.695991');
INSERT INTO public.product_code_field_options VALUES (44, 31, '40±1dBm', 'A', '从产品 RFT-BDA410 LT/M 自动添加的指标', true, 1, '2025-04-26 03:09:40.253768', '2025-04-26 11:09:40.253777');
INSERT INTO public.product_code_field_options VALUES (45, 42, '1', 'A', '从产品 RFT-BDA410 LT/M 自动添加的规格值', true, 1, '2025-04-26 03:10:38.841406', '2025-04-26 11:23:02.910007');
INSERT INTO public.product_code_field_options VALUES (46, 43, '4MHz', 'F', '', true, 0, '2025-04-26 03:13:09.349774', '2025-04-26 11:13:09.349785');


--
-- Data for Name: products; Type: TABLE DATA; Schema: public; Owner: pma_user
--

INSERT INTO public.products VALUES (1, '第三方产品', '基站', 'OBJSVOTXQ01', '智能信道交换机', 'S1024', '端口数量：24个  网线类型：3、4、5类双绞线   防雷等级：4级（6KV） 用途：CP、IP、LCP、系统监控配件/信道机', '华三', '套', 780.00, 'upcoming', '836dc414143b499798302a9170930cbf.jpeg', '2025-04-15 00:23:07.941755', '2025-04-23 12:49:29.47851', 5);
INSERT INTO public.products VALUES (2, '项目产品', '基站', 'BC3I3X4GN', '消防救援对讲通信基站', 'MarkNET3000', '频率范围：350-370MHz  数字/模拟虚拟集群三载波信道 -一体化合路剥离矩阵  NetFlex网络服务', '和源通信', '套', 147000.00, 'discontinued', NULL, '2025-04-15 00:23:07.941759', '2025-04-20 17:37:13.222514', 5);
INSERT INTO public.products VALUES (3, '项目产品', '基站', 'HYBC3XI30', '消防救援对讲通信基站', 'MarkNET3000', '频率范围：351-356/361-366MHz 带宽：≤5M      -基站控制器 -基站交换机 -三载波数模兼容信道 -三载波合路平台    合路输出：10W -功能：网讯平台', '和源通信', '套', 125000.00, 'active', NULL, '2025-04-15 00:23:07.94176', '2025-04-18 23:53:55.989533', 5);
INSERT INTO public.products VALUES (4, '项目产品', '基站', 'BC4I2X4NN', '常规数字基站', 'Mark3000BS', '频率范围：400-430MHz  数字/模拟二载波信道 -一体化合路剥离矩阵  可升级NetFlex网络服务  可升级虚拟集群', '和源通信', '套', 48000.00, 'upcoming', NULL, '2025-04-15 00:23:07.941761', '2025-04-22 00:11:34.764235', 5);
INSERT INTO public.products VALUES (5, '项目产品', '基站', 'BC4I3X4NN', '常规数字基站', 'Mark3000BS', '频率范围：400-430MHz  数字/模拟三载波信道 -一体化合路剥离矩阵  可升级NetFlex网络服务  可升级虚拟集群', '和源通信', '套', 63500.00, 'upcoming', NULL, '2025-04-15 00:23:07.941762', '2025-04-22 00:11:34.004622', 5);
INSERT INTO public.products VALUES (6, '项目产品', '基站', 'BC4I4X4NN', '常规数字基站', 'Mark3000BS', '频率范围：400-430MHz  数字/模拟四载波信道 -一体化合路剥离矩阵  可升级NetFlex网络服务  可升级虚拟集群', '和源通信', '套', 79000.00, 'upcoming', NULL, '2025-04-15 00:23:07.941763', '2025-04-22 00:11:33.275791', 5);
INSERT INTO public.products VALUES (7, '项目产品', '基站', 'BC4I4X4GE', '智能集群基站', 'Mark3000BS PLUS', '频率范围：400-430MHz  数字/模拟虚拟集群二载波信道 -一体化合路剥离矩阵  NetFlex网络服务', '和源通信', '套', 100300.00, 'upcoming', NULL, '2025-04-15 00:23:07.941764', '2025-04-22 00:11:20.851801', 5);
INSERT INTO public.products VALUES (8, '项目产品', '基站', 'BC4I3X4GE', '智能集群基站', 'Mark3000BS PLUS', '频率范围：400-430MHz  数字/模拟虚拟集群三载波信道 -一体化合路剥离矩阵  NetFlex网络服务', '和源通信', '套', 125700.00, 'upcoming', NULL, '2025-04-15 00:23:07.941764', '2025-04-22 00:11:22.043299', 5);
INSERT INTO public.products VALUES (9, '项目产品', '基站', 'BC4I2X4GE', '智能集群基站', 'Mark3000BS PLUS', '频率范围：400-430MHz  数字/模拟虚拟集群四载波信道 -一体化合路剥离矩阵  NetFlex网络服务', '和源通信', '套', 143200.00, 'upcoming', NULL, '2025-04-15 00:23:07.941765', '2025-04-22 00:11:23.379421', 5);
INSERT INTO public.products VALUES (10, '项目产品', '基站', 'HYPSMXI30', '数字智能信道机', 'Mark1000 MAX', '频率范围：350-400MHz-功率 25W-网讯平台-数模兼容', '和源通信', '套', 14583.00, 'active', NULL, '2025-04-15 00:23:07.941766', '2025-04-20 16:39:53.024141', 5);
INSERT INTO public.products VALUES (11, '渠道产品', '基站', 'HYPSMXI40', '数字智能信道机', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W-网讯平台-数模兼容', '和源通信', '套', 13580.00, 'active', NULL, '2025-04-15 00:23:07.941766', '2025-04-20 16:40:22.186171', 5);
INSERT INTO public.products VALUES (12, '渠道产品', '基站', 'WCF9PH', '信道机虚拟集群功能许可', 'LS-VTT-RPT', '授权信道机在注册虚拟集群功能许可', '和源通信', '个', 3000.00, 'upcoming', NULL, '2025-04-15 00:23:07.941767', '2025-04-22 00:11:46.175663', 5);
INSERT INTO public.products VALUES (13, '渠道产品', '基站', 'OBUSWG10', '虚拟集群服务器主机', 'R240/虚拟集群软件', '4背板奔腾双核G5400 3.8GH 8G内存丨1*1T硬盘 微软正版系统win10软件/虚拟集群服务软件', '戴尔', '台', 13600.00, 'upcoming', NULL, '2025-04-15 00:23:07.941768', '2025-04-22 00:11:47.069138', 5);
INSERT INTO public.products VALUES (14, '渠道产品', '基站', 'WCP0PH', '虚拟集群服务', 'GW-VTT-RPT', '服务器虚拟集群信道控制服务软件，服务器配套', '和源通信', '个', NULL, 'discontinued', NULL, '2025-04-15 00:23:07.941769', '2025-04-18 23:53:55.989541', 5);
INSERT INTO public.products VALUES (15, '项目产品', '基站', 'OAMFF5WUGH1', '广播多频点调频处理器', 'E-BDA088-U FM', '频率范围：087-108MHz;最大功率：1mW;机柜式;尺寸：3U;供电供电220VAC;内置功能：16信道广播接入&广播告警切换;监控能力：不支持', '和源通信', '套', 116667.00, 'active', NULL, '2025-04-15 00:23:07.941769', '2025-04-18 23:53:55.989542', 5);
INSERT INTO public.products VALUES (16, '渠道产品', '合路平台', 'HYMFC2A10', '定向耦合合路器', 'E-FH150-2', '频率范围：163-167MHz 单端口承载功率：50W;插入损耗：≤4.0dB接入端口数量：2;安装方式：机柜式;', '和源通信', '套', 7902.00, 'discontinued', NULL, '2025-04-15 00:23:07.94177', '2025-04-18 23:53:55.989542', 5);
INSERT INTO public.products VALUES (17, '渠道产品', '合路平台', 'HYMFC4A10', '定向耦合合路器', 'E-FH150-4', '频率范围：163-167MHz 单端口承载功率：50W;插入损耗：≤7.0dB接入端口数量：4;安装方式：机柜式;', '和源通信', '套', 11111.00, 'discontinued', NULL, '2025-04-15 00:23:07.941771', '2025-04-18 23:53:55.989543', 5);
INSERT INTO public.products VALUES (18, '渠道产品', '合路平台', 'ECM1B042CZ2', '定向耦合合路器', 'E-FH350-4', '频率范围：350-390MHz 单端口承载功率：50W;插入损耗：≤8.5dB接入端口数量：4;安装方式：机柜式;尺寸：2U', '和源通信', '套', 6667.00, 'active', NULL, '2025-04-15 00:23:07.941771', '2025-04-18 23:53:55.989544', 5);
INSERT INTO public.products VALUES (19, '渠道产品', '合路平台', 'ECM1B022CZ1', '定向耦合合路器', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 4569.00, 'active', NULL, '2025-04-15 00:23:07.941772', '2025-04-18 23:53:55.989544', 5);
INSERT INTO public.products VALUES (20, '渠道产品', '合路平台', 'ECM1B042CZ1', '定向耦合合路器', 'E-FH400-4', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤8.5dB 接入端口数量：4 安装方式：机柜式 尺寸2U', '和源通信', '套', 6642.00, 'active', NULL, '2025-04-15 00:23:07.941773', '2025-04-18 23:53:55.989545', 5);
INSERT INTO public.products VALUES (21, '渠道产品', '合路平台', 'ECM1B062CZ1', '定向耦合合路器', 'E-FH400-6', '频率范围：400-430MHz 单端口承载功率：50W;插入损耗：≤11dB;接入端口数量：6;安装方式：机柜式;尺寸：2U', '和源通信', '套', 10760.00, 'active', NULL, '2025-04-15 00:23:07.941773', '2025-04-18 23:53:55.989546', 5);
INSERT INTO public.products VALUES (22, '渠道产品', '合路平台', 'ECM1B082CZ1', '定向耦合合路器', 'E-FH400-8', '频率范围：400-430MHz 单端口承载功率：50W;插入损耗：≤12dB;接入端口数量：8;安装方式：机柜式;尺寸：2U', '和源通信', '套', 14120.00, 'discontinued', NULL, '2025-04-15 00:23:07.941774', '2025-04-18 23:53:55.989546', 5);
INSERT INTO public.products VALUES (23, '渠道产品', '合路平台', 'HYMJC2010', '分路器', 'E-JF150-2', '频率范围：130-170MHz 单端口承载功率：1W 插入损耗：≤3.5dB 接入端口数量：2 安装方式：机柜式 尺寸 1U', '和源通信', '套', 2493.00, 'discontinued', NULL, '2025-04-15 00:23:07.941775', '2025-04-18 23:53:55.989547', 5);
INSERT INTO public.products VALUES (24, '渠道产品', '合路平台', 'HYMJC4010', '分路器', 'E-JF150-4', '频率范围：130-170MHz 单端口承载功率：1W;插入损耗：≤7.0dB接入端口数量：4;安装方式：机柜式;', '和源通信', '套', 2913.00, 'discontinued', NULL, '2025-04-15 00:23:07.941775', '2025-04-18 23:53:55.989548', 5);
INSERT INTO public.products VALUES (25, '渠道产品', '合路平台', 'EDE1BU2xCZ1', '分路器', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 2320.00, 'active', NULL, '2025-04-15 00:23:07.941776', '2025-04-18 23:53:55.989548', 5);
INSERT INTO public.products VALUES (26, '渠道产品', '合路平台', 'EDE1BU4xCZ1', '分路器', 'E-JF350/400-4', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤7.5dB 接入端口数量：4 安装方式：机柜式 尺寸1U', '和源通信', '套', 2493.00, 'active', NULL, '2025-04-15 00:23:07.941777', '2025-04-18 23:53:55.989549', 5);
INSERT INTO public.products VALUES (27, '渠道产品', '合路平台', 'EDE1BU6xCZ1', '分路器', 'E-JF350/400-6', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤9.5dB 接入端口数量：6 安装方式：机柜式 尺寸1U', '和源通信', '套', 3580.00, 'active', NULL, '2025-04-15 00:23:07.941778', '2025-04-18 23:53:55.98955', 5);
INSERT INTO public.products VALUES (173, '第三方产品', '配件', 'W000161', '衰减器', 'E-RFATT50-20DB', '衰减值：20dB    功率：50W    接口： N型', '国产', '个', 190.00, 'active', NULL, '2025-04-15 00:23:07.941875', '2025-04-18 23:53:55.989641', 5);
INSERT INTO public.products VALUES (28, '渠道产品', '合路平台', 'EDE1BU8xCZ1', '分路器', 'E-JF350/400-8', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤10.5dB 接入端口数量：8 安装方式：机柜式 尺寸1U', '和源通信', '套', 4962.00, 'discontinued', NULL, '2025-04-15 00:23:07.941778', '2025-04-18 23:53:55.98955', 5);
INSERT INTO public.products VALUES (29, '渠道产品', '合路平台', 'MCFCMN53N', '多信道分合路器', 'FHJ400-2', '频率范围: 400-430MHz    信道端口数: 2    最大输入功率: 50W    插入损耗: ≤9dB    驻波比: ≤1.5    端口隔离度: ≥35dB    电源: /', '和源通信', '套', 6800.00, 'active', NULL, '2025-04-15 00:23:07.941779', '2025-04-20 17:24:25.604799', 5);
INSERT INTO public.products VALUES (30, '渠道产品', '合路平台', 'MCFFMM53N', '多信道分合路器', 'FHJ400-4', '频率范围: 400-430MHz    信道端口数: 4    最大输入功率: 50W    插入损耗: ≤7.5dB    驻波比: ≤1.5    端口隔离度: ≥35dB', '和源通信', '套', 9100.00, 'active', NULL, '2025-04-15 00:23:07.94178', '2025-04-20 17:24:41.968104', 5);
INSERT INTO public.products VALUES (31, '渠道产品', '合路平台', 'MCFHMO53N', '多信道分合路器', 'FHJ400-6', '频率范围: 400-430MHz    信道端口数: 6    最大输入功率: 50W    插入损耗: ≤11dB    驻波比: ≤1.5    端口隔离度: ≥35dB', '和源通信', '套', 14000.00, 'active', NULL, '2025-04-15 00:23:07.94178', '2025-04-20 17:40:49.484822', 5);
INSERT INTO public.products VALUES (32, '渠道产品', '合路平台', 'EC3FATN31N', '信号剥离矩阵', 'R-EVDC-BLST-4', '频率范围: 350-430MHz    信道端口数: 4 input/ 4 output    最大输入功率: 100W    路由: Two-way    工作电压: /    端口耦合度: ≤29dB    Insert Loss: ≤1dB', '和源通信', '套', 7500.00, 'active', NULL, '2025-04-15 00:23:07.941781', '2025-04-20 17:40:50.239716', 5);
INSERT INTO public.products VALUES (33, '渠道产品', '合路平台', 'EC3SATN31N', '信号剥离矩阵', 'R-EVDC-BLST-6', '频率范围: 350-430MHz    信道端口数: 6 input/ 6 output    最大输入功率: 100W    路由: Two-way    工作电压: /    端口耦合度: ≤29dB    Insert Loss: ≤1dB', '和源通信', '套', 9200.00, 'active', NULL, '2025-04-15 00:23:07.941782', '2025-04-20 17:40:51.271026', 5);
INSERT INTO public.products VALUES (34, '项目产品', '合路平台', 'MCHFLL52C', '一体化分合路矩阵', 'FHJ400-BLST-4', '频率范围: 350-370MHz/350-470MHz    信道端口数: 4    最大输入功率: 250mw/24dB    插入损耗: ≤6dB    驻波比: ≤1.5    端口隔离度: ≥16dB    电源: 220V/ CN', '和源通信', '套', 16000.00, 'upcoming', NULL, '2025-04-15 00:23:07.941782', '2025-04-22 00:12:08.987531', 5);
INSERT INTO public.products VALUES (35, '项目产品', '合路平台', 'MCGFLF52C', '一体化分合路矩阵', 'FHJ400-BLST-4', '频率范围: 410-430MHz/350-470MHz    信道端口数: 4    最大输入功率: 250mw/24dB    插入损耗: /    驻波比: ≤1.5    端口隔离度: ≥16dB    电源: 220V/ CN', '和源通信', '套', 18000.00, 'upcoming', NULL, '2025-04-15 00:23:07.941783', '2025-04-22 00:12:12.483634', 5);
INSERT INTO public.products VALUES (36, '渠道产品', '合路平台', 'HYMBC6A1U', '上行信号剥离器', 'R-EVDC-BLST-U', '频率范围：87-170MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 4938.00, 'discontinued', NULL, '2025-04-15 00:23:07.941784', '2025-04-18 23:53:55.989555', 5);
INSERT INTO public.products VALUES (37, '渠道产品', '合路平台', 'HYMBC6A1D', '下行信号剥离器', 'R-EVDC-BLST-D', '频率范围：87-170MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 4938.00, 'discontinued', NULL, '2025-04-15 00:23:07.941784', '2025-04-18 23:53:55.989556', 5);
INSERT INTO public.products VALUES (38, '渠道产品', '合路平台', 'EDE1AD6xCZ1', '下行信号剥离器', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 4569.00, 'active', NULL, '2025-04-15 00:23:07.941785', '2025-04-18 23:53:55.989557', 5);
INSERT INTO public.products VALUES (39, '渠道产品', '合路平台', 'EDE1AU6xCZ1', '上行信号剥离器', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 4569.00, 'active', NULL, '2025-04-15 00:23:07.941786', '2025-04-18 23:53:55.989557', 5);
INSERT INTO public.products VALUES (40, '渠道产品', '合路平台', 'HYMDF2A10', '双工器', 'E-SGQ150D', '频率范围：157.3-160.6/163.0-166.3MHz;单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：5.7M 隔离方式：带通 工作带宽：2M（可调） 安装方式：机柜式;', '和源通信', '套', 7902.00, 'discontinued', NULL, '2025-04-15 00:23:07.941786', '2025-04-18 23:53:55.989558', 5);
INSERT INTO public.products VALUES (41, '渠道产品', '合路平台', 'EDUPB5H1CZ1', '双工器', 'E-SGQ350D', '频率范围：351-356/361-366MHz 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 隔离方式：带通 工作带宽：5M 安装方式：机柜式 尺寸：2U', '和源通信', '套', 9167.00, 'discontinued', NULL, '2025-04-15 00:23:07.941787', '2025-04-18 23:53:55.989559', 5);
INSERT INTO public.products VALUES (42, '渠道产品', '合路平台', 'EDULN4N1CZ2', '双工器', 'E-SGQ400N', '频率范围：402-406/412-416MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 3753.00, 'active', NULL, '2025-04-15 00:23:07.941788', '2025-04-20 18:29:24.653215', 5);
INSERT INTO public.products VALUES (43, '渠道产品', '合路平台', 'EDULN4N1CZ1', '双工器', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 3753.00, 'active', NULL, '2025-04-15 00:23:07.941788', '2025-04-20 18:29:26.076865', 5);
INSERT INTO public.products VALUES (44, '渠道产品', '合路平台', 'EDULB4H1CZ1', '双工器', 'E-SGQ400D', '频率范围：410-414/420-424MHz 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 隔离方式：带通 工作带宽：4M 安装方式：机柜式 尺寸：2U', '和源通信', '套', 7876.00, 'active', NULL, '2025-04-15 00:23:07.941789', '2025-04-20 18:29:28.239144', 5);
INSERT INTO public.products VALUES (45, '渠道产品', '合路平台', 'EDULB4H1CZ2', '双工器', 'E-SGQ400D', '频率范围：402-406/412-416MHz 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 隔离方式：带通 工作带宽：4M 安装方式：机柜式 尺寸：2U', '和源通信', '套', 7876.00, 'active', NULL, '2025-04-15 00:23:07.94179', '2025-04-20 18:29:29.350004', 5);
INSERT INTO public.products VALUES (46, '渠道产品', '合路平台', 'EDUPGFH1CZ1', '双工器', 'E-SGQ800D', '频率范围：806-821/851-866MHz 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：45M 隔离方式：带通 工作带宽：15M 安装方式：机柜式 尺寸：2U', '和源通信', '套', 9167.00, 'active', NULL, '2025-04-15 00:23:07.94179', '2025-04-20 18:29:30.373479', 5);
INSERT INTO public.products VALUES (47, '渠道产品', '合路平台', 'ECM1BB22CZ2', '系统合路器', 'E-FHP2000-2', '频率范围：351-366/410-424MHz 单端口承载功率：50W 插入损耗：≤1.5dB 接入端口数量：2 安装方式：机柜式 尺寸：2U', '和源通信', '套', 7917.00, 'active', NULL, '2025-04-15 00:23:07.941791', '2025-04-20 18:29:48.139871', 5);
INSERT INTO public.products VALUES (48, '渠道产品', '合路平台', 'ECM1BB22CZ1', '系统合路器', 'E-FHP2000-2', '频率范围：351-366/402-416MHz 单端口承载功率：50W 插入损耗：≤1.5dB 接入端口数量：2 安装方式：机柜式 尺寸：2U', '和源通信', '套', 7917.00, 'active', NULL, '2025-04-15 00:23:07.941791', '2025-04-20 18:29:48.968858', 5);
INSERT INTO public.products VALUES (49, '渠道产品', '合路平台', 'HYMPC2A30', '系统合路器', 'E-FHP2000-2', '频率范围：351-366/372-386MHz 单端口承载功率：50W 插入损耗：≤2.0dB 接入端口数量：2', '和源通信', '套', 6691.00, 'discontinued', NULL, '2025-04-15 00:23:07.941792', '2025-04-20 18:30:15.140701', 5);
INSERT INTO public.products VALUES (50, '渠道产品', '合路平台', 'EHYR321092', '系统合路器', 'E-FHP2000-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤4dB 工作带宽：30M 接入端口数量：2 安装方式：机柜式 尺寸：2U', '和源通信', '套', 5000.00, 'discontinued', NULL, '2025-04-15 00:23:07.941793', '2025-04-20 18:30:00.107801', 5);
INSERT INTO public.products VALUES (51, '渠道产品', '合路平台', 'EHYR321078', '系统合路器', 'E-FHP2000-2', '频率范围：400-424/806-866MHz 单端口承载功率：50W 接入端口数量：2 安装方式：机柜式', '和源通信', '套', 7917.00, 'discontinued', NULL, '2025-04-15 00:23:07.941793', '2025-04-20 18:30:00.79351', 5);
INSERT INTO public.products VALUES (174, '第三方产品', '配件', 'W000072', '衰减器', 'E-RFATT50-10DB', '衰减值：10dB    功率：50W    接口： N型', '国产', '个', 190.00, 'active', NULL, '2025-04-15 00:23:07.941875', '2025-04-18 23:53:55.989642', 5);
INSERT INTO public.products VALUES (52, '渠道产品', '合路平台', 'ECM4BB32CZ1', '系统合路器', 'E-FHP2000-3', '频率范围：351-366/372-386/410-424MHz 单端口承载功率：50W 插入损耗：≤2.0dB 接入端口数量：3 安装方式：机柜式 尺寸：2U', '和源通信', '套', 16667.00, 'discontinued', NULL, '2025-04-15 00:23:07.941794', '2025-04-20 18:30:01.415363', 5);
INSERT INTO public.products VALUES (53, '渠道产品', '合路平台', 'ECM5BB32CZ1', '系统合路器', 'E-FHP2000-3', '频率范围：87-108/351-366/410-424MHz 单端口承载功率：50W 插入损耗：≤2.0dB 接入端口数量：3 安装方式：机柜式 尺寸：2U', '和源通信', '套', 16667.00, 'discontinued', NULL, '2025-04-15 00:23:07.941795', '2025-04-20 18:30:02.152845', 5);
INSERT INTO public.products VALUES (54, '渠道产品', '合路平台', 'ECM5BB32CZ2', '系统合路器', 'E-FHP2000-3', '频率范围：87-108/351-366/402-416MHz 单端口承载功率：50W 插入损耗：≤2.0dB 接入端口数量：3 安装方式：机柜式 尺寸：2U', '和源通信', '套', 16667.00, 'discontinued', NULL, '2025-04-15 00:23:07.941795', '2025-04-18 23:53:55.989567', 5);
INSERT INTO public.products VALUES (55, '渠道产品', '合路平台', 'EHYR321079', '系统合路器', 'E-FHP2000-3', '频率范围：351-365/400-424/806-866MHz 单端口承载功率：50W 接入端口数量：3 安装方式：机柜式', '和源通信', '套', 16667.00, 'discontinued', NULL, '2025-04-15 00:23:07.941796', '2025-04-18 23:53:55.989567', 5);
INSERT INTO public.products VALUES (56, '渠道产品', '合路平台', 'HYMPC3AA0', '系统合路器', 'E-FHP2000-3', '频率范围：87-108MHz/163-166MHz/361-366MHz 单端口承载功率：50W;插入损耗：≤12dB;接入端口数量：3 安装方式：机柜式;尺寸：2U', '和源通信', '套', 8750.00, 'discontinued', NULL, '2025-04-15 00:23:07.941797', '2025-04-18 23:53:55.989568', 5);
INSERT INTO public.products VALUES (57, '项目产品', '合路平台', 'HYMPC2ACP', '系统合路器 | 供电', 'E-FHP2000-2/P', '频率范围：351-366/403-430MHz 单端口承载功率：50W 插入损耗：≤2.0dB 供电模块', '和源通信', '套', 10450.00, 'discontinued', NULL, '2025-04-15 00:23:07.941797', '2025-04-18 23:53:55.989569', 5);
INSERT INTO public.products VALUES (58, '项目产品', '合路平台', 'HYMPC3ABP', '系统合路器 | 供电', 'E-FHP2000-3 /P', '频率范围：87-108MHz/361-366MHz/403-430 单端口承载功率：50W;插入损耗：≤12dB;接入端口数量：3 内置电源模块', '和源通信', '套', 20450.00, 'discontinued', NULL, '2025-04-15 00:23:07.941798', '2025-04-18 23:53:55.989569', 5);
INSERT INTO public.products VALUES (59, '渠道产品', '直放站', 'HYR1SN140', '常规射频直放站', 'E-BDA400B LT', '频率范围：410-414/420-424      链路带宽 4MHz     最大射频输出功率 33dBm(2W)', '和源通信', '套', 8396.00, 'active', NULL, '2025-04-15 00:23:07.941799', '2025-04-18 23:53:55.98957', 5);
INSERT INTO public.products VALUES (60, '渠道产品', '直放站', 'HYR1SN14A', '常规射频直放站', 'E-BDA400B LT', '频率范围：403-405/413-415MHz 带宽：≤4M 输出：2W  功能：正面状态灯', '和源通信', '套', 8396.00, 'active', NULL, '2025-04-15 00:23:07.941799', '2025-04-18 23:53:55.989571', 5);
INSERT INTO public.products VALUES (61, '渠道产品', '直放站', 'EAMLR4FBKR2', '射频中继组件 413MHz', 'E-BDA400-B LT', '频率范围:403-405/413-415MHz 输出功率:33dB 增益:≥50dB 收发频率间隔:10M 工作带宽:2M 安装方式:壁挂式', '和源通信', '套', 10120.00, 'discontinued', NULL, '2025-04-15 00:23:07.9418', '2025-04-20 17:05:59.158437', 5);
INSERT INTO public.products VALUES (62, '渠道产品', '直放站', 'HYR2SI000', '智能光纤近端机', 'RFS-88 LT/M', '频率范围：87-108MHz 远端携带：4 功能：正面状态灯/面板调试', '和源通信', '套', 8958.00, 'discontinued', NULL, '2025-04-15 00:23:07.941801', '2025-04-18 23:53:55.989572', 5);
INSERT INTO public.products VALUES (63, '渠道产品', '直放站', 'HYR2SI010', '智能光纤近端机', 'RFS-100 LT/M', '频率范围：150-170MHz 带宽：≤20M 远端携带：4 功能： 正面状态灯/网讯平台', '和源通信', '套', 8958.00, 'discontinued', NULL, '2025-04-15 00:23:07.941801', '2025-04-18 23:53:55.989573', 5);
INSERT INTO public.products VALUES (64, '渠道产品', '直放站', 'HYR2SI030', '智能光纤近端机', 'RFS-400 LT/M', '频率范围：350-50MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 9876.00, 'active', NULL, '2025-04-15 00:23:07.941802', '2025-04-20 18:30:25.693844', 5);
INSERT INTO public.products VALUES (65, '渠道产品', '直放站', 'HYR2SI080', '智能光纤近端机', 'RFS-800 LT/M', '频率范围：800-890MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 8958.00, 'active', NULL, '2025-04-15 00:23:07.941802', '2025-04-20 18:30:28.904407', 5);
INSERT INTO public.products VALUES (66, '渠道产品', '直放站', 'HYR3SI300', '智能光纤远端直放站', 'RFT-BDA88 LT/M', '频率范围：87-108MHz；带宽：≤21M；输出：10W；2U机柜；功能：正面状态灯/面板调试', '和源通信', '套', 22500.00, 'active', NULL, '2025-04-15 00:23:07.941803', '2025-04-20 18:30:33.600774', 5);
INSERT INTO public.products VALUES (67, '渠道产品', '直放站', 'HYR3SI310', '智能光纤远端直放站', 'RFT-BDA110 LT/M', '频率范围：157-161/163-167MHz 带宽：≤4M 输出：10W 功能： 正面状态灯/网讯平台', '和源通信', '套', 25000.00, 'active', NULL, '2025-04-15 00:23:07.941804', '2025-04-20 18:30:34.376231', 5);
INSERT INTO public.products VALUES (68, '渠道产品', '直放站', 'HYR3S1130', '智能光纤远端直放站', 'RFT-BDA300B LT', '频率范围：351-356/361-366MHz 带宽：≤4M 输出：2W 功能：正面状态灯/网讯平台', '和源通信', '套', 12851.00, 'active', NULL, '2025-04-15 00:23:07.941804', '2025-04-20 18:30:38.184467', 5);
INSERT INTO public.products VALUES (69, '渠道产品', '直放站', 'HYR3SI330', '智能光纤远端直放站', 'RFT-BDA310 LT/M', '频率范围：351-356/361-366MHz 带宽：≤5M 输出：10W 2U机箱 功能： 正面状态灯/网讯平台', '和源通信', '套', 21250.00, 'active', NULL, '2025-04-15 00:23:07.941805', '2025-04-20 18:30:40.395304', 5);
INSERT INTO public.products VALUES (70, '渠道产品', '直放站', 'HYR3SI14A', '智能光纤远端直放站', 'RFT-BDA400B LT/M', '频率范围：403-405/413-415MHz 带宽：≤4M 输出：2W  功能： 网讯平台', '和源通信', '套', 11851.00, 'active', NULL, '2025-04-15 00:23:07.941806', '2025-04-20 18:30:41.635964', 5);
INSERT INTO public.products VALUES (71, '渠道产品', '直放站', 'HYR3SI140', '智能光纤远端直放站', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 1U机箱 功能： 网讯平台', '和源通信', '套', 11851.00, 'active', NULL, '2025-04-15 00:23:07.941806', '2025-04-20 18:30:42.574485', 5);
INSERT INTO public.products VALUES (72, '渠道产品', '直放站', 'HYR3SI340', '智能光纤远端直放站', 'RFT-BDA410 LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：10W 功能： 正面状态灯/网讯平台', '和源通信', '套', 21250.00, 'active', NULL, '2025-04-15 00:23:07.941808', '2025-04-20 18:30:45.542868', 5);
INSERT INTO public.products VALUES (73, '渠道产品', '直放站', 'HYR3SI380', '智能光纤远端直放站', 'RFT-BDA810 LT/M', '频率范围：806-821/851-866MHz 带宽：≤15M 输出：10W 2U机箱 功能： 正面状态灯/网讯平台', '和源通信', '套', 21250.00, 'active', NULL, '2025-04-15 00:23:07.941809', '2025-04-20 18:30:46.626291', 5);
INSERT INTO public.products VALUES (74, '项目产品', '直放站', 'HYR2DI000', '数字智能光纤近端机', 'DRFS-88/M', '频率范围：87-108MHz 远端携带：32 数字型 功能：触摸屏/网讯平台', '和源通信', '套', 25000.00, 'active', NULL, '2025-04-15 00:23:07.94181', '2025-04-20 18:30:48.519356', 5);
INSERT INTO public.products VALUES (75, '项目产品', '直放站', 'HYR2DI010', '数字智能光纤近端机', 'DRFS-100/M', '频率范围：150-170MHz 带宽：≤20M 远端携带：32 数字型 功能：触摸屏/网讯平台', '和源通信', '套', 25000.00, 'active', NULL, '2025-04-15 00:23:07.94181', '2025-04-20 18:30:49.263984', 5);
INSERT INTO public.products VALUES (76, '项目产品', '直放站', 'HYR2DI030', '数字智能光纤近端机', 'DRFS-300/M', '频率范围：350MHz 远端携带：32 数字型 功能：触摸屏/网讯平台', '和源通信', '套', 25000.00, 'active', NULL, '2025-04-15 00:23:07.941811', '2025-04-20 18:30:50.656539', 5);
INSERT INTO public.products VALUES (77, '项目产品', '直放站', 'OC4DC4IN', '数字智能光纤近端机', 'DRFS-400B/M', '频率范围: 400-470MHz    工作模式: Digital    安装方式: Cabinet 2U    IP防护: IP40    光纤端口类型: LC-LC   功能: NetFlex', '和源通信', '套', 21000.00, 'active', NULL, '2025-04-15 00:23:07.941812', '2025-04-18 23:53:55.989581', 5);
INSERT INTO public.products VALUES (78, '项目产品', '直放站', 'HYR2DI040', '数字智能光纤近端机', 'DRFS-400/M', '频率范围：410-414/420-424MHz 远端携带：32 数字型 功能：触摸屏/网讯平台', '和源通信', '套', 25000.00, 'active', NULL, '2025-04-15 00:23:07.941812', '2025-04-20 18:30:54.87096', 5);
INSERT INTO public.products VALUES (79, '项目产品', '直放站', 'HYR2DI080', '数字智能光纤近端机', 'DRFS-800/M', '频率范围：800-890MHz 远端携带：32 数字型 功能：触摸屏/网讯平台', '和源通信', '套', 25000.00, 'active', NULL, '2025-04-15 00:23:07.941813', '2025-04-20 18:30:56.188898', 5);
INSERT INTO public.products VALUES (136, '项目产品', '应用', 'HYBIOCBNY', '蓝牙定位信标+许可证', 'BTN10', '标准iBeacon协议    电池续航3年    专用对讲机广播报文    许可证：蓝牙定位入网许可', '和源通信', '套', 110.00, 'active', NULL, '2025-04-15 00:23:07.94185', '2025-04-20 18:33:07.934665', 5);
INSERT INTO public.products VALUES (80, '项目产品', '直放站', 'HYR3DI300', '数字智能光纤远端直放站', 'DRFT-BDA88/M', '频率范围：87-108MHz；带宽：≤21M；输出：10W；数字型 功能：触摸屏/网讯平台 扩展：馈电', '和源通信', '套', 45833.00, 'active', NULL, '2025-04-15 00:23:07.941814', '2025-04-20 18:30:57.579705', 5);
INSERT INTO public.products VALUES (81, '项目产品', '直放站', 'HYR3DI310', '数字智能光纤远端直放站', 'DRFT-BDA110/M', '频率范围：157-161/163-167MHz 带宽：≤4M；输出：10W；数字型 功能：触摸屏/网讯平台 扩展：馈电', '和源通信', '套', 51250.00, 'active', NULL, '2025-04-15 00:23:07.941814', '2025-04-20 18:30:58.697747', 5);
INSERT INTO public.products VALUES (82, '项目产品', '直放站', 'HYR3DI330', '数字智能光纤远端直放站', 'DRFT-BDA310/M', '频率范围：351-356/361-366MHz；带宽：≤21M；输出：10W；数字型 功能：触摸屏/网讯平台 扩展：馈电', '和源通信', '套', 47917.00, 'active', NULL, '2025-04-15 00:23:07.941815', '2025-04-20 18:30:59.904486', 5);
INSERT INTO public.products VALUES (83, '项目产品', '直放站', 'RC4D2C4IN', '数字智能光纤远端直放站', 'DRFT-BDA400B/M', '频率范围: 400-470MHz    工作模式: Digital   最大输出功率: 2W   安装方式: Cabinet 2U    IP防护: IP40   光纤端口类型: LC-LC   功能: NetFlex', '和源通信', '套', 27200.00, 'discontinued', NULL, '2025-04-15 00:23:07.941816', '2025-04-18 23:53:55.989585', 5);
INSERT INTO public.products VALUES (84, '项目产品', '直放站', 'HYR3DI340', '数字智能光纤远端直放站', 'DRFT-BDA410/M', '频率范围：410-414/420-424MHz 数字带宽：≤4M 输出：10W 数字型 功能：触摸屏/网讯平台 扩展：馈电', '和源通信', '套', 47917.00, 'active', NULL, '2025-04-15 00:23:07.941816', '2025-04-20 18:31:08.838398', 5);
INSERT INTO public.products VALUES (85, '项目产品', '直放站', 'HYR3DI380', '数字智能光纤远端直放站', 'DRFT-BDA810/M', '频率范围：806-821/851-866MHz 带宽：≤15M ；输出：10W；数字型 功能：触摸屏/网讯平台 扩展：馈电', '和源通信', '套', 45833.00, 'active', NULL, '2025-04-15 00:23:07.941817', '2025-04-20 18:31:09.634366', 5);
INSERT INTO public.products VALUES (86, '项目产品', '直放站', 'HYR3DI34J', '数字智能光纤交织型远端直放站', 'DRFT-BDA410/MITW', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：10W 数字交织型 功能：触摸屏/网讯平台 扩展：馈电', '和源通信', '套', 66667.00, 'active', NULL, '2025-04-15 00:23:07.941817', '2025-04-20 18:31:12.718713', 5);
INSERT INTO public.products VALUES (87, '渠道产品', '直放站', 'HYGF20000', '馈电模组', 'FDPower400', '馈电功能模组    需搭配可扩展远端机;内置远端内向天馈提供电力;', '和源通信', '套', 1583.00, 'active', NULL, '2025-04-15 00:23:07.941818', '2025-04-20 18:31:15.684608', 5);
INSERT INTO public.products VALUES (88, '渠道产品', '功率/耦合器', 'HYCCN31Y', '定向耦合器', 'EVDC-6 LT', '频率范围：150-170MHz    承载功率：100W;耦合规格：6dB', '和源通信', '套', 184.00, 'discontinued', NULL, '2025-04-15 00:23:07.941819', '2025-04-20 18:31:25.358934', 5);
INSERT INTO public.products VALUES (89, '渠道产品', '功率/耦合器', 'HYCCN41Y', '定向耦合器', 'EVDC-10 LT', '频率范围：150-170MHz    承载功率：100W;耦合规格：10dB', '和源通信', '套', 184.00, 'discontinued', NULL, '2025-04-15 00:23:07.941819', '2025-04-20 18:31:26.149825', 5);
INSERT INTO public.products VALUES (90, '渠道产品', '功率/耦合器', 'HYCDN24Y', '功率分配器', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 142.00, 'active', NULL, '2025-04-15 00:23:07.94182', '2025-04-20 18:31:21.803854', 5);
INSERT INTO public.products VALUES (91, '渠道产品', '功率/耦合器', 'HYCCN51Y', '定向耦合器', 'EVDC-15 LT', '频率范围：150-170MHz    ;承载功率：100W;耦合规格：15dB', '和源通信', '套', 184.00, 'active', NULL, '2025-04-15 00:23:07.941821', '2025-04-20 18:31:28.374313', 5);
INSERT INTO public.products VALUES (92, '渠道产品', '功率/耦合器', 'HYCCN61Y', '定向耦合器', 'EVDC-20 LT', '频率范围：150-170MHz    承载功率：100W;耦合规格：20dB', '和源通信', '套', 184.00, 'active', NULL, '2025-04-15 00:23:07.941821', '2025-04-20 18:31:29.301758', 5);
INSERT INTO public.products VALUES (93, '渠道产品', '功率/耦合器', 'HYCCN34Y', '定向耦合器', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 142.00, 'active', NULL, '2025-04-15 00:23:07.941822', '2025-04-20 18:31:30.529903', 5);
INSERT INTO public.products VALUES (94, '渠道产品', '功率/耦合器', 'HYCCN44Y', '定向耦合器', 'EVDC-10 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：10dB;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 142.00, 'active', NULL, '2025-04-15 00:23:07.941823', '2025-04-20 18:31:33.765315', 5);
INSERT INTO public.products VALUES (95, '渠道产品', '功率/耦合器', 'HYCCN54Y', '定向耦合器', 'EVDC-15 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：15dB;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 142.00, 'active', NULL, '2025-04-15 00:23:07.941823', '2025-04-20 18:31:34.521176', 5);
INSERT INTO public.products VALUES (96, '渠道产品', '功率/耦合器', 'HYCCN64Y', '定向耦合器', 'EVDC-20 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：20dB;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 142.00, 'active', NULL, '2025-04-15 00:23:07.941824', '2025-04-20 18:31:35.185558', 5);
INSERT INTO public.products VALUES (97, '渠道产品', '功率/耦合器', 'HYCCN74Y', '定向耦合器', 'EVDC-30 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：30dB;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 142.00, 'active', NULL, '2025-04-15 00:23:07.941825', '2025-04-20 18:31:36.070956', 5);
INSERT INTO public.products VALUES (98, '渠道产品', '功率/耦合器', 'HYCDF24Y', '馈电功率分配器', 'MAPD-2', '频率范围：88-866MHz 承载功率：100W 分路端口数量：2 防护等级：IP65 应用：馈电', '和源通信', '套', 208.00, 'active', NULL, '2025-04-15 00:23:07.941825', '2025-04-20 18:31:40.333617', 5);
INSERT INTO public.products VALUES (99, '渠道产品', '功率/耦合器', 'HYCCF34Y', '馈电定向耦合器', 'MADC-6', '频率范围：351-470MHz 承载功率：100W 耦合规格：6dB 分路端口数量：2 防护等级：IP65 应用：馈电', '和源通信', '套', 246.00, 'active', NULL, '2025-04-15 00:23:07.941826', '2025-04-20 18:31:41.593819', 5);
INSERT INTO public.products VALUES (100, '渠道产品', '功率/耦合器', 'HYCCF44Y', '馈电定向耦合器', 'MADC-10', '频率范围：351-470MHz 承载功率：100W 耦合规格：10dB 分路端口数量：2 防护等级：IP65 应用：馈电', '和源通信', '套', 246.00, 'active', NULL, '2025-04-15 00:23:07.941827', '2025-04-20 18:31:42.550213', 5);
INSERT INTO public.products VALUES (101, '渠道产品', '功率/耦合器', 'HYCCF54Y', '馈电定向耦合器', 'MADC-15', '频率范围：351-470MHz 承载功率：100W 耦合规格：15dB 分路端口数量：2 防护等级：IP65 应用：馈电', '和源通信', '套', 246.00, 'active', NULL, '2025-04-15 00:23:07.941827', '2025-04-20 18:31:53.292506', 5);
INSERT INTO public.products VALUES (102, '渠道产品', '功率/耦合器', 'HYCCF64Y', '馈电定向耦合器', 'MADC-20', '频率范围：351-470MHz 承载功率：100W 耦合规格：20dB 分路端口数量：2 防护等级：IP65 应用：馈电', '和源通信', '套', 246.00, 'active', NULL, '2025-04-15 00:23:07.941828', '2025-04-20 18:31:54.027154', 5);
INSERT INTO public.products VALUES (103, '渠道产品', '天线', 'HYAIOCN1N', '室内全向吸顶天线', 'E-ANTO LT', '频率范围：88-430MHz 承载功率：50W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 209.00, 'active', NULL, '2025-04-15 00:23:07.941829', '2025-04-20 18:31:56.197511', 5);
INSERT INTO public.products VALUES (104, '渠道产品', '天线', 'HYAIOCN4Y', '超薄室内全向吸顶天线', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '套', 142.00, 'active', NULL, '2025-04-15 00:23:07.941829', '2025-04-20 18:31:57.046745', 5);
INSERT INTO public.products VALUES (105, '渠道产品', '天线', 'HYAIOCL4Y', '智能室内全向吸顶天线', 'MA11', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65 应用：指示灯', '和源通信', '套', 208.00, 'active', NULL, '2025-04-15 00:23:07.94183', '2025-04-20 18:31:58.024018', 5);
INSERT INTO public.products VALUES (106, '项目产品', '天线', 'HYAIOCB4Y', '智能室内蓝牙全向吸顶天线', 'MA12', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65 应用：指示灯 蓝牙信标', '和源通信', '套', 270.00, 'active', NULL, '2025-04-15 00:23:07.941831', '2025-04-20 18:31:58.954873', 5);
INSERT INTO public.products VALUES (107, '渠道产品', '天线', 'EAN2OFD2TE2', '室外定向板状天线', 'E-ANTD 400', '频率范围：400-430MHz 增益：2.5dBi 防护等级：IP65 辐射方向：定向 最大承载功率：50W 接头类型：N-Femade 特性：室外', '和源通信', '套', 354.00, 'active', NULL, '2025-04-15 00:23:07.941831', '2025-04-20 18:32:01.705217', 5);
INSERT INTO public.products VALUES (137, '渠道产品', '应用', 'EHYW521066', 'MOTOROLA 信道服务软件', 'GW-MOT-RPT', 'MOTOROLA信道机协议通信服务软件 功能 CP LCP 常规模式互通', '和源通信', '套', 36667.00, 'active', NULL, '2025-04-15 00:23:07.941851', '2025-04-20 18:33:08.953826', 5);
INSERT INTO public.products VALUES (108, '渠道产品', '天线', 'EANFOMO5HR1', '室外全向玻璃钢天线', 'E-ANTG-150', '频率范围：150-170MHz    增益：5dBi    防护等级：IP65    辐射方向：全向    最大承载功率：50W    接头类型：N-Femade    特性：室外', '和源通信', '套', 1333.00, 'active', NULL, '2025-04-15 00:23:07.941832', '2025-04-20 18:32:02.79434', 5);
INSERT INTO public.products VALUES (109, '渠道产品', '天线', 'EANPOMO5HR1', '室外全向玻璃钢天线', 'E-ANTG 350', '频率范围：350-380MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade 特性：室外', '和源通信', '套', 625.00, 'active', NULL, '2025-04-15 00:23:07.941833', '2025-04-20 18:32:03.644702', 5);
INSERT INTO public.products VALUES (110, '渠道产品', '天线', 'EANLOMO5HR1', '室外全向玻璃钢天线', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 458.00, 'active', NULL, '2025-04-15 00:23:07.941833', '2025-04-20 18:32:04.361524', 5);
INSERT INTO public.products VALUES (111, '渠道产品', '天线', 'OANFOYD7MJ1', '室外八木定向天线', 'E-ANTY 100', '频率范围：087-108MHz 增益：6dBi 防护等级：IP65 辐射方向：定向 最大承载功率：50W 接头类型：N-Femade 特性：室外', '和源通信', '套', 750.00, 'active', NULL, '2025-04-15 00:23:07.941834', '2025-04-20 18:32:06.397338', 5);
INSERT INTO public.products VALUES (112, '项目产品', '天线', 'EAN2ICO2FZ1', '综合防爆型室内全向吸顶天', 'E-ANTO EX', '频率范围：351-470MHz 承载功率：100W 增益3dBi/IP65/IICA21防爆', '和源通信', '套', 6667.00, 'discontinued', NULL, '2025-04-15 00:23:07.941834', '2025-04-20 17:04:56.016009', 5);
INSERT INTO public.products VALUES (113, '项目产品', '天线', 'ACC3OOCXS', '防爆型高防护全向天线', 'MAEX 10', '频率范围: 350-470 MHz  增益: 0 dB   工作环境: 室内/室外   极化方向: 全向极化   功能: 防爆    IP防护: IP 65', '和源通信', '套', 7200.00, 'active', NULL, '2025-04-15 00:23:07.941835', '2025-04-20 18:32:11.307711', 5);
INSERT INTO public.products VALUES (114, '渠道产品', '对讲机', 'HYTD1MA', 'DMR常规对讲机', 'PNR2000', '频率范围：150-170MHz    锂电池 3700mAh', '和源通信', '套', 1333.00, 'active', NULL, '2025-04-15 00:23:07.941836', '2025-04-20 18:32:20.564008', 5);
INSERT INTO public.products VALUES (115, '渠道产品', '对讲机', 'HYTD4MA', 'DMR常规对讲机', 'PNR2000', '频率范围：400-470MHz    锂电池 3700mAh', '和源通信', '套', 1333.00, 'active', NULL, '2025-04-15 00:23:07.941836', '2025-04-20 16:27:14.881755', 5);
INSERT INTO public.products VALUES (116, '项目产品', '对讲机', 'HYTX0NA', 'DMR智能对讲机', 'PNR2100', '频率范围：400-470MHz/ 4G     功率：1-2W    3800mAH锂电池    蓝牙 5.0 定位    电池管理', '和源通信', '套', 2750.00, 'upcoming', NULL, '2025-04-15 00:23:07.941837', '2025-04-22 00:12:58.760151', 5);
INSERT INTO public.products VALUES (117, '渠道产品', '对讲机', 'HYTCANR01', '常规锂电池板', 'HYTCANR01', '3800mA 3.7V 锂电子 电池组 支持 PNR2000系列', '和源通信', '套', 160.00, 'active', NULL, '2025-04-15 00:23:07.941838', '2025-04-20 16:28:02.241005', 5);
INSERT INTO public.products VALUES (118, '渠道产品', '对讲机', 'HYTCAZR02', '智能锂电池板', 'HYTCAZR02', '3800mA 3.7V 锂电池组 内置充放电效能管理芯片 支持PNR2000系列', '和源通信', '套', 200.00, 'upcoming', NULL, '2025-04-15 00:23:07.941838', '2025-04-22 00:13:14.261733', 5);
INSERT INTO public.products VALUES (119, '渠道产品', '对讲机', 'ZCTZ6NN', '智能多联充电器', 'CMP2600', '功能: 智能   充电座数量: 6  NetFlex网络服务：电池健康度管理', '和源通信', '套', 1860.00, 'active', NULL, '2025-04-15 00:23:07.941839', '2025-04-20 18:32:30.38407', 5);
INSERT INTO public.products VALUES (120, '渠道产品', '对讲机', 'ZCTS6NN', '智能多联充电栈', 'CRSTC1000', '功能: 智能多联充电器+托架结构  类型: 栈    充电座数量: 6    功能: 智能   充电座数量: 6  NetFlex网络服务：电池健康度管理', '和源通信', '套', 2460.00, 'active', NULL, '2025-04-15 00:23:07.94184', '2025-04-20 18:32:43.409839', 5);
INSERT INTO public.products VALUES (121, '渠道产品', '对讲机', 'ZCTCN4T', '多联充电柜', 'CRCAB2000', '功能: 智能    类型: 柜    充电栈数量: 3     Dimensions: 27U  功能: 智能   充电座数量: 6  NetFlex网络服务：电池健康度管理', '和源通信', '套', 9800.00, 'active', NULL, '2025-04-15 00:23:07.94184', '2025-04-20 18:32:45.752896', 5);
INSERT INTO public.products VALUES (122, '渠道产品', '对讲机', 'HYZNC5000', '多联充电柜', 'EVT-CRCAB2000', '五套六联充电栈    支持同时30路对讲机的充电储存    42U    独立供电    电源保护    适用PNR系列对讲机', '和源通信', '套', 11500.00, 'active', NULL, '2025-04-15 00:23:07.941841', '2025-04-18 23:53:55.989609', 5);
INSERT INTO public.products VALUES (123, '第三方产品', '应用', 'OBUSWG00', '网关服务器主机', 'R240', '4背板奔腾双核G5400 3.8GH 8G内存丨1*1T硬盘 微软正版系统win10软件', '戴尔', '台', 13600.00, 'active', NULL, '2025-04-15 00:23:07.941842', '2025-04-20 18:32:49.358151', 5);
INSERT INTO public.products VALUES (124, '渠道产品', '应用', 'HYWG0NB1', '网讯网关服务 软件', 'NFX_GATW', '用于本地系统设备管理和服务器的同步 -本地系统建立和配置 -设备驱动管理 -设备参数设置 -云同步 -设备报警管理', '和源通信', '套', 12500.00, 'active', NULL, '2025-04-15 00:23:07.941842', '2025-04-20 18:32:51.47406', 5);
INSERT INTO public.products VALUES (125, '第三方产品', '应用', 'OBUSWP00', '平台服务器主机', 'R340', 'R340 4背板E-2134 3.5G 4核8线程 16G内存丨3*1T硬盘 微软正版系统win10软件', '戴尔', '台', 23300.00, 'active', NULL, '2025-04-15 00:23:07.941843', '2025-04-20 18:32:54.245908', 5);
INSERT INTO public.products VALUES (126, '渠道产品', '应用', 'HYWP0NC1', '网讯平台服务 软件', 'NFX_MAST_OPETN', '-账户创建和访问管理-设备数据和系统数据的存储和恢复-产品库数据-系统拓扑和设备位置显示和管理-系统资源统计和告警分析推送-系统工作台主次账号一个-20个远端站授权    4个信道机授权    100个终端授权', '和源通信', '套', 105000.00, 'active', NULL, '2025-04-15 00:23:07.941844', '2025-04-20 18:32:56.242962', 5);
INSERT INTO public.products VALUES (127, '渠道产品', '应用', 'HYWF0NA1', '系统工作台', 'ACC-CWT', '提供某一个项目上所有系统的工作管理    直观全面的反映系统的整体面貌和其中设备的布局    并可以跟踪每个设备及服务的进程。-告警处置模块-告警详情模块-维修情况和完成情况-设备位置地图模块    含一年的在线后台服', '和源通信', '个/年', 8333.00, 'active', NULL, '2025-04-15 00:23:07.941844', '2025-04-20 18:32:58.019975', 5);
INSERT INTO public.products VALUES (128, '项目产品', '应用', 'HYWACHA1', '网讯平台在线巡检功能', 'NFX-PAT-OPETN', '支持携带对讲机完成在线的路线巡检记录及任务编排', '和源通信', '套', 22000.00, 'active', NULL, '2025-04-15 00:23:07.941845', '2025-04-20 18:32:58.759172', 5);
INSERT INTO public.products VALUES (129, '项目产品', '应用', 'HYWADHA1', '网讯平台人员分布功能', 'NFX-LCN-OPETN', '支持对讲机在地图上人员的动态分布和查询功能', '和源通信', '套', 14600.00, 'active', NULL, '2025-04-15 00:23:07.941846', '2025-04-20 18:32:59.826766', 5);
INSERT INTO public.products VALUES (130, '项目产品', '应用', 'HYWAEHA1', '网讯平台终端录音功能', 'NFX-RCD-OPETN', '支持对讲机在线通话的实时录音    回访和ID检索功能', '和源通信', '套', 8400.00, 'active', NULL, '2025-04-15 00:23:07.941846', '2025-04-20 18:33:01.390951', 5);
INSERT INTO public.products VALUES (131, '渠道产品', '应用', 'HYWT0NA1', '运维工具包', 'ACC-NUT', '提供多单位的系统运维流程跟踪-告警管理和推送-故障设备快速定位-维护更新工作单', '和源通信', '个/年', 4167.00, 'active', NULL, '2025-04-15 00:23:07.941847', '2025-04-20 18:33:02.371983', 5);
INSERT INTO public.products VALUES (132, '项目产品', '应用', 'HYWR0NA1', '消防救援通信系统资源管理', 'ACC-NRR', '消防管理机构对日常所辖区域内救援通信资源-在线单位数量    系统信息-通信健康度情况 含一年后台服务', '和源通信', '个', 50000.00, 'active', NULL, '2025-04-15 00:23:07.941848', '2025-04-20 18:33:03.74643', 5);
INSERT INTO public.products VALUES (133, '渠道产品', '应用', 'HYWSPNB1', '信道机接入许可', 'LS-NFX-RPT', '网讯平台信道机接入管理服务许可 -信道资源管理 -呼叫类型繁忙度分析', '和源通信', '套', 2500.00, 'active', NULL, '2025-04-15 00:23:07.941848', '2025-04-20 18:33:04.566099', 5);
INSERT INTO public.products VALUES (134, '渠道产品', '应用', 'HYWSRNB1', '远端站接入许可', 'LS-NFX-BDA', '网讯云端终端直放站接入管理服务许可-远端站告警-远端区域状态更新', '和源通信', '套', 1500.00, 'active', NULL, '2025-04-15 00:23:07.941849', '2025-04-20 18:33:06.975155', 5);
INSERT INTO public.products VALUES (135, '渠道产品', '应用', 'HYWSTNB1', '对讲机终端接入许可', 'LS-NFX-RAD', '网讯平台终端对讲机接入管理服务许可-对讲机ID呼叫管理-对讲机上下线管理-呼叫组繁忙度分析', '和源通信', '套', 180.00, 'active', NULL, '2025-04-15 00:23:07.94185', '2025-04-20 16:38:01.196787', 5);
INSERT INTO public.products VALUES (172, '第三方产品', '配件', 'W000162', '衰减器', 'E-RFATT50-30DB', '衰减值：30dB    功率：50W    接口： N型', '国产', '个', 190.00, 'active', NULL, '2025-04-15 00:23:07.941874', '2025-04-18 23:53:55.989641', 5);
INSERT INTO public.products VALUES (138, '第三方产品', '配件', 'EDFWYFC24W', '光纤配线架', 'ST/FC  24口', '尺寸类型：标准尺寸FC口    端口数：24口    产品类型：机架式    特性：含法兰头    不含配套尾纤', '国产', '套', 430.00, 'active', NULL, '2025-04-15 00:23:07.941852', '2025-04-20 18:33:10.255504', 5);
INSERT INTO public.products VALUES (139, '第三方产品', '配件', 'EDFWYFC48W', '光纤配线架', 'ST/FC 48口', '尺寸类型：标准尺寸FC口    端口数：48口    产品类型：机架式    特性：含法兰头    不含配套尾纤', '国产', '套', 860.00, 'active', NULL, '2025-04-15 00:23:07.941852', '2025-04-18 23:53:55.989619', 5);
INSERT INTO public.products VALUES (140, '第三方产品', '配件', 'EDFWYFC04O', '光纤配线架', 'ST/FC  4口', '尺寸类型：标准尺寸FC口    端口数：4口    产品类型：墙上型    特性：含法兰头    不含配套尾纤', '国产', '套', 163.00, 'active', NULL, '2025-04-15 00:23:07.941853', '2025-04-20 18:33:13.944238', 5);
INSERT INTO public.products VALUES (141, '第三方产品', '配件', 'EDFWYFC08O', '光纤配线架', 'ST/FC  8口', '尺寸类型：标准尺寸FC口    端口数：8口    产品类型：墙上型    特性：含法兰头    不含配套尾纤', '国产', '套', 250.00, 'active', NULL, '2025-04-15 00:23:07.941854', '2025-04-20 18:33:15.895659', 5);
INSERT INTO public.products VALUES (142, '第三方产品', '配件', 'W0000144', '单模光纤跳线单芯', '单模单芯FC-LC 5米', '光纤类型：单模    光缆类型：单芯    接口类型：FC/PC-LC/PC    长度：5米', '国产', '根', 33.00, 'active', NULL, '2025-04-15 00:23:07.941854', '2025-04-20 18:33:17.239826', 5);
INSERT INTO public.products VALUES (143, '第三方产品', '配件', 'EJUWY05A4001', '单模光纤跳线单芯', '单模单芯 FC-FC  5米', '光纤类型：单模    光缆类型：单芯    接口类型：FC/PC-FC/PC    长度：5米', '国产', '根', 30.00, 'active', NULL, '2025-04-15 00:23:07.941855', '2025-04-20 18:33:18.100749', 5);
INSERT INTO public.products VALUES (144, '第三方产品', '配件', 'W000612', '单模光纤跳线单芯', 'FC/APC-FC/APC 5M', '光纤类型：单模    光缆类型：单芯    接口类型：FC/APC-FC/APC    长度：5米', '国产', '根', 27.00, 'active', NULL, '2025-04-15 00:23:07.941856', '2025-04-18 23:53:55.989622', 5);
INSERT INTO public.products VALUES (145, '第三方产品', '配件', 'W000154', '单模光纤跳线单芯', '单模单芯FC-LC 10米', '光纤类型：单模    光缆类型：单芯    接口类型：FC/PC-LC/PC    长度：10米', '国产', '根', 58.00, 'active', NULL, '2025-04-15 00:23:07.941856', '2025-04-18 23:53:55.989623', 5);
INSERT INTO public.products VALUES (146, '第三方产品', '配件', 'EJUWY10A4001', '单模光纤跳线单芯', '单模单芯 FC-FC 10米', '光纤类型：单模    光缆类型：单芯    接口类型：FC/PC-FC/PC    长度：10米', '国产', '米', 35.00, 'active', NULL, '2025-04-15 00:23:07.941857', '2025-04-18 23:53:55.989624', 5);
INSERT INTO public.products VALUES (147, '第三方产品', '配件', 'ECAWYGYXTH0401', '轻低烟无卤阻燃铠光缆', 'GYXTH-4B1 4芯', '芯数：4芯    钢带：铠装    特性：单模    低烟无卤阻燃', '国产', '米', 9.00, 'discontinued', NULL, '2025-04-15 00:23:07.941858', '2025-04-18 23:53:55.989624', 5);
INSERT INTO public.products VALUES (148, '第三方产品', '配件', '80093324', '普通中心束管式光缆', 'GYXTW-24B1', '芯数：24芯    钢带：铠装    特性：单模', '国产', '米', 15.00, 'active', NULL, '2025-04-15 00:23:07.941858', '2025-04-18 23:53:55.989625', 5);
INSERT INTO public.products VALUES (149, '第三方产品', '配件', 'ECAWYGYXTH1601', '轻低烟无卤阻燃铠光缆', 'GYXTH-16B1 16芯', '芯数：16芯    钢带：铠装    特性：单模    低烟无卤阻燃', '国产', '米', 17.00, 'active', NULL, '2025-04-15 00:23:07.941859', '2025-04-18 23:53:55.989625', 5);
INSERT INTO public.products VALUES (150, '第三方产品', '配件', 'W000611', '轻低烟无卤阻燃铠光缆', 'GYXTH-8B1.3', '芯数：8芯;钢带：铠装;特性：单模;低烟无卤阻燃', '国产', '米', 8.00, 'active', NULL, '2025-04-15 00:23:07.94186', '2025-04-18 23:53:55.989626', 5);
INSERT INTO public.products VALUES (151, '第三方产品', '配件', 'OBJANOTGR01', '标准L型贴墙室外天线支架', 'MONT80', '曲臂长度50cm 材料：不锈钢 结构类型：L型结构', '国产', '套', 150.00, 'active', NULL, '2025-04-15 00:23:07.94186', '2025-04-20 18:33:24.176524', 5);
INSERT INTO public.products VALUES (152, '第三方产品', '配件', 'OBJANOTHS01', '同轴避雷器', 'CA-23RS', '频率范围：0-1000MHz 功率：700W 阻抗：50Ω 接口（可选）：N', '钻石', '套', 133.00, 'active', NULL, '2025-04-15 00:23:07.941861', '2025-04-20 18:33:26.227182', 5);
INSERT INTO public.products VALUES (153, '第三方产品', '配件', 'OZCH221035', '波纹管同轴电缆', 'HCAAYZ -50-12', '尺寸：1/2＂    特性1：低烟无卤    特性2：阻燃    阻抗：50Ω', '浙江联创', '米', 13.00, 'active', NULL, '2025-04-15 00:23:07.941862', '2025-04-20 18:33:28.062541', 5);
INSERT INTO public.products VALUES (154, '第三方产品', '配件', 'OZCH221036', '波纹管同轴电缆', 'HCTAYZ -50-22', '尺寸：7/8＂    特性1：低烟无卤    特性2：阻燃    阻抗：50Ω', '浙江联创', '米', 35.00, 'active', NULL, '2025-04-15 00:23:07.941862', '2025-04-18 23:53:55.989628', 5);
INSERT INTO public.products VALUES (155, '第三方产品', '配件', '40425003', '漏泄同轴电缆', 'HLCTYZ-50-42', '尺寸：1-5/8＂特性：低烟无卤    用途：漏泄同轴电缆', '联创', '米', 83.00, 'active', NULL, '2025-04-15 00:23:07.941863', '2025-04-18 23:53:55.989629', 5);
INSERT INTO public.products VALUES (156, '第三方产品', '配件', 'OISKHB1JLC1', '跳线', 'E-JP50-7', '长度：0.5米 接口：NJ转NJ 用途：天线连接跳线', '国产', '根', 35.00, 'active', NULL, '2025-04-15 00:23:07.941864', '2025-04-20 18:33:30.442671', 5);
INSERT INTO public.products VALUES (157, '第三方产品', '配件', 'EJUMJK4310NJNJ', '同轴电缆跳接线', 'NJ/NJ-3 1米', '接口：NJ转NJ    长度：1米    用途：机柜内跳线', '国产', '根', 37.00, 'active', NULL, '2025-04-15 00:23:07.941864', '2025-04-20 18:33:31.549517', 5);
INSERT INTO public.products VALUES (158, '第三方产品', '配件', 'W0000225', '同轴电缆跳接线', 'NJ/NJ-3 10米', '接口：NJ转NJ    长度：10米    用途：机柜内跳线', '国产', '根', 100.00, 'active', NULL, '2025-04-15 00:23:07.941865', '2025-04-18 23:53:55.989631', 5);
INSERT INTO public.products VALUES (159, '第三方产品', '配件', 'W000188', '超柔同轴电缆跳接线', 'NJ-3/NJ-3-1.5M', '接口：NJ转NJ    长度：1.5米    特性1：超柔    特性2：SYV-50-3', '国产', '根', 100.00, 'active', NULL, '2025-04-15 00:23:07.941865', '2025-04-18 23:53:55.989631', 5);
INSERT INTO public.products VALUES (160, '第三方产品', '配件', 'W000185', '同轴电缆跳接线', 'NJ-3/NJ-3-0.3M', '接口：NJ转NJ    长度：0.3米    用途：机柜内跳线', '国产', '根', 33.00, 'active', NULL, '2025-04-15 00:23:07.941866', '2025-04-18 23:53:55.989632', 5);
INSERT INTO public.products VALUES (161, '第三方产品', '配件', 'EJUMJK4320NJQJ', '同轴电缆跳接线', 'N/Q9-3 2米', '接口：NJ转BNC    长度：2米    用途：机柜内跳线', '国产', '根', 35.00, 'active', NULL, '2025-04-15 00:23:07.941867', '2025-04-18 23:53:55.989633', 5);
INSERT INTO public.products VALUES (162, '第三方产品', '配件', 'EJUMJK4325NJNJ', '同轴电缆跳接线', 'NJ-3/NJ-3_2.5m', '接口：NJ转NJ    长度：2.5米    用途：机柜内跳线', '国产', '根', 42.00, 'active', NULL, '2025-04-15 00:23:07.941867', '2025-04-18 23:53:55.989633', 5);
INSERT INTO public.products VALUES (163, '第三方产品', '配件', 'EJUMJK4315NJQJ', '同轴电缆跳接线', 'NJ/Q9-3 1.5米', '接口：NJ转BNC    长度：1.5米    用途：机柜内跳线', '国产', '根', 38.00, 'active', NULL, '2025-04-15 00:23:07.941868', '2025-04-18 23:53:55.989634', 5);
INSERT INTO public.products VALUES (164, '第三方产品', '配件', 'EJUMJK4320NJNJ', '同轴电缆跳接线', 'NJ/NJ-3 2米', '接口：NJ转NJ    长度：2米    用途：机柜内跳线', '国产', '根', 41.00, 'active', NULL, '2025-04-15 00:23:07.941869', '2025-04-18 23:53:55.989635', 5);
INSERT INTO public.products VALUES (165, '第三方产品', '配件', 'EJUMJK4315NJNJ', '同轴电缆跳接线', 'NJ/NJ-3 1.5米', '接口：NJ转NJ    长度：1.5米    用途：机柜内跳线', '国产', '根', 40.00, 'active', NULL, '2025-04-15 00:23:07.941869', '2025-04-18 23:53:55.989635', 5);
INSERT INTO public.products VALUES (166, '第三方产品', '配件', 'EJUMJK4310NJQJ', '同轴电缆跳接线', 'NJ/Q9-3 1米', '接口：NJ转BNC    长度：1米    用途：机柜内跳线', '国产', '根', 34.00, 'active', NULL, '2025-04-15 00:23:07.94187', '2025-04-18 23:53:55.989636', 5);
INSERT INTO public.products VALUES (167, '第三方产品', '配件', 'W000163', '终端负载', 'E-TF50', '功率：50W    接口：N型', '国产', '个', 142.00, 'active', NULL, '2025-04-15 00:23:07.941871', '2025-04-20 18:33:34.651458', 5);
INSERT INTO public.products VALUES (168, '第三方产品', '配件', 'OCIN5JZALC1', '同轴电缆连接器', 'N-J1/2', '尺寸：1/2＂    接口：N-J     外径：15.7mm    用途：同轴电缆连接器', '国产', '只', 15.00, 'active', NULL, '2025-04-15 00:23:07.941871', '2025-04-20 18:33:35.504947', 5);
INSERT INTO public.products VALUES (169, '第三方产品', '配件', 'OCIN5JWALC1', '同轴电缆连接转换器', 'N-50JKW', '类型：N型    特性：直角弯    用途：连接器', '国产', '只', 15.00, 'active', NULL, '2025-04-15 00:23:07.941872', '2025-04-18 23:53:55.989638', 5);
INSERT INTO public.products VALUES (170, '第三方产品', '配件', 'OCIN5KZALC1', '同轴电缆连接转换器', 'N-50KK', '类型：N型    特性：双通    用途：连接器', '国产', '只', 15.00, 'active', NULL, '2025-04-15 00:23:07.941873', '2025-04-18 23:53:55.989639', 5);
INSERT INTO public.products VALUES (171, '第三方产品', '配件', 'OCIN5JZELC1', '同轴电缆连接器', 'N-J7/8', '尺寸：7/8＂    接口：N-J    外径：32.5mm    用途：同轴电缆连接器', '国产', '只', 30.00, 'active', NULL, '2025-04-15 00:23:07.941873', '2025-04-18 23:53:55.98964', 5);
INSERT INTO public.products VALUES (175, '第三方产品', '配件', 'W000160', '馈线接地卡', '环扣式接地卡', '尺寸：1/2＂    长度：5m    线径：BVC16mm平方     用途：漏缆专用接地卡', '联创', '个', 67.00, 'active', NULL, '2025-04-15 00:23:07.941876', '2025-04-18 23:53:55.989643', 5);
INSERT INTO public.products VALUES (176, '第三方产品', '配件', 'W000159', '馈线接地卡', '环扣式接地卡', '尺寸：7/8＂    长度：5m    线径：BVC16mm平方     用途：漏缆专用接地卡', '联创', '个', 75.00, 'active', NULL, '2025-04-15 00:23:07.941877', '2025-04-18 23:53:55.989644', 5);
INSERT INTO public.products VALUES (177, '第三方产品', '配件', 'W000140', '馈线接地卡', '环扣式接地卡', '尺寸：1-5/8＂    长度：5m    线径：-22     用途：漏缆专用接地卡', '联创', '个', 170.00, 'active', NULL, '2025-04-15 00:23:07.941877', '2025-04-18 23:53:55.989644', 5);
INSERT INTO public.products VALUES (178, '第三方产品', '配件', '4042RNM', '1-5/8”漏泄同轴电缆接头', 'NM-42R', '尺寸：1-5/8”    用途：漏泄同轴电缆接头', '联创', '个', 150.00, 'active', NULL, '2025-04-15 00:23:07.941878', '2025-04-18 23:53:55.989645', 5);
INSERT INTO public.products VALUES (179, '第三方产品', '配件', '4042RDNPT', '1-5/8”漏泄同轴电缆吊夹', 'KXC-42R-DNPT', '尺寸：1-5/8”    用途：漏泄同轴电缆吊夹', '联创', '个', 33.00, 'active', NULL, '2025-04-15 00:23:07.941879', '2025-04-18 23:53:55.989646', 5);
INSERT INTO public.products VALUES (180, '第三方产品', '配件', '4042RDNFH', '1-5/8”漏泄同轴电缆防火吊夹', 'KXC-42R-DNFH', '尺寸：1-5/8”    用途：漏泄同轴电缆防火吊夹', '联创', '个', 40.00, 'active', NULL, '2025-04-15 00:23:07.941879', '2025-04-18 23:53:55.989648', 5);
INSERT INTO public.products VALUES (181, '第三方产品', '配件', 'W000141', '直流隔断器', 'DC-BLOCK', '测试电压：DC100V    接口类型：N公-N母    最大功率：5W    频率：DC-6GHz        外形尺寸：φ15.8*50mm', '定制', '个', 330.00, 'active', NULL, '2025-04-15 00:23:07.94188', '2025-04-18 23:53:55.989649', 5);
INSERT INTO public.products VALUES (182, '第三方产品', '服务', 'W000008', '施工附件', '/', '安装所需要的小型支架    紧固件    防水胶布    轧带和标签    管线材料    按施工要求决定', '服务', '批', 0.00, 'active', NULL, '2025-04-15 00:23:07.941881', '2025-04-20 18:33:38.697715', 5);
INSERT INTO public.products VALUES (183, '第三方产品', '服务', 'F0005', '调试开通', '/', '-深化图纸现场施工图    竣工图纸
-安装督导和图纸交底协调
-部署调试开通    软件环境部署    培训', '服务', '次', 30000.00, 'active', NULL, '2025-04-15 00:23:07.941881', '2025-04-20 18:33:39.496499', 5);
INSERT INTO public.products VALUES (184, '第三方产品', '服务', 'F0011', '主站频率占用费', '转移支付', '根据系统使用的信道机数量来申报的每年一次的基站频率占用费    按国家核定标准收取', '服务', '台', 3300.00, 'active', NULL, '2025-04-15 00:23:07.941882', '2025-04-20 18:33:40.286414', 5);
INSERT INTO public.products VALUES (185, '第三方产品', '服务', 'F0010', '对讲机频率占用费', '转移支付', '根据系统使用的对讲机终端数量来申报的每年一次的对讲机频率占用费    按国家核定标准收取', '服务', '台', 170.00, 'active', NULL, '2025-04-15 00:23:07.941883', '2025-04-20 16:38:24.018364', 5);
INSERT INTO public.products VALUES (186, '第三方产品', '服务', 'F0012', '电磁环境检测及申报报告费', '/', '提供前期安装现场电磁环境测试和申请频率的初选建议报告及提高无线电管理局的申报材料的准备    指导申请过程    包含1天的现场测试二个工程师    2天测试报告的撰写和一周的资料准备工作量', '服务', '次', 8000.00, 'active', NULL, '2025-04-15 00:23:07.941883', '2025-04-20 18:33:41.716173', 5);


--
-- Data for Name: product_codes; Type: TABLE DATA; Schema: public; Owner: pma_user
--



--
-- Data for Name: product_code_field_values; Type: TABLE DATA; Schema: public; Owner: pma_user
--



--
-- Data for Name: project_members; Type: TABLE DATA; Schema: public; Owner: pma_user
--



--
-- Data for Name: quotations; Type: TABLE DATA; Schema: public; Owner: pma_user
--

INSERT INTO public.quotations VALUES (10, 'QU202504-010', 2, NULL, 184.74, NULL, NULL, '2025-04-22 10:14:58.656105', '2025-04-22 10:24:27.884351', 5);
INSERT INTO public.quotations VALUES (14, 'QU202504-014', 1, NULL, 116667, NULL, NULL, '2025-04-22 11:07:19.876548', '2025-04-22 11:07:19.876553', 5);
INSERT INTO public.quotations VALUES (16, 'QU202504-016', 5, NULL, 711.42, NULL, NULL, '2025-04-22 11:50:16.94874', '2025-04-24 04:18:12.650114', 6);
INSERT INTO public.quotations VALUES (17, 'QU202504-017', 6, NULL, 400.22, NULL, NULL, '2025-04-23 04:49:52.746543', '2025-05-01 09:09:02.621331', 5);
INSERT INTO public.quotations VALUES (18, 'QU202504-145', 56, NULL, 13916, '招标中', NULL, '2025-04-17 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (20, 'QU202503-019', 64, NULL, 984312, '签约', NULL, '2025-03-24 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (21, 'QU202503-020', 67, NULL, 117016, '签约', NULL, '2025-03-24 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (22, 'QU202503-021', 70, NULL, 203797, '签约', NULL, '2025-03-09 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (23, 'QU202502-025', 55, NULL, 83247, '品牌植入', NULL, '2025-02-23 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (24, 'QU202502-026', 66, NULL, 86873, '签约', NULL, '2025-02-13 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (25, 'QU202502-027', 84, NULL, 176468, '品牌植入', NULL, '2025-02-10 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (26, 'QU202502-028', 72, NULL, 476420, '招标中', NULL, '2025-02-06 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (27, 'QU202501-013', 85, NULL, 480197, '品牌植入', NULL, '2025-01-09 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (28, 'QU202501-014', 110, NULL, 164050, '签约', NULL, '2025-01-01 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (29, 'QU202412-037', 53, NULL, 362013, '品牌植入', NULL, '2024-12-27 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (30, 'QU202412-038', 59, NULL, 1955362, '中标', NULL, '2024-12-25 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (31, 'QU202412-039', 80, NULL, 524616, '品牌植入', NULL, '2024-12-20 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (32, 'QU202412-040', 89, NULL, 720113, '品牌植入', NULL, '2024-12-20 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (33, 'QU202412-041', 68, NULL, 1506548, '中标', NULL, '2024-12-06 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (34, 'QU202412-042', 54, NULL, 703335, '签约', NULL, '2024-12-04 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (35, 'QU202411-019', 69, NULL, 184100, '中标', NULL, '2024-11-15 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (36, 'QU202411-020', 78, NULL, 193868, '招标前', NULL, '2024-11-15 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (37, 'QU202411-021', 88, NULL, 852209, '失败', NULL, '2024-11-08 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (38, 'QU202410-007', 77, NULL, 169599, '品牌植入', NULL, '2024-10-23 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (39, 'QU202409-013', 79, NULL, 205651, '品牌植入', NULL, '2024-09-20 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (40, 'QU202409-014', 91, NULL, 1986595, '品牌植入', NULL, '2024-09-06 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (41, 'QU202408-007', 97, NULL, 229944, '招标前', NULL, '2024-08-08 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (42, 'QU202407-019', 99, NULL, 148433, '品牌植入', NULL, '2024-07-28 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (43, 'QU202407-020', 101, NULL, 518741, '品牌植入', NULL, '2024-07-15 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (44, 'QU202407-021', 50, NULL, 850252, '签约', NULL, '2024-07-10 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (45, 'QU202406-013', 71, NULL, 528356, '失败', NULL, '2024-06-21 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (46, 'QU202406-014', 98, NULL, 135415, '签约', NULL, '2024-06-18 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (47, 'QU202405-007', 90, NULL, 175868, '品牌植入', NULL, '2024-05-08 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (48, 'QU202404-013', 109, NULL, 32528, '签约', NULL, '2024-04-24 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (49, 'QU202404-014', 107, NULL, 45056, '签约', NULL, '2024-04-11 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (50, 'QU202402-007', 96, NULL, 367785, '品牌植入', NULL, '2024-02-28 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (51, 'QU202311-157', 57, NULL, 1070544, '中标', NULL, '2023-10-31 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (52, 'QU202311-158', 60, NULL, 2771088, '招标中', NULL, '2023-10-31 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (53, 'QU202311-159', 73, NULL, 644950, '中标', NULL, '2023-10-31 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (54, 'QU202311-160', 74, NULL, 272060, '品牌植入', NULL, '2023-10-31 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (55, 'QU202311-161', 75, NULL, 153598, '品牌植入', NULL, '2023-10-31 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (56, 'QU202311-162', 76, NULL, 374246, '品牌植入', NULL, '2023-10-31 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (57, 'QU202311-163', 81, NULL, 645204, '招标前', NULL, '2023-10-31 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (58, 'QU202311-164', 82, NULL, 591916, '搁置', NULL, '2023-10-31 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (59, 'QU202311-165', 83, NULL, 3649725, '搁置', NULL, '2023-10-31 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (60, 'QU202311-166', 87, NULL, 3050914, '搁置 ', NULL, '2023-10-31 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (61, 'QU202311-167', 92, NULL, 383480, '招标中', NULL, '2023-10-31 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (62, 'QU202311-168', 93, NULL, 217906, '品牌植入', NULL, '2023-10-31 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (63, 'QU202311-169', 94, NULL, 502526, '招标前', NULL, '2023-10-31 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (64, 'QU202311-170', 95, NULL, 346687, '招标前', NULL, '2023-10-31 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (65, 'QU202311-171', 100, NULL, 146451, '品牌植入', NULL, '2023-10-31 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (66, 'QU202311-172', 102, NULL, 97202, '招标前', NULL, '2023-10-31 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (67, 'QU202311-173', 103, NULL, 301086, '品牌植入', NULL, '2023-10-31 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (68, 'QU202311-174', 104, NULL, 57448, '品牌植入', NULL, '2023-10-31 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (69, 'QU202311-175', 105, NULL, 643544, '招标前', NULL, '2023-10-31 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (70, 'QU202311-176', 106, NULL, 403410, '招标中', NULL, '2023-10-31 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (71, 'QU202311-177', 108, NULL, 410528, '品牌植入', NULL, '2023-10-31 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (72, 'QU202311-178', 111, NULL, 69716, '品牌植入', NULL, '2023-10-31 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (73, 'QU202311-179', 112, NULL, 305198, '品牌植入', NULL, '2023-10-31 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (74, 'QU202311-180', 113, NULL, 391058, '品牌植入', NULL, '2023-10-31 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (75, 'QU202311-181', 114, NULL, 33503, '品牌植入', NULL, '2023-10-31 00:00:00', '2025-04-30 00:00:00', 16);
INSERT INTO public.quotations VALUES (76, 'QU202311-182', 115, NULL, 238670, '品牌植入', NULL, '2023-10-31 00:00:00', '2025-04-30 00:00:00', 16);


--
-- Data for Name: quotation_details; Type: TABLE DATA; Schema: public; Owner: pma_user
--

INSERT INTO public.quotation_details VALUES (11, 10, '定向耦合器', 'EVDC-6 LT', '频率范围：150-170MHz    承载功率：100W;耦合规格：6dB', '和源通信', '套', 1, 0.01004, 184, 184.736, 184.736, 'HYCCN31Y', '2025-04-22 18:24:27.889045', '2025-04-22 18:24:27.889051');
INSERT INTO public.quotation_details VALUES (15, 14, '广播多频点调频处理器', 'E-BDA088-U FM', '频率范围：087-108MHz;最大功率：1mW;机柜式;尺寸：3U;供电供电220VAC;内置功能：16信道广播接入&广播告警切换;监控能力：不支持', '和源通信', '套', 1, 1, 116667, 116667, 116667, NULL, '2025-04-22 19:07:19.877818', '2025-04-22 19:07:19.87783');
INSERT INTO public.quotation_details VALUES (19, 16, '功率分配器', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 5, 1, 142, 142.284, 711.42, 'HYCDN24Y', '2025-04-24 12:18:12.654709', '2025-04-24 12:18:12.654714');
INSERT INTO public.quotation_details VALUES (20, 18, '雄安国贸中心项目43#楼精装修工程及弱电智能化工程', 'NFX_GATW', '用于本地系统设备管理和服务器的同步 -本地系统建立和配置 -设备驱动管理 -设备参数设置 -云同步 -设备报警管理', '和源通信', '套', 1, 1, 12500, 12500, 12500, 'HYWG0NB1', '2025-04-18 00:00:00', '2025-04-19 00:00:00');
INSERT INTO public.quotation_details VALUES (21, 18, '雄安国贸中心项目43#楼精装修工程及弱电智能化工程', 'E-ANTD 400', '频率范围：400-430MHz 增益：2.5dBi 防护等级：IP65 辐射方向：定向 最大承载功率：50W 接头类型：N-Femade 特性：室外', '和源通信', '套', 1, 1, 354, 354, 1416, 'EAN2OFD2TE2', '2025-04-18 00:00:00', '2025-04-19 00:00:00');
INSERT INTO public.quotation_details VALUES (37, 20, '无锡奥林匹克体育产业中心二期项目', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '套', 1, 0.45, 142, 142, 46008, 'HYAIOCN4Y', '2025-03-25 00:00:00', '2025-04-02 00:00:00');
INSERT INTO public.quotation_details VALUES (38, 20, '无锡奥林匹克体育产业中心二期项目', 'RFS-400 LT/M', '频率范围：350-50MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 1, 0.45, 9876, 9876, 69132, 'HYR2SI030', '2025-03-25 00:00:00', '2025-04-02 00:00:00');
INSERT INTO public.quotation_details VALUES (39, 20, '无锡奥林匹克体育产业中心二期项目', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 1, 0.45, 142, 142, 59924, 'HYCCN34Y', '2025-03-25 00:00:00', '2025-04-02 00:00:00');
INSERT INTO public.quotation_details VALUES (40, 20, '无锡奥林匹克体育产业中心二期项目', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 1, 0.45, 142, 142, 10508, 'HYCDN24Y', '2025-03-25 00:00:00', '2025-04-02 00:00:00');
INSERT INTO public.quotation_details VALUES (41, 20, '无锡奥林匹克体育产业中心二期项目', 'E-ANTD 400', '频率范围：400-430MHz 增益：2.5dBi 防护等级：IP65 辐射方向：定向 最大承载功率：50W 接头类型：N-Femade 特性：室外', '和源通信', '套', 1, 0.45, 354, 354, 9912, 'EAN2OFD2TE2', '2025-03-25 00:00:00', '2025-04-02 00:00:00');
INSERT INTO public.quotation_details VALUES (42, 20, '无锡奥林匹克体育产业中心二期项目', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 1, 0.45, 458, 458, 916, 'EANLOMO5HR1', '2025-03-25 00:00:00', '2025-04-02 00:00:00');
INSERT INTO public.quotation_details VALUES (43, 20, '无锡奥林匹克体育产业中心二期项目', 'PNR2000', '频率范围：400-470MHz    锂电池 3700mAh', '和源通信', '套', 1, 0.45, 1333, 1333, 53320, 'HYTD4MA', '2025-03-25 00:00:00', '2025-04-02 00:00:00');
INSERT INTO public.quotation_details VALUES (44, 20, '无锡奥林匹克体育产业中心二期项目', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 1U机箱 功能： 网讯平台', '和源通信', '套', 1, 0.45, 11851, 11851, 319977, 'HYR3SI140', '2025-03-25 00:00:00', '2025-04-02 00:00:00');
INSERT INTO public.quotation_details VALUES (45, 20, '无锡奥林匹克体育产业中心二期项目', 'E-FHP2000-2', '频率范围：351-366/410-424MHz 单端口承载功率：50W 插入损耗：≤1.5dB 接入端口数量：2 安装方式：机柜式 尺寸：2U', '和源通信', '套', 1, 0.45, 7917, 7917, 142506, 'ECM1BB22CZ2', '2025-03-25 00:00:00', '2025-04-02 00:00:00');
INSERT INTO public.quotation_details VALUES (46, 20, '无锡奥林匹克体育产业中心二期项目', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 1, 0.45, 142, 142, 12212, 'HYCCN34Y', '2025-03-25 00:00:00', '2025-04-02 00:00:00');
INSERT INTO public.quotation_details VALUES (47, 20, '无锡奥林匹克体育产业中心二期项目', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 1, 0.45, 142, 142, 994, 'HYCDN24Y', '2025-03-25 00:00:00', '2025-04-02 00:00:00');
INSERT INTO public.quotation_details VALUES (48, 20, '无锡奥林匹克体育产业中心二期项目', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 0.45, 4569, 4569, 4569, 'EDE1AU6xCZ1', '2025-03-25 00:00:00', '2025-04-02 00:00:00');
INSERT INTO public.quotation_details VALUES (49, 20, '无锡奥林匹克体育产业中心二期项目', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 0.45, 4569, 4569, 4569, 'EDE1AD6xCZ1', '2025-03-25 00:00:00', '2025-04-02 00:00:00');
INSERT INTO public.quotation_details VALUES (50, 20, '无锡奥林匹克体育产业中心二期项目', 'E-ANTD 400', '频率范围：400-430MHz 增益：2.5dBi 防护等级：IP65 辐射方向：定向 最大承载功率：50W 接头类型：N-Femade 特性：室外', '和源通信', '套', 1, 0.45, 354, 354, 1416, 'EAN2OFD2TE2', '2025-03-25 00:00:00', '2025-04-02 00:00:00');
INSERT INTO public.quotation_details VALUES (51, 20, '无锡奥林匹克体育产业中心二期项目', 'RFS-400 LT/M', '频率范围：350-50MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 1, 0.45, 9876, 9876, 19752, 'HYR2SI030', '2025-03-25 00:00:00', '2025-04-02 00:00:00');
INSERT INTO public.quotation_details VALUES (52, 20, '无锡奥林匹克体育产业中心二期项目', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 1U机箱 功能： 网讯平台', '和源通信', '套', 1, 0.45, 11851, 11851, 94808, 'HYR3SI140', '2025-03-25 00:00:00', '2025-04-02 00:00:00');
INSERT INTO public.quotation_details VALUES (53, 20, '无锡奥林匹克体育产业中心二期项目', 'E-FHP2000-2', '频率范围：351-366/410-424MHz 单端口承载功率：50W 插入损耗：≤1.5dB 接入端口数量：2 安装方式：机柜式 尺寸：2U', '和源通信', '套', 1, 0.45, 7917, 7917, 39585, 'ECM1BB22CZ2', '2025-03-25 00:00:00', '2025-04-02 00:00:00');
INSERT INTO public.quotation_details VALUES (54, 20, '无锡奥林匹克体育产业中心二期项目', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W-网讯平台-数模兼容', '和源通信', '套', 1, 0.45, 13580, 13580, 40740, 'HYPSMXI40', '2025-03-25 00:00:00', '2025-04-02 00:00:00');
INSERT INTO public.quotation_details VALUES (55, 20, '无锡奥林匹克体育产业中心二期项目', 'E-FH400-4', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤8.5dB 接入端口数量：4 安装方式：机柜式 尺寸2U', '和源通信', '套', 1, 0.45, 6642, 6642, 6642, 'ECM1B042CZ1', '2025-03-25 00:00:00', '2025-04-02 00:00:00');
INSERT INTO public.quotation_details VALUES (56, 20, '无锡奥林匹克体育产业中心二期项目', 'E-JF350/400-4', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤7.5dB 接入端口数量：4 安装方式：机柜式 尺寸1U', '和源通信', '套', 1, 0.45, 2493, 2493, 2493, 'EDE1BU4xCZ1', '2025-03-25 00:00:00', '2025-04-02 00:00:00');
INSERT INTO public.quotation_details VALUES (57, 20, '无锡奥林匹克体育产业中心二期项目', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '套', 1, 0.45, 142, 142, 13916, 'HYAIOCN4Y', '2025-03-25 00:00:00', '2025-04-02 00:00:00');
INSERT INTO public.quotation_details VALUES (58, 20, '无锡奥林匹克体育产业中心二期项目', 'PNR2000', '频率范围：400-470MHz    锂电池 3700mAh', '和源通信', '套', 1, 0.45, 1333, 1333, 26660, 'HYTD4MA', '2025-03-25 00:00:00', '2025-04-02 00:00:00');
INSERT INTO public.quotation_details VALUES (59, 20, '无锡奥林匹克体育产业中心二期项目', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 1, 0.45, 3753, 3753, 3753, 'EDULN4N1CZ1', '2025-03-25 00:00:00', '2025-04-02 00:00:00');
INSERT INTO public.quotation_details VALUES (60, 21, '上海静安太保家园', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 1, 0.45, 2320, 2320, 2320, 'EDE1BU2xCZ1', '2025-03-25 00:00:00', '2025-03-29 00:00:00');
INSERT INTO public.quotation_details VALUES (61, 21, '上海静安太保家园', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 1, 0.45, 3753, 3753, 3753, 'EDULN4N1CZ1', '2025-03-25 00:00:00', '2025-03-29 00:00:00');
INSERT INTO public.quotation_details VALUES (62, 21, '上海静安太保家园', 'E-BDA400B LT', '频率范围：410-414/420-424 , 链路带宽 4MHz, 最大射频输出功率 33dBm(2W)', '和源通信', '套', 1, 0.45, 8396, 8396, 8396, 'HYR1SN140', '2025-03-25 00:00:00', '2025-03-29 00:00:00');
INSERT INTO public.quotation_details VALUES (63, 21, '上海静安太保家园', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '套', 1, 0.45, 142, 142, 8378, 'HYAIOCN4Y', '2025-03-25 00:00:00', '2025-03-29 00:00:00');
INSERT INTO public.quotation_details VALUES (64, 21, '上海静安太保家园', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 1, 0.45, 142, 142, 142, 'HYCDN24Y', '2025-03-25 00:00:00', '2025-03-29 00:00:00');
INSERT INTO public.quotation_details VALUES (65, 21, '上海静安太保家园', 'PNR2000', '频率范围：400-470MHz，锂电池 3700mAh', '和源通信', '套', 1, 0.45, 1333, 1333, 53320, 'HYTD4MA', '2025-03-25 00:00:00', '2025-03-29 00:00:00');
INSERT INTO public.quotation_details VALUES (66, 21, '上海静安太保家园', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W-网讯平台-数模兼容', '和源通信', '套', 1, 0.45, 13580, 13580, 27160, 'HYPSMXI40', '2025-03-25 00:00:00', '2025-03-29 00:00:00');
INSERT INTO public.quotation_details VALUES (67, 21, '上海静安太保家园', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 1, 0.45, 4569, 4569, 4569, 'ECM1B022CZ1', '2025-03-25 00:00:00', '2025-03-29 00:00:00');
INSERT INTO public.quotation_details VALUES (68, 21, '上海静安太保家园', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 1, 0.45, 142, 142, 8520, 'HYCCN34Y', '2025-03-25 00:00:00', '2025-03-29 00:00:00');
INSERT INTO public.quotation_details VALUES (69, 21, '上海静安太保家园', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 1, 0.45, 458, 458, 458, 'EANLOMO5HR1', '2025-03-25 00:00:00', '2025-03-29 00:00:00');
INSERT INTO public.quotation_details VALUES (70, 22, '荡口古镇太师府酒店建设项目智能化工程', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 1, 0.42, 4569, 4569, 4569, 'ECM1B022CZ1', '2025-03-10 00:00:00', '2025-03-28 00:00:00');
INSERT INTO public.quotation_details VALUES (71, 22, '荡口古镇太师府酒店建设项目智能化工程', 'RFS-400 LT/M', '频率范围：350-50MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 1, 0.42, 9876, 9876, 29628, 'HYR2SI030', '2025-03-10 00:00:00', '2025-03-28 00:00:00');
INSERT INTO public.quotation_details VALUES (72, 22, '荡口古镇太师府酒店建设项目智能化工程', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 1U机箱 功能： 网讯平台', '和源通信', '套', 1, 0.42, 11851, 11851, 106659, 'HYR3SI140', '2025-03-10 00:00:00', '2025-03-28 00:00:00');
INSERT INTO public.quotation_details VALUES (73, 22, '荡口古镇太师府酒店建设项目智能化工程', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '套', 1, 0.42, 142, 142, 22720, 'HYAIOCN4Y', '2025-03-10 00:00:00', '2025-03-28 00:00:00');
INSERT INTO public.quotation_details VALUES (74, 22, '荡口古镇太师府酒店建设项目智能化工程', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 1, 0.42, 142, 142, 22720, 'HYCCN34Y', '2025-03-10 00:00:00', '2025-03-28 00:00:00');
INSERT INTO public.quotation_details VALUES (75, 22, '荡口古镇太师府酒店建设项目智能化工程', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 1, 0.42, 458, 458, 2290, 'EANLOMO5HR1', '2025-03-10 00:00:00', '2025-03-28 00:00:00');
INSERT INTO public.quotation_details VALUES (76, 22, '荡口古镇太师府酒店建设项目智能化工程', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 0.42, 4569, 4569, 4569, 'EDE1AD6xCZ1', '2025-03-10 00:00:00', '2025-03-28 00:00:00');
INSERT INTO public.quotation_details VALUES (77, 22, '荡口古镇太师府酒店建设项目智能化工程', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 1, 0.42, 2320, 2320, 2320, 'EDE1BU2xCZ1', '2025-03-10 00:00:00', '2025-03-28 00:00:00');
INSERT INTO public.quotation_details VALUES (78, 22, '荡口古镇太师府酒店建设项目智能化工程', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 1, 0.42, 3753, 3753, 3753, 'EDULN4N1CZ1', '2025-03-10 00:00:00', '2025-03-28 00:00:00');
INSERT INTO public.quotation_details VALUES (79, 22, '荡口古镇太师府酒店建设项目智能化工程', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 0.42, 4569, 4569, 4569, 'EDE1AU6xCZ1', '2025-03-10 00:00:00', '2025-03-28 00:00:00');
INSERT INTO public.quotation_details VALUES (80, 23, '北京新首钢园东南区1612-(769)地块项目-调整增补', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4569, 4569, 4569, 'EDE1AD6xCZ1', '2025-02-24 00:00:00', '2025-02-24 00:00:00');
INSERT INTO public.quotation_details VALUES (81, 23, '北京新首钢园东南区1612-(769)地块项目-调整增补', 'RFS-400 LT/M', '频率范围：350-50MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 1, 1, 9876, 9876, 39504, 'HYR2SI030', '2025-02-24 00:00:00', '2025-02-24 00:00:00');
INSERT INTO public.quotation_details VALUES (82, 23, '北京新首钢园东南区1612-(769)地块项目-调整增补', 'NJ/Q9-3 1.5米', '接口：NJ转BNC    长度：1.5米    用途：机柜内跳线', '国产', '根', 1, 1, 38, 38, 76, 'EJUMJK4315NJQJ', '2025-02-24 00:00:00', '2025-02-24 00:00:00');
INSERT INTO public.quotation_details VALUES (83, 23, '北京新首钢园东南区1612-(769)地块项目-调整增补', 'NJ/NJ-3 1.5米', '接口：NJ转NJ    长度：1.5米    用途：机柜内跳线', '国产', '根', 1, 1, 40, 40, 480, 'EJUMJK4315NJNJ', '2025-02-24 00:00:00', '2025-02-24 00:00:00');
INSERT INTO public.quotation_details VALUES (84, 23, '北京新首钢园东南区1612-(769)地块项目-调整增补', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W-网讯平台-数模兼容', '和源通信', '套', 1, 1, 13580, 13580, 27160, 'HYPSMXI40', '2025-02-24 00:00:00', '2025-02-24 00:00:00');
INSERT INTO public.quotation_details VALUES (85, 23, '北京新首钢园东南区1612-(769)地块项目-调整增补', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 1, 1, 4569, 4569, 4569, 'ECM1B022CZ1', '2025-02-24 00:00:00', '2025-02-24 00:00:00');
INSERT INTO public.quotation_details VALUES (86, 23, '北京新首钢园东南区1612-(769)地块项目-调整增补', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 1, 1, 2320, 2320, 2320, 'EDE1BU2xCZ1', '2025-02-24 00:00:00', '2025-02-24 00:00:00');
INSERT INTO public.quotation_details VALUES (87, 23, '北京新首钢园东南区1612-(769)地块项目-调整增补', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4569, 4569, 4569, 'EDE1AU6xCZ1', '2025-02-24 00:00:00', '2025-02-24 00:00:00');
INSERT INTO public.quotation_details VALUES (88, 24, '上海市松江区巨人科技园B楼项目弱电智能化投标项目', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '', 1, 0.45, 9876, 9876, 19752, 'HYR2SI030', '2025-02-14 00:00:00', '2025-03-28 00:00:00');
INSERT INTO public.quotation_details VALUES (89, 24, '上海市松江区巨人科技园B楼项目弱电智能化投标项目', 'E-BDA400B LT', '频率范围：410~414/420~424 , 链路带宽 4MHz, 最大射频输出功率 33dBm(2W)', '和源通信', '', 1, 0.45, 8396, 8396, 16792, 'HYR1SN140', '2025-02-14 00:00:00', '2025-03-28 00:00:00');
INSERT INTO public.quotation_details VALUES (90, 24, '上海市松江区巨人科技园B楼项目弱电智能化投标项目', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '', 1, 0.45, 2320, 2320, 2320, 'EDE1BU2xCZ1', '2025-02-14 00:00:00', '2025-03-28 00:00:00');
INSERT INTO public.quotation_details VALUES (91, 24, '上海市松江区巨人科技园B楼项目弱电智能化投标项目', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '', 1, 0.45, 4569, 4569, 4569, 'ECM1B022CZ1', '2025-02-14 00:00:00', '2025-03-28 00:00:00');
INSERT INTO public.quotation_details VALUES (92, 24, '上海市松江区巨人科技园B楼项目弱电智能化投标项目', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 1U机箱 功能： 网讯平台', '和源通信', '', 1, 0.45, 11851, 11851, 23702, 'HYR3SI140', '2025-02-14 00:00:00', '2025-03-28 00:00:00');
INSERT INTO public.quotation_details VALUES (93, 24, '上海市松江区巨人科技园B楼项目弱电智能化投标项目', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '', 1, 0.45, 142, 142, 9798, 'HYAIOCN4Y', '2025-02-14 00:00:00', '2025-03-28 00:00:00');
INSERT INTO public.quotation_details VALUES (94, 24, '上海市松江区巨人科技园B楼项目弱电智能化投标项目', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 0.45, 142, 142, 9656, 'HYCCN34Y', '2025-02-14 00:00:00', '2025-03-28 00:00:00');
INSERT INTO public.quotation_details VALUES (95, 24, '上海市松江区巨人科技园B楼项目弱电智能化投标项目', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 0.45, 142, 142, 284, 'HYCDN24Y', '2025-02-14 00:00:00', '2025-03-28 00:00:00');
INSERT INTO public.quotation_details VALUES (96, 25, '兴化天宝皇冠酒店智能化项目', 'HCAAYZ -50-12', '尺寸：1/2＂    特性1：低烟无卤    特性2：阻燃    阻抗：50Ω', '浙江联创', '米', 1, 1, 13, 13, 39000, 'OZCH221035', '2025-02-11 00:00:00', '2025-02-11 00:00:00');
INSERT INTO public.quotation_details VALUES (97, 25, '兴化天宝皇冠酒店智能化项目', 'NJ-3/NJ-3-1.5M', '接口：NJ转NJ    长度：1.5米    特性1：超柔    特性2：SYV-50-3', '国产', '根', 1, 1, 100, 100, 600, 'W000188', '2025-02-11 00:00:00', '2025-02-11 00:00:00');
INSERT INTO public.quotation_details VALUES (98, 25, '兴化天宝皇冠酒店智能化项目', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 1, 1, 143, 143, 17160, 'HYCDN24Y', '2025-02-11 00:00:00', '2025-02-11 00:00:00');
INSERT INTO public.quotation_details VALUES (99, 25, '兴化天宝皇冠酒店智能化项目', 'EVDC-6 LT', '频率范围：150-170MHz    承载功率：100W;耦合规格：6dB', '和源通信', '套', 1, 1, 185, 185, 740, 'HYCCN31Y', '2025-02-11 00:00:00', '2025-02-11 00:00:00');
INSERT INTO public.quotation_details VALUES (100, 25, '兴化天宝皇冠酒店智能化项目', 'N-J1/2', '尺寸：1/2＂    接口：N-J     外径：15.7mm    用途：同轴电缆连接器', '国产', '只', 1, 1, 15, 15, 5250, 'OCIN5JZALC1', '2025-02-11 00:00:00', '2025-02-11 00:00:00');
INSERT INTO public.quotation_details VALUES (101, 25, '兴化天宝皇冠酒店智能化项目', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 1, 1, 458, 458, 458, 'EANLOMO5HR1', '2025-02-11 00:00:00', '2025-02-11 00:00:00');
INSERT INTO public.quotation_details VALUES (102, 25, '兴化天宝皇冠酒店智能化项目', 'MONT80', '曲臂长度50cm 材料：不锈钢 结构类型：L型结构', '国产', '套', 1, 1, 151, 151, 151, 'OBJANOTGR01', '2025-02-11 00:00:00', '2025-02-11 00:00:00');
INSERT INTO public.quotation_details VALUES (103, 25, '兴化天宝皇冠酒店智能化项目', 'CA-23RS', '频率范围：0-1000MHz 功率：700W 阻抗：50Ω 接口（可选）：N', '钻石', '套', 1, 1, 134, 134, 134, 'OBJANOTHS01', '2025-02-11 00:00:00', '2025-02-11 00:00:00');
INSERT INTO public.quotation_details VALUES (104, 25, '兴化天宝皇冠酒店智能化项目', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '套', 1, 1, 142, 142, 17324, 'HYAIOCN4Y', '2025-02-11 00:00:00', '2025-02-11 00:00:00');
INSERT INTO public.quotation_details VALUES (105, 25, '兴化天宝皇冠酒店智能化项目', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 1, 1, 4569, 4569, 4569, 'ECM1B022CZ1', '2025-02-11 00:00:00', '2025-02-11 00:00:00');
INSERT INTO public.quotation_details VALUES (106, 25, '兴化天宝皇冠酒店智能化项目', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 1, 1, 2321, 2321, 2321, 'EDE1BU2xCZ1', '2025-02-11 00:00:00', '2025-02-11 00:00:00');
INSERT INTO public.quotation_details VALUES (107, 25, '兴化天宝皇冠酒店智能化项目', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 1, 1, 3753, 3753, 3753, 'EDULN4N1CZ1', '2025-02-11 00:00:00', '2025-02-11 00:00:00');
INSERT INTO public.quotation_details VALUES (108, 25, '兴化天宝皇冠酒店智能化项目', 'E-BDA400B LT', '频率范围：410-414/420-424      链路带宽 4MHz     最大射频输出功率 33dBm(2W)', '和源通信', '套', 1, 1, 8396, 8396, 25188, 'HYR1SN140', '2025-02-11 00:00:00', '2025-02-11 00:00:00');
INSERT INTO public.quotation_details VALUES (109, 25, '兴化天宝皇冠酒店智能化项目', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W-网讯平台-数模兼容', '和源通信', '套', 1, 1, 13580, 13580, 27160, 'HYPSMXI40', '2025-02-11 00:00:00', '2025-02-11 00:00:00');
INSERT INTO public.quotation_details VALUES (110, 25, '兴化天宝皇冠酒店智能化项目', 'PNR2000', '频率范围：400-470MHz    锂电池 3700mAh', '和源通信', '套', 1, 1, 1333, 1333, 26660, 'HYTD4MA', '2025-02-11 00:00:00', '2025-02-11 00:00:00');
INSERT INTO public.quotation_details VALUES (111, 25, '兴化天宝皇冠酒店智能化项目', 'LS-VTT-RPT', '授权信道机在注册虚拟集群功能许可', '和源通信', '个', 1, 1, 3000, 3000, 6000, 'WCF9PH', '2025-02-11 00:00:00', '2025-02-11 00:00:00');
INSERT INTO public.quotation_details VALUES (112, 26, '国家会展中心(北区)厨房工程项目（天津）', 'HCAAYZ -50-12', '尺寸：1/2＂    特性1：低烟无卤    特性2：阻燃    阻抗：50Ω', '浙江联创', '米', 1, 1, 13, 13, 13000, 'OZCH221035', '2025-02-07 00:00:00', '2025-02-14 00:00:00');
INSERT INTO public.quotation_details VALUES (113, 26, '国家会展中心(北区)厨房工程项目（天津）', 'N-J1/2', '尺寸：1/2＂    接口：N-J     外径：15.7mm    用途：同轴电缆连接器', '国产', '只', 1, 1, 15, 15, 1200, 'OCIN5JZALC1', '2025-02-07 00:00:00', '2025-02-14 00:00:00');
INSERT INTO public.quotation_details VALUES (114, 26, '国家会展中心(北区)厨房工程项目（天津）', 'N-50KK', '类型：N型    特性：双通    用途：连接器', '国产', '只', 1, 1, 15, 15, 450, 'OCIN5KZALC1', '2025-02-07 00:00:00', '2025-02-14 00:00:00');
INSERT INTO public.quotation_details VALUES (115, 26, '国家会展中心(北区)厨房工程项目（天津）', 'NJ-3/NJ-3-1.5M', '接口：NJ转NJ    长度：1.5米    特性1：超柔    特性2：SYV-50-3', '国产', '根', 1, 1, 100, 100, 800, 'W000188', '2025-02-07 00:00:00', '2025-02-14 00:00:00');
INSERT INTO public.quotation_details VALUES (116, 26, '国家会展中心(北区)厨房工程项目（天津）', 'DRFS-300/M', '频率范围：350MHz 远端携带：32 数字型 功能：触摸屏/网讯平台', '和源通信', '套', 1, 1, 25000, 25000, 25000, 'HYR2DI030', '2025-02-07 00:00:00', '2025-02-14 00:00:00');
INSERT INTO public.quotation_details VALUES (117, 26, '国家会展中心(北区)厨房工程项目（天津）', 'DRFT-BDA310/M', '频率范围：351-356/361-366MHz；带宽：≤21M；输出：10W；数字型 功能：触摸屏/网讯平台 扩展：馈电', '和源通信', '套', 1, 1, 47918, 47918, 191672, 'HYR3DI330', '2025-02-07 00:00:00', '2025-02-14 00:00:00');
INSERT INTO public.quotation_details VALUES (118, 26, '国家会展中心(北区)厨房工程项目（天津）', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '套', 1, 1, 142, 142, 3976, 'HYAIOCN4Y', '2025-02-07 00:00:00', '2025-02-14 00:00:00');
INSERT INTO public.quotation_details VALUES (119, 26, '国家会展中心(北区)厨房工程项目（天津）', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 1, 1, 142, 142, 3124, 'HYCCN34Y', '2025-02-07 00:00:00', '2025-02-14 00:00:00');
INSERT INTO public.quotation_details VALUES (120, 26, '国家会展中心(北区)厨房工程项目（天津）', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 1, 1, 142, 142, 568, 'HYCDN24Y', '2025-02-07 00:00:00', '2025-02-14 00:00:00');
INSERT INTO public.quotation_details VALUES (121, 26, '国家会展中心(北区)厨房工程项目（天津）', 'ST/FC  8口', '尺寸类型：标准尺寸FC口    端口数：8口    产品类型：墙上型    特性：含法兰头    不含配套尾纤', '国产', '套', 1, 1, 250, 250, 1250, 'EDFWYFC08O', '2025-02-07 00:00:00', '2025-02-14 00:00:00');
INSERT INTO public.quotation_details VALUES (122, 26, '国家会展中心(北区)厨房工程项目（天津）', 'FC/APC-FC/APC 5M', '光纤类型：单模    光缆类型：单芯    接口类型：FC/APC-FC/APC    长度：5米', '国产', '根', 1, 1, 27, 27, 432, 'W000612', '2025-02-07 00:00:00', '2025-02-14 00:00:00');
INSERT INTO public.quotation_details VALUES (123, 26, '国家会展中心(北区)厨房工程项目（天津）', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4569, 4569, 9138, 'EDE1AU6xCZ1', '2025-02-07 00:00:00', '2025-02-14 00:00:00');
INSERT INTO public.quotation_details VALUES (124, 26, '国家会展中心(北区)厨房工程项目（天津）', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4569, 4569, 9138, 'EDE1AD6xCZ1', '2025-02-07 00:00:00', '2025-02-14 00:00:00');
INSERT INTO public.quotation_details VALUES (125, 26, '国家会展中心(北区)厨房工程项目（天津）', 'DRFS-400/M', '频率范围：410-414/420-424MHz 远端携带：32 数字型 功能：触摸屏/网讯平台', '和源通信', '套', 1, 1, 25000, 25000, 25000, 'HYR2DI040', '2025-02-07 00:00:00', '2025-02-14 00:00:00');
INSERT INTO public.quotation_details VALUES (126, 26, '国家会展中心(北区)厨房工程项目（天津）', 'DRFT-BDA410/M', '频率范围：410-414/420-424MHz 数字带宽：≤4M 输出：10W 数字型 功能：触摸屏/网讯平台 扩展：馈电', '和源通信', '套', 1, 1, 47918, 47918, 191672, 'HYR3DI340', '2025-02-07 00:00:00', '2025-02-14 00:00:00');
INSERT INTO public.quotation_details VALUES (127, 27, '白下都市工业园项目', 'PNR2000', '频率范围：400-470MHz    锂电池 3700mAh', '和源通信', '套', 1, 1, 1333, 1333, 66650, 'HYTD4MA', '2025-01-10 00:00:00', '2025-01-10 00:00:00');
INSERT INTO public.quotation_details VALUES (128, 27, '白下都市工业园项目', 'NFX_GATW', '用于本地系统设备管理和服务器的同步 -本地系统建立和配置 -设备驱动管理 -设备参数设置 -云同步 -设备报警管理', '和源通信', '套', 1, 1, 12500, 12500, 12500, 'HYWG0NB1', '2025-01-10 00:00:00', '2025-01-10 00:00:00');
INSERT INTO public.quotation_details VALUES (129, 27, '白下都市工业园项目', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 1, 1, 142, 142, 3692, 'HYCDN24Y', '2025-01-10 00:00:00', '2025-01-10 00:00:00');
INSERT INTO public.quotation_details VALUES (130, 27, '白下都市工业园项目', 'BTN10', '标准iBeacon协议    电池续航3年    专用对讲机广播报文    许可证：蓝牙定位入网许可', '和源通信', '套', 1, 1, 110, 110, 5500, 'HYBIOCBNY', '2025-01-10 00:00:00', '2025-01-10 00:00:00');
INSERT INTO public.quotation_details VALUES (131, 27, '白下都市工业园项目', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '套', 1, 1, 142, 142, 24992, 'HYAIOCN4Y', '2025-01-10 00:00:00', '2025-01-10 00:00:00');
INSERT INTO public.quotation_details VALUES (132, 27, '白下都市工业园项目', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 1, 1, 458, 458, 458, 'EANLOMO5HR1', '2025-01-10 00:00:00', '2025-01-10 00:00:00');
INSERT INTO public.quotation_details VALUES (133, 27, '白下都市工业园项目', 'MONT80', '曲臂长度50cm 材料：不锈钢 结构类型：L型结构', '国产', '套', 1, 1, 151, 151, 151, 'OBJANOTGR01', '2025-01-10 00:00:00', '2025-01-10 00:00:00');
INSERT INTO public.quotation_details VALUES (134, 27, '白下都市工业园项目', 'CA-23RS', '频率范围：0-1000MHz 功率：700W 阻抗：50Ω 接口（可选）：N', '钻石', '套', 1, 1, 134, 134, 134, 'OBJANOTHS01', '2025-01-10 00:00:00', '2025-01-10 00:00:00');
INSERT INTO public.quotation_details VALUES (135, 27, '白下都市工业园项目', 'HCAAYZ -50-12', '尺寸：1/2＂    特性1：低烟无卤    特性2：阻燃    阻抗：50Ω', '浙江联创', '米', 1, 1, 13, 13, 114400, 'OZCH221035', '2025-01-10 00:00:00', '2025-01-10 00:00:00');
INSERT INTO public.quotation_details VALUES (136, 27, '白下都市工业园项目', 'N-J1/2', '尺寸：1/2＂    接口：N-J     外径：15.7mm    用途：同轴电缆连接器', '国产', '只', 1, 1, 16, 16, 12800, 'OCIN5JZALC1', '2025-01-10 00:00:00', '2025-01-10 00:00:00');
INSERT INTO public.quotation_details VALUES (137, 27, '白下都市工业园项目', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4569, 4569, 4569, 'EDE1AU6xCZ1', '2025-01-10 00:00:00', '2025-01-10 00:00:00');
INSERT INTO public.quotation_details VALUES (138, 27, '白下都市工业园项目', 'NFX-PAT-OPETN', '支持携带对讲机完成在线的路线巡检记录及任务编排', '和源通信', '套', 1, 1, 22000, 22000, 22000, 'HYWACHA1', '2025-01-10 00:00:00', '2025-01-10 00:00:00');
INSERT INTO public.quotation_details VALUES (139, 27, '白下都市工业园项目', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4570, 4570, 4570, 'EDE1AD6xCZ1', '2025-01-10 00:00:00', '2025-01-10 00:00:00');
INSERT INTO public.quotation_details VALUES (140, 27, '白下都市工业园项目', 'RFS-400 LT/M', '频率范围：350-50MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 1, 1, 9876, 9876, 19752, 'HYR2SI030', '2025-01-10 00:00:00', '2025-01-10 00:00:00');
INSERT INTO public.quotation_details VALUES (141, 27, '白下都市工业园项目', 'RFT-BDA400B LT/M', '频率范围：403-405/413-415MHz 带宽：≤4M 输出：2W  功能： 网讯平台', '和源通信', '套', 1, 1, 11852, 11852, 94816, 'HYR3SI14A', '2025-01-10 00:00:00', '2025-01-10 00:00:00');
INSERT INTO public.quotation_details VALUES (142, 27, '白下都市工业园项目', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 1, 1, 142, 142, 21016, 'HYCCN34Y', '2025-01-10 00:00:00', '2025-01-10 00:00:00');
INSERT INTO public.quotation_details VALUES (143, 27, '白下都市工业园项目', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 1, 1, 4569, 4569, 4569, 'ECM1B022CZ1', '2025-01-10 00:00:00', '2025-01-10 00:00:00');
INSERT INTO public.quotation_details VALUES (144, 27, '白下都市工业园项目', 'LS-NFX-RPT', '网讯平台信道机接入管理服务许可 -信道资源管理 -呼叫类型繁忙度分析', '和源通信', '套', 1, 1, 2501, 2501, 5002, 'HYWSPNB1', '2025-01-10 00:00:00', '2025-01-10 00:00:00');
INSERT INTO public.quotation_details VALUES (145, 27, '白下都市工业园项目', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 1, 1, 2321, 2321, 2321, 'EDE1BU2xCZ1', '2025-01-10 00:00:00', '2025-01-10 00:00:00');
INSERT INTO public.quotation_details VALUES (146, 27, '白下都市工业园项目', 'LS-NFX-RAD', '网讯平台终端对讲机接入管理服务许可-对讲机ID呼叫管理-对讲机上下线管理-呼叫组繁忙度分析', '和源通信', '套', 1, 1, 181, 181, 9050, 'HYWSTNB1', '2025-01-10 00:00:00', '2025-01-10 00:00:00');
INSERT INTO public.quotation_details VALUES (147, 27, '白下都市工业园项目', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 1, 1, 3753, 3753, 3753, 'EDULN4N1CZ1', '2025-01-10 00:00:00', '2025-01-10 00:00:00');
INSERT INTO public.quotation_details VALUES (148, 27, '白下都市工业园项目', 'ACC-CWT', '提供某一个项目上所有系统的工作管理    直观全面的反映系统的整体面貌和其中设备的布局    并可以跟踪每个设备及服务的进程。-告警处置模块-告警详情模块-维修情况和完成情况-设备位置地图模块    含一年的在线后台服', '和源通信', '个/年', 1, 1, 8334, 8334, 8334, 'HYWF0NA1', '2025-01-10 00:00:00', '2025-01-10 00:00:00');
INSERT INTO public.quotation_details VALUES (149, 27, '白下都市工业园项目', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W-网讯平台-数模兼容', '和源通信', '套', 1, 1, 13580, 13580, 27160, 'HYPSMXI40', '2025-01-10 00:00:00', '2025-01-10 00:00:00');
INSERT INTO public.quotation_details VALUES (150, 27, '白下都市工业园项目', 'LS-NFX-BDA', '网讯云端终端直放站接入管理服务许可-远端站告警-远端区域状态更新', '和源通信', '套', 1, 1, 1501, 1501, 12008, 'HYWSRNB1', '2025-01-10 00:00:00', '2025-01-10 00:00:00');
INSERT INTO public.quotation_details VALUES (151, 28, '苏州工业园区20200118地块智能化项目', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 0.4, 142, 142, 24424, 'HYCCN34Y', '2025-01-02 00:00:00', '2025-01-04 00:00:00');
INSERT INTO public.quotation_details VALUES (152, 28, '苏州工业园区20200118地块智能化项目', 'E-BDA400B LT', '频率范围：410~414/420~424 , 链路带宽 4MHz, 最大射频输出功率 33dBm(2W)', '和源通信', '', 1, 0.4, 8396, 8396, 100752, 'HYR1SN140', '2025-01-02 00:00:00', '2025-01-04 00:00:00');
INSERT INTO public.quotation_details VALUES (153, 28, '苏州工业园区20200118地块智能化项目', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '', 1, 0.4, 3753, 3753, 3753, 'EDULN4N1CZ1', '2025-01-02 00:00:00', '2025-01-04 00:00:00');
INSERT INTO public.quotation_details VALUES (154, 28, '苏州工业园区20200118地块智能化项目', 'E-JF350/400-4', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤7.5dB 接入端口数量：4 安装方式：机柜式 尺寸1U', '和源通信', '', 1, 0.4, 2493, 2493, 2493, 'EDE1BU4xCZ1', '2025-01-02 00:00:00', '2025-01-04 00:00:00');
INSERT INTO public.quotation_details VALUES (155, 28, '苏州工业园区20200118地块智能化项目', 'E-FH400-4', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤8.5dB 接入端口数量：4 安装方式：机柜式 尺寸2U', '和源通信', '', 1, 0.4, 6642, 6642, 6642, 'ECM1B042CZ1', '2025-01-02 00:00:00', '2025-01-04 00:00:00');
INSERT INTO public.quotation_details VALUES (156, 28, '苏州工业园区20200118地块智能化项目', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '', 1, 0.4, 142, 142, 25844, 'HYAIOCN4Y', '2025-01-02 00:00:00', '2025-01-04 00:00:00');
INSERT INTO public.quotation_details VALUES (157, 28, '苏州工业园区20200118地块智能化项目', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 0.4, 142, 142, 142, 'HYCDN24Y', '2025-01-02 00:00:00', '2025-01-04 00:00:00');
INSERT INTO public.quotation_details VALUES (158, 29, '天津中芯国际-改造项目', 'LS-NFX-RAD', '网讯平台终端对讲机接入管理服务许可-对讲机ID呼叫管理-对讲机上下线管理-呼叫组繁忙度分析', '和源通信', '套', 1, 1, 180, 180, 3600, 'HYWSTNB1', '2024-12-28 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (159, 29, '天津中芯国际-改造项目', 'NFX-PAT-OPETN', '支持携带对讲机完成在线的路线巡检记录及任务编排', '和源通信', '套', 1, 1, 22000, 22000, 22000, 'HYWACHA1', '2024-12-28 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (160, 29, '天津中芯国际-改造项目', 'NFX-LCN-OPETN', '支持对讲机在地图上人员的动态分布和查询功能', '和源通信', '套', 1, 1, 14600, 14600, 14600, 'HYWADHA1', '2024-12-28 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (161, 29, '天津中芯国际-改造项目', 'NFX_GATW', '用于本地系统设备管理和服务器的同步 -本地系统建立和配置 -设备驱动管理 -设备参数设置 -云同步 -设备报警管理', '和源通信', '套', 1, 1, 12500, 12500, 12500, 'HYWG0NB1', '2024-12-28 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (162, 29, '天津中芯国际-改造项目', 'ACC-CWT', '提供某一个项目上所有系统的工作管理    直观全面的反映系统的整体面貌和其中设备的布局    并可以跟踪每个设备及服务的进程。-告警处置模块-告警详情模块-维修情况和完成情况-设备位置地图模块    含一年的在线后台服', '和源通信', '个/年', 1, 1, 8333, 8333, 8333, 'HYWF0NA1', '2024-12-28 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (163, 29, '天津中芯国际-改造项目', 'LS-NFX-RPT', '网讯平台信道机接入管理服务许可 -信道资源管理 -呼叫类型繁忙度分析', '和源通信', '套', 1, 1, 2500, 2500, 5000, 'HYWSPNB1', '2024-12-28 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (164, 29, '天津中芯国际-改造项目', 'NFX_MAST_OPETN', '-账户创建和访问管理-设备数据和系统数据的存储和恢复-产品库数据-系统拓扑和设备位置显示和管理-系统资源统计和告警分析推送-系统工作台主次账号一个-20个远端站授权    4个信道机授权    100个终端授权', '和源通信', '套', 1, 1, 105000, 105000, 105000, 'HYWP0NC1', '2024-12-28 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (165, 29, '天津中芯国际-改造项目', 'LS-NFX-BDA', '网讯云端终端直放站接入管理服务许可-远端站告警-远端区域状态更新', '和源通信', '套', 1, 1, 1500, 1500, 10500, 'HYWSRNB1', '2024-12-28 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (166, 29, '天津中芯国际-改造项目', 'PNR2000', '频率范围：400-470MHz    锂电池 3700mAh', '和源通信', '套', 1, 1, 1333, 1333, 26660, 'HYTD4MA', '2024-12-28 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (167, 29, '天津中芯国际-改造项目', 'RFS-400 LT/M', '频率范围：350-50MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 1, 1, 9876, 9876, 19752, 'HYR2SI030', '2024-12-28 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (168, 29, '天津中芯国际-改造项目', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 1U机箱 功能： 网讯平台', '和源通信', '套', 1, 1, 11851, 11851, 82957, 'HYR3SI140', '2024-12-28 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (169, 29, '天津中芯国际-改造项目', 'FDPower400', '馈电功能模组    需搭配可扩展远端机;内置远端内向天馈提供电力;', '和源通信', '套', 1, 1, 1583, 1583, 11081, 'HYGF20000', '2024-12-28 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (170, 29, '天津中芯国际-改造项目', 'BTN10', '标准iBeacon协议    电池续航3年    专用对讲机广播报文    许可证：蓝牙定位入网许可', '和源通信', '套', 1, 1, 110, 110, 12870, 'HYBIOCBNY', '2024-12-28 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (171, 29, '天津中芯国际-改造项目', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W-网讯平台-数模兼容', '和源通信', '套', 1, 1, 13580, 13580, 27160, 'HYPSMXI40', '2024-12-28 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (172, 30, '桑田科学岛科创中心项目东片区实验室项目（实验楼、地库及能源中心）', 'LS-NFX-BDA', '网讯云端终端直放站接入管理服务许可-远端站告警-远端区域状态更新', '和源通信', '套', 1, 1, 1500, 1500, 1500, 'HYWSRNB1', '2024-12-26 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (173, 30, '桑田科学岛科创中心项目东片区实验室项目（实验楼、地库及能源中心）', 'LS-NFX-RAD', '网讯平台终端对讲机接入管理服务许可-对讲机ID呼叫管理-对讲机上下线管理-呼叫组繁忙度分析', '和源通信', '套', 1, 1, 180, 180, 18900, 'HYWSTNB1', '2024-12-26 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (174, 30, '桑田科学岛科创中心项目东片区实验室项目（实验楼、地库及能源中心）', 'NFX-PAT-OPETN', '支持携带对讲机完成在线的路线巡检记录及任务编排', '和源通信', '套', 1, 1, 22000, 22000, 22000, 'HYWACHA1', '2024-12-26 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (175, 30, '桑田科学岛科创中心项目东片区实验室项目（实验楼、地库及能源中心）', 'NFX_MAST_OPETN', '-账户创建和访问管理-设备数据和系统数据的存储和恢复-产品库数据-系统拓扑和设备位置显示和管理-系统资源统计和告警分析推送-系统工作台主次账号一个-20个远端站授权    4个信道机授权    100个终端授权', '和源通信', '套', 1, 1, 105000, 105000, 105000, 'HYWP0NC1', '2024-12-26 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (176, 30, '桑田科学岛科创中心项目东片区实验室项目（实验楼、地库及能源中心）', 'NFX_GATW', '用于本地系统设备管理和服务器的同步 -本地系统建立和配置 -设备驱动管理 -设备参数设置 -云同步 -设备报警管理', '和源通信', '套', 1, 1, 12500, 12500, 12500, 'HYWG0NB1', '2024-12-26 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (177, 30, '桑田科学岛科创中心项目东片区实验室项目（实验楼、地库及能源中心）', 'ACC-CWT', '提供某一个项目上所有系统的工作管理    直观全面的反映系统的整体面貌和其中设备的布局    并可以跟踪每个设备及服务的进程。-告警处置模块-告警详情模块-维修情况和完成情况-设备位置地图模块    含一年的在线后台服', '和源通信', '个/年', 1, 1, 8333, 8333, 8333, 'HYWF0NA1', '2024-12-26 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (178, 30, '桑田科学岛科创中心项目东片区实验室项目（实验楼、地库及能源中心）', 'LS-NFX-RPT', '网讯平台信道机接入管理服务许可 -信道资源管理 -呼叫类型繁忙度分析', '和源通信', '套', 1, 1, 2500, 2500, 10000, 'HYWSPNB1', '2024-12-26 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (179, 30, '桑田科学岛科创中心项目东片区实验室项目（实验楼、地库及能源中心）', 'NJ/NJ-3 1.5米', '接口：NJ转NJ    长度：1.5米    用途：机柜内跳线', '国产', '根', 1, 1, 40, 40, 960, 'EJUMJK4315NJNJ', '2024-12-26 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (180, 30, '桑田科学岛科创中心项目东片区实验室项目（实验楼、地库及能源中心）', 'HCAAYZ -50-12', '尺寸：1/2＂    特性1：低烟无卤    特性2：阻燃    阻抗：50Ω', '浙江联创', '米', 1, 1, 13, 13, 227500, 'OZCH221035', '2024-12-26 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (181, 30, '桑田科学岛科创中心项目东片区实验室项目（实验楼、地库及能源中心）', 'N-J1/2', '尺寸：1/2＂    接口：N-J     外径：15.7mm    用途：同轴电缆连接器', '国产', '只', 1, 1, 16, 16, 41760, 'OCIN5JZALC1', '2024-12-26 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (182, 30, '桑田科学岛科创中心项目东片区实验室项目（实验楼、地库及能源中心）', 'BTN10', '标准iBeacon协议    电池续航3年    专用对讲机广播报文    许可证：蓝牙定位入网许可', '和源通信', '套', 1, 1, 110, 110, 58190, 'HYBIOCBNY', '2024-12-26 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (183, 30, '桑田科学岛科创中心项目东片区实验室项目（实验楼、地库及能源中心）', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '套', 1, 1, 142, 142, 72846, 'HYAIOCN4Y', '2024-12-26 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (184, 30, '桑田科学岛科创中心项目东片区实验室项目（实验楼、地库及能源中心）', 'E-ANTD 400', '频率范围：400-430MHz 增益：2.5dBi 防护等级：IP65 辐射方向：定向 最大承载功率：50W 接头类型：N-Femade 特性：室外', '和源通信', '套', 1, 1, 354, 354, 25134, 'EAN2OFD2TE2', '2024-12-26 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (185, 30, '桑田科学岛科创中心项目东片区实验室项目（实验楼、地库及能源中心）', 'MONT80', '曲臂长度50cm 材料：不锈钢 结构类型：L型结构', '国产', '套', 1, 1, 151, 151, 151, 'OBJANOTGR01', '2024-12-26 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (186, 30, '桑田科学岛科创中心项目东片区实验室项目（实验楼、地库及能源中心）', 'CA-23RS', '频率范围：0-1000MHz 功率：700W 阻抗：50Ω 接口（可选）：N', '钻石', '套', 1, 1, 134, 134, 134, 'OBJANOTHS01', '2024-12-26 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (187, 30, '桑田科学岛科创中心项目东片区实验室项目（实验楼、地库及能源中心）', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 1, 1, 458, 458, 458, 'EANLOMO5HR1', '2024-12-26 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (188, 30, '桑田科学岛科创中心项目东片区实验室项目（实验楼、地库及能源中心）', 'E-SGQ400D', '频率范围：410-414/420-424MHz 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 隔离方式：带通 工作带宽：4M 安装方式：机柜式 尺寸：2U', '和源通信', '套', 1, 1, 7876, 7876, 7876, 'EDULB4H1CZ1', '2024-12-26 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (189, 30, '桑田科学岛科创中心项目东片区实验室项目（实验楼、地库及能源中心）', 'RFS-400 LT/M', '频率范围：350-50MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 1, 1, 9876, 9876, 345660, 'HYR2SI030', '2024-12-26 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (190, 30, '桑田科学岛科创中心项目东片区实验室项目（实验楼、地库及能源中心）', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 1U机箱 功能： 网讯平台', '和源通信', '套', 1, 1, 11851, 11851, 367381, 'HYR3SI140', '2024-12-26 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (191, 30, '桑田科学岛科创中心项目东片区实验室项目（实验楼、地库及能源中心）', 'EVDC-6 LT', '频率范围：150-170MHz    承载功率：100W;耦合规格：6dB', '和源通信', '套', 1, 1, 184, 184, 107456, 'HYCCN31Y', '2024-12-26 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (192, 30, '桑田科学岛科创中心项目东片区实验室项目（实验楼、地库及能源中心）', 'PNR2000', '频率范围：400-470MHz    锂电池 3700mAh', '和源通信', '套', 1, 1, 1333, 1333, 6665, 'HYTD4MA', '2024-12-26 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (222, 32, '中原高铁港数字展贸城', 'LS-NFX-RAD', '网讯平台终端对讲机接入管理服务许可-对讲机ID呼叫管理-对讲机上下线管理-呼叫组繁忙度分析', '和源通信', '套', 1, 1, 180, 180, 10800, 'HYWSTNB1', '2024-12-21 00:00:00', '2024-12-21 00:00:00');
INSERT INTO public.quotation_details VALUES (193, 30, '桑田科学岛科创中心项目东片区实验室项目（实验楼、地库及能源中心）', 'E-FH400-4', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤8.5dB 接入端口数量：4 安装方式：机柜式 尺寸2U', '和源通信', '套', 1, 1, 6642, 6642, 6642, 'ECM1B042CZ1', '2024-12-26 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (194, 30, '桑田科学岛科创中心项目东片区实验室项目（实验楼、地库及能源中心）', 'E-JF350/400-4', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤7.5dB 接入端口数量：4 安装方式：机柜式 尺寸1U', '和源通信', '套', 1, 1, 2494, 2494, 2494, 'EDE1BU4xCZ1', '2024-12-26 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (195, 30, '桑田科学岛科创中心项目东片区实验室项目（实验楼、地库及能源中心）', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4569, 4569, 82242, 'EDE1AU6xCZ1', '2024-12-26 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (196, 30, '桑田科学岛科创中心项目东片区实验室项目（实验楼、地库及能源中心）', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4570, 4570, 82260, 'EDE1AD6xCZ1', '2024-12-26 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (197, 30, '桑田科学岛科创中心项目东片区实验室项目（实验楼、地库及能源中心）', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W-网讯平台-数模兼容', '和源通信', '套', 1, 1, 13580, 13580, 54320, 'HYPSMXI40', '2024-12-26 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (198, 30, '桑田科学岛科创中心项目东片区实验室项目（实验楼、地库及能源中心）', 'LS-VTT-RPT', '授权信道机在注册虚拟集群功能许可', '和源通信', '个', 1, 1, 3000, 3000, 12000, 'WCF9PH', '2024-12-26 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (199, 30, '桑田科学岛科创中心项目东片区实验室项目（实验楼、地库及能源中心）', 'PNR2100', '频率范围：400-470MHz/ 4G     功率：1-2W    3800mAH锂电池    蓝牙 5.0 定位    电池管理', '和源通信', '套', 1, 1, 2750, 2750, 275000, 'HYTX0NA', '2024-12-26 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (200, 31, 'MY07 Dragonfly 总包项目', 'N-50KK', '类型：N型    特性：双通    用途：连接器', '国产', '只', 1, 1, 15, 15, 450, 'OCIN5KZALC1', '2024-12-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (201, 31, 'MY07 Dragonfly 总包项目', 'E-JP50-7', '长度：0.5米 接口：NJ转NJ 用途：天线连接跳线', '国产', '根', 1, 1, 35, 35, 700, 'OISKHB1JLC1', '2024-12-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (202, 31, 'MY07 Dragonfly 总包项目', 'NJ-3/NJ-3-1.5M', '接口：NJ转NJ    长度：1.5米    特性1：超柔    特性2：SYV-50-3', '国产', '根', 1, 1, 100, 100, 2400, 'W000188', '2024-12-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (203, 31, 'MY07 Dragonfly 总包项目', 'PNR2000', '频率范围：400-470MHz    锂电池 3700mAh', '和源通信', '套', 1, 1, 1333, 1333, 39990, 'HYTD4MA', '2024-12-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (204, 31, 'MY07 Dragonfly 总包项目', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 1, 1, 3753, 3753, 7506, 'EDULN4N1CZ1', '2024-12-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (205, 31, 'MY07 Dragonfly 总包项目', 'CA-23RS', '频率范围：0-1000MHz 功率：700W 阻抗：50Ω 接口（可选）：N', '钻石', '套', 1, 1, 133, 133, 532, 'OBJANOTHS01', '2024-12-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (206, 31, 'MY07 Dragonfly 总包项目', 'MONT80', '曲臂长度50cm 材料：不锈钢 结构类型：L型结构', '国产', '套', 1, 1, 150, 150, 600, 'OBJANOTGR01', '2024-12-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (207, 31, 'MY07 Dragonfly 总包项目', 'HCAAYZ -50-12', '尺寸：1/2＂    特性1：低烟无卤    特性2：阻燃    阻抗：50Ω', '浙江联创', '米', 1, 1, 13, 13, 67600, 'OZCH221035', '2024-12-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (208, 31, 'MY07 Dragonfly 总包项目', 'N-J1/2', '尺寸：1/2＂    接口：N-J     外径：15.7mm    用途：同轴电缆连接器', '国产', '只', 1, 1, 15, 15, 11400, 'OCIN5JZALC1', '2024-12-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (209, 31, 'MY07 Dragonfly 总包项目', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 1U机箱 功能： 网讯平台', '和源通信', '套', 1, 1, 11851, 11851, 118510, 'HYR3SI140', '2024-12-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (210, 31, 'MY07 Dragonfly 总包项目', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '套', 1, 1, 142, 142, 23572, 'HYAIOCN4Y', '2024-12-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (211, 31, 'MY07 Dragonfly 总包项目', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 1, 1, 142, 142, 26980, 'HYCCN34Y', '2024-12-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (212, 31, 'MY07 Dragonfly 总包项目', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 1, 1, 142, 142, 284, 'HYCDN24Y', '2024-12-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (213, 31, 'MY07 Dragonfly 总包项目', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 1, 1, 458, 458, 1832, 'EANLOMO5HR1', '2024-12-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (214, 31, 'MY07 Dragonfly 总包项目', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W-网讯平台-数模兼容', '和源通信', '套', 1, 1, 13580, 13580, 135800, 'HYPSMXI40', '2024-12-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (215, 31, 'MY07 Dragonfly 总包项目', 'E-FH400-6', '频率范围：400-430MHz 单端口承载功率：50W;插入损耗：≤11dB;接入端口数量：6;安装方式：机柜式;尺寸：2U', '和源通信', '套', 1, 1, 10760, 10760, 21520, 'ECM1B062CZ1', '2024-12-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (216, 31, 'MY07 Dragonfly 总包项目', 'E-JF350/400-6', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤9.5dB 接入端口数量：6 安装方式：机柜式 尺寸1U', '和源通信', '套', 1, 1, 3580, 3580, 7160, 'EDE1BU6xCZ1', '2024-12-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (217, 31, 'MY07 Dragonfly 总包项目', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4569, 4569, 9138, 'EDE1AU6xCZ1', '2024-12-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (218, 31, 'MY07 Dragonfly 总包项目', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4569, 4569, 9138, 'EDE1AD6xCZ1', '2024-12-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (219, 31, 'MY07 Dragonfly 总包项目', 'RFS-400 LT/M', '频率范围：350-50MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 1, 1, 9876, 9876, 39504, 'HYR2SI030', '2024-12-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (220, 32, '中原高铁港数字展贸城', 'LS-NFX-RPT', '网讯平台信道机接入管理服务许可 -信道资源管理 -呼叫类型繁忙度分析', '和源通信', '套', 1, 1, 2500, 2500, 5000, 'HYWSPNB1', '2024-12-21 00:00:00', '2024-12-21 00:00:00');
INSERT INTO public.quotation_details VALUES (221, 32, '中原高铁港数字展贸城', 'LS-NFX-BDA', '网讯云端终端直放站接入管理服务许可-远端站告警-远端区域状态更新', '和源通信', '套', 1, 1, 1500, 1500, 15000, 'HYWSRNB1', '2024-12-21 00:00:00', '2024-12-21 00:00:00');
INSERT INTO public.quotation_details VALUES (223, 32, '中原高铁港数字展贸城', 'NJ-3/NJ-3-1.5M', '接口：NJ转NJ    长度：1.5米    特性1：超柔    特性2：SYV-50-3', '国产', '根', 1, 1, 100, 100, 600, 'W000188', '2024-12-21 00:00:00', '2024-12-21 00:00:00');
INSERT INTO public.quotation_details VALUES (224, 32, '中原高铁港数字展贸城', 'PNR2000', '频率范围：400-470MHz    锂电池 3700mAh', '和源通信', '套', 1, 1, 1333, 1333, 79980, 'HYTD4MA', '2024-12-21 00:00:00', '2024-12-21 00:00:00');
INSERT INTO public.quotation_details VALUES (225, 32, '中原高铁港数字展贸城', 'NFX_GATW', '用于本地系统设备管理和服务器的同步 -本地系统建立和配置 -设备驱动管理 -设备参数设置 -云同步 -设备报警管理', '和源通信', '套', 1, 1, 12500, 12500, 12500, 'HYWG0NB1', '2024-12-21 00:00:00', '2024-12-21 00:00:00');
INSERT INTO public.quotation_details VALUES (226, 32, '中原高铁港数字展贸城', 'ACC-CWT', '提供某一个项目上所有系统的工作管理    直观全面的反映系统的整体面貌和其中设备的布局    并可以跟踪每个设备及服务的进程。-告警处置模块-告警详情模块-维修情况和完成情况-设备位置地图模块    含一年的在线后台服', '和源通信', '个/年', 1, 1, 8333, 8333, 8333, 'HYWF0NA1', '2024-12-21 00:00:00', '2024-12-21 00:00:00');
INSERT INTO public.quotation_details VALUES (227, 32, '中原高铁港数字展贸城', 'HCAAYZ -50-12', '尺寸：1/2＂    特性1：低烟无卤    特性2：阻燃    阻抗：50Ω', '浙江联创', '米', 1, 1, 13, 13, 132600, 'OZCH221035', '2024-12-21 00:00:00', '2024-12-21 00:00:00');
INSERT INTO public.quotation_details VALUES (228, 32, '中原高铁港数字展贸城', 'N-J1/2', '尺寸：1/2＂    接口：N-J     外径：15.7mm    用途：同轴电缆连接器', '国产', '只', 1, 1, 15, 15, 9150, 'OCIN5JZALC1', '2024-12-21 00:00:00', '2024-12-21 00:00:00');
INSERT INTO public.quotation_details VALUES (229, 32, '中原高铁港数字展贸城', 'N-50KK', '类型：N型    特性：双通    用途：连接器', '国产', '只', 1, 1, 15, 15, 900, 'OCIN5KZALC1', '2024-12-21 00:00:00', '2024-12-21 00:00:00');
INSERT INTO public.quotation_details VALUES (230, 32, '中原高铁港数字展贸城', 'E-JP50-7', '长度：0.5米 接口：NJ转NJ 用途：天线连接跳线', '国产', '根', 1, 1, 35, 35, 700, 'OISKHB1JLC1', '2024-12-21 00:00:00', '2024-12-21 00:00:00');
INSERT INTO public.quotation_details VALUES (231, 32, '中原高铁港数字展贸城', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 1, 1, 142, 142, 284, 'HYCDN24Y', '2024-12-21 00:00:00', '2024-12-21 00:00:00');
INSERT INTO public.quotation_details VALUES (232, 32, '中原高铁港数字展贸城', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 1, 1, 458, 458, 458, 'EANLOMO5HR1', '2024-12-21 00:00:00', '2024-12-21 00:00:00');
INSERT INTO public.quotation_details VALUES (233, 32, '中原高铁港数字展贸城', 'CA-23RS', '频率范围：0-1000MHz 功率：700W 阻抗：50Ω 接口（可选）：N', '钻石', '套', 1, 1, 133, 133, 133, 'OBJANOTHS01', '2024-12-21 00:00:00', '2024-12-21 00:00:00');
INSERT INTO public.quotation_details VALUES (234, 32, '中原高铁港数字展贸城', 'MONT80', '曲臂长度50cm 材料：不锈钢 结构类型：L型结构', '国产', '套', 1, 1, 150, 150, 150, 'OBJANOTGR01', '2024-12-21 00:00:00', '2024-12-21 00:00:00');
INSERT INTO public.quotation_details VALUES (235, 32, '中原高铁港数字展贸城', 'RFS-400 LT/M', '频率范围：350-50MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 1, 1, 9876, 9876, 59256, 'HYR2SI030', '2024-12-21 00:00:00', '2024-12-21 00:00:00');
INSERT INTO public.quotation_details VALUES (236, 32, '中原高铁港数字展贸城', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 1U机箱 功能： 网讯平台', '和源通信', '套', 1, 1, 11851, 11851, 284424, 'HYR3SI140', '2024-12-21 00:00:00', '2024-12-21 00:00:00');
INSERT INTO public.quotation_details VALUES (237, 32, '中原高铁港数字展贸城', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '套', 1, 1, 142, 142, 28542, 'HYAIOCN4Y', '2024-12-21 00:00:00', '2024-12-21 00:00:00');
INSERT INTO public.quotation_details VALUES (238, 32, '中原高铁港数字展贸城', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 1, 1, 142, 142, 28116, 'HYCCN34Y', '2024-12-21 00:00:00', '2024-12-21 00:00:00');
INSERT INTO public.quotation_details VALUES (239, 32, '中原高铁港数字展贸城', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 1, 1, 4569, 4569, 4569, 'ECM1B022CZ1', '2024-12-21 00:00:00', '2024-12-21 00:00:00');
INSERT INTO public.quotation_details VALUES (240, 32, '中原高铁港数字展贸城', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 1, 1, 2320, 2320, 2320, 'EDE1BU2xCZ1', '2024-12-21 00:00:00', '2024-12-21 00:00:00');
INSERT INTO public.quotation_details VALUES (241, 32, '中原高铁港数字展贸城', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4569, 4569, 4569, 'EDE1AU6xCZ1', '2024-12-21 00:00:00', '2024-12-21 00:00:00');
INSERT INTO public.quotation_details VALUES (242, 32, '中原高铁港数字展贸城', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4569, 4569, 4569, 'EDE1AD6xCZ1', '2024-12-21 00:00:00', '2024-12-21 00:00:00');
INSERT INTO public.quotation_details VALUES (243, 32, '中原高铁港数字展贸城', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W-网讯平台-数模兼容', '和源通信', '套', 1, 1, 13580, 13580, 27160, 'HYPSMXI40', '2024-12-21 00:00:00', '2024-12-21 00:00:00');
INSERT INTO public.quotation_details VALUES (244, 33, '南京江北新金融中心一期项目DFG地块弱电智能化工程', 'N-50JKW', '类型：N型    特性：直角弯    用途：连接器', '国产', '只', 1, 1, 16, 16, 4160, 'OCIN5JWALC1', '2024-12-07 00:00:00', '2025-02-14 00:00:00');
INSERT INTO public.quotation_details VALUES (245, 33, '南京江北新金融中心一期项目DFG地块弱电智能化工程', 'E-JP50-7', '长度：0.5米 接口：NJ转NJ 用途：天线连接跳线', '国产', '根', 1, 1, 35, 35, 1890, 'OISKHB1JLC1', '2024-12-07 00:00:00', '2025-02-14 00:00:00');
INSERT INTO public.quotation_details VALUES (246, 33, '南京江北新金融中心一期项目DFG地块弱电智能化工程', 'PNR2000', '频率范围：400-470MHz    锂电池 3700mAh', '和源通信', '套', 1, 1, 1333, 1333, 159960, 'HYTD4MA', '2024-12-07 00:00:00', '2025-02-14 00:00:00');
INSERT INTO public.quotation_details VALUES (247, 33, '南京江北新金融中心一期项目DFG地块弱电智能化工程', 'N-J1/2', '尺寸：1/2＂    接口：N-J     外径：15.7mm    用途：同轴电缆连接器', '国产', '只', 1, 1, 16, 16, 13728, 'OCIN5JZALC1', '2024-12-07 00:00:00', '2025-02-14 00:00:00');
INSERT INTO public.quotation_details VALUES (248, 33, '南京江北新金融中心一期项目DFG地块弱电智能化工程', 'N-50KK', '类型：N型    特性：双通    用途：连接器', '国产', '只', 1, 1, 16, 16, 4160, 'OCIN5KZALC1', '2024-12-07 00:00:00', '2025-02-14 00:00:00');
INSERT INTO public.quotation_details VALUES (249, 33, '南京江北新金融中心一期项目DFG地块弱电智能化工程', 'MONT80', '曲臂长度50cm 材料：不锈钢 结构类型：L型结构', '国产', '套', 1, 1, 151, 151, 906, 'OBJANOTGR01', '2024-12-07 00:00:00', '2025-02-14 00:00:00');
INSERT INTO public.quotation_details VALUES (250, 33, '南京江北新金融中心一期项目DFG地块弱电智能化工程', 'CA-23RS', '频率范围：0-1000MHz 功率：700W 阻抗：50Ω 接口（可选）：N', '钻石', '套', 1, 1, 134, 134, 804, 'OBJANOTHS01', '2024-12-07 00:00:00', '2025-02-14 00:00:00');
INSERT INTO public.quotation_details VALUES (251, 33, '南京江北新金融中心一期项目DFG地块弱电智能化工程', 'ST/FC  4口', '尺寸类型：标准尺寸FC口    端口数：4口    产品类型：墙上型    特性：含法兰头    不含配套尾纤', '国产', '套', 1, 1, 163, 163, 2771, 'EDFWYFC04O', '2024-12-07 00:00:00', '2025-02-14 00:00:00');
INSERT INTO public.quotation_details VALUES (252, 33, '南京江北新金融中心一期项目DFG地块弱电智能化工程', 'HCAAYZ -50-12', '尺寸：1/2＂    特性1：低烟无卤    特性2：阻燃    阻抗：50Ω', '浙江联创', '米', 1, 1, 13, 13, 117000, 'OZCH221035', '2024-12-07 00:00:00', '2025-02-14 00:00:00');
INSERT INTO public.quotation_details VALUES (253, 33, '南京江北新金融中心一期项目DFG地块弱电智能化工程', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '套', 1, 1, 142, 142, 37772, 'HYAIOCN4Y', '2024-12-07 00:00:00', '2025-02-14 00:00:00');
INSERT INTO public.quotation_details VALUES (254, 33, '南京江北新金融中心一期项目DFG地块弱电智能化工程', 'EVDC-6 LT', '频率范围：150-170MHz    承载功率：100W;耦合规格：6dB', '和源通信', '套', 1, 1, 184, 184, 47104, 'HYCCN31Y', '2024-12-07 00:00:00', '2025-02-14 00:00:00');
INSERT INTO public.quotation_details VALUES (255, 33, '南京江北新金融中心一期项目DFG地块弱电智能化工程', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 1, 1, 458, 458, 2748, 'EANLOMO5HR1', '2024-12-07 00:00:00', '2025-02-14 00:00:00');
INSERT INTO public.quotation_details VALUES (256, 33, '南京江北新金融中心一期项目DFG地块弱电智能化工程', 'ST/FC  24口', '尺寸类型：标准尺寸FC口    端口数：24口    产品类型：机架式    特性：含法兰头    不含配套尾纤', '国产', '套', 1, 1, 431, 431, 1293, 'EDFWYFC24W', '2024-12-07 00:00:00', '2025-02-14 00:00:00');
INSERT INTO public.quotation_details VALUES (257, 33, '南京江北新金融中心一期项目DFG地块弱电智能化工程', 'DRFS-100/M', '频率范围：150-170MHz 带宽：≤20M 远端携带：32 数字型 功能：触摸屏/网讯平台', '和源通信', '套', 1, 1, 25000, 25000, 75000, 'HYR2DI010', '2024-12-07 00:00:00', '2025-02-14 00:00:00');
INSERT INTO public.quotation_details VALUES (258, 33, '南京江北新金融中心一期项目DFG地块弱电智能化工程', 'DRFT-BDA110/M', '频率范围：157-161/163-167MHz 带宽：≤4M；输出：10W；数字型 功能：触摸屏/网讯平台 扩展：馈电', '和源通信', '套', 1, 1, 51250, 51250, 871250, 'HYR3DI310', '2024-12-07 00:00:00', '2025-02-14 00:00:00');
INSERT INTO public.quotation_details VALUES (259, 33, '南京江北新金融中心一期项目DFG地块弱电智能化工程', 'E-SGQ150D', '频率范围：157.3-160.6/163.0-166.3MHz;单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：5.7M 隔离方式：带通 工作带宽：2M（可调） 安装方式：机柜式;', '和源通信', '套', 1, 1, 7902, 7902, 23706, 'HYMDF2A10', '2024-12-07 00:00:00', '2025-02-14 00:00:00');
INSERT INTO public.quotation_details VALUES (260, 33, '南京江北新金融中心一期项目DFG地块弱电智能化工程', 'R-EVDC-BLST-U', '频率范围：87-170MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4938, 4938, 14814, 'HYMBC6A1U', '2024-12-07 00:00:00', '2025-02-14 00:00:00');
INSERT INTO public.quotation_details VALUES (261, 33, '南京江北新金融中心一期项目DFG地块弱电智能化工程', 'R-EVDC-BLST-D', '频率范围：87-170MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4938, 4938, 14814, 'HYMBC6A1D', '2024-12-07 00:00:00', '2025-02-14 00:00:00');
INSERT INTO public.quotation_details VALUES (262, 33, '南京江北新金融中心一期项目DFG地块弱电智能化工程', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W-网讯平台-数模兼容', '和源通信', '套', 1, 1, 13580, 13580, 81480, 'HYPSMXI40', '2024-12-07 00:00:00', '2025-02-14 00:00:00');
INSERT INTO public.quotation_details VALUES (263, 33, '南京江北新金融中心一期项目DFG地块弱电智能化工程', 'E-FH150-2', '频率范围：163-167MHz 单端口承载功率：50W;插入损耗：≤4.0dB接入端口数量：2;安装方式：机柜式;', '和源通信', '套', 1, 1, 7902, 7902, 23706, 'HYMFC2A10', '2024-12-07 00:00:00', '2025-02-14 00:00:00');
INSERT INTO public.quotation_details VALUES (264, 33, '南京江北新金融中心一期项目DFG地块弱电智能化工程', 'E-JF150-2', '频率范围：130-170MHz 单端口承载功率：1W 插入损耗：≤3.5dB 接入端口数量：2 安装方式：机柜式 尺寸 1U', '和源通信', '套', 1, 1, 2494, 2494, 7482, 'HYMJC2010', '2024-12-07 00:00:00', '2025-02-14 00:00:00');
INSERT INTO public.quotation_details VALUES (265, 34, '北京新首钢园东南区1612-(775-778--769-783-786)地块项目', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '套', 1, 0.43, 142, 142, 83780, 'HYAIOCN4Y', '2024-12-05 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (266, 34, '北京新首钢园东南区1612-(775-778--769-783-786)地块项目', 'PNR2000', '频率范围：400-470MHz，锂电池 3700mAh', '和源通信', '套', 1, 0.43, 1333, 1333, 119970, 'HYTD4MA', '2024-12-05 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (267, 34, '北京新首钢园东南区1612-(775-778--769-783-786)地块项目', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 1U机箱 功能： 网讯平台', '和源通信', '套', 1, 0.43, 11851, 11851, 367381, 'HYR3SI140', '2024-12-05 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (268, 34, '北京新首钢园东南区1612-(775-778--769-783-786)地块项目', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 1, 0.43, 142, 142, 107778, 'HYCCN34Y', '2024-12-05 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (269, 34, '北京新首钢园东南区1612-(775-778--769-783-786)地块项目', 'E-ANTD 400', '频率范围：400-430MHz 增益：2.5dBi 防护等级：IP65 辐射方向：定向 最大承载功率：50W 接头类型：N-Femade 特性：室外', '和源通信', '套', 1, 0.43, 354, 354, 24426, 'EAN2OFD2TE2', '2024-12-05 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (270, 35, '桑田科学岛科创中心项目东片区实验室项目（行政楼）', 'N-50KK', '类型：N型    特性：双通    用途：连接器', '国产', '只', 1, 1, 15, 15, 4500, 'OCIN5KZALC1', '2024-11-16 00:00:00', '2024-11-16 00:00:00');
INSERT INTO public.quotation_details VALUES (271, 35, '桑田科学岛科创中心项目东片区实验室项目（行政楼）', 'N-50JKW', '类型：N型    特性：直角弯    用途：连接器', '国产', '只', 1, 1, 15, 15, 300, 'OCIN5JWALC1', '2024-11-16 00:00:00', '2024-11-16 00:00:00');
INSERT INTO public.quotation_details VALUES (272, 35, '桑田科学岛科创中心项目东片区实验室项目（行政楼）', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '套', 1, 1, 142, 142, 11076, 'HYAIOCN4Y', '2024-11-16 00:00:00', '2024-11-16 00:00:00');
INSERT INTO public.quotation_details VALUES (273, 35, '桑田科学岛科创中心项目东片区实验室项目（行政楼）', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 1, 1, 142, 142, 10792, 'HYCCN34Y', '2024-11-16 00:00:00', '2024-11-16 00:00:00');
INSERT INTO public.quotation_details VALUES (274, 35, '桑田科学岛科创中心项目东片区实验室项目（行政楼）', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 1, 1, 142, 142, 284, 'HYCDN24Y', '2024-11-16 00:00:00', '2024-11-16 00:00:00');
INSERT INTO public.quotation_details VALUES (275, 35, '桑田科学岛科创中心项目东片区实验室项目（行政楼）', 'HCAAYZ -50-12', '尺寸：1/2＂    特性1：低烟无卤    特性2：阻燃    阻抗：50Ω', '浙江联创', '米', 1, 1, 13, 13, 60840, 'OZCH221035', '2024-11-16 00:00:00', '2024-11-16 00:00:00');
INSERT INTO public.quotation_details VALUES (276, 35, '桑田科学岛科创中心项目东片区实验室项目（行政楼）', 'N-J1/2', '尺寸：1/2＂    接口：N-J     外径：15.7mm    用途：同轴电缆连接器', '国产', '只', 1, 1, 15, 15, 1500, 'OCIN5JZALC1', '2024-11-16 00:00:00', '2024-11-16 00:00:00');
INSERT INTO public.quotation_details VALUES (277, 35, '桑田科学岛科创中心项目东片区实验室项目（行政楼）', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 1U机箱 功能： 网讯平台', '和源通信', '套', 1, 1, 11851, 11851, 94808, 'HYR3SI140', '2024-11-16 00:00:00', '2024-11-16 00:00:00');
INSERT INTO public.quotation_details VALUES (278, 36, '麒麟科创园3-3地块2号楼智能化工程', 'PNR2000', '频率范围：400-470MHz    锂电池 3700mAh', '和源通信', '套', 1, 1, 1333, 1333, 26660, 'HYTD4MA', '2024-11-16 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (279, 36, '麒麟科创园3-3地块2号楼智能化工程', 'GYXTH-4B1 4芯', '芯数：4芯    钢带：铠装    特性：单模    低烟无卤阻燃', '国产', '米', 1, 1, 9, 9, 2700, 'ECAWYGYXTH0401', '2024-11-16 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (280, 36, '麒麟科创园3-3地块2号楼智能化工程', 'HCAAYZ -50-12', '尺寸：1/2＂    特性1：低烟无卤    特性2：阻燃    阻抗：50Ω', '浙江联创', '米', 1, 1, 13, 13, 36400, 'OZCH221035', '2024-11-16 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (281, 36, '麒麟科创园3-3地块2号楼智能化工程', 'N-J1/2', '尺寸：1/2＂    接口：N-J     外径：15.7mm    用途：同轴电缆连接器', '国产', '只', 1, 1, 16, 16, 2240, 'OCIN5JZALC1', '2024-11-16 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (282, 36, '麒麟科创园3-3地块2号楼智能化工程', 'N-50KK', '类型：N型    特性：双通    用途：连接器', '国产', '只', 1, 1, 16, 16, 4000, 'OCIN5KZALC1', '2024-11-16 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (283, 36, '麒麟科创园3-3地块2号楼智能化工程', 'N-50JKW', '类型：N型    特性：直角弯    用途：连接器', '国产', '只', 1, 1, 16, 16, 960, 'OCIN5JWALC1', '2024-11-16 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (284, 36, '麒麟科创园3-3地块2号楼智能化工程', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '套', 1, 1, 142, 142, 9230, 'HYAIOCN4Y', '2024-11-16 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (285, 36, '麒麟科创园3-3地块2号楼智能化工程', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 1, 1, 143, 143, 9009, 'HYCDN24Y', '2024-11-16 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (286, 36, '麒麟科创园3-3地块2号楼智能化工程', 'EVDC-6 LT', '频率范围：150-170MHz    承载功率：100W;耦合规格：6dB', '和源通信', '套', 1, 1, 185, 185, 370, 'HYCCN31Y', '2024-11-16 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (287, 36, '麒麟科创园3-3地块2号楼智能化工程', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 1, 1, 458, 458, 458, 'EANLOMO5HR1', '2024-11-16 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (288, 36, '麒麟科创园3-3地块2号楼智能化工程', 'MONT80', '曲臂长度50cm 材料：不锈钢 结构类型：L型结构', '国产', '套', 1, 1, 151, 151, 151, 'OBJANOTGR01', '2024-11-16 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (289, 36, '麒麟科创园3-3地块2号楼智能化工程', 'CA-23RS', '频率范围：0-1000MHz 功率：700W 阻抗：50Ω 接口（可选）：N', '钻石', '套', 1, 1, 134, 134, 134, 'OBJANOTHS01', '2024-11-16 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (290, 36, '麒麟科创园3-3地块2号楼智能化工程', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4570, 4570, 4570, 'EDE1AD6xCZ1', '2024-11-16 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (291, 36, '麒麟科创园3-3地块2号楼智能化工程', 'ST/FC  24口', '尺寸类型：标准尺寸FC口    端口数：24口    产品类型：机架式    特性：含法兰头    不含配套尾纤', '国产', '套', 1, 1, 431, 431, 431, 'EDFWYFC24W', '2024-11-16 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (292, 36, '麒麟科创园3-3地块2号楼智能化工程', 'RFS-400 LT/M', '频率范围：350-50MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 1, 1, 9876, 9876, 9876, 'HYR2SI030', '2024-11-16 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (293, 36, '麒麟科创园3-3地块2号楼智能化工程', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 1U机箱 功能： 网讯平台', '和源通信', '套', 1, 1, 11851, 11851, 47404, 'HYR3SI140', '2024-11-16 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (294, 36, '麒麟科创园3-3地块2号楼智能化工程', 'ST/FC  4口', '尺寸类型：标准尺寸FC口    端口数：4口    产品类型：墙上型    特性：含法兰头    不含配套尾纤', '国产', '套', 1, 1, 164, 164, 656, 'EDFWYFC04O', '2024-11-16 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (295, 36, '麒麟科创园3-3地块2号楼智能化工程', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W-网讯平台-数模兼容', '和源通信', '套', 1, 1, 13580, 13580, 27160, 'HYPSMXI40', '2024-11-16 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (296, 36, '麒麟科创园3-3地块2号楼智能化工程', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 1, 1, 4569, 4569, 4569, 'ECM1B022CZ1', '2024-11-16 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (297, 36, '麒麟科创园3-3地块2号楼智能化工程', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 1, 1, 2321, 2321, 2321, 'EDE1BU2xCZ1', '2024-11-16 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (298, 36, '麒麟科创园3-3地块2号楼智能化工程', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4569, 4569, 4569, 'EDE1AU6xCZ1', '2024-11-16 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (299, 37, '芜湖梦溪科创走廊一期项目', 'EVDC-6 LT', '频率范围：150-170MHz    承载功率：100W;耦合规格：6dB', '和源通信', '套', 1, 1, 185, 185, 2220, 'HYCCN31Y', '2024-11-09 00:00:00', '2024-11-09 00:00:00');
INSERT INTO public.quotation_details VALUES (300, 37, '芜湖梦溪科创走廊一期项目', 'HCAAYZ -50-12', '尺寸：1/2＂    特性1：低烟无卤    特性2：阻燃    阻抗：50Ω', '浙江联创', '米', 1, 1, 13, 13, 156000, 'OZCH221035', '2024-11-09 00:00:00', '2024-11-09 00:00:00');
INSERT INTO public.quotation_details VALUES (301, 37, '芜湖梦溪科创走廊一期项目', 'N-J1/2', '尺寸：1/2＂    接口：N-J     外径：15.7mm    用途：同轴电缆连接器', '国产', '只', 1, 1, 16, 16, 22400, 'OCIN5JZALC1', '2024-11-09 00:00:00', '2024-11-09 00:00:00');
INSERT INTO public.quotation_details VALUES (302, 37, '芜湖梦溪科创走廊一期项目', 'N-50KK', '类型：N型    特性：双通    用途：连接器', '国产', '只', 1, 1, 16, 16, 3520, 'OCIN5KZALC1', '2024-11-09 00:00:00', '2024-11-09 00:00:00');
INSERT INTO public.quotation_details VALUES (303, 37, '芜湖梦溪科创走廊一期项目', 'N-50JKW', '类型：N型    特性：直角弯    用途：连接器', '国产', '只', 1, 1, 16, 16, 5440, 'OCIN5JWALC1', '2024-11-09 00:00:00', '2024-11-09 00:00:00');
INSERT INTO public.quotation_details VALUES (304, 37, '芜湖梦溪科创走廊一期项目', 'PNR2000', '频率范围：400-470MHz    锂电池 3700mAh', '和源通信', '套', 1, 1, 1333, 1333, 26660, 'HYTD4MA', '2024-11-09 00:00:00', '2024-11-09 00:00:00');
INSERT INTO public.quotation_details VALUES (305, 37, '芜湖梦溪科创走廊一期项目', 'E-JP50-7', '长度：0.5米 接口：NJ转NJ 用途：天线连接跳线', '国产', '根', 1, 1, 35, 35, 700, 'OISKHB1JLC1', '2024-11-09 00:00:00', '2024-11-09 00:00:00');
INSERT INTO public.quotation_details VALUES (306, 37, '芜湖梦溪科创走廊一期项目', 'RFT-BDA400B LT/M', '频率范围：403-405/413-415MHz 带宽：≤4M 输出：2W  功能： 网讯平台', '和源通信', '套', 1, 1, 11852, 11852, 308152, 'HYR3SI14A', '2024-11-09 00:00:00', '2024-11-09 00:00:00');
INSERT INTO public.quotation_details VALUES (307, 37, '芜湖梦溪科创走廊一期项目', 'ST/FC  4口', '尺寸类型：标准尺寸FC口    端口数：4口    产品类型：墙上型    特性：含法兰头    不含配套尾纤', '国产', '套', 1, 1, 164, 164, 4264, 'EDFWYFC04O', '2024-11-09 00:00:00', '2024-11-09 00:00:00');
INSERT INTO public.quotation_details VALUES (308, 37, '芜湖梦溪科创走廊一期项目', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4569, 4569, 9138, 'EDE1AU6xCZ1', '2024-11-09 00:00:00', '2024-11-09 00:00:00');
INSERT INTO public.quotation_details VALUES (309, 37, '芜湖梦溪科创走廊一期项目', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4570, 4570, 9140, 'EDE1AD6xCZ1', '2024-11-09 00:00:00', '2024-11-09 00:00:00');
INSERT INTO public.quotation_details VALUES (310, 37, '芜湖梦溪科创走廊一期项目', 'ST/FC  24口', '尺寸类型：标准尺寸FC口    端口数：24口    产品类型：机架式    特性：含法兰头    不含配套尾纤', '国产', '套', 1, 1, 431, 431, 862, 'EDFWYFC24W', '2024-11-09 00:00:00', '2024-11-09 00:00:00');
INSERT INTO public.quotation_details VALUES (311, 37, '芜湖梦溪科创走廊一期项目', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '套', 1, 1, 142, 142, 48280, 'HYAIOCN4Y', '2024-11-09 00:00:00', '2024-11-09 00:00:00');
INSERT INTO public.quotation_details VALUES (312, 37, '芜湖梦溪科创走廊一期项目', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 1, 1, 143, 143, 45760, 'HYCDN24Y', '2024-11-09 00:00:00', '2024-11-09 00:00:00');
INSERT INTO public.quotation_details VALUES (313, 37, '芜湖梦溪科创走廊一期项目', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W-网讯平台-数模兼容', '和源通信', '套', 1, 1, 13580, 13580, 108640, 'HYPSMXI40', '2024-11-09 00:00:00', '2024-11-09 00:00:00');
INSERT INTO public.quotation_details VALUES (314, 37, '芜湖梦溪科创走廊一期项目', 'E-FH400-4', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤8.5dB 接入端口数量：4 安装方式：机柜式 尺寸2U', '和源通信', '套', 1, 1, 6642, 6642, 13284, 'ECM1B042CZ1', '2024-11-09 00:00:00', '2024-11-09 00:00:00');
INSERT INTO public.quotation_details VALUES (315, 37, '芜湖梦溪科创走廊一期项目', 'E-JF350/400-4', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤7.5dB 接入端口数量：4 安装方式：机柜式 尺寸1U', '和源通信', '套', 1, 1, 2494, 2494, 4988, 'EDE1BU4xCZ1', '2024-11-09 00:00:00', '2024-11-09 00:00:00');
INSERT INTO public.quotation_details VALUES (316, 37, '芜湖梦溪科创走廊一期项目', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 1, 1, 3753, 3753, 3753, 'EDULN4N1CZ1', '2024-11-09 00:00:00', '2024-11-09 00:00:00');
INSERT INTO public.quotation_details VALUES (317, 37, '芜湖梦溪科创走廊一期项目', 'RFS-400 LT/M', '频率范围：350-50MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 1, 1, 9876, 9876, 79008, 'HYR2SI030', '2024-11-09 00:00:00', '2024-11-09 00:00:00');
INSERT INTO public.quotation_details VALUES (318, 38, '青少年体育发展中心智能化工程', 'HCAAYZ -50-12', '尺寸：1/2＂    特性1：低烟无卤    特性2：阻燃    阻抗：50Ω', '浙江联创', '米', 1, 1, 13, 13, 36400, 'OZCH221035', '2024-10-24 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (319, 38, '青少年体育发展中心智能化工程', 'N-J1/2', '尺寸：1/2＂    接口：N-J     外径：15.7mm    用途：同轴电缆连接器', '国产', '只', 1, 1, 16, 16, 2240, 'OCIN5JZALC1', '2024-10-24 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (320, 38, '青少年体育发展中心智能化工程', 'N-50KK', '类型：N型    特性：双通    用途：连接器', '国产', '只', 1, 1, 16, 16, 2720, 'OCIN5KZALC1', '2024-10-24 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (321, 38, '青少年体育发展中心智能化工程', 'N-50JKW', '类型：N型    特性：直角弯    用途：连接器', '国产', '只', 1, 1, 16, 16, 960, 'OCIN5JWALC1', '2024-10-24 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (322, 38, '青少年体育发展中心智能化工程', 'PNR2000', '频率范围：400-470MHz    锂电池 3700mAh', '和源通信', '套', 1, 1, 1333, 1333, 26660, 'HYTD4MA', '2024-10-24 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (323, 38, '青少年体育发展中心智能化工程', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '套', 1, 1, 142, 142, 7810, 'HYAIOCN4Y', '2024-10-24 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (324, 38, '青少年体育发展中心智能化工程', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 1, 1, 143, 143, 429, 'HYCDN24Y', '2024-10-24 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (325, 38, '青少年体育发展中心智能化工程', 'EVDC-6 LT', '频率范围：150-170MHz    承载功率：100W;耦合规格：6dB', '和源通信', '套', 1, 1, 185, 185, 9620, 'HYCCN31Y', '2024-10-24 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (326, 38, '青少年体育发展中心智能化工程', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 1, 1, 458, 458, 458, 'EANLOMO5HR1', '2024-10-24 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (327, 38, '青少年体育发展中心智能化工程', 'MONT80', '曲臂长度50cm 材料：不锈钢 结构类型：L型结构', '国产', '套', 1, 1, 151, 151, 151, 'OBJANOTGR01', '2024-10-24 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (328, 38, '青少年体育发展中心智能化工程', 'CA-23RS', '频率范围：0-1000MHz 功率：700W 阻抗：50Ω 接口（可选）：N', '钻石', '套', 1, 1, 134, 134, 134, 'OBJANOTHS01', '2024-10-24 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (329, 38, '青少年体育发展中心智能化工程', 'R-EVDC-BLST-D', '频率范围：87-170MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4939, 4939, 4939, 'HYMBC6A1D', '2024-10-24 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (330, 38, '青少年体育发展中心智能化工程', 'ST/FC  24口', '尺寸类型：标准尺寸FC口    端口数：24口    产品类型：机架式    特性：含法兰头    不含配套尾纤', '国产', '套', 1, 1, 431, 431, 431, 'EDFWYFC24W', '2024-10-24 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (331, 38, '青少年体育发展中心智能化工程', 'RFS-400 LT/M', '频率范围：350-50MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 1, 1, 9876, 9876, 9876, 'HYR2SI030', '2024-10-24 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (332, 38, '青少年体育发展中心智能化工程', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 1U机箱 功能： 网讯平台', '和源通信', '套', 1, 1, 11851, 11851, 23702, 'HYR3SI140', '2024-10-24 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (333, 38, '青少年体育发展中心智能化工程', 'ST/FC  4口', '尺寸类型：标准尺寸FC口    端口数：4口    产品类型：墙上型    特性：含法兰头    不含配套尾纤', '国产', '套', 1, 1, 164, 164, 328, 'EDFWYFC04O', '2024-10-24 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (334, 38, '青少年体育发展中心智能化工程', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W-网讯平台-数模兼容', '和源通信', '套', 1, 1, 13580, 13580, 27160, 'HYPSMXI40', '2024-10-24 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (335, 38, '青少年体育发展中心智能化工程', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 1, 1, 4569, 4569, 4569, 'ECM1B022CZ1', '2024-10-24 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (336, 38, '青少年体育发展中心智能化工程', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 1, 1, 2321, 2321, 2321, 'EDE1BU2xCZ1', '2024-10-24 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (337, 38, '青少年体育发展中心智能化工程', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 1, 1, 3753, 3753, 3753, 'EDULN4N1CZ1', '2024-10-24 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (338, 38, '青少年体育发展中心智能化工程', 'R-EVDC-BLST-U', '频率范围：87-170MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4938, 4938, 4938, 'HYMBC6A1U', '2024-10-24 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (339, 39, '江山汇项目 D 地块弱电智能化工程项目', 'N-50KK', '类型：N型    特性：双通    用途：连接器', '国产', '只', 1, 1, 16, 16, 4480, 'OCIN5KZALC1', '2024-09-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (340, 39, '江山汇项目 D 地块弱电智能化工程项目', 'N-50JKW', '类型：N型    特性：直角弯    用途：连接器', '国产', '只', 1, 1, 16, 16, 640, 'OCIN5JWALC1', '2024-09-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (341, 39, '江山汇项目 D 地块弱电智能化工程项目', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 1, 1, 142, 142, 1704, 'HYCDN24Y', '2024-09-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (342, 39, '江山汇项目 D 地块弱电智能化工程项目', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 1, 1, 142, 142, 8804, 'HYCCN34Y', '2024-09-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (343, 39, '江山汇项目 D 地块弱电智能化工程项目', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '套', 1, 1, 142, 142, 8804, 'HYAIOCN4Y', '2024-09-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (344, 39, '江山汇项目 D 地块弱电智能化工程项目', 'HCAAYZ -50-12', '尺寸：1/2＂    特性1：低烟无卤    特性2：阻燃    阻抗：50Ω', '浙江联创', '米', 1, 1, 13, 13, 45500, 'OZCH221035', '2024-09-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (345, 39, '江山汇项目 D 地块弱电智能化工程项目', 'N-J1/2', '尺寸：1/2＂    接口：N-J     外径：15.7mm    用途：同轴电缆连接器', '国产', '只', 1, 1, 16, 16, 1120, 'OCIN5JZALC1', '2024-09-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (346, 39, '江山汇项目 D 地块弱电智能化工程项目', 'ST/FC  24口', '尺寸类型：标准尺寸FC口    端口数：24口    产品类型：机架式    特性：含法兰头    不含配套尾纤', '国产', '套', 1, 1, 431, 431, 431, 'EDFWYFC24W', '2024-09-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (347, 39, '江山汇项目 D 地块弱电智能化工程项目', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 1, 1, 3753, 3753, 3753, 'EDULN4N1CZ1', '2024-09-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (348, 39, '江山汇项目 D 地块弱电智能化工程项目', 'RFS-400 LT/M', '频率范围：350-50MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 1, 1, 9876, 9876, 9876, 'HYR2SI030', '2024-09-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (349, 39, '江山汇项目 D 地块弱电智能化工程项目', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 1U机箱 功能： 网讯平台', '和源通信', '套', 1, 1, 11851, 11851, 23702, 'HYR3SI140', '2024-09-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (350, 39, '江山汇项目 D 地块弱电智能化工程项目', 'ST/FC  4口', '尺寸类型：标准尺寸FC口    端口数：4口    产品类型：墙上型    特性：含法兰头    不含配套尾纤', '国产', '套', 1, 1, 164, 164, 328, 'EDFWYFC04O', '2024-09-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (351, 39, '江山汇项目 D 地块弱电智能化工程项目', 'PNR2000', '频率范围：400-470MHz    锂电池 3700mAh', '和源通信', '套', 1, 1, 1333, 1333, 53320, 'HYTD4MA', '2024-09-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (352, 39, '江山汇项目 D 地块弱电智能化工程项目', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 1, 1, 4569, 4569, 4569, 'ECM1B022CZ1', '2024-09-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (353, 39, '江山汇项目 D 地块弱电智能化工程项目', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 1, 1, 2321, 2321, 2321, 'EDE1BU2xCZ1', '2024-09-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (354, 39, '江山汇项目 D 地块弱电智能化工程项目', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4569, 4569, 4569, 'EDE1AU6xCZ1', '2024-09-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (355, 39, '江山汇项目 D 地块弱电智能化工程项目', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4570, 4570, 4570, 'EDE1AD6xCZ1', '2024-09-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (356, 39, '江山汇项目 D 地块弱电智能化工程项目', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W-网讯平台-数模兼容', '和源通信', '套', 1, 1, 13580, 13580, 27160, 'HYPSMXI40', '2024-09-21 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (357, 40, '北京颐缇港二期627地块项目', 'E-FH350-4', '频率范围：350-390MHz 单端口承载功率：50W;插入损耗：≤8.5dB接入端口数量：4;安装方式：机柜式;尺寸：2U', '和源通信', '套', 1, 1, 6667, 6667, 6667, 'ECM1B042CZ2', '2024-09-07 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (358, 40, '北京颐缇港二期627地块项目', 'E-FH400-4', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤8.5dB 接入端口数量：4 安装方式：机柜式 尺寸2U', '和源通信', '套', 1, 1, 6642, 6642, 6642, 'ECM1B042CZ1', '2024-09-07 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (359, 40, '北京颐缇港二期627地块项目', 'E-JF350/400-4', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤7.5dB 接入端口数量：4 安装方式：机柜式 尺寸1U', '和源通信', '套', 1, 1, 2493, 2493, 2493, 'EDE1BU4xCZ1', '2024-09-07 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (360, 40, '北京颐缇港二期627地块项目', 'R-EVDC-BLST-U', '频率范围：87-170MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4938, 4938, 4938, 'HYMBC6A1U', '2024-09-07 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (361, 40, '北京颐缇港二期627地块项目', 'R-EVDC-BLST-D', '频率范围：87-170MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4938, 4938, 4938, 'HYMBC6A1D', '2024-09-07 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (362, 40, '北京颐缇港二期627地块项目', 'E-JF350/400-4', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤7.5dB 接入端口数量：4 安装方式：机柜式 尺寸1U', '和源通信', '套', 1, 1, 2493, 2493, 2493, 'EDE1BU4xCZ1', '2024-09-07 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (363, 40, '北京颐缇港二期627地块项目', 'E-SGQ350D', '频率范围：351-356/361-366MHz 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 隔离方式：带通 工作带宽：5M 安装方式：机柜式 尺寸：2U', '和源通信', '套', 1, 1, 9167, 9167, 9167, 'EDUPB5H1CZ1', '2024-09-07 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (364, 40, '北京颐缇港二期627地块项目', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 1, 1, 3753, 3753, 3753, 'EDULN4N1CZ1', '2024-09-07 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (365, 40, '北京颐缇港二期627地块项目', 'E-SGQ800D', '频率范围：806-821/851-866MHz 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：45M 隔离方式：带通 工作带宽：15M 安装方式：机柜式 尺寸：2U', '和源通信', '套', 1, 1, 9167, 9167, 9167, 'EDUPGFH1CZ1', '2024-09-07 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (366, 40, '北京颐缇港二期627地块项目', 'E-ANTY 100', '频率范围：087-108MHz 增益：6dBi 防护等级：IP65 辐射方向：定向 最大承载功率：50W 接头类型：N-Femade 特性：室外', '和源通信', '套', 1, 1, 750, 750, 750, 'OANFOYD7MJ1', '2024-09-07 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (367, 40, '北京颐缇港二期627地块项目', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 1, 1, 458, 458, 458, 'EANLOMO5HR1', '2024-09-07 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (368, 40, '北京颐缇港二期627地块项目', 'RFS-88 LT/M', '频率范围：87-108MHz 远端携带：4 功能：正面状态灯/面板调试', '和源通信', '套', 1, 1, 8958, 8958, 35832, 'HYR2SI000', '2024-09-07 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (369, 40, '北京颐缇港二期627地块项目', 'RFT-BDA88 LT/M', '频率范围：87-108MHz；带宽：≤21M；输出：10W；2U机柜；功能：正面状态灯/面板调试', '和源通信', '套', 1, 1, 22500, 22500, 157500, 'HYR3SI300', '2024-09-07 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (370, 40, '北京颐缇港二期627地块项目', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4569, 4569, 13707, 'EDE1AU6xCZ1', '2024-09-07 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (371, 40, '北京颐缇港二期627地块项目', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4569, 4569, 13707, 'EDE1AD6xCZ1', '2024-09-07 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (372, 40, '北京颐缇港二期627地块项目', 'RFS-400 LT/M', '频率范围：350-50MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 1, 1, 9876, 9876, 128388, 'HYR2SI030', '2024-09-07 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (373, 40, '北京颐缇港二期627地块项目', 'RFT-BDA310 LT/M', '频率范围：351-356/361-366MHz 带宽：≤5M 输出：10W 2U机箱 功能： 正面状态灯/网讯平台', '和源通信', '套', 1, 1, 21250, 21250, 276250, 'HYR3SI330', '2024-09-07 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (374, 40, '北京颐缇港二期627地块项目', 'RFT-BDA410 LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：10W 功能： 正面状态灯/网讯平台', '和源通信', '套', 1, 1, 21250, 21250, 255000, 'HYR3SI340', '2024-09-07 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (375, 40, '北京颐缇港二期627地块项目', 'RFS-800 LT/M', '频率范围：800-890MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 1, 1, 8958, 8958, 62706, 'HYR2SI080', '2024-09-07 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (376, 40, '北京颐缇港二期627地块项目', 'RFT-BDA810 LT/M', '频率范围：806-821/851-866MHz 带宽：≤15M 输出：10W 2U机箱 功能： 正面状态灯/网讯平台', '和源通信', '套', 1, 1, 21250, 21250, 276250, 'HYR3SI380', '2024-09-07 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (377, 40, '北京颐缇港二期627地块项目', 'HCAAYZ -50-12', '尺寸：1/2＂    特性1：低烟无卤    特性2：阻燃    阻抗：50Ω', '浙江联创', '米', 1, 1, 13, 13, 117000, 'OZCH221035', '2024-09-07 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (378, 40, '北京颐缇港二期627地块项目', 'E-BDA088-U FM', '频率范围：087-108MHz;最大功率：1mW;机柜式;尺寸：3U;供电供电220VAC;内置功能：16信道广播接入&广播告警切换;监控能力：不支持', '和源通信', '套', 1, 1, 116667, 116667, 116667, 'OAMFF5WUGH1', '2024-09-07 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (379, 40, '北京颐缇港二期627地块项目', 'E-FHP2000-3', '频率范围：87-108/351-366/410-424MHz 单端口承载功率：50W 插入损耗：≤2.0dB 接入端口数量：3 安装方式：机柜式 尺寸：2U', '和源通信', '套', 1, 1, 16667, 16667, 216671, 'ECM5BB32CZ1', '2024-09-07 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (380, 40, '北京颐缇港二期627地块项目', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '套', 1, 1, 142, 142, 36210, 'HYAIOCN4Y', '2024-09-07 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (381, 40, '北京颐缇港二期627地块项目', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 1, 1, 142, 142, 25560, 'HYCCN34Y', '2024-09-07 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (382, 40, '北京颐缇港二期627地块项目', 'ACC-CWT', '提供某一个项目上所有系统的工作管理    直观全面的反映系统的整体面貌和其中设备的布局    并可以跟踪每个设备及服务的进程。-告警处置模块-告警详情模块-维修情况和完成情况-设备位置地图模块    含一年的在线后台服', '和源通信', '个/年', 1, 1, 8333, 8333, 8333, 'HYWF0NA1', '2024-09-07 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (383, 40, '北京颐缇港二期627地块项目', 'LS-NFX-BDA', '网讯云端终端直放站接入管理服务许可-远端站告警-远端区域状态更新', '和源通信', '套', 1, 1, 1500, 1500, 67500, 'HYWSRNB1', '2024-09-07 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (384, 40, '北京颐缇港二期627地块项目', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 1, 1, 142, 142, 10082, 'HYCDN24Y', '2024-09-07 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (385, 40, '北京颐缇港二期627地块项目', 'CA-23RS', '频率范围：0-1000MHz 功率：700W 阻抗：50Ω 接口（可选）：N', '钻石', '套', 1, 1, 133, 133, 266, 'OBJANOTHS01', '2024-09-07 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (386, 40, '北京颐缇港二期627地块项目', 'NFX_GATW', '用于本地系统设备管理和服务器的同步 -本地系统建立和配置 -设备驱动管理 -设备参数设置 -云同步 -设备报警管理', '和源通信', '套', 1, 1, 12500, 12500, 12500, 'HYWG0NB1', '2024-09-07 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (387, 40, '北京颐缇港二期627地块项目', 'NFX_MAST_OPETN', '-账户创建和访问管理-设备数据和系统数据的存储和恢复-产品库数据-系统拓扑和设备位置显示和管理-系统资源统计和告警分析推送-系统工作台主次账号一个-20个远端站授权    4个信道机授权    100个终端授权', '和源通信', '套', 1, 1, 105000, 105000, 105000, 'HYWP0NC1', '2024-09-07 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (388, 41, '江阴澄星广场及大厦办公区域智能化项目', 'N-50KK', '类型：N型    特性：双通    用途：连接器', '国产', '只', 1, 1, 15, 15, 900, 'OCIN5KZALC1', '2024-08-09 00:00:00', '2024-08-09 00:00:00');
INSERT INTO public.quotation_details VALUES (389, 41, '江阴澄星广场及大厦办公区域智能化项目', 'N-J1/2', '尺寸：1/2＂    接口：N-J     外径：15.7mm    用途：同轴电缆连接器', '国产', '只', 1, 1, 15, 15, 5250, 'OCIN5JZALC1', '2024-08-09 00:00:00', '2024-08-09 00:00:00');
INSERT INTO public.quotation_details VALUES (390, 41, '江阴澄星广场及大厦办公区域智能化项目', 'NJ-3/NJ-3-1.5M', '接口：NJ转NJ    长度：1.5米    特性1：超柔    特性2：SYV-50-3', '国产', '根', 1, 1, 100, 100, 800, 'W000188', '2024-08-09 00:00:00', '2024-08-09 00:00:00');
INSERT INTO public.quotation_details VALUES (391, 41, '江阴澄星广场及大厦办公区域智能化项目', '单模单芯FC-LC 10米', '光纤类型：单模    光缆类型：单芯    接口类型：FC/PC-LC/PC    长度：10米', '国产', '根', 1, 1, 58, 58, 464, 'W000154', '2024-08-09 00:00:00', '2024-08-09 00:00:00');
INSERT INTO public.quotation_details VALUES (392, 41, '江阴澄星广场及大厦办公区域智能化项目', 'ST/FC  24口', '尺寸类型：标准尺寸FC口    端口数：24口    产品类型：机架式    特性：含法兰头    不含配套尾纤', '国产', '套', 1, 1, 430, 430, 430, 'EDFWYFC24W', '2024-08-09 00:00:00', '2024-08-09 00:00:00');
INSERT INTO public.quotation_details VALUES (393, 41, '江阴澄星广场及大厦办公区域智能化项目', 'ST/FC  4口', '尺寸类型：标准尺寸FC口    端口数：4口    产品类型：墙上型    特性：含法兰头    不含配套尾纤', '国产', '套', 1, 1, 163, 163, 652, 'EDFWYFC04O', '2024-08-09 00:00:00', '2024-08-09 00:00:00');
INSERT INTO public.quotation_details VALUES (394, 41, '江阴澄星广场及大厦办公区域智能化项目', 'GYXTH-4B1 4芯', '芯数：4芯    钢带：铠装    特性：单模    低烟无卤阻燃', '国产', '米', 1, 1, 9, 9, 5400, 'ECAWYGYXTH0401', '2024-08-09 00:00:00', '2024-08-09 00:00:00');
INSERT INTO public.quotation_details VALUES (395, 41, '江阴澄星广场及大厦办公区域智能化项目', 'HCAAYZ -50-12', '尺寸：1/2＂    特性1：低烟无卤    特性2：阻燃    阻抗：50Ω', '浙江联创', '米', 1, 1, 13, 13, 33800, 'OZCH221035', '2024-08-09 00:00:00', '2024-08-09 00:00:00');
INSERT INTO public.quotation_details VALUES (396, 41, '江阴澄星广场及大厦办公区域智能化项目', 'PNR2000', '频率范围：400-470MHz    锂电池 3700mAh', '和源通信', '套', 1, 1, 1333, 1333, 53320, 'HYTD4MA', '2024-08-09 00:00:00', '2024-08-09 00:00:00');
INSERT INTO public.quotation_details VALUES (397, 41, '江阴澄星广场及大厦办公区域智能化项目', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 1, 1, 3753, 3753, 3753, 'EDULN4N1CZ1', '2024-08-09 00:00:00', '2024-08-09 00:00:00');
INSERT INTO public.quotation_details VALUES (398, 41, '江阴澄星广场及大厦办公区域智能化项目', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 1, 1, 142, 142, 284, 'HYCDN24Y', '2024-08-09 00:00:00', '2024-08-09 00:00:00');
INSERT INTO public.quotation_details VALUES (399, 41, '江阴澄星广场及大厦办公区域智能化项目', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 1, 1, 142, 142, 12212, 'HYCCN34Y', '2024-08-09 00:00:00', '2024-08-09 00:00:00');
INSERT INTO public.quotation_details VALUES (400, 41, '江阴澄星广场及大厦办公区域智能化项目', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '套', 1, 1, 142, 142, 12212, 'HYAIOCN4Y', '2024-08-09 00:00:00', '2024-08-09 00:00:00');
INSERT INTO public.quotation_details VALUES (401, 41, '江阴澄星广场及大厦办公区域智能化项目', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 1U机箱 功能： 网讯平台', '和源通信', '套', 1, 1, 11851, 11851, 47404, 'HYR3SI140', '2024-08-09 00:00:00', '2024-08-09 00:00:00');
INSERT INTO public.quotation_details VALUES (402, 41, '江阴澄星广场及大厦办公区域智能化项目', 'RFS-400 LT/M', '频率范围：350-50MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 1, 1, 9876, 9876, 9876, 'HYR2SI030', '2024-08-09 00:00:00', '2024-08-09 00:00:00');
INSERT INTO public.quotation_details VALUES (403, 41, '江阴澄星广场及大厦办公区域智能化项目', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4569, 4569, 4569, 'EDE1AD6xCZ1', '2024-08-09 00:00:00', '2024-08-09 00:00:00');
INSERT INTO public.quotation_details VALUES (404, 41, '江阴澄星广场及大厦办公区域智能化项目', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4569, 4569, 4569, 'EDE1AU6xCZ1', '2024-08-09 00:00:00', '2024-08-09 00:00:00');
INSERT INTO public.quotation_details VALUES (405, 41, '江阴澄星广场及大厦办公区域智能化项目', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 1, 1, 2320, 2320, 2320, 'EDE1BU2xCZ1', '2024-08-09 00:00:00', '2024-08-09 00:00:00');
INSERT INTO public.quotation_details VALUES (406, 41, '江阴澄星广场及大厦办公区域智能化项目', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 1, 1, 4569, 4569, 4569, 'ECM1B022CZ1', '2024-08-09 00:00:00', '2024-08-09 00:00:00');
INSERT INTO public.quotation_details VALUES (407, 41, '江阴澄星广场及大厦办公区域智能化项目', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W-网讯平台-数模兼容', '和源通信', '套', 1, 1, 13580, 13580, 27160, 'HYPSMXI40', '2024-08-09 00:00:00', '2024-08-09 00:00:00');
INSERT INTO public.quotation_details VALUES (408, 42, '杭州阿里巴巴总部西溪七期', 'E-FH400-4', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤8.5dB 接入端口数量：4 安装方式：机柜式 尺寸2U', '和源通信', '套', 1, 1, 6642, 6642, 6642, 'ECM1B042CZ1', '2024-07-29 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (409, 42, '杭州阿里巴巴总部西溪七期', 'E-JF350/400-4', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤7.5dB 接入端口数量：4 安装方式：机柜式 尺寸1U', '和源通信', '套', 1, 1, 2493, 2493, 2493, 'EDE1BU4xCZ1', '2024-07-29 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (410, 42, '杭州阿里巴巴总部西溪七期', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4569, 4569, 4569, 'EDE1AD6xCZ1', '2024-07-29 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (411, 42, '杭州阿里巴巴总部西溪七期', 'RFS-400 LT/M', '频率范围：350-50MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 1, 1, 9876, 9876, 9876, 'HYR2SI030', '2024-07-29 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (412, 42, '杭州阿里巴巴总部西溪七期', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 1U机箱 功能： 网讯平台', '和源通信', '套', 1, 1, 11851, 11851, 35553, 'HYR3SI140', '2024-07-29 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (413, 42, '杭州阿里巴巴总部西溪七期', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '套', 1, 1, 142, 142, 8236, 'HYAIOCN4Y', '2024-07-29 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (414, 42, '杭州阿里巴巴总部西溪七期', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 1, 1, 142, 142, 6816, 'HYCCN34Y', '2024-07-29 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (415, 42, '杭州阿里巴巴总部西溪七期', 'HCAAYZ -50-12', '尺寸：1/2＂    特性1：低烟无卤    特性2：阻燃    阻抗：50Ω', '浙江联创', '米', 1, 1, 13, 13, 52000, 'OZCH221035', '2024-07-29 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (416, 42, '杭州阿里巴巴总部西溪七期', 'N-J1/2', '尺寸：1/2＂    接口：N-J     外径：15.7mm    用途：同轴电缆连接器', '国产', '只', 1, 1, 15, 15, 3600, 'OCIN5JZALC1', '2024-07-29 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (417, 42, '杭州阿里巴巴总部西溪七期', 'N-50KK', '类型：N型    特性：双通    用途：连接器', '国产', '只', 1, 1, 15, 15, 300, 'OCIN5KZALC1', '2024-07-29 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (418, 42, '杭州阿里巴巴总部西溪七期', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 1, 1, 3753, 3753, 3753, 'EDULN4N1CZ1', '2024-07-29 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (447, 43, '芜湖第四人民医院（安定医院）', 'MONT80', '曲臂长度50cm 材料：不锈钢 结构类型：L型结构', '国产', '套', 1, 1, 150, 150, 150, 'OBJANOTGR01', '2024-07-16 00:00:00', '2024-07-16 00:00:00');
INSERT INTO public.quotation_details VALUES (419, 42, '杭州阿里巴巴总部西溪七期', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4569, 4569, 4569, 'EDE1AU6xCZ1', '2024-07-29 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (420, 42, '杭州阿里巴巴总部西溪七期', '单模单芯 FC-FC  5米', '光纤类型：单模    光缆类型：单芯    接口类型：FC/PC-FC/PC    长度：5米', '国产', '根', 1, 1, 30, 30, 180, 'EJUWY05A4001', '2024-07-29 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (421, 42, '杭州阿里巴巴总部西溪七期', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 1, 1, 142, 142, 1136, 'HYCDN24Y', '2024-07-29 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (422, 42, '杭州阿里巴巴总部西溪七期', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 1, 1, 458, 458, 458, 'EANLOMO5HR1', '2024-07-29 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (423, 42, '杭州阿里巴巴总部西溪七期', 'MONT80', '曲臂长度50cm 材料：不锈钢 结构类型：L型结构', '国产', '套', 1, 1, 150, 150, 150, 'OBJANOTGR01', '2024-07-29 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (424, 42, '杭州阿里巴巴总部西溪七期', 'CA-23RS', '频率范围：0-1000MHz 功率：700W 阻抗：50Ω 接口（可选）：N', '钻石', '套', 1, 1, 133, 133, 133, 'OBJANOTHS01', '2024-07-29 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (425, 42, '杭州阿里巴巴总部西溪七期', 'GYXTH-4B1 4芯', '芯数：4芯    钢带：铠装    特性：单模    低烟无卤阻燃', '国产', '米', 1, 1, 9, 9, 4500, 'ECAWYGYXTH0401', '2024-07-29 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (426, 42, '杭州阿里巴巴总部西溪七期', 'ST/FC  4口', '尺寸类型：标准尺寸FC口    端口数：4口    产品类型：墙上型    特性：含法兰头    不含配套尾纤', '国产', '套', 1, 1, 163, 163, 489, 'EDFWYFC04O', '2024-07-29 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (427, 42, '杭州阿里巴巴总部西溪七期', 'ST/FC  24口', '尺寸类型：标准尺寸FC口    端口数：24口    产品类型：机架式    特性：含法兰头    不含配套尾纤', '国产', '套', 1, 1, 430, 430, 430, 'EDFWYFC24W', '2024-07-29 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (428, 42, '杭州阿里巴巴总部西溪七期', 'E-JP50-7', '长度：0.5米 接口：NJ转NJ 用途：天线连接跳线', '国产', '根', 1, 1, 35, 35, 1400, 'OISKHB1JLC1', '2024-07-29 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (429, 42, '杭州阿里巴巴总部西溪七期', 'NJ-3/NJ-3-1.5M', '接口：NJ转NJ    长度：1.5米    特性1：超柔    特性2：SYV-50-3', '国产', '根', 1, 1, 100, 100, 1000, 'W000188', '2024-07-29 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (430, 42, '杭州阿里巴巴总部西溪七期', 'N-50JKW', '类型：N型    特性：直角弯    用途：连接器', '国产', '只', 1, 1, 15, 15, 150, 'OCIN5JWALC1', '2024-07-29 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (431, 43, '芜湖第四人民医院（安定医院）', 'LS-NFX-RPT', '网讯平台信道机接入管理服务许可 -信道资源管理 -呼叫类型繁忙度分析', '和源通信', '套', 1, 1, 2500, 2500, 5000, 'HYWSPNB1', '2024-07-16 00:00:00', '2024-07-16 00:00:00');
INSERT INTO public.quotation_details VALUES (432, 43, '芜湖第四人民医院（安定医院）', 'LS-NFX-BDA', '网讯云端终端直放站接入管理服务许可-远端站告警-远端区域状态更新', '和源通信', '套', 1, 1, 1500, 1500, 16500, 'HYWSRNB1', '2024-07-16 00:00:00', '2024-07-16 00:00:00');
INSERT INTO public.quotation_details VALUES (433, 43, '芜湖第四人民医院（安定医院）', 'LS-NFX-RAD', '网讯平台终端对讲机接入管理服务许可-对讲机ID呼叫管理-对讲机上下线管理-呼叫组繁忙度分析', '和源通信', '套', 1, 1, 180, 180, 7200, 'HYWSTNB1', '2024-07-16 00:00:00', '2024-07-16 00:00:00');
INSERT INTO public.quotation_details VALUES (434, 43, '芜湖第四人民医院（安定医院）', 'ACC-NUT', '提供多单位的系统运维流程跟踪-告警管理和推送-故障设备快速定位-维护更新工作单', '和源通信', '个/年', 1, 1, 4167, 4167, 4167, 'HYWT0NA1', '2024-07-16 00:00:00', '2024-07-16 00:00:00');
INSERT INTO public.quotation_details VALUES (435, 43, '芜湖第四人民医院（安定医院）', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W-网讯平台-数模兼容', '和源通信', '套', 1, 1, 13580, 13580, 27160, 'HYPSMXI40', '2024-07-16 00:00:00', '2024-07-16 00:00:00');
INSERT INTO public.quotation_details VALUES (436, 43, '芜湖第四人民医院（安定医院）', 'PNR2000', '频率范围：400-470MHz    锂电池 3700mAh', '和源通信', '套', 1, 1, 1333, 1333, 53320, 'HYTD4MA', '2024-07-16 00:00:00', '2024-07-16 00:00:00');
INSERT INTO public.quotation_details VALUES (437, 43, '芜湖第四人民医院（安定医院）', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 1, 1, 4569, 4569, 4569, 'ECM1B022CZ1', '2024-07-16 00:00:00', '2024-07-16 00:00:00');
INSERT INTO public.quotation_details VALUES (438, 43, '芜湖第四人民医院（安定医院）', 'NFX_GATW', '用于本地系统设备管理和服务器的同步 -本地系统建立和配置 -设备驱动管理 -设备参数设置 -云同步 -设备报警管理', '和源通信', '套', 1, 1, 12500, 12500, 12500, 'HYWG0NB1', '2024-07-16 00:00:00', '2024-07-16 00:00:00');
INSERT INTO public.quotation_details VALUES (439, 43, '芜湖第四人民医院（安定医院）', 'ACC-CWT', '提供某一个项目上所有系统的工作管理    直观全面的反映系统的整体面貌和其中设备的布局    并可以跟踪每个设备及服务的进程。-告警处置模块-告警详情模块-维修情况和完成情况-设备位置地图模块    含一年的在线后台服', '和源通信', '个/年', 1, 1, 8333, 8333, 8333, 'HYWF0NA1', '2024-07-16 00:00:00', '2024-07-16 00:00:00');
INSERT INTO public.quotation_details VALUES (440, 43, '芜湖第四人民医院（安定医院）', 'MAPD-2', '频率范围：88-866MHz 承载功率：100W 分路端口数量：2 防护等级：IP65 应用：馈电', '和源通信', '套', 1, 1, 208, 208, 5616, 'HYCDF24Y', '2024-07-16 00:00:00', '2024-07-16 00:00:00');
INSERT INTO public.quotation_details VALUES (441, 43, '芜湖第四人民医院（安定医院）', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 1, 1, 2320, 2320, 2320, 'EDE1BU2xCZ1', '2024-07-16 00:00:00', '2024-07-16 00:00:00');
INSERT INTO public.quotation_details VALUES (442, 43, '芜湖第四人民医院（安定医院）', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 1, 1, 3753, 3753, 3753, 'EDULN4N1CZ1', '2024-07-16 00:00:00', '2024-07-16 00:00:00');
INSERT INTO public.quotation_details VALUES (443, 43, '芜湖第四人民医院（安定医院）', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4569, 4569, 4569, 'EDE1AU6xCZ1', '2024-07-16 00:00:00', '2024-07-16 00:00:00');
INSERT INTO public.quotation_details VALUES (444, 43, '芜湖第四人民医院（安定医院）', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4569, 4569, 4569, 'EDE1AD6xCZ1', '2024-07-16 00:00:00', '2024-07-16 00:00:00');
INSERT INTO public.quotation_details VALUES (445, 43, '芜湖第四人民医院（安定医院）', 'RFS-400 LT/M', '频率范围：350-50MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 1, 1, 9876, 9876, 29628, 'HYR2SI030', '2024-07-16 00:00:00', '2024-07-16 00:00:00');
INSERT INTO public.quotation_details VALUES (446, 43, '芜湖第四人民医院（安定医院）', 'CA-23RS', '频率范围：0-1000MHz 功率：700W 阻抗：50Ω 接口（可选）：N', '钻石', '套', 1, 1, 133, 133, 133, 'OBJANOTHS01', '2024-07-16 00:00:00', '2024-07-16 00:00:00');
INSERT INTO public.quotation_details VALUES (448, 43, '芜湖第四人民医院（安定医院）', 'HCAAYZ -50-12', '尺寸：1/2＂    特性1：低烟无卤    特性2：阻燃    阻抗：50Ω', '浙江联创', '米', 1, 1, 13, 13, 104000, 'OZCH221035', '2024-07-16 00:00:00', '2024-07-16 00:00:00');
INSERT INTO public.quotation_details VALUES (449, 43, '芜湖第四人民医院（安定医院）', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 1U机箱 功能： 网讯平台', '和源通信', '套', 1, 1, 11851, 11851, 130361, 'HYR3SI140', '2024-07-16 00:00:00', '2024-07-16 00:00:00');
INSERT INTO public.quotation_details VALUES (450, 43, '芜湖第四人民医院（安定医院）', 'FDPower400', '馈电功能模组    需搭配可扩展远端机;内置远端内向天馈提供电力;', '和源通信', '套', 1, 1, 1583, 1583, 17413, 'HYGF20000', '2024-07-16 00:00:00', '2024-07-16 00:00:00');
INSERT INTO public.quotation_details VALUES (451, 43, '芜湖第四人民医院（安定医院）', 'MADC-6', '频率范围：351-470MHz 承载功率：100W 耦合规格：6dB 分路端口数量：2 防护等级：IP65 应用：馈电', '和源通信', '套', 1, 1, 246, 246, 30504, 'HYCCF34Y', '2024-07-16 00:00:00', '2024-07-16 00:00:00');
INSERT INTO public.quotation_details VALUES (452, 43, '芜湖第四人民医院（安定医院）', 'N-J1/2', '尺寸：1/2＂    接口：N-J     外径：15.7mm    用途：同轴电缆连接器', '国产', '只', 1, 1, 15, 15, 9150, 'OCIN5JZALC1', '2024-07-16 00:00:00', '2024-07-16 00:00:00');
INSERT INTO public.quotation_details VALUES (453, 43, '芜湖第四人民医院（安定医院）', 'N-50KK', '类型：N型    特性：双通    用途：连接器', '国产', '只', 1, 1, 15, 15, 2250, 'OCIN5KZALC1', '2024-07-16 00:00:00', '2024-07-16 00:00:00');
INSERT INTO public.quotation_details VALUES (454, 43, '芜湖第四人民医院（安定医院）', 'E-JP50-7', '长度：0.5米 接口：NJ转NJ 用途：天线连接跳线', '国产', '根', 1, 1, 35, 35, 3150, 'OISKHB1JLC1', '2024-07-16 00:00:00', '2024-07-16 00:00:00');
INSERT INTO public.quotation_details VALUES (455, 43, '芜湖第四人民医院（安定医院）', 'NJ/NJ-3 1.5米', '接口：NJ转NJ    长度：1.5米    用途：机柜内跳线', '国产', '根', 1, 1, 40, 40, 560, 'EJUMJK4315NJNJ', '2024-07-16 00:00:00', '2024-07-16 00:00:00');
INSERT INTO public.quotation_details VALUES (456, 43, '芜湖第四人民医院（安定医院）', 'MA11', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65 应用：指示灯', '和源通信', '套', 1, 1, 208, 208, 31408, 'HYAIOCL4Y', '2024-07-16 00:00:00', '2024-07-16 00:00:00');
INSERT INTO public.quotation_details VALUES (457, 43, '芜湖第四人民医院（安定医院）', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 1, 1, 458, 458, 458, 'EANLOMO5HR1', '2024-07-16 00:00:00', '2024-07-16 00:00:00');
INSERT INTO public.quotation_details VALUES (458, 44, '北京新首钢园东南区1612-(774-779-784)地块项目', 'LS-NFX-BDA', '网讯云端终端直放站接入管理服务许可-远端站告警-远端区域状态更新', '和源通信', '套', 1, 0.35, 1500, 1500, 75000, 'HYWSRNB1', '2024-07-11 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (459, 44, '北京新首钢园东南区1612-(774-779-784)地块项目', 'ACC-CWT', '提供某一个项目上所有系统的工作管理，直观全面的反映系统的整体面貌和其中设备的布局，并可以跟踪每个设备及服务的进程。-告警处置模块-告警详情模块-维修情况和完成情况-设备位置地图模块，含一年的在线后台服', '和源通信', '个/年', 1, 0.35, 8333, 8333, 8333, 'HYWF0NA1', '2024-07-11 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (460, 44, '北京新首钢园东南区1612-(774-779-784)地块项目', 'ACC-NUT', '提供多单位的系统运维流程跟踪-告警管理和推送-故障设备快速定位-维护更新工作单', '和源通信', '个/年', 1, 0.35, 4167, 4167, 4167, 'HYWT0NA1', '2024-07-11 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (461, 44, '北京新首钢园东南区1612-(774-779-784)地块项目', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 1, 0.42, 142, 142, 66598, 'HYCCN34Y', '2024-07-11 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (462, 44, '北京新首钢园东南区1612-(774-779-784)地块项目', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '套', 1, 0.42, 142, 142, 63190, 'HYAIOCN4Y', '2024-07-11 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (463, 44, '北京新首钢园东南区1612-(774-779-784)地块项目', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 0.42, 4569, 4569, 18276, 'EDE1AU6xCZ1', '2024-07-11 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (464, 44, '北京新首钢园东南区1612-(774-779-784)地块项目', 'PNR2000', '频率范围：400-470MHz，锂电池 3700mAh', '和源通信', '套', 1, 0.42, 1333, 1333, 93310, 'HYTD4MA', '2024-07-11 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (465, 44, '北京新首钢园东南区1612-(774-779-784)地块项目', 'NFX_GATW', '用于本地系统设备管理和服务器的同步 -本地系统建立和配置 -设备驱动管理 -设备参数设置 -云同步 -设备报警管理', '和源通信', '套', 1, 0.35, 12500, 12500, 12500, 'HYWG0NB1', '2024-07-11 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (466, 44, '北京新首钢园东南区1612-(774-779-784)地块项目', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 1U机箱 功能： 网讯平台', '和源通信', '套', 1, 0.42, 11851, 11851, 225169, 'HYR3SI140', '2024-07-11 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (467, 44, '北京新首钢园东南区1612-(774-779-784)地块项目', 'RFS-400 LT/M', '频率范围：350-50MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 1, 0.42, 9876, 9876, 128388, 'HYR2SI030', '2024-07-11 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (468, 44, '北京新首钢园东南区1612-(774-779-784)地块项目', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 1, 0.42, 2320, 2320, 2320, 'EDE1BU2xCZ1', '2024-07-11 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (469, 44, '北京新首钢园东南区1612-(774-779-784)地块项目', 'E-FH400-4', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤8.5dB 接入端口数量：4 安装方式：机柜式 尺寸2U', '和源通信', '套', 1, 0.42, 6642, 6642, 6642, 'ECM1B042CZ1', '2024-07-11 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (470, 44, '北京新首钢园东南区1612-(774-779-784)地块项目', 'E-JF350/400-4', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤7.5dB 接入端口数量：4 安装方式：机柜式 尺寸1U', '和源通信', '套', 1, 0.42, 2493, 2493, 2493, 'EDE1BU4xCZ1', '2024-07-11 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (471, 44, '北京新首钢园东南区1612-(774-779-784)地块项目', 'LS-NFX-RPT', '网讯平台信道机接入管理服务许可 -信道资源管理 -呼叫类型繁忙度分析', '和源通信', '套', 1, 0.35, 2500, 2500, 7500, 'HYWSPNB1', '2024-07-11 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (472, 44, '北京新首钢园东南区1612-(774-779-784)地块项目', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 0.42, 4569, 4569, 18276, 'EDE1AD6xCZ1', '2024-07-11 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (473, 44, '北京新首钢园东南区1612-(774-779-784)地块项目', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W-网讯平台-数模兼容', '和源通信', '套', 1, 0.42, 13580, 13580, 67900, 'HYPSMXI40', '2024-07-11 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (474, 44, '北京新首钢园东南区1612-(774-779-784)地块项目', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 1, 0.42, 4569, 4569, 4569, 'ECM1B022CZ1', '2024-07-11 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (475, 44, '北京新首钢园东南区1612-(774-779-784)地块项目', 'LS-NFX-RAD', '网讯平台终端对讲机接入管理服务许可-对讲机ID呼叫管理-对讲机上下线管理-呼叫组繁忙度分析', '和源通信', '套', 1, 0.35, 180, 180, 27000, 'HYWSTNB1', '2024-07-11 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (476, 44, '北京新首钢园东南区1612-(774-779-784)地块项目', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 1, 0.42, 3753, 3753, 3753, 'EDULN4N1CZ1', '2024-07-11 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (477, 44, '北京新首钢园东南区1612-(774-779-784)地块项目', 'E-ANTD 400', '频率范围：400-430MHz 增益：2.5dBi 防护等级：IP65 辐射方向：定向 最大承载功率：50W 接头类型：N-Femade 特性：室外', '和源通信', '套', 1, 0.42, 354, 354, 14868, 'EAN2OFD2TE2', '2024-07-11 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (478, 45, '中江国际集团公司总部新办公园区', 'PNR2000', '频率范围：400-470MHz    锂电池 3700mAh', '和源通信', '套', 1, 1, 1333, 1333, 53320, 'HYTD4MA', '2024-06-22 00:00:00', '2024-06-22 00:00:00');
INSERT INTO public.quotation_details VALUES (479, 45, '中江国际集团公司总部新办公园区', 'FDPower400', '馈电功能模组    需搭配可扩展远端机;内置远端内向天馈提供电力;', '和源通信', '套', 1, 1, 1583, 1583, 14247, 'HYGF20000', '2024-06-22 00:00:00', '2024-06-22 00:00:00');
INSERT INTO public.quotation_details VALUES (480, 45, '中江国际集团公司总部新办公园区', 'NFX-LCN-OPETN', '支持对讲机在地图上人员的动态分布和查询功能', '和源通信', '套', 1, 1, 14600, 14600, 14600, 'HYWADHA1', '2024-06-22 00:00:00', '2024-06-22 00:00:00');
INSERT INTO public.quotation_details VALUES (481, 45, '中江国际集团公司总部新办公园区', 'NFX-PAT-OPETN', '支持携带对讲机完成在线的路线巡检记录及任务编排', '和源通信', '套', 1, 1, 22000, 22000, 22000, 'HYWACHA1', '2024-06-22 00:00:00', '2024-06-22 00:00:00');
INSERT INTO public.quotation_details VALUES (482, 45, '中江国际集团公司总部新办公园区', 'LS-NFX-RAD', '网讯平台终端对讲机接入管理服务许可-对讲机ID呼叫管理-对讲机上下线管理-呼叫组繁忙度分析', '和源通信', '套', 1, 1, 180, 180, 7200, 'HYWSTNB1', '2024-06-22 00:00:00', '2024-06-22 00:00:00');
INSERT INTO public.quotation_details VALUES (483, 45, '中江国际集团公司总部新办公园区', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 1, 1, 458, 458, 458, 'EANLOMO5HR1', '2024-06-22 00:00:00', '2024-06-22 00:00:00');
INSERT INTO public.quotation_details VALUES (484, 45, '中江国际集团公司总部新办公园区', 'MONT80', '曲臂长度50cm 材料：不锈钢 结构类型：L型结构', '国产', '套', 1, 1, 150, 150, 150, 'OBJANOTGR01', '2024-06-22 00:00:00', '2024-06-22 00:00:00');
INSERT INTO public.quotation_details VALUES (485, 45, '中江国际集团公司总部新办公园区', 'CA-23RS', '频率范围：0-1000MHz 功率：700W 阻抗：50Ω 接口（可选）：N', '钻石', '套', 1, 1, 133, 133, 133, 'OBJANOTHS01', '2024-06-22 00:00:00', '2024-06-22 00:00:00');
INSERT INTO public.quotation_details VALUES (486, 45, '中江国际集团公司总部新办公园区', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W-网讯平台-数模兼容', '和源通信', '套', 1, 1, 13580, 13580, 27160, 'HYPSMXI40', '2024-06-22 00:00:00', '2024-06-22 00:00:00');
INSERT INTO public.quotation_details VALUES (487, 45, '中江国际集团公司总部新办公园区', 'MAPD-2', '频率范围：88-866MHz 承载功率：100W 分路端口数量：2 防护等级：IP65 应用：馈电', '和源通信', '套', 1, 1, 208, 208, 6864, 'HYCDF24Y', '2024-06-22 00:00:00', '2024-06-22 00:00:00');
INSERT INTO public.quotation_details VALUES (488, 45, '中江国际集团公司总部新办公园区', 'NFX_GATW', '用于本地系统设备管理和服务器的同步 -本地系统建立和配置 -设备驱动管理 -设备参数设置 -云同步 -设备报警管理', '和源通信', '套', 1, 1, 12500, 12500, 12500, 'HYWG0NB1', '2024-06-22 00:00:00', '2024-06-22 00:00:00');
INSERT INTO public.quotation_details VALUES (489, 45, '中江国际集团公司总部新办公园区', 'ACC-CWT', '提供某一个项目上所有系统的工作管理    直观全面的反映系统的整体面貌和其中设备的布局    并可以跟踪每个设备及服务的进程。-告警处置模块-告警详情模块-维修情况和完成情况-设备位置地图模块    含一年的在线后台服', '和源通信', '个/年', 1, 1, 8333, 8333, 8333, 'HYWF0NA1', '2024-06-22 00:00:00', '2024-06-22 00:00:00');
INSERT INTO public.quotation_details VALUES (490, 45, '中江国际集团公司总部新办公园区', 'ACC-NUT', '提供多单位的系统运维流程跟踪-告警管理和推送-故障设备快速定位-维护更新工作单', '和源通信', '个/年', 1, 1, 4167, 4167, 4167, 'HYWT0NA1', '2024-06-22 00:00:00', '2024-06-22 00:00:00');
INSERT INTO public.quotation_details VALUES (491, 45, '中江国际集团公司总部新办公园区', 'LS-NFX-RPT', '网讯平台信道机接入管理服务许可 -信道资源管理 -呼叫类型繁忙度分析', '和源通信', '套', 1, 1, 2500, 2500, 5000, 'HYWSPNB1', '2024-06-22 00:00:00', '2024-06-22 00:00:00');
INSERT INTO public.quotation_details VALUES (492, 45, '中江国际集团公司总部新办公园区', 'LS-NFX-BDA', '网讯云端终端直放站接入管理服务许可-远端站告警-远端区域状态更新', '和源通信', '套', 1, 1, 1500, 1500, 13500, 'HYWSRNB1', '2024-06-22 00:00:00', '2024-06-22 00:00:00');
INSERT INTO public.quotation_details VALUES (493, 45, '中江国际集团公司总部新办公园区', 'MA12', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65 应用：指示灯 蓝牙信标', '和源通信', '套', 1, 1, 270, 270, 41310, 'HYAIOCB4Y', '2024-06-22 00:00:00', '2024-06-22 00:00:00');
INSERT INTO public.quotation_details VALUES (494, 45, '中江国际集团公司总部新办公园区', 'HCAAYZ -50-12', '尺寸：1/2＂    特性1：低烟无卤    特性2：阻燃    阻抗：50Ω', '浙江联创', '米', 1, 1, 13, 13, 101400, 'OZCH221035', '2024-06-22 00:00:00', '2024-06-22 00:00:00');
INSERT INTO public.quotation_details VALUES (495, 45, '中江国际集团公司总部新办公园区', 'N-J1/2', '尺寸：1/2＂    接口：N-J     外径：15.7mm    用途：同轴电缆连接器', '国产', '只', 1, 1, 15, 15, 9300, 'OCIN5JZALC1', '2024-06-22 00:00:00', '2024-06-22 00:00:00');
INSERT INTO public.quotation_details VALUES (496, 45, '中江国际集团公司总部新办公园区', 'N-50KK', '类型：N型    特性：双通    用途：连接器', '国产', '只', 1, 1, 15, 15, 2295, 'OCIN5KZALC1', '2024-06-22 00:00:00', '2024-06-22 00:00:00');
INSERT INTO public.quotation_details VALUES (497, 45, '中江国际集团公司总部新办公园区', 'NJ-3/NJ-3-1.5M', '接口：NJ转NJ    长度：1.5米    特性1：超柔    特性2：SYV-50-3', '国产', '根', 1, 1, 100, 100, 800, 'W000188', '2024-06-22 00:00:00', '2024-06-22 00:00:00');
INSERT INTO public.quotation_details VALUES (498, 45, '中江国际集团公司总部新办公园区', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4569, 4569, 4569, 'EDE1AU6xCZ1', '2024-06-22 00:00:00', '2024-06-22 00:00:00');
INSERT INTO public.quotation_details VALUES (499, 45, '中江国际集团公司总部新办公园区', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4569, 4569, 4569, 'EDE1AD6xCZ1', '2024-06-22 00:00:00', '2024-06-22 00:00:00');
INSERT INTO public.quotation_details VALUES (500, 45, '中江国际集团公司总部新办公园区', 'RFS-400 LT/M', '频率范围：350-50MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 1, 1, 9876, 9876, 29628, 'HYR2SI030', '2024-06-22 00:00:00', '2024-06-22 00:00:00');
INSERT INTO public.quotation_details VALUES (501, 45, '中江国际集团公司总部新办公园区', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 1U机箱 功能： 网讯平台', '和源通信', '套', 1, 1, 11851, 11851, 106659, 'HYR3SI140', '2024-06-22 00:00:00', '2024-06-22 00:00:00');
INSERT INTO public.quotation_details VALUES (502, 45, '中江国际集团公司总部新办公园区', 'MADC-6', '频率范围：351-470MHz 承载功率：100W 耦合规格：6dB 分路端口数量：2 防护等级：IP65 应用：馈电', '和源通信', '套', 1, 1, 246, 246, 27552, 'HYCCF34Y', '2024-06-22 00:00:00', '2024-06-22 00:00:00');
INSERT INTO public.quotation_details VALUES (503, 45, '中江国际集团公司总部新办公园区', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 1, 1, 4569, 4569, 4569, 'ECM1B022CZ1', '2024-06-22 00:00:00', '2024-06-22 00:00:00');
INSERT INTO public.quotation_details VALUES (504, 45, '中江国际集团公司总部新办公园区', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 1, 1, 2320, 2320, 2320, 'EDE1BU2xCZ1', '2024-06-22 00:00:00', '2024-06-22 00:00:00');
INSERT INTO public.quotation_details VALUES (505, 45, '中江国际集团公司总部新办公园区', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 1, 1, 3753, 3753, 3753, 'EDULN4N1CZ1', '2024-06-22 00:00:00', '2024-06-22 00:00:00');
INSERT INTO public.quotation_details VALUES (506, 46, '无锡锡东新城高铁商务区地下车行通道工程', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 0.45, 142, 142, 2272, 'HYCDN24Y', '2024-06-19 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (507, 46, '无锡锡东新城高铁商务区地下车行通道工程', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '', 1, 0.45, 2320, 2320, 2320, 'EDE1BU2xCZ1', '2024-06-19 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (508, 46, '无锡锡东新城高铁商务区地下车行通道工程', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 0.45, 4569, 4569, 4569, 'EDE1AU6xCZ1', '2024-06-19 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (509, 46, '无锡锡东新城高铁商务区地下车行通道工程', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 0.45, 4569, 4569, 4569, 'EDE1AD6xCZ1', '2024-06-19 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (510, 46, '无锡锡东新城高铁商务区地下车行通道工程', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '', 1, 0.45, 9876, 9876, 19752, 'HYR2SI030', '2024-06-19 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (511, 46, '无锡锡东新城高铁商务区地下车行通道工程', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 1U机箱 功能： 网讯平台', '和源通信', '', 1, 0.45, 11851, 11851, 94808, 'HYR3SI140', '2024-06-19 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (512, 46, '无锡锡东新城高铁商务区地下车行通道工程', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 0.45, 142, 142, 2556, 'HYCCN34Y', '2024-06-19 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (513, 46, '无锡锡东新城高铁商务区地下车行通道工程', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '', 1, 0.45, 4569, 4569, 4569, 'ECM1B022CZ1', '2024-06-19 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (514, 47, '徐州市睢宁县医院院区智能化工程项目', 'NJ/Q9-3 1.5米', '接口：NJ转BNC    长度：1.5米    用途：机柜内跳线', '国产', '根', 1, 1, 38, 38, 76, 'EJUMJK4315NJQJ', '2024-05-09 00:00:00', '2024-05-09 00:00:00');
INSERT INTO public.quotation_details VALUES (515, 47, '徐州市睢宁县医院院区智能化工程项目', 'PNR2000', '频率范围：400-470MHz    锂电池 3700mAh', '和源通信', '套', 1, 1, 1333, 1333, 53320, 'HYTD4MA', '2024-05-09 00:00:00', '2024-05-09 00:00:00');
INSERT INTO public.quotation_details VALUES (516, 47, '徐州市睢宁县医院院区智能化工程项目', 'CA-23RS', '频率范围：0-1000MHz 功率：700W 阻抗：50Ω 接口（可选）：N', '钻石', '套', 1, 1, 133, 133, 266, 'OBJANOTHS01', '2024-05-09 00:00:00', '2024-05-09 00:00:00');
INSERT INTO public.quotation_details VALUES (517, 47, '徐州市睢宁县医院院区智能化工程项目', 'HCAAYZ -50-12', '尺寸：1/2＂    特性1：低烟无卤    特性2：阻燃    阻抗：50Ω', '浙江联创', '米', 1, 1, 13, 13, 26000, 'OZCH221035', '2024-05-09 00:00:00', '2024-05-09 00:00:00');
INSERT INTO public.quotation_details VALUES (518, 47, '徐州市睢宁县医院院区智能化工程项目', 'N-J1/2', '尺寸：1/2＂    接口：N-J     外径：15.7mm    用途：同轴电缆连接器', '国产', '只', 1, 1, 15, 15, 600, 'OCIN5JZALC1', '2024-05-09 00:00:00', '2024-05-09 00:00:00');
INSERT INTO public.quotation_details VALUES (519, 47, '徐州市睢宁县医院院区智能化工程项目', 'N-50KK', '类型：N型    特性：双通    用途：连接器', '国产', '只', 1, 1, 15, 15, 1800, 'OCIN5KZALC1', '2024-05-09 00:00:00', '2024-05-09 00:00:00');
INSERT INTO public.quotation_details VALUES (520, 47, '徐州市睢宁县医院院区智能化工程项目', 'N-50JKW', '类型：N型    特性：直角弯    用途：连接器', '国产', '只', 1, 1, 15, 15, 600, 'OCIN5JWALC1', '2024-05-09 00:00:00', '2024-05-09 00:00:00');
INSERT INTO public.quotation_details VALUES (521, 47, '徐州市睢宁县医院院区智能化工程项目', 'E-JP50-7', '长度：0.5米 接口：NJ转NJ 用途：天线连接跳线', '国产', '根', 1, 1, 35, 35, 280, 'OISKHB1JLC1', '2024-05-09 00:00:00', '2024-05-09 00:00:00');
INSERT INTO public.quotation_details VALUES (522, 47, '徐州市睢宁县医院院区智能化工程项目', 'NJ/NJ-3 1.5米', '接口：NJ转NJ    长度：1.5米    用途：机柜内跳线', '国产', '根', 1, 1, 40, 40, 400, 'EJUMJK4315NJNJ', '2024-05-09 00:00:00', '2024-05-09 00:00:00');
INSERT INTO public.quotation_details VALUES (523, 47, '徐州市睢宁县医院院区智能化工程项目', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4569, 4569, 4569, 'EDE1AD6xCZ1', '2024-05-09 00:00:00', '2024-05-09 00:00:00');
INSERT INTO public.quotation_details VALUES (524, 47, '徐州市睢宁县医院院区智能化工程项目', 'RFS-400 LT/M', '频率范围：350-50MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 1, 1, 9876, 9876, 9876, 'HYR2SI030', '2024-05-09 00:00:00', '2024-05-09 00:00:00');
INSERT INTO public.quotation_details VALUES (525, 47, '徐州市睢宁县医院院区智能化工程项目', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 1U机箱 功能： 网讯平台', '和源通信', '套', 1, 1, 11851, 11851, 23702, 'HYR3SI140', '2024-05-09 00:00:00', '2024-05-09 00:00:00');
INSERT INTO public.quotation_details VALUES (526, 47, '徐州市睢宁县医院院区智能化工程项目', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 1, 1, 142, 142, 5396, 'HYCCN34Y', '2024-05-09 00:00:00', '2024-05-09 00:00:00');
INSERT INTO public.quotation_details VALUES (527, 47, '徐州市睢宁县医院院区智能化工程项目', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '套', 1, 1, 142, 142, 5396, 'HYAIOCN4Y', '2024-05-09 00:00:00', '2024-05-09 00:00:00');
INSERT INTO public.quotation_details VALUES (528, 47, '徐州市睢宁县医院院区智能化工程项目', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 1, 1, 458, 458, 916, 'EANLOMO5HR1', '2024-05-09 00:00:00', '2024-05-09 00:00:00');
INSERT INTO public.quotation_details VALUES (529, 47, '徐州市睢宁县医院院区智能化工程项目', 'MONT80', '曲臂长度50cm 材料：不锈钢 结构类型：L型结构', '国产', '套', 1, 1, 150, 150, 300, 'OBJANOTGR01', '2024-05-09 00:00:00', '2024-05-09 00:00:00');
INSERT INTO public.quotation_details VALUES (530, 47, '徐州市睢宁县医院院区智能化工程项目', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W-网讯平台-数模兼容', '和源通信', '套', 1, 1, 13580, 13580, 27160, 'HYPSMXI40', '2024-05-09 00:00:00', '2024-05-09 00:00:00');
INSERT INTO public.quotation_details VALUES (531, 47, '徐州市睢宁县医院院区智能化工程项目', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 1, 1, 4569, 4569, 4569, 'ECM1B022CZ1', '2024-05-09 00:00:00', '2024-05-09 00:00:00');
INSERT INTO public.quotation_details VALUES (532, 47, '徐州市睢宁县医院院区智能化工程项目', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 1, 1, 2320, 2320, 2320, 'EDE1BU2xCZ1', '2024-05-09 00:00:00', '2024-05-09 00:00:00');
INSERT INTO public.quotation_details VALUES (533, 47, '徐州市睢宁县医院院区智能化工程项目', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 1, 1, 3753, 3753, 3753, 'EDULN4N1CZ1', '2024-05-09 00:00:00', '2024-05-09 00:00:00');
INSERT INTO public.quotation_details VALUES (534, 47, '徐州市睢宁县医院院区智能化工程项目', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4569, 4569, 4569, 'EDE1AU6xCZ1', '2024-05-09 00:00:00', '2024-05-09 00:00:00');
INSERT INTO public.quotation_details VALUES (535, 48, '江苏省中医院牛首山分院一期项目智能化系统工程', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '', 1, 0.45, 3753, 3753, 3753, 'EDULN4N1CZ1', '2024-04-25 00:00:00', '2025-01-04 00:00:00');
INSERT INTO public.quotation_details VALUES (536, 48, '江苏省中医院牛首山分院一期项目智能化系统工程', 'E-BDA400B LT', '频率范围：410~414/420~424 , 链路带宽 4MHz, 最大射频输出功率 33dBm(2W)', '和源通信', '', 1, 0.45, 8396, 8396, 8396, 'HYR1SN140', '2024-04-25 00:00:00', '2025-01-04 00:00:00');
INSERT INTO public.quotation_details VALUES (537, 48, '江苏省中医院牛首山分院一期项目智能化系统工程', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 0.45, 142, 142, 6674, 'HYCCN34Y', '2024-04-25 00:00:00', '2025-01-04 00:00:00');
INSERT INTO public.quotation_details VALUES (538, 48, '江苏省中医院牛首山分院一期项目智能化系统工程', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '', 1, 0.45, 142, 142, 6816, 'HYAIOCN4Y', '2024-04-25 00:00:00', '2025-01-04 00:00:00');
INSERT INTO public.quotation_details VALUES (539, 48, '江苏省中医院牛首山分院一期项目智能化系统工程', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '', 1, 0.45, 4569, 4569, 4569, 'ECM1B022CZ1', '2024-04-25 00:00:00', '2025-01-04 00:00:00');
INSERT INTO public.quotation_details VALUES (540, 48, '江苏省中医院牛首山分院一期项目智能化系统工程', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '', 1, 0.45, 2320, 2320, 2320, 'EDE1BU2xCZ1', '2024-04-25 00:00:00', '2025-01-04 00:00:00');
INSERT INTO public.quotation_details VALUES (541, 49, '南通昱景希尔顿酒店', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 1, 0.45, 4569, 4569, 4569, 'ECM1B022CZ1', '2024-04-12 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (542, 49, '南通昱景希尔顿酒店', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 1, 0.45, 2320, 2320, 2320, 'EDE1BU2xCZ1', '2024-04-12 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (543, 49, '南通昱景希尔顿酒店', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 1, 0.45, 3753, 3753, 3753, 'EDULN4N1CZ1', '2024-04-12 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (544, 49, '南通昱景希尔顿酒店', 'E-BDA400B LT', '频率范围：410-414/420-424 , 链路带宽 4MHz, 最大射频输出功率 33dBm(2W)', '和源通信', '套', 1, 0.45, 8396, 8396, 8396, 'HYR1SN140', '2024-04-12 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (545, 49, '南通昱景希尔顿酒店', 'EVDC-6 LT', '频率范围：351-470MHz 承载功率：100W 耦合规格：6dB 分路端口数量：2 防护等级：IP65 应用：馈电', '和源通信', '套', 1, 0.45, 142, 142, 12780, 'HYCCN34Y', '2024-04-12 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (546, 49, '南通昱景希尔顿酒店', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '套', 1, 0.45, 142, 142, 12780, 'HYAIOCN4Y', '2024-04-12 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (547, 49, '南通昱景希尔顿酒店', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 1, 0.45, 458, 458, 458, 'EANLOMO5HR1', '2024-04-12 00:00:00', '2024-12-29 00:00:00');
INSERT INTO public.quotation_details VALUES (548, 50, '常州建科股份大楼', 'ST/FC  24口', '尺寸类型：标准尺寸FC口,端口数：24口,产品类型：机架式,特性：含法兰头,不含配套尾纤', '国产', '套', 1, 1, 430, 430, 430, 'EDFWYFC24W', '2024-02-29 00:00:00', '2024-02-29 00:00:00');
INSERT INTO public.quotation_details VALUES (549, 50, '常州建科股份大楼', 'ST/FC  4口', '尺寸类型：标准尺寸FC口,端口数：4口,产品类型：墙上型,特性：含法兰头,不含配套尾纤', '国产', '套', 1, 1, 163, 163, 1304, 'EDFWYFC04O', '2024-02-29 00:00:00', '2024-02-29 00:00:00');
INSERT INTO public.quotation_details VALUES (550, 50, '常州建科股份大楼', '单模单芯 FC-FC  5米', '光纤类型：单模,光缆类型：单芯,接口类型：FC/PC-FC/PC,长度：5米', '国产', '根', 1, 1, 30, 30, 480, 'EJUWY05A4001', '2024-02-29 00:00:00', '2024-02-29 00:00:00');
INSERT INTO public.quotation_details VALUES (551, 50, '常州建科股份大楼', 'N-50KK', '类型：N型,特性：双通,用途：连接器', '国产', '只', 1, 1, 15, 15, 600, 'OCIN5KZALC1', '2024-02-29 00:00:00', '2024-02-29 00:00:00');
INSERT INTO public.quotation_details VALUES (552, 50, '常州建科股份大楼', 'N-50JKW', '类型：N型,特性：直角弯,用途：连接器', '国产', '只', 1, 1, 15, 15, 1500, 'OCIN5JWALC1', '2024-02-29 00:00:00', '2024-02-29 00:00:00');
INSERT INTO public.quotation_details VALUES (553, 50, '常州建科股份大楼', 'NJ/NJ-3 1.5米', '接口：NJ转NJ,长度：1.5米,用途：机柜内跳线', '国产', '根', 1, 1, 40, 40, 400, 'EJUMJK4315NJNJ', '2024-02-29 00:00:00', '2024-02-29 00:00:00');
INSERT INTO public.quotation_details VALUES (554, 50, '常州建科股份大楼', 'NJ/Q9-3 1.5米', '接口：NJ转BNC,长度：1.5米,用途：机柜内跳线', '国产', '根', 1, 1, 38, 38, 76, 'EJUMJK4315NJQJ', '2024-02-29 00:00:00', '2024-02-29 00:00:00');
INSERT INTO public.quotation_details VALUES (555, 50, '常州建科股份大楼', 'E-JP50-7', '长度：0.5米 接口：NJ转NJ 用途：天线连接跳线', '国产', '根', 1, 1, 35, 35, 1120, 'OISKHB1JLC1', '2024-02-29 00:00:00', '2024-02-29 00:00:00');
INSERT INTO public.quotation_details VALUES (556, 50, '常州建科股份大楼', 'GYXTH-4B1 4芯', '芯数：4芯,钢带：铠装,特性：单模,低烟无卤阻燃', '国产', '米', 1, 1, 9, 9, 7200, 'ECAWYGYXTH0401', '2024-02-29 00:00:00', '2024-02-29 00:00:00');
INSERT INTO public.quotation_details VALUES (557, 50, '常州建科股份大楼', 'CA-23RS', '频率范围：0-1000MHz 功率：700W 阻抗：50Ω 接口（可选）：N', '钻石', '套', 1, 1, 133, 133, 133, 'OBJANOTHS01', '2024-02-29 00:00:00', '2024-02-29 00:00:00');
INSERT INTO public.quotation_details VALUES (558, 50, '常州建科股份大楼', 'MONT80', '曲臂长度50cm 材料：不锈钢 结构类型：L型结构', '国产', '套', 1, 1, 150, 150, 150, 'OBJANOTGR01', '2024-02-29 00:00:00', '2024-02-29 00:00:00');
INSERT INTO public.quotation_details VALUES (559, 50, '常州建科股份大楼', 'PNR2000', '频率范围：400-470MHz，锂电池 3700mAh', '和源通信', '套', 1, 1, 1333, 1333, 53320, 'HYTD4MA', '2024-02-29 00:00:00', '2024-02-29 00:00:00');
INSERT INTO public.quotation_details VALUES (560, 50, '常州建科股份大楼', 'HCAAYZ -50-12', '尺寸：1/2＂,特性1：低烟无卤,特性2：阻燃,阻抗：50Ω', '浙江联创', '米', 1, 1, 13, 13, 84500, 'OZCH221035', '2024-02-29 00:00:00', '2024-02-29 00:00:00');
INSERT INTO public.quotation_details VALUES (561, 50, '常州建科股份大楼', 'N-J1/2', '尺寸：1/2＂,接口：N-J, 外径：15.7mm,用途：同轴电缆连接器', '国产', '只', 1, 1, 15, 15, 9600, 'OCIN5JZALC1', '2024-02-29 00:00:00', '2024-02-29 00:00:00');
INSERT INTO public.quotation_details VALUES (562, 50, '常州建科股份大楼', 'RFS-400 LT/M', '频率范围：350-430MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 1, 1, 9876, 9876, 19752, 'HYR2SI030', '2024-02-29 00:00:00', '2024-02-29 00:00:00');
INSERT INTO public.quotation_details VALUES (563, 50, '常州建科股份大楼', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 1U机箱 功能： 网讯平台', '和源通信', '套', 1, 1, 11851, 11851, 94808, 'HYR3SI140', '2024-02-29 00:00:00', '2024-02-29 00:00:00');
INSERT INTO public.quotation_details VALUES (564, 50, '常州建科股份大楼', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 1, 1, 142, 142, 7668, 'HYCDN24Y', '2024-02-29 00:00:00', '2024-02-29 00:00:00');
INSERT INTO public.quotation_details VALUES (565, 50, '常州建科股份大楼', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 1, 1, 142, 142, 14910, 'HYCCN34Y', '2024-02-29 00:00:00', '2024-02-29 00:00:00');
INSERT INTO public.quotation_details VALUES (566, 50, '常州建科股份大楼', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '套', 1, 1, 142, 142, 22436, 'HYAIOCN4Y', '2024-02-29 00:00:00', '2024-02-29 00:00:00');
INSERT INTO public.quotation_details VALUES (567, 50, '常州建科股份大楼', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 1, 1, 458, 458, 458, 'EANLOMO5HR1', '2024-02-29 00:00:00', '2024-02-29 00:00:00');
INSERT INTO public.quotation_details VALUES (568, 50, '常州建科股份大楼', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W-网讯平台-数模兼容', '和源通信', '套', 1, 1, 13580, 13580, 27160, 'HYPSMXI40', '2024-02-29 00:00:00', '2024-02-29 00:00:00');
INSERT INTO public.quotation_details VALUES (569, 50, '常州建科股份大楼', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 1, 1, 4569, 4569, 4569, 'ECM1B022CZ1', '2024-02-29 00:00:00', '2024-02-29 00:00:00');
INSERT INTO public.quotation_details VALUES (570, 50, '常州建科股份大楼', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 1, 1, 2320, 2320, 2320, 'EDE1BU2xCZ1', '2024-02-29 00:00:00', '2024-02-29 00:00:00');
INSERT INTO public.quotation_details VALUES (571, 50, '常州建科股份大楼', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 1, 1, 3753, 3753, 3753, 'EDULN4N1CZ1', '2024-02-29 00:00:00', '2024-02-29 00:00:00');
INSERT INTO public.quotation_details VALUES (572, 50, '常州建科股份大楼', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4569, 4569, 4569, 'EDE1AU6xCZ1', '2024-02-29 00:00:00', '2024-02-29 00:00:00');
INSERT INTO public.quotation_details VALUES (573, 50, '常州建科股份大楼', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 1, 1, 4569, 4569, 4569, 'EDE1AD6xCZ1', '2024-02-29 00:00:00', '2024-02-29 00:00:00');
INSERT INTO public.quotation_details VALUES (574, 51, '南京惠民路隧道项目', 'DRFT-BDA88/M', '频率范围：87-108MHz；带宽：≤21M；输出：10W；数字型 功能：触摸屏/网讯平台 扩展：馈电', '和源通信', '', 1, 1, 45833, 45833, 183332, 'HYR3DI300', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (575, 51, '南京惠民路隧道项目', 'DRFS-88/M', '频率范围：87-108MHz 远端携带：32 数字型 功能：触摸屏/网讯平台', '和源通信', '', 1, 1, 25000, 25000, 25000, 'HYR2DI000', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (576, 51, '南京惠民路隧道项目', 'E-FHP2000-3', '频率范围：87-108/351-366/410-424MHz 单端口承载功率：50W 插入损耗：≤2.0dB 接入端口数量：3 安装方式：机柜式 尺寸：2U', '和源通信', '', 1, 1, 16667, 16667, 66668, 'ECM5BB32CZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (577, 51, '南京惠民路隧道项目', 'E-FHP2000-2', '频率范围：351-366/372-386MHz 单端口承载功率：50W 插入损耗：≤2.0dB 接入端口数量：2', '和源通信', '', 1, 1, 6691, 6691, 66910, 'HYMPC2A30', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (578, 51, '南京惠民路隧道项目', 'DRFS-400/M', '频率范围：410-414/420-424MHz 远端携带：32 数字型 功能：触摸屏/网讯平台', '和源通信', '', 1, 1, 25000, 25000, 100000, 'HYR2DI040', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (579, 51, '南京惠民路隧道项目', 'DRFS-400/M', '频率范围：410-414/420-424MHz 远端携带：32 数字型 功能：触摸屏/网讯平台', '和源通信', '', 1, 1, 25000, 25000, 25000, 'HYR2DI040', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (580, 51, '南京惠民路隧道项目', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AD6xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (581, 51, '南京惠民路隧道项目', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AU6xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (582, 51, '南京惠民路隧道项目', 'E-SGQ400D', '频率范围：410-414/420-424MHz 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 隔离方式：带通 工作带宽：4M 安装方式：机柜式 尺寸：2U', '和源通信', '', 1, 1, 7876, 7876, 7876, 'EDULB4H1CZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (583, 51, '南京惠民路隧道项目', 'PNR2000', '频率范围：400~470MHz，锂电池 3700mAh', '和源通信', '', 1, 1, 1333, 1333, 13330, 'HYTD4MA', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (584, 51, '南京惠民路隧道项目', 'E-ANTD 400', '频率范围：400-430MHz 增益：2.5dBi 防护等级：IP65 辐射方向：定向 最大承载功率：50W 接头类型：N-Femade 特性：室外', '和源通信', '', 1, 1, 354, 354, 2124, 'EAN2OFD2TE2', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (585, 51, '南京惠民路隧道项目', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 1988, 'HYCCN34Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (586, 51, '南京惠民路隧道项目', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 426, 'HYCDN24Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (587, 51, '南京惠民路隧道项目', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '', 1, 1, 142, 142, 1278, 'HYAIOCN4Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (588, 51, '南京惠民路隧道项目', 'DRFT-BDA310/M', '频率范围：351-356/361-366MHz；带宽：≤21M；输出：10W；数字型 功能：触摸屏/网讯平台 扩展：馈电', '和源通信', '', 1, 1, 47917, 47917, 383336, 'HYR3DI330', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (589, 51, '南京惠民路隧道项目', 'DRFS-300/M', '频率范围：350MHz 远端携带：32 数字型 功能：触摸屏/网讯平台', '和源通信', '', 1, 1, 25000, 25000, 50000, 'HYR2DI030', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (590, 51, '南京惠民路隧道项目', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AD6xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (591, 51, '南京惠民路隧道项目', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AU6xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (592, 51, '南京惠民路隧道项目', 'MarkNET3000', '频率范围：351-356/361-366MHz 带宽：≤5M ， -基站控制器 -基站交换机 -三载波数模兼容信道 -三载波合路平台，合路输出：10W -功能：网讯平台', '和源通信', '', 1, 1, 125000, 125000, 125000, 'HYBC3XI30', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (593, 52, '南京建宁西路过江隧道项目', 'ACC-CWT', '提供某一个项目上所有系统的工作管理，直观全面的反映系统的整体面貌和其中设备的布局，并可以跟踪每个设备及服务的进程。-告警处置模块-告警详情模块-维修情况和完成情况-设备位置地图模块，含一年的在线后台服', '和源通信', '', 1, 1, 8333, 8333, 8333, 'HYWF0NA1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (594, 52, '南京建宁西路过江隧道项目', 'PNR2000', '频率范围：400~470MHz，锂电池 3700mAh', '和源通信', '', 1, 1, 1333, 1333, 26660, 'HYTD4MA', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (595, 52, '南京建宁西路过江隧道项目', 'DRFS-88/M', '频率范围：87-108MHz 远端携带：32 数字型 功能：触摸屏/网讯平台', '和源通信', '', 1, 1, 25000, 25000, 25000, 'HYR2DI000', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (596, 52, '南京建宁西路过江隧道项目', 'DRFT-BDA88/M', '频率范围：87-108MHz；带宽：≤21M；输出：10W；数字型 功能：触摸屏/网讯平台 扩展：馈电', '和源通信', '', 1, 1, 45833, 45833, 458330, 'HYR3DI300', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (597, 52, '南京建宁西路过江隧道项目', 'MarkNET3000', '频率范围：351-356/361-366MHz 带宽：≤5M ， -基站控制器 -基站交换机 -三载波数模兼容信道 -三载波合路平台，合路输出：10W -功能：网讯平台', '和源通信', '', 1, 1, 125000, 125000, 250000, 'HYBC3XI30', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (598, 52, '南京建宁西路过江隧道项目', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 9138, 'EDE1AU6xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (599, 52, '南京建宁西路过江隧道项目', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 9138, 'EDE1AD6xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (600, 52, '南京建宁西路过江隧道项目', 'DRFS-300/M', '频率范围：350MHz 远端携带：32 数字型 功能：触摸屏/网讯平台', '和源通信', '', 1, 1, 25000, 25000, 150000, 'HYR2DI030', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (601, 52, '南京建宁西路过江隧道项目', 'DRFT-BDA310/M', '频率范围：351-356/361-366MHz；带宽：≤21M；输出：10W；数字型 功能：触摸屏/网讯平台 扩展：馈电', '和源通信', '', 1, 1, 47917, 47917, 958340, 'HYR3DI330', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (602, 52, '南京建宁西路过江隧道项目', 'E-ANTO LT', '频率范围：88-430MHz 承载功率：50W 性能：室内全向 天线增益：0dBi', '和源通信', '', 1, 1, 209, 209, 1463, 'HYAIOCN1N', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (603, 52, '南京建宁西路过江隧道项目', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 426, 'HYCDN24Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (604, 52, '南京建宁西路过江隧道项目', 'EVDC-6 LT', '频率范围：150-170MHz，承载功率：100W;耦合规格：6dB', '和源通信', '', 1, 1, 184, 184, 1288, 'HYCCN31Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (605, 52, '南京建宁西路过江隧道项目', 'E-ANTD 400', '频率范围：400-430MHz 增益：2.5dBi 防护等级：IP65 辐射方向：定向 最大承载功率：50W 接头类型：N-Femade 特性：室外', '和源通信', '', 1, 1, 354, 354, 708, 'EAN2OFD2TE2', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (606, 52, '南京建宁西路过江隧道项目', 'NFX_GATW', '用于本地系统设备管理和服务器的同步 -本地系统建立和配置 -设备驱动管理 -设备参数设置 -云同步 -设备报警管理', '和源通信', '', 1, 1, 12500, 12500, 12500, 'HYWG0NB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (607, 52, '南京建宁西路过江隧道项目', 'NFX_MAST_OPETN', '-账户创建和访问管理-设备数据和系统数据的存储和恢复-产品库数据-系统拓扑和设备位置显示和管理-系统资源统计和告警分析推送-系统工作台主次账号一个-20个远端站授权，4个信道机授权，100个终端授权', '和源通信', '', 1, 1, 105000, 105000, 105000, 'HYWP0NC1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (608, 52, '南京建宁西路过江隧道项目', 'E-SGQ400D', '频率范围：410-414/420-424MHz 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 隔离方式：带通 工作带宽：4M 安装方式：机柜式 尺寸：2U', '和源通信', '', 1, 1, 7876, 7876, 7876, 'EDULB4H1CZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (609, 52, '南京建宁西路过江隧道项目', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AU6xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (610, 52, '南京建宁西路过江隧道项目', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AD6xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (611, 52, '南京建宁西路过江隧道项目', 'DRFS-400/M', '频率范围：410-414/420-424MHz 远端携带：32 数字型 功能：触摸屏/网讯平台', '和源通信', '', 1, 1, 25000, 25000, 25000, 'HYR2DI040', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (612, 52, '南京建宁西路过江隧道项目', 'DRFT-BDA410/M', '频率范围：410-414/420-424MHz 数字带宽：≤4M 输出：10W 数字型 功能：触摸屏/网讯平台 扩展：馈电', '和源通信', '', 1, 1, 47917, 47917, 479170, 'HYR3DI340', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (613, 52, '南京建宁西路过江隧道项目', 'E-FHP2000-2', '频率范围：351-366/372-386MHz 单端口承载功率：50W 插入损耗：≤2.0dB 接入端口数量：2', '和源通信', '', 1, 1, 6691, 6691, 66910, 'HYMPC2A30', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (614, 52, '南京建宁西路过江隧道项目', 'E-FHP2000-3', '频率范围：87-108/351-366/410-424MHz 单端口承载功率：50W 插入损耗：≤2.0dB 接入端口数量：3 安装方式：机柜式 尺寸：2U', '和源通信', '', 1, 1, 16667, 16667, 166670, 'ECM5BB32CZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (615, 53, '南京市鼓楼区2019G61地块项目（中信泰富江苏总部）', 'LS-NFX-BDA', '网讯云端终端直放站接入管理服务许可-远端站告警-远端区域状态更新', '和源通信', '', 1, 1, 1500, 1500, 19500, 'HYWSRNB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (616, 53, '南京市鼓楼区2019G61地块项目（中信泰富江苏总部）', 'LS-NFX-RAD', '网讯平台终端对讲机接入管理服务许可-对讲机ID呼叫管理-对讲机上下线管理-呼叫组繁忙度分析', '和源通信', '', 1, 1, 180, 180, 10800, 'HYWSTNB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (617, 53, '南京市鼓楼区2019G61地块项目（中信泰富江苏总部）', 'ACC-NUT', '提供多单位的系统运维流程跟踪-告警管理和推送-故障设备快速定位-维护更新工作单', '和源通信', '', 1, 1, 4167, 4167, 4167, 'HYWT0NA1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (618, 53, '南京市鼓楼区2019G61地块项目（中信泰富江苏总部）', 'Mark1000 MAX VHF（停售）', '频率范围：136~174MHz-网讯平台-数模兼容', '和源通信', '', 1, 1, 14580, 14580, 43740, 'HYPSMXI10', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (619, 53, '南京市鼓楼区2019G61地块项目（中信泰富江苏总部）', 'E-FH150-4', '频率范围：163-167MHz 单端口承载功率：50W;插入损耗：≤7.0dB接入端口数量：4;安装方式：机柜式;', '和源通信', '', 1, 1, 11111, 11111, 11111, 'HYMFC4A10', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (620, 53, '南京市鼓楼区2019G61地块项目（中信泰富江苏总部）', 'E-JF150-4', '频率范围：130-170MHz 单端口承载功率：1W;插入损耗：≤7.0dB接入端口数量：4;安装方式：机柜式;', '和源通信', '', 1, 1, 2913, 2913, 2913, 'HYMJC4010', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (621, 53, '南京市鼓楼区2019G61地块项目（中信泰富江苏总部）', 'R-EVDC-BLST-D', '频率范围：87-170MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4938, 4938, 4938, 'HYMBC6A1D', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (622, 53, '南京市鼓楼区2019G61地块项目（中信泰富江苏总部）', 'R-EVDC-BLST-U', '频率范围：87-170MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4938, 4938, 4938, 'HYMBC6A1U', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (623, 53, '南京市鼓楼区2019G61地块项目（中信泰富江苏总部）', 'RFS-100 LT/M', '频率范围：150~170MHz 带宽：≤20M 远端携带：4 功能： 正面状态灯/网讯平台', '和源通信', '', 1, 1, 8958, 8958, 35832, 'HYR2SI010', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (624, 53, '南京市鼓楼区2019G61地块项目（中信泰富江苏总部）', 'RFT-BDA110 LT/M', '频率范围：157-161/163-167MHz 带宽：≤4M 输出：10W 功能： 正面状态灯/网讯平台', '和源通信', '', 1, 1, 25000, 25000, 325000, 'HYR3SI310', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (625, 53, '南京市鼓楼区2019G61地块项目（中信泰富江苏总部）', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 8520, 'HYCDN24Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (626, 53, '南京市鼓楼区2019G61地块项目（中信泰富江苏总部）', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 28400, 'HYCCN34Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (627, 53, '南京市鼓楼区2019G61地块项目（中信泰富江苏总部）', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '', 1, 1, 142, 142, 36778, 'HYAIOCN4Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (628, 53, '南京市鼓楼区2019G61地块项目（中信泰富江苏总部）', 'PNR2000', '频率范围：150~170MHz，锂电池 3700mAh', '和源通信', '', 1, 1, 1333, 1333, 79980, 'HYTD1MA', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (629, 53, '南京市鼓楼区2019G61地块项目（中信泰富江苏总部）', 'ACC-CWT', '提供某一个项目上所有系统的工作管理，直观全面的反映系统的整体面貌和其中设备的布局，并可以跟踪每个设备及服务的进程。-告警处置模块-告警详情模块-维修情况和完成情况-设备位置地图模块，含一年的在线后台服', '和源通信', '', 1, 1, 8333, 8333, 8333, 'HYWF0NA1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (630, 53, '南京市鼓楼区2019G61地块项目（中信泰富江苏总部）', 'NFX_GATW', '用于本地系统设备管理和服务器的同步 -本地系统建立和配置 -设备驱动管理 -设备参数设置 -云同步 -设备报警管理', '和源通信', '', 1, 1, 12500, 12500, 12500, 'HYWG0NB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (631, 53, '南京市鼓楼区2019G61地块项目（中信泰富江苏总部）', 'LS-NFX-RPT', '网讯平台信道机接入管理服务许可 -信道资源管理 -呼叫类型繁忙度分析', '和源通信', '', 1, 1, 2500, 2500, 7500, 'HYWSPNB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (632, 54, '阳澄湖健康颐养酒店', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AD6xCZ1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (633, 54, '阳澄湖健康颐养酒店', 'PNR2000', '频率范围：400~470MHz，锂电池 3700mAh', '和源通信', '', 1, 1, 1333, 1333, 53320, 'HYTD4MA', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (634, 54, '阳澄湖健康颐养酒店', 'ACC-NUT', '提供多单位的系统运维流程跟踪-告警管理和推送-故障设备快速定位-维护更新工作单', '和源通信', '', 1, 1, 4167, 4167, 4167, 'HYWT0NA1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (635, 54, '阳澄湖健康颐养酒店', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '', 1, 1, 13580, 13580, 27160, 'HYPSMXI40', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (636, 54, '阳澄湖健康颐养酒店', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'ECM1B022CZ1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (637, 54, '阳澄湖健康颐养酒店', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '', 1, 1, 2320, 2320, 2320, 'EDE1BU2xCZ1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (638, 54, '阳澄湖健康颐养酒店', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '', 1, 1, 3753, 3753, 3753, 'EDULN4N1CZ1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (639, 54, '阳澄湖健康颐养酒店', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AU6xCZ1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (640, 54, '阳澄湖健康颐养酒店', 'NFX_GATW', '用于本地系统设备管理和服务器的同步 -本地系统建立和配置 -设备驱动管理 -设备参数设置 -云同步 -设备报警管理', '和源通信', '', 1, 1, 12500, 12500, 12500, 'HYWG0NB1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (641, 54, '阳澄湖健康颐养酒店', 'LS-NFX-RAD', '网讯平台终端对讲机接入管理服务许可-对讲机ID呼叫管理-对讲机上下线管理-呼叫组繁忙度分析', '和源通信', '', 1, 1, 180, 180, 7200, 'HYWSTNB1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (642, 54, '阳澄湖健康颐养酒店', 'LS-NFX-BDA', '网讯云端终端直放站接入管理服务许可-远端站告警-远端区域状态更新', '和源通信', '', 1, 1, 1500, 1500, 7500, 'HYWSRNB1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (643, 54, '阳澄湖健康颐养酒店', 'LS-NFX-RPT', '网讯平台信道机接入管理服务许可 -信道资源管理 -呼叫类型繁忙度分析', '和源通信', '', 1, 1, 2500, 2500, 5000, 'HYWSPNB1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (644, 54, '阳澄湖健康颐养酒店', 'ACC-CWT', '提供某一个项目上所有系统的工作管理，直观全面的反映系统的整体面貌和其中设备的布局，并可以跟踪每个设备及服务的进程。-告警处置模块-告警详情模块-维修情况和完成情况-设备位置地图模块，含一年的在线后台服', '和源通信', '', 1, 1, 8333, 8333, 8333, 'HYWF0NA1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (645, 54, '阳澄湖健康颐养酒店', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 1U机箱 功能： 网讯平台', '和源通信', '套', 1, 1, 11851, 11851, 71106, 'HYR3SI140', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (646, 54, '阳澄湖健康颐养酒店', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 2272, 'HYCDN24Y', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (647, 54, '阳澄湖健康颐养酒店', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 15620, 'HYCCN34Y', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (648, 54, '阳澄湖健康颐养酒店', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '', 1, 1, 142, 142, 17892, 'HYAIOCN4Y', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (649, 54, '阳澄湖健康颐养酒店', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '', 1, 1, 458, 458, 458, 'EANLOMO5HR1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (650, 54, '阳澄湖健康颐养酒店', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '', 1, 1, 9876, 9876, 19752, 'HYR2SI030', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (651, 55, '武汉阳逻国际冷链产业园区项目', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'ECM1B022CZ1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (652, 55, '武汉阳逻国际冷链产业园区项目', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '', 1, 1, 2320, 2320, 2320, 'EDE1BU2xCZ1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (653, 55, '武汉阳逻国际冷链产业园区项目', 'PNR2000', '频率范围：400~470MHz，锂电池 3700mAh', '和源通信', '', 1, 1, 1333, 1333, 26660, 'HYTD4MA', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (654, 55, '武汉阳逻国际冷链产业园区项目', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 10792, 'HYCCN34Y', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (655, 55, '武汉阳逻国际冷链产业园区项目', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '', 1, 1, 142, 142, 11218, 'HYAIOCN4Y', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (656, 55, '武汉阳逻国际冷链产业园区项目', 'E-ANTD 400', '频率范围：400-430MHz 增益：2.5dBi 防护等级：IP65 辐射方向：定向 最大承载功率：50W 接头类型：N-Femade 特性：室外', '和源通信', '', 1, 1, 354, 354, 708, 'EAN2OFD2TE2', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (657, 55, '武汉阳逻国际冷链产业园区项目', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '', 1, 1, 13580, 13580, 27160, 'HYPSMXI40', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (658, 55, '武汉阳逻国际冷链产业园区项目', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '', 1, 1, 3753, 3753, 3753, 'EDULN4N1CZ1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (659, 55, '武汉阳逻国际冷链产业园区项目', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AU6xCZ1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (660, 55, '武汉阳逻国际冷链产业园区项目', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AD6xCZ1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (661, 55, '武汉阳逻国际冷链产业园区项目', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '', 1, 1, 9876, 9876, 9876, 'HYR2SI030', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (662, 55, '武汉阳逻国际冷链产业园区项目', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 1U机箱 功能： 网讯平台', '和源通信', '', 1, 1, 11851, 11851, 47404, 'HYR3SI140', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (663, 56, '无锡国家软件园五期项目', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 1U机箱 功能： 网讯平台', '和源通信', '', 1, 1, 11851, 11851, 47404, 'HYR3SI140', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (664, 56, '无锡国家软件园五期项目', 'PNR2000', '频率范围：400~470MHz，锂电池 3700mAh', '和源通信', '', 1, 1, 1333, 1333, 39990, 'HYTD4MA', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (665, 56, '无锡国家软件园五期项目', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 53960, 'HYCCN34Y', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (666, 56, '无锡国家软件园五期项目', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '', 1, 1, 142, 142, 53392, 'HYAIOCN4Y', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (667, 56, '无锡国家软件园五期项目', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '', 1, 1, 13580, 13580, 54320, 'HYPSMXI40', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (668, 56, '无锡国家软件园五期项目', 'E-FH400-4', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤8.5dB 接入端口数量：4 安装方式：机柜式 尺寸2U', '和源通信', '', 1, 1, 6642, 6642, 6642, 'ECM1B042CZ1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (696, 57, '南京建宁西路隧道东延段项目', 'DRFS-88/M', '频率范围：87-108MHz 远端携带：32 数字型 功能：触摸屏/网讯平台', '和源通信', '', 1, 1, 25000, 25000, 25000, 'HYR2DI000', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (669, 56, '无锡国家软件园五期项目', 'E-JF350/400-4', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤7.5dB 接入端口数量：4 安装方式：机柜式 尺寸1U', '和源通信', '', 1, 1, 2493, 2493, 2493, 'EDE1BU4xCZ1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (670, 56, '无锡国家软件园五期项目', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '', 1, 1, 3753, 3753, 3753, 'EDULN4N1CZ1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (671, 56, '无锡国家软件园五期项目', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AU6xCZ1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (672, 56, '无锡国家软件园五期项目', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AD6xCZ1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (673, 56, '无锡国家软件园五期项目', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '', 1, 1, 9876, 9876, 9876, 'HYR2SI030', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (674, 56, '无锡国家软件园五期项目', 'LS-NFX-RPT', '网讯平台信道机接入管理服务许可 -信道资源管理 -呼叫类型繁忙度分析', '和源通信', '', 1, 1, 2500, 2500, 10000, 'HYWSPNB1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (675, 56, '无锡国家软件园五期项目', 'LS-NFX-BDA', '网讯云端终端直放站接入管理服务许可-远端站告警-远端区域状态更新', '和源通信', '', 1, 1, 1500, 1500, 6000, 'HYWSRNB1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (676, 56, '无锡国家软件园五期项目', 'LS-NFX-RAD', '网讯平台终端对讲机接入管理服务许可-对讲机ID呼叫管理-对讲机上下线管理-呼叫组繁忙度分析', '和源通信', '', 1, 1, 180, 180, 5400, 'HYWSTNB1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (677, 56, '无锡国家软件园五期项目', 'NFX-PAT-OPETN', '支持携带对讲机完成在线的路线巡检记录及任务编排', '和源通信', '', 1, 1, 22000, 22000, 22000, 'HYWACHA1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (678, 56, '无锡国家软件园五期项目', 'BTN10', '标准iBeacon协议，电池续航3年，专用对讲机广播报文，许可证：蓝牙定位入网许可', '和源通信', '', 1, 1, 110, 110, 24420, 'HYBIOCBNY', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (679, 56, '无锡国家软件园五期项目', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '', 1, 1, 458, 458, 458, 'EANLOMO5HR1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (680, 56, '无锡国家软件园五期项目', 'NFX_GATW', '用于本地系统设备管理和服务器的同步 -本地系统建立和配置 -设备驱动管理 -设备参数设置 -云同步 -设备报警管理', '和源通信', '', 1, 1, 12500, 12500, 12500, 'HYWG0NB1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (681, 56, '无锡国家软件园五期项目', 'ACC-CWT', '提供某一个项目上所有系统的工作管理，直观全面的反映系统的整体面貌和其中设备的布局，并可以跟踪每个设备及服务的进程。-告警处置模块-告警详情模块-维修情况和完成情况-设备位置地图模块，含一年的在线后台服', '和源通信', '', 1, 1, 8333, 8333, 8333, 'HYWF0NA1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (682, 56, '无锡国家软件园五期项目', 'ACC-NUT', '提供多单位的系统运维流程跟踪-告警管理和推送-故障设备快速定位-维护更新工作单', '和源通信', '', 1, 1, 4167, 4167, 4167, 'HYWT0NA1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (683, 57, '南京建宁西路隧道东延段项目', 'DRFS-300/M', '频率范围：350MHz 远端携带：32 数字型 功能：触摸屏/网讯平台', '和源通信', '', 1, 1, 25000, 25000, 25000, 'HYR2DI030', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (684, 57, '南京建宁西路隧道东延段项目', 'DRFT-BDA310/M', '频率范围：351-356/361-366MHz；带宽：≤21M；输出：10W；数字型 功能：触摸屏/网讯平台 扩展：馈电', '和源通信', '', 1, 1, 47917, 47917, 95834, 'HYR3DI330', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (685, 57, '南京建宁西路隧道东延段项目', 'E-ANTO LT', '频率范围：88-430MHz 承载功率：50W 性能：室内全向 天线增益：0dBi', '和源通信', '', 1, 1, 209, 209, 2090, 'HYAIOCN1N', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (686, 57, '南京建宁西路隧道东延段项目', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 284, 'HYCDN24Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (687, 57, '南京建宁西路隧道东延段项目', 'EVDC-6 LT', '频率范围：150-170MHz，承载功率：100W;耦合规格：6dB', '和源通信', '', 1, 1, 184, 184, 2760, 'HYCCN31Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (688, 57, '南京建宁西路隧道东延段项目', 'E-ANTD 400', '频率范围：400-430MHz 增益：2.5dBi 防护等级：IP65 辐射方向：定向 最大承载功率：50W 接头类型：N-Femade 特性：室外', '和源通信', '', 1, 1, 354, 354, 1416, 'EAN2OFD2TE2', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (689, 57, '南京建宁西路隧道东延段项目', 'E-SGQ400D', '频率范围：410-414/420-424MHz 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 隔离方式：带通 工作带宽：4M 安装方式：机柜式 尺寸：2U', '和源通信', '', 1, 1, 7876, 7876, 7876, 'EDULB4H1CZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (690, 57, '南京建宁西路隧道东延段项目', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AU6xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (691, 57, '南京建宁西路隧道东延段项目', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AD6xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (692, 57, '南京建宁西路隧道东延段项目', 'DRFS-400/M', '频率范围：410-414/420-424MHz 远端携带：32 数字型 功能：触摸屏/网讯平台', '和源通信', '', 1, 1, 25000, 25000, 25000, 'HYR2DI040', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (693, 57, '南京建宁西路隧道东延段项目', 'DRFT-BDA410/M', '频率范围：410-414/420-424MHz 数字带宽：≤4M 输出：10W 数字型 功能：触摸屏/网讯平台 扩展：馈电', '和源通信', '', 1, 1, 47917, 47917, 95834, 'HYR3DI340', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (694, 57, '南京建宁西路隧道东延段项目', 'DRFT-BDA410/M', '频率范围：410-414/420-424MHz 数字带宽：≤4M 输出：10W 数字型 功能：触摸屏/网讯平台 扩展：馈电', '和源通信', '', 1, 1, 47917, 47917, 95834, 'HYR3DI340', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (695, 57, '南京建宁西路隧道东延段项目', 'E-FHP2000-3', '频率范围：87-108/351-366/410-424MHz 单端口承载功率：50W 插入损耗：≤2.0dB 接入端口数量：3 安装方式：机柜式 尺寸：2U', '和源通信', '', 1, 1, 16667, 16667, 33334, 'ECM5BB32CZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (697, 57, '南京建宁西路隧道东延段项目', 'DRFT-BDA88/M', '频率范围：87-108MHz；带宽：≤21M；输出：10W；数字型 功能：触摸屏/网讯平台 扩展：馈电', '和源通信', '', 1, 1, 45833, 45833, 91666, 'HYR3DI300', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (698, 57, '南京建宁西路隧道东延段项目', 'MarkNET3000', '频率范围：351-356/361-366MHz 带宽：≤5M ， -基站控制器 -基站交换机 -三载波数模兼容信道 -三载波合路平台，合路输出：10W -功能：网讯平台', '和源通信', '', 1, 1, 125000, 125000, 125000, 'HYBC3XI30', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (699, 57, '南京建宁西路隧道东延段项目', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AU6xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (700, 57, '南京建宁西路隧道东延段项目', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AD6xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (701, 58, '苏州漕湖商务中心项目', 'E-BDA088-U FM', '频率范围：087-108MHz;最大功率：1mW;机柜式;尺寸：3U;供电供电220VAC;内置功能：16信道广播接入&广播告警切换;监控能力：不支持', '和源通信', '', 1, 1, 116667, 116667, 116667, 'OAMFF5WUGH1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (702, 58, '苏州漕湖商务中心项目', 'RFS-88 LT/M', '频率范围：87-108MHz 远端携带：4 功能：正面状态灯/面板调试', '和源通信', '', 1, 1, 8958, 8958, 8958, 'HYR2SI000', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (703, 58, '苏州漕湖商务中心项目', 'RFT-BDA88 LT/M', '频率范围：87-108MHz；带宽：≤21M；输出：10W；2U机柜；功能：正面状态灯/面板调试', '和源通信', '', 1, 1, 22500, 22500, 22500, 'HYR3SI300', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (704, 58, '苏州漕湖商务中心项目', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 1846, 'HYCDN24Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (705, 58, '苏州漕湖商务中心项目', 'E-ANTO LT', '频率范围：88-430MHz 承载功率：50W 性能：室内全向 天线增益：0dBi', '和源通信', '', 1, 1, 209, 209, 2717, 'HYAIOCN1N', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (706, 58, '苏州漕湖商务中心项目', 'ACC-CWT', '提供某一个项目上所有系统的工作管理，直观全面的反映系统的整体面貌和其中设备的布局，并可以跟踪每个设备及服务的进程。-告警处置模块-告警详情模块-维修情况和完成情况-设备位置地图模块，含一年的在线后台服', '和源通信', '', 1, 1, 8333, 8333, 8333, 'HYWF0NA1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (707, 58, '苏州漕湖商务中心项目', 'ACC-NUT', '提供多单位的系统运维流程跟踪-告警管理和推送-故障设备快速定位-维护更新工作单', '和源通信', '', 1, 1, 4167, 4167, 4167, 'HYWT0NA1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (708, 58, '苏州漕湖商务中心项目', 'LS-NFX-BDA', '网讯云端终端直放站接入管理服务许可-远端站告警-远端区域状态更新', '和源通信', '', 1, 1, 1500, 1500, 3000, 'HYWSRNB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (709, 58, '苏州漕湖商务中心项目', 'LS-NFX-RPT', '网讯平台信道机接入管理服务许可 -信道资源管理 -呼叫类型繁忙度分析', '和源通信', '', 1, 1, 2500, 2500, 25000, 'HYWSPNB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (710, 58, '苏州漕湖商务中心项目', 'LS-NFX-RAD', '网讯平台终端对讲机接入管理服务许可-对讲机ID呼叫管理-对讲机上下线管理-呼叫组繁忙度分析', '和源通信', '', 1, 1, 180, 180, 7200, 'HYWSTNB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (711, 58, '苏州漕湖商务中心项目', 'NFX_GATW', '用于本地系统设备管理和服务器的同步 -本地系统建立和配置 -设备驱动管理 -设备参数设置 -云同步 -设备报警管理', '和源通信', '', 1, 1, 12500, 12500, 12500, 'HYWG0NB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (712, 58, '苏州漕湖商务中心项目', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '', 1, 1, 13580, 13580, 27160, 'HYPSMXI40', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (713, 58, '苏州漕湖商务中心项目', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'ECM1B022CZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (714, 58, '苏州漕湖商务中心项目', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '', 1, 1, 2320, 2320, 2320, 'EDE1BU2xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (715, 58, '苏州漕湖商务中心项目', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '', 1, 1, 3753, 3753, 3753, 'EDULN4N1CZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (716, 58, '苏州漕湖商务中心项目', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AU6xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (717, 58, '苏州漕湖商务中心项目', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AD6xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (718, 58, '苏州漕湖商务中心项目', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '', 1, 1, 9876, 9876, 29628, 'HYR2SI030', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (719, 58, '苏州漕湖商务中心项目', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 1U机箱 功能： 网讯平台', '和源通信', '', 1, 1, 11851, 11851, 118510, 'HYR3SI140', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (720, 58, '苏州漕湖商务中心项目', 'FDPower400', '馈电功能模组,需搭配可扩展远端机;内置远端内向天馈提供电力;', '和源通信', '', 1, 1, 1583, 1583, 15830, 'HYGF20000', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (721, 58, '苏州漕湖商务中心项目', 'MA12', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65 应用：指示灯 蓝牙信标', '和源通信', '', 1, 1, 410, 410, 77900, 'HYAIOCB4Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (722, 58, '苏州漕湖商务中心项目', 'MADC-6', '频率范围：351-470MHz 承载功率：100W 耦合规格：6dB 分路端口数量：2 防护等级：IP65 应用：馈电', '和源通信', '', 1, 1, 246, 246, 36900, 'HYCCF34Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (723, 58, '苏州漕湖商务中心项目', 'PNR2000', '频率范围：400~470MHz，锂电池 3700mAh', '和源通信', '', 1, 1, 1333, 1333, 53320, 'HYTD4MA', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (751, 60, '深圳乐高乐园度假区项目', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 35500, 'HYCCN34Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (724, 59, '温州国际博览中心', 'NFX_MAST_OPETN', '-账户创建和访问管理-设备数据和系统数据的存储和恢复-产品库数据-系统拓扑和设备位置显示和管理-系统资源统计和告警分析推送-系统工作台主次账号一个-20个远端站授权，4个信道机授权，100个终端授权', '和源通信', '', 1, 1, 105000, 105000, 105000, 'HYWP0NC1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (725, 59, '温州国际博览中心', 'ACC-CWT', '提供某一个项目上所有系统的工作管理，直观全面的反映系统的整体面貌和其中设备的布局，并可以跟踪每个设备及服务的进程。-告警处置模块-告警详情模块-维修情况和完成情况-设备位置地图模块，含一年的在线后台服', '和源通信', '', 1, 1, 8333, 8333, 8333, 'HYWF0NA1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (726, 59, '温州国际博览中心', 'LS-NFX-RAD', '网讯平台终端对讲机接入管理服务许可-对讲机ID呼叫管理-对讲机上下线管理-呼叫组繁忙度分析', '和源通信', '', 1, 1, 180, 180, 14400, 'HYWSTNB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (727, 59, '温州国际博览中心', 'LS-NFX-BDA', '网讯云端终端直放站接入管理服务许可-远端站告警-远端区域状态更新', '和源通信', '', 1, 1, 1500, 1500, 306000, 'HYWSRNB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (728, 59, '温州国际博览中心', 'LS-NFX-RPT', '网讯平台信道机接入管理服务许可 -信道资源管理 -呼叫类型繁忙度分析', '和源通信', '', 1, 1, 2500, 2500, 10000, 'HYWSPNB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (729, 59, '温州国际博览中心', 'PNR2000', '频率范围：400~470MHz，锂电池 3700mAh', '和源通信', '', 1, 1, 1333, 1333, 106640, 'HYTD4MA', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (730, 59, '温州国际博览中心', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AU6xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (731, 59, '温州国际博览中心', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AD6xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (732, 59, '温州国际博览中心', 'DRFS-400/M', '频率范围：410-414/420-424MHz 远端携带：32 数字型 功能：触摸屏/网讯平台', '和源通信', '', 1, 1, 25000, 25000, 50000, 'HYR2DI040', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (733, 59, '温州国际博览中心', 'DRFT-BDA410/M', '频率范围：410-414/420-424MHz 数字带宽：≤4M 输出：10W 数字型 功能：触摸屏/网讯平台 扩展：馈电', '和源通信', '', 1, 1, 47917, 47917, 1150008, 'HYR3DI340', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (734, 59, '温州国际博览中心', 'E-ANTD 400', '频率范围：400-430MHz 增益：2.5dBi 防护等级：IP65 辐射方向：定向 最大承载功率：50W 接头类型：N-Femade 特性：室外', '和源通信', '', 1, 1, 354, 354, 8496, 'EAN2OFD2TE2', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (735, 59, '温州国际博览中心', 'MA12', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65 应用：指示灯 蓝牙信标', '和源通信', '', 1, 1, 410, 410, 156210, 'HYAIOCB4Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (736, 59, '温州国际博览中心', 'MADC-6', '频率范围：351-470MHz 承载功率：100W 耦合规格：6dB 分路端口数量：2 防护等级：IP65 应用：馈电', '和源通信', '', 1, 1, 246, 246, 70356, 'HYCCF34Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (737, 59, '温州国际博览中心', 'FDPower400', '馈电功能模组,需搭配可扩展远端机;内置远端内向天馈提供电力;', '和源通信', '', 1, 1, 1583, 1583, 37992, 'HYGF20000', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (738, 59, '温州国际博览中心', 'E-FHP2000-2', '频率范围：351-366/410-424MHz 单端口承载功率：50W 插入损耗：≤1.5dB 接入端口数量：2 安装方式：机柜式 尺寸：2U', '和源通信', '', 1, 1, 7917, 7917, 190008, 'ECM1BB22CZ2', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (739, 59, '温州国际博览中心', 'E-SGQ350D', '频率范围：351-356/361-366MHz 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 隔离方式：带通 工作带宽：5M 安装方式：机柜式 尺寸：2U', '和源通信', '', 1, 1, 9167, 9167, 9167, 'EDUPB5H1CZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (740, 59, '温州国际博览中心', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AU6xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (741, 59, '温州国际博览中心', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AD6xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (742, 59, '温州国际博览中心', 'DRFS-300/M', '频率范围：350MHz 远端携带：32 数字型 功能：触摸屏/网讯平台', '和源通信', '', 1, 1, 25000, 25000, 50000, 'HYR2DI030', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (743, 59, '温州国际博览中心', 'DRFT-BDA310/M', '频率范围：351-356/361-366MHz；带宽：≤21M；输出：10W；数字型 功能：触摸屏/网讯平台 扩展：馈电', '和源通信', '', 1, 1, 47917, 47917, 1150008, 'HYR3DI330', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (744, 59, '温州国际博览中心', 'MarkNET3000', '频率范围：351-356/361-366MHz 带宽：≤5M ， -基站控制器 -基站交换机 -三载波数模兼容信道 -三载波合路平台，合路输出：10W -功能：网讯平台', '和源通信', '', 1, 1, 125000, 125000, 125000, 'HYBC3XI30', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (745, 59, '温州国际博览中心', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '', 1, 1, 13580, 13580, 54320, 'HYPSMXI40', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (746, 59, '温州国际博览中心', 'E-FH400-4', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤8.5dB 接入端口数量：4 安装方式：机柜式 尺寸2U', '和源通信', '', 1, 1, 6642, 6642, 6642, 'ECM1B042CZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (747, 59, '温州国际博览中心', 'E-JF350/400-4', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤7.5dB 接入端口数量：4 安装方式：机柜式 尺寸1U', '和源通信', '', 1, 1, 2493, 2493, 2493, 'EDE1BU4xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (748, 59, '温州国际博览中心', 'NFX_GATW', '用于本地系统设备管理和服务器的同步 -本地系统建立和配置 -设备驱动管理 -设备参数设置 -云同步 -设备报警管理', '和源通信', '', 1, 1, 12500, 12500, 12500, 'HYWG0NB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (749, 59, '温州国际博览中心', 'E-SGQ400D', '频率范围：402-406/412-416MHz 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 隔离方式：带通 工作带宽：4M 安装方式：机柜式 尺寸：2U', '和源通信', '', 1, 1, 7876, 7876, 7876, 'EDULB4H1CZ2', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (750, 60, '深圳乐高乐园度假区项目', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 21300, 'HYCDN24Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (752, 60, '深圳乐高乐园度假区项目', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '', 1, 1, 142, 142, 56800, 'HYAIOCN4Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (753, 60, '深圳乐高乐园度假区项目', 'ACC-CWT', '提供某一个项目上所有系统的工作管理，直观全面的反映系统的整体面貌和其中设备的布局，并可以跟踪每个设备及服务的进程。-告警处置模块-告警详情模块-维修情况和完成情况-设备位置地图模块，含一年的在线后台服', '和源通信', '', 1, 1, 8333, 8333, 8333, 'HYWF0NA1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (754, 60, '深圳乐高乐园度假区项目', 'NFX_GATW', '用于本地系统设备管理和服务器的同步 -本地系统建立和配置 -设备驱动管理 -设备参数设置 -云同步 -设备报警管理', '和源通信', '', 1, 1, 12500, 12500, 25000, 'HYWG0NB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (755, 60, '深圳乐高乐园度假区项目', 'NFX_MAST_OPETN', '-账户创建和访问管理-设备数据和系统数据的存储和恢复-产品库数据-系统拓扑和设备位置显示和管理-系统资源统计和告警分析推送-系统工作台主次账号一个-20个远端站授权，4个信道机授权，100个终端授权', '和源通信', '', 1, 1, 105000, 105000, 105000, 'HYWP0NC1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (756, 60, '深圳乐高乐园度假区项目', 'LS-NFX-BDA', '网讯云端终端直放站接入管理服务许可-远端站告警-远端区域状态更新', '和源通信', '', 1, 1, 1500, 1500, 79500, 'HYWSRNB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (757, 60, '深圳乐高乐园度假区项目', 'E-FH400-8', '频率范围：400-430MHz 单端口承载功率：50W;插入损耗：≤12dB;接入端口数量：8;安装方式：机柜式;尺寸：2U', '和源通信', '', 1, 1, 14120, 14120, 14120, 'ECM1B082CZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (758, 60, '深圳乐高乐园度假区项目', 'E-JF350/400-8', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤10.5dB 接入端口数量：8 安装方式：机柜式 尺寸1U', '和源通信', '', 1, 1, 4962, 4962, 4962, 'EDE1BU8xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (759, 60, '深圳乐高乐园度假区项目', 'E-SGQ400D', '频率范围：402-406/412-416MHz 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 隔离方式：带通 工作带宽：4M 安装方式：机柜式 尺寸：2U', '和源通信', '', 1, 1, 7876, 7876, 15752, 'EDULB4H1CZ2', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (760, 60, '深圳乐高乐园度假区项目', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 9138, 'EDE1AU6xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (761, 60, '深圳乐高乐园度假区项目', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 9138, 'EDE1AD6xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (762, 60, '深圳乐高乐园度假区项目', 'DRFS-400/M', '频率范围：410-414/420-424MHz 远端携带：32 数字型 功能：触摸屏/网讯平台', '和源通信', '', 1, 1, 25000, 25000, 125000, 'HYR2DI040', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (763, 60, '深圳乐高乐园度假区项目', 'DRFT-BDA410/M', '频率范围：410-414/420-424MHz 数字带宽：≤4M 输出：10W 数字型 功能：触摸屏/网讯平台 扩展：馈电', '和源通信', '', 1, 1, 47917, 47917, 2539601, 'HYR3DI340', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (764, 60, '深圳乐高乐园度假区项目', 'E-ANTD 400', '频率范围：400-430MHz 增益：2.5dBi 防护等级：IP65 辐射方向：定向 最大承载功率：50W 接头类型：N-Femade 特性：室外', '和源通信', '', 1, 1, 354, 354, 1770, 'EAN2OFD2TE2', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (765, 61, '连云港花果山总部研发中心', 'PNR2000', '频率范围：400~470MHz，锂电池 3700mAh', '和源通信', '', 1, 1, 1333, 1333, 26660, 'HYTD4MA', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (766, 61, '连云港花果山总部研发中心', 'NFX-LCN-OPETN', '支持对讲机在地图上人员的动态分布和查询功能', '和源通信', '', 1, 1, 14600, 14600, 14600, 'HYWADHA1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (767, 61, '连云港花果山总部研发中心', 'NFX-PAT-OPETN', '支持携带对讲机完成在线的路线巡检记录及任务编排', '和源通信', '', 1, 1, 22000, 22000, 22000, 'HYWACHA1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (768, 61, '连云港花果山总部研发中心', 'ACC-NUT', '提供多单位的系统运维流程跟踪-告警管理和推送-故障设备快速定位-维护更新工作单', '和源通信', '', 1, 1, 4167, 4167, 4167, 'HYWT0NA1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (769, 61, '连云港花果山总部研发中心', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AU6xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (770, 61, '连云港花果山总部研发中心', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AD6xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (771, 61, '连云港花果山总部研发中心', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '', 1, 1, 9876, 9876, 19752, 'HYR2SI030', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (772, 61, '连云港花果山总部研发中心', 'RFT-BDA400B LT/M', '频率范围：403-405/413-415MHz 带宽：≤4M 输出：2W  功能： 网讯平台', '和源通信', '', 1, 1, 11851, 11851, 94808, 'HYR3SI14A', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (773, 61, '连云港花果山总部研发中心', 'FDPower400', '馈电功能模组,需搭配可扩展远端机;内置远端内向天馈提供电力;', '和源通信', '', 1, 1, 1583, 1583, 12664, 'HYGF20000', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (774, 61, '连云港花果山总部研发中心', 'MAPD-2', '频率范围：88-866MHz 承载功率：100W 分路端口数量：2 防护等级：IP65 应用：馈电', '和源通信', '', 1, 1, 208, 208, 2704, 'HYCDF24Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (775, 61, '连云港花果山总部研发中心', 'MADC-6', '频率范围：351-470MHz 承载功率：100W 耦合规格：6dB 分路端口数量：2 防护等级：IP65 应用：馈电', '和源通信', '', 1, 1, 246, 246, 25584, 'HYCCF34Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (776, 61, '连云港花果山总部研发中心', 'MA12', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65 应用：指示灯 蓝牙信标', '和源通信', '', 1, 1, 410, 410, 51660, 'HYAIOCB4Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (777, 61, '连云港花果山总部研发中心', 'E-ANTD 400', '频率范围：400-430MHz 增益：2.5dBi 防护等级：IP65 辐射方向：定向 最大承载功率：50W 接头类型：N-Femade 特性：室外', '和源通信', '', 1, 1, 354, 354, 708, 'EAN2OFD2TE2', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (778, 61, '连云港花果山总部研发中心', 'BTN10', '标准iBeacon协议，电池续航3年，专用对讲机广播报文，许可证：蓝牙定位入网许可', '和源通信', '', 1, 1, 110, 110, 19800, 'HYBIOCBNY', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (779, 61, '连云港花果山总部研发中心', 'NFX_GATW', '用于本地系统设备管理和服务器的同步 -本地系统建立和配置 -设备驱动管理 -设备参数设置 -云同步 -设备报警管理', '和源通信', '', 1, 1, 12500, 12500, 12500, 'HYWG0NB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (780, 61, '连云港花果山总部研发中心', 'LS-NFX-RAD', '网讯平台终端对讲机接入管理服务许可-对讲机ID呼叫管理-对讲机上下线管理-呼叫组繁忙度分析', '和源通信', '', 1, 1, 180, 180, 3600, 'HYWSTNB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (781, 61, '连云港花果山总部研发中心', 'LS-NFX-BDA', '网讯云端终端直放站接入管理服务许可-远端站告警-远端区域状态更新', '和源通信', '', 1, 1, 1500, 1500, 12000, 'HYWSRNB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (782, 61, '连云港花果山总部研发中心', 'LS-NFX-RPT', '网讯平台信道机接入管理服务许可 -信道资源管理 -呼叫类型繁忙度分析', '和源通信', '', 1, 1, 2500, 2500, 5000, 'HYWSPNB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (783, 61, '连云港花果山总部研发中心', 'ACC-CWT', '提供某一个项目上所有系统的工作管理，直观全面的反映系统的整体面貌和其中设备的布局，并可以跟踪每个设备及服务的进程。-告警处置模块-告警详情模块-维修情况和完成情况-设备位置地图模块，含一年的在线后台服', '和源通信', '', 1, 1, 8333, 8333, 8333, 'HYWF0NA1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (784, 61, '连云港花果山总部研发中心', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '', 1, 1, 13580, 13580, 27160, 'HYPSMXI40', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (785, 61, '连云港花果山总部研发中心', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'ECM1B022CZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (786, 61, '连云港花果山总部研发中心', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '', 1, 1, 2320, 2320, 2320, 'EDE1BU2xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (787, 61, '连云港花果山总部研发中心', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '', 1, 1, 3753, 3753, 3753, 'EDULN4N1CZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (788, 62, '安吉“两山”未来科技城文化艺术中心项目', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '', 1, 1, 2320, 2320, 2320, 'EDE1BU2xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (789, 62, '安吉“两山”未来科技城文化艺术中心项目', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '', 1, 1, 3753, 3753, 3753, 'EDULN4N1CZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (790, 62, '安吉“两山”未来科技城文化艺术中心项目', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AU6xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (791, 62, '安吉“两山”未来科技城文化艺术中心项目', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AD6xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (792, 62, '安吉“两山”未来科技城文化艺术中心项目', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '', 1, 1, 9876, 9876, 19752, 'HYR2SI030', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (793, 62, '安吉“两山”未来科技城文化艺术中心项目', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 1U机箱 功能： 网讯平台', '和源通信', '', 1, 1, 11851, 11851, 94808, 'HYR3SI140', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (794, 62, '安吉“两山”未来科技城文化艺术中心项目', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 18602, 'HYCCN34Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (795, 62, '安吉“两山”未来科技城文化艺术中心项目', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 9230, 'HYCDN24Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (796, 62, '安吉“两山”未来科技城文化艺术中心项目', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '', 1, 1, 142, 142, 28116, 'HYAIOCN4Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (797, 62, '安吉“两山”未来科技城文化艺术中心项目', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '', 1, 1, 458, 458, 458, 'EANLOMO5HR1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (798, 62, '安吉“两山”未来科技城文化艺术中心项目', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '', 1, 1, 13580, 13580, 27160, 'HYPSMXI40', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (799, 62, '安吉“两山”未来科技城文化艺术中心项目', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'ECM1B022CZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (800, 63, '南通炜赋华邑酒店项目', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '', 1, 1, 4569, 4569, 9138, 'ECM1B022CZ1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (801, 63, '南通炜赋华邑酒店项目', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '', 1, 1, 2320, 2320, 4640, 'EDE1BU2xCZ1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (802, 63, '南通炜赋华邑酒店项目', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '', 1, 1, 3753, 3753, 7506, 'EDULN4N1CZ1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (803, 63, '南通炜赋华邑酒店项目', 'LS-NFX-BDA', '网讯云端终端直放站接入管理服务许可-远端站告警-远端区域状态更新', '和源通信', '', 1, 1, 1500, 1500, 15000, 'HYWSRNB1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (804, 63, '南通炜赋华邑酒店项目', 'LS-NFX-RPT', '网讯平台信道机接入管理服务许可 -信道资源管理 -呼叫类型繁忙度分析', '和源通信', '', 1, 1, 2500, 2500, 10000, 'HYWSPNB1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (805, 63, '南通炜赋华邑酒店项目', 'ACC-CWT', '提供某一个项目上所有系统的工作管理，直观全面的反映系统的整体面貌和其中设备的布局，并可以跟踪每个设备及服务的进程。-告警处置模块-告警详情模块-维修情况和完成情况-设备位置地图模块，含一年的在线后台服', '和源通信', '', 1, 1, 8333, 8333, 16666, 'HYWF0NA1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (806, 63, '南通炜赋华邑酒店项目', 'PNR2000', '频率范围：400~470MHz，锂电池 3700mAh', '和源通信', '', 1, 1, 1333, 1333, 106640, 'HYTD4MA', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (807, 63, '南通炜赋华邑酒店项目', 'ACC-NUT', '提供多单位的系统运维流程跟踪-告警管理和推送-故障设备快速定位-维护更新工作单', '和源通信', '', 1, 1, 4167, 4167, 8334, 'HYWT0NA1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (808, 63, '南通炜赋华邑酒店项目', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '', 1, 1, 13580, 13580, 54320, 'HYPSMXI40', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (809, 63, '南通炜赋华邑酒店项目', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 22720, 'HYCCN34Y', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (810, 63, '南通炜赋华邑酒店项目', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '', 1, 1, 142, 142, 31950, 'HYAIOCN4Y', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (811, 63, '南通炜赋华邑酒店项目', 'NFX_GATW', '用于本地系统设备管理和服务器的同步 -本地系统建立和配置 -设备驱动管理 -设备参数设置 -云同步 -设备报警管理', '和源通信', '', 1, 1, 12500, 12500, 25000, 'HYWG0NB1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (812, 63, '南通炜赋华邑酒店项目', 'LS-NFX-RAD', '网讯平台终端对讲机接入管理服务许可-对讲机ID呼叫管理-对讲机上下线管理-呼叫组繁忙度分析', '和源通信', '', 1, 1, 180, 180, 14400, 'HYWSTNB1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (813, 63, '南通炜赋华邑酒店项目', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 9138, 'EDE1AD6xCZ1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (814, 63, '南通炜赋华邑酒店项目', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '', 1, 1, 9876, 9876, 29628, 'HYR2SI030', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (815, 63, '南通炜赋华邑酒店项目', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 1U机箱 功能： 网讯平台', '和源通信', '套', 1, 1, 11851, 11851, 118510, 'HYR3SI140', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (816, 63, '南通炜赋华邑酒店项目', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 9798, 'HYCDN24Y', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (817, 63, '南通炜赋华邑酒店项目', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 9138, 'EDE1AU6xCZ1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (818, 64, '南京悦柳酒店', 'NFX_MAST_OPETN', '-账户创建和访问管理-设备数据和系统数据的存储和恢复-产品库数据-系统拓扑和设备位置显示和管理-系统资源统计和告警分析推送-系统工作台主次账号一个-20个远端站授权，4个信道机授权，100个终端授权', '和源通信', '', 1, 1, 105000, 105000, 105000, 'HYWP0NC1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (819, 64, '南京悦柳酒店', 'LS-NFX-RPT', '网讯平台信道机接入管理服务许可 -信道资源管理 -呼叫类型繁忙度分析', '和源通信', '', 1, 1, 2500, 2500, 5000, 'HYWSPNB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (820, 64, '南京悦柳酒店', 'LS-NFX-BDA', '网讯云端终端直放站接入管理服务许可-远端站告警-远端区域状态更新', '和源通信', '', 1, 1, 1500, 1500, 4500, 'HYWSRNB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (821, 64, '南京悦柳酒店', 'LS-NFX-RAD', '网讯平台终端对讲机接入管理服务许可-对讲机ID呼叫管理-对讲机上下线管理-呼叫组繁忙度分析', '和源通信', '', 1, 1, 180, 180, 7200, 'HYWSTNB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (822, 64, '南京悦柳酒店', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '', 1, 1, 13580, 13580, 27160, 'HYPSMXI40', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (823, 64, '南京悦柳酒店', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'ECM1B022CZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (824, 64, '南京悦柳酒店', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '', 1, 1, 2320, 2320, 2320, 'EDE1BU2xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (825, 64, '南京悦柳酒店', 'NFX_GATW', '用于本地系统设备管理和服务器的同步 -本地系统建立和配置 -设备驱动管理 -设备参数设置 -云同步 -设备报警管理', '和源通信', '', 1, 1, 12500, 12500, 12500, 'HYWG0NB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (826, 64, '南京悦柳酒店', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AU6xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (827, 64, '南京悦柳酒店', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AD6xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (828, 64, '南京悦柳酒店', 'DRFT-BDA410/M', '频率范围：410-414/420-424MHz 数字带宽：≤4M 输出：10W 数字型 功能：触摸屏/网讯平台 扩展：馈电', '和源通信', '', 1, 1, 47917, 47917, 143751, 'HYR3DI340', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (829, 64, '南京悦柳酒店', 'FDPower400', '馈电功能模组,需搭配可扩展远端机;内置远端内向天馈提供电力;', '和源通信', '', 1, 1, 1583, 1583, 4749, 'HYGF20000', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (830, 64, '南京悦柳酒店', 'MA11', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65 应用：指示灯', '和源通信', '', 1, 1, 208, 208, 12480, 'HYAIOCL4Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (831, 64, '南京悦柳酒店', 'MA11', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65 应用：指示灯', '和源通信', '', 1, 1, 208, 208, 8320, 'HYAIOCL4Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (832, 65, '长春瑯珀凯越甄选酒店', 'LS-NFX-RAD', '网讯平台终端对讲机接入管理服务许可-对讲机ID呼叫管理-对讲机上下线管理-呼叫组繁忙度分析', '和源通信', '', 1, 1, 180, 180, 1800, 'HYWSTNB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (833, 65, '长春瑯珀凯越甄选酒店', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '', 1, 1, 13580, 13580, 27160, 'HYPSMXI40', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (834, 65, '长春瑯珀凯越甄选酒店', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'ECM1B022CZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (835, 65, '长春瑯珀凯越甄选酒店', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '', 1, 1, 2320, 2320, 2320, 'EDE1BU2xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (836, 65, '长春瑯珀凯越甄选酒店', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '', 1, 1, 3753, 3753, 3753, 'EDULN4N1CZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (837, 65, '长春瑯珀凯越甄选酒店', 'E-BDA400B LT', '频率范围：410~414/420~424 , 链路带宽 4MHz, 最大射频输出功率 33dBm(2W)', '和源通信', '', 1, 1, 8396, 8396, 33584, 'HYR1SN140', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (838, 65, '长春瑯珀凯越甄选酒店', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 8520, 'HYCCN34Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (839, 65, '长春瑯珀凯越甄选酒店', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 4260, 'HYCDN24Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (840, 65, '长春瑯珀凯越甄选酒店', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '', 1, 1, 142, 142, 12922, 'HYAIOCN4Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (841, 65, '长春瑯珀凯越甄选酒店', 'PNR2000', '频率范围：400~470MHz，锂电池 3700mAh', '和源通信', '', 1, 1, 1333, 1333, 13330, 'HYTD4MA', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (842, 65, '长春瑯珀凯越甄选酒店', 'NFX-RCD-OPETN', '支持对讲机在线通话的实时录音，回访和ID检索功能', '和源通信', '', 1, 1, 8400, 8400, 8400, 'HYWAEHA1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (843, 65, '长春瑯珀凯越甄选酒店', 'ACC-CWT', '提供某一个项目上所有系统的工作管理，直观全面的反映系统的整体面貌和其中设备的布局，并可以跟踪每个设备及服务的进程。-告警处置模块-告警详情模块-维修情况和完成情况-设备位置地图模块，含一年的在线后台服', '和源通信', '', 1, 1, 8333, 8333, 8333, 'HYWF0NA1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (844, 65, '长春瑯珀凯越甄选酒店', 'NFX_GATW', '用于本地系统设备管理和服务器的同步 -本地系统建立和配置 -设备驱动管理 -设备参数设置 -云同步 -设备报警管理', '和源通信', '', 1, 1, 12500, 12500, 12500, 'HYWG0NB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (845, 65, '长春瑯珀凯越甄选酒店', 'LS-NFX-RPT', '网讯平台信道机接入管理服务许可 -信道资源管理 -呼叫类型繁忙度分析', '和源通信', '', 1, 1, 2500, 2500, 5000, 'HYWSPNB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (846, 66, '集创北方总部暨显示驱动芯片设计和先进测试基地项目', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '', 1, 1, 142, 142, 16330, 'HYAIOCN4Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (847, 66, '集创北方总部暨显示驱动芯片设计和先进测试基地项目', 'E-JF350/400-4', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤7.5dB 接入端口数量：4 安装方式：机柜式 尺寸1U', '和源通信', '', 1, 1, 2493, 2493, 2493, 'EDE1BU4xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (848, 66, '集创北方总部暨显示驱动芯片设计和先进测试基地项目', 'E-FH400-4', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤8.5dB 接入端口数量：4 安装方式：机柜式 尺寸2U', '和源通信', '', 1, 1, 6642, 6642, 6642, 'ECM1B042CZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (849, 66, '集创北方总部暨显示驱动芯片设计和先进测试基地项目', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '', 1, 1, 3753, 3753, 3753, 'EDULN4N1CZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (850, 66, '集创北方总部暨显示驱动芯片设计和先进测试基地项目', 'E-BDA400B LT', '频率范围：410~414/420~424 , 链路带宽 4MHz, 最大射频输出功率 33dBm(2W)', '和源通信', '', 1, 1, 8396, 8396, 50376, 'HYR1SN140', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (851, 66, '集创北方总部暨显示驱动芯片设计和先进测试基地项目', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 17608, 'HYCCN34Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (852, 67, '江宁九龙湖国际企业总部园二期项目', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 284, 'HYCDN24Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (853, 67, '江宁九龙湖国际企业总部园二期项目', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '', 1, 1, 142, 142, 31098, 'HYAIOCN4Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (854, 67, '江宁九龙湖国际企业总部园二期项目', 'PNR2000', '频率范围：400~470MHz，锂电池 3700mAh', '和源通信', '', 1, 1, 1333, 1333, 106640, 'HYTD4MA', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (855, 67, '江宁九龙湖国际企业总部园二期项目', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '', 1, 1, 13580, 13580, 54320, 'HYPSMXI40', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (856, 67, '江宁九龙湖国际企业总部园二期项目', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '', 1, 1, 2320, 2320, 4640, 'EDE1BU2xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (857, 67, '江宁九龙湖国际企业总部园二期项目', 'E-JF150-2', '频率范围：130-170MHz 单端口承载功率：1W 插入损耗：≤3.5dB 接入端口数量：2 安装方式：机柜式 尺寸 1U', '和源通信', '', 1, 1, 2493, 2493, 4986, 'HYMJC2010', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (858, 67, '江宁九龙湖国际企业总部园二期项目', 'E-BDA400B LT', '频率范围：410~414/420~424 , 链路带宽 4MHz, 最大射频输出功率 33dBm(2W)', '和源通信', '', 1, 1, 8396, 8396, 67168, 'HYR1SN140', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (859, 67, '江宁九龙湖国际企业总部园二期项目', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 31950, 'HYCCN34Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (978, 17, '功率分配器', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 1, 1, 142, 200.22, 200.22, 'HYCDN24Y', '2025-05-01 17:09:02.631835', '2025-05-01 17:09:02.631841');
INSERT INTO public.quotation_details VALUES (860, 68, '安徽黄山市徽州体育馆', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 4402, 'HYCCN34Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (861, 68, '安徽黄山市徽州体育馆', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 1136, 'HYCDN24Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (862, 68, '安徽黄山市徽州体育馆', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '', 1, 1, 142, 142, 5254, 'HYAIOCN4Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (863, 68, '安徽黄山市徽州体育馆', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '', 1, 1, 458, 458, 458, 'EANLOMO5HR1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (864, 68, '安徽黄山市徽州体育馆', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '', 1, 1, 13580, 13580, 27160, 'HYPSMXI40', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (865, 68, '安徽黄山市徽州体育馆', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'ECM1B022CZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (866, 68, '安徽黄山市徽州体育馆', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '', 1, 1, 2320, 2320, 2320, 'EDE1BU2xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (867, 68, '安徽黄山市徽州体育馆', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '', 1, 1, 3753, 3753, 3753, 'EDULN4N1CZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (868, 68, '安徽黄山市徽州体育馆', 'E-BDA400B LT', '频率范围：410~414/420~424 , 链路带宽 4MHz, 最大射频输出功率 33dBm(2W)', '和源通信', '', 1, 1, 8396, 8396, 8396, 'HYR1SN140', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (869, 69, '南京燕子矶新城医院工程', 'LS-NFX-BDA', '网讯云端终端直放站接入管理服务许可-远端站告警-远端区域状态更新', '和源通信', '', 1, 1, 1500, 1500, 19500, 'HYWSRNB1', '2023-11-01 00:00:00', '2024-07-05 00:00:00');
INSERT INTO public.quotation_details VALUES (870, 69, '南京燕子矶新城医院工程', 'NFX_GATW', '用于本地系统设备管理和服务器的同步 -本地系统建立和配置 -设备驱动管理 -设备参数设置 -云同步 -设备报警管理', '和源通信', '', 1, 1, 12500, 12500, 12500, 'HYWG0NB1', '2023-11-01 00:00:00', '2024-07-05 00:00:00');
INSERT INTO public.quotation_details VALUES (871, 69, '南京燕子矶新城医院工程', 'LS-NFX-RPT', '网讯平台信道机接入管理服务许可 -信道资源管理 -呼叫类型繁忙度分析', '和源通信', '', 1, 1, 2500, 2500, 5000, 'HYWSPNB1', '2023-11-01 00:00:00', '2024-07-05 00:00:00');
INSERT INTO public.quotation_details VALUES (872, 69, '南京燕子矶新城医院工程', 'FDPower400', '馈电功能模组    需搭配可扩展远端机;内置远端内向天馈提供电力;', '和源通信', '套', 1, 1, 1583, 1583, 20579, 'HYGF20000', '2023-11-01 00:00:00', '2024-07-05 00:00:00');
INSERT INTO public.quotation_details VALUES (873, 69, '南京燕子矶新城医院工程', 'R-EVDC-BLST-U', '频率范围：87-170MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4938, 4938, 4938, 'HYMBC6A1U', '2023-11-01 00:00:00', '2024-07-05 00:00:00');
INSERT INTO public.quotation_details VALUES (874, 69, '南京燕子矶新城医院工程', 'RFS-100 LT/M', '频率范围：150~170MHz 带宽：≤20M 远端携带：4 功能： 正面状态灯/网讯平台', '和源通信', '', 1, 1, 8958, 8958, 35832, 'HYR2SI010', '2023-11-01 00:00:00', '2024-07-05 00:00:00');
INSERT INTO public.quotation_details VALUES (875, 69, '南京燕子矶新城医院工程', 'RFT-BDA110 LT/M', '频率范围：157-161/163-167MHz 带宽：≤4M 输出：10W 功能： 正面状态灯/网讯平台', '和源通信', '', 1, 1, 25000, 25000, 325000, 'HYR3SI310', '2023-11-01 00:00:00', '2024-07-05 00:00:00');
INSERT INTO public.quotation_details VALUES (876, 69, '南京燕子矶新城医院工程', 'MADC-6', '频率范围：351-470MHz 承载功率：100W 耦合规格：6dB 分路端口数量：2 防护等级：IP65 应用：馈电', '和源通信', '套', 1, 1, 246, 246, 33210, 'HYCCF34Y', '2023-11-01 00:00:00', '2024-07-05 00:00:00');
INSERT INTO public.quotation_details VALUES (877, 69, '南京燕子矶新城医院工程', 'MAPD-2', '频率范围：88-866MHz 承载功率：100W 分路端口数量：2 防护等级：IP65 应用：馈电', '和源通信', '套', 1, 1, 208, 208, 20800, 'HYCDF24Y', '2023-11-01 00:00:00', '2024-07-05 00:00:00');
INSERT INTO public.quotation_details VALUES (878, 69, '南京燕子矶新城医院工程', 'MA11', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65 应用：指示灯', '和源通信', '套', 1, 1, 208, 208, 48672, 'HYAIOCL4Y', '2023-11-01 00:00:00', '2024-07-05 00:00:00');
INSERT INTO public.quotation_details VALUES (879, 69, '南京燕子矶新城医院工程', 'LS-NFX-RAD', '网讯平台终端对讲机接入管理服务许可-对讲机ID呼叫管理-对讲机上下线管理-呼叫组繁忙度分析', '和源通信', '', 1, 1, 180, 180, 7200, 'HYWSTNB1', '2023-11-01 00:00:00', '2024-07-05 00:00:00');
INSERT INTO public.quotation_details VALUES (880, 69, '南京燕子矶新城医院工程', 'ACC-CWT', '提供某一个项目上所有系统的工作管理，直观全面的反映系统的整体面貌和其中设备的布局，并可以跟踪每个设备及服务的进程。-告警处置模块-告警详情模块-维修情况和完成情况-设备位置地图模块，含一年的在线后台服', '和源通信', '', 1, 1, 8333, 8333, 8333, 'HYWF0NA1', '2023-11-01 00:00:00', '2024-07-05 00:00:00');
INSERT INTO public.quotation_details VALUES (881, 69, '南京燕子矶新城医院工程', 'ACC-NUT', '提供多单位的系统运维流程跟踪-告警管理和推送-故障设备快速定位-维护更新工作单', '和源通信', '', 1, 1, 4167, 4167, 4167, 'HYWT0NA1', '2023-11-01 00:00:00', '2024-07-05 00:00:00');
INSERT INTO public.quotation_details VALUES (882, 69, '南京燕子矶新城医院工程', 'PNR2000', '频率范围：150~170MHz，锂电池 3700mAh', '和源通信', '', 1, 1, 1333, 1333, 53320, 'HYTD1MA', '2023-11-01 00:00:00', '2024-07-05 00:00:00');
INSERT INTO public.quotation_details VALUES (883, 69, '南京燕子矶新城医院工程', 'Mark1000 MAX VHF（停售）', '频率范围：136~174MHz-网讯平台-数模兼容', '和源通信', '', 1, 1, 14580, 14580, 29160, 'HYPSMXI10', '2023-11-01 00:00:00', '2024-07-05 00:00:00');
INSERT INTO public.quotation_details VALUES (884, 69, '南京燕子矶新城医院工程', 'E-FH150-2', '频率范围：163-167MHz 单端口承载功率：50W;插入损耗：≤4.0dB接入端口数量：2;安装方式：机柜式;', '和源通信', '', 1, 1, 7902, 7902, 7902, 'HYMFC2A10', '2023-11-01 00:00:00', '2024-07-05 00:00:00');
INSERT INTO public.quotation_details VALUES (885, 69, '南京燕子矶新城医院工程', 'E-JF150-2', '频率范围：130-170MHz 单端口承载功率：1W 插入损耗：≤3.5dB 接入端口数量：2 安装方式：机柜式 尺寸 1U', '和源通信', '', 1, 1, 2493, 2493, 2493, 'HYMJC2010', '2023-11-01 00:00:00', '2024-07-05 00:00:00');
INSERT INTO public.quotation_details VALUES (886, 69, '南京燕子矶新城医院工程', 'R-EVDC-BLST-D', '频率范围：87-170MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4938, 4938, 4938, 'HYMBC6A1D', '2023-11-01 00:00:00', '2024-07-05 00:00:00');
INSERT INTO public.quotation_details VALUES (887, 70, '阿里江苏总部园区B地块', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 8378, 'HYCDN24Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (888, 70, '阿里江苏总部园区B地块', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 33796, 'HYCCN34Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (889, 70, '阿里江苏总部园区B地块', 'LS-NFX-RPT', '网讯平台信道机接入管理服务许可 -信道资源管理 -呼叫类型繁忙度分析', '和源通信', '', 1, 1, 2500, 2500, 5000, 'HYWSPNB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (890, 70, '阿里江苏总部园区B地块', 'LS-NFX-BDA', '网讯云端终端直放站接入管理服务许可-远端站告警-远端区域状态更新', '和源通信', '', 1, 1, 1500, 1500, 25500, 'HYWSRNB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (891, 70, '阿里江苏总部园区B地块', 'LS-NFX-RAD', '网讯平台终端对讲机接入管理服务许可-对讲机ID呼叫管理-对讲机上下线管理-呼叫组繁忙度分析', '和源通信', '', 1, 1, 180, 180, 7200, 'HYWSTNB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (892, 70, '阿里江苏总部园区B地块', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'ECM1B022CZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (893, 70, '阿里江苏总部园区B地块', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '', 1, 1, 2320, 2320, 2320, 'EDE1BU2xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (894, 70, '阿里江苏总部园区B地块', 'NFX_GATW', '用于本地系统设备管理和服务器的同步 -本地系统建立和配置 -设备驱动管理 -设备参数设置 -云同步 -设备报警管理', '和源通信', '', 1, 1, 12500, 12500, 12500, 'HYWG0NB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (895, 70, '阿里江苏总部园区B地块', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AU6xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (896, 70, '阿里江苏总部园区B地块', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AD6xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (897, 70, '阿里江苏总部园区B地块', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '', 1, 1, 9876, 9876, 49380, 'HYR2SI030', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (898, 70, '阿里江苏总部园区B地块', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 1U机箱 功能： 网讯平台', '和源通信', '', 1, 1, 11851, 11851, 201467, 'HYR3SI140', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (899, 70, '阿里江苏总部园区B地块', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '', 1, 1, 142, 142, 44162, 'HYAIOCN4Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (900, 71, '阿里江苏总部园区C地块项目', 'LS-NFX-BDA', '网讯云端终端直放站接入管理服务许可-远端站告警-远端区域状态更新', '和源通信', '', 1, 1, 1500, 1500, 24000, 'HYWSRNB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (901, 71, '阿里江苏总部园区C地块项目', 'LS-NFX-RAD', '网讯平台终端对讲机接入管理服务许可-对讲机ID呼叫管理-对讲机上下线管理-呼叫组繁忙度分析', '和源通信', '', 1, 1, 180, 180, 7200, 'HYWSTNB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (902, 71, '阿里江苏总部园区C地块项目', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '', 1, 1, 2320, 2320, 2320, 'EDE1BU2xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (903, 71, '阿里江苏总部园区C地块项目', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'ECM1B022CZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (904, 71, '阿里江苏总部园区C地块项目', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AD6xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (905, 71, '阿里江苏总部园区C地块项目', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AU6xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (906, 71, '阿里江苏总部园区C地块项目', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '', 1, 1, 3753, 3753, 3753, 'EDULN4N1CZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (907, 71, '阿里江苏总部园区C地块项目', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 1U机箱 功能： 网讯平台', '和源通信', '', 1, 1, 11851, 11851, 189616, 'HYR3SI140', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (908, 71, '阿里江苏总部园区C地块项目', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '', 1, 1, 9876, 9876, 39504, 'HYR2SI030', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (909, 71, '阿里江苏总部园区C地块项目', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 28400, 'HYCCN34Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (910, 71, '阿里江苏总部园区C地块项目', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 14484, 'HYCDN24Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (911, 71, '阿里江苏总部园区C地块项目', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '', 1, 1, 142, 142, 42884, 'HYAIOCN4Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (912, 71, '阿里江苏总部园区C地块项目', 'LS-NFX-RPT', '网讯平台信道机接入管理服务许可 -信道资源管理 -呼叫类型繁忙度分析', '和源通信', '', 1, 1, 2500, 2500, 5000, 'HYWSPNB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (913, 71, '阿里江苏总部园区C地块项目', 'NFX_GATW', '用于本地系统设备管理和服务器的同步 -本地系统建立和配置 -设备驱动管理 -设备参数设置 -云同步 -设备报警管理', '和源通信', '', 1, 1, 12500, 12500, 12500, 'HYWG0NB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (914, 71, '阿里江苏总部园区C地块项目', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '', 1, 1, 13580, 13580, 27160, 'HYPSMXI40', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (915, 72, '青岛市山东路立交地下空间', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '', 1, 1, 13580, 13580, 27160, 'HYPSMXI40', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (916, 72, '青岛市山东路立交地下空间', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'ECM1B022CZ1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (917, 72, '青岛市山东路立交地下空间', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 1, 1, 3753, 3753, 3753, 'EDULN4N1CZ1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (918, 72, '青岛市山东路立交地下空间', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '', 1, 1, 142, 142, 2698, 'HYAIOCN4Y', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (919, 72, '青岛市山东路立交地下空间', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 2130, 'HYCCN34Y', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (920, 72, '青岛市山东路立交地下空间', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 426, 'HYCDN24Y', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (921, 72, '青岛市山东路立交地下空间', 'PNR2000', '频率范围：400~470MHz，锂电池 3700mAh', '和源通信', '', 1, 1, 1333, 1333, 26660, 'HYTD4MA', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (922, 72, '青岛市山东路立交地下空间', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '', 1, 1, 2320, 2320, 2320, 'EDE1BU2xCZ1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (923, 73, '山东青岛创意文化综合体建设项目', 'PNR2000', '频率范围：400~470MHz，锂电池 3700mAh', '和源通信', '', 1, 1, 1333, 1333, 53320, 'HYTD4MA', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (924, 73, '山东青岛创意文化综合体建设项目', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 1, 1, 3753, 3753, 3753, 'EDULN4N1CZ1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (925, 73, '山东青岛创意文化综合体建设项目', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '', 1, 1, 13580, 13580, 27160, 'HYPSMXI40', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (926, 73, '山东青岛创意文化综合体建设项目', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '', 1, 1, 9876, 9876, 29628, 'HYR2SI030', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (927, 73, '山东青岛创意文化综合体建设项目', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 1U机箱 功能： 网讯平台', '和源通信', '', 1, 1, 11851, 11851, 118510, 'HYR3SI140', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (928, 73, '山东青岛创意文化综合体建设项目', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '', 1, 1, 142, 142, 28116, 'HYAIOCN4Y', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (929, 73, '山东青岛创意文化综合体建设项目', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 28116, 'HYCCN34Y', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (930, 73, '山东青岛创意文化综合体建设项目', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 568, 'HYCDN24Y', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (931, 73, '山东青岛创意文化综合体建设项目', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'ECM1B022CZ1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (932, 73, '山东青岛创意文化综合体建设项目', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '', 1, 1, 2320, 2320, 2320, 'EDE1BU2xCZ1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (933, 73, '山东青岛创意文化综合体建设项目', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AU6xCZ1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (934, 73, '山东青岛创意文化综合体建设项目', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AD6xCZ1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (935, 74, '浙中新能源汽车城市广场', 'LS-NFX-BDA', '网讯云端终端直放站接入管理服务许可-远端站告警-远端区域状态更新', '和源通信', '', 1, 1, 1500, 1500, 18000, 'HYWSRNB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (936, 74, '浙中新能源汽车城市广场', 'ACC-NUT', '提供多单位的系统运维流程跟踪-告警管理和推送-故障设备快速定位-维护更新工作单', '和源通信', '', 1, 1, 4167, 4167, 4167, 'HYWT0NA1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (937, 74, '浙中新能源汽车城市广场', 'NFX_GATW', '用于本地系统设备管理和服务器的同步 -本地系统建立和配置 -设备驱动管理 -设备参数设置 -云同步 -设备报警管理', '和源通信', '', 1, 1, 12500, 12500, 12500, 'HYWG0NB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (938, 74, '浙中新能源汽车城市广场', 'LS-NFX-RAD', '网讯平台终端对讲机接入管理服务许可-对讲机ID呼叫管理-对讲机上下线管理-呼叫组繁忙度分析', '和源通信', '', 1, 1, 180, 180, 7200, 'HYWSTNB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (939, 74, '浙中新能源汽车城市广场', 'ACC-CWT', '提供某一个项目上所有系统的工作管理，直观全面的反映系统的整体面貌和其中设备的布局，并可以跟踪每个设备及服务的进程。-告警处置模块-告警详情模块-维修情况和完成情况-设备位置地图模块，含一年的在线后台服', '和源通信', '', 1, 1, 8333, 8333, 8333, 'HYWF0NA1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (940, 74, '浙中新能源汽车城市广场', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '', 1, 1, 13580, 13580, 27160, 'HYPSMXI40', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (941, 74, '浙中新能源汽车城市广场', 'PNR2000', '频率范围：400~470MHz，锂电池 3700mAh', '和源通信', '', 1, 1, 1333, 1333, 53320, 'HYTD4MA', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (942, 74, '浙中新能源汽车城市广场', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '', 1, 1, 2320, 2320, 2320, 'EDE1BU2xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (943, 74, '浙中新能源汽车城市广场', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'ECM1B022CZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (944, 74, '浙中新能源汽车城市广场', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '', 1, 1, 3753, 3753, 3753, 'EDULN4N1CZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (945, 74, '浙中新能源汽车城市广场', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AU6xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (946, 74, '浙中新能源汽车城市广场', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AD6xCZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (947, 74, '浙中新能源汽车城市广场', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 1U机箱 功能： 网讯平台', '和源通信', '', 1, 1, 11851, 11851, 142212, 'HYR3SI140', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (948, 74, '浙中新能源汽车城市广场', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '', 1, 1, 9876, 9876, 29628, 'HYR2SI030', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (949, 74, '浙中新能源汽车城市广场', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 17750, 'HYCCN34Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (950, 74, '浙中新能源汽车城市广场', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 14200, 'HYCDN24Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (951, 74, '浙中新能源汽车城市广场', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '', 1, 1, 142, 142, 31808, 'HYAIOCN4Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (952, 74, '浙中新能源汽车城市广场', 'LS-NFX-RPT', '网讯平台信道机接入管理服务许可 -信道资源管理 -呼叫类型繁忙度分析', '和源通信', '', 1, 1, 2500, 2500, 5000, 'HYWSPNB1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (953, 75, '上海打浦桥社区文化活动中心', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '', 1, 1, 142, 142, 1420, 'HYAIOCN4Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (954, 75, '上海打浦桥社区文化活动中心', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '', 1, 1, 13580, 13580, 13580, 'HYPSMXI40', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (955, 75, '上海打浦桥社区文化活动中心', 'PNR2000', '频率范围：400~470MHz，锂电池 3700mAh', '和源通信', '', 1, 1, 1333, 1333, 13330, 'HYTD4MA', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (956, 75, '上海打浦桥社区文化活动中心', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '', 1, 1, 3753, 3753, 3753, 'EDULN4N1CZ1', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (957, 75, '上海打浦桥社区文化活动中心', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 1420, 'HYCCN34Y', '2023-11-01 00:00:00', '2024-02-28 00:00:00');
INSERT INTO public.quotation_details VALUES (958, 76, '东台市金融广场', 'NFX_GATW', '用于本地系统设备管理和服务器的同步 -本地系统建立和配置 -设备驱动管理 -设备参数设置 -云同步 -设备报警管理', '和源通信', '', 1, 1, 12500, 12500, 12500, 'HYWG0NB1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (959, 76, '东台市金融广场', 'LS-NFX-BDA', '网讯云端终端直放站接入管理服务许可-远端站告警-远端区域状态更新', '和源通信', '', 1, 1, 1500, 1500, 12000, 'HYWSRNB1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (960, 76, '东台市金融广场', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '', 1, 1, 13580, 13580, 27160, 'HYPSMXI40', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (961, 76, '东台市金融广场', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 14200, 'HYCCN34Y', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (962, 76, '东台市金融广场', 'EVPD-2 LT', '频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;', '和源通信', '', 1, 1, 142, 142, 6106, 'HYCDN24Y', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (963, 76, '东台市金融广场', 'LS-NFX-RPT', '网讯平台信道机接入管理服务许可 -信道资源管理 -呼叫类型繁忙度分析', '和源通信', '', 1, 1, 2500, 2500, 5000, 'HYWSPNB1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (964, 76, '东台市金融广场', 'LS-NFX-RAD', '网讯平台终端对讲机接入管理服务许可-对讲机ID呼叫管理-对讲机上下线管理-呼叫组繁忙度分析', '和源通信', '', 1, 1, 180, 180, 7200, 'HYWSTNB1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (965, 76, '东台市金融广场', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AU6xCZ1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (966, 76, '东台市金融广场', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'EDE1AD6xCZ1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (967, 76, '东台市金融广场', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 1U机箱 功能： 网讯平台', '和源通信', '', 1, 1, 11851, 11851, 94808, 'HYR3SI140', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (968, 76, '东台市金融广场', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '', 1, 1, 9876, 9876, 19752, 'HYR2SI030', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (969, 76, '东台市金融广场', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '', 1, 1, 142, 142, 20164, 'HYAIOCN4Y', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (970, 76, '东台市金融广场', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 1, 1, 3753, 3753, 3753, 'EDULN4N1CZ1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (971, 76, '东台市金融广场', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '', 1, 1, 2320, 2320, 2320, 'EDE1BU2xCZ1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (972, 76, '东台市金融广场', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '', 1, 1, 4569, 4569, 4569, 'ECM1B022CZ1', '2023-11-01 00:00:00', '2025-02-25 00:00:00');
INSERT INTO public.quotation_details VALUES (979, 17, '定向耦合器', 'EVDC-6 LT', '频率范围：150-170MHz    承载功率：100W;耦合规格：6dB', '和源通信', '套', 1, 1, 184, 200, 200, 'HYCCN31Y', '2025-05-01 17:09:02.632017', '2025-05-01 17:09:02.632019');


--
-- Data for Name: role_permissions; Type: TABLE DATA; Schema: public; Owner: pma_user
--

INSERT INTO public.role_permissions VALUES (8, 'sales', 'project', true, true, true, true);
INSERT INTO public.role_permissions VALUES (9, 'sales', 'customer', true, true, true, true);
INSERT INTO public.role_permissions VALUES (10, 'sales', 'quotation', true, true, true, true);
INSERT INTO public.role_permissions VALUES (11, 'sales', 'product', true, false, false, false);
INSERT INTO public.role_permissions VALUES (12, 'sales', 'product_code', false, false, false, false);
INSERT INTO public.role_permissions VALUES (13, 'sales', 'user', false, false, false, false);
INSERT INTO public.role_permissions VALUES (14, 'sales', 'permission', false, false, false, false);
INSERT INTO public.role_permissions VALUES (29, 'user', 'project', true, true, true, true);
INSERT INTO public.role_permissions VALUES (30, 'user', 'customer', true, true, true, true);
INSERT INTO public.role_permissions VALUES (31, 'user', 'quotation', true, true, true, true);
INSERT INTO public.role_permissions VALUES (32, 'user', 'product', false, false, false, false);
INSERT INTO public.role_permissions VALUES (33, 'user', 'product_code', false, false, false, false);
INSERT INTO public.role_permissions VALUES (34, 'user', 'user', false, false, false, false);
INSERT INTO public.role_permissions VALUES (35, 'user', 'permission', false, false, false, false);
INSERT INTO public.role_permissions VALUES (36, 'channel_manager', 'project', true, true, true, true);
INSERT INTO public.role_permissions VALUES (37, 'channel_manager', 'customer', true, true, true, true);
INSERT INTO public.role_permissions VALUES (38, 'channel_manager', 'quotation', true, true, true, true);
INSERT INTO public.role_permissions VALUES (39, 'channel_manager', 'product', true, false, false, false);
INSERT INTO public.role_permissions VALUES (40, 'channel_manager', 'product_code', false, false, false, false);
INSERT INTO public.role_permissions VALUES (41, 'channel_manager', 'user', false, false, false, false);
INSERT INTO public.role_permissions VALUES (42, 'channel_manager', 'permission', false, false, false, false);
INSERT INTO public.role_permissions VALUES (57, '6e7a1ada', 'project', true, true, true, true);
INSERT INTO public.role_permissions VALUES (58, '6e7a1ada', 'customer', true, true, true, true);
INSERT INTO public.role_permissions VALUES (59, '6e7a1ada', 'quotation', true, true, true, true);
INSERT INTO public.role_permissions VALUES (60, '6e7a1ada', 'product', true, true, true, true);
INSERT INTO public.role_permissions VALUES (61, '6e7a1ada', 'product_code', false, false, false, false);
INSERT INTO public.role_permissions VALUES (62, '6e7a1ada', 'user', false, false, false, false);
INSERT INTO public.role_permissions VALUES (63, '6e7a1ada', 'permission', false, false, false, false);
INSERT INTO public.role_permissions VALUES (71, 'service_manager', 'project', true, true, true, true);
INSERT INTO public.role_permissions VALUES (72, 'service_manager', 'customer', true, true, true, true);
INSERT INTO public.role_permissions VALUES (73, 'service_manager', 'quotation', true, true, true, true);
INSERT INTO public.role_permissions VALUES (74, 'service_manager', 'product', true, false, false, false);
INSERT INTO public.role_permissions VALUES (75, 'service_manager', 'product_code', false, false, false, false);
INSERT INTO public.role_permissions VALUES (76, 'service_manager', 'user', false, false, false, false);
INSERT INTO public.role_permissions VALUES (77, 'service_manager', 'permission', false, false, false, false);
INSERT INTO public.role_permissions VALUES (78, 'ceo', 'project', true, true, true, true);
INSERT INTO public.role_permissions VALUES (79, 'ceo', 'customer', true, true, true, true);
INSERT INTO public.role_permissions VALUES (80, 'ceo', 'quotation', true, true, true, true);
INSERT INTO public.role_permissions VALUES (81, 'ceo', 'product', true, true, true, true);
INSERT INTO public.role_permissions VALUES (82, 'ceo', 'product_code', true, true, true, true);
INSERT INTO public.role_permissions VALUES (83, 'ceo', 'user', false, false, false, false);
INSERT INTO public.role_permissions VALUES (84, 'ceo', 'permission', false, false, false, false);


--
-- Name: actions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_user
--

SELECT pg_catalog.setval('public.actions_id_seq', 9, true);


--
-- Name: affiliations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_user
--

SELECT pg_catalog.setval('public.affiliations_id_seq', 1, false);


--
-- Name: companies_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_user
--

SELECT pg_catalog.setval('public.companies_id_seq', 1, false);


--
-- Name: contacts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_user
--

SELECT pg_catalog.setval('public.contacts_id_seq', 1, false);


--
-- Name: data_affiliations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_user
--

SELECT pg_catalog.setval('public.data_affiliations_id_seq', 1, true);


--
-- Name: dev_product_specs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_user
--

SELECT pg_catalog.setval('public.dev_product_specs_id_seq', 1, false);


--
-- Name: dev_products_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_user
--

SELECT pg_catalog.setval('public.dev_products_id_seq', 1, false);


--
-- Name: dictionaries_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_user
--

SELECT pg_catalog.setval('public.dictionaries_id_seq', 28, true);


--
-- Name: permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_user
--

SELECT pg_catalog.setval('public.permissions_id_seq', 58, true);


--
-- Name: product_categories_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_user
--

SELECT pg_catalog.setval('public.product_categories_id_seq', 1, false);


--
-- Name: product_code_field_options_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_user
--

SELECT pg_catalog.setval('public.product_code_field_options_id_seq', 1, false);


--
-- Name: product_code_field_values_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_user
--

SELECT pg_catalog.setval('public.product_code_field_values_id_seq', 1, false);


--
-- Name: product_code_fields_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_user
--

SELECT pg_catalog.setval('public.product_code_fields_id_seq', 1, false);


--
-- Name: product_codes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_user
--

SELECT pg_catalog.setval('public.product_codes_id_seq', 1, false);


--
-- Name: product_regions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_user
--

SELECT pg_catalog.setval('public.product_regions_id_seq', 1, false);


--
-- Name: product_subcategories_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_user
--

SELECT pg_catalog.setval('public.product_subcategories_id_seq', 1, false);


--
-- Name: products_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_user
--

SELECT pg_catalog.setval('public.products_id_seq', 1, false);


--
-- Name: project_members_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_user
--

SELECT pg_catalog.setval('public.project_members_id_seq', 1, false);


--
-- Name: projects_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_user
--

SELECT pg_catalog.setval('public.projects_id_seq', 1, false);


--
-- Name: quotation_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_user
--

SELECT pg_catalog.setval('public.quotation_details_id_seq', 1, false);


--
-- Name: quotations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_user
--

SELECT pg_catalog.setval('public.quotations_id_seq', 1, false);


--
-- Name: role_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_user
--

SELECT pg_catalog.setval('public.role_permissions_id_seq', 84, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_user
--

SELECT pg_catalog.setval('public.users_id_seq', 1, false);


--
-- PostgreSQL database dump complete
--

