yosys -import
setundef -zero
read_verilog -sv /scratch/perf_area_eff/experiment_7ca0dda7/syn_obj/input_src/DivSqrtRawFN_small_e11_s53.sv
read_verilog -sv /scratch/perf_area_eff/experiment_7ca0dda7/syn_obj/input_src/DivSqrtRecFMToRaw_small_e11_s53.sv
read_verilog -sv /scratch/perf_area_eff/experiment_7ca0dda7/syn_obj/input_src/DivSqrtRecFM_small_e11_s53.sv
read_verilog -sv /scratch/perf_area_eff/experiment_7ca0dda7/syn_obj/input_src/FDivSqrtUnit.sv
read_verilog -sv /scratch/perf_area_eff/experiment_7ca0dda7/syn_obj/input_src/FPToFP.sv
read_verilog -sv /scratch/perf_area_eff/experiment_7ca0dda7/syn_obj/input_src/FPUExeUnit.sv
read_verilog -sv /scratch/perf_area_eff/experiment_7ca0dda7/syn_obj/input_src/MulAddRecFNPipe_l2_e11_s53.sv
read_verilog -sv /scratch/perf_area_eff/experiment_7ca0dda7/syn_obj/input_src/RecFNToRecFN.sv
read_verilog -sv /scratch/perf_area_eff/experiment_7ca0dda7/syn_obj/input_src/RecFNToRecFN_1.sv
read_verilog -sv /scratch/perf_area_eff/experiment_7ca0dda7/syn_obj/input_src/RoundAnyRawFNToRecFN_ie11_is53_oe8_os24.sv
read_verilog -sv /scratch/perf_area_eff/experiment_7ca0dda7/syn_obj/input_src/RoundAnyRawFNToRecFN_ie11_is55_oe11_os53.sv
read_verilog -sv /scratch/perf_area_eff/experiment_7ca0dda7/syn_obj/input_src/RoundAnyRawFNToRecFN_ie8_is24_oe11_os53.sv
read_verilog -sv /scratch/perf_area_eff/experiment_7ca0dda7/syn_obj/input_src/RoundRawFNToRecFN_e11_s53.sv
read_verilog -sv /scratch/perf_area_eff/experiment_7ca0dda7/syn_obj/input_src/UOPCodeFDivDecoder.sv
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__ff_100C_1v65.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__ff_100C_1v95.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__ff_n40C_1v56.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__ff_n40C_1v65.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__ff_n40C_1v76.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__ff_n40C_1v95_ccsnoise.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__ss_100C_1v40.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__ss_100C_1v60.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__ss_n40C_1v28.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__ss_n40C_1v35.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__ss_n40C_1v40.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__ss_n40C_1v44.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__ss_n40C_1v60_ccsnoise.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__ss_n40C_1v76.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_100C_1v80.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__gpiov2_pad_tt_tt_025C_1v80_3v30.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__gpiov2_pad_wrapped_ff_ff_100C_1v95_5v50.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__gpiov2_pad_wrapped_ff_ff_n40C_1v95_5v50.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__gpiov2_pad_wrapped_ss_ss_100C_1v60_3v00.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__gpiov2_pad_wrapped_tt_tt_025C_1v80_3v30.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vccd_lvc_clamped3_pad_ff_100C_1v95_5v50_5v50.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vccd_lvc_clamped3_pad_ff_n40C_1v95_5v50_5v50.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vccd_lvc_clamped3_pad_ss_100C_1v60_3v00_3v00.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vccd_lvc_clamped3_pad_tt_025C_1v80_3v30_3v30.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vccd_lvc_clamped_pad_ff_100C_1v95_5v50_5v50.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vccd_lvc_clamped_pad_ff_n40C_1v95_5v50_5v50.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vccd_lvc_clamped_pad_ss_100C_1v60_3v00_3v00.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vccd_lvc_clamped_pad_tt_025C_1v80_3v30_3v30.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vdda_hvc_clamped_pad_ff_100C_1v95_5v50_5v50.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vdda_hvc_clamped_pad_ff_n40C_1v95_5v50_5v50.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vdda_hvc_clamped_pad_ss_100C_1v60_3v00_3v00.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vdda_hvc_clamped_pad_tt_025C_1v80_3v30_3v30.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vddio_hvc_clamped_pad_ff_100C_1v95_5v50_5v50.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vddio_hvc_clamped_pad_ff_n40C_1v95_5v50_5v50.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vddio_hvc_clamped_pad_ss_100C_1v60_3v00_3v00.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vddio_hvc_clamped_pad_tt_025C_1v80_3v30_3v30.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vssa_hvc_clamped_pad_ff_100C_1v95_5v50_5v50.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vssa_hvc_clamped_pad_ff_n40C_1v95_5v50_5v50.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vssa_hvc_clamped_pad_ss_100C_1v60_3v00_3v00.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vssa_hvc_clamped_pad_tt_025C_1v80_3v30_3v30.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vssd_lvc_clamped3_pad_ff_100C_1v95_5v50.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vssd_lvc_clamped3_pad_ff_n40C_1v95_5v50.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vssd_lvc_clamped3_pad_ss_100C_1v60_3v00.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vssd_lvc_clamped3_pad_tt_025C_1v80_3v30.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vssd_lvc_clamped3_pad_tt_100C_1v80_3v30.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vssd_lvc_clamped_pad_ff_100C_1v95_5v50.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vssd_lvc_clamped_pad_ff_n40C_1v95_5v50.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vssd_lvc_clamped_pad_ss_100C_1v60_3v00.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vssd_lvc_clamped_pad_tt_025C_1v80_3v30.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vssd_lvc_clamped_pad_tt_100C_1v80_3v30.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vssio_hvc_clamped_pad_ff_100C_1v95_5v50_5v50.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vssio_hvc_clamped_pad_ff_n40C_1v95_5v50_5v50.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vssio_hvc_clamped_pad_ss_100C_1v60_3v00_3v00.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vssio_hvc_clamped_pad_tt_025C_1v80_3v30_3v30.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_gpiov2_ff_ff_100C_1v95_5v50.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_gpiov2_ff_ff_n40C_1v95_5v50.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_gpiov2_ss_ss_100C_1v60_3v00.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_gpiov2_tt_tt_025C_1v80_3v30.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_ground_hvc_wpad_ff_100C_1v95_5v50_5v50.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_ground_hvc_wpad_ff_n40C_1v95_5v50_5v50.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_ground_hvc_wpad_ss_100C_1v60_3v00_3v00.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_ground_hvc_wpad_tt_025C_1v80_3v30_3v30.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_ground_lvc_wpad_ff_100C_1v95_5v50.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_ground_lvc_wpad_ff_n40C_1v95_5v50.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_ground_lvc_wpad_ss_100C_1v60_3v00.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_ground_lvc_wpad_tt_025C_1v80_3v30.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_ground_lvc_wpad_tt_100C_1v80_3v30.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_power_hvc_wpad_ff_100C_1v95_5v50_5v50.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_power_hvc_wpad_ff_n40C_1v95_5v50_5v50.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_power_hvc_wpad_ss_100C_1v60_3v00_3v00.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_power_hvc_wpad_tt_025C_1v80_3v30_3v30.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_power_lvc_wpad_ff_100C_1v95_5v50_5v50.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_power_lvc_wpad_ff_n40C_1v95_5v50_5v50.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_power_lvc_wpad_ss_100C_1v60_3v00_3v00.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_power_lvc_wpad_tt_025C_1v80_3v30_3v30.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_xres4v2_ff_ff_100C_1v95_5v50.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_xres4v2_ff_ff_n40C_1v95_5v50.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_xres4v2_ss_ss_100C_1v60_3v00.lib
read_liberty -lib /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_xres4v2_tt_tt_025C_1v80_3v30.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/cc_dir_ext_ff_n40C_1v95.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/cc_dir_ext_ss_100C_1v60.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/cc_dir_ext_tt_025C_1v80.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/cc_banks_0_ext_ff_n40C_1v95.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/cc_banks_0_ext_ss_100C_1v60.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/cc_banks_0_ext_tt_025C_1v80.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/tag_array_ext_ff_n40C_1v95.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/tag_array_ext_ss_100C_1v60.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/tag_array_ext_tt_025C_1v80.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/array_0_0_0_ext_ff_n40C_1v95.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/array_0_0_0_ext_ss_100C_1v60.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/array_0_0_0_ext_tt_025C_1v80.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/tag_array_0_ext_ff_n40C_1v95.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/tag_array_0_ext_ss_100C_1v60.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/tag_array_0_ext_tt_025C_1v80.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/dataArrayWay_0_ext_ff_n40C_1v95.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/dataArrayWay_0_ext_ss_100C_1v60.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/dataArrayWay_0_ext_tt_025C_1v80.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/table_ext_ff_n40C_1v95.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/table_ext_ss_100C_1v60.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/table_ext_tt_025C_1v80.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/table_0_ext_ff_n40C_1v95.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/table_0_ext_ss_100C_1v60.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/table_0_ext_tt_025C_1v80.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/table_1_ext_ff_n40C_1v95.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/table_1_ext_ss_100C_1v60.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/table_1_ext_tt_025C_1v80.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/btb_0_ext_ff_n40C_1v95.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/btb_0_ext_ss_100C_1v60.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/btb_0_ext_tt_025C_1v80.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/ebtb_ext_ff_n40C_1v95.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/ebtb_ext_ss_100C_1v60.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/ebtb_ext_tt_025C_1v80.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/data_ext_ff_n40C_1v95.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/data_ext_ss_100C_1v60.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/data_ext_tt_025C_1v80.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/meta_0_ext_ff_n40C_1v95.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/meta_0_ext_ss_100C_1v60.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/meta_0_ext_tt_025C_1v80.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/ghist_0_ext_ff_n40C_1v95.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/ghist_0_ext_ss_100C_1v60.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/ghist_0_ext_tt_025C_1v80.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/rob_debug_inst_mem_ext_ff_n40C_1v95.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/rob_debug_inst_mem_ext_ss_100C_1v60.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/rob_debug_inst_mem_ext_tt_025C_1v80.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/l2_tlb_ram_0_ext_ff_n40C_1v95.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/l2_tlb_ram_0_ext_ss_100C_1v60.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/l2_tlb_ram_0_ext_tt_025C_1v80.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/mem_ext_ff_n40C_1v95.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/mem_ext_ss_100C_1v60.lib
read_liberty -lib /tmp/hammer_sky130_open_6mswgok0/cacti_libs/mem_ext_tt_025C_1v80.lib
puts "(hammer) yosys proc"
yosys proc
puts "(hammer) hierarchy -check -top FDivSqrtUnit"
hierarchy -check -top FDivSqrtUnit

