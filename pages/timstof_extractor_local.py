import os
import time

import streamlit as st
from tdfextractor.ms2_extractor import write_ms2_file

st.title('TimsTof Raw File Extractor')

with st.expander('Help'):
    st.subheader('Where to find tdf files?')
    st.markdown("""
    ctrl+right click DFolder and select 'copy as path', then paste path in text box
    """)

d_folder = st.text_input('Path to DFolder', 'path/to/dfolder')
include_spectra = st.checkbox(label='Include Spectra', value=True, help='Include MS/MS spectra')

if st.button('Run'):

    if d_folder == 'path/to/dfolder':
        st.warning('Enter path to dfolder!')
        st.stop()
    elif not os.path.exists(d_folder):
        st.warning('Dfolder path invalid!')
        st.stop()

    start_time = time.time()
    write_ms2_file(d_folder, include_spectra=include_spectra)
    st.write('Done!')
    st.metric(label='Time', value=time.time()-start_time)
