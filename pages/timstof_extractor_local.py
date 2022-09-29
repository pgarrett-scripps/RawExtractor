import os
import shutil
from pathlib import Path

import streamlit as st
from tdfextractor.ms2_extractor import get_ms2_content

st.title('TimsTof Raw File Extractor')

with st.expander('Help'):
    st.subheader('Where to find tdf files?')
    st.markdown("""
    ctrl+right click DFolder and select 'copy as path', then paste path in text box
    """)

d_folder = st.text_input('Path to DFolder', 'path/to/dfolder')

if st.button('Run'):

    if d_folder == 'path/to/dfolder':
        st.warning('Enter path to dfolder!')
        st.stop()
    elif not os.path.exists(d_folder):
        st.warning('Dfolder path invalid!')
        st.stop()

    ms2_content = ''.join(get_ms2_content(str(d_folder)))
    st.download_button('Download Ms2', ms2_content, Path(d_folder).stem + '.ms2')