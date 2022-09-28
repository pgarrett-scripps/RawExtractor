import timsdata
import numpy as np
import sqlite3
from sqlite3 import Error
import math

place_high = 3
precursor_counter = 0
version = "0.1.3"


def enhance_signal(intensity):
    return (intensity ** 1.414 + 100.232) ** 1.414


def create_connection(analysis_dir):
    import os
    db_file = os.path.join(analysis_dir, 'analysis.tdf')
    """ create a database connection to the SQLite database
        specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return None


def select_all_PasefFrameMsMsInfo(conn):
    """
    Query all rows in the tasks table
    :param conn: the Connection object
    :return:
    """
    cur = conn.cursor()
    cur.execute("SELECT * FROM PasefFrameMsMsInfo")

    rows = cur.fetchall()

    data_all = np.array(rows)
    return data_all


def select_all_Frames(conn):
    """
    Query all rows in the tasks table
    :param conn: the Connection object
    :return:
    """
    cur = conn.cursor()
    cur.execute("SELECT * FROM Frames")

    rows = cur.fetchall()

    data_all = np.array(rows)
    return data_all


def select_all_Precursors(conn):
    """
    Query all rows in the tasks table
    :param conn: the Connection object
    :return:
    """
    cur = conn.cursor()
    cur.execute("SELECT * FROM Precursors")

    rows = cur.fetchall()

    data_all = np.array(rows)
    return data_all


def generate_MS1_scan(conn, id, get_last=False):
    global place_high
    cur = conn.cursor()
    key = (id,)
    cur.execute('''
        select Frame, ScanNumBegin from PasefFrameMsMsInfo 
        INNER JOIN Precursors on PasefFrameMsMsInfo.Precursor = Precursors.Id 
        where Precursors.Parent = ? order by frame, ScanNumBegin ''', key)
    rows = cur.fetchall()
    if len(rows) > 0:
        index = len(rows) - 1 if get_last else 0
        data = np.array(rows[index])
        tims_scan_num_begin = int(data[1])
        frame = int(data[0])
        place = math.ceil(math.log10(tims_scan_num_begin))
        if place > place_high:
            place_high = place
        else:
            place = place_high

        ms1_scan = frame * 10 ** place + tims_scan_num_begin - 1
        return ms1_scan
    else:
        return -1


def generate_ms1_scan_v2(frame_id, precursor_list):
    global precursor_counter
    while precursor_counter < len(precursor_list) and precursor_list[precursor_counter][-1] < frame_id:
        precursor_counter += 1
    if precursor_counter >= len(precursor_list):
        id = precursor_list[len(precursor_list) - 1][0]
        parent = precursor_list[len(precursor_list) - 1][-1]
        return id + parent + 1, id, parent
    elif precursor_list[precursor_counter][-1] > frame_id and precursor_counter > 0:
        id = precursor_list[precursor_counter - 1][0]
        parent = precursor_list[precursor_counter - 1][-1]
        return id + parent + 1, id, parent
    else:
        id = precursor_list[precursor_counter][0]
        parent = precursor_list[precursor_counter][-1]
        return id + parent - 1, id, parent


def msms_frame_parent_dict(all_frame):
    i = 1
    parent_frame_id_dict = {}
    msms_type_array = np.array(all_frame).transpose()[4]
    last_zero = 0
    for each in msms_type_array:
        if each == '0':
            parent_frame_id_dict[i] = i
            last_zero = i
        elif each == '8':
            parent_frame_id_dict[i] = last_zero
        i += 1
    return parent_frame_id_dict


def build_offset_map(precursor_map, all_ms1_list):
    offset = 0
    offset_map = {}
    for row in all_ms1_list:
        frame_id = int(row[0])
        offset_map[frame_id] = offset
        if frame_id in precursor_map:
            precursor_id = int(precursor_map[frame_id][0])
            parent = int(precursor_map[frame_id][-1])
            offset += precursor_id + parent
    return offset_map


def build_frame_id_ms1_scan_map(precursor_map, all_ms1_list):
    frame_id_ms1_scan_map = {}
    ms2_map = {}
    prev_scan = 0
    for row in all_ms1_list:
        frame_id = int(row[0])
        prev_scan += 1
        frame_id_ms1_scan_map[frame_id] = prev_scan
        if frame_id in precursor_map:
            if frame_id not in ms2_map:
                ms2_map[frame_id] = {}
            for count, rows in enumerate(precursor_map[frame_id], prev_scan + 1):
                prec_id = int(rows[0])
                ms2_map[frame_id][prec_id] = count
            prev_scan += len(precursor_map[frame_id])
    return frame_id_ms1_scan_map, ms2_map


def generate_ms2(analysis_directory):
    td = timsdata.TimsData(analysis_directory)

    conn = td.conn
    ms2_lines = []

    try:

        precursor_map = {}
        precursor_collision_energy_map = {}
        with conn:
            msms_data = select_all_PasefFrameMsMsInfo(conn)
            for frame, sn_begin, sn_end, isoMz, isoW, ce, prec_id in msms_data:
                precursor_collision_energy_map[prec_id] = ce
            # print msms_data[0:5]
            all_frame = select_all_Frames(conn)
            frame_id_to_frame = {int(frame[0]):frame for frame in all_frame}
            # print all_frame[0:5]
            precursor_list = select_all_Precursors(conn)
            for row in precursor_list:
                parent_id = int(row[-1])
                if parent_id not in precursor_map:
                    precursor_map[parent_id] = []
                precursor_map[parent_id].append(row)

        all_ms1_frames = [a for a in all_frame if a[4] == '0']

        frame_id_ms1_scan_map, ms2_scan_map = build_frame_id_ms1_scan_map(precursor_map, all_ms1_frames)

        precursor_array = np.array(
            precursor_list)  # 'ID', 'LargestPeakMz', 'AverageMz', 'MonoisotopicMz', 'Charge', 'ScanNumber', 'Intensity', 'Parent'

        parent_frame_array = np.array(precursor_array[:, 7])
        frame_index_list = []
        last_val = 0
        for idx, val in enumerate(parent_frame_array):
            if val != last_val:
                frame_index_list.append(idx)
            last_val = val

        ms2_header = 'H\tExtractor\tTimsTOF_extractor\n' \
                     'H\tExtractorVersion\t{}\n' \
                     'H\tPublicationDate\t20-02-2020\n' \
                     'H\tComments\tTimsTOF_extractor written by Yu Gao, 2018\n' \
                     'H\tComments\tTimsTOF_extractor modified by Titus Jung, 2019\n' \
                     'H\tComments\tTimsTOF_extractor modified by Patrick Garrett, 2021\n' \
                     'H\tExtractorOptions\tMSn\n' \
                     'H\tAcquisitionMethod\tData-Dependent\n' \
                     'H\tInstrumentType\tTIMSTOF\n' \
                     'H\tDataType\tCentroid\n' \
                     'H\tScanType\tMS2\n' \
                     'H\tResolution\n' \
                     'H\tIsolationWindow\n' \
                     'H\tFirstScan\t1\n' \
                     'H\tLastScan\t{}\n' \
                     'H\tMonoIsotopic PrecMz\tTrue\n'.format(version, len(msms_data))

        ms2_lines.append(ms2_header)
        for row in precursor_list:
            prc_id, largest_preak_mz, average_mz, monoisotopic_mz, cs, scan_number, intensity, parent = row
            prc_id_int = int(prc_id)
            if monoisotopic_mz is not None and cs is not None:
                prc_mass_mz = float(monoisotopic_mz)
                prc_mass = (prc_mass_mz * cs) - (cs - 1) * 1.007276466

                mz_int_arr = td.readPasefMsMs([prc_id_int])
                parent_index = int(parent)
                scan_id = ms2_scan_map[parent_index][prc_id_int]
                rt_time = float(frame_id_to_frame[parent_index][1])
                k0 = td.scanNumToOneOverK0(parent_index, [scan_number])
                mz_arr = mz_int_arr[prc_id_int][0]
                collision_energy = precursor_collision_energy_map[prc_id_int]
                if len(mz_arr) > 0:
                    ms2_lines.append("S\t{0:06d}\t{1:06d}\t{2:.5f}\n".format(scan_id, scan_id, prc_mass_mz))
                    ms2_lines.append("I\tTIMSTOF_Parent_ID\t{}\n".format(parent))
                    ms2_lines.append("I\tTIMSTOF_Precursor_ID\t{}\n".format(prc_id))
                    ms2_lines.append("I\tPrecursor Intensity\t{0:.5f}\n".format(intensity))
                    ms2_lines.append("I\tRetTime\t{0:.5f}\n".format(rt_time))
                    ms2_lines.append("I\tIon Mobility\t{0:.5f}\n".format(k0[0]))
                    ms2_lines.append("I\tCCS\t{0:.5f}\n".format(timsdata.oneOverK0ToCCSforMz(k0[0], cs, prc_mass_mz)))
                    ms2_lines.append("I\tCollision Energy\t{0:.3f}\n".format(collision_energy))
                    ms2_lines.append("Z\t{1}\t{0:.5f}\n".format(prc_mass, cs))

                    int_arr = mz_int_arr[prc_id_int][1]
                    for j in range(0, len(mz_arr)):
                        ms2_lines.append("%.5f %.1f \n" % (mz_arr[j], int_arr[j]))
    finally:
        conn.close()
    return ''.join(ms2_lines)
