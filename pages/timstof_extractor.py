import os
import shutil
from pathlib import Path
from uuid import uuid4
import streamlit as st

from timstof_utils import generate_ms2

st.title('TimsTof Raw File Extractor')

rand_uuid = str(uuid4())
ms2_file_name = rand_uuid + '.ms2'

tdf = st.file_uploader('tdf file', type='.tdf')
tdf_bin = st.file_uploader('tdf_bin file', type='.tdf_bin')
ms2_file_name = st.text_input('Ms2 File Name', ms2_file_name)

if st.button('Run'):

    d_folder = Path()
    os.mkdir(d_folder)

    tdf_path = d_folder / 'analysis.tdf'
    tdf_path.write_bytes(tdf.getvalue())

    tdf_bin_path = d_folder / 'analysis.tdf_bin'
    tdf_bin_path.write_bytes(tdf_bin.getvalue())

    ms2_file = generate_ms2(str(d_folder))

    shutil.rmtree(str(d_folder))

    st.download_button('Download Ms2', ms2_file, ms2_file_name)



