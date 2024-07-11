# text2matrix

## Rationale

This projects explores how we could use a large language model to reformat text species descriptions into species / character matrices, suitable for building multi-entry identification keys.

## Pre-requisites

An environment capable of running Python and the build tool `make`

## Set-up

1. Create a virtual environment: `python -m venv env`
1. Activate it: `source env/Scripts/activate` 
1. Install required libraries: `pip install -r requirements.txt` 

## Running the software

A complete run will download the specified DWCA files from the World Flora Online data server and process them to extract the taxonomy and descriptions to delimited text files, suitable for further processing using a LLM.

You can see what steps the makefile will execute by typing `make all --dry-run`

You can run the makefile to build all targets by typing: `make all`

## Contributing

Specific issues or enhancements can be added to the [issues tracker](https://github.com/WFO-ID-pilots/text2matrix/issues) for this project. More general discussions are also welcomed on the [discussion board](https://github.com/orgs/WFO-ID-pilots/discussions) for the parent project

## Contacts

- Nicky Nicolson - [@nickynicolson](https://github.com/nickynicolson)
- Young Jun Lee - [@yjkiwilee](https://github.com/yjkiwilee)