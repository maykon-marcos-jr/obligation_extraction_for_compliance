# obligation_extraction_for_compliance

## setup
> creates the environment
```sh
conda env create -f alma_env.yml
```

## start
> activates the env
```sh
conda activate alma_env
```

## run
> uses conda to run main.py

```sh
echo "running the main archive..."
python main.py
```

## detection-test
> runs the obligation_detection module for tests
```sh
cd src
python obligation_detection.py
```


## update
> reloads the nev with added dependencies
```sh
conda env update --file alma_env.yml --prune
```