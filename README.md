# Terrascan-ML-Model
Register in google earth engine and use the project id in the code
Create a virtual environment
	python -m venv venv
	source vent/bin/activate
	

pip  install ee earthengine-api geemap setuptools tqdm
Run the fetch AOI script
Download and install Miniconda
Create and activate a conda environment
conda create -n terrascan python=3.10
conda activate terrascan
Install GDAL using conda-forge
	conda install -c conda-forge gdal
Run the generate lucd dataset script
Data PreProcessing
Run split dataset script
Run normalize and encode script
Create data loaders according to your model requirements

