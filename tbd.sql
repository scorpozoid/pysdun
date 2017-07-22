-- cp1251
set client_encoding to 'WIN1251';

--
-- connect to tcp:postgresql://{host}:{port}/{alias} user {username} identified by {password};
--
-- connect to tcp:postgresql://127.0.0.1:5432/postgres user postgres identified by ;
-- drop database ;
-- drop database {alias};
-- disconnect;
-- create database {alias};
--
-- connect to tcp:postgresql://127.0.0.1:5432/ user postgres identified by ;
--
--



create domain date_t as date;
create domain double_t as double precision;
create domain file_t as blob;
create domain filename_t as varchar(1024);
create domain int_t as integer;
create domain lla_t as varchar(128);
create domain text_t as varchar(1024);
create domain time_t as time;
create domain timestamp_t as timestamp;


create table akt_pd_p (id_akt_pd_p int_t not null, nom_akt_p text_t not null, naim_sr_p text_t not null, nom_p text_t not null, id_mest_p int_t not null, id_tth_p int_t not null, id_histor int_t not null);
create table bp (id_bp int_t not null, ser_bp text_t not null, n_bp int_t not null, dov_bp timestamp_t not null, podp_bp timestamp_t not null, dig_sign filename_t not null, id_mestdat int_t not null, id_vs_podr int_t not null, id_podrktk int_t not null, id_karta int_t not null, id_operob int_t not null, id_zadktk int_t not null, id_mestdat int_t not null, order_mark filename_t not null, id_zadktk int_t not null, id_vzsr int_t not null, id_rezzad int_t not null, got_bp timestamp_t not null, id_histor int_t not null);
create table br (id_br int_t not null, n_br double_t not null, t_d_polych timestamp_t not null, t_d_podpis timestamp_t not null, id_mestdat int_t not null, id_vs_podr int_t not null, id_dolgnost int_t not null, text_br text_t not null, id_obkon int_t not null, id__zadktk int_t not null, id_vzsr int_t not null, id_signupr int_t not null, id_obesp int_t not null, id_rezzad int_t not null, id_mestdat int_t not null, id_sxsviazi int_t not null, id_infsrsil int_t not null, id_meteo int_t not null, id_norrukdoc int_t not null, id_rxbz int_t not null, id_pnm int_t not null, id_histor int_t not null);
create table bz_f (id_bz_f int_t not null, n_bz_f text_t not null, ser_bz_f text_t not null, id_vs_podr int_t not null, id_vs_podr int_t not null, time_bz_f timestamp_t not null, nah_bz_f timestamp_t not null, kon_bz_f timestamp_t not null, id_obkon int_t not null, id_meteo int_t not null, id_mestdat int_t not null, id_sviaz int_t not null, id_ogrzap int_t not null, id_zadktk int_t not null, id_xarok int_t not null, id_texn int_t not null, vip_bz_f timestamp_t not null, id_vs_podr int_t not null, id_vs_podr int_t not null, id_rezzad int_t not null, id_histor int_t not null);
create table bz_k (id_bz_k int_t not null, n_bz_k text_t not null, ser_bz_k text_t not null, id_vs_podr int_t not null, id_vs_podr int_t not null, time_bz_k timestamp_t not null, nah_bz_k timestamp_t not null, kon_bz_k timestamp_t not null, id_obkon int_t not null, id_sviaz int_t not null, id_ogrzap int_t not null, id_zadktk int_t not null, id_xarok int_t not null, id_texn int_t not null, vip_bz_k timestamp_t not null, id_vs_podr int_t not null, id_vs_podr int_t not null, id_rezzad int_t not null, id_histor int_t not null);
create table bz_r (id_bz_r int_t not null, n_bz_r text_t not null, ser_bz_r text_t not null, id_vs_podr int_t not null, id_vs_podr int_t not null, time_bz_r timestamp_t not null, nah_bz_r timestamp_t not null, kon_bz_r timestamp_t not null, id_obkon int_t not null, id_frenizl int_t not null, id_sviaz int_t not null, id_ogrzap int_t not null, id_zadktk int_t not null, id_xarok int_t not null, id_texn int_t not null, vip_bz_r timestamp_t not null, id_vs_podr int_t not null, id_vs_podr int_t not null, id_rezzad int_t not null, id_histor int_t not null);
create table bz_t (id_bz_t int_t not null, n_bz_t text_t not null, ser_bz_t text_t not null, id_vs_podr int_t not null, id_vs_podr int_t not null, time_bz_t timestamp_t not null, nah_bz_t timestamp_t not null, kon_bz_t timestamp_t not null, id_obkon int_t not null, id_sviaz int_t not null, id_ogrzap int_t not null, id_zadktk int_t not null, id_xarok int_t not null, id_texn int_t not null, vip_bz_t timestamp_t not null, id_vs_podr int_t not null, id_vs_podr int_t not null, id_rezzad int_t not null, id_histor int_t not null);
create table docrez (id_docrez int_t not null, name_doc text_t not null, tip_doc text_t not null, id_dolgnost int_t not null, nomer_doc text_t not null, sod_docrez filename_t not null, d_t_doc timestamp_t not null, dop_doc text_t not null, id_dolgnost int_t not null, id_histor int_t not null);
create table dolgnost (id_dolgnost int_t not null, n_dolgnost text_t not null, id_podrktk int_t not null, vus_dolgnost text_t not null, id_histor int_t not null);
create table dprizn (id_dprizn int_t not null, name_dprizn text_t not null, id__os int_t not null, xar_dprizn text_t not null, id_histor int_t not null);
create table dvigenie (id_dvigenie int_t not null, ed_dvigenie text_t not null, sr_dvigenie text_t not null, max_dvigenie text_t not null, min_dvigenie text_t not null, dis_dvigenie text_t not null, mas_dvigenie text_t not null, prim_dvigenie text_t not null, id_histor int_t not null);
create table energ_ogr_p (id_ener_ogr_p int_t not null, id_nom_por_p text_t not null, min_moh_izl_p text_t not null, dop_moh_izl_p text_t not null, id_histor int_t not null);
create table frenizl (id_frenizl int_t not null, tip_frenizl text_t not null, ed_frenizl text_t not null, niz_frenizl text_t not null, sr_frenizl text_t not null, ver_frenizl text_t not null, pog_frenizl text_t not null, id_histor int_t not null);
create table haraks (id_haraks int_t not null, name_haraks text_t not null, par_haraks text_t not null, vel_haraks text_t not null, max_haraks text_t not null, min_haraks text_t not null, id_histor int_t not null);
create table has_ogr_p (id_has_ogr_p int_t not null, id_nom_por_p text_t not null, n_gr_p text_t not null, v_gr_p text_t not null, id_histor int_t not null);
create table him_zar_p (id_him_zar_p int_t not null, naim_p text_t not null, dat_vrem_p timestamp_t not null, id_ok_p int_t not null, dat_vrem_zar_p timestamp_t not null, tip_bh_p text_t not null, tip_ov_p text_t not null, id_histor int_t not null);
create table histor (id_histor int_t not null, d_t_histor timestamp_t not null, id_pole text_t not null, dest_bd text_t not null, zn_pole text_t not null, id_polz int_t not null, id_bd int_t not null);
create table iad_vzr_p (id_iad_vzr_p int_t not null, naim_p text_t not null, dat_vrem_p timestamp_t not null, vrem_p time_t not null, vid_p text_t not null, moh_p text_t not null, vis_p text_t not null, id_ok_p int_t not null, prin_p text_t not null, rad_p text_t not null, boepr_p text_t not null, id_histor int_t not null);
create table infsrsil (id_infsrsil int_t not null, id_l_s int_t not null, id_texn int_t not null, id_vs_podr int_t not null, id_histor int_t not null);
create table ishdan (id_ishdan int_t not null, n_ishdan text_t not null, v_ishdan text_t not null, ed_ishdan text_t not null, id_histor int_t not null);
create table karta (id_karta int_t not null, karta filename_t not null, god_karta date_t not null, id_histor int_t not null);
create table kolona (id_kolona int_t not null, id_texn int_t not null, id_dvigenie int_t not null, id_texn int_t not null, id_dvigenie int_t not null, zgd_kolona text_t not null, id_texn int_t not null, id_dvigenie int_t not null, ztd_kolona text_t not null, id_texn int_t not null, id_dvigenie int_t not null, ztz_kolona text_t not null, id_histor int_t not null);
create table l_s (id_l_s int_t not null, id_vs_podr int_t not null, id_vs_podr int_t not null, id_histor int_t not null);
create table mer_dd_p (id_mer_dd_p int_t not null, id_ok_p <REF> not null, mer_skrit_p text_t not null, id_histor int_t not null);
create table mer_im_p (id_mer_im_p int_t not null, id_ok_p <REF> not null, mer_imit_p text_t not null, id_histor int_t not null);
create table mer_pd_p (id_mer_pd__p int_t not null, nom_por_p text_t not null, has_ogr_p int_t not null, pros_ogr_p int_t not null, energ_ogr_p int_t not null, vrem_ogr_p int_t not null, id_histor int_t not null);
create table mer_skr_p (id_mer_skr_p int_t not null, id_ok_p <REF> not null, mer_skrit_p text_t not null, id_histor int_t not null);
create table mer_suv_p (id_mer_suv_p int_t not null, id_ok_p <REF> not null, mer_suvos_p text_t not null, id_histor int_t not null);
create table merapd (id_merapd int_t not null, naimemerapd text_t not null, zadmerapd text_t not null, id__os int_t not null, id_histor int_t not null);
create table mestdat (id_mestdat int_t not null, tip_mest text_t not null, naim_punkta text_t not null, koord lla_t not null, dat_vr_mest timestamp_t not null, prim_mest text_t not null, podst_mestdat text_t not null, id_histor int_t not null);
create table meteo (id_meteo int_t not null, n_meteo text_t not null, tip_meteo text_t not null, x_meteo text_t not null, time_meteo date_t not null, id_mestdat int_t not null, par_meteo text_t not null, zn_meteo text_t not null, id_histor int_t not null);
create table mnogoug (id_mnog int_t not null, soedin_tohki text_t not null, koord_1 lla_t not null, nom_tohki <REF> not null, koord_tohki <REF> not null, sl_lin filename_t not null);
create table norrukdoc (id_norrukdoc int_t not null, naim_doc text_t not null, tip_doc text_t not null, sod_doc filename_t not null, time_doc timestamp_t not null, inf_doc filename_t not null, id_histor int_t not null);
create table ob_reo_p (id_ob_reo_p int_t not null, nom_ppp_p text_t not null, dat_vrem_p timestamp_t not null, naim_p text_t not null, prin_p text_t not null, nom_v_h_p text_t not null, tip_p text_t not null, sostav_p text_t not null, kateg_p text_t not null, id_ok_p int_t not null, graf_p file_t not null, id_rad_d int_t not null, id_histor int_t not null);
create table obesp (id_obesp int_t not null, name_obesp text_t not null, id_obkon int_t not null, sost_obesp text_t not null);
create table obkon (id_obkon int_t not null, id_prinok int_t not null, naim_obkon text_t not null, vh_obkon text_t not null, sokr_obkon text_t not null, vag_obkon text_t not null, kat_obkon text_t not null, id_mer_suv_p int_t not null, id_ttx_ok int_t not null, id_sviaz int_t not null, id_os int_t not null, id_dprizn int_t not null, id_merapd int_t not null, id_histor int_t not null);
create table ogrzap (id_ogrzap int_t not null, nah_ogrzap timestamp_t not null, kon_ogrzap timestamp_t not null, n_ogrzap text_t not null, id_mestdat int_t not null, par_ogrzap text_t not null, vel_ogrzap text_t not null, id_histor int_t not null);
create table operob (id_operob int_t not null, id_karta int_t not null, id_oper <REF> not null, id_histor int_t not null);
create table os (id_os int_t not null, n_os text_t not null, par_os text_t not null, ed_os text_t not null, zn_os text_t not null, id_norrukdoc int_t not null, id_histor int_t not null);
create table pnm (id_pnm int_t not null, ser_pnm text_t not null, nom_pnm text_t not null, pol_pnm timestamp_t not null, podp_pnm timestamp_t not null, id_mestdat int_t not null, id_vs_podr int_t not null, id_podrktk int_t not null, id_karta int_t not null, id_operob int_t not null, viv_pnm text_t not null, id_mestdat int_t not null, id_mestdat int_t not null, id_kolona int_t not null, id_mestdat int_t not null, id_mestdat int_t not null, id_mestdat int_t not null, got_pnm timestamp_t not null, id_karta int_t not null, id_zadktk int_t not null, id_signupr int_t not null, id_sviaz int_t not null, id_histor int_t not null);
create table podrktk (id_podrktk int_t not null, n_podrktk text_t not null, naz_podrktk text_t not null, xar_podrktk text_t not null, sos_podrktk text_t not null, id_zadktk int_t not null, id_histor int_t not null);
create table prinok (id_prinok int_t not null, id_obkon int_t not null, nazn_prinok text_t not null, inf_prinok text_t not null, svz_prinok text_t not null, id_histor int_t not null);
create table pros_ogr_p (id_pros_ogr_p int_t not null, id_nom_por_p text_t not null, n_gr_sek_p text_t not null, v_gr_sek__p text_t not null, id_histor int_t not null);
create table rad_d_p (id_rad_d_p int_t not null, abon_p text_t not null, poz_p text_t not null, osn_f_p text_t not null, zap_f_p text_t not null, reg_p file_t not null, graf_p file_t not null, id_histor int_t not null);
create table rad_obst_p (id_rad_obst_p int_t not null, naim_p text_t not null, dat_vrem_p timestamp_t not null, raion_p file_t not null, id_ok_p int_t not null, urov_rd_p text_t not null, vrem_p time_t not null, istoh_p text_t not null, id_histor int_t not null);
create table raion (id_raion int_t not null, naim_raion text_t not null, tip_raion text_t not null, radius_raion double_t not null, koord lla_t not null, id_mnog int_t not null);
create table rezzad (id_rezzad int_t not null, name_rezzad text_t not null, d_t_rezzad timestamp_t not null, d_p_rezzad timestamp_t not null, d_pod_rezzad timestamp_t not null, tip_rezzad filename_t not null, sod_rezzad filename_t not null, id_histor int_t not null);
create table rxbz (id_rxbz int_t not null, op_rxbz text_t not null, sos_rxbz text_t not null, x_rxbz text_t not null, time_rxbz date_t not null, id_mestdat int_t not null, par_rxbz text_t not null, zn_rxbz text_t not null, inf_rxbz text_t not null, id_histor int_t not null);
create table signupr (id_signupr int_t not null, kan_signupr text_t not null, name_signupr text_t not null, dest_signupr text_t not null, znah_signupr text_t not null, id_histor int_t not null);
create table soob_biol_obst_p (id_soob_biol_obst_p int_t not null, dat_vrem_poluh_p timestamp_t not null, soder_soob_p text_t not null, id_biol_zar_p int_t not null, id_histor int_t not null);
create table soob_him_obst_p (id_soob_him_obst_p int_t not null, dat_vrem_poluh_p timestamp_t not null, soder_soob_p text_t not null, id_him_zar_p int_t not null, id_histor int_t not null);
create table soob_iad_vzr_p (id_soob_iad_vzr_p int_t not null, dat_vrem_poluh_p timestamp_t not null, soder_soob_p text_t not null, id_iad_vzr_p int_t not null, id_histor int_t not null);
create table soob_reo_p (id_soob_reo_p int_t not null, dat_vrem_poluh_p timestamp_t not null, soder_soob_p text_t not null, id_ob_reo_p int_t not null, id_histor int_t not null);
create table spektr (id_spektr int_t not null, tip_spektr text_t not null, ed_spektr text_t not null, nf_spektr text_t not null, sf_spektr text_t not null, vf_spektr text_t not null, pog_spektr text_t not null, dev_spektr text_t not null, mod_spektr text_t not null, tr_spektr filename_t not null, id_histor int_t not null);
create table st_vip_zad (id_st_vip_zad int_t not null, t_st_vip_zad date_t not null, v_st_vip_zad text_t not null, ed_st_vip_zad text_t not null, id_histor int_t not null);
create table sviaz (id_sviaz int_t not null, ab_sviaz text_t not null, poz_sviaz text_t not null, fren_os_sviaz text_t not null, fren_zp_sviaz text_t not null, reg_sviaz text_t not null, gr_sviaz filename_t not null, id_histor int_t not null);
create table sxsviazi (id_sxsviazi int_t not null, sxsviazi filename_t not null, id_histor int_t not null);
create table tekmesto (id_tekmesto int_t not null, nam_tekmesto text_t not null, kor_tekmesto lla_t not null, pl_tekmesto int_t not null, vid_tekmesto text_t not null, mob_tekmesto text_t not null, id_histor int_t not null);
create table texn (id_texn int_t not null, name_texn text_t not null, ser_n_texn text_t not null, id_ttx int_t not null, sost_texn text_t not null, pov_texn date_t not null, dv_texn date_t not null, nor_texn filename_t not null, doc_texn filename_t not null, to_texn filename_t not null, esx_texn filename_t not null, id_histor int_t not null);
create table tsr_har_p (id_tsr_har_p int_t not null, non_pp_p text_t not null, tip_p text_t not null, naim_p text_t not null, vid_p text_t not null, isp_p text_t not null, id_mestdat int_t not null, reg_p text_t not null, vis_p text_t not null, knd_p text_t not null, koef_p text_t not null, nig_f_p text_t not null, ver_f_p text_t not null, huvst_p text_t not null, id_histor int_t not null);
create table tsr_p (id_tsr_p int_t not null, dat_vrem_poluh_p timestamp_t not null, soder_soob_p text_t not null, id_tsr_har_p int_t not null, id_ok_p int_t not null, id_histor int_t not null);
create table tth_p (id_tth_p int_t not null, vis_p text_t not null, koef_p text_t not null, hir_p text_t not null, n_gr_p text_t not null, v_gr_p text_t not null, i_moh_p text_t not null, sr_moh_p text_t not null, hir_sp_p text_t not null, tip_pom_p text_t not null, id_histor int_t not null);
create table ttx (id_ttx int_t not null, id_haraks int_t not null, id_histor int_t not null);
create table ttx_ok (id_ttx_ok int_t not null, id_xarok int_t not null, id_xar_izlok int_t not null, id_xar_one int_t not null, id_ogrzap int_t not null, id_histor int_t not null);
create table vrem_ogr_p (id_vr_ogr_p int_t not null, vr_per_p text_t not null, id_nom_por_p text_t not null, nah_vr_izl_p text_t not null, kon_vr_izl_p text_t not null, id_histor int_t not null);
create table vs_podr (id_vs_podr int_t not null, fio_vs_podr text_t not null, d_vs_podr date_t not null, n_vs_podr text_t not null, vs_podr text_t not null, id_dolgnost int_t not null, or_vs_podr text_t not null, x_vs_podr text_t not null, id_histor int_t not null);
create table vzsr (id_vzsr int_t not null, id_prinok <REF> not null, zad_vzsr text_t not null, ogr_vzsr text_t not null, spos_vzsr text_t not null, id_sviaz int_t not null, vzaim_vzsr text_t not null, his_per_dan filename_t not null, his_prin_dan filename_t not null, org_vzsr text_t not null);
create table xar_izlok (id_xar_izlok int_t not null, id_frenizl int_t not null, id_spektr int_t not null, id_ int_t not null, o_xar_izlok text_t not null, d_t_izl timestamp_t not null, dek_izl text_t not null, zap_izl filename_t not null, dek_izl filename_t not null, etal_izl filename_t not null, id_haraks int_t not null, tip_izl text_t not null, nes_izl text_t not null, hir_izl text_t not null, pol_prop text_t not null, urov_izl text_t not null, s_h_izl text_t not null, tip_sign text_t not null, peleng text_t not null, pelen_izl text_t not null, id_histor int_t not null);
create table xar_one (id__xar_one int_t not null, id_haraks int_t not null, id_histor int_t not null);
create table xarok (id_xarok int_t not null, name_xarok text_t not null, id_haraks int_t not null, id_haraks int_t not null, id_histor int_t not null);
create table zadktk (id_zadktk int_t not null, tip_zad text_t not null, id_obkon int_t not null, naim_zadktk text_t not null, spos_zadktk text_t not null, id_vs_podr int_t not null, nach_zadktk timestamp_t not null, okon_zadktk timestamp_t not null, id_mestdat int_t not null, zel_zadktk text_t not null, vag_zadktk text_t not null, id_st_vip_zad int_t not null, itog_zadktk text_t not null, id_docrez int_t not null, id_ishdan int_t not null, id_histor int_t not null);








