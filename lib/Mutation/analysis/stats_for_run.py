
# Library to compute the stats after run.py

from __future__ import print_function
import os
import sys
import shutil
import json
import argparse
import shutil
import scipy.stats
import numpy as np

import pandas as pd

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.insert(0, os.path.expanduser("~/mytools/MFI-V2.0/Analysis"))
import plotMerge

###### Non Parametic Vargha Delaney A12 ######
# Taken from -- https://gist.github.com/timm/5630491

def a12(lst1,lst2,pairwise=False, rev=True):
    "how often is x in lst1 more than y in lst2?"
    more = same = 0.0
    for i,x in enumerate(lst1):
        second = [lst2[i]] if pairwise else lst2
        for y in second:
            if   x==y : same += 1
            elif rev     and x > y : more += 1
            elif not rev and x < y : more += 1
    return (more + 0.5*same) / (len(lst1) if pairwise else len(lst1)*len(lst2))

def wilcoxon(list1, list2, isranksum=True):
    if isranksum:
        p_value = scipy.stats.ranksums(list1, list2)
    else:
        p_value = scipy.stats.wilcoxon(list1, list2)
    return p_value
#~ def wilcoxon()
#############################################
def compute_auc(in_x_list, in_y_list):
    """ SUM(abs(x2-x1) * abs(y2-y1) / 2 + (x2 - x1) * min(y1, y2))
    """
    # make sure both inlist are sorted by x
    assert len(set(in_x_list)) == len(in_x_list), "duplicate in in_x_list"
    assert len(in_x_list) == len(in_y_list), "X and Y have diffrent lengths"
    assert len(in_x_list) > 1, "At leats 2 elements required"
    x_list = []
    y_list = []
    for v_x, v_y in sorted(zip(in_x_list, in_y_list), key=lambda p: p[0]):
        x_list.append(v_x)
        y_list.append(v_y)
        assert v_y >= 0, "Only supports positive or null Y coordinate values"

    auc = 0.0
    prev_x = None
    prev_y = None
    for p_ind, (x_val, y_val) in enumerate(zip(x_list, y_list)):
        if prev_x is not None:
            auc += (x_val - prev_x) * \
                                (min(y_val, prev_y) + abs(y_val - prev_y)/2.0)
        prev_x = x_val
        prev_y = y_val
    return auc
#~ def compute_auc()
  
def compute_apfd(in_x_list, in_y_list):
    auc = compute_auc(in_x_list, in_y_list)
    apfd = auc / abs(max(in_x_list) - min(in_x_list))
    return apfd
#~ def compute_apfd()
########################


def make_twoside_plot(left_y_vals, right_y_vals, img_out_file, \
                                        x_label="X", y_left_label="Y_LEFT", \
                                                    y_right_label="Y_RIGHT"):

    fig, ax1 = plt.subplots()

    color = 'tab:red'
    ax1.set_xlabel(x_label)

    ax1.set_ylabel(y_left_label, color=color)
    ax1.boxplot(left_y_vals, color=color)
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'tab:blue'
    ax2.set_ylabel(y_right_label, color=color)  # we already handled the x-label with ax1
    ax2.boxplot(right_y_vals, color=color)
    ax2.tick_params(axis='y', labelcolor=color)

    plt.xticks([])

    plt.tight_layout()
    plt.savefig(img_out_file+".pdf", format="pdf")
    plt.close('all')
#~ def make_twoside_plot()


csv_file="Results.csv"
funcs_csv_file="Results-byfunctions.csv"
initial_json="Initial-dat.json"

def getProjRelDir():
    Modes = ["DEV", "KLEE", "NUM", "PASS"]
    curMode = "PASS"
    testSamplePercent = "100.0"
    eachIndirPrefix = 'TestGenFinalAggregated'

    assert curMode in Modes, "curMode not in Modes: "+curMode
    eachIndir = eachIndirPrefix + curMode + '_' + testSamplePercent

    projreldir = os.path.join('OUTPUT', eachIndir)

    return projreldir
#~deg getProjRelDir()

