# irrigation_doodles
 
## For AQUASTAT: 
### Metadata: 

data/AQUASTAT Dissemination System.csv was retrieved from https://data.apps.fao.org/aquastat/?lang=en on 12/11/23
using the parameters:
- Variables = Pressure on water resources
- Area = World
- Year = 2020, 2019, 2015, 2010, 2005, 2000, 1995, 1990

## For GEE EVI: 
### Installation: 

Create your conda environment to run the python scripts. 

```bash
conda create --name gee_evi python=3.9
conda activate gee_evi
pip install --file requirements.txt
conda list # check everything installed properly
```

You will then need to authenticate your google earth engine account. Make sure gee_evi is activated. 

```bash
earthengine authenticate
```