puts "(hammer) synth -top FDivSqrtUnit"
synth -top FDivSqrtUnit

# Optimize the design
puts "(hammer) opt -purge"
opt -purge

# Technology mapping of latches
puts "(hammer) techmap -map /home/ray/conda-sky130/share/pdk/sky130A/libs.tech/openlane/sky130_fd_sc_hd/latch_map.v"
techmap -map /home/ray/conda-sky130/share/pdk/sky130A/libs.tech/openlane/sky130_fd_sc_hd/latch_map.v

# Technology mapping of flip-flops
puts "dfflibmap -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib" 
dfflibmap -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib
puts "opt" 
opt
# Technology mapping for cells
# ABC supports multiple liberty files, but the hook from Yosys to ABC doesn't
# TODO: this is a bad way of getting one liberty file, need a way to merge all std cell lib files
# NOTE: this breaks for any PDK that has multiple LIB files for std cell library
puts "(hammer) abc -D 20000"
abc -D 20000 \
    -constr "/scratch/perf_area_eff/experiment_7ca0dda7/syn_obj/syn-rundir/FDivSqrtUnit.mapped.sdc" \
    -liberty "/home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib" \
    -showtmp

# Replace undef values with defined constants
# TODO: do we need this??
puts "(hammer) setundef -zero"
setundef -zero