alter table mer_dd_p add constraint fk_mer_dd_p_id_ok_p_<TABLE>_id_ok_p foreign key (id_ok_p) references <TABLE> (id_ok_p) cascade cascade;;
alter table mer_im_p add constraint fk_mer_im_p_id_ok_p_<TABLE>_id_ok_p foreign key (id_ok_p) references <TABLE> (id_ok_p) cascade cascade;;
alter table mer_skr_p add constraint fk_mer_skr_p_id_ok_p_<TABLE>_id_ok_p foreign key (id_ok_p) references <TABLE> (id_ok_p) cascade cascade;;
alter table mer_suv_p add constraint fk_mer_suv_p_id_ok_p_<TABLE>_id_ok_p foreign key (id_ok_p) references <TABLE> (id_ok_p) cascade cascade;;
alter table mnogoug add constraint fk_mnogoug_koord_tohki_<TABLE>_koord_tohki foreign key (koord_tohki) references <TABLE> (koord_tohki) cascade cascade;;
alter table mnogoug add constraint fk_mnogoug_nom_tohki_<TABLE>_nom_tohki foreign key (nom_tohki) references <TABLE> (nom_tohki) cascade cascade;;
alter table operob add constraint fk_operob_id_oper_<TABLE>_id_oper foreign key (id_oper) references <TABLE> (id_oper) cascade cascade;;
alter table vzsr add constraint fk_vzsr_id_prinok_<TABLE>_id_prinok foreign key (id_prinok) references <TABLE> (id_prinok) cascade cascade;;


/* EOF */
