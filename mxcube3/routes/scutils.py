# -*- coding: utf-8 -*-
import logging

# We are patching queue_entry.mount_sample at the end of this file.
import queue_entry

from mxcube3 import app as mxcube
from queue_entry import QueueSkippEntryException, CENTRING_METHOD


def set_current_sample(sample_id):
    mxcube.CURRENTLY_MOUNTED_SAMPLE = str(sample_id)


def get_current_sample():
    return mxcube.CURRENTLY_MOUNTED_SAMPLE


def mount_sample(beamline_setup_hwobj,
                 view, data_model,
                 centring_done_cb, async_result):

    view.setText(1, "Loading sample")
    set_current_sample(data_model.loc_str)

    beamline_setup_hwobj.shape_history_hwobj.clear_all()
    log = logging.getLogger("user_level_log")

    loc = data_model.location
    holder_length = data_model.holder_length

    # This is a possible solution how to deal with two devices that
    # can move sample on beam (sample changer, plate holder, in future 
    # also harvester)
    # TODO make sample_Changer_one, sample_changer_two
    if beamline_setup_hwobj.diffractometer_hwobj.in_plate_mode():
        sample_mount_device = beamline_setup_hwobj.plate_manipulator_hwobj
    else:
        sample_mount_device = beamline_setup_hwobj.sample_changer_hwobj

    if hasattr(sample_mount_device, '__TYPE__'):
        if sample_mount_device.__TYPE__ in ['Marvin','CATS']:
            element = '%d:%02d' % loc
            sample_mount_device.load(sample=element, wait=True)
        elif sample_mount_device.__TYPE__ == "PlateManipulator": 
            sample_mount_device.load_sample(sample_location=loc)
        else:
            if sample_mount_device.load_sample(holder_length, sample_location=loc, wait=True) == False:
                # WARNING: explicit test of False return value.
                # This is to preserve backward compatibility (load_sample was supposed to return None);
                # if sample could not be loaded, but no exception is raised, let's skip the sample
                raise QueueSkippEntryException("Sample changer could not load sample", "")

    if not sample_mount_device.hasLoadedSample():
        #Disables all related collections
        view.setOn(False)
        view.setText(1, "Sample not loaded")
        set_current_sample('')
        raise QueueSkippEntryException("Sample not loaded", "")
    else:
        view.setText(1, "Sample loaded")
        dm = beamline_setup_hwobj.diffractometer_hwobj 
        if dm is not None:
            try:
                dm.connect("centringAccepted", centring_done_cb)
                centring_method = view.listView().parent().\
                                  centring_method
                if centring_method == CENTRING_METHOD.MANUAL:
                    log.warning("Manual centring used, waiting for" +\
                                " user to center sample")
                    dm.startCentringMethod(dm.MANUAL3CLICK_MODE)
                elif centring_method == CENTRING_METHOD.LOOP:
                    dm.startCentringMethod(dm.C3D_MODE)
                    log.warning("Centring in progress. Please save" +\
                                " the suggested centring or re-center")
                elif centring_method == CENTRING_METHOD.FULLY_AUTOMATIC:
                    log.info("Centring sample, please wait.")
                    dm.startCentringMethod(dm.C3D_MODE)
                else:
                    dm.startCentringMethod(dm.MANUAL3CLICK_MODE)

                view.setText(1, "Centring !")
                centring_result = async_result.get()
                if centring_result['valid']: 
                    view.setText(1, "Centring done !")
                    log.info("Centring saved")
                else:
                    if centring_method == CENTRING_METHOD.FULLY_AUTOMATIC:
                        raise QueueSkippEntryException("Could not center sample, skipping", "")
                    else:
                        raise RuntimeError("Could not center sample")
            except:
                pass
            finally:
                dm.disconnect("centringAccepted", centring_done_cb)

def mount_sample_clean_up(sample):
    try:
        msg = '[SC] mounting %s (%r)', sample['location'], sample['sampleID']
        logging.getLogger('HWR').info(msg)
        set_current_sample(sample['sampleID'])

        if not sample['location'] == 'Manual':
            mxcube.sample_changer.load(sample['sampleID'], False)

        mxcube.queue.mounted_sample = sample['sampleID']
    except Exception:
        logging.getLogger('HWR').exception('[SC] sample could not be mounted')
        set_current_sample('')
        raise
    else:       
        # Clearing centered position
        mxcube.diffractometer.savedCentredPos = []
        mxcube.diffractometer.savedCentredPosCount = 1

        logging.getLogger('HWR').info('[SC] mounted %s' % sample)


def unmount_sample_clean_up(sample):
    try:
        if not sample['location'] == 'Manual':
            mxcube.sample_changer.unload(sample['sampleID'], False)
        mxcube.queue.mounted_sample = ''

        # Remove Centring points
        mxcube.diffractometer.savedCentredPos = []
        mxcube.diffractometer.savedCentredPosCount = 1

        msg = '[SC] %s unmounted %s (%r)', sample['location'], sample['sampleID']
        logging.getLogger('HWR').info(msg)
    except Exception:
        logging.getLogger('HWR').exception('[SC] sample could not be mounted')
        raise
    else:
         set_current_sample('')


# Important, patch queue_entry.mount_sample with the mount_sample defined above
queue_entry.mount_sample = mount_sample
