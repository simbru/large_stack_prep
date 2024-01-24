

#import necessary libraries 
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import pathlib
import processing_pypeline.readScanM as rsm
#import napari
import igorwriter
#from igor import binarywave

from scanmsupport.scanm.scanm_smp import SMP, SMH
from ParamsNum_to_dict import ParamsNum_PythontoIGOR_dict, ParamsNum_IGORtoPython_dict

def pull_labels_and_clean(path):
    """
    Pulls labels from pre-existing text file (much easier to keep track of indeces)
    """
    # Get label list
    labels = np.loadtxt(path, dtype=str)
    # Replace 'nan' strings with empty strings
    labels = np.where(labels == "nan", "", labels).tolist()
    return labels

def load_Igor(path):
    # Initiate object
    scmf = SMP()
    # Load header
    scmf.loadSMH(path, verbose=False)
    # Load data
    scmf.loadSMP()
    return scmf

def build_wParams(initialised_SMP_object):
    # Build wParamsNum and wParamsStr
    keys = initialised_SMP_object._kvPairDict.keys() 
    AllParams = [(i, initialised_SMP_object._kvPairDict[i]) for i in initialised_SMP_object._kvPairDict]
    AllParams_arr = np.array(AllParams, dtype = object)
    # Get all info for wParamsStr and compile two lits (list lables and list values)
    guid = initialised_SMP_object.GUID # no clue what this is but is included in wParamsStr
    wParamsStr_labels = ["ComputerName", "UserName", "OriginalPixelDataFileName", "DateStamp", 
    "TimeStamp", "ScanMproductVersionAndTargetOS", "CallingProcessPath", "CallingProcessVersion",
    "StimBufLenList", "TargetedStimDurList", "TargetedStimDurList", "InChan_PixBufLenList", 
    "ScanPathFunc", "IgorGUIVer", "Comment", "Objective", "RealStimDurList"]
    wParamsStr_vals = [str(f'"{initialised_SMP_object._kvPairDict[i][2]}"') for i in wParamsStr_labels]
    # Go through and clean up all indeces so they match current IGOR implementation (not so many so just setting this manually)
    wParamsStr_vals[0]  = wParamsStr_vals[0].upper()
    wParamsStr_vals[1]  = wParamsStr_vals[1].upper()
    wParamsStr_vals[9]  = wParamsStr_vals[9].replace("[", "").replace("]", "").replace(" ", ";").replace(".", "")
    wParamsStr_vals[10] = wParamsStr_vals[10].replace("[", "").replace("]", "").replace(" ", ";").replace(".", "")
    wParamsStr_vals[11] = wParamsStr_vals[11].replace("[", "").replace("]", "").replace(" ", ";").replace(".", "")
    wParamsStr_vals[12] = wParamsStr_vals[12].replace("[", "").replace("]", "").replace(" ", "").replace(",", "").replace("'", "|").replace("||", "|")
    wParamsStr_vals[16] = wParamsStr_vals[16].replace("[", "").replace("]", "").replace(" ", ";").replace(".", "")
    wParamsStr_labels.insert(0, "GUID") # insert this for label
    wParamsStr_vals.insert(0, f'"{guid}"'.upper())
    wParamsStr_vals = np.array(wParamsStr_vals, dtype = object)
    # Do similar for wParamsStr (all this info comes from ScM_FileIO.ipf in Igor installation)
    wParamsNum_labels = list(ParamsNum_IGORtoPython_dict.values())
    wParamsNumlabels_IGOR = pull_labels_and_clean(r".\NumParams_label_list.txt")
    wParamsNumlabels_labels_Python = [ParamsNum_IGORtoPython_dict[i] for i in wParamsNumlabels_IGOR]
    wParamsNum_vals = np.zeros([60])
    wParamsNum_val_lable_tuples = [(i, initialised_SMP_object._kvPairDict[i][2]) if i in initialised_SMP_object._kvPairDict else (i, 0) for i in wParamsNumlabels_labels_Python]
    for n, i in enumerate(wParamsNum_val_lable_tuples):
        wParamsNum_vals[n] = i[1]
    # # Now that needs to go to into .ibw files
    wParamsStr = igorwriter.IgorWave(wParamsStr_vals, name='wParamsStr')
    # wParamsNum = igorwriter.IgorWave(wParamsNum_vals, name='wParamsNum')
    wParamsNum = igorwriter.IgorWave(wParamsNum_vals, name='wParamsNum')
    wParamsNum.set_dimensionlablels(wParamsNumlabels_IGOR)
    return wParamsStr, wParamsNum
    # return wParamsStr_vals, wParamsNum_vals




def output_ch2crop(scanm_file_object, input_path):
    # Create nice paths for save directory
    input_path = pathlib.Path(input_path)
    save_path_parent = pathlib.Path(input_path).parent
    filename = input_path.stem
    save_path = save_path_parent.joinpath(filename)
    # Create storage folder
    save_path.mkdir(exist_ok = True)
    # Create .ibw tables that need to be moved with imaging files
    wParamsStr, wParamsNum = build_wParams(scanm_file_object) # note that these are IGOR waves
    wParamsNum.save_itx("label_test.itx")
    # Get imaging data
    channel0 = scanm_file_object.getData(ch=0, crop=True)
    channel2 = scanm_file_object.getData(ch=2, crop=True)
    # Crop trigger channel 
    channel2 = np.copy(channel2[:, :, :2])
    # Convert to Igor waves
    wDataCh0 = igorwriter.IgorWave(channel0.swapaxes(0, 2), name = "wDataCh0")
    wDataCh2 = igorwriter.IgorWave(channel2.swapaxes(0, 2), name = "wDataCh2")
    # Save as .ibw
    save_list = [wParamsStr, wParamsNum, wDataCh0, wDataCh2]
    folder_name = "test"
    for i in save_list:
        current_name = i.name
        print("Writing", current_name)
        if current_name == "wParamsStr" or current_name == "wParamsNum":
            i.save_itx(save_path.joinpath(current_name).with_suffix(".itx"))
        else:
            i.save(save_path.joinpath(current_name).with_suffix(".ibw"))
    print("Done. Saved outputs to", save_path)

def filesize_reducer(input_path):
    scanmfile = load_Igor(input_path)
    output_ch2crop(scanmfile, input_path)