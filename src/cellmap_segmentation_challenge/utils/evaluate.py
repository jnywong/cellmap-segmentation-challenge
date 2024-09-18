"""
Submission requirements:
1. The submission should be a single zip file containing a single Zarr-2 file with the following structure:
   - submission.zarr
     - /<test_volume_name>
        - /<label_name>
2. The names of the test volumes and labels should match the names of the test volumes and labels in the test data.
3. Each label volume should be a 3D binary volume with the same shape and scale as the corresponding test volume. The scale for all volumes is 8x8x8 nm/voxel.

Assuming your data is already 8x8x8nm/voxel, you can convert the submission to the required format using the following convenience functions:
- For converting a single 3D numpy array of class labels to a Zarr-2 file, use the following function:
  `cellmap_segmentation_challenge.utils.evaluate.save_numpy_labels_to_zarr`
- For converting a list of 3D numpy arrays of binary labels to a Zarr-2 file, use the following function:
  `cellmap_segmentation_challenge.utils.evaluate.save_numpy_binary_to_zarr`
The arguments for both functions are the same:
- `submission_path`: The path to save the Zarr-2 file (ending with <filename>.zarr).
- `test_volume_name`: The name of the test volume.
- `label_names`: A list of label names corresponding to the list of 3D numpy arrays or the number of the class labels (0 is always assumed to be background).
- `labels`: A list of 3D numpy arrays of binary labels or a single 3D numpy array of class labels.

To zip the Zarr-2 file, you can use the following command:
`zip -r submission.zip submission.zarr`

To submit the zip file, upload it to the challenge platform.
"""

import json
import sys
import zipfile
import numpy as np
import zarr
import os
from upath import UPath


def unzip_file(zip_path):
    """
    Unzip a zip file to a specified directory.

    Args:
        zip_path (str): The path to the zip file.

    Example usage:
        unzip_file('submission.zip')
    """
    name = UPath(zip_path).name
    extract_path = UPath(zip_path).parent / name.split(".")[0]
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_path)

    return extract_path


def save_numpy_labels_to_zarr(
    submission_path, test_volume_name, label_name, labels, overwrite=False
):
    """
    Save a single 3D numpy array of class labels to a
    Zarr-2 file with the required structure.

    Args:
        submission_path (str): The path to save the Zarr-2 file (ending with <filename>.zarr).
        test_volume_name (str): The name of the test volume.
        label_names (str): The names of the labels.
        labels (np.ndarray): A 3D numpy array of class labels.

    Example usage:
        # Generate random class labels, with 0 as background
        labels = np.random.randint(0, 4, (128, 128, 128))
        save_numpy_labels_to_zarr('submission.zarr', 'test_volume', ['label1', 'label2', 'label3'], labels)
    """
    # Create a Zarr-2 file
    if not UPath(submission_path).exists():
        os.makedirs(UPath(submission_path).parent)
        store = zarr.DirectoryStore(submission_path)
        zarr_group = zarr.group(store)

    # Save the test volume group
    zarr_group.create_group(test_volume_name, overwrite=overwrite)

    # Save the labels
    for i, label_name in enumerate(label_name):
        zarr_group[test_volume_name].create_dataset(
            label_name,
            data=(labels == i + 1),
            chunks=(64, 64, 64),
            # compressor=zarr.Blosc(cname='zstd', clevel=3, shuffle=2),
        )


def save_numpy_binary_to_zarr(
    submission_path, test_volume_name, label_names, labels, overwrite=False
):
    """
    Save a list of 3D numpy arrays of binary labels to a
    Zarr-2 file with the required structure.

    Args:
        submission_path (str): The path to save the Zarr-2 file (ending with <filename>.zarr).
        test_volume_name (str): The name of the test volume.
        label_names (list): A list of label names corresponding to the list of 3D numpy arrays.
        labels (list): A list of 3D numpy arrays of binary labels.

    Example usage:
        label_names = ['label1', 'label2', 'label3']
        # Generate random binary volumes for each label
        labels = [np.random.randint(0, 2, (128, 128, 128)) for _ in range len(label_names)]
        save_numpy_binary_to_zarr('submission.zarr', 'test_volume', label_names, labels)

    """
    # Create a Zarr-2 file
    if not UPath(submission_path).exists():
        os.makedirs(UPath(submission_path).parent)
        store = zarr.DirectoryStore(submission_path)
        zarr_group = zarr.group(store)

    # Save the test volume group
    zarr_group.create_group(test_volume_name, overwrite=overwrite)

    # Save the labels
    for i, label_name in enumerate(label_names):
        zarr_group[test_volume_name].create_dataset(
            label_name,
            data=labels[i],
            chunks=(64, 64, 64),
            # compressor=zarr.Blosc(cname='zstd', clevel=3, shuffle=2),
        )


def score_label(pred_label_path) -> dict[str, float]:
    """
    Score a single label volume against the ground truth label volume.

    Args:
        pred_label_path (str): The path to the predicted label volume.

    Returns:
        dict: A dictionary of scores for the label volume.

    Example usage:
        scores = score_label('pred.zarr/test_volume/label1')
    """
    # Load the predicted and ground truth label volumes
    label_name = UPath(pred_label_path).name
    volume_name = UPath(pred_label_path).parent.name
    pred_label = zarr.open(pred_label_path)
    # TODO: REPLACE WITH THE GROUND TRUTH LABEL VOLUME PATH
    truth_label = zarr.open(UPath("truth.zarr") / volume_name / label_name)

    # Check if the label volumes have the same shape
    assert (
        pred_label.shape == truth_label.shape
    ), "The predicted and ground truth label volumes must have the same shape."

    # Calculate the scores
    scores = {}
    ...

    return scores


def score_volume(pred_volume_path) -> dict[str, dict[str, float]]:
    """
    Score a single volume against the ground truth volume.

    Args:
        pred_volume_path (str): The path to the predicted volume.

    Returns:
        dict: A dictionary of scores for the volume.

    Example usage:
        scores = score_volume('pred.zarr/test_volume')
    """
    # Find labels to score
    pred_labels = [a for a in zarr.open(pred_volume_path).array_keys()]

    volume_name = UPath(pred_volume_path).name
    truth_labels = [
        a for a in zarr.open(UPath("truth.zarr") / volume_name).array_keys()
    ]

    labels = list(set(pred_labels) & set(truth_labels))

    # Score each label
    scores = {label: score_label(pred_volume_path / label) for label in labels}

    return scores


def score_submission(
    submission_path, save_path=None
) -> dict[str, dict[str, dict[str, float]]]:
    """
    Score a submission against the ground truth data.

    Args:
        submission_path (str): The path to the zipped submission Zarr-2 file.
        save_path (str): The path to save the scores.

    Returns:
        dict: A dictionary of scores for the submission.

    Example usage:
        scores = score_submission('submission.zip')
    """
    # Unzip the submission
    submission_path = unzip_file(submission_path)

    # Load the submission
    submission = zarr.open(submission_path)

    # Find volumes to score
    pred_volumes = [a for a in submission.array_keys()]
    truth_volumes = [a for a in zarr.open("truth.zarr").array_keys()]

    volumes = list(set(pred_volumes) & set(truth_volumes))

    # Score each volume
    scores = {volume: score_volume(submission_path / volume) for volume in pred_volumes}

    # Save the scores
    if save_path:
        with open(save_path, "w") as f:
            json.dump(scores, f)
    else:
        return scores


if __name__ == "__main__":
    # Evaluate a submission
    # example usage: python evaluate.py submission.zip
    score_submission(sys.argv[1])