# Split multi-bit nets into single-bit nets.
# Splitting nets resolves unwanted compound assign statements in netlist (assign [..] = [..])
puts "(hammer) splitnets"
splitnets

# Remove unused cells and wires
puts "(hammer) opt_clean -purge"
opt_clean -purge
# Technology mapping of constant hi- and/or lo-drivers
puts "(hammer) hilomap -singleton"
hilomap -singleton \
        -hicell {*}sky130_fd_sc_hd__conb_1 HI \
        -locell {*}sky130_fd_sc_hd__conb_1 LO
# Insert driver cells for pass through wires
puts "(hammer) insbuf -buf {*}sky130_fd_sc_hd__buf_4 A X"
insbuf -buf {*}sky130_fd_sc_hd__buf_4 A X
puts "(hammer) tee -o /scratch/perf_area_eff/experiment_7ca0dda7/syn_obj/syn-rundir/FDivSqrtUnit.synth_check.rpt check"
tee -o /scratch/perf_area_eff/experiment_7ca0dda7/syn_obj/syn-rundir/FDivSqrtUnit.synth_check.rpt check

puts "(hammer) tee -o /scratch/perf_area_eff/experiment_7ca0dda7/syn_obj/syn-rundir/FDivSqrtUnit.synth_stat.txt stat -top FDivSqrtUnit -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__gpiov2_pad_tt_tt_025C_1v80_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__gpiov2_pad_wrapped_tt_tt_025C_1v80_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vccd_lvc_clamped3_pad_tt_025C_1v80_3v30_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vccd_lvc_clamped_pad_tt_025C_1v80_3v30_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vdda_hvc_clamped_pad_tt_025C_1v80_3v30_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vddio_hvc_clamped_pad_tt_025C_1v80_3v30_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vssa_hvc_clamped_pad_tt_025C_1v80_3v30_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vssd_lvc_clamped3_pad_tt_025C_1v80_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vssd_lvc_clamped_pad_tt_025C_1v80_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vssio_hvc_clamped_pad_tt_025C_1v80_3v30_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_gpiov2_tt_tt_025C_1v80_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_ground_hvc_wpad_tt_025C_1v80_3v30_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_ground_lvc_wpad_tt_025C_1v80_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_power_hvc_wpad_tt_025C_1v80_3v30_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_power_lvc_wpad_tt_025C_1v80_3v30_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_xres4v2_tt_tt_025C_1v80_3v30.lib -liberty /tmp/hammer_sky130_open_6mswgok0/cacti_libs/cc_dir_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_6mswgok0/cacti_libs/cc_banks_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_6mswgok0/cacti_libs/tag_array_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_6mswgok0/cacti_libs/array_0_0_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_6mswgok0/cacti_libs/tag_array_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_6mswgok0/cacti_libs/dataArrayWay_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_6mswgok0/cacti_libs/table_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_6mswgok0/cacti_libs/table_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_6mswgok0/cacti_libs/table_1_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_6mswgok0/cacti_libs/btb_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_6mswgok0/cacti_libs/ebtb_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_6mswgok0/cacti_libs/data_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_6mswgok0/cacti_libs/meta_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_6mswgok0/cacti_libs/ghist_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_6mswgok0/cacti_libs/rob_debug_inst_mem_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_6mswgok0/cacti_libs/l2_tlb_ram_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_6mswgok0/cacti_libs/mem_ext_tt_025C_1v80.lib"
tee -o /scratch/perf_area_eff/experiment_7ca0dda7/syn_obj/syn-rundir/FDivSqrtUnit.synth_stat.txt stat -top FDivSqrtUnit -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__gpiov2_pad_tt_tt_025C_1v80_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__gpiov2_pad_wrapped_tt_tt_025C_1v80_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vccd_lvc_clamped3_pad_tt_025C_1v80_3v30_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vccd_lvc_clamped_pad_tt_025C_1v80_3v30_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vdda_hvc_clamped_pad_tt_025C_1v80_3v30_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vddio_hvc_clamped_pad_tt_025C_1v80_3v30_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vssa_hvc_clamped_pad_tt_025C_1v80_3v30_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vssd_lvc_clamped3_pad_tt_025C_1v80_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vssd_lvc_clamped_pad_tt_025C_1v80_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vssio_hvc_clamped_pad_tt_025C_1v80_3v30_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_gpiov2_tt_tt_025C_1v80_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_ground_hvc_wpad_tt_025C_1v80_3v30_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_ground_lvc_wpad_tt_025C_1v80_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_power_hvc_wpad_tt_025C_1v80_3v30_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_power_lvc_wpad_tt_025C_1v80_3v30_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_xres4v2_tt_tt_025C_1v80_3v30.lib -liberty /tmp/hammer_sky130_open_6mswgok0/cacti_libs/cc_dir_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_6mswgok0/cacti_libs/cc_banks_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_6mswgok0/cacti_libs/tag_array_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_6mswgok0/cacti_libs/array_0_0_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_6mswgok0/cacti_libs/tag_array_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_6mswgok0/cacti_libs/dataArrayWay_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_6mswgok0/cacti_libs/table_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_6mswgok0/cacti_libs/table_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_6mswgok0/cacti_libs/table_1_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_6mswgok0/cacti_libs/btb_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_6mswgok0/cacti_libs/ebtb_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_6mswgok0/cacti_libs/data_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_6mswgok0/cacti_libs/meta_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_6mswgok0/cacti_libs/ghist_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_6mswgok0/cacti_libs/rob_debug_inst_mem_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_6mswgok0/cacti_libs/l2_tlb_ram_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_6mswgok0/cacti_libs/mem_ext_tt_025C_1v80.lib
puts "(hammer) write_verilog -noattr -noexpr -nohex -nodec -defparam \"/scratch/perf_area_eff/experiment_7ca0dda7/syn_obj/syn-rundir/FDivSqrtUnit.mapped.v\""
write_verilog -noattr -noexpr -nohex -nodec -defparam "/scratch/perf_area_eff/experiment_7ca0dda7/syn_obj/syn-rundir/FDivSqrtUnit.mapped.v"

# flatten

# # OpenROAD will throw an error if the verilog from Yosys is not flattened
# # UPDATE ON THIS: nvm, it somehow works now...
# write_verilog -noattr -noexpr -nohex -nodec -defparam "/scratch/perf_area_eff/experiment_7ca0dda7/syn_obj/syn-rundir/FDivSqrtUnit.mapped.v"

# BLIF file seems to be easier to parse than mapped verilog for find_regs functions so leave for now
# write_blif -top FDivSqrtUnit "/scratch/perf_area_eff/experiment_7ca0dda7/syn_obj/syn-rundir/FDivSqrtUnit.mapped.blif"
exit