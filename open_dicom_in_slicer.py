import sys
import os
import slicer
from DICOMLib import DICOMUtils

def log(msg):
    print(f"[SLICER] {msg}")

# ----------------------------
# Input
# ----------------------------

if len(sys.argv) < 2:
    log("No DICOM folder provided")
    sys.exit(1)

dicom_folder = sys.argv[1]

if not os.path.isdir(dicom_folder):
    log(f"Invalid DICOM folder: {dicom_folder}")
    sys.exit(1)

log(f"Using DICOM folder: {dicom_folder}")

# ----------------------------
# Ensure DICOM database
# ----------------------------

if not slicer.dicomDatabase.isOpen:
    slicer.dicomDatabase.openDatabase(
        slicer.app.temporaryPath + "/DICOM.db"
    )

# ----------------------------
# Import + Load DICOM
# ----------------------------

with DICOMUtils.TemporaryDICOMDatabase() as db:
    DICOMUtils.importDicom(dicom_folder, db)

    patient_uids = db.patients()
    if not patient_uids:
        log("No patients found after import")
        sys.exit(1)

    DICOMUtils.loadPatientByUID(patient_uids[0])

log("DICOM imported and loaded")

# ----------------------------
# Select preferred volume
# ----------------------------

def select_preferred_volume(volumes):
    priority = ["axial", "ax", "bone", "ct"]
    for term in priority:
        for v in volumes:
            if term in v.GetName().lower():
                log(f"Selected volume: {v.GetName()}")
                return v
    return volumes[0]

volumes = slicer.util.getNodesByClass("vtkMRMLScalarVolumeNode")
if not volumes:
    log("No volumes found")
    sys.exit(1)

volume = select_preferred_volume(volumes)

# ----------------------------
# Volume Rendering
# ----------------------------

slicer.util.selectModule("VolumeRendering")

vr_logic = slicer.modules.volumerendering.logic()
display_node = vr_logic.CreateDefaultVolumeRenderingNodes(volume)
display_node.SetVisibility(True)

# ----------------------------
# Center view
# ----------------------------

view = slicer.app.layoutManager().threeDWidget(0).threeDView()
view.resetCamera()
view.resetFocalPoint()

log("Volume rendering enabled and view centered")
log("Ready.")
