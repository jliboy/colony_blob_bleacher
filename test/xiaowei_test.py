import numpy as np
import pandas as pd
import napari
from pycromanager import Bridge
from matplotlib.backends.qt_compat import QtCore, QtWidgets
if QtCore.qVersion() >= "5.":
    from matplotlib.backends.backend_qt5agg import FigureCanvas
else:
    from matplotlib.backends.backend_qt4agg import FigureCanvas
from matplotlib.figure import Figure
from vispy.color import Colormap
from skimage.measure import label,regionprops
from shared.find_organelles import find_organelle, nucleoli_analysis
import shared.analysis as ana
import shared.display as dis
import shared.objects as obj
import shared.bleach_points as ble
import os
from skimage.segmentation import random_walker, clear_border
from scipy import ndimage


# --------------------------
# PARAMETERS allow change
# --------------------------
# paths
# data_path = "C:\\Users\\NicoLocal\\Images\\Jess\\20201116-Nucleoli-bleaching-4x\\PythonAcq1\\AutoBleach_15"
data_path = "/Users/xiaoweiyan/Dropbox/LAB/ValeLab/Projects/Blob_bleacher/" \
            "20201216_CBB_nucleoliBleachingTest_drugTreatment/Ctrl-2DG-CCCP-36pos_partial/exp_98/"
save_path = "/Users/xiaoweiyan/Dropbox/LAB/ValeLab/Projects/Blob_bleacher/" \
            "20201216_CBB_nucleoliBleachingTest_drugTreatment/Ctrl-2DG-CCCP-36pos_partial/exp_110/"

# values for analysis
data_z = 0
data_c = 0
data_p = 0
ref_t = 0  # reference frame t for nucleoli detection, bleach spots filtration
thresholding = 'local-nucleoli'
# global thresholding method; choose in between 'na','otsu','yen', 'local-nucleoli' and 'local-sg'
min_size = 10  # minimum nucleoli size; default = 10
max_size = 1000  # maximum nucleoli size; default = 1000;
                 # larger ones are generally cells without nucleoli
num_dilation = 3  # number of dilation from the coordinate;
                  # determines analysis size of the analysis spots; default = 3

# modes
mode_bleach_detection = 'single-offset'  # only accepts 'single-raw' or 'single-offset'
display_mode = 'N'  # only accepts 'N' or 'Y'

# --------------------------
# LOAD MOVIE
# --------------------------
print("### Load movie ...")

# build up pycromanager bridge
# first start up Micro-Manager (needs to be compatible version)
bridge = Bridge()
mmc = bridge.get_core()
mm = bridge.get_studio()
# load time series data
store = mm.data().load_data(data_path, True)
max_t = store.get_max_indices().get_t()
cb = mm.data().get_coords_builder()
cb.t(0).p(0).c(0).z(0)

# --------------------------------------
# IMAGE ANALYSIS based on reference time
# --------------------------------------
print("### Image analysis: nucleoli detection based on reference time %s ..." % ref_t)

# reference image of ref_t
temp = store.get_image(cb.p(data_p).z(data_z).c(data_c).t(ref_t).build())
pix = np.reshape(temp.get_raw_pixels(), newshape=[temp.get_height(), temp.get_width()])
# nuclear detection
markers = np.zeros_like(pix)
markers[pix < 220] = 1
markers[pix > 450] = 2
seg = random_walker(pix, markers)

nuclear = np.zeros_like(pix)
nuclear[seg == 2] = 1
nuclear_fill = ndimage.binary_fill_holes(nuclear)

# separate touching nuclei
label_nuclear = obj.label_watershed(nuclear_fill)
label_nuclear_ft = clear_border(label_nuclear)
label_nuclear_ft = obj.label_remove_small(label_nuclear_ft, 1500)

nuclear_prop = regionprops(label_nuclear_ft)

with napari.gui_qt():
    viewer = napari.Viewer()
    viewer.add_image(pix, name='data')
    winter_woBg = dis.num_color_colormap('winter', len(nuclear_prop))[0]
    viewer.add_image(label_nuclear_ft, name='nuclear', colormap=('winter woBg', winter_woBg))
