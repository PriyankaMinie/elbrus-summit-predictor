import cdsapi

client = cdsapi.Client()

dataset = "reanalysis-era5-pressure-levels"
years = ["2018", "2019", "2020", "2021", "2022", "2023", "2024"]

for year in years:
    request = {
        "product_type": ["reanalysis"],
        "variable": ["temperature", "u_component_of_wind", "v_component_of_wind"],
        "pressure_level": ["500"],
        "year": [year],
        "month": ["07", "08", "09", "10"],
        "day": [
            "01",
            "02",
            "03",
            "04",
            "05",
            "06",
            "07",
            "08",
            "09",
            "10",
            "11",
            "12",
            "13",
            "14",
            "15",
            "16",
            "17",
            "18",
            "19",
            "20",
            "21",
            "22",
            "23",
            "24",
            "25",
            "26",
            "27",
            "28",
            "29",
            "30",
            "31",
        ],
        "time": [
            "00:00",
            "01:00",
            "02:00",
            "03:00",
            "04:00",
            "05:00",
            "06:00",
            "07:00",
            "08:00",
            "09:00",
            "10:00",
            "11:00",
            "12:00",
            "13:00",
            "14:00",
            "15:00",
            "16:00",
            "17:00",
            "18:00",
            "19:00",
            "20:00",
            "21:00",
            "22:00",
            "23:00",
        ],
        "data_format": "netcdf",
        "download_format": "unarchived",
        "area": [44, 42, 43, 43],  # North, West, South, East
    }

    filename = f"era5_pressure_{year}.nc"
    print(f"Requesting {year}...")
    client.retrieve(dataset, request).download(filename)
    print(f"Downloaded {filename}")

print("All years downloaded successfully")