PROJECT_ID_COL = "projectID"
SpecialTechs = {'_pureklee_': 'klee', '50_50_0_0_rnd_5_on_nocrit':'concrete'}
def libMain(outdir, proj2dir, use_func=False, customMaxtime=None, \
                                                        projcommonreldir=None):
    merged_df = None
    all_initial = {}
    if projcommonreldir is None:
        projcommonreldir = getProjRelDir()

    input_csv = funcs_csv_file if use_func else csv_file

    # Load data
    for proj in proj2dir:
        fulldir = os.path.join(proj2dir[proj], projcommonreldir)
        full_csv_file = os.path.join(fulldir, input_csv)
        full_initial_json = os.path.join(fulldir, initial_json)

        tmp_df = pd.read_csv(full_csv_file, index_col=False)
        assert PROJECT_ID_COL not in tmp_df, PROJECT_ID_COL+" is in df"
        if use_func:
            funcNameCol = "FunctionName"
            assert funcNameCol in tmp_df, \
                                        "invalid func csv file: "+full_csv_file
            tmp_df[PROJECT_ID_COL] = list(\
                    map(lambda x: os.path.join(proj, x), tmp_df[funcNameCol]))
        else:
            tmp_df[PROJECT_ID_COL] = [proj] * len(tmp_df.index)

        if merged_df is None:
            merged_df = tmp_df
        else:
            assert set(merged_df) == set(tmp_df), "Mismatch column for "+proj 
            merged_df = merged_df.append(tmp_df, ignore_index=True)

        with open(full_initial_json) as fp:
            all_initial[proj] = json.load(fp)

    # Compute the merged json
    merged_json_obj = {}
    merged_json_obj["Initial#Mutants"] = \
            sum([int(all_initial[v]["Initial#Mutants"]) for v in all_initial])
    merged_json_obj["Initial#KilledMutants"] = \
            sum([int(all_initial[v]["Initial#KilledMutants"]) \
                                                        for v in all_initial])
    merged_json_obj["Inintial#Tests"] = \
            sum([int(all_initial[v]["Inintial#Tests"]) for v in all_initial])
    merged_json_obj["Initial-MS"] = \
            sum([float(all_initial[v]["Initial-MS"]) \
                                    for v in all_initial]) / len(all_initial)
    merged_json_obj["TestSampleMode"] = \
                        all_initial[all_initial.keys()[0]]["TestSampleMode"]
    merged_json_obj["MaxTestGen-Time(min)"] = \
                    all_initial[all_initial.keys()[0]]["MaxTestGen-Time(min)"]
    if use_func:
        merged_json_obj['By-Functions'] = {}
        for proj in all_initial:
            for func in all_initial[proj]:
                func_name_merged = os.path.join(proj, func)
                merged_json_obj['By-Functions'][func_name_merged] = \
                                                        all_initial[proj][func]

    # save merged json
    with open(os.path.join(outdir, initial_json), 'w') as fp:
        json.dump(merged_json_obj, fp)
    
    # COMPUTATIONS ON DF
    timeCol = "TimeSnapshot(min)"
    config_columns = ["_precondLength","_mutantMaxFork", 
                        "_genTestForDircardedFrom", "_postCheckContProba", 
                        "_mutantContStrategy", "_maxTestsGenPerMut", 
                        "_disableStateDiffInTestgen"
                    ]
    other_cols = ["_testGenOnlyCriticalDiffs" ]

    msCol = "MS-INC"
    targetCol = "#Targeted"
    numMutsCol = "#Mutants"
    techConfCol = "Tech-Config"
    stateCompTimeCol = "StateComparisonTime(s)"
    numGenTestsCol = "#GenTests"
    numForkedMutStatesCol = "#MutStatesForkedFromOriginal"
    mutPointNoDifCol = "#MutStatesEqWithOrigAtMutPoint"

    if customMaxtime is not None:
        # filter anything higher than maxtime (minutes)
        assert customMaxtime > 0, "maxtime must be greater than 0"
        merged_df = merged_df[merged_df[timeCol] <= customMaxtime]
        if len(merged_df) == 0:
            print("# The customMaxtime specified is too low. Terminating ...")
            exit(1)

    tech_confs = set(merged_df[techConfCol])
    projects = set(merged_df[PROJECT_ID_COL])
    ms_apfds = {p: {t_c: None for t_c in tech_confs} for p in projects}
    for p in ms_apfds:
        p_tmp_df = merged_df[merged_df[PROJECT_ID_COL] == p]
        for t_c in ms_apfds[p]:
            # get the data
            tmp_df = p_tmp_df[p_tmp_df[techConfCol] == t_c]
            ms_apfds[p][t_c] = compute_apfd(tmp_df[timeCol], tmp_df[msCol])
        tmp_df = p_tmp_df = None
    
    only_semu_cfg_df = merged_df[~merged_df[techConfCol].isin(SpecialTechs)]

    vals_by_conf = {}
    for c in config_columns:
        vals_by_conf[c] = list(set(only_semu_cfg_df[c]))

    techConfbyvalbyconf = {}
    for pc in config_columns:
        techConfbyvalbyconf[pc] = {}
        # process param config (get apfds)
        for val in vals_by_conf[pc]:
            keys = \
                set(only_semu_cfg_df[only_semu_cfg_df[pc] == val][techConfCol])
            techConfbyvalbyconf[pc][val] = keys

    def getListAPFDSForTechConf (t_c):
        v_list = []
        for p in ms_apfds:
            assert t_c in ms_apfds[p]
            v_list.append(ms_apfds[p][t_c])
        return v_list

    colors_bw = ['white', 'whitesmoke', 'lightgray', 'silver', 'darkgrey', \
                                                    'gray', 'dimgrey', "black"]
    colors = ["green", 'blue', 'red', "black", "maroon", "magenta", "cyan"]
    linestyles = ['solid', 'solid', 'dashed', 'dashed', 'dashdot', 'dotted', \
                                                                    'solid']
    linewidths = [1.75, 1.75, 2.5, 2.5, 3.25, 3.75, 2]

    # XXX process APFDs (max, min, med)
    #proj_agg_func = np.median
    proj_agg_func = np.average
    for pc in techConfbyvalbyconf:
        min_vals = {}
        max_vals = {}
        med_vals = {}
        for val in techConfbyvalbyconf[pc]:
            sorted_by_apfd_tmp = sorted(techConfbyvalbyconf[pc][val], \
                    key=lambda x: proj_agg_func(getListAPFDSForTechConf(x)))
            min_vals[val] = sorted_by_apfd_tmp[0]
            max_vals[val] = sorted_by_apfd_tmp[-1]
            med_vals[val] = sorted_by_apfd_tmp[len(sorted_by_apfd_tmp)/2]
        # plot
        plot_out_file = os.path.join(outdir, "perconf_apfd_"+pc)
        data = {val: {"min": getListAPFDSForTechConf(min_vals[val]), \
                        "med": getListAPFDSForTechConf(med_vals[val]), \
                        "max": getListAPFDSForTechConf(max_vals[val])} \
                                            for val in techConfbyvalbyconf[pc]}
        for sp in SpecialTechs:
            data[SpecialTechs[sp]] = {em:getListAPFDSForTechConf(sp) \
                                                for em in ['min', 'med','max']}
        tmp_all_vals = []
        for g in data:
            for m in data[g]:
                tmp_all_vals += data[g][m]
        min_y = min(tmp_all_vals)
        max_y = max(tmp_all_vals)
        assert min_y >= 0 and min_y <= 100, "invalid min_y: "+str(min_y)
        assert max_y >= 0 and max_y <= 100, "invalid max_y: "+str(max_y)
        # Actual plot with data 
        # TODO arange max_y, min_y and step_y
        if max_y - min_y >= 10:
            max_y = int(max_y) + 2 
            min_y = int(min_y) - 1 
            step_y = (max_y - min_y) / 10
        else:
            step_y = 1
            rem_tmp = 10 - max_y - min_y + 1
            if 100 - max_y < rem_tmp/2:
                min_y = int(min_y - (rem_tmp - (100 - max_y)))
                max_y = 100
            elif min_y < rem_tmp/2:
                max_y = int(max_y + (rem_tmp - min_y)) 
                min_y = 0
            else:
                max_y = int(max_y + rem_tmp/2)
                min_y = int(min_y - rem_tmp/2)
        yticks_range = range(min_y, max_y+1, step_y)
        plotMerge.plot_Box_Grouped(data, plot_out_file, colors_bw, \
                                "AVERAGE MS", yticks_range=yticks_range, \
                                    selectData=['min', 'med', 'max'])
    
    # XXX Find best and worse confs
    apfd_ordered_techconf_list = sorted(list(set(merged_df[techConfCol])), \
                    reverse=True, \
                    key=lambda x: proj_agg_func(getListAPFDSForTechConf(x)))
    best_val_tmp = proj_agg_func(getListAPFDSForTechConf(\
                                            apfd_ordered_techconf_list[0]))
    worse_val_tmp = proj_agg_func(getListAPFDSForTechConf(\
                                            apfd_ordered_techconf_list[-1]))
    best_elems = []
    worse_elems = []
    for i, v in enumerate(apfd_ordered_techconf_list):
        if proj_agg_func(getListAPFDSForTechConf(v)) >= best_val_tmp:
            best_elems.append(v)
        if proj_agg_func(getListAPFDSForTechConf(v)) <= worse_val_tmp:
            worse_elems.append(v)
    # get corresponding param values and save as csv (best and worse)
    best_df_obj = []
    worse_df_obj = []
    for elem_list, df_obj_list in [(best_elems, best_df_obj), \
                                                (worse_elems, worse_df_obj)]:
        for v in elem_list:
            row = {}
            for pc in techConfbyvalbyconf:
                for val in techConfbyvalbyconf[pc]:
                    if v in techConfbyvalbyconf[pc][val]:
                        assert pc not in row, "BUG"
                        row[pc] = val
            row[techConfCol] = v
            row['MS_INC_APFD'] = proj_agg_func(getListAPFDSForTechConf(v))
            df_obj_list.append(row)
    best_df = pd.DataFrame(best_df_obj)
    worse_df = pd.DataFrame(worse_df_obj)
    best_df_file = os.path.join(outdir, "best_tech_conf_apfd.csv")
    worse_df_file = os.path.join(outdir, "worse_tech_conf_apfd.csv")
    best_df.to_csv(best_df_file, index=False)
    worse_df.to_csv(worse_df_file, index=False)

    # XXX compare MS with compareState time, %targeted, #testgen, WM%
    if customMaxtime is None:
        selectedTimes_minutes = [15, 30, 60, 120]
    else:
        selectedTimes_minutes = [customMaxtime]

    fixed_y = msCol
    changing_ys = [targetCol, stateCompTimeCol, numGenTestsCol, \
                                    numForkedMutStatesCol, mutPointNoDifCol]
    # get data and plot
    for time_snap in selectedTimes_minutes:
        time_snap_df = \
                    only_semu_cfg_df[only_semu_cfg_df[timeCol] == time_snap]
        tmp_tech_confs = set(time_snap_df[techConfCol])
        metric2techconf2values = {}
        # for each metric, get per techConf list on values
        # techConfCol
        for tech_conf in tmp_tech_confs:
            t_c_tmp_df = time_snap_df[time_snap_df[techConfCol] == tech_conf]
            for metric_col in [fixed_y] + changing_ys:
                if metric_col not in metric2techconf2values:
                    metric2techconf2values[metric_col] = {}
                metric2techconf2values[metric_col][tech_conf] = \
                                                        t_c_tmp_df[metric_col]
        
        sorted_techconf_by_ms = metric2techconf2values[fixed_y].keys()
        sorted_techconf_by_ms.sort(reverse=True, \
                                    key=lambda x: (np.median(x), np.average(x)))
        # Make plots of ms and the others
        for chang_y in changing_ys:
            plot_img_out_file = os.path.join(outdir, "otherVSms-"+ \
                                str(time_snap) + "-"+chang_y.replace('#','n'))
            fix_vals = []
            chang_vals = []
            for tech_conf in sorted_techconf_by_ms:
                fix_vals.append(metric2techconf2values[fixed_y][tech_conf])
                chang_vals.append(metric2techconf2values[chang_y][tech_conf])
            make_twoside_plot(fix_vals, chang_vals, plot_img_out_file, \
                            x_label="Configuations", y_left_label=fixed_y, \
                                                        y_right_label=chang_y)
            
