import numpy as np
from pycocotools import mask as maskUtils

from .coco import CocoDataset


def rotate_mat(ang):
    # input in radius
    return np.array(
        [
        [np.cos(ang), -np.sin(ang)],
        [np.sin(ang), np.cos(ang)],
        ],dtype=float
    )

def generate_obj_mask(ann, h, w):
    angle = ann['attributes']['rotation'] / 180 * np.pi
    bbox = ann['bbox']
    center = np.array([bbox[0], bbox[1]])
    rel_coords = np.array([
        [bbox[2], bbox[3]],
        [bbox[2], -bbox[3]],
        [-bbox[2], -bbox[3]],
        [-bbox[2], bbox[3]],
    ]) / 2
    rel_coords = center + (rel_coords @ rotate_mat(angle).T)
    rles = maskUtils.frPyObjects(rel_coords.flatten()[None, :].astype(int).tolist(), 720, 1280)
    rle = maskUtils.decode(maskUtils.merge(rles))
    if rle.max() == 0:
        import pdb
        pdb.set_trace()
    return rle



class PUBRDataset(CocoDataset):
    # Note! same with DOTA2_v3
    CLASSES = ('plane', 'baseball-diamond',
                'bridge', 'ground-track-field',
                'small-vehicle', 'large-vehicle',
                'ship', 'tennis-court',
                'basketball-court', 'storage-tank',
                'soccer-ball-field', 'roundabout',
                'harbor', 'swimming-pool',
                'helicopter', 'container-crane')

    def _parse_ann_info(self, ann_info, with_mask=True):
        """Parse bbox and mask annotation.

        Args:
            ann_info (list[dict]): Annotation info of an image.
            with_mask (bool): Whether to parse mask annotations.

        Returns:
            dict: A dict containing the following keys: bboxes, bboxes_ignore,
                labels, masks, mask_polys, poly_lens.
        """
        gt_bboxes = []
        gt_labels = []
        gt_bboxes_ignore = []
        # Two formats are provided.
        # 1. mask: a binary map of the same size of the image.
        # 2. polys: each mask consists of one or several polys, each poly is a
        # list of float.
        if with_mask:
            gt_masks = []
            gt_mask_polys = []
            gt_poly_lens = []
        for i, ann in enumerate(ann_info):
            if ann.get('ignore', False):
                continue
            x1, y1, w, h = ann['bbox']
            if ann['area'] <= 80 or max(w, h) < 12:
                continue
            bbox = [x1, y1, x1 + w - 1, y1 + h - 1]
            if ann['iscrowd']:
                gt_bboxes_ignore.append(bbox)
            else:
                gt_bboxes.append(bbox)
                gt_labels.append(self.cat2label[ann['category_id']])
            if with_mask:
                gt_masks.append(generate_obj_mask(ann, h, w))
                mask_polys = [
                    p for p in ann['segmentation'] if len(p) >= 6
                ]  # valid polygons have >= 3 points (6 coordinates)
                poly_lens = [len(p) for p in mask_polys]
                gt_mask_polys.append(mask_polys)
                gt_poly_lens.extend(poly_lens)
        if gt_bboxes:
            gt_bboxes = np.array(gt_bboxes, dtype=np.float32)
            gt_labels = np.array(gt_labels, dtype=np.int64)
        else:
            gt_bboxes = np.zeros((0, 4), dtype=np.float32)
            gt_labels = np.array([], dtype=np.int64)

        if gt_bboxes_ignore:
            gt_bboxes_ignore = np.array(gt_bboxes_ignore, dtype=np.float32)
        else:
            gt_bboxes_ignore = np.zeros((0, 4), dtype=np.float32)

        ann = dict(
            bboxes=gt_bboxes, labels=gt_labels, bboxes_ignore=gt_bboxes_ignore)

        if with_mask:
            ann['masks'] = gt_masks
            # poly format is not used in the current implementation
            ann['mask_polys'] = gt_mask_polys
            ann['poly_lens'] = gt_poly_lens
        return ann
