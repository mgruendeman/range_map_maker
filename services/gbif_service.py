
# gbif_service.py
import requests
import pandas as pd
import json
import os

class GBIFService:
    def __init__(self, limit = 300):
        self.base_url = "https://api.gbif.org/v1/occurrence/search"
        self.base_dir = "./data/" 
        self.limit = limit

    def download_gbif_data(self, genus, species, filetype, licenses):

        # Setup file names and scientific name
        scientific_name = str(genus.strip() + ' ' + species.strip())
        filename = str(genus.strip() + '_' + species.strip())

        # print(f"Requesting: {self.base_url} with params: {params}")

        # print(licenses)

        offset = 0
        records = []

        licenses_list = licenses.split(',')

        
        for licse in licenses_list: ## I could not figure out how to input two paramaters of the same type so I am loopin
            offset = 0
            print("Working on: " + str(licse))

            while True:
                
                params = {
                    'scientificName': scientific_name,
                    'limit': self.limit,
                    'offset': offset,
                    'basisOfRecord' : 'HUMAN_OBSERVATION',
                    'hasCoordinate' : 'true',
                    'hasGeospatialIssue' : 'false',
                    'license' : licse
                }
                response = requests.get(self.base_url, params=params)

                print(f"Request URL: {response.request.url}")

                if response.status_code == 200:
                    data = response.json()
                    records.extend(data['results'])  # Add the records from this page to the list

                    # Check if we have reached the end of the dataset
                    if len(data['results']) < self.limit:
                        break  # Exit the loop if fewer records are returned than the limit
                    offset += self.limit  # Prepare the offset for the next batch of data
                else:
                    print("Failed to download data. Status code:", response.status_code)
                    break
        
        if filetype == "json":
            self.save_data_to_json(records, filename)

        print("Data Saved")

    def save_data_to_json(self, data, filename):

         # Construct the directory path for this species
        species_dir = os.path.join(self.base_dir, filename)

        # Check if the species directory exists, and if not, create it
        if not os.path.exists(species_dir):
            os.makedirs(species_dir)
        
        # Construct the full file path for the JSON file within the species directory
        filename = f"{filename}.json"
        data_file_path = os.path.join(species_dir, filename)
        
        # Write data to the file, replacing the old file if it exists
        with open(data_file_path, 'w') as file:
            json.dump(data, file)

    def save_data_to_csv(self, data, filename):
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)

    def read_data_from_json(self, filename):
        with open(filename, 'r') as file:
            return json.load(file)

    def read_data_from_csv(self, filename):
        return pd.read_csv(filename)

























# def download_data(genus,species):

    # scientific_name = str(genus.strip() + ' ' + species.strip())

    # base_url = "https://api.gbif.org/v1/occurrence/search"

    # limit = 300
    # offset = 0
    # records = []

    # while True:
    #     params = {
    #         'scientificName': scientific_name,
    #         'limit': limit,
    #         'offset': offset
    #     }
    #     response = requests.get(base_url, params=params)

    #     if response.status_code == 200:
    #         data = response.json()
    #         records.extend(data['results'])  # Add the records from this page to the list

    #         # Check if we have reached the end of the dataset
    #         if len(data['results']) < limit:
    #             break  # Exit the loop if fewer records are returned than the limit
    #         offset += limit  # Prepare the offset for the next batch of data
    #     else:
    #         print("Failed to download data. Status code:", response.status_code)
    #         break

    

    


    # with open(data_file, 'w') as file:
    #     json.dump(records, file)

