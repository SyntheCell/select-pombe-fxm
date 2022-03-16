# select-pombe-fxm

This code facilitates the analysis of data obtained using the Fluorescence Exclusion Method (FXm) for the measurement of yeast cell volume. 


## Dependencies

This code requires the following Python packages (also see `requirements.txt`):
```
mahotas==1.4.9
matplotlib==3.2.1
numpy==1.18.5
pandas==1.0.4
scipy==1.6.0
```

## How does it work?

FXm analysis involves a step of image normalization.
This step generates a mask in which objects are pre-identified.

select-pombe-fxm uses this mask and:

1. Automatically selects all objects and filters out those that show an abnormally high or low volume, or

2. Displays all pre-selected objects to the user for manual filtering

3. Optional: assigns different groups to the selected cells, based on other fluorescent markers


The normalization mask is generated using a custom MATLAB software from Cadart et al., Methods Cell Biol. (2017).


## Installation

1. Create a virtual environment and activate it.
    ```
    python3.7 -m venv venv
    source venv/bin/activate
    ```
2. Install the requirements in `requirements.txt`.
    ```
    pip install -r requirements.txt
    ```


## Usage
```shell script
# Activate virtual environment
source venv/bin/activate
```
```shell script
# Run script to calculate volumes

$ python main.py -h
usage: main.py [-h] [--pixel PIXEL] [-t [THRESHOLDS] | -m] path pillar

Analyze images for S. pombe volume measurement.

positional arguments:
  path                  Path to images directory
  pillar                Height of the microfluidic chamber in µm

optional arguments:
  -h, --help            show this help message and exit
  --pixel PIXEL         Size of image pixel in µm given by your camera pixel
                        size and the magnification used
  -t [THRESHOLDS], --thresholds [THRESHOLDS]
                        IQR factor to automatically filter outliers. It sets
                        thresholds using the IQR method (t*IQR). Lower
                        thresholds are more restrictive.
  -m, --manual          Use manual filtering instead of automatic detection.

```

```shell script
# Optional: run script to assign groups to cells
python group.py -h
usage: group.py [-h] [-g GROUPS] [-f FXM_PREFIX] [-m MARKER_PREFIX] path

Separate FXm cells in groups

positional arguments:
  path                  Path to .tsv analysis file

optional arguments:
  -h, --help            Shows this help message and exit
  -g GROUPS, --groups GROUPS
                        Number of groups to classify the cells in
  -f FXM_PREFIX, --fxm-prefix FXM_PREFIX
                        Prefix of the fxm file name (e.g. FITC, for FITC-1.tif file)
  -m MARKER_PREFIX, --marker-prefix MARKER_PREFIX
                        Prefix of the marker file name (e.g. mCherry, for mCherry-1.tif file)

```

### Automatic mode

This mode automatically selects all objects and discards those that show abnormally high or low volumes using the default 1*IQR threshold.

Enter the path and pillar height arguments and run:
```
python main.py </path/to/experiment/files> <pillar-height>
```

This will generate a `.tsv` file with all the data.
This file includes a `bool` column called `AutoFilterIQR_1.0` with the results of the automatic filtering using the IQR method (1*IQR).

- `True`: automatically discarded as outlier
- `False`: valid cells

Optionally, you can define another filtering threshold as a factor of IQR by adding the flag `-t`. You can add several thresholds if needed:
```
python main.py </path/to/experiment/files> <pillar-height> -t <threshold1> -t <threshold2>
```

In this case, the output file will contain one `bool` column detailing the included and excluded values for each threshold.

Additionally, it will provide some descriptive statistics. Here is an example output of the data obtained using the 'Automatic Mode' with one image, using two different thresholds:

```
----------------------------------------
AUTOMATICALLY FILTERED DATA (1.0*IQR):
----------------------------------------
Total number
of objects:     28
Accepted cells: 22

Mean volume:    107.3 µm3
Volume stdev:   23.3 µm3
Min. volume:    58.4 µm3
1st quartile:   92.4 µm3
Median:         106.4 µm3
Median absdev:  17.5 µm3
3rd quartile:   119.0 µm3
Max. volume:    157.3 µm3

Low outliers:   1 (3.6 %)
High outliers:  5 (17.9 %)
Total outliers: 6 (21.4 %)

----------------------------------------
AUTOMATICALLY FILTERED DATA (2.0*IQR):
----------------------------------------
Total number
of objects:     28
Accepted cells: 25

Mean volume:    118.4 µm3
Volume stdev:   37.9 µm3
Min. volume:    58.4 µm3
1st quartile:   97.8 µm3
Median:         109.4 µm3
Median absdev:  28.0 µm3
3rd quartile:   129.9 µm3
Max. volume:    208.8 µm3

Low outliers:   1 (3.6 %)
High outliers:  2 (7.1 %)
Total outliers: 3 (10.7 %)

----------------------------------------
```


