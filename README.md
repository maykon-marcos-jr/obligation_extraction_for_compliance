# obligation_extraction_for_compliance

## run
> uses conda to run main.py

```sh
echo "running the main archive..."
conda run -n alma_env python main.py
```

## detection-test
> runs the obligation_detection module for tests
```sh
echo "running the detection archive..."
cd src
conda run -n alma_env python obligation_detection.py
```

## setup
> creates the environment
```sh
conda env create -f alma_env.yml
```


## update
> reloads the nev with added dependencies
```sh
conda env update --file alma_env.yml --prune
```