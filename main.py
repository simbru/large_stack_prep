

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
    Pulls labels from a pre-existing text file and cleans the data.

    Parameters
    ----------
    path : str
        The path to the text file containing labels.

    Returns
    -------
    list of str
        A list of labels extracted from the specified text file. 'nan' strings
        are replaced with empty strings in the result.

    Notes
    -----
    This function reads the labels from the given text file using NumPy's
    `loadtxt` function and then cleans the data by replacing 'nan' strings
    with empty strings.

    Examples
    --------
    >>> labels_path = "path/to/labels.txt"
    >>> cleaned_labels = pull_labels_and_clean(labels_path)
    >>> print(cleaned_labels)
    ['label1', 'label2', '', 'label4', ...]
    """
    # Get label list
    labels = np.loadtxt(path, dtype=str)
    # Replace 'nan' strings with empty strings
    labels = np.where(labels == "nan", "", labels).tolist()
    return labels

def load_Igor(path):
    """
    Load data from an Igor Pro file using the SMP class.

    Parameters
    ----------
    path : str
        The file path to the Igor Pro file.

    Returns
    -------
    SMP
        An SMP object containing loaded data.

    Notes
    -----
    This function initializes an SMP object,
    loads the header using the `loadSMH` method, and then loads the data using
    the `loadSMP` method.

    Parameters
    ----------
    path : str
        The file path to the Igor Pro file.

    Returns
    -------
    SMP
        An SMP object containing loaded data.

    Examples
    --------
    >>> igor_file_path = "path/to/igor_file.ibw"
    >>> loaded_smp_object = load_Igor(igor_file_path)
    >>> print(loaded_smp_object)
    <SMP object at 0x...>
    """
    # Initiate object
    scmf = SMP()
    # Load header
    scmf.loadSMH(path, verbose=False)
    # Load data
    scmf.loadSMP()
    return scmf

def build_wParams(initialised_SMP_object):
    """
    Build wParamsStr and wParamsNum Igor Waves from an initialised SMP object.

    Parameters
    ----------
    initialised_SMP_object : SMP
        An SMP (Scanning Microscopy Particle) object that has been initialized and
        contains key-value pair information.

    Returns
    -------
    wParamsStr : IgorWave
        An Igor Wave containing string values for specified parameters.

    wParamsNum : IgorWave
        An Igor Wave containing numeric values for specified parameters.

    Notes
    -----
    This function builds two Igor Waves, `wParamsStr` and `wParamsNum`, from the
    key-value pair information stored in the initialised SMP object. The Waves are
    constructed based on specific labels and values extracted from the SMP object.

    Parameters
    ----------
    initialised_SMP_object : SMP
        An SMP object that has been initialized and contains key-value pair information.

    Returns
    -------
    wParamsStr : IgorWave
        An Igor Wave containing string values for specified parameters.

    wParamsNum : IgorWave
        An Igor Wave containing numeric values for specified parameters.
    """
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
    """
    Process and save cropped Channel 2 data along with relevant Igor Waves.

    Parameters
    ----------
    scanm_file_object : SMP
        A ScanM File object containing imaging data.

    input_path : str
        The file path to the input ScanM file.

    Notes
    -----
    This function processes Channel 2 data from the given ScanM File object,
    crops the trigger channel, and saves the relevant information as Igor Waves
    (.ibw files and associated .itx tables).

    Parameters
    ----------
    scanm_file_object : SMP
        A ScanM File object containing imaging data.

    input_path : str
        The file path to the input ScanM file.

    Examples
    --------
    >>> scanm_file = initialise_SMP()  # Assuming a function to initialize SMP objects
    >>> input_file_path = "path/to/scanm_file.smp"
    >>> output_ch2crop(scanm_file, input_file_path)
    >>> # Check the output folder for saved Igor Waves and tables.
    """
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
    """
    Reduce the file size of an Igor Pro file by cropping Channel 2 data.

    Parameters
    ----------
    input_path : str
        The file path to the input Igor Pro file.

    Notes
    -----
    This function loads the Igor Pro file from the specified path, processes it by
    cropping Channel 2 data, and saves the relevant information, effectively reducing
    the file size.

    Parameters
    ----------
    input_path : str
        The file path to the input Igor Pro file.

    Examples
    --------
    >>> input_file_path = "path/to/igor_file.ibw"
    >>> filesize_reducer(input_file_path)
    >>> # Check the output folder for reduced file size Igor Waves and tables.
    """
    scanmfile = load_Igor(input_path)
    output_ch2crop(scanmfile, input_path)