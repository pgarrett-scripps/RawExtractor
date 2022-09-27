import os
import shutil
from pathlib import Path
from uuid import uuid4
import streamlit as st

from timstof_utils import generate_ms2

st.title('TimsTof Raw File Extractor')

with st.expander('Help'):
    st.subheader('Where to find tdf files?')
    st.markdown("""
    The analysis.tdf and analysis.tdf_bin are located inside of the .d folder
    
    Rename the ms2 file to whatever you like. Otherwise leave it blank to randomly generate a file name.
    """)

tdf = st.file_uploader(label='tdf file', type='.tdf')
tdf_bin = st.file_uploader(label='tdf_bin file', type='.tdf_bin')
ms2_file_name = st.text_input(label='Ms2 File Name', value='',
                              help='name to give ms2 file, leave blank to randomly generate a unique name.')

if ms2_file_name == '':
    ms2_file_name = str(uuid4()) + '.ms2'
st.markdown(f'**output ms2 file**:  {ms2_file_name}')

if st.button('Run'):

    if tdf is None:
        st.warning('upload tdf file')

    if tdf_bin is None:
        st.warning('upload tdf_bin file')

    if tdf is None or tdf_bin is None:
        st.stop()

    rand_uuid = str(uuid4())
    d_folder = Path(rand_uuid)

    try:
        os.mkdir(d_folder)

        tdf_path = d_folder / 'analysis.tdf'
        tdf_path.write_bytes(tdf.getvalue())

        tdf_bin_path = d_folder / 'analysis.tdf_bin'
        tdf_bin_path.write_bytes(tdf_bin.getvalue())

        ms2_file = generate_ms2(str(d_folder))
    finally:
        shutil.rmtree(str(d_folder))

    st.download_button('Download Ms2', ms2_file, ms2_file_name)




