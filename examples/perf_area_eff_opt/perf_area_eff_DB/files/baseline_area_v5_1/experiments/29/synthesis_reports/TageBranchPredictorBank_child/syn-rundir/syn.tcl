yosys -import
setundef -zero
read_verilog -sv /scratch/perf_area_eff/experiment_24790b5e/syn_obj/input_src/ComposedBranchPredictorBank.sv
read_verilog -sv /scratch/perf_area_eff/experiment_24790b5e/syn_obj/input_src/MaxPeriodFibonacciLFSR_3.sv
read_verilog -sv /scratch/perf_area_eff/experiment_24790b5e/syn_obj/input_src/RenameMapTable.sv
read_verilog -sv /scratch/perf_area_eff/experiment_24790b5e/syn_obj/input_src/RenameMapTable_1.sv
read_verilog -sv /scratch/perf_area_eff/experiment_24790b5e/syn_obj/input_src/TageBranchPredictorBank.sv
read_verilog -sv /scratch/perf_area_eff/experiment_24790b5e/syn_obj/input_src/TageTable.sv
read_verilog -sv /scratch/perf_area_eff/experiment_24790b5e/syn_obj/input_src/TageTable_1.sv
read_verilog -sv /scratch/perf_area_eff/experiment_24790b5e/syn_obj/input_src/TageTable_2.sv
read_verilog -sv /scratch/perf_area_eff/experiment_24790b5e/syn_obj/input_src/TageTable_3.sv
read_verilog -sv /scratch/perf_area_eff/experiment_24790b5e/syn_obj/input_src/TageTable_4.sv
read_verilog -sv /scratch/perf_area_eff/experiment_24790b5e/syn_obj/input_src/TageTable_5.sv
read_verilog -sv /scratch/perf_area_eff/experiment_24790b5e/syn_obj/input_src/cacti_table_0_ext.v
read_verilog -sv /scratch/perf_area_eff/experiment_24790b5e/syn_obj/input_src/cacti_table_1_ext.v
read_verilog -sv /scratch/perf_area_eff/experiment_24790b5e/syn_obj/input_src/cacti_table_ext.v
read_verilog -sv /scratch/perf_area_eff/experiment_24790b5e/syn_obj/input_src/cacti_tage_us_0_ext.v
read_verilog -sv /scratch/perf_area_eff/experiment_24790b5e/syn_obj/input_src/cacti_tage_us_ext.v
read_verilog -sv /scratch/perf_area_eff/experiment_24790b5e/syn_obj/input_src/chipyard.harness.TestHarness.MediumBoomV3Config.top.mems.v
read_verilog -sv /scratch/perf_area_eff/experiment_24790b5e/syn_obj/input_src/extern_modules.sv
read_verilog -sv /scratch/perf_area_eff/experiment_24790b5e/syn_obj/input_src/meta_0.sv
read_verilog -sv /scratch/perf_area_eff/experiment_24790b5e/syn_obj/input_src/meta_1.sv
read_verilog -sv /scratch/perf_area_eff/experiment_24790b5e/syn_obj/input_src/table_0.sv
read_verilog -sv /scratch/perf_area_eff/experiment_24790b5e/syn_obj/input_src/table_0_0.sv
read_verilog -sv /scratch/perf_area_eff/experiment_24790b5e/syn_obj/input_src/table_1.sv
read_verilog -sv /scratch/perf_area_eff/experiment_24790b5e/syn_obj/input_src/table_2.sv
read_verilog -sv /scratch/perf_area_eff/experiment_24790b5e/syn_obj/input_src/table_3.sv
read_verilog -sv /scratch/perf_area_eff/experiment_24790b5e/syn_obj/input_src/table_4.sv
read_verilog -sv /scratch/perf_area_eff/experiment_24790b5e/syn_obj/input_src/tage_us.sv
read_verilog -sv /scratch/perf_area_eff/experiment_24790b5e/syn_obj/input_src/tage_us_0.sv
read_verilog -sv /scratch/perf_area_eff/experiment_24790b5e/syn_obj/input_src/tage_us_1.sv
read_verilog -sv /scratch/perf_area_eff/experiment_24790b5e/syn_obj/input_src/tage_us_2.sv
read_verilog -sv /scratch/perf_area_eff/experiment_24790b5e/syn_obj/input_src/tage_us_3.sv
read_verilog -sv /scratch/perf_area_eff/experiment_24790b5e/syn_obj/input_src/tage_us_4.sv
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
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/cc_dir_ext_ff_n40C_1v95.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/cc_dir_ext_ss_100C_1v60.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/cc_dir_ext_tt_025C_1v80.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/cc_banks_0_ext_ff_n40C_1v95.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/cc_banks_0_ext_ss_100C_1v60.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/cc_banks_0_ext_tt_025C_1v80.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/tag_array_ext_ff_n40C_1v95.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/tag_array_ext_ss_100C_1v60.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/tag_array_ext_tt_025C_1v80.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/array_0_0_0_ext_ff_n40C_1v95.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/array_0_0_0_ext_ss_100C_1v60.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/array_0_0_0_ext_tt_025C_1v80.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/tag_array_0_ext_ff_n40C_1v95.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/tag_array_0_ext_ss_100C_1v60.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/tag_array_0_ext_tt_025C_1v80.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/dataArrayWay_0_ext_ff_n40C_1v95.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/dataArrayWay_0_ext_ss_100C_1v60.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/dataArrayWay_0_ext_tt_025C_1v80.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/tage_us_ext_ff_n40C_1v95.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/tage_us_ext_ss_100C_1v60.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/tage_us_ext_tt_025C_1v80.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/table_ext_ff_n40C_1v95.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/table_ext_ss_100C_1v60.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/table_ext_tt_025C_1v80.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/tage_us_0_ext_ff_n40C_1v95.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/tage_us_0_ext_ss_100C_1v60.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/tage_us_0_ext_tt_025C_1v80.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/table_0_ext_ff_n40C_1v95.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/table_0_ext_ss_100C_1v60.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/table_0_ext_tt_025C_1v80.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/table_1_ext_ff_n40C_1v95.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/table_1_ext_ss_100C_1v60.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/table_1_ext_tt_025C_1v80.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/btb_0_ext_ff_n40C_1v95.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/btb_0_ext_ss_100C_1v60.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/btb_0_ext_tt_025C_1v80.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/ebtb_ext_ff_n40C_1v95.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/ebtb_ext_ss_100C_1v60.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/ebtb_ext_tt_025C_1v80.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/data_ext_ff_n40C_1v95.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/data_ext_ss_100C_1v60.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/data_ext_tt_025C_1v80.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/meta_0_ext_ff_n40C_1v95.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/meta_0_ext_ss_100C_1v60.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/meta_0_ext_tt_025C_1v80.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/ghist_0_ext_ff_n40C_1v95.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/ghist_0_ext_ss_100C_1v60.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/ghist_0_ext_tt_025C_1v80.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/rob_debug_inst_mem_ext_ff_n40C_1v95.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/rob_debug_inst_mem_ext_ss_100C_1v60.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/rob_debug_inst_mem_ext_tt_025C_1v80.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/l2_tlb_ram_0_ext_ff_n40C_1v95.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/l2_tlb_ram_0_ext_ss_100C_1v60.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/l2_tlb_ram_0_ext_tt_025C_1v80.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/mem_ext_ff_n40C_1v95.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/mem_ext_ss_100C_1v60.lib
read_liberty -lib /tmp/hammer_sky130_open_oepvdjei/cacti_libs/mem_ext_tt_025C_1v80.lib
puts "(hammer) yosys proc"
yosys proc
puts "(hammer) hierarchy -check -top TageBranchPredictorBank"
hierarchy -check -top TageBranchPredictorBank

