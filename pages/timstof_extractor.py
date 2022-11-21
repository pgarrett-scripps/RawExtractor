import os
import shutil
import time
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

import streamlit as st
from tdfextractor.ms2_extractor import get_ms2_content, generate_header
from serenipy.ms2 import to_ms2
from tdfpy import PandasTdf

st.title('TimsTof Raw File Extractor')

with st.expander('Help'):
    st.subheader('Where to find tdf files?')
    st.markdown("""
    The analysis.tdf and analysis.tdf_bin are located inside of the .d folder

    Rename the ms2 file to whatever you like. Otherwise leave it blank to randomly generate a file name.
    """)

tdf = st.file_uploader(label='tdf file', type='.tdf')
tdf_bin = st.file_uploader(label='tdf_bin file', type='.tdf_bin')
include_spectra = st.checkbox(label='Include Spectra', value=True, help='Include MS/MS spectra')


@contextmanager
def sqlite_connect(tdf, tdf_bin):
    fp = Path(str(uuid4()))
    os.mkdir(fp)
    tdf_path = fp / 'analysis.tdf'
    tdf_path.write_bytes(tdf.getvalue())

    tdf_bin_path = fp / 'analysis.tdf_bin'
    tdf_bin_path.write_bytes(tdf_bin.getvalue())

    try:
        yield fp
    finally:
        shutil.rmtree(str(fp))


if st.button('Run'):

    if tdf is None:
        st.warning('upload tdf file')
        st.stop()

    if tdf_bin is None:
        st.warning('upload tdf_bin file')
        st.stop()

    start_time = time.time()
    with sqlite_connect(tdf, tdf_bin) as d_folder:
        ms2_header = generate_header(d_folder)
        ms2_spectra = list(get_ms2_content(str(d_folder), include_spectra=include_spectra))
        ms2_content = to_ms2([ms2_header], ms2_spectra)

        pd_tdf = PandasTdf(str(Path(d_folder) / 'analysis.tdf'))
        metadata = {row[0]:row[1] for name, row in pd_tdf.global_metadata.iterrows()}
        ms2_name = str(d_folder) + ".ms2"
        if metadata.get('SampleName'):
            ms2_name = metadata['SampleName'] + ".ms2"

        st.write('Done!')
        st.metric(label='Time', value=time.time() - start_time)

        st.download_button('Download Ms2', ms2_content, ms2_name)
