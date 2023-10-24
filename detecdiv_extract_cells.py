import re
import os
import numpy as np
from scipy.io import loadmat
import mahotas as mh
import autoSegment as auto
import matplotlib.pyplot as plt

import argparse


# Sorting functions
def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    '''
    return [ atoi(c) for c in re.split(r'(\d+)', text) ]


def save_cells(image_path, image_type, cell_count) -> int:
    """
    Saves the cells in the image as individual images.
    image_path: path to the image to process.
    image_type: string with the type of image to process.
    cell_count: number of cells to process.

    Returns the number of cells processed.
    """

    # Load MATLAB normalization data
    #path = os.path.join("giles", "GFP", "Normalization")
    mat = loadmat(os.path.join(image_path, "frame1.mat"))
    image = mat["imageFlat"]
    mask = mat["deadZoneMask"]

    # Normalize image in case there are pixels with value > 1
    image = image / image.max()

    # Run automatic segmentation of cells
    cells = auto.segment(mask)

    # Get centers of preselected regions
    centers = mh.center_of_mass(cells, cells)

    # Remove background region from data
    centers = centers[1:]
    
    for cellID, pix in enumerate(centers):  # Iterate over all intensity centers

        # Get coodinates of the center   
        x = int(pix[0])
        y = int(pix[1])

        # Get coordinates of 200x200 box around each cell
        [x0, x1, y0, y1] = auto.get_bg_box(x, y)

        # Select 200x200 image around the center
        selection = image[x0:x1, y0:y1]

        # Mask out the background
        current_mask = (cells == cellID + 1)
        img_masked = image * current_mask
        selection_masked = img_masked[x0:x1, y0:y1]
        
        # Convert to 16-bit image
        selection = (selection * (2**16-1)).astype(np.uint16) 
        selection_masked = (selection_masked * (2**16-1)).astype(np.uint16) 

        # Save cell box
        mask_out_path = os.path.join(image_path, "../..", "single_cells_mask")
        img_out_path = os.path.join(image_path, "../..", "single_cells_img")

        if image_type in ['mask', 'both']:
            # Create path if it doesn't exist
            if not os.path.exists(mask_out_path):
                os.makedirs(mask_out_path)
                print("Created path: {}".format(mask_out_path))

            mh.imsave(os.path.join(mask_out_path, f"cell_{cell_count:04d}_w1GFP.tif"), selection_masked)

        if image_type in ['image', 'both']:
            # Create path if it doesn't exist
            if not os.path.exists(img_out_path):
                os.makedirs(img_out_path)

            mh.imsave(os.path.join(img_out_path, f"cell_{cell_count:04d}_w1GFP.tif"), selection)

        print(f"Saved {cell_count}")
        cell_count += 1

    return cell_count


# User interaction and parameter logic
parser = argparse.ArgumentParser(description="Extract masked cells from normalized images and save them as individual .tif files.")
parser.add_argument("path", type=str, help="Path to images directory.")
parser.add_argument("type", choices=['mask', 'image', 'both'], help='Choose which image(s) you want to extract.')
parser.add_argument("-c", "--cell_count", type=int, default=1, help="Starting cell count, useful to add cells to existing dataset.")

args = parser.parse_args()

experiment_folder = args.path
image_type = args.type
cell_count = args.cell_count

if cell_count != 1:
    print("Starting at cell count: {}".format(cell_count))

# Look for normalization files inside given path
for root, dirs, files in os.walk(experiment_folder):
    dirs.sort(key=natural_keys)  # Sort directories in human order
    for file in files:
        if file.endswith('.mat'):
            print(root)
            cell_count = save_cells(root, image_type, cell_count)