#~ def libMain()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output", default=None, \
            help="Output directory, will be deleted and recreated if exists")
    parser.add_argument("-i", "--intopdir", default=None, \
            help="Top directory where to all projects are"\
                                        +" (will search the finished ones)")
    parser.add_argument("--usefunctions", action='store_true', \
                help="Enable using by function instead of just by project")
    parser.add_argument("--maxtimes", default=None, \
                help="space separated customMaxtime list to use (in minutes)")
    parser.add_argument("--onlyprojects", default=None, \
                help="space separated project list to use")
    args = parser.parse_args()

    outdir = args.output
    intopdir = args.intopdir
    assert outdir is not None
    assert intopdir is not None
    assert os.path.isdir(intopdir)

    maxtime_list = None
    if args.maxtimes is not None:
        maxtime_list = list(set(args.maxtimes.strip().split()))
    
    onlyprojects_list = None
    if args.onlyprojects is not None:
        onlyprojects_list = list(set(args.onlyprojects.strip().split()))

    if os.path.isdir(outdir):
        if raw_input("\nspecified output exists. Clear it? [y/n] ").lower() \
                                                                        == 'y':
            shutil.rmtree(outdir)
        else:
            print("# please specify another outdir")
            return
    os.mkdir(outdir)
    proj2dir = {}
    for f_d in os.listdir(intopdir):
        direct = os.path.join(intopdir, f_d, getProjRelDir())
        if os.path.isfile(os.path.join(direct, csv_file)) and \
                        os.path.isfile(os.path.join(direct, funcs_csv_file)):
            proj2dir[f_d] = os.path.join(intopdir, f_d)
    if onlyprojects_list is not None:
        for p in set(proj2dir) - set(onlyprojects_list):
            if p in proj2dir:
                del proj2dir[p]
    if len(proj2dir) > 0:
        print ("# Calling libMain on projects", list(proj2dir), "...")
        if maxtime_list is None:
            libMain(outdir, proj2dir, use_func=args.usefunctions)
        else:
            for maxtime in maxtime_list:
                mt_outdir = os.path.join(outdir, "maxtime-"+maxtime)
                os.mkdir(mt_outdir)
                libMain(mt_outdir, proj2dir, use_func=args.usefunctions, \
                                                customMaxtime=float(maxtime))

        print("# DONE")
    else:
        print("# !! No good project found")

if __name__ == '__main__':
    main()