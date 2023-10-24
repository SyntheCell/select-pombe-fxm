import os
from scipy.io import loadmat
import pandas as pd
import numpy as np

import argparse

def print_output_stats(data, class_group) -> None:
    """
    Prints the output of the analysis extracted from pd.DataFrame.describe().
    data: pd.DataFrame containing the FXm data.
    class_group: string with the name of the classification group to print stats for.
    """

    stats = data.loc[data["DetecDivGroup"] == class_group, "Volume"].describe()

    cell_count = int(stats["count"])
    mean_vol = stats["mean"]
    std_vol = stats["std"]
    min_vol = stats["min"]
    Q1_vol = stats["25%"]
    med_vol = stats["50%"]
    mad = data.loc[data["DetecDivGroup"] == class_group, "Volume"].mad()
    Q3_vol = stats["75%"]
    max_vol = stats["max"]
    
    # NOTE: User may uncomment the desired stats to print
    print(f"Total number\n{'of objects:':16}{len(data)}")
    print(f"{'Accepted cells:':16}{cell_count:d}")
    print()
    #print(f"{'Mean volume:':16}{mean_vol:.1f} µm3")
    #print(f"{'Volume stdev:':16}{std_vol:.1f} µm3")
    #print(f"{'Min. volume:':16}{min_vol:.1f} µm3")
    #print(f"{'1st quartile:':16}{Q1_vol:.1f} µm3")
    print(f"{'Median:':16}{med_vol:.1f} µm3")
    print(f"{'Median absdev:':16}{mad:.1f} µm3")
    #print(f"{'3rd quartile:':16}{Q3_vol:.1f} µm3")
    #print(f"{'Max. volume:':16}{max_vol:.1f} µm3")

# User interaction and parameter logic
parser = argparse.ArgumentParser(description="Extract DetecDiv classification and calculate volume of experiment.")
parser.add_argument("path", type=str, help="Path to .tsv.")
parser.add_argument("classification", type=str, help="Path to .mat file with clasification")
parser.add_argument("-g", "--group", type=str, help="Classification group name to print experiment stats for.", required=False)

args = parser.parse_args()
mat_file = args.classification
class_group = args.group

# Extract classification data from matlab file
mat = loadmat(mat_file)
data = mat['results'].item()[0][0][0][0][0]

# Convert classification data to pd DataFrame as string
class_df = pd.DataFrame(data, columns={"DetecDivGroup"})

# Open FXm data and add the new classification column
vm_df = pd.read_csv(args.path, sep="\t", index_col=0)
vm_df["DetecDivGroup"] = class_df["DetecDivGroup"].astype(str)

if class_group:
    
    # Print stats for classification group
    print("-" * 40)
    print(f"DETECDIV FILTERED DATA, group {class_group}")
    print("-" * 40)
    
    print_output_stats(vm_df, class_group)

# Save the new data
tsv_file_name = os.path.splitext(os.path.basename(args.path))[0]  # Get name of FXm .tsv file, without extension
expt_folder = os.path.dirname(args.path)  # Get path to FXm .tsv file

output_file = os.path.join(expt_folder, f"{tsv_file_name}_D.tsv")
vm_df.to_csv(output_file, sep="\t")

print(f"DetecDiv filtered data saved to {output_file}")