puts "(hammer) synth -top TageBranchPredictorBank"
synth -top TageBranchPredictorBank

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
    -constr "/scratch/perf_area_eff/experiment_24790b5e/syn_obj/syn-rundir/TageBranchPredictorBank.mapped.sdc" \
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
puts "(hammer) tee -o /scratch/perf_area_eff/experiment_24790b5e/syn_obj/syn-rundir/TageBranchPredictorBank.synth_check.rpt check"
tee -o /scratch/perf_area_eff/experiment_24790b5e/syn_obj/syn-rundir/TageBranchPredictorBank.synth_check.rpt check

puts "(hammer) tee -o /scratch/perf_area_eff/experiment_24790b5e/syn_obj/syn-rundir/TageBranchPredictorBank.synth_stat.txt stat -top TageBranchPredictorBank -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__gpiov2_pad_tt_tt_025C_1v80_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__gpiov2_pad_wrapped_tt_tt_025C_1v80_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vccd_lvc_clamped3_pad_tt_025C_1v80_3v30_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vccd_lvc_clamped_pad_tt_025C_1v80_3v30_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vdda_hvc_clamped_pad_tt_025C_1v80_3v30_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vddio_hvc_clamped_pad_tt_025C_1v80_3v30_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vssa_hvc_clamped_pad_tt_025C_1v80_3v30_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vssd_lvc_clamped3_pad_tt_025C_1v80_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vssd_lvc_clamped_pad_tt_025C_1v80_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vssio_hvc_clamped_pad_tt_025C_1v80_3v30_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_gpiov2_tt_tt_025C_1v80_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_ground_hvc_wpad_tt_025C_1v80_3v30_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_ground_lvc_wpad_tt_025C_1v80_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_power_hvc_wpad_tt_025C_1v80_3v30_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_power_lvc_wpad_tt_025C_1v80_3v30_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_xres4v2_tt_tt_025C_1v80_3v30.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/cc_dir_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/cc_banks_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/tag_array_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/array_0_0_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/tag_array_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/dataArrayWay_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/tage_us_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/table_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/tage_us_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/table_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/table_1_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/btb_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/ebtb_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/data_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/meta_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/ghist_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/rob_debug_inst_mem_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/l2_tlb_ram_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/mem_ext_tt_025C_1v80.lib"
tee -o /scratch/perf_area_eff/experiment_24790b5e/syn_obj/syn-rundir/TageBranchPredictorBank.synth_stat.txt stat -top TageBranchPredictorBank -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__gpiov2_pad_tt_tt_025C_1v80_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__gpiov2_pad_wrapped_tt_tt_025C_1v80_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vccd_lvc_clamped3_pad_tt_025C_1v80_3v30_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vccd_lvc_clamped_pad_tt_025C_1v80_3v30_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vdda_hvc_clamped_pad_tt_025C_1v80_3v30_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vddio_hvc_clamped_pad_tt_025C_1v80_3v30_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vssa_hvc_clamped_pad_tt_025C_1v80_3v30_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vssd_lvc_clamped3_pad_tt_025C_1v80_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vssd_lvc_clamped_pad_tt_025C_1v80_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_ef_io__vssio_hvc_clamped_pad_tt_025C_1v80_3v30_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_gpiov2_tt_tt_025C_1v80_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_ground_hvc_wpad_tt_025C_1v80_3v30_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_ground_lvc_wpad_tt_025C_1v80_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_power_hvc_wpad_tt_025C_1v80_3v30_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_power_lvc_wpad_tt_025C_1v80_3v30_3v30.lib -liberty /home/ray/conda-sky130/share/pdk/sky130A/libs.ref/sky130_fd_io/lib/sky130_fd_io__top_xres4v2_tt_tt_025C_1v80_3v30.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/cc_dir_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/cc_banks_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/tag_array_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/array_0_0_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/tag_array_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/dataArrayWay_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/tage_us_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/table_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/tage_us_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/table_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/table_1_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/btb_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/ebtb_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/data_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/meta_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/ghist_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/rob_debug_inst_mem_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/l2_tlb_ram_0_ext_tt_025C_1v80.lib -liberty /tmp/hammer_sky130_open_oepvdjei/cacti_libs/mem_ext_tt_025C_1v80.lib
puts "(hammer) write_verilog -noattr -noexpr -nohex -nodec -defparam \"/scratch/perf_area_eff/experiment_24790b5e/syn_obj/syn-rundir/TageBranchPredictorBank.mapped.v\""
write_verilog -noattr -noexpr -nohex -nodec -defparam "/scratch/perf_area_eff/experiment_24790b5e/syn_obj/syn-rundir/TageBranchPredictorBank.mapped.v"

# flatten

# # OpenROAD will throw an error if the verilog from Yosys is not flattened
# # UPDATE ON THIS: nvm, it somehow works now...
# write_verilog -noattr -noexpr -nohex -nodec -defparam "/scratch/perf_area_eff/experiment_24790b5e/syn_obj/syn-rundir/TageBranchPredictorBank.mapped.v"

# BLIF file seems to be easier to parse than mapped verilog for find_regs functions so leave for now
# write_blif -top TageBranchPredictorBank "/scratch/perf_area_eff/experiment_24790b5e/syn_obj/syn-rundir/TageBranchPredictorBank.mapped.blif"
exit