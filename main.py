import numpy as np
import pandas as pd
import os
import argparse

from scipy.io import loadmat
import autoSegment as auto
import interactive as inter


def analyze_experiment(path, manual=False, pillar_height=5.6, pixel_size=0.325):
    """
    Loads image and mask, calculates volumes and decides whether or not to analyze objects manually
    :param path: path to normalization file
    :param manual: manual analysis flag. If True, calls interactive functions to manually select the objects
    :param pillar_height: Height of the microfluidic chamber in µm
    :param pixel_size: Size of image pixel in µm given by your camera pixel size and the magnification used
    :return volumes: DataFrame with volume data and manual or automatic filter
    """

    # Load MATLAB normalization data (default)
    # If you have your own normalized images, load using mh.imread(os.path.join(path, "image.tif"))
    mat = loadmat(os.path.join(path, "frame1.mat"))
    image = mat["imageFlat"]
    mask = mat["deadZoneMask"]

    mask = mask > 0

    # Output variables
    segm_path = os.path.join(path, "../Segmentation")
    segm_file = "py_data_Auto.tsv"

    # Gets selections from normalization mask
    cells = auto.segment(mask)

    # Calculates volumes
    volumes = auto.get_volume(image, mask, cells, pillar_height=pillar_height, pixel_size=pixel_size)

    if volumes.empty:
        return pd.DataFrame({})

    if manual:
        # Displays objects for manual filtering by the user
        volumes = inter.filter_cells(image, mask, volumes, path=path)
        segm_file = f"py_data_Manual.tsv"

    # Adds folder name column
    volumes['Path'] = os.path.abspath(os.path.join(path, ".."))

    volumes.to_csv(os.path.join(segm_path, segm_file), sep="\t")  # Save

    return volumes


def print_output_stats(data, filter_name):
    """
    Prints the output of the analysis extracted from pd.DataFrame.describe()
    """

    stats = data.loc[data[filter_name] == False, "Volume"].describe()

    cell_count = int(stats["count"])
    mean_vol = stats["mean"]
    std_vol = stats["std"]
    min_vol = stats["min"]
    Q1_vol = stats["25%"]
    med_vol = stats["50%"]
    mad = data.loc[data[filter_name] == False, "Volume"].mad()
    Q3_vol = stats["75%"]
    max_vol = stats["max"]
    
    print(f"Total number\n{'of objects:':16}{len(data)}")
    print(f"{'Accepted cells:':16}{cell_count:d}")
    print()
    print(f"{'Mean volume:':16}{mean_vol:.1f} µm3")
    print(f"{'Volume stdev:':16}{std_vol:.1f} µm3")
    print(f"{'Min. volume:':16}{min_vol:.1f} µm3")
    print(f"{'1st quartile:':16}{Q1_vol:.1f} µm3")
    print(f"{'Median:':16}{med_vol:.1f} µm3")
    print(f"{'Median absdev:':16}{mad:.1f} µm3")
    print(f"{'3rd quartile:':16}{Q3_vol:.1f} µm3")
    print(f"{'Max. volume:':16}{max_vol:.1f} µm3")


# User interaction and parameter logic
parser = argparse.ArgumentParser(description="Analyze images for S. pombe volume measurement.")
parser.add_argument("path", type=str, help="Path to images directory")
parser.add_argument("pillar", type=float, help="Height of the microfluidic chamber in µm")
parser.add_argument("--pixel", type=float, help="Size of image pixel in µm given by your camera pixel size and the "
                                                "magnification used", required=False)

group = parser.add_mutually_exclusive_group()
group.add_argument("-t", "--thresholds", type=float, action="append", nargs='?',
                   help="IQR factor to automatically filter outliers. It sets thresholds using the IQR method (t*IQR). "
                        "Lower thresholds are more restrictive.")
group.add_argument("-m", "--manual", action="store_true", help="Use manual filtering instead of automatic detection.")


# Change defaults depending on your setup
parser.set_defaults(
    pixel=0.325,  # Pixel size of your images (µm)
    thresholds=[1]  # List of thresholds to use for automatic outlier detection
)

args = parser.parse_args()

analysis_dir = args.path
pillar_height = args.pillar
pixel_size = args.pixel
thresholds = sorted([float(t) for t in set(args.thresholds)])
manual = args.manual

if not os.path.isdir(analysis_dir):
    print(f"The analysis directory does not exist.")
    exit()


norm_file = "frame1.mat"  # Normalization file that the script will look for


df = pd.DataFrame({})

# File finding
for root, dirs, files in os.walk(analysis_dir):
    for file in files:
        if file.endswith(norm_file):
            print(root)
            try:
                v = analyze_experiment(root, manual, pillar_height=pillar_height, pixel_size=pixel_size)
            except Exception as e:
                print(f"Image could not be analyzed due to an exception:\n{e}")
                continue
            if v.empty:
                print(f"No cells in image")
                continue
            if df.empty:
                df = v
            else:
                df = df.append(v, ignore_index=True)

print()

if df.empty:
    print(f"No data obtained. Did not find any {norm_file} files inside the analysis directory.")
    print(f"Have you normalized your images?")
    exit()

strain_dir = os.path.abspath(os.path.join(root, "../.."))
df_file = strain_dir + f"_A.tsv"

# Saves data and prints output information
if manual:
    df_file = strain_dir + f"_M.tsv"

    print("-" * 40)
    print("MANUALLY FILTERED DATA")
    print("-" * 40)

    print_output_stats(df, "ManualFilter")

    #print(f"Total number of objects: {len(df)}")
    #print(f"Accepted cells:")
    #print(df.loc[df["ManualFilter"] == False, "Volume"].describe())
    print()
else:
    df_file = strain_dir + f"_A.tsv"

    # Calculates IQR
    Q1 = np.percentile(df["Volume"], 25)
    med = np.percentile(df["Volume"], 50)
    Q3 = np.percentile(df["Volume"], 75)
    IQR = Q3 - Q1

    for th in thresholds:
        # Finds outliers
        outliers = np.logical_or(df["Volume"] > (Q3 + IQR * th), df["Volume"] < (Q1 - IQR * th))

        # Calculate number of outliers
        n_total_outliers = len(df.loc[outliers])
        n_high_outliers = len(df.loc[(df["Volume"] > Q3 + th * IQR)])
        n_low_outliers = len(df.loc[(df["Volume"] < Q1 - th * IQR)])

        # Calculate percentages of outliers
        p_total_outliers = n_total_outliers / len(df) * 100
        p_high_outliers = n_high_outliers / len(df) * 100
        p_low_outliers = n_low_outliers / len(df) * 100

        # Add column with automatic filter
        filter_name = f"AutoFilterIQR_{th}"  # Name of the column that includes IQR threshold (th*IQR)
        df[filter_name] = outliers
        
        print("-" * 40)
        print(f"AUTOMATICALLY FILTERED DATA ({th}*IQR):")
        print("-" * 40)

        print_output_stats(df, filter_name)

        # Prints outlier percentages
        print()
        print(f"{'Low outliers:':16}{n_low_outliers:d} ({p_low_outliers:.1f} %)")
        print(f"{'High outliers:':16}{n_high_outliers:d} ({p_high_outliers:.1f} %)")
        print(f"{'Total outliers:':16}{n_total_outliers:d} ({p_total_outliers:.1f} %)")
        print()

print("-" * 40)
print(f'Output file: {df_file}')
df.to_csv(df_file, sep="\t")
