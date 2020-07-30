

Generate dicominfo.txt

    singularity run -B /data:/data/ /data/backed_up/shared/bin/heudiconv_0.8.0.sif \
    -d /data/backed_up/shared/ThalHi_MRI_2020/Raw/{subject}/SCANS/*/DICOM/*.dcm \
    -o /data/backed_up/shared/ThalHi_MRI_2020/BIDS \
    -f /data/backed_up/shared/bin/heudiconv/heuristics/convertall.py -s JH -c none --overwrite

Convert dicom to BIDS

    singularity run -B /data:/data/ /data/backed_up/shared/bin/heudiconv_0.8.0.sif \
    -d /data/backed_up/shared/ThalHi_MRI_2020/Raw/{subject}/SCANS/*/DICOM/*.dcm \
    -o /data/backed_up/shared/ThalHi_MRI_2020/BIDS \
    -b \
    -f /data/backed_up/shared/bin/heudiconv/heuristics/thalhi.py -s JH -c dcm2niix --overwrite



Edit json for field FieldMap
In order for fmriprep to recognize fieldmap data during preprocessing, an addition field must be inserted into each fieldmap's jason file.

    "IntendedFor": ["func/sub-20200130_task-MB3_run-001_bold.nii.gz", "func/sub-20200130_task-MB2_run-001_bold.nii.gz"],

In this field you would have to list all the functional runs you want to use this fmap data to correct for. 

Below is an example python script I found online to insert an additional data field into an exiting json file.
We can use write a function based on this to edit jason files associated with each fieldmap nifti.

    import json

    # first, get the absolute path to json file
    PATH_TO_JSON = 'data.json' #  assuming same directory (but you can work your magic here with os.)

    # read existing json to memory. you do this to preserve whatever existing data.

    with open(PATH_TO_JSON,'r') as jsonfile:
        json_content = json.load(jsonfile) # this is now in memory! you can use it outside 'open'


    # add the id key-value pair (rmbr that it already has the "name" key value)

    json_content["id"] = "134"

    with open(PATH_TO_JSON,'w') as jsonfile:
        json.dump(json_content, jsonfile, indent=4) # you decide the indentation level

Then run fmriprep with our usual setup. 
