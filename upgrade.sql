alter table tb_Zet add column c_nofiscal int(4) default 0;
alter table tb_Zet add column c_saled int(4) default 0;
alter table tb_Zet add column `nf_summa` double(8,2) DEFAULT '0.00';
alter table tb_Zet add column `nf_discount` double(8,2) DEFAULT '0.00';
alter table tb_Zet add column `nf_bonus_discount` double(8,2) DEFAULT '0.00';
alter table tb_Zet add column `nf_vir` double(8,2) DEFAULT '0.00';
alter table tb_Zet_cont add column `isfiscal`  tinyint(1) default 0;
