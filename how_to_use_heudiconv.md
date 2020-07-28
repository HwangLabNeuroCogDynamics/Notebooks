

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

run fmriprep

    singularity run --cleanenv -B /data:/data /opt/fmriprep/fmriprep.simg \
    /data/backed_up/shared/MRRF_Seq_Test/BIDS_2020_3T /data/backed_up/shared/MRRF_Seq_Test/fmpaptest \
    participant --participant_label 20200212TEST --nthreads 16 --omp-nthreads 16 \
    -w /data/backed_up/shared/MRRF_Seq_Test/work2/