### Manual mode

This mode allows the user to manually exclude irrelevant objects from the analysis.

Run the manual mode by adding the `-m` flag:
```
python main.py </path/to/experiment/files> <pillar-height> -m
```

This will open a `pyplot` window showing all pre-selected objects of the image.
Irrelevant objects can be de-selected by simple mouse click (discarded objects are red-barred).
When the manual filtering of a given image is done, simply close the window (data are automatically saved).
A new window for the next image is then opened.

Note: each subplot is a 200x200 px image centered on the object that is being selected.
However, these selections do not need to be discarded as only the centered object will be considered for volume calculation.

When all images have been treated, a `.tsv` file containing all data is generated.
It includes a column called "ManualFilter" with the results of the manual filtering.

- `True`: manually discarded as outlier
- `False`: valid cells

Additionally, it will provide some descriptive statistics. Here is an example output of the data obtained using the 'Manual Mode' with one image:

```
----------------------------------------
MANUALLY FILTERED DATA
----------------------------------------
Total number
of objects:     28
Accepted cells: 20

Mean volume:    102.8 µm3
Volume stdev:   19.2 µm3
Min. volume:    58.4 µm3
1st quartile:   90.0 µm3
Median:         106.1 µm3
Median absdev:  15.0 µm3
3rd quartile:   113.7 µm3
Max. volume:    137.0 µm3

----------------------------------------
```



### Group mode
This mode allows the user to separate cells into different groups, based on other fluorescent markers.
For this, it uses images on a different fluorescent channel as well as the FXm images.

After running the manual or the automatic mode, run the group mode as follows:
```shell script
# To assign groups to manually filtered cells (run Manual mode first)

python group.py </path/to/data_M.tsv> -g <group number> -f <prefix of FXm images> -m <prefix of marker images>
```
```shell script
# To assign groups to all cells (run Automatic mode first)

python group.py </path/to/data_A.tsv> -g <group number> -f <prefix of FXm images> -m <prefix of marker images>
```
This will open a `pyplot` window showing the selected cells or all the objects, which are automatically assigned to Group 1 (G1).
The user will be able to select the appropriate group as follows:

- Left click on each object to increase the group number.
- Right click on each object to decrease the group number.
- Discard object by assigning the `None` group (group 0) (for instance, right click when group is 1)
- Click on the radiobuttons (or press `space`) to alternate between FXm image and the fluorescent marker image.

This mode will make a copy of the analysis, will add a column "Group" with the group information, and will save the file by adding `_grp` to its name (e.g., `data_A_grp.tsv` or `data_M_grp.tsv`)

Additionally, it will provide some descriptive statistics. Here is an example output of the data obtained using the 'Group Mode' with one image:

```
----------------------------------------
DATA FOR ALL GROUPS:
----------------------------------------
Total number
of objects:       28
Cells in
all groups:       20

Mean volume:      102.8 µm3
Volume stdev:     19.2 µm3
Min. volume:      58.4 µm3
1st quartile:     90.0 µm3
Median:           106.1 µm3
Median abs. dev.: 15.0 µm3
3rd quartile:     113.7 µm3
Max. volume:      137.0 µm3

----------------------------------------
DATA FOR GROUP 1:
----------------------------------------
Total number
of objects:       28
Cells in group 1: 8

Mean volume:      105.3 µm3
Volume stdev:     17.8 µm3
Min. volume:      80.7 µm3
1st quartile:     93.6 µm3
Median:           107.9 µm3
Median abs. dev.: 14.1 µm3
3rd quartile:     117.9 µm3
Max. volume:      129.9 µm3

----------------------------------------
DATA FOR GROUP 2:
----------------------------------------
Total number
of objects:       28
Cells in group 2: 12

Mean volume:      101.2 µm3
Volume stdev:     20.7 µm3
Min. volume:      58.4 µm3
1st quartile:     90.0 µm3
Median:           103.4 µm3
Median abs. dev.: 15.1 µm3
3rd quartile:     110.2 µm3
Max. volume:      137.0 µm3

----------------------------------------
```

Note: to adapt the visualization of the fluorescent marker, determine the optimal levels in another program, and edit the
display parameters inside `group.py` in the following line:

`marker_img = plt.imshow(msk_marker, cmap=plt.cm.Reds, alpha=1, vmin=250, vmax=450)`